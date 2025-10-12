"""
Configuration module - loads environment variables and provides constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------------------- Paths --------------------
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))
TZ = os.getenv("TZ", "Europe/Sofia")

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# -------------------- Trading --------------------
DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "15m")
MAX_CANDLES = int(os.getenv("MAX_CANDLES", "1000"))
EXCHANGE_NAME = os.getenv("EXCHANGE", "mexc")

# -------------------- Telegram --------------------
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
TELEGRAM_CHANNELS = [
    c.strip() for c in os.getenv("TELEGRAM_CHANNELS", "").split(",") if c.strip()
]

# -------------------- Risk Management --------------------
ACCOUNT_EQUITY_USDT = float(os.getenv("ACCOUNT_EQUITY_USDT", "1000"))
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "2"))
DAILY_MAX_LOSS_PCT = float(os.getenv("DAILY_MAX_LOSS_PCT", "5.0"))
LEVERAGE = float(os.getenv("LEVERAGE", "5"))

# -------------------- Validation --------------------
if TELEGRAM_API_ID == 0:
    print("[WARNING] TELEGRAM_API_ID not set in .env file")
if not TELEGRAM_API_HASH:
    print("[WARNING] TELEGRAM_API_HASH not set in .env file")
if not TELEGRAM_PHONE:
    print("[WARNING] TELEGRAM_PHONE not set in .env file")
if not TELEGRAM_CHANNELS:
    print("[WARNING] TELEGRAM_CHANNELS not set in .env file")
