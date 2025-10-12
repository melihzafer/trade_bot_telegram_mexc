# 🚀 Setup & Usage Guide

Complete step-by-step instructions for setting up and running the MEXC Multi-Source Trading System.

---

## Prerequisites

✅ **Python 3.10+** installed
✅ **Active Telegram account**
✅ **Internet connection**

---

## Step 1: Get Telegram API Credentials

### 1.1 Visit Telegram API Portal
Open your browser and navigate to: **https://my.telegram.org/apps**

### 1.2 Log In
- Enter your phone number (with country code, e.g., `+905551234567`)
- Telegram will send you a confirmation code
- Enter the code to log in

### 1.3 Create New Application
Click **"Create new application"** and fill in:
- **App title**: `MEXC Trading Bot` (or any name)
- **Short name**: `mexc_bot`
- **Platform**: Web (or any)
- **Description**: Optional

### 1.4 Get Credentials
After creating the app, you'll see:
- **api_id**: A numeric value (e.g., `123456`)
- **api_hash**: A long alphanumeric string

⚠️ **Keep these private!** Never commit them to Git.

---

## Step 2: Install Python & Dependencies

### 2.1 Verify Python Version
```bash
python --version
# Should show 3.10 or higher
```

If not installed:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: `sudo apt install python3.10 python3.10-venv`
- **Mac**: `brew install python@3.10`

### 2.2 Clone/Download Project
```bash
cd "d:\OMNI Tech Solutions"
cd trade_bot_telegram_mexc
```

### 2.3 Create Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 2.4 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- `telethon` - Telegram client
- `ccxt` - Exchange API
- `pydantic` - Data validation
- `pandas` - Data processing
- `rich` - Beautiful console output

---

## Step 3: Configure Environment

### 3.1 Copy Template
```bash
# Windows
copy .env.sample .env

# Linux/Mac
cp .env.sample .env
```

### 3.2 Edit `.env` File
Open `.env` in your text editor and fill in:

```env
# === REQUIRED: Telegram Credentials ===
TELEGRAM_API_ID=123456                        # From Step 1
TELEGRAM_API_HASH=your_32char_hash_here       # From Step 1
TELEGRAM_PHONE=+905551234567                  # Your phone number

# === REQUIRED: Channels to Monitor ===
TELEGRAM_CHANNELS=@crypto_signals,@btc_alerts
# Use actual channel usernames (comma-separated, no spaces)

# === OPTIONAL: Risk Settings ===
ACCOUNT_EQUITY_USDT=1000          # Starting virtual balance
RISK_PER_TRADE_PCT=1.0            # Risk 1% per trade
MAX_CONCURRENT_POSITIONS=2        # Max 2 positions at once
DAILY_MAX_LOSS_PCT=5.0            # Stop trading if lose 5% in a day
LEVERAGE=5                        # 5x leverage

# === OPTIONAL: Trading Settings ===
EXCHANGE_NAME=mexc                # Don't change
DEFAULT_TIMEFRAME=15m             # Candle timeframe
TZ=Europe/Sofia                   # Your timezone
```

### 3.3 Find Channel Usernames
To get channel usernames:
1. Open Telegram
2. Go to the channel
3. Click the channel name
4. Look for `@username` (if public)
5. If private, you need to be a member and use the invite link format

---

## Step 4: First Run - Establish Session

⚠️ **Important**: The first run will create a Telegram session file.

### 4.1 Run Collector Mode
```bash
python main.py --mode collector
```

### 4.2 Enter Phone Verification
You'll see:
```
Please enter the code you received: _
```

1. Check your Telegram for a code
2. Enter the code
3. If asked for 2FA password, enter it

### 4.3 Success Indicator
You should see:
```
✅ Successfully connected to Telegram
🔊 Listening to channels: @crypto_signals, @btc_alerts
```

### 4.4 Let It Collect
Leave it running for **24-48 hours** to gather signals.

Press `Ctrl+C` to stop gracefully.

---

## Step 5: Parse Collected Messages

After collecting raw messages, parse them:

```bash
python telegram/parser.py
```

**Output:**
```
📊 Parser Results
═══════════════════════════════════════
✅ Total parsed: 47 signals
💾 Saved to: data/signals_parsed.csv
```

Check `data/signals_parsed.csv` to verify signals were extracted correctly.

---

## Step 6: Run Backtest

Test the collected signals against historical data:

```bash
python main.py --mode backtest
```

**Output:**
```
📊 Backtest Results Summary
═══════════════════════════════════════
Total Signals: 47
✅ Wins: 28
❌ Losses: 15
⏳ Open: 3
⚠️  Errors: 1
📈 Win Rate: 65.12%
```

