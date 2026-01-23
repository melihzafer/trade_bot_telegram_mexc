# 🤖 Telegram Signal Backtest System# 🤖 MEXC Multi-Source Trading System



**LOCAL-ONLY** backtest platformu - Telegram sinyallerini topla, analiz et, karlılığı test et!> **Production-lean MVP for backtesting and paper trading crypto signals from multiple Telegram channels**



## 📁 Proje YapısıA robust Python system that collects trading signals from Telegram, backtests them against historical data, and simulates live trading with paper accounts—all without risking real capital.



```---

trade_bot_telegram_mexc/

├── config/              # Konfigürasyon dosyaları## 📋 Table of Contents

│   └── channels.csv     # Telegram kanalları listesi

├── telegram/            # Telegram modülleri- [Features](#-features)

│   ├── collector.py     # Gerçek zamanlı sinyal toplayıcı- [Architecture](#-architecture)

│   └── history_collector.py  # Geçmiş sinyalleri indir (TODO)- [Requirements](#-requirements)

├── trading/             # Trading modülleri- [Installation](#-installation)

│   └── parser.py        # Sinyal parser (geliştirilecek)- [Configuration](#-configuration)

├── analysis/            # Backtest ve analiz modülleri- [Usage](#-usage)

│   ├── backtest_engine.py   # Backtest motoru (TODO)- [Project Structure](#-project-structure)

│   └── performance.py       # Performans metrikleri (TODO)- [Components](#-components)

├── reports/             # HTML ve chart raporları- [Risk Management](#-risk-management)

│   └── charts/          # Performans grafikleri (TODO)- [Limitations](#-limitations)

├── data/                # Tüm veri dosyaları- [Roadmap](#-roadmap)

│   ├── signals_raw.jsonl    # Ham Telegram sinyalleri- [Security](#-security)

│   ├── signals_parsed.jsonl # Parse edilmiş sinyaller (TODO)- [License](#-license)

│   └── historical_prices/   # MEXC fiyat verileri (TODO)

├── logs/                # Log dosyaları---

├── scripts/             # Yardımcı scriptler

│   ├── list_channel.py  # Kanal listesi## ✨ Features

│   └── test_read.py     # Test okuyucu

├── utils/               # Utility fonksiyonlar### Core Capabilities

│   ├── config.py        # Config yönetimi- **Multi-Channel Telegram Collector**: Monitors multiple channels simultaneously using Telethon

│   └── logger.py        # Logging sistemi- **Intelligent Signal Parser**: Regex-based extraction of BUY/SELL, ENTRY, TP, SL from messages

├── .env                 # Environment variables (GİZLİ!)- **Full Backtest Engine**: Tests signals against MEXC historical OHLCV data

├── main.py              # Ana uygulama- **Paper Trading**: Live simulation with virtual positions and real-time pricing

└── requirements.txt     # Python dependencies- **Risk Management**: Position limits, daily loss caps, leverage control

```- **Comprehensive Logging**: Rich console output + rotating log files



## 🎯 Proje Amacı### Data Flow

```

1. ✅ **Gerçek Zamanlı Toplama**: 11 Telegram kanalından sinyal toplaTelegram → Raw JSONL → Parsed CSV → Backtest Results

2. 🔄 **Geçmiş Sinyaller**: Son 500-1000 mesajı indir (PHASE 3)                ↓

3. ⚙️ **Parser Geliştir**: Tüm sinyal formatlarını parse et (PHASE 4)         Paper Trader → Virtual P&L

4. 📈 **MEXC Entegrasyon**: Geçmiş fiyat verilerini çek (PHASE 5)```

5. 🧪 **Backtest Engine**: Sinyalleri test et, karlılığı hesapla (PHASE 6)

6. 📊 **Performans Analizi**: Başarı oranı, kar/zarar raporları (PHASE 7)---

7. 📄 **HTML Raporlar**: Görsel grafikler ve detaylı raporlar (PHASE 8)

8. ✅ **Final Karar**: Hangi kanallar karlı? Live trading yapılmalı mı? (PHASE 9)## 🏗️ Architecture



