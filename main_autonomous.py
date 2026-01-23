"""
🤖 Main Autonomous System - Project Chimera
The Central Nervous System for 24/7 autonomous trading.

This is the infinite loop that ties all components together:
- Telegram Signal Listener
- Hybrid AI/Regex Parser
- Risk Sentinel
- CCXT Trading Engine
- Telegram Notifier

Features:
- Robust error recovery (auto-restart on crash)
- Daily report scheduling (00:00 UTC)
- Real-time notifications for all events
- Comprehensive logging
- Graceful shutdown handling

Author: Project Chimera Team
Version: 1.0.0
"""

import os
import sys
import asyncio
import signal
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telethon import TelegramClient, events
from telethon.tl.types import Message

from parsers.enhanced_parser import EnhancedParser, ParsedSignal
from trading.trading_engine import TradingEngine, Signal
from trading.risk_manager import RiskSentinel
from reporting.notifier import TelegramNotifier
from config.trading_config import SignalConfig, RiskConfig, TRADING_MODE
from utils.config import DEFAULT_LEVERAGE

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ChimeraAutonomous:
    """
    🧠 The Central Nervous System
    
    Coordinates all components for autonomous trading:
    1. Listen for Telegram signals
    2. Parse with Hybrid AI/Regex
    3. Validate with Risk Sentinel
    4. Execute with Trading Engine
    5. Notify admin of all events
    6. Generate daily reports
    """
    
    def __init__(
        self,
        initial_equity: float = 10000.0,
        trading_mode: str = "paper"
    ):
        """
        Initialize the autonomous system.
        
        Args:
            initial_equity: Starting capital in USDT
            trading_mode: "paper" or "live"
        """
        logger.info("="*60)
        logger.info("🚀 PROJECT CHIMERA - AUTONOMOUS SYSTEM")
        logger.info("="*60)
        
        # Core components
        self.parser = EnhancedParser()
        self.sentinel = RiskSentinel(initial_equity=initial_equity)
        self.engine = TradingEngine(mode=trading_mode)
        self.notifier = TelegramNotifier()
        
        # Telegram listener
        self.telegram_client: Optional[TelegramClient] = None
        self.channels: List[str] = []
        
        # State tracking
        self.running = False
        self.last_report_date = None
        self.messages_processed = 0
        self.signals_parsed = 0
        self.trades_executed = 0
        self.trades_rejected = 0
        
        # Performance metrics
        self.start_time = None
        self.last_message_time = None
        
        logger.info(f"💼 Initial Equity: {initial_equity:.2f} USDT")
        logger.info(f"⚙️  Trading Mode: {trading_mode.upper()}")
        logger.info(f"📢 Notifier: {'ENABLED' if self.notifier.enabled else 'DISABLED'}")
        
        # ✅ SAFETY RESET: Clear circuit breaker for paper trading
        if trading_mode == "paper":
            logger.info("🔄 SAFETY RESET: Clearing circuit breaker for paper trading...")
            self.sentinel.update_equity(initial_equity)
            logger.success(f"✅ Sentinel equity reset to ${initial_equity:.2f}")
        
        logger.info("="*60)
    
    async def initialize_telegram(self):
        """Initialize Telegram client for listening to channels."""
        try:
            api_id = os.getenv("TELEGRAM_API_ID")
            api_hash = os.getenv("TELEGRAM_API_HASH")
            phone = os.getenv("TELEGRAM_PHONE")
            
            if not all([api_id, api_hash, phone]):
                raise ValueError("Missing Telegram credentials. Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            
            # Create client
            self.telegram_client = TelegramClient(
                'autonomous_session',
                int(api_id),
                api_hash
            )
            
            # ✅ INTEGER ENFORCEMENT: Numeric IDs only
            channels_str = os.getenv("TELEGRAM_CHANNELS", "")
            raw_channels = [ch.strip() for ch in channels_str.split(",") if ch.strip()]
            
            self.channels = []
            for channel in raw_channels:
                try:
                    # Only accept numeric IDs (convert to int)
                    self.channels.append(int(channel))
                    logger.debug(f"✅ Added channel ID: {channel}")
                except ValueError:
                    # Skip non-numeric entries (e.g., @username)
                    logger.warn(f"⚠️  SKIPPED non-numeric channel: {channel} (only numeric IDs allowed)")
            
            if not self.channels:
                raise ValueError("❌ ERROR: No valid numeric channel IDs found! Check .env TELEGRAM_CHANNELS")
            
            logger.info(f"📡 Telegram client initialized for {len(self.channels)} integer channels")
            # ----------------------------------------------------
            
            # Start client
            await self.telegram_client.start(phone=phone)
            logger.success("✅ Telegram client connected")
            
            # Register message handler
            @self.telegram_client.on(events.NewMessage(chats=self.channels))
            async def handle_new_message(event):
                """Handle incoming Telegram messages."""
                await self._process_message(event.message)
            
            logger.info(f"👂 Listening to channels: {', '.join(str(c) for c in self.channels)}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram: {e}")
            raise
    
    async def _process_message(self, message: Message):
        """
        Process incoming Telegram message.
        
        Pipeline:
        1. Extract text
        2. Parse with Hybrid AI/Regex
        3. Validate with Risk Sentinel
        4. Execute with Trading Engine
        5. Notify admin
        """
        try:
            self.messages_processed += 1
            self.last_message_time = datetime.now()
            
            # Extract text
            text = message.text or message.message or ""
            if not text or len(text) < 10:
                return  # Too short to be a signal
            
            # 📩 VERBOSE: Log incoming message BEFORE parsing
            logger.info(f"📩 INCOMING MESSAGE: {text[:100]}...")
            
            # Parse signal (Hybrid AI/Regex)
            parsed_signal = await self.parser.parse(text)
            
            if not parsed_signal or not parsed_signal.symbol:
                # ❌ VERBOSE: Log when NOT a signal
                logger.debug(f"❌ NOT A SIGNAL: {text[:50]}...")
                return
            
            self.signals_parsed += 1
            
            # ✅ VERBOSE: Log valid signal detection
            logger.success(f"✅ SIGNAL DETECTED: {parsed_signal.symbol} {parsed_signal.side}")
            logger.info(
                f"📊 Parsed: {parsed_signal.symbol} {parsed_signal.side} "
                f"@ {parsed_signal.entry_min} (confidence: {parsed_signal.confidence:.2f})"
            )
            
            # Convert to Signal object for trading engine
            signal = Signal(
                symbol=parsed_signal.symbol,
                side=parsed_signal.side or "LONG",
                entry=parsed_signal.entry_min,
                tp=parsed_signal.tps[0] if parsed_signal.tps else None,
                sl=parsed_signal.sl,
                leverage=parsed_signal.leverage_x or DEFAULT_LEVERAGE,
                timestamp=parsed_signal.timestamp_iso,
                source="telegram"
            )
            
            # Get current positions for correlation check
            open_positions = self.engine.portfolio.get_all_positions()
            
            # Validate with Risk Sentinel
            validation_result = self.sentinel.validate_signal(
                symbol=signal.symbol,
                side=signal.side,
                entry=signal.entry or 0,
                sl=signal.sl or 0,
                tp=signal.tp or 0,
                open_positions=open_positions
            )
            
            if not validation_result.valid:
                # Signal rejected by Risk Sentinel
                self.trades_rejected += 1
                
                logger.warn(f"🚫 Signal REJECTED: {validation_result.reason}")
                
                # 📢 ALWAYS notify admin of parsed signals (even rejected)
                await self.notifier.send_trade_notification(
                    signal=parsed_signal,
                    success=False,
                    reason=validation_result.reason
                )
                
                # Send risk alert if critical
                if "circuit breaker" in validation_result.reason.lower():
                    await self.notifier.send_alert(
                        f"🔴 CIRCUIT BREAKER ACTIVE\n\n{validation_result.reason}",
                        critical=True
                    )
                elif "kill switch" in validation_result.reason.lower():
                    await self.notifier.send_alert(
                        f"🛑 KILL SWITCH ACTIVE\n\n{validation_result.reason}",
                        critical=True
                    )
                
                return
            
            # Signal approved - execute trade
            logger.success(f"✅ Signal APPROVED (confidence: {parsed_signal.confidence:.2f})")
            
            if validation_result.warnings:
                logger.warn(f"⚠️ Warnings: {', '.join(validation_result.warnings)}")
            
            # Execute via Trading Engine
            result = await self.engine.execute_signal(signal)
            
            if result:
                self.trades_executed += 1
                logger.success(f"✅ Trade EXECUTED: {signal.symbol} {signal.side}")
                
                # Update sentinel equity
                current_equity = self.engine.portfolio.get_equity()
                self.sentinel.update_equity(current_equity)
                
                # 📢 ALWAYS notify admin of executed trades (paper or live)
                await self.notifier.send_trade_notification(
                    signal=parsed_signal,
                    success=True
                )
            else:
                # Execution failed
                logger.error(f"❌ Trade FAILED: Unable to execute")
                
                await self.notifier.send_trade_notification(
                    signal=parsed_signal,
                    success=False,
                    reason="Execution failed"
                )
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            await self.notifier.send_error_notification(str(e), critical=False)
    
    async def check_daily_report(self):
        """
        Check if it's time to send daily report (00:00 UTC).
        """
        now_utc = datetime.now(timezone.utc)
        current_date = now_utc.date()
        
        # Check if we crossed midnight UTC
        if self.last_report_date != current_date and now_utc.hour == 0:
            logger.info("📊 Generating daily report...")
            
            try:
                # Get portfolio statistics
                portfolio_stats = self.engine.portfolio.get_statistics()
                
                # Get risk metrics
                risk_metrics = self.sentinel.get_risk_metrics()
                
                # Compile report
                report = {
                    "total_trades": portfolio_stats.get("total_trades", 0),
                    "winning_trades": portfolio_stats.get("winning_trades", 0),
                    "losing_trades": portfolio_stats.get("losing_trades", 0),
                    "total_pnl": portfolio_stats.get("total_pnl_realized", 0),
                    "win_rate": portfolio_stats.get("win_rate", 0),
                    "largest_win": portfolio_stats.get("largest_win", 0),
                    "largest_loss": portfolio_stats.get("largest_loss", 0),
                    "equity": self.engine.portfolio.get_equity(),
                    "open_positions": len(self.engine.portfolio.get_all_positions()),
                    "daily_pnl": risk_metrics.daily_pnl,
                    "daily_pnl_pct": risk_metrics.daily_pnl_pct,
                    "circuit_breaker_active": risk_metrics.circuit_breaker_active,
                    "kill_switch_active": risk_metrics.kill_switch_active
                }
                
                # Send report
                await self.notifier.send_daily_report(report)
                
                logger.success("✅ Daily report sent")
                self.last_report_date = current_date
                
                # Reset daily counters in sentinel (optional - sentinel auto-resets at midnight)
                # self.sentinel._reset_daily_counters()
            
            except Exception as e:
                logger.error(f"❌ Failed to generate daily report: {e}")
    
    async def run(self):
        """
        Main infinite loop.
        
        The bot runs forever, processing signals and handling errors gracefully.
        """
        self.running = True
        self.start_time = datetime.now()
        
        try:
            # Initialize Telegram
            await self.initialize_telegram()
            
            # Send startup notification
            await self.notifier.send_startup_notification()
            
            logger.success("🚀 Autonomous system is LIVE!")
            logger.info("Press Ctrl+C to stop...")
            
            # Main loop
            while self.running:
                try:
                    # Check for daily report (every minute)
                    await self.check_daily_report()
                    
                    # Keep connection alive
                    await asyncio.sleep(60)  # Check every minute
                
                except asyncio.CancelledError:
                    logger.info("⏸️ Loop cancelled")
                    break
                
                except Exception as e:
                    # Catch any error in the main loop
                    logger.error(f"❌ Error in main loop: {e}")
                    
                    # Send error notification
                    await self.notifier.send_error_notification(str(e), critical=True)
                    
                    # Wait before continuing
                    logger.info("⏱️ Waiting 10 seconds before restart...")
                    await asyncio.sleep(10)
                    
                    # Auto-restart the loop
                    logger.info("🔄 Restarting loop...")
        
        except KeyboardInterrupt:
            logger.info("⏹️ Keyboard interrupt received")
            await self.shutdown("User interrupt (Ctrl+C)")
        
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            await self.shutdown(f"Fatal error: {e}")
        
        finally:
            if self.running:
                await self.shutdown("System exit")
    
    async def shutdown(self, reason: str = "Normal shutdown"):
        """
        Graceful shutdown.
        
        Args:
            reason: Reason for shutdown
        """
        if not self.running:
            return
        
        self.running = False
        
        logger.info("="*60)
        logger.info("🛑 SHUTTING DOWN PROJECT CHIMERA")
        logger.info("="*60)
        
        # Print final statistics
        runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        logger.info(f"⏱️  Runtime: {runtime}")
        logger.info(f"📨 Messages Processed: {self.messages_processed}")
        logger.info(f"📊 Signals Parsed: {self.signals_parsed}")
        logger.info(f"✅ Trades Executed: {self.trades_executed}")
        logger.info(f"🚫 Trades Rejected: {self.trades_rejected}")
        
        # Send shutdown notification
        await self.notifier.send_shutdown_notification(reason)
        
        # Close connections
        if self.telegram_client:
            await self.telegram_client.disconnect()
            logger.info("📡 Telegram client disconnected")
        
        if self.engine:
            await self.engine.close()
            logger.info("🔧 Trading engine closed")
        
        if self.notifier:
            await self.notifier.close()
            logger.info("📢 Notifier closed")
        
        logger.info("="*60)
        logger.success("✅ Shutdown complete. Goodbye!")
        logger.info("="*60)


# ============================================
# Entry Point
# ============================================
async def main():
    """Main entry point."""
    # Load configuration
    initial_equity = float(os.getenv("ACCOUNT_EQUITY_USDT", "10000"))
    trading_mode = os.getenv("TRADING_MODE", "paper").lower()
    
    # Create autonomous system
    chimera = ChimeraAutonomous(
        initial_equity=initial_equity,
        trading_mode=trading_mode
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        """Handle Ctrl+C and kill signals."""
        logger.info(f"📡 Signal {sig} received")
        asyncio.create_task(chimera.shutdown(f"Signal {sig}"))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the system
    await chimera.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
