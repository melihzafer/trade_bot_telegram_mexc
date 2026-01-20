# 🤖 Autonomous Trading System - README

## Project Chimera Phase 4: Full Autonomy

The autonomous trading system is the culmination of all previous phases, providing a 24/7 self-operating trading bot that:

- **Listens** to Telegram channels for trading signals
- **Parses** signals using Hybrid AI/Regex (DeepSeek R1 + Rule-based)
- **Validates** trades through the Risk Sentinel (circuit breaker, kill switch, whitelist)
- **Executes** orders via CCXT (MEXC exchange)
- **Notifies** admin of all events via Telegram Bot
- **Reports** daily performance metrics
- **Recovers** automatically from errors
- **Runs** forever with graceful shutdown

---

## 📦 Components

### 1. **Telegram Notifier** (`reporting/notifier.py`)
   - Sends real-time notifications to admin via Telegram Bot API
   - Separate from Telegram listener (uses bot token, not user credentials)
   - **Features:**
     - Trade alerts (executed, rejected, failed)
     - Risk alerts (circuit breaker, kill switch)
     - Daily PnL reports
     - Startup/shutdown notifications
     - Error notifications
     - Retry logic with exponential backoff

### 2. **Autonomous System** (`main_autonomous.py`)
   - The Central Nervous System that coordinates all components
   - Infinite loop with robust error recovery
   - **Pipeline:**
     ```
     Telegram Message → Hybrid Parser → Risk Sentinel → Trading Engine → Notifier
     ```
   - **Error Recovery:** Catches all exceptions and auto-restarts loop after 10s
   - **Daily Reports:** Sends performance report at 00:00 UTC
   - **Graceful Shutdown:** Handles Ctrl+C and kill signals properly

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# -------------------- Telegram Bot Notifications --------------------
# Get Bot Token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Get your Chat ID from @userinfobot
ADMIN_CHAT_ID=123456789

# -------------------- Trading Configuration --------------------
ACCOUNT_EQUITY_USDT=10000
TRADING_MODE=paper

# -------------------- Telegram Listener --------------------
TELEGRAM_API_ID=28115427
TELEGRAM_API_HASH=dee3e8cdaf87c416dabd1db1a224cee1
TELEGRAM_PHONE=+359892958483
TELEGRAM_CHANNELS=-1002001037199,@kriptodelisi11

# -------------------- Live Trading (MEXC) --------------------
MEXC_API_KEY=your_mexc_api_key_here
MEXC_API_SECRET=your_mexc_api_secret_here

# -------------------- AI Parser (OpenRouter) --------------------
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=deepseek/deepseek-r1
```

### How to Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the instructions to create a bot
4. Copy the token provided (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
5. Set as `TELEGRAM_BOT_TOKEN` in `.env`

### How to Get Your Chat ID

1. Open Telegram and search for **@userinfobot**
2. Send `/start`
3. Copy your numeric ID (e.g., `123456789`)
4. Set as `ADMIN_CHAT_ID` in `.env`

---

## 🚀 Usage

### Start Autonomous Trading

```bash
# Paper trading (recommended for testing)
python main_autonomous.py

# Live trading (requires MEXC API keys)
TRADING_MODE=live python main_autonomous.py
```

### What Happens When You Run It

1. **Initialization:**
   - Loads all components (Parser, Sentinel, Engine, Notifier)
   - Connects to Telegram (listener)
   - Sends startup notification to admin

2. **Main Loop (Forever):**
   - Listens for messages from configured channels
   - Parses each message using Hybrid AI/Regex
   - Validates signals with Risk Sentinel
   - Executes approved trades
   - Notifies admin of every event
   - Checks for 00:00 UTC to send daily report

3. **Error Recovery:**
   - If any error occurs, logs it and sends error notification
   - Waits 10 seconds
   - Automatically restarts the loop
   - **Never dies** (unless fatal system error)

4. **Graceful Shutdown (Ctrl+C):**
   - Prints final statistics
   - Sends shutdown notification
   - Closes all connections
   - Exits cleanly

---

## 📊 Notification Examples

### Trade Executed
```
✅ Trade Executed [14:23:45 20/01/2026]

