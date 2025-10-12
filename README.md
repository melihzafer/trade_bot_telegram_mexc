# 🤖 MEXC Multi-Source Trading System

> **Production-lean MVP for backtesting and paper trading crypto signals from multiple Telegram channels**

A robust Python system that collects trading signals from Telegram, backtests them against historical data, and simulates live trading with paper accounts—all without risking real capital.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Components](#-components)
- [Risk Management](#-risk-management)
- [Limitations](#-limitations)
- [Roadmap](#-roadmap)
- [Security](#-security)
- [License](#-license)

---

## ✨ Features

### Core Capabilities
- **Multi-Channel Telegram Collector**: Monitors multiple channels simultaneously using Telethon
- **Intelligent Signal Parser**: Regex-based extraction of BUY/SELL, ENTRY, TP, SL from messages
- **Full Backtest Engine**: Tests signals against MEXC historical OHLCV data
- **Paper Trading**: Live simulation with virtual positions and real-time pricing
- **Risk Management**: Position limits, daily loss caps, leverage control
- **Comprehensive Logging**: Rich console output + rotating log files

### Data Flow
```
Telegram → Raw JSONL → Parsed CSV → Backtest Results
                ↓
         Paper Trader → Virtual P&L
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MAIN ORCHESTRATOR                     │
│                      (main.py)                           │
└───────────┬─────────────────────────────────┬───────────┘
            │                                 │
    ┌───────▼────────┐                ┌──────▼───────┐
    │   TELEGRAM     │                │   TRADING    │
    │   COLLECTOR    │─────┐          │   ENGINE     │
    │  (Telethon)    │     │          │              │
    └────────────────┘     │          └──────────────┘
                           │                 │
                    ┌──────▼──────┐         │
                    │   PARSER    │         │
                    │  (Regex)    │         │
                    └──────┬──────┘         │
                           │                │
                    ┌──────▼──────┐  ┌──────▼────────┐
                    │ BACKTESTER  │  │ PAPER TRADER  │
                    │   (ccxt)    │  │   (Virtual)   │
                    └─────────────┘  └───────────────┘
```

---

## 📦 Requirements

- **Python**: 3.10 or higher
- **Telegram Account**: Active account with API credentials
- **Internet Connection**: For Telegram + MEXC API access

### System Dependencies
- No additional system packages required (pure Python)

---

## 🚀 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd trade_bot_telegram_mexc
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy sample env file
copy .env.sample .env  # Windows
cp .env.sample .env    # Linux/Mac

# Edit .env with your credentials
```

---

## ⚙️ Configuration

### Get Telegram API Credentials
1. Visit [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number
3. Create a new application
4. Copy `api_id` and `api_hash`

### Configure `.env` File
```env
# Telegram
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+905551234567
TELEGRAM_CHANNELS=@crypto_signals,@btc_alerts,@scalpers

# Risk Management
ACCOUNT_EQUITY_USDT=1000
RISK_PER_TRADE_PCT=1.0
MAX_CONCURRENT_POSITIONS=2
DAILY_MAX_LOSS_PCT=5.0
LEVERAGE=5

# Trading
DEFAULT_TIMEFRAME=15m
TZ=Europe/Sofia
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_API_ID` | Telegram API ID from my.telegram.org | - | ✅ |
| `TELEGRAM_API_HASH` | Telegram API hash | - | ✅ |
| `TELEGRAM_PHONE` | Your phone number with country code | - | ✅ |
| `TELEGRAM_CHANNELS` | Comma-separated channel list | - | ✅ |
| `ACCOUNT_EQUITY_USDT` | Initial virtual balance | 1000 | ❌ |
| `RISK_PER_TRADE_PCT` | Risk per trade as % of equity | 1.0 | ❌ |
| `MAX_CONCURRENT_POSITIONS` | Max open positions | 2 | ❌ |
| `DAILY_MAX_LOSS_PCT` | Daily loss circuit breaker | 5.0 | ❌ |
| `LEVERAGE` | Position leverage multiplier | 5 | ❌ |
| `DEFAULT_TIMEFRAME` | Candle timeframe for backtest | 15m | ❌ |
| `TZ` | Timezone for timestamps | Europe/Sofia | ❌ |

---

## 🎯 Usage

### Mode 1: Full System (Default)
Runs collector, parser, and paper trader concurrently.

```bash
python main.py
```

or

```bash
python main.py --mode full
```

**What happens:**
- Telegram collector listens to configured channels
- Parser processes messages every 5 seconds
- Paper trader opens/closes virtual positions based on signals

Press `Ctrl+C` to stop gracefully.

---

### Mode 2: Collector Only
Gather messages without trading (recommended for initial setup).

```bash
python main.py --mode collector
```

**What happens:**
- Only Telegram listener runs
- Raw messages saved to `data/signals_raw.jsonl`
- No parsing or trading occurs

**Use case:** Collect signals for 24-48h before backtesting.

---

### Mode 3: Backtest Only
Test historical performance without live trading.

```bash
python main.py --mode backtest
```

**What happens:**
- Reads `data/signals_parsed.csv`
- Fetches historical OHLCV from MEXC
- Evaluates TP/SL hits
- Saves results to `data/backtest_results.csv`

**Output:**
```
📊 Backtest Results Summary
══════════════════════════════════════════════════
Total Signals: 150
✅ Wins: 87
❌ Losses: 45
⏳ Open: 12
⚠️  Errors: 6
📈 Win Rate: 65.91%
```

---

### Standalone Components

#### Run Parser Manually
```bash
python telegram/parser.py
```

#### Run Backtester Manually
```bash
python trading/backtester.py
```

#### Run Paper Trader Manually
```bash
python trading/paper_trader.py
```

---

## 📂 Project Structure

```
trade_bot_telegram_mexc/
│
├── main.py                      # Main orchestrator
├── requirements.txt             # Python dependencies
├── .env.sample                  # Environment template
├── .env                         # Your config (gitignored)
├── PROJECT_PLAN.md              # Original spec
├── README.md                    # This file
│
├── telegram/
│   ├── collector.py             # Multi-channel Telethon listener
│   └── parser.py                # Signal extraction engine
│
├── trading/
│   ├── models.py                # Pydantic data models
│   ├── backtester.py            # Historical simulation
│   ├── paper_trader.py          # Live paper trading
│   └── risk_manager.py          # Risk controls
│
├── utils/
│   ├── config.py                # Environment loader
│   ├── logger.py                # Rich console + file logging
│   └── timeutils.py             # Timezone helpers
│
├── data/                        # Data files (gitignored)
│   ├── signals_raw.jsonl        # Raw Telegram messages
│   ├── signals_parsed.csv       # Extracted signals
│   └── backtest_results.csv     # Backtest outcomes
│
└── logs/                        # Log files (gitignored)
    └── runtime.log              # System logs
```

---

## 🧩 Components

### 1. Telegram Collector (`telegram/collector.py`)
- **Technology**: Telethon (async MTProto client)
- **Function**: Listens to multiple channels, saves raw messages to JSONL
- **Output**: `data/signals_raw.jsonl` (append-only)

**Example Message:**
```json
{"source": "@crypto_signals", "ts": "2025-10-12T14:30:00", "text": "BUY BTCUSDT ENTRY 64800 TP 65500 SL 64200"}
```

---

### 2. Signal Parser (`telegram/parser.py`)
- **Technology**: Regex pattern matching
- **Function**: Extracts structured signals from raw text
- **Output**: `data/signals_parsed.csv`

**Regex Pattern:**
```regex
\b(BUY|SELL)\b\s+([A-Z]{2,10}USDT)\b.*?
(?:ENTRY[:\s]*([0-9]+\.?[0-9]*))?.*?
(?:TP[:\s]*([0-9]+\.?[0-9]*))?.*?
(?:SL[:\s]*([0-9]+\.?[0-9]*))?
```

**Channel-Specific Parsers:**
Future versions will support custom parser profiles per channel (e.g., TP1/TP2/TP3).

---

### 3. Backtester (`trading/backtester.py`)
- **Technology**: ccxt (MEXC exchange API)
- **Function**: Fetches OHLCV, tests signals, calculates outcomes
- **Output**: `data/backtest_results.csv`

**Algorithm:**
1. For each signal, fetch 1000 candles (15m default)
2. Look ahead 96 candles (24h) from signal timestamp
3. Check if TP or SL hit first
4. Record WIN/LOSS/OPEN/ERROR

**Limitations:**
- Uses latest 1000 candles (not timestamp-specific yet)
- No slippage/fee simulation

---

### 4. Paper Trader (`trading/paper_trader.py`)
- **Technology**: ccxt public API (live pricing)
- **Function**: Simulates trading with virtual positions
- **Features**:
  - Position sizing based on risk %
  - Real-time TP/SL monitoring
  - PnL tracking
  - No real orders placed

**Flow:**
```
Signal → Calculate Position Size → Open Virtual Position
         ↓
   Monitor Live Price → Check TP/SL → Close & Record PnL
```

---

### 5. Risk Manager (`trading/risk_manager.py`)
- **Function**: Enforces safety limits
- **Controls**:
  - Max concurrent positions
  - Daily loss circuit breaker
  - Position size calculation
  - Order validation (TP/SL sanity checks)

---

## 🛡️ Risk Management

### Position Sizing Formula
```
Risk Amount = Account Equity × (Risk % / 100)

Position Size = (Risk Amount / |Entry - SL|) × Leverage / Entry
```

**Example:**
- Equity: $1000
- Risk per trade: 1% = $10
- Entry: $64,800
- SL: $64,200
- Risk per unit: $600
- Nominal size: $10 / $600 = 0.0167 BTC
- With 5x leverage: ~0.0129 BTC position

### Safety Limits
- **Max Positions**: Prevents overexposure (default: 2)
- **Daily Loss Cap**: Circuit breaker at -5% (default)
- **Leverage Control**: Multiplier applied to position size (default: 5x)

---

## ⚠️ Limitations

### Current Constraints
1. **No Real Orders**: Paper trading only, educational use
2. **Backtest Limitations**:
   - No timestamp-based OHLCV fetching (uses latest candles)
   - No fee/slippage simulation
   - Lookahead bias possible
3. **Parser Simplicity**: Single regex pattern (channel-specific profiles not yet implemented)
4. **No Web Dashboard**: Terminal-based only
5. **MEXC Public API**: Rate limits may apply

### Not Included
- Live order execution
- MEXC Futures testnet integration
- Multi-exchange support
- Advanced indicators (RSI, MA, etc.)
- Webhook notifications
- Database storage

---

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Multi-channel Telegram collector
- [x] Basic signal parser
- [x] Full backtest engine
- [x] Paper trader with virtual positions
- [x] Risk manager
- [x] Comprehensive logging

### Phase 2 (Next)
- [ ] Channel-specific parser profiles
- [ ] Timestamp-based backtest (eliminate lookahead bias)
- [ ] Fee & slippage simulation
- [ ] Flask dashboard with live charts
- [ ] Webhook/Discord notifications
- [ ] Daily performance reports

### Phase 3 (Future)
- [ ] MEXC Futures testnet integration
- [ ] Advanced signal filters (volatility, spread, R:R)
- [ ] Multi-TP management (TP1/TP2/TP3)
- [ ] Database backend (PostgreSQL)
- [ ] Strategy optimization (grid search)
- [ ] Real account integration (optional, at your own risk)

---

## 🔒 Security

### Best Practices
- **Never commit `.env`**: Contains API keys
- **Use .env.sample**: Template without secrets
- **Telegram Session**: `session.session` file is sensitive
- **No Passwords in Code**: All secrets in environment variables
- **Read-Only APIs**: If using exchange APIs, prefer read-only keys

### File Permissions
```bash
# Protect sensitive files (Linux/Mac)
chmod 600 .env
chmod 600 session.session
```

---

## 📜 License

This project is provided as-is for educational purposes. Use at your own risk.

**Disclaimer:**
- No warranties or guarantees
- Not financial advice
- Past performance ≠ future results
- Author not liable for losses

---

## 🙏 Acknowledgments

- **Telethon**: MTProto client for Python
- **ccxt**: Unified crypto exchange API
- **Pydantic**: Data validation
- **Rich**: Beautiful terminal output

---

## 📞 Support

For issues or questions:
1. Check [Limitations](#-limitations) section
2. Review `.env.sample` for correct config
3. Verify Telegram API credentials
4. Check `logs/runtime.log` for errors

---

## 🚦 Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with Telegram credentials
- [ ] Telegram channels added to config
- [ ] Run collector for 24h to gather signals
- [ ] Run backtest to validate strategy
- [ ] (Optional) Run full system for paper trading

---

**Built with ❤️ for safe crypto trading experimentation**
