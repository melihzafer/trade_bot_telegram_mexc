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
# Environment & Config
TELEGRAM_CHANNELS = [
    c.strip() for c in os.getenv("TELEGRAM_CHANNELS", "").split(",") if c.strip()
]

# Separate channel list for backtesting (optional - falls back to TELEGRAM_CHANNELS)
BACKTEST_CHANNELS = [
    c.strip() for c in os.getenv("BACKTEST_CHANNELS", "").split(",") if c.strip()
]
if not BACKTEST_CHANNELS:
    BACKTEST_CHANNELS = TELEGRAM_CHANNELS

# -------------------- Risk Management --------------------
ACCOUNT_EQUITY_USDT = float(os.getenv("ACCOUNT_EQUITY_USDT", "1000"))
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "2"))
DAILY_MAX_LOSS_PCT = float(os.getenv("DAILY_MAX_LOSS_PCT", "5.0"))
LEVERAGE = float(os.getenv("LEVERAGE", "5"))

# -------------------- Paper Trading --------------------
PAPER_TRADING_CHANNELS = [
    int(c.strip()) for c in os.getenv("PAPER_TRADING_CHANNELS", "").split(",") if c.strip()
]
PAPER_TRADING_ENABLED = os.getenv("PAPER_TRADING_ENABLED", "true").lower() == "true"
PAPER_INITIAL_BALANCE = float(os.getenv("PAPER_INITIAL_BALANCE", "10000"))
PAPER_POSITION_SIZE_PCT = float(os.getenv("PAPER_POSITION_SIZE_PCT", "5"))

# -------------------- AI Parser (Multi-Provider) --------------------
# OpenRouter (DeepSeek R1)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")

# Local API (e.g., LM Studio, Gemini)
LOCAL_AI_URL = os.getenv("LOCAL_AI_URL", "")
LOCAL_AI_KEY = os.getenv("LOCAL_AI_KEY", "")
LOCAL_AI_MODEL = os.getenv("LOCAL_AI_MODEL", "gemini-3-flash")

# Ollama (Local LLMs)
OLLAMA_URL = os.getenv("OLLAMA_URL", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_CONTEXT_SIZE = int(os.getenv("OLLAMA_CONTEXT_SIZE", "8192"))  # 8k for speed
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", OLLAMA_MODEL)  # Legacy compatibility

# Groq (Fast cloud inference)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Default Trading Rules
DEFAULT_ENTRY_TYPE = os.getenv("DEFAULT_ENTRY_TYPE", "MARKET")
DEFAULT_LEVERAGE = float(os.getenv("DEFAULT_LEVERAGE", "15"))
MAX_LOSS_PCT = float(os.getenv("MAX_LOSS_PCT", "30"))
MAX_PROFIT_PCT = float(os.getenv("MAX_PROFIT_PCT", "100"))

# Take Profit Ratios (R multiples)
TP1_RATIO = float(os.getenv("TP1_RATIO", "1.0"))
TP2_RATIO = float(os.getenv("TP2_RATIO", "2.0"))
TP3_RATIO = float(os.getenv("TP3_RATIO", "3.0"))

# -------------------- Validation --------------------
if TELEGRAM_API_ID == 0:
    print("[WARNING] TELEGRAM_API_ID not set in .env file")
if not TELEGRAM_API_HASH:
    print("[WARNING] TELEGRAM_API_HASH not set in .env file")
if not TELEGRAM_PHONE:
    print("[WARNING] TELEGRAM_PHONE not set in .env file")
if not TELEGRAM_CHANNELS:
    print("[WARNING] TELEGRAM_CHANNELS not set in .env file")
if PAPER_TRADING_ENABLED and not PAPER_TRADING_CHANNELS:
    print("[WARNING] PAPER_TRADING_CHANNELS not set but paper trading is enabled")
