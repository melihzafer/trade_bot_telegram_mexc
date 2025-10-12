"""
Utility module.

Components:
- config: Environment variable loading and validation
- logger: Rich console + file logging
- timeutils: Timezone management for timestamps
"""

from .config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    TELEGRAM_CHANNELS,
    EXCHANGE_NAME,
    DEFAULT_TIMEFRAME,
    ACCOUNT_EQUITY_USDT,
    RISK_PER_TRADE_PCT,
    MAX_CONCURRENT_POSITIONS,
    DAILY_MAX_LOSS_PCT,
    LEVERAGE,
    DATA_DIR,
    LOG_DIR,
    TZ,
)
from .logger import info, warn, error, success, debug
from .timeutils import (
    get_timezone,
    now_utc,
    now_local,
    to_utc,
    to_local,
    format_datetime,
)

__all__ = [
    # Config
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "TELEGRAM_PHONE",
    "TELEGRAM_CHANNELS",
    "EXCHANGE_NAME",
    "DEFAULT_TIMEFRAME",
    "ACCOUNT_EQUITY_USDT",
    "RISK_PER_TRADE_PCT",
    "MAX_CONCURRENT_POSITIONS",
    "DAILY_MAX_LOSS_PCT",
    "LEVERAGE",
    "DATA_DIR",
    "LOG_DIR",
    "TZ",
    # Logger
    "info",
    "warn",
    "error",
    "success",
    "debug",
    # Timeutils
    "get_timezone",
    "now_utc",
    "now_local",
    "to_utc",
    "to_local",
    "format_datetime",
]