## 🚀 Hızlı Başlangıç```

┌─────────────────────────────────────────────────────────┐

### 1. Kurulum│                    MAIN ORCHESTRATOR                     │

```powershell│                      (main.py)                           │

# Virtual environment aktif et└───────────┬─────────────────────────────────┬───────────┘

.\.venv\Scripts\Activate.ps1            │                                 │

    ┌───────▼────────┐                ┌──────▼───────┐

# Dependencies yükle (zaten yüklü)    │   TELEGRAM     │                │   TRADING    │

pip install -r requirements.txt    │   COLLECTOR    │─────┐          │   ENGINE     │

```    │  (Telethon)    │     │          │              │

    └────────────────┘     │          └──────────────┘

### 2. Gerçek Zamanlı Toplama (ÇALIŞIYOR ✅)                           │                 │

```powershell                    ┌──────▼──────┐         │

python main.py                    │   PARSER    │         │

```                    │  (Regex)    │         │

→ Sinyaller `data/signals_raw.jsonl` dosyasına kaydedilir                    └──────┬──────┘         │

                           │                │

## 📋 Development Roadmap                    ┌──────▼──────┐  ┌──────▼────────┐

                    │ BACKTESTER  │  │ PAPER TRADER  │

- ✅ PHASE 1: Project Cleanup (TAMAM!)                    │   (ccxt)    │  │   (Virtual)   │

- ✅ PHASE 2: Folder Restructure (TAMAM!)                    └─────────────┘  └───────────────┘

- ⏳ PHASE 3: Historical Signal Collection```

- ⏳ PHASE 4: Parser Development

- ⏳ PHASE 5: MEXC API Integration---

- ⏳ PHASE 6: Backtest Engine

- ⏳ PHASE 7: Performance Metrics## 📦 Requirements

- ⏳ PHASE 8: Reporting System

- ⏳ PHASE 9: Final Analysis- **Python**: 3.10 or higher

- **Telegram Account**: Active account with API credentials

## 🔧 Teknolojiler- **Internet Connection**: For Telegram + MEXC API access



- **Python 3.14**: Ana dil### System Dependencies

- **Telethon**: Telegram API client- No additional system packages required (pure Python)

- **MEXC API**: Geçmiş fiyat verileri (gelecek)

- **Pandas**: Veri analizi (gelecek)---

- **Matplotlib/Plotly**: Grafikler (gelecek)

## 🚀 Installation

## 📊 Mevcut Durum

### 1. Clone Repository

- ✅ 11 Telegram kanalı aktif```bash

- ✅ Gerçek zamanlı sinyal toplama çalışıyorgit clone <repository-url>

- ✅ Thread-safe dosya yazmacd trade_bot_telegram_mexc

- ⏳ Geçmiş sinyaller indirilecek```

- ⏳ Parser geliştirilecek

- ⏳ Backtest engine yapılacak### 2. Create Virtual Environment

```bash

## 🔐 Güvenlik# Windows

python -m venv .venv

- `.env` dosyası GİT'e eklenmedi (session key içeriyor!).venv\Scripts\activate

- Session dosyası lokal kalıyor

- Tüm veriler PC'de, cloud yok!# Linux/Mac

python3 -m venv .venv

## 📞 Desteksource .venv/bin/activate

```

Sorular için: PROJECT_PLAN.md dosyasını inceleyin!

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

### Step 1: Collect Signals

Before backtesting, you need to collect signals from Telegram channels.

#### Real-Time Collection (Recommended)
Collects signals as they arrive in real-time:

```bash
# Collect raw signals (saves everything)
python collect_signals.py

# Collect and auto-parse signals (saves only valid trading signals)
python collect_signals.py --parse

# Custom output file
python collect_signals.py --output data/my_signals.jsonl --parse
```

**Best Practice:** Run for 24-48 hours to gather sufficient data:
```bash
# Linux/Mac (background process)
nohup python collect_signals.py --parse > collector.log 2>&1 &

