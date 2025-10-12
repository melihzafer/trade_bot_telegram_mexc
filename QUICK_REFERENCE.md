# 🚀 Quick Reference Card

**MEXC Multi-Source Trading System - Command Cheat Sheet**

---

## 🔧 Installation Commands

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.sample .env  # Windows
cp .env.sample .env    # Linux/Mac
```

---

## 🎯 Main Commands

### Full System (Collector + Parser + Paper Trading)
```bash
python main.py
# or
python main.py --mode full
```

### Collector Only (Gather signals)
```bash
python main.py --mode collector
```

### Backtest Only (Test historical performance)
```bash
python main.py --mode backtest
```

---

## 🔧 Standalone Components

### Run Parser Manually
```bash
python telegram/parser.py
```

### Run Backtester Manually
```bash
python trading/backtester.py
```

### Run Paper Trader Manually
```bash
python trading/paper_trader.py
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `.env` | Your configuration (gitignored) |
| `.env.sample` | Configuration template |
| `data/signals_raw.jsonl` | Raw Telegram messages |
| `data/signals_parsed.csv` | Extracted signals |
| `data/backtest_results.csv` | Historical test results |
| `logs/runtime.log` | System logs |
| `session.session` | Telegram authentication |

---

## ⚙️ Configuration (.env)

```env
# Telegram Credentials
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_hash_here
TELEGRAM_PHONE=+905551234567
TELEGRAM_CHANNELS=@channel1,@channel2

# Risk Settings
ACCOUNT_EQUITY_USDT=1000
RISK_PER_TRADE_PCT=1.0
MAX_CONCURRENT_POSITIONS=2
DAILY_MAX_LOSS_PCT=5.0
LEVERAGE=5
```

---

## 🆘 Troubleshooting

### Problem: "API_ID or API_HASH is not set"
**Solution:** Edit `.env` file with your Telegram credentials

### Problem: "No signals found"
**Solution:** Run collector for 24-48h first, then parse

### Problem: Session error
**Solution:** Delete `session.session` and re-authenticate
```bash
del session.session  # Windows
rm session.session   # Linux/Mac
```

### Problem: Import errors
**Solution:** Activate virtual environment
```bash
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac
```

---

## 📊 Typical Workflow

### Day 1: Initial Setup
```bash
# 1. Configure environment
copy .env.sample .env
# Edit .env with your credentials

# 2. Start collecting
python main.py --mode collector
# Enter phone verification code
# Let run for 24-48h
```

### Day 2: Testing
```bash
# 3. Parse collected messages
python telegram/parser.py

# 4. Run backtest
python main.py --mode backtest
# Review results in data/backtest_results.csv
```

### Day 3+: Paper Trading
```bash
# 5. Run full system
python main.py
# Monitor console output
# Press Ctrl+C to stop
```

---

## 🔍 Checking Data

### View raw messages
```bash
# Windows
type data\signals_raw.jsonl

# Linux/Mac
cat data/signals_raw.jsonl
```

### View parsed signals
```bash
# Windows
type data\signals_parsed.csv

# Linux/Mac
cat data/signals_parsed.csv
```

### View backtest results
```bash
# Windows
type data\backtest_results.csv

# Linux/Mac
cat data/backtest_results.csv
```

### View logs
```bash
# Windows
type logs\runtime.log

# Linux/Mac
cat logs/runtime.log
```

---

## 🎛️ Execution Modes

| Mode | Command | Collector | Parser | Paper Trading |
|------|---------|-----------|--------|---------------|
| **Full** | `python main.py` | ✅ | ✅ | ✅ |
| **Backtest** | `python main.py --mode backtest` | ❌ | ❌ | ❌ |
| **Collector** | `python main.py --mode collector` | ✅ | ❌ | ❌ |

---

## 📈 Success Indicators

### ✅ Collector Working
```
✅ Successfully connected to Telegram
🔊 Listening to channels: @crypto_signals, @btc_alerts
```

### ✅ Parser Working
```
📊 Parser Results
✅ Total parsed: 47 signals
💾 Saved to: data/signals_parsed.csv
```

### ✅ Backtest Working
```
📊 Backtest Results Summary
Total Signals: 47
✅ Wins: 28
❌ Losses: 15
📈 Win Rate: 65.12%
```

### ✅ Paper Trading Working
```
💰 Balance: 1000.00 USDT
📈 Equity: 1023.50 USDT (+2.35%)
📂 Open Positions: 1 / 2
```

---

## 🔒 Security Reminders

- ⚠️ Never commit `.env` file
- ⚠️ Never share `session.session` file
- ⚠️ Keep `TELEGRAM_API_HASH` private
- ⚠️ This is paper trading only (no real money)

---

## 📞 Getting Help

1. Check `logs/runtime.log` for errors
2. Review `SETUP_GUIDE.md` for detailed instructions
3. Read `README.md` for architecture overview
4. Verify `.env` configuration matches `.env.sample`

---

**Quick Start**: `python main.py --mode collector` → wait 24h → `python main.py --mode backtest` → `python main.py`
