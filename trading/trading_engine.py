"""
🚀 Unified Trading Engine
Orchestrates backtest → paper → live trading pipeline.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass

from config.trading_config import (
    TradingMode, TRADING_MODE,
    RiskConfig, PaperConfig, LiveConfig, SignalConfig
)
from trading.portfolio import Portfolio
from utils.logger import info, warn, error, success
from utils.binance_api import BinanceClient


@dataclass
class Signal:
    """Trading signal from Telegram."""
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry: Optional[float] = None  # None = market order
    tp: Optional[float] = None
    sl: Optional[float] = None
    timestamp: str = None
    source: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TradingEngine:
    """Main trading engine for all modes."""
    
    def __init__(self, mode: TradingMode = TRADING_MODE):
        self.mode = mode
        info(f"🚀 Trading Engine initialized in {mode.upper()} mode")
        
        # Initialize components based on mode
        if mode == "paper":
            self.portfolio = Portfolio(
                initial_balance=PaperConfig.INITIAL_BALANCE,
                portfolio_file=PaperConfig.PORTFOLIO_FILE
            )
            self.trades_log = PaperConfig.TRADES_LOG
        elif mode == "live":
            self.portfolio = Portfolio(
                initial_balance=RiskConfig.INITIAL_CAPITAL,
                portfolio_file=LiveConfig.POSITIONS_FILE
            )
            self.trades_log = LiveConfig.TRADES_LOG
            self._check_emergency_stop()
        else:  # backtest
            self.portfolio = None  # Backtest uses separate logic
        
        # Price client (Binance for now, MEXC when connection fixed)
        self.price_client = BinanceClient()
        
        # Signal queue
        self.signal_queue = []
        self.signal_queue_file = SignalConfig.SIGNALS_QUEUE_FILE
        self._load_signal_queue()
    
    def _check_emergency_stop(self):
        """Check for emergency stop file."""
        if LiveConfig.ENABLE_EMERGENCY_STOP:
            if LiveConfig.EMERGENCY_STOP_FILE.exists():
                error("🚨 EMERGENCY STOP FILE EXISTS! Remove it to continue.")
                raise RuntimeError("Trading halted by emergency stop")
    
    def _load_signal_queue(self):
        """Load pending signals from disk."""
        if not self.signal_queue_file.exists():
            return
        
        try:
            with open(self.signal_queue_file, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    self.signal_queue.append(Signal(**data))
            
            info(f"📥 Loaded {len(self.signal_queue)} pending signals")
        except Exception as e:
            error(f"❌ Failed to load signal queue: {e}")
    
    def _save_signal_queue(self):
        """Save signal queue to disk."""
        try:
            self.signal_queue_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.signal_queue_file, 'w', encoding='utf-8') as f:
                for signal in self.signal_queue:
                    f.write(json.dumps(signal.__dict__, ensure_ascii=False) + '\n')
        except Exception as e:
            error(f"❌ Failed to save signal queue: {e}")
    
    def add_signal(self, signal: Signal):
        """Add signal to queue."""
        self.signal_queue.append(signal)
        self._save_signal_queue()
        info(f"➕ Signal queued: {signal.side} {signal.symbol}")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price."""
        try:
            price_data = self.price_client.get_current_price(symbol)
            if price_data:
                return float(price_data['price'])
            return None
        except Exception as e:
            error(f"❌ Failed to get price for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, symbol: str, entry_price: float) -> float:
        """Calculate position size based on risk rules."""
        equity = self.portfolio.get_equity()
        max_position_value = equity * RiskConfig.MAX_POSITION_SIZE_PCT
        
        # Ensure minimum
        if max_position_value < RiskConfig.MIN_POSITION_SIZE_USDT:
            max_position_value = RiskConfig.MIN_POSITION_SIZE_USDT
        
        quantity = max_position_value / entry_price
        return quantity
    
    def execute_signal_paper(self, signal: Signal) -> bool:
        """Execute signal in paper trading mode."""
        # Get entry price
        entry_price = signal.entry
        if entry_price is None:
            # Market order - get current price
            entry_price = self.get_current_price(signal.symbol)
            if entry_price is None:
                error(f"❌ Cannot get price for {signal.symbol}")
                return False
        
        # Calculate position size
        quantity = self.calculate_position_size(signal.symbol, entry_price)
        
        # Simulate fees if enabled
        fees = 0.0
        if PaperConfig.SIMULATE_FEES:
            position_value = entry_price * quantity
            fees = position_value * PaperConfig.TAKER_FEE
        
        # Simulate slippage if enabled
        if PaperConfig.SIMULATE_SLIPPAGE:
            slippage = entry_price * PaperConfig.AVG_SLIPPAGE_PCT
            if signal.side == "LONG":
                entry_price += slippage
            else:
                entry_price -= slippage
        
        # Open position
        success_open = self.portfolio.open_position(
            symbol=signal.symbol,
            side=signal.side,
            entry_price=entry_price,
            quantity=quantity,
            tp=signal.tp,
            sl=signal.sl
        )
        
        if success_open:
            # Log trade
            self._log_trade({
                'action': 'OPEN',
                'symbol': signal.symbol,
                'side': signal.side,
                'entry_price': entry_price,
                'quantity': quantity,
                'tp': signal.tp,
                'sl': signal.sl,
                'fees': fees,
                'timestamp': datetime.now().isoformat()
            })
            return True
        
        return False
    
    def execute_signal_live(self, signal: Signal) -> bool:
        """Execute signal in live trading mode."""
        # Safety checks
        self._check_emergency_stop()
        
        if LiveConfig.REQUIRE_CONFIRMATION:
            warn("⚠️ Live trading requires manual confirmation!")
            # TODO: Implement confirmation mechanism
            return False
        
        # TODO: Implement MEXC order execution
        error("❌ Live trading not yet implemented!")
        return False
    
    def execute_signal(self, signal: Signal) -> bool:
        """Execute signal based on mode."""
        # Check if already have position
        if self.portfolio.has_position(signal.symbol):
            warn(f"⚠️ Already have position for {signal.symbol}, skipping")
            return False
        
        # Check risk limits
        open_count = self.portfolio.get_open_position_count()
        if open_count >= RiskConfig.MAX_CONCURRENT_TRADES:
            warn(f"⚠️ Max concurrent trades ({RiskConfig.MAX_CONCURRENT_TRADES}) reached")
            return False
        
        # Execute based on mode
        if self.mode == "paper":
            return self.execute_signal_paper(signal)
        elif self.mode == "live":
            return self.execute_signal_live(signal)
        else:
            error(f"❌ Cannot execute signal in {self.mode} mode")
            return False
    
    def check_exit_conditions(self):
        """Check TP/SL for all open positions."""
        if not self.portfolio:
            return
        
        for symbol, position in list(self.portfolio.positions.items()):
            current_price = self.get_current_price(symbol)
            if current_price is None:
                continue
            
            # Update unrealized PnL
            position.update_pnl(current_price)
            
            # Check TP
            if position.tp:
                if position.side == "LONG" and current_price >= position.tp:
                    self._close_position(symbol, current_price, "TP")
                elif position.side == "SHORT" and current_price <= position.tp:
                    self._close_position(symbol, current_price, "TP")
            
            # Check SL
            if position.sl:
                if position.side == "LONG" and current_price <= position.sl:
                    self._close_position(symbol, current_price, "SL")
                elif position.side == "SHORT" and current_price >= position.sl:
                    self._close_position(symbol, current_price, "SL")
    
    def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close a position."""
        # Calculate fees
        fees = 0.0
        if self.mode == "paper" and PaperConfig.SIMULATE_FEES:
            position = self.portfolio.get_position(symbol)
            if position:
                position_value = exit_price * position.quantity
                fees = position_value * PaperConfig.TAKER_FEE
        
        # Close position
        success_close = self.portfolio.close_position(symbol, exit_price, reason, fees)
        
        if success_close:
            # Log trade
            self._log_trade({
                'action': 'CLOSE',
                'symbol': symbol,
                'exit_price': exit_price,
                'reason': reason,
                'fees': fees,
                'timestamp': datetime.now().isoformat()
            })
    
    def _log_trade(self, trade_data: dict):
        """Log trade to file."""
        try:
            self.trades_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trades_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_data, ensure_ascii=False) + '\n')
        except Exception as e:
            error(f"❌ Failed to log trade: {e}")
    
    def process_signal_queue(self):
        """Process all pending signals."""
        if not self.signal_queue:
            return
        
        info(f"🔄 Processing {len(self.signal_queue)} queued signals...")
        
        executed = 0
        failed = 0
        
        # Process each signal
        for signal in list(self.signal_queue):
            if self.execute_signal(signal):
                executed += 1
                self.signal_queue.remove(signal)
            else:
                failed += 1
        
        # Save updated queue
        self._save_signal_queue()
        
        info(f"✅ Executed: {executed}, Failed: {failed}, Remaining: {len(self.signal_queue)}")
    
    async def run_async(self):
        """Run trading engine asynchronously."""
        info(f"🏃 Trading engine running in {self.mode.upper()} mode...")
        
        try:
            while True:
                # Check emergency stop for live mode
                if self.mode == "live":
                    self._check_emergency_stop()
                
                # Process queued signals
                self.process_signal_queue()
                
                # Check exit conditions for open positions
                self.check_exit_conditions()
                
                # Update portfolio
                if self.portfolio:
                    # Get all current prices
                    prices = {}
                    for symbol in self.portfolio.positions.keys():
                        price = self.get_current_price(symbol)
                        if price:
                            prices[symbol] = price
                    
                    self.portfolio.update_positions(prices)
                
                # Sleep based on mode
                if self.mode == "paper":
                    await asyncio.sleep(SignalConfig.POLL_INTERVAL_SECONDS)
                elif self.mode == "live":
                    await asyncio.sleep(LiveConfig.SYNC_INTERVAL_SECONDS)
                else:
                    break  # Exit loop for backtest mode
        
        except KeyboardInterrupt:
            info("⏹️ Trading engine stopped by user")
        except Exception as e:
            error(f"❌ Trading engine error: {e}")
            raise
        finally:
            if self.portfolio:
                self.portfolio.print_summary()
    
    def run(self):
        """Run trading engine synchronously."""
        asyncio.run(self.run_async())


if __name__ == "__main__":
    # Test trading engine
    engine = TradingEngine(mode="paper")
    
    # Add test signal
    signal = Signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=None,  # Market order
        tp=115000,
        sl=109000
    )
    
    engine.add_signal(signal)
    
    # Process signals
    engine.process_signal_queue()
    
    # Check positions
    engine.portfolio.print_summary()
