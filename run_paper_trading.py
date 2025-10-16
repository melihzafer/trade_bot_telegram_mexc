"""
🎯 Paper Trading Launcher
Start automated paper trading with real-time signals.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.trading_config import (
    TRADING_MODE, PaperConfig,
    ensure_directories, validate_config
)
from trading.trading_engine import TradingEngine
from telegram.signal_listener import SignalListener
from utils.logger import info, error, success, warn


def check_preconditions():
    """Verify paper trading preconditions."""
    # Check mode
    if TRADING_MODE != "paper":
        error(f"❌ TRADING_MODE must be 'paper' (current: {TRADING_MODE})")
        error("   Update config/trading_config.py: TRADING_MODE = 'paper'")
        return False
    
    # Check portfolio file
    if PaperConfig.PORTFOLIO_FILE.exists():
        warn(f"⚠️ Existing portfolio found: {PaperConfig.PORTFOLIO_FILE}")
        response = input("   Continue with existing portfolio? (y/n): ")
        if response.lower() != 'y':
            info("   Exiting...")
            return False
    
    return True


def print_banner():
    """Print startup banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🎯 PAPER TRADING MODE - ACTIVE                     ║
║                                                              ║
║  ⚠️  SIMULATED TRADING - NO REAL MONEY INVOLVED            ║
║                                                              ║
║  Initial Balance: $10,000 USDT                              ║
║  Max Position: 10% ($1,000)                                 ║
║  Max Concurrent: 5 trades                                   ║
║  Daily Loss Limit: 5% ($500)                                ║
║  Max Drawdown: 25% ($2,500)                                 ║
║                                                              ║
║  📊 Portfolio: data/paper_portfolio.json                    ║
║  📝 Trades Log: data/paper_trades.jsonl                     ║
║  📡 Signal Listener: ACTIVE                                 ║
║                                                              ║
║  Press Ctrl+C to stop gracefully                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


async def run_paper_trading():
    """Run paper trading with signal listener."""
    try:
        # Initialize trading engine
        info("🚀 Initializing Trading Engine...")
        engine = TradingEngine(mode="paper")
        
        # Initialize signal listener
        info("📡 Initializing Signal Listener...")
        listener = SignalListener(engine)
        
        # Fetch recent signals
        info("🔄 Fetching recent signals from Telegram...")
        await listener.fetch_recent_signals(limit=20)
        
        # Process any queued signals
        engine.process_signal_queue()
        
        # Print initial portfolio
        if engine.portfolio:
            engine.portfolio.print_summary()
        
        success("✅ Paper trading started successfully!")
        info("👂 Listening for new signals... (Press Ctrl+C to stop)")
        
        # Run both engine and listener concurrently
        await asyncio.gather(
            engine.run_async(),
            listener.listen()
        )
    
    except KeyboardInterrupt:
        info("\n⏹️ Stopping paper trading...")
    except Exception as e:
        error(f"❌ Paper trading error: {e}")
        raise
    finally:
        # Print final summary
        if engine.portfolio:
            print("\n" + "="*60)
            info("📊 Final Portfolio Summary:")
            engine.portfolio.print_summary()
            print("="*60)


def main():
    """Main entry point."""
    # Ensure directories exist
    ensure_directories()
    
    # Validate configuration
    if not validate_config():
        error("❌ Configuration validation failed!")
        sys.exit(1)
    
    # Check preconditions
    if not check_preconditions():
        sys.exit(1)
    
    # Print banner
    print_banner()
    
    # Run paper trading
    try:
        asyncio.run(run_paper_trading())
    except KeyboardInterrupt:
        info("\n👋 Paper trading stopped by user")
    except Exception as e:
        error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
