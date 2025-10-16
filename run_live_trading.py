"""
🔴 Live Trading Launcher
Start automated live trading with REAL MONEY.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.trading_config import (
    TRADING_MODE, LiveConfig, RiskConfig,
    ensure_directories, validate_config
)
from trading.trading_engine import TradingEngine
from telegram.signal_listener import SignalListener
from utils.logger import info, error, success, warn


def check_preconditions() -> bool:
    """Verify live trading preconditions (STRICT CHECKS)."""
    # Check mode
    if TRADING_MODE != "live":
        error(f"❌ TRADING_MODE must be 'live' (current: {TRADING_MODE})")
        error("   Update config/trading_config.py: TRADING_MODE = 'live'")
        return False
    
    # Check for emergency stop file
    if LiveConfig.EMERGENCY_STOP_FILE.exists():
        error(f"❌ EMERGENCY STOP FILE EXISTS: {LiveConfig.EMERGENCY_STOP_FILE}")
        error("   Remove it to enable live trading")
        return False
    
    # Check MEXC API credentials
    try:
        from utils.config import MEXC_API_KEY, MEXC_API_SECRET
        if not MEXC_API_KEY or not MEXC_API_SECRET:
            error("❌ MEXC API credentials not configured!")
            error("   Set MEXC_API_KEY and MEXC_API_SECRET in .env")
            return False
    except ImportError:
        error("❌ Cannot import MEXC credentials from utils.config")
        return False
    
    # Check portfolio file
    if LiveConfig.POSITIONS_FILE.exists():
        warn(f"⚠️ Existing live positions found: {LiveConfig.POSITIONS_FILE}")
        response = input("   Continue with existing positions? (y/n): ")
        if response.lower() != 'y':
            info("   Exiting...")
            return False
    
    return True


def confirm_live_trading() -> bool:
    """Get explicit user confirmation for live trading."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              ⚠️  LIVE TRADING CONFIRMATION ⚠️               ║
║                                                              ║
║  YOU ARE ABOUT TO START TRADING WITH REAL MONEY!            ║
║                                                              ║
║  Risks:                                                      ║
║   • You can lose ALL your capital                           ║
║   • Market conditions can change rapidly                    ║
║   • Technical issues may occur                              ║
║   • No guarantees of profit                                 ║
║                                                              ║
║  Safety mechanisms:                                          ║
║   ✅ Daily loss limit: 5%                                   ║
║   ✅ Weekly loss limit: 15%                                 ║
║   ✅ Max drawdown: 25%                                      ║
║   ✅ Emergency stop file                                    ║
║   ✅ Max concurrent trades: 5                               ║
║                                                              ║
║  By proceeding, you acknowledge:                            ║
║   • You understand the risks                                ║
║   • You accept full responsibility                          ║
║   • You have tested in paper trading                        ║
║   • You are using capital you can afford to lose            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Triple confirmation
    print("Type 'I UNDERSTAND THE RISKS' to continue (case-sensitive):")
    response1 = input("> ")
    
    if response1 != "I UNDERSTAND THE RISKS":
        error("❌ Confirmation failed. Exiting...")
        return False
    
    print("\nType 'START LIVE TRADING' to proceed (case-sensitive):")
    response2 = input("> ")
    
    if response2 != "START LIVE TRADING":
        error("❌ Confirmation failed. Exiting...")
        return False
    
    print("\nFinal confirmation - type 'YES' (case-sensitive):")
    response3 = input("> ")
    
    if response3 != "YES":
        error("❌ Confirmation failed. Exiting...")
        return False
    
    return True


