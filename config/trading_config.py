"""
🎯 Trading Configuration
Centralized settings for backtest/paper/live trading modes.
"""
from pathlib import Path
from typing import Literal

# ============================================================================
# TRADING MODE
# ============================================================================
TradingMode = Literal["backtest", "paper", "live"]

TRADING_MODE: TradingMode = "paper"  # backtest | paper | live

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
class RiskConfig:
    """Position sizing and risk controls."""
    
    # Capital allocation
    INITIAL_CAPITAL = 10000.0  # USDT
    MAX_POSITION_SIZE_PCT = 0.10  # 10% of capital per trade
    MIN_POSITION_SIZE_USDT = 10.0  # Minimum order size
    
    # Risk limits
    MAX_CONCURRENT_TRADES = 5  # Maximum open positions
    DAILY_LOSS_LIMIT_PCT = 0.05  # 5% daily loss → stop trading
    WEEKLY_LOSS_LIMIT_PCT = 0.15  # 15% weekly loss → stop trading
    MAX_DRAWDOWN_PCT = 0.25  # 25% drawdown → emergency stop
    
    # Leverage (futures only)
    USE_LEVERAGE = False
    MAX_LEVERAGE = 3  # 1-5x recommended
    
    # Order execution
    SLIPPAGE_TOLERANCE_PCT = 0.005  # 0.5% max slippage
    ORDER_TIMEOUT_SECONDS = 30  # Cancel after 30s if not filled


# ============================================================================
# PAPER TRADING
# ============================================================================
class PaperConfig:
    """Paper trading simulator settings."""
    
    INITIAL_BALANCE = 10000.0  # Starting virtual balance
    SIMULATE_FEES = True
    MAKER_FEE = 0.0002  # 0.02% maker fee
    TAKER_FEE = 0.0006  # 0.06% taker fee
    SIMULATE_SLIPPAGE = True
    AVG_SLIPPAGE_PCT = 0.001  # 0.1% average slippage
    
    # Portfolio file
    PORTFOLIO_FILE = Path("data/paper_portfolio.json")
    TRADES_LOG = Path("data/paper_trades.jsonl")


# ============================================================================
# LIVE TRADING
# ============================================================================
class LiveConfig:
    """Live trading on MEXC."""
    
    # API settings (from .env)
    USE_TESTNET = False  # Set True for testnet
    
    # Safety mechanisms
    REQUIRE_CONFIRMATION = True  # Manual approval before first trade
    DRY_RUN_FIRST = True  # Validate order before submitting
    ENABLE_EMERGENCY_STOP = True  # Kill switch via file
    EMERGENCY_STOP_FILE = Path("data/EMERGENCY_STOP")
    
    # Order types
    DEFAULT_ORDER_TYPE = "MARKET"  # MARKET | LIMIT
    USE_POST_ONLY = False  # Limit orders only (no market taking)
    
    # Position tracking
    SYNC_INTERVAL_SECONDS = 10  # Sync positions every 10s
    POSITIONS_FILE = Path("data/live_positions.json")
    TRADES_LOG = Path("data/live_trades.jsonl")


# ============================================================================
# SIGNAL PROCESSING
# ============================================================================
class SignalConfig:
    """Real-time signal handling."""
    
    # Telegram listener
    ENABLE_REAL_TIME = True  # Listen to channels live
    POLL_INTERVAL_SECONDS = 5  # Check new messages every 5s
    
    # Signal validation
    VALIDATE_SYMBOL = True  # Check symbol exists on exchange
    MIN_SIGNAL_CONFIDENCE = 0.0  # Future: confidence scoring
    BLACKLIST_CHANNELS = []  # Skip these channels (low performance)
    
    # Duplicate detection
    DEDUPE_WINDOW_MINUTES = 10  # Same signal within 10 min = duplicate
    
    # Signal queue
    SIGNALS_QUEUE_FILE = Path("data/signal_queue.jsonl")
    MAX_QUEUE_SIZE = 100


# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================
class AnalyticsConfig:
    """Performance monitoring and reporting."""
    
    # Metrics calculation
    TRACK_METRICS = True
    METRICS_FILE = Path("data/performance_metrics.json")
    
    # Alerts
    ENABLE_ALERTS = True
    ALERT_ON_WIN = False  # Don't spam on wins
    ALERT_ON_LOSS = True  # Alert on losses
    ALERT_ON_EMERGENCY = True  # Critical alerts
    
    # Reporting
    DAILY_SUMMARY = True  # Generate daily reports
    REPORT_DIR = Path("data/reports")


# ============================================================================
# LOGGING
# ============================================================================
class LogConfig:
    """Logging configuration."""
    
    LOG_DIR = Path("logs")
    LOG_LEVEL = "INFO"  # DEBUG | INFO | WARNING | ERROR
    
    # Separate log files
    TRADING_LOG = LOG_DIR / "trading.log"
    ORDERS_LOG = LOG_DIR / "orders.log"
    RISK_LOG = LOG_DIR / "risk.log"
    ERRORS_LOG = LOG_DIR / "errors.log"
    
    # Rotation
    MAX_LOG_SIZE_MB = 50
    BACKUP_COUNT = 5


# ============================================================================
# DIRECTORIES
# ============================================================================
def ensure_directories():
    """Create required directories if they don't exist."""
    dirs = [
        Path("data"),
        Path("logs"),
        AnalyticsConfig.REPORT_DIR,
        LogConfig.LOG_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate configuration settings."""
    errors = []
    
    # Risk checks
    if RiskConfig.MAX_POSITION_SIZE_PCT > 0.25:
        errors.append("⚠️ MAX_POSITION_SIZE_PCT > 25% is very risky!")
    
    if RiskConfig.MAX_CONCURRENT_TRADES > 10:
        errors.append("⚠️ MAX_CONCURRENT_TRADES > 10 needs high capital")
    
    if LiveConfig.USE_TESTNET and TRADING_MODE == "live":
        print("✅ Using MEXC testnet for live trading (safe)")
    
    if not LiveConfig.REQUIRE_CONFIRMATION and TRADING_MODE == "live":
        errors.append("⚠️ Live trading without confirmation is dangerous!")
    
    # Capital checks
    if RiskConfig.INITIAL_CAPITAL < 1000 and TRADING_MODE == "live":
        errors.append("⚠️ Capital < $1000 may have issues with min order sizes")
    
    if errors:
        print("\n🚨 Configuration Warnings:")
        for err in errors:
            print(f"  {err}")
        print()
    
    return len(errors) == 0


# ============================================================================
# INITIALIZATION
# ============================================================================
if __name__ == "__main__":
    print("📋 Trading Configuration")
    print("=" * 80)
    print(f"Mode:              {TRADING_MODE.upper()}")
    print(f"Initial Capital:   ${RiskConfig.INITIAL_CAPITAL:,.2f}")
    print(f"Max Position:      {RiskConfig.MAX_POSITION_SIZE_PCT*100:.1f}%")
    print(f"Max Trades:        {RiskConfig.MAX_CONCURRENT_TRADES}")
    print(f"Daily Loss Limit:  {RiskConfig.DAILY_LOSS_LIMIT_PCT*100:.1f}%")
    print(f"Emergency Stop:    {LiveConfig.ENABLE_EMERGENCY_STOP}")
    print("=" * 80)
    
    ensure_directories()
    is_valid = validate_config()
    
    if is_valid:
        print("✅ Configuration valid!")
    else:
        print("⚠️ Please review warnings above")