# Windows (keep terminal open)
python collect_signals.py --parse
```

#### Historical Collection
Fetches past messages from channels:

```bash
# Collect last 100 messages per channel
python collect_signals.py --mode historical

# Collect last 500 messages and parse
python collect_signals.py --mode historical --limit 500 --parse

# Collect last 1000 messages (large dataset)
python collect_signals.py --mode historical --limit 1000 --parse
```

**Output Files:**
- `data/signals_raw.jsonl` - Raw Telegram messages
- `data/signals_parsed.jsonl` - Parsed trading signals (ready for backtest)

---

### Step 2: Run Backtest
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

### Step 2: Run Backtest

Test collected signals against historical price data **(now with Binance API for better reliability)**.

**New Features:**
- 📡 **Channel Comparison**: See which signal sources perform best
- 🌐 **Binance Integration**: Uses Binance API for historical data (more reliable than MEXC)
- 🎯 **Source Tracking**: Every trade shows which channel it came from
Test historical performance with realistic simulation.

```bash
# Run backtest with default settings
python run_backtest.py

# Custom capital and risk
python run_backtest.py --capital 50000 --risk 0.03

# Filter by date range
python run_backtest.py --start-date 2024-01-01 --end-date 2024-12-31

# Custom fees and slippage
python run_backtest.py --maker-fee 0.0001 --taker-fee 0.0005 --slippage 0.002

# Use custom signals file
python run_backtest.py --signals data/my_signals.jsonl

# Skip charts/HTML (metrics only)
python run_backtest.py --no-charts --no-html
```

**What happens:**
- Reads parsed signals from JSONL file
- Fetches historical OHLCV data from MEXC
- Simulates realistic trading with:
  - Position sizing based on risk management
  - Trading fees (0.02% maker / 0.06% taker)
  - Slippage (0.1% average)
  - Stop loss and take profit execution
- Calculates comprehensive metrics:
  - Win rate, profit factor, expectancy
  - Sharpe ratio, max drawdown
  - Monthly performance breakdown
- Generates visualizations:
  - Equity curve with drawdown overlay
  - Trade PnL distribution histograms
  - Monthly performance heatmap
  - Win/loss pie chart
- Exports results:
  - Detailed HTML report with charts
  - JSON metrics file
  - CSV trade log for external analysis
  - JSONL trade history

**Output:**
```
🧪 BACKTEST RESULTS
══════════════════════════════════════════════════════════════════════
💰 Initial Capital: $10,000.00
💵 Final Capital: $12,450.75
📈 Total Return: $2,450.75 (+24.51%)
📊 Total Trades: 150
✅ Wins: 92 (61.3%)
❌ Losses: 58
💹 Profit Factor: 1.85
🎯 Expectancy: $16.34 per trade
📉 Max Drawdown: $680.25 (6.80%)
📊 Sharpe Ratio: 1.82
💸 Total Fees: $145.20
📉 Total Slippage: $85.40
══════════════════════════════════════════════════════════════════════
✅ HTML report saved: reports/backtest_report_20260122_003000.html
```

**Available Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--signals` | Path to signals JSONL file | `data/signals_parsed.jsonl` |
| `--output` | Output directory for reports | `reports` |
| `--capital` | Initial capital in USDT | `10000` |
| `--risk` | Risk percentage per trade | `0.02` (2%) |
| `--maker-fee` | Maker fee percentage | `0.0002` (0.02%) |
| `--taker-fee` | Taker fee percentage | `0.0006` (0.06%) |
| `--slippage` | Average slippage percentage | `0.001` (0.1%) |
| `--max-bars` | Max candles to hold position | `96` (24h for 15m) |
| `--start-date` | Start date filter (YYYY-MM-DD) | None |
| `--end-date` | End date filter (YYYY-MM-DD) | None |
| `--no-charts` | Skip chart generation | False |
| `--no-html` | Skip HTML report | False |

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

## 🚀 Railway Deployment

### Deploy Signal Collector to Cloud (24/7 Collection)