📊 Symbol: BTCUSDT
📈 Side: LONG
🎯 Entry: 42000.0000
🎯 TP: 45000.0000 - 47000.0000
🛑 SL: 40000.0000
⚡ Leverage: 5x

Status: EXECUTED
Order ID: 123456789
Quantity: 0.05
```

### Trade Rejected
```
🚫 Trade Rejected [14:25:10 20/01/2026]

📊 Symbol: DOGEUSDT
📈 Side: LONG
🎯 Entry: 0.0850

Status: REJECTED
Reason: Symbol not in whitelist
```

### Circuit Breaker Alert
```
🔔 Alert [15:30:00]

🔴 CIRCUIT BREAKER ACTIVE

Daily loss limit exceeded (-5.2%)
Trading halted for protection
```

### Daily Report
```
📊 Daily Performance Report
📅 Date: 20/01/2026

📈 Trading Activity
   Total Trades: 15
   Winning: 9 ✅
   Losing: 6 ❌

💰 Performance
   Total PnL: 🟢 +350.50 USDT
   Win Rate: 60.0%
   Largest Win: +120.50 USDT
   Largest Loss: -80.30 USDT

💼 Portfolio
   Current Equity: 10350.50 USDT
   Open Positions: 2
   Daily Loss: -1.5%
```

---

## 🔒 Risk Management Integration

The autonomous system integrates the Risk Sentinel for capital protection:

### Automatic Checks Before Every Trade

1. **Kill Switch:** File-based emergency stop (`data/EMERGENCY_STOP`)
2. **Circuit Breaker:** Daily loss limit (5% default)
3. **Whitelist:** Only approved symbols
4. **Blacklist:** Rejected scam/delisted coins
5. **Correlation:** Prevent over-exposure to similar assets
6. **Price Validation:** Entry, TP, SL must be valid
7. **R:R Ratio:** Warning if Risk:Reward < 1.5

### Real-Time Notifications

- ✅ Trade executed → Immediate notification
- 🚫 Trade rejected → Notification with reason
- 🔴 Circuit breaker activated → Critical alert
- 🛑 Kill switch detected → Critical alert
- ❌ Execution failed → Error notification

---

## 🧪 Testing

### Test Telegram Notifier

```bash
python reporting/notifier.py
```

This will send test messages to your admin chat:
- Test alert
- Test trade notification
- Test daily report

### Test Full System (Dry Run)

```bash
# Set to paper mode
TRADING_MODE=paper python main_autonomous.py
```

- Monitor the console output
- Check your Telegram for notifications
- Verify signals are parsed correctly
- Confirm trades are executed in paper mode

---

## 📈 Performance Metrics

The system tracks:

- **Messages Processed:** Total Telegram messages received
- **Signals Parsed:** Valid signals detected
- **Trades Executed:** Successful order placements
- **Trades Rejected:** Blocked by Risk Sentinel
- **Runtime:** System uptime
- **Notification Stats:** Sent/failed notifications

View statistics on shutdown or check logs.

---

## 🛡️ Safety Features

### 1. **Kill Switch**
```bash
# Activate emergency stop
touch data/EMERGENCY_STOP