def print_banner():
    """Print live trading banner."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          🔴 LIVE TRADING MODE - ACTIVE                      ║
║                                                              ║
║  ⚠️  REAL MONEY - REAL RISK                                ║
║                                                              ║
║  Initial Capital: ${RiskConfig.INITIAL_CAPITAL:,.2f} USDT                          ║
║  Max Position: {RiskConfig.MAX_POSITION_SIZE_PCT*100}% (${RiskConfig.INITIAL_CAPITAL * RiskConfig.MAX_POSITION_SIZE_PCT:,.2f})                            ║
║  Max Concurrent: {RiskConfig.MAX_CONCURRENT_TRADES} trades                                   ║
║  Daily Loss Limit: {RiskConfig.DAILY_LOSS_LIMIT_PCT*100}% (${RiskConfig.INITIAL_CAPITAL * RiskConfig.DAILY_LOSS_LIMIT_PCT:,.2f})                          ║
║  Max Drawdown: {RiskConfig.MAX_DRAWDOWN_PCT*100}% (${RiskConfig.INITIAL_CAPITAL * RiskConfig.MAX_DRAWDOWN_PCT:,.2f})                        ║
║                                                              ║
║  📊 Positions: data/live_positions.json                     ║
║  📝 Trades Log: data/live_trades.jsonl                      ║
║  📡 Signal Listener: ACTIVE                                 ║
║  🛑 Emergency Stop: {LiveConfig.EMERGENCY_STOP_FILE}                 ║
║                                                              ║
║  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
║                                                              ║
║  ⚠️  CREATE EMERGENCY_STOP FILE TO HALT TRADING            ║
║  Press Ctrl+C to stop gracefully                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def create_safety_instructions():
    """Create emergency stop instructions file."""
    instructions_file = Path("EMERGENCY_STOP_INSTRUCTIONS.txt")
    
    content = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🛑 EMERGENCY STOP INSTRUCTIONS                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

TO IMMEDIATELY HALT LIVE TRADING:

Windows PowerShell:
    New-Item -Path "data\EMERGENCY_STOP" -ItemType File

Windows CMD:
    type nul > data\EMERGENCY_STOP

Linux/Mac:
    touch data/EMERGENCY_STOP


The trading system will stop immediately when it detects this file.

To resume trading:
1. Delete the EMERGENCY_STOP file
2. Restart the trading script


⚠️  IMPORTANT NOTES:

• This stops NEW trades only - existing positions remain open
• You may need to manually close positions via MEXC
• Always check your MEXC account after emergency stop
• Do not resume trading until you understand why you stopped


For urgent issues:
1. Create EMERGENCY_STOP file
2. Close this terminal window (Ctrl+C)
3. Log into MEXC and manually close positions
4. Contact support if needed

═══════════════════════════════════════════════════════════════
"""
    
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    info(f"📄 Emergency stop instructions: {instructions_file}")


async def run_live_trading():
    """Run live trading with signal listener."""
    try:
        # Initialize trading engine
        info("🚀 Initializing Trading Engine...")
        engine = TradingEngine(mode="live")
        
        # Initialize signal listener
        info("📡 Initializing Signal Listener...")
        listener = SignalListener(engine)
        
        # Fetch recent signals
        info("🔄 Fetching recent signals from Telegram...")
        await listener.fetch_recent_signals(limit=10)
        
        # Process any queued signals
        engine.process_signal_queue()
        
        # Print initial portfolio
        if engine.portfolio:
            engine.portfolio.print_summary()
        
        success("✅ Live trading started successfully!")
        warn("⚠️  TRADING WITH REAL MONEY - Monitor closely!")
        info("👂 Listening for new signals... (Create EMERGENCY_STOP file to halt)")
        
        # Run both engine and listener concurrently
        await asyncio.gather(
            engine.run_async(),
            listener.listen()
        )
    
    except KeyboardInterrupt:
        warn("\n⏹️ Stopping live trading...")
    except Exception as e:
        error(f"❌ Live trading error: {e}")
        raise
    finally:
        # Print final summary
        if engine.portfolio:
            print("\n" + "="*60)
            warn("📊 Final Portfolio Summary:")
            engine.portfolio.print_summary()
            print("="*60)
        
        info("💡 Check your MEXC account for any open positions!")


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
    
    # Get user confirmation
    if LiveConfig.REQUIRE_CONFIRMATION:
        if not confirm_live_trading():
            sys.exit(1)
    
    # Create safety instructions
    create_safety_instructions()
    
    # Print banner
    print_banner()
    
    # Run live trading
    try:
        asyncio.run(run_live_trading())
    except KeyboardInterrupt:
        warn("\n👋 Live trading stopped by user")
    except Exception as e:
        error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