**Railway** provides free hosting with PostgreSQL, perfect for running collector 24/7.

#### 1️⃣ Prepare for Railway

```bash
# Commit latest changes
git add .
git commit -m "Add Flask API and email reporter"
git push origin main
```

#### 2️⃣ Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `trade_bot_telegram_mexc`
4. Railway will auto-detect and deploy

#### 3️⃣ Configure Environment Variables

Go to Railway → Variables → Add these:

```env
# Telegram API (required)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+1234567890
TELEGRAM_SESSION_STRING=1BJWap1s...  # Get from: python export_session.py

# Channels to monitor (11 channels: 7 public + 4 private)
TELEGRAM_CHANNELS=@kriptotestmz,@kriptodelisi11,@kriptokampiislem,@kriptostarr,@kriptosimpsons,@deepwebkripto,@ProCrypto_Trading,-1002251019196,-1002001037199,-1002388163345,-1002263653702

# MEXC API (for backtesting later)
MEXC_API_KEY=mx0v...
MEXC_API_SECRET=your_secret_here

# Flask API (optional)
PORT=8080
FLASK_ENV=production

# Email Reporter (optional - for daily reports)
SMTP_EMAIL=your@gmail.com
SMTP_PASSWORD=your_app_password  # Get from: https://myaccount.google.com/apppasswords
REPORT_EMAIL=recipient@email.com  # Optional, defaults to SMTP_EMAIL
```

**🔐 Get TELEGRAM_SESSION_STRING:**
```bash
python export_session.py
# Copy the output string to Railway
```

**🔐 Get Gmail App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Select app: Mail
3. Select device: Other (custom name)
4. Copy 16-character password

#### 4️⃣ Deploy Services

Railway will run the `web` service (Flask API) automatically.

To run collector separately:
1. Railway → Settings → Service Variables
2. Change Procfile command:
   ```
   web: python main.py --mode collector
   ```

**Or run both (recommended):**
Create 2 services in Railway:
- **Service 1** (API): `web: python api.py`
- **Service 2** (Collector): `worker: python main.py --mode collector`

#### 5️⃣ Access Your Dashboard

Railway will provide a public URL like:
```
https://trade-bot-telegram-mexc-production.up.railway.app
```

**Dashboard Features:**
- 📊 View total signals collected
- 📡 See signals by channel
- 🔥 Latest signal preview
- 📥 Download raw signals (JSONL)
- 📥 Download parsed signals (CSV)
- 🔌 JSON API endpoint

#### 6️⃣ Schedule Email Reports (Optional)

Add Railway Cron Job:
1. Railway → Settings → Cron Jobs
2. Add schedule: `0 18 * * *` (daily at 6 PM)
3. Command: `python email_reporter.py`

This will email you signal reports every day!

#### 7️⃣ Monitor Logs

```bash
# View Railway logs
railway logs

# Or use Railway dashboard → Deployments → Logs
```

#### 8️⃣ Download Collected Signals

**Option A: Web Dashboard**
- Visit your Railway URL
- Click "Download Raw Signals"

**Option B: Direct API**
```bash
curl https://your-app.railway.app/download/raw -o signals.jsonl
```

**Option C: Email Report**
- Wait for scheduled email
- Download attachment

---

### Railway Tips

✅ **Free Tier Limits:**
- 500 hours/month execution time
- $5 credit/month
- Perfect for signal collector!

✅ **Keep Collector Running:**
- Railway auto-restarts on crash
- Logs saved automatically
- No need to worry about downtime

✅ **Update Code:**
```bash
git push origin main
# Railway auto-deploys!
```

✅ **Check Health:**
Visit: `https://your-app.railway.app/health`

---

## 📧 Email Reporter

Get daily signal reports delivered to your inbox!

```bash
# Test locally
python email_reporter.py

# Schedule in Railway (see Railway section above)
```

**Email includes:**
- Total signals collected
- Breakdown by channel
- Latest signal preview
- Attached JSONL file
- Attached CSV (if parsed)

---

**Built with ❤️ for safe crypto trading experimentation**
