"""
🧪 Enhanced Backtest Engine
Simulates realistic trading with position sizing, fees, slippage, and advanced metrics.
"""
import json
import ccxt
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field

from utils.logger import info, warn, error, success
from config.trading_config import RiskConfig, PaperConfig


@dataclass
class BacktestTrade:
    """Single backtest trade record."""
    signal_id: int
    symbol: str
    side: str  # BUY/SELL
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: str
    exit_time: str
    exit_reason: str  # TP/SL/TIMEOUT
    pnl_gross: float
    pnl_net: float
    pnl_pct: float
    fees: float
    slippage: float
    bars_held: int
    capital_at_entry: float
    source: str = ""  # Channel source
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics."""
    # Basic metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # PnL metrics
    total_pnl_gross: float = 0.0
    total_pnl_net: float = 0.0
    total_fees: float = 0.0
    total_slippage: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_days: int = 0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Equity metrics
    initial_capital: float = 0.0
    final_capital: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    
    # Time metrics
    start_date: str = ""
    end_date: str = ""
    duration_days: int = 0
    avg_trade_duration_hours: float = 0.0
    
    # Monthly breakdown
    monthly_returns: Dict[str, float] = field(default_factory=dict)
    
    # Channel comparison
    channel_metrics: Dict[str, Dict] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


class BacktestEngine:
    """
    Enhanced backtesting engine with realistic simulation.
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        risk_pct: float = 0.02,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.0006,
        slippage_pct: float = 0.001,
        max_bars_held: int = 96  # 24 hours for 15m candles
    ):
        """
        Initialize backtest engine.
        
        Args:
            initial_capital: Starting capital in USDT
            risk_pct: Risk percentage per trade (0.02 = 2%)
            maker_fee: Maker fee percentage (0.0002 = 0.02%)
            taker_fee: Taker fee percentage (0.0006 = 0.06%)
            slippage_pct: Average slippage percentage (0.001 = 0.1%)
            max_bars_held: Maximum candles to hold position (timeout)
        """
        self.initial_capital = initial_capital
        self.risk_pct = risk_pct
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage_pct = slippage_pct
        self.max_bars_held = max_bars_held
        
        # State
        self.capital = initial_capital
        self.equity_curve: List[float] = [initial_capital]
        self.trades: List[BacktestTrade] = []
        self.daily_returns: List[float] = []
        
        # Use Binance instead of MEXC
        from utils.binance_api import BinanceClient
        self.exchange = BinanceClient()
        
        info(f"🧪 Backtest Engine initialized")
        info(f"   💰 Capital: ${initial_capital:,.2f}")
        info(f"   📊 Risk per trade: {risk_pct*100:.1f}%")
        info(f"   💸 Fees: {maker_fee*100:.2f}% maker / {taker_fee*100:.2f}% taker")
        info(f"   📉 Slippage: {slippage_pct*100:.2f}%")
    
    def calculate_position_size(
        self, 
        entry_price: float, 
        sl_price: Optional[float],
        side: str
    ) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            entry_price: Entry price
            sl_price: Stop loss price (None = use default risk)
            side: BUY or SELL
            
        Returns:
            Position size in base asset
        """
        # Risk amount in USDT
        risk_amount = self.capital * self.risk_pct
        
        if sl_price and sl_price > 0:
            # Calculate based on actual stop loss distance
            if side == "BUY":
                risk_per_unit = abs(entry_price - sl_price)
            else:  # SELL
                risk_per_unit = abs(sl_price - entry_price)
            
            if risk_per_unit > 0:
                position_size_usdt = risk_amount / (risk_per_unit / entry_price)
            else:
                # Fallback to 2% of capital if SL is at entry
                position_size_usdt = self.capital * 0.02
        else:
            # No SL, use fixed percentage
            position_size_usdt = self.capital * 0.02
        
        # Enforce position limits
        max_position = self.capital * RiskConfig.MAX_POSITION_SIZE_PCT
        position_size_usdt = min(position_size_usdt, max_position)
        position_size_usdt = max(position_size_usdt, RiskConfig.MIN_POSITION_SIZE_USDT)
        
        # Convert to quantity
        quantity = position_size_usdt / entry_price
        
        return quantity
    
    def apply_slippage(self, price: float, side: str) -> float:
        """Apply slippage to execution price."""
        if side == "BUY":
            return price * (1 + self.slippage_pct)
        else:
            return price * (1 - self.slippage_pct)
    
    def calculate_fees(self, position_value: float, is_maker: bool = False) -> float:
        """Calculate trading fees."""
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        return position_value * fee_rate
    
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = "15m", 
        limit: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data from Binance.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            timeframe: Candle timeframe
            limit: Number of candles
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Binance uses same symbol format as MEXC (BTCUSDT)
            bars = self.exchange.get_klines(symbol, interval=timeframe, limit=limit)
            
            if not bars:
                return None
            
            df = pd.DataFrame(
                bars, 
                columns=["timestamp", "open", "high", "low", "close", "volume", 
                        "close_time", "quote_volume", "trades", "taker_buy_base", 
                        "taker_buy_quote", "ignore"]
            )
            
            # Keep only needed columns
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            # Convert to float
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            
            return df
        
        except Exception as e:
            error(f"Failed to fetch OHLCV for {symbol}: {e}")
            return None
    
    def simulate_trade(
        self,
        signal: Dict,
        df_ohlcv: pd.DataFrame,
        signal_id: int
    ) -> Optional[BacktestTrade]:
        """
        Simulate a single trade based on signal and price data.
        
        Args:
            signal: Signal dictionary with symbol, side, entry, tp, sl
            df_ohlcv: Historical OHLCV data
            signal_id: Unique signal identifier
            
        Returns:
            BacktestTrade or None if trade invalid
        """
        try:
            symbol = signal["symbol"]
            side = signal["side"]
            entry = signal.get("entry")
            tp = signal.get("tp")
            sl = signal.get("sl")
            entry_time = signal.get("timestamp", datetime.now(timezone.utc).isoformat())
            source = signal.get("source", "unknown")  # Track channel source
            
            # Use last close if no entry specified
            if not entry or entry <= 0:
                entry = float(df_ohlcv.iloc[-1]["close"])
            
            # Apply slippage to entry
            entry_slipped = self.apply_slippage(entry, side)
            
            # Calculate position size
            quantity = self.calculate_position_size(entry_slipped, sl, side)
            position_value = quantity * entry_slipped
            
            # Entry fees
            entry_fee = self.calculate_fees(position_value, is_maker=False)
            slippage_cost = abs(entry_slipped - entry) * quantity
            
            # Simulate holding period
            exit_price = None
            exit_reason = None
            bars_held = 0
            
            # Check future candles for TP/SL hits
            future_candles = df_ohlcv.tail(self.max_bars_held)
            
            for idx, candle in future_candles.iterrows():
                bars_held += 1
                
                if side == "BUY":
                    # Check TP hit
                    if tp and candle["high"] >= tp:
                        exit_price = tp
                        exit_reason = "TP"
                        break
                    # Check SL hit
                    if sl and candle["low"] <= sl:
                        exit_price = sl
                        exit_reason = "SL"
                        break
                
                else:  # SELL
                    # Check TP hit
                    if tp and candle["low"] <= tp:
                        exit_price = tp
                        exit_reason = "TP"
                        break
                    # Check SL hit
                    if sl and candle["high"] >= sl:
                        exit_price = sl
                        exit_reason = "SL"
                        break
            
            # Timeout if no TP/SL hit
            if exit_price is None:
                exit_price = float(future_candles.iloc[-1]["close"])
                exit_reason = "TIMEOUT"
            
            # Apply slippage to exit
            exit_slipped = self.apply_slippage(exit_price, "SELL" if side == "BUY" else "BUY")
            
            # Exit fees
            exit_fee = self.calculate_fees(quantity * exit_slipped, is_maker=False)
            exit_slippage = abs(exit_slipped - exit_price) * quantity
            
            # Calculate PnL
            if side == "BUY":
                pnl_gross = (exit_slipped - entry_slipped) * quantity
            else:  # SELL
                pnl_gross = (entry_slipped - exit_slipped) * quantity
            
            total_fees = entry_fee + exit_fee
            total_slippage = slippage_cost + exit_slippage
            pnl_net = pnl_gross - total_fees - total_slippage
            pnl_pct = (pnl_net / position_value) * 100
            
            # Update capital
            capital_before = self.capital
            self.capital += pnl_net
            self.equity_curve.append(self.capital)
            
            # Calculate exit time
            exit_time_dt = pd.to_datetime(entry_time) + pd.Timedelta(minutes=15*bars_held)
            
            # Create trade record
            trade = BacktestTrade(
                signal_id=signal_id,
                symbol=symbol,
                side=side,
                entry_price=entry_slipped,
                exit_price=exit_slipped,
                quantity=quantity,
                entry_time=entry_time,
                exit_time=exit_time_dt.isoformat(),
                exit_reason=exit_reason,
                pnl_gross=pnl_gross,
                pnl_net=pnl_net,
                pnl_pct=pnl_pct,
                fees=total_fees,
                slippage=total_slippage,
                bars_held=bars_held,
                capital_at_entry=capital_before,
                source=source
            )
            
            return trade
        
        except Exception as e:
            error(f"Error simulating trade for {signal.get('symbol')}: {e}")
            return None
    
    def calculate_metrics(self) -> BacktestMetrics:
        """Calculate comprehensive performance metrics."""
        if not self.trades:
            return BacktestMetrics(initial_capital=self.initial_capital)
        
        metrics = BacktestMetrics()
        
        # Basic counts
        metrics.total_trades = len(self.trades)
        metrics.winning_trades = len([t for t in self.trades if t.pnl_net > 0])
        metrics.losing_trades = len([t for t in self.trades if t.pnl_net < 0])
        metrics.win_rate = (metrics.winning_trades / metrics.total_trades * 100) if metrics.total_trades > 0 else 0
        
        # PnL metrics
        wins = [t.pnl_net for t in self.trades if t.pnl_net > 0]
        losses = [t.pnl_net for t in self.trades if t.pnl_net < 0]
        
        metrics.total_pnl_gross = sum(t.pnl_gross for t in self.trades)
        metrics.total_pnl_net = sum(t.pnl_net for t in self.trades)
        metrics.total_fees = sum(t.fees for t in self.trades)
        metrics.total_slippage = sum(t.slippage for t in self.trades)
        
        metrics.avg_win = np.mean(wins) if wins else 0
        metrics.avg_loss = np.mean(losses) if losses else 0
        metrics.largest_win = max(wins) if wins else 0
        metrics.largest_loss = min(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        metrics.profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        # Expectancy
        if metrics.total_trades > 0:
            metrics.expectancy = (
                (metrics.win_rate / 100 * metrics.avg_win) - 
                ((1 - metrics.win_rate / 100) * abs(metrics.avg_loss))
            )
        
        # Equity metrics
        metrics.initial_capital = self.initial_capital
        metrics.final_capital = self.capital
        metrics.total_return = metrics.final_capital - metrics.initial_capital
        metrics.total_return_pct = (metrics.total_return / metrics.initial_capital * 100)
        
        # Drawdown calculation
        equity_curve = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        metrics.max_drawdown_pct = abs(drawdown.min() * 100)
        metrics.max_drawdown = abs((equity_curve - running_max).min())
        
        # Sharpe ratio (annualized)
        returns = np.diff(equity_curve) / equity_curve[:-1]
        if len(returns) > 0:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            if std_return > 0:
                # Annualize: 252 trading days, assume 15m bars = ~1500 bars/day (simplification)
                metrics.sharpe_ratio = (avg_return / std_return) * np.sqrt(252)
        
        # Time metrics
        if self.trades:
            entry_times = [pd.to_datetime(t.entry_time) for t in self.trades]
            exit_times = [pd.to_datetime(t.exit_time) for t in self.trades]
            
            metrics.start_date = min(entry_times).strftime("%Y-%m-%d")
            metrics.end_date = max(exit_times).strftime("%Y-%m-%d")
            metrics.duration_days = (max(exit_times) - min(entry_times)).days
            
            durations = [(pd.to_datetime(t.exit_time) - pd.to_datetime(t.entry_time)).total_seconds() / 3600 
                        for t in self.trades]
            metrics.avg_trade_duration_hours = np.mean(durations)
        
        # Monthly returns
        trades_df = pd.DataFrame([t.to_dict() for t in self.trades])
        trades_df["exit_time"] = pd.to_datetime(trades_df["exit_time"])
        trades_df["month"] = trades_df["exit_time"].dt.to_period("M")
        monthly = trades_df.groupby("month")["pnl_net"].sum()
        metrics.monthly_returns = {str(k): float(v) for k, v in monthly.items()}
        
        # Channel comparison metrics
        if "source" in trades_df.columns:
            channel_metrics = {}
            for channel in trades_df["source"].unique():
                channel_trades = trades_df[trades_df["source"] == channel]
                
                wins = channel_trades[channel_trades["pnl_net"] > 0]
                losses = channel_trades[channel_trades["pnl_net"] < 0]
                
                total_pnl = channel_trades["pnl_net"].sum()
                total_trades = len(channel_trades)
                win_count = len(wins)
                win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
                
                avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
                
                # Profit factor
                total_wins = wins["pnl_net"].sum() if len(wins) > 0 else 0
                total_losses = abs(losses["pnl_net"].sum()) if len(losses) > 0 else 0
                profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
                
                channel_metrics[str(channel)] = {
                    "total_trades": int(total_trades),
                    "winning_trades": int(win_count),
                    "losing_trades": int(len(losses)),
                    "win_rate": float(win_rate),
                    "total_pnl": float(total_pnl),
                    "avg_pnl_per_trade": float(avg_pnl),
                    "profit_factor": float(profit_factor),
                    "best_trade": float(channel_trades["pnl_net"].max()),
                    "worst_trade": float(channel_trades["pnl_net"].min())
                }
            
            metrics.channel_metrics = channel_metrics
        
        return metrics
    
    def run_backtest(
        self, 
        signals: List[Dict],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[BacktestTrade], BacktestMetrics]:
        """
        Run backtest on list of signals.
        
        Args:
            signals: List of signal dictionaries
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            
        Returns:
            Tuple of (trades list, metrics)
        """
        info("=" * 70)
        info("🧪 STARTING BACKTEST")
        info("=" * 70)
        
        # Filter signals by date
        filtered_signals = signals
        if start_date or end_date:
            filtered_signals = []
            for sig in signals:
                sig_date = pd.to_datetime(sig.get("timestamp")).strftime("%Y-%m-%d")
                if start_date and sig_date < start_date:
                    continue
                if end_date and sig_date > end_date:
                    continue
                filtered_signals.append(sig)
        
        info(f"📊 Processing {len(filtered_signals)} signals")
        
        for idx, signal in enumerate(filtered_signals, 1):
            try:
                symbol = signal.get("symbol")
                
                if idx % 10 == 0:
                    info(f"   [{idx}/{len(filtered_signals)}] Testing {symbol}...")
                
                # Fetch OHLCV
                df_ohlcv = self.fetch_ohlcv(symbol)
                if df_ohlcv is None or len(df_ohlcv) < 10:
                    warn(f"Insufficient data for {symbol}, skipping")
                    continue
                
                # Simulate trade
                trade = self.simulate_trade(signal, df_ohlcv, idx)
                if trade:
                    self.trades.append(trade)
            
            except Exception as e:
                error(f"Error processing signal {idx}: {e}")
        
        # Calculate metrics
        metrics = self.calculate_metrics()
        
        # Print summary
        info("\n" + "=" * 70)
        info("📊 BACKTEST RESULTS")
        info("=" * 70)
        info(f"💰 Initial Capital: ${metrics.initial_capital:,.2f}")
        info(f"💵 Final Capital: ${metrics.final_capital:,.2f}")
        info(f"📈 Total Return: ${metrics.total_return:,.2f} ({metrics.total_return_pct:+.2f}%)")
        info(f"📊 Total Trades: {metrics.total_trades}")
        info(f"✅ Wins: {metrics.winning_trades} ({metrics.win_rate:.1f}%)")
        info(f"❌ Losses: {metrics.losing_trades}")
        info(f"💹 Profit Factor: {metrics.profit_factor:.2f}")
        info(f"🎯 Expectancy: ${metrics.expectancy:.2f} per trade")
        info(f"📉 Max Drawdown: ${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.2f}%)")
        info(f"📊 Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        info(f"💸 Total Fees: ${metrics.total_fees:,.2f}")
        info(f"📉 Total Slippage: ${metrics.total_slippage:,.2f}")
        info("=" * 70)
        
        return self.trades, metrics
