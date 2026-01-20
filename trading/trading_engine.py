"""
🚀 Unified Trading Engine - Phase 2 (Project Chimera)
CCXT-powered live trading with robust error handling & risk management.

Features:
- Paper trading (simulated)
- Live trading (Binance Futures via CCXT)
- Async operation
- Position size calculation
- Leverage management
- Order execution (Market/Limit)
- TP/SL monitoring
- Symbol normalization (BTCUSDT → BTC/USDT)
- Precision handling
- Error recovery
"""
import os
import asyncio
import json
import ccxt.async_support as ccxt
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass

from config.trading_config import (
    TradingMode, TRADING_MODE,
    RiskConfig, PaperConfig, LiveConfig, SignalConfig
)
from trading.portfolio import Portfolio

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from utils.binance_api import BinanceClient
except ImportError:
    BinanceClient = None


@dataclass
class Signal:
    """Trading signal from Telegram."""
    symbol: str
    side: Literal["LONG", "SHORT", "long", "short"]
    entry: Optional[float] = None  # None = market order
    tp: Optional[float] = None
    sl: Optional[float] = None
    leverage: Optional[int] = None
    timestamp: str = None
    source: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        # Normalize side to uppercase
        if self.side:
            self.side = self.side.upper()


class TradingEngine:
    """
    Main trading engine supporting PAPER and LIVE modes.
    
    Architecture:
    - Paper Mode: Simulated execution with portfolio tracking
    - Live Mode: Real Binance Futures orders via CCXT
    """
    
    def __init__(self, mode: TradingMode = TRADING_MODE):
        self.mode = mode
        logger.info(f"🚀 Trading Engine initializing in {mode.upper()} mode...")
        
        # Initialize CCXT exchange (live mode only)
        self.exchange = None
        self.markets = {}  # Cache market info for precision
        if mode == "live":
            asyncio.run(self._initialize_exchange())
        
        # Initialize portfolio tracking
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
            self.portfolio = None
        
        # Price client fallback (if CCXT fails)
        self.price_client = None
        if BinanceClient:
            try:
                self.price_client = BinanceClient()
            except Exception as e:
                logger.warn(f"⚠️  Binance price client unavailable: {e}")
        
        # Signal queue
        self.signal_queue = []
        self.signal_queue_file = SignalConfig.SIGNALS_QUEUE_FILE
        self._load_signal_queue()
        
        # Statistics
        self.stats = {
            'signals_processed': 0,
            'trades_executed': 0,
            'trades_failed': 0,
            'total_fees_paid': 0.0
        }
        
        logger.success(f"✅ Trading Engine ready in {mode.upper()} mode")
    
    async def _initialize_exchange(self):
        """Initialize CCXT exchange connection for live trading (async)."""
        try:
            # Load API credentials from environment
            api_key = os.getenv("BINANCE_API_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")
            
            if not api_key or not api_secret:
                logger.error("❌ BINANCE_API_KEY or BINANCE_API_SECRET not set in environment!")
                raise ValueError("Missing Binance API credentials")
            
            # Initialize Binance exchange
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures by default
                    'adjustForTimeDifference': True,  # Auto-adjust for server time
                }
            })
            
            logger.info("✅ CCXT exchange initialized (Binance Futures)")
            
            # Load markets (for precision handling)
            try:
                self.markets = await self.exchange.load_markets()
                logger.info(f"✅ Loaded {len(self.markets)} market pairs")
            except Exception as e:
                logger.warn(f"⚠️ Failed to load markets: {e}")
            
            # Set position mode to One-Way (not Hedge)
            try:
                await self.exchange.fapiPrivate_post_positionside_dual({
                    'dualSidePosition': 'false'
                })
                logger.info("✅ Position mode set to One-Way")
            except Exception as e:
                logger.warn(f"⚠️ Failed to set position mode (may already be set): {e}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize CCXT exchange: {e}")
            raise
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to Binance format (BTC/USDT).
        
        Telegram signals usually come as BTCUSDT, but Binance CCXT requires BTC/USDT.
        
        Args:
            symbol: Symbol in any format (BTCUSDT, BTC/USDT, etc.)
        
        Returns:
            Normalized symbol (BTC/USDT)
        """
        # If already has slash, return as-is
        if '/' in symbol:
            return symbol.upper()
        
        # Common patterns: BTCUSDT, ETHUSDT, etc.
        symbol = symbol.upper()
        
        # Try to split based on USDT suffix
        if symbol.endswith('USDT'):
            base = symbol[:-4]  # Remove USDT
            return f"{base}/USDT"
        
        # Try other quote currencies
        for quote in ['BUSD', 'USDC', 'USD', 'BTC', 'ETH']:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        
        # If no match, assume USDT and add slash before last 4 chars
        logger.warn(f"⚠️ Could not parse symbol {symbol}, assuming /USDT")
        return f"{symbol[:-4]}/USDT"
    
    def _check_emergency_stop(self):
        """Check for emergency stop file."""
        if LiveConfig.ENABLE_EMERGENCY_STOP:
            if LiveConfig.EMERGENCY_STOP_FILE.exists():
                logger.error("🚨 EMERGENCY STOP FILE EXISTS! Remove it to continue.")
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
            
            logger.info(f"📥 Loaded {len(self.signal_queue)} pending signals")
        except Exception as e:
            logger.error(f"❌ Failed to load signal queue: {e}")
    
    def _save_signal_queue(self):
        """Save signal queue to disk."""
        try:
            self.signal_queue_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.signal_queue_file, 'w', encoding='utf-8') as f:
                for signal in self.signal_queue:
                    f.write(json.dumps(signal.__dict__, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"❌ Failed to save signal queue: {e}")
    
    def add_signal(self, signal: Signal):
        """Add signal to queue."""
        self.signal_queue.append(signal)
        self._save_signal_queue()
        logger.info(f"➕ Signal queued: {signal.side} {signal.symbol}")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price (async).
        
        Priority:
        1. CCXT exchange (if live mode)
        2. Binance client (fallback)
        
        Args:
            symbol: Trading pair (BTCUSDT or BTC/USDT)
        
        Returns:
            Current price or None
        """
        # Normalize symbol
        normalized_symbol = self._normalize_symbol(symbol)
        
        try:
            # Try CCXT first (if available)
            if self.exchange:
                ticker = await self.exchange.fetch_ticker(normalized_symbol)
                return float(ticker['last'])
            
            # Fallback to Binance client (sync)
            if self.price_client:
                # Remove slash for Binance client
                symbol_no_slash = symbol.replace('/', '')
                price_data = self.price_client.get_current_price(symbol_no_slash)
                if price_data:
                    return float(price_data['price'])
            
            logger.warn(f"⚠️  No price source available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get price for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, symbol: str, entry_price: float, leverage: int = 1) -> Dict[str, float]:
        """
        Calculate position size based on risk management rules.
        
        Returns:
            dict with 'quantity', 'position_value', 'margin_required'
        """
        equity = self.portfolio.get_equity()
        
        # Calculate max position value (percentage of equity)
        max_position_value = equity * RiskConfig.MAX_POSITION_SIZE_PCT
        
        # Ensure minimum
        if max_position_value < RiskConfig.MIN_POSITION_SIZE_USDT:
            max_position_value = RiskConfig.MIN_POSITION_SIZE_USDT
        
        # Apply leverage (if futures)
        if leverage > 1:
            # With leverage, we can control more with less margin
            position_value = max_position_value * leverage
            margin_required = max_position_value
        else:
            position_value = max_position_value
            margin_required = max_position_value
        
        # Calculate quantity
        quantity = position_value / entry_price
        
        return {
            'quantity': quantity,
            'position_value': position_value,
            'margin_required': margin_required
        }
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol (futures only).
        
        Args:
            symbol: Trading pair (will be normalized)
            leverage: Leverage multiplier (1-125 depending on symbol)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.exchange or self.mode != "live":
            logger.debug(f"📝 Would set leverage {leverage}x for {symbol}")
            return True
        
        # Normalize symbol
        normalized_symbol = self._normalize_symbol(symbol)
        
        try:
            # Binance leverage setting
            await self.exchange.set_leverage(leverage, normalized_symbol)
            logger.info(f"⚙️  Leverage set to {leverage}x for {normalized_symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set leverage for {normalized_symbol}: {e}")
            return False
    
    async def execute_signal_paper(self, signal: Signal) -> bool:
        """
        Execute signal in paper trading mode (simulated).
        
        Args:
            signal: Parsed trading signal
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📝 Paper trading: {signal.side} {signal.symbol}")
        
        # Get entry price
        entry_price = signal.entry
        if entry_price is None:
            # Market order - get current price
            entry_price = await self.get_current_price(signal.symbol)
            if entry_price is None:
                logger.error(f"❌ Cannot get price for {signal.symbol}")
                return False
        
        # Get leverage (default to 1 if not specified)
        leverage = signal.leverage if signal.leverage else 1
        
        # Calculate position size
        size_info = self.calculate_position_size(signal.symbol, entry_price, leverage)
        quantity = size_info['quantity']
        
        # Simulate fees if enabled
        fees = 0.0
        if PaperConfig.SIMULATE_FEES:
            position_value = size_info['position_value']
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
            sl=signal.sl,
            margin_required=size_info['margin_required']
        )
        
        if success_open:
            # Log trade
            self._log_trade({
                'mode': 'PAPER',
                'action': 'OPEN',
                'symbol': signal.symbol,
                'side': signal.side,
                'entry_price': entry_price,
                'quantity': quantity,
                'leverage': leverage,
                'tp': signal.tp,
                'sl': signal.sl,
                'fees': fees,
                'margin_used': size_info['margin_required'],
                'timestamp': datetime.now().isoformat()
            })
            
            self.stats['trades_executed'] += 1
            self.stats['total_fees_paid'] += fees
            
            logger.success(
                f"✅ Paper trade opened: {signal.side} {quantity:.4f} {signal.symbol} "
                f"@ {entry_price:.2f} (Leverage: {leverage}x)"
            )
            return True
        
        return False
    
    async def execute_signal_live(self, signal: Signal) -> bool:
        """
        Execute signal in live trading mode using CCXT.
        
        Args:
            signal: Parsed trading signal
        
        Returns:
            True if successful, False otherwise
        """
        if not self.exchange:
            logger.error("❌ Exchange not initialized!")
            return False
        
        # Normalize symbol
        normalized_symbol = self._normalize_symbol(signal.symbol)
        
        logger.info(f"🔴 LIVE TRADING: {signal.side} {normalized_symbol}")
        
        # Safety checks
        self._check_emergency_stop()
        
        if LiveConfig.REQUIRE_CONFIRMATION:
            logger.warn("⚠️  Live trading requires manual confirmation!")
            # TODO: Implement confirmation mechanism (e.g., webhook, Telegram)
            return False
        
        try:
            # Get current price
            current_price = await self.get_current_price(normalized_symbol)
            if current_price is None:
                logger.error(f"❌ Cannot get price for {normalized_symbol}")
                return False
            
            # Determine entry price
            entry_price = signal.entry if signal.entry else current_price
            
            # Get leverage (default to 1 if not specified)
            leverage = signal.leverage if signal.leverage else RiskConfig.MAX_LEVERAGE
            
            # Set leverage (futures only)
            if leverage > 1:
                leverage_set = await self.set_leverage(normalized_symbol, leverage)
                if not leverage_set:
                    logger.warn(f"⚠️  Leverage setting failed, continuing anyway...")
            
            # Calculate position size
            size_info = self.calculate_position_size(normalized_symbol, entry_price, leverage)
            quantity = size_info['quantity']
            
            # Apply precision (critical for Binance!)
            if normalized_symbol in self.markets:
                market = self.markets[normalized_symbol]
                quantity = float(self.exchange.amount_to_precision(normalized_symbol, quantity))
                entry_price = float(self.exchange.price_to_precision(normalized_symbol, entry_price))
                logger.info(f"🎯 Applied precision: quantity={quantity}, price={entry_price}")
            else:
                logger.warn(f"⚠️  Market info not available for {normalized_symbol}, using raw values")
            
            # Determine order type
            order_type = "market" if signal.entry is None else LiveConfig.DEFAULT_ORDER_TYPE.lower()
            
            # Determine side for CCXT (buy/sell)
            ccxt_side = "buy" if signal.side == "LONG" else "sell"
            
            logger.info(f"📤 Placing {order_type.upper()} order: {ccxt_side} {quantity:.4f} {normalized_symbol} @ {entry_price:.2f}")
            
            # DRY RUN CHECK
            if LiveConfig.DRY_RUN_FIRST:
                logger.warn(f"🧪 DRY RUN: Would place order but not executing (set DRY_RUN_FIRST=False to execute)")
                self._log_trade({
                    'mode': 'LIVE_DRY_RUN',
                    'action': 'OPEN',
                    'symbol': normalized_symbol,
                    'side': signal.side,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'leverage': leverage,
                    'order_type': order_type,
                    'tp': signal.tp,
                    'sl': signal.sl,
                    'timestamp': datetime.now().isoformat()
                })
                return True
            
            # Place order via CCXT
            order = None
            if order_type == "market":
                order = await self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='market',
                    side=ccxt_side,
                    amount=quantity
                )
            else:  # limit order
                order = await self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='limit',
                    side=ccxt_side,
                    amount=quantity,
                    price=entry_price
                )
            
            if order:
                logger.success(f"✅ Order placed successfully! Order ID: {order.get('id')}")
                
                # Log order details
                fill_price = order.get('price') or order.get('average') or entry_price
                fees_paid = order.get('fee', {}).get('cost', 0.0)
                
                # Open position in portfolio tracker
                self.portfolio.open_position(
                    symbol=normalized_symbol,
                    side=signal.side,
                    entry_price=fill_price,
                    quantity=quantity,
                    tp=signal.tp,
                    sl=signal.sl
                )
                
                # Log trade
                self._log_trade({
                    'mode': 'LIVE',
                    'action': 'OPEN',
                    'symbol': normalized_symbol,
                    'side': signal.side,
                    'entry_price': fill_price,
                    'quantity': quantity,
                    'leverage': leverage,
                    'order_type': order_type,
                    'order_id': order.get('id'),
                    'tp': signal.tp,
                    'sl': signal.sl,
                    'fees': fees_paid,
                    'margin_used': size_info['margin_required'],
                    'timestamp': datetime.now().isoformat()
                })
                
                self.stats['trades_executed'] += 1
                self.stats['total_fees_paid'] += fees_paid
                
                return True
            
            logger.error("❌ Order placement failed - no order returned")
            return False
        
        except ccxt.InsufficientFunds as e:
            logger.error(f"❌ Insufficient funds: {e}")
            return False
        
        except ccxt.InvalidOrder as e:
            logger.error(f"❌ Invalid order: {e}")
            return False
        
        except ccxt.NetworkError as e:
            logger.error(f"❌ Network error: {e}")
            return False
        
        except ccxt.ExchangeError as e:
            logger.error(f"❌ Exchange error: {e}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error during order execution: {type(e).__name__}: {e}")
            return False
    
    async def execute_signal(self, signal: Signal) -> bool:
        """
        Execute signal based on current mode (async).
        
        Args:
            signal: Parsed trading signal
        
        Returns:
            True if successful, False otherwise
        """
        self.stats['signals_processed'] += 1
        
        # Check if already have position
        if self.portfolio.has_position(signal.symbol):
            logger.warn(f"⚠️  Already have position for {signal.symbol}, skipping")
            return False
        
        # Check risk limits
        open_count = self.portfolio.get_open_position_count()
        if open_count >= RiskConfig.MAX_CONCURRENT_TRADES:
            logger.warn(f"⚠️  Max concurrent trades ({RiskConfig.MAX_CONCURRENT_TRADES}) reached")
            return False
        
        # Execute based on mode
        if self.mode == "paper":
            return await self.execute_signal_paper(signal)
        elif self.mode == "live":
            return await self.execute_signal_live(signal)
        else:
            logger.error(f"❌ Cannot execute signal in {self.mode} mode")
            return False
    
    async def check_exit_conditions(self):
        """Check TP/SL for all open positions (async)."""
        if not self.portfolio:
            return
        
        for symbol, position in list(self.portfolio.positions.items()):
            current_price = await self.get_current_price(symbol)
            if current_price is None:
                continue
            
            # Update unrealized PnL
            position.update_pnl(current_price)
            
            # Check TP
            if position.tp:
                if position.side == "LONG" and current_price >= position.tp:
                    await self._close_position(symbol, current_price, "TP")
                elif position.side == "SHORT" and current_price <= position.tp:
                    await self._close_position(symbol, current_price, "TP")
            
            # Check SL
            if position.sl:
                if position.side == "LONG" and current_price <= position.sl:
                    await self._close_position(symbol, current_price, "SL")
                elif position.side == "SHORT" and current_price >= position.sl:
                    await self._close_position(symbol, current_price, "SL")
    
    async def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close a position (async)."""
        position = self.portfolio.get_position(symbol)
        if not position:
            logger.warn(f"⚠️  Position not found: {symbol}")
            return
        
        # Normalize symbol
        normalized_symbol = self._normalize_symbol(symbol)
        
        logger.info(f"🔒 Closing position: {normalized_symbol} @ {exit_price:.2f} (Reason: {reason})")
        
        # Calculate fees
        fees = 0.0
        
        # Live trading: execute close order via CCXT
        if self.mode == "live" and self.exchange:
            try:
                # Determine side (opposite of entry)
                ccxt_side = "sell" if position.side == "LONG" else "buy"
                
                # Get precise quantity
                quantity = position.quantity
                if normalized_symbol in self.markets:
                    quantity = float(self.exchange.amount_to_precision(normalized_symbol, quantity))
                
                logger.info(f"📤 Placing close order: {ccxt_side} {quantity:.4f} {normalized_symbol}")
                
                # Place market order to close
                order = await self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='market',
                    side=ccxt_side,
                    amount=quantity
                )
                
                if order:
                    logger.success(f"✅ Close order placed! Order ID: {order.get('id')}")
                    exit_price = order.get('price') or order.get('average') or exit_price
                    fees = order.get('fee', {}).get('cost', 0.0)
                else:
                    logger.error(f"❌ Failed to place close order for {normalized_symbol}")
                    return
            
            except Exception as e:
                logger.error(f"❌ Error closing position via CCXT: {e}")
                return
        
        # Paper trading: simulate fees
        elif self.mode == "paper" and PaperConfig.SIMULATE_FEES:
            position_value = exit_price * position.quantity
            fees = position_value * PaperConfig.TAKER_FEE
        
        # Close position in portfolio tracker
        success_close = self.portfolio.close_position(normalized_symbol, exit_price, reason, fees)
        
        if success_close:
            # Log trade
            self._log_trade({
                'mode': self.mode.upper(),
                'action': 'CLOSE',
                'symbol': normalized_symbol,
                'side': position.side,
                'exit_price': exit_price,
                'reason': reason,
                'fees': fees,
                'pnl': position.realized_pnl,
                'timestamp': datetime.now().isoformat()
            })
            
            self.stats['total_fees_paid'] += fees
            
            logger.success(f"✅ Position closed: {normalized_symbol} | PnL: {position.realized_pnl:.2f} USDT")
    
    def _log_trade(self, trade_data: dict):
        """Log trade to file."""
        try:
            self.trades_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trades_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_data, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"❌ Failed to log trade: {e}")
    
    async def process_signal_queue(self):
        """Process all pending signals (async)."""
        if not self.signal_queue:
            return
        
        logger.info(f"🔄 Processing {len(self.signal_queue)} queued signals...")
        
        executed = 0
        failed = 0
        
        # Process each signal
        for signal in list(self.signal_queue):
            if await self.execute_signal(signal):
                executed += 1
                self.signal_queue.remove(signal)
            else:
                failed += 1
        
        # Save updated queue
        self._save_signal_queue()
        
        logger.info(f"✅ Executed: {executed}, Failed: {failed}, Remaining: {len(self.signal_queue)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trading engine statistics."""
        stats = self.stats.copy()
        
        if self.portfolio:
            stats['equity'] = self.portfolio.get_equity()
            stats['open_positions'] = self.portfolio.get_open_position_count()
            stats['total_trades'] = len(self.portfolio.trade_history)
        
        return stats
    
    async def run_async(self):
        """Run trading engine asynchronously."""
        logger.info(f"🏃 Trading engine running in {self.mode.upper()} mode...")
        
        try:
            while True:
                # Check emergency stop for live mode
                if self.mode == "live":
                    self._check_emergency_stop()
                
                # Process queued signals
                await self.process_signal_queue()
                
                # Check exit conditions for open positions
                await self.check_exit_conditions()
                
                # Update portfolio
                if self.portfolio:
                    # Get all current prices
                    prices = {}
                    for symbol in list(self.portfolio.positions.keys()):
                        price = await self.get_current_price(symbol)
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
            logger.info("⏹️  Trading engine stopped by user")
        except Exception as e:
            logger.error(f"❌ Trading engine error: {e}")
            raise
        finally:
            # Cleanup
            if self.exchange:
                await self.exchange.close()
                logger.info("🔌 CCXT exchange connection closed")
            
            if self.portfolio:
                self.portfolio.print_summary()
            
            # Print statistics
            logger.info("📊 Trading Statistics:")
            stats = self.get_stats()
            for key, value in stats.items():
                logger.info(f"   {key}: {value}")
    
    def run(self):
        """Run trading engine synchronously."""
        asyncio.run(self.run_async())
    
    async def start(self):
        """Initialize and start the trading engine."""
        logger.info("🚀 Trading Engine starting...")
        if self.mode == "live" and not self.exchange:
            await self._initialize_exchange()
    
    async def stop(self):
        """Gracefully shut down the trading engine (alias for close)."""
        logger.info("🛑 Trading Engine stopping...")
        await self.close()
    
    async def close(self):
        """Close the trading engine and cleanup resources."""
        if self.exchange:
            await self.exchange.close()
            logger.info("🔌 CCXT exchange connection closed")
    
    async def execute_parsed_signal(self, parsed_signal):
        """
        Execute a ParsedSignal object from the enhanced parser.
        
        Args:
            parsed_signal: ParsedSignal object from EnhancedParser
        
        Returns:
            True if successful, False otherwise
        """
        # Convert ParsedSignal to Signal
        signal = Signal(
            symbol=parsed_signal.symbol,
            side=parsed_signal.side.upper() if parsed_signal.side else "LONG",
            entry=parsed_signal.entry_min,  # Use first entry
            tp=parsed_signal.tps[0] if parsed_signal.tps else None,  # Use first TP
            sl=parsed_signal.sl,
            leverage=parsed_signal.leverage_x,
            source=parsed_signal.source
        )
        
        return await self.execute_signal(signal)


if __name__ == "__main__":
    # Test trading engine
    import asyncio
    
    async def main():
        engine = TradingEngine(mode="paper")
        
        # Add test signal
        signal = Signal(
            symbol="BTCUSDT",
            side="LONG",
            entry=None,  # Market order
            tp=115000.0,
            sl=109000.0,
            leverage=5
        )
        
        engine.add_signal(signal)
        
        # Process signals
        await engine.process_signal_queue()
        
        # Check positions
        if engine.portfolio:
            engine.portfolio.print_summary()
        
        # Print stats
        print("\n📊 Stats:", engine.get_stats())
        
        # Close exchange if open
        if engine.exchange:
            await engine.exchange.close()
    
    asyncio.run(main())