# Deactivate
rm data/EMERGENCY_STOP
```

### 2. **Circuit Breaker**
- Automatically activates when daily loss > 5%
- Resets at midnight UTC
- Can be manually reset (not recommended)

### 3. **Paper Mode**
- Simulated trading (no real orders)
- Perfect for testing strategies
- Tracks performance as if trading live

### 4. **Auto-Restart**
- System never dies from non-fatal errors
- Logs all errors for debugging
- Notifies admin immediately

### 5. **Graceful Shutdown**
- Handles Ctrl+C properly
- Closes all connections
- Sends final statistics

---

## 🚨 Troubleshooting

### Notifier Not Working

**Problem:** No notifications received

**Solutions:**
1. Check `TELEGRAM_BOT_TOKEN` is set correctly
2. Check `ADMIN_CHAT_ID` is your numeric Telegram ID
3. Ensure bot can send messages to you (start a chat with your bot)
4. Check logs for API errors

### Signals Not Parsed

**Problem:** Messages received but not parsed

**Solutions:**
1. Check if `OPENROUTER_API_KEY` is valid
2. Verify regex patterns match your signal format
3. Check confidence threshold (default 0.85)
4. Review parser logs for errors

### Trades Not Executing

**Problem:** Signals parsed but no trades executed

**Solutions:**
1. Check Risk Sentinel is not blocking (whitelist, circuit breaker)
2. Verify `TRADING_MODE` is set correctly
3. For live mode, check MEXC API keys
4. Review risk validation logs

### System Crashes

**Problem:** Bot stops running

**Solutions:**
1. Check error logs in `logs/` directory
2. Verify all dependencies installed (`pip install -r requirements.txt`)
3. Ensure `.env` file has all required variables
4. Check for network connectivity issues

---

## 📝 Logs

All logs are saved to `logs/` directory:

- `trading_bot_YYYYMMDD.log` - Main system logs
- Console output shows real-time events

**Log Levels:**
- `INFO` - Normal operations
- `WARN` - Warnings (non-critical)
- `ERROR` - Errors (critical but recovered)
- `SUCCESS` - Successful operations

---

## 🔄 Deployment

### Local Machine
```bash
# Run in background (Linux/Mac)
nohup python main_autonomous.py > output.log 2>&1 &

# Run in background (Windows)
pythonw main_autonomous.py
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main_autonomous.py"]
```

### Cloud (Railway, Heroku, AWS)
- Set environment variables in platform dashboard
- Deploy as worker/background process
- Ensure 24/7 uptime plan

---

## 🎯 Best Practices

1. **Always Start in Paper Mode**
   - Test thoroughly before going live
   - Verify signal parsing accuracy
   - Check risk management rules

2. **Monitor Regularly**
   - Check Telegram notifications
   - Review daily reports
   - Analyze trade performance

3. **Set Conservative Risk Limits**
   - Start with low leverage (2-5x)
   - Risk 1% per trade max
   - Set daily loss limit at 5%

4. **Use Whitelist Carefully**
   - Only add high-volume, liquid pairs
   - Avoid scam/new/low-cap coins
   - Update blacklist regularly

5. **Have an Exit Plan**
   - Know how to activate kill switch
   - Monitor circuit breaker status
   - Set stop-loss on all trades

---

## 📚 Related Documentation

- **Phase 1:** [AI Parser](parsers/AI_PARSER_README.md)
- **Phase 1:** [Hybrid Architecture](parsers/HYBRID_ARCHITECTURE.md)
- **Phase 2:** [Trading Engine](trading/TRADING_ENGINE_README.md)
- **Phase 3:** [Risk Sentinel](trading/RISK_SENTINEL_README.md)
- **Implementation Plan:** [IMPLEMENTATION_PLAN_V2.md](IMPLEMENTATION_PLAN_V2.md)

---

## 🤝 Support

If you encounter issues:

1. Check this README first
2. Review component documentation
3. Check logs for errors
4. Verify configuration
5. Test components individually

---

## ⚖️ Disclaimer

**This is an automated trading system. Trading cryptocurrencies carries significant risk.**

- Start with paper trading
- Never risk more than you can afford to lose
- Past performance does not guarantee future results
- The system is provided as-is without warranty
- You are responsible for your own trades

**USE AT YOUR OWN RISK**

---

**Project Chimera** - Autonomous Crypto Trading System
Version 1.0.0 | 2026