Results saved to `data/backtest_results.csv`.

---

## Step 7: Run Full System (Paper Trading)

Once satisfied with backtest, run live paper trading:

```bash
python main.py --mode full
```

or simply:

```bash
python main.py
```

**What happens:**
1. **Collector** listens to Telegram channels
2. **Parser** processes new messages every 5 seconds
3. **Paper Trader** opens/closes virtual positions based on signals

**Console Output:**
```
═══════════════════════════════════════
📊 Paper Trading Status
═══════════════════════════════════════
💰 Balance: 1000.00 USDT
📈 Equity: 1023.50 USDT (+2.35%)
📂 Open Positions: 2 / 2
═══════════════════════════════════════

🔥 OPEN POSITIONS:
─────────────────────────────────────
BTCUSDT | LONG | 0.0150 BTC
  Entry: 64800.00 | Current: 65100.00
  TP: 65500.00 | SL: 64200.00
  PnL: +7.20 USDT (+0.72%)
─────────────────────────────────────
```

Press `Ctrl+C` to stop.

---

## Troubleshooting

### Issue: "No module named 'telethon'"
**Solution:** Activate virtual environment and reinstall dependencies
```bash
.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### Issue: "API_ID or API_HASH is not set"
**Solution:** Check your `.env` file has correct values:
- No quotes around values
- No spaces
- Correct variable names

### Issue: "Invalid phone number"
**Solution:** Use international format with `+` sign:
- ✅ `+905551234567`
- ❌ `05551234567`

### Issue: "Session file corrupted"
**Solution:** Delete session file and re-authenticate
```bash
# Windows
del session.session

# Linux/Mac
rm session.session

# Then run collector again
python main.py --mode collector
```

### Issue: "No signals found"
**Solution:** 
1. Verify channels are sending messages
2. Check channel usernames are correct (with `@`)
3. Ensure you're a member of the channels
4. Let collector run for at least 24 hours

### Issue: "MEXC API rate limit"
**Solution:** 
- Backtest uses public API (60 requests/min limit)
- Wait a few minutes and try again
- Reduce number of signals being tested

### Issue: "Backtest shows all errors"
**Solution:**
- Check internet connection
- Verify symbol is correct (e.g., `BTCUSDT`, not `BTC`)
- MEXC may not have data for that pair

---

## Usage Patterns

### Pattern 1: Initial Setup (Days 1-2)
```bash
# Day 1: Start collecting
python main.py --mode collector
# Leave running for 24-48h

# Day 2: Stop (Ctrl+C), then parse
python telegram/parser.py

# Run backtest
python main.py --mode backtest
```

### Pattern 2: Daily Operation
```bash
# Morning: Start full system
python main.py

# Leave running all day
# Paper trades automatically

# Evening: Stop (Ctrl+C)
# Review logs/data/
```

### Pattern 3: Analysis Only
```bash
# Just collect signals (no trading)
python main.py --mode collector

# Later, backtest anytime
python main.py --mode backtest
```

---

## File Locations

| File | Purpose | Location |
|------|---------|----------|
| Raw messages | Telegram collector output | `data/signals_raw.jsonl` |
| Parsed signals | Extracted signals | `data/signals_parsed.csv` |
| Backtest results | Historical performance | `data/backtest_results.csv` |
| Logs | System logs | `logs/runtime.log` |
| Session | Telegram auth | `session.session` |
| Config | Your settings | `.env` |

---

## Performance Tips

### Optimize Collector
- Monitor only active channels (remove inactive ones)
- Use `--mode collector` initially to build signal database

### Optimize Backtest
- Test smaller time ranges first
- Filter signals by symbol before testing
- Check `data/backtest_results.csv` for patterns

### Optimize Paper Trading
- Start with conservative risk (0.5-1%)
- Limit concurrent positions (2-3 max)
- Monitor `logs/runtime.log` for errors

---

## Next Steps

After successful setup:

1. **Monitor Performance**: Check `logs/runtime.log` daily
2. **Analyze Signals**: Review `data/signals_parsed.csv` for quality
3. **Tune Risk**: Adjust `.env` settings based on results
4. **Add Channels**: Expand to more signal sources
5. **Review Backtest**: Study `data/backtest_results.csv` for insights

---

## Safety Reminders

⚠️ **This is paper trading only** - No real money at risk
⚠️ **Never commit `.env`** - Contains sensitive credentials
⚠️ **Start small** - Use low risk % until confident
⚠️ **Not financial advice** - For educational purposes only

---

**Ready to start? Go back to [Step 1](#step-1-get-telegram-api-credentials)!**
