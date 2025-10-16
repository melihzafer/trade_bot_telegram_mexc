# ⚡ Quick Start Guide - Paper Trading in 5 Minutes

## Step 1: Verify Configuration (30 seconds)

```powershell
# Check trading mode
python -c "from config.trading_config import TRADING_MODE; print(f'Mode: {TRADING_MODE}')"

# Expected output: Mode: paper
```

**If not "paper":**
```python
# Edit: config/trading_config.py
TRADING_MODE = "paper"  # Change this line
```

---

## Step 2: Configure Telegram Channels (1 minute)

```python
# Edit: config/trading_config.py
class SignalConfig:
    CHANNELS = [
        "your_channel_username1",  # Replace with real channel
        "your_channel_username2"   # Add more as needed
    ]
```

---

## Step 3: Set Environment Variables (1 minute)

```powershell
# Create .env file (if doesn't exist)
New-Item -Path ".env" -ItemType File
```

**Edit `.env` file:**
```env
# Telegram (REQUIRED for signal listener)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE_NUMBER=+1234567890

# Binance (already configured for price data)
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret

# MEXC (NOT needed for paper trading)
MEXC_API_KEY=not_needed_yet
MEXC_API_SECRET=not_needed_yet
```

**Get Telegram credentials:**
1. Go to: https://my.telegram.org/
2. Login with your phone number
3. Click "API development tools"
4. Create app, copy API ID and API Hash

---

## Step 4: Test Components (2 minutes)

### Test Parser
```powershell
python -c "from telegram.parser import parse_message; result = parse_message({'text': '🟢 LONG\n💲 BTCUSDT\n📈 Entry: 50000\n🎯 Target: 52000\n🛑 Stop Loss: 48000', 'timestamp': '2025-01-01T00:00:00', 'source': 'test'}); print('✅ Parser works!' if result else '❌ Parser failed')"
```

### Test Portfolio
```powershell
python trading\portfolio.py
```

**Expected:** Portfolio test output with BTC/ETH positions

---

## Step 5: Launch Paper Trading (30 seconds)

```powershell
python run_paper_trading.py
```

**First time:** Telegram will send verification code to your phone
- Enter the code in console
- Session saved for future runs (no need to verify again)

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════╗
║          🎯 PAPER TRADING MODE - ACTIVE                     ║
║  ⚠️  SIMULATED TRADING - NO REAL MONEY INVOLVED            ║
║  Initial Balance: $10,000 USDT                              ║
╚══════════════════════════════════════════════════════════════╝

[INFO] 🚀 Trading Engine initialized in PAPER mode
[INFO] 📡 Signal Listener initialized for 2 channels
[INFO] ✅ Telegram client connected
[SUCCESS] ✅ Access to channel1: Crypto Signals
[INFO] 🔄 Fetching last 20 messages from channels...
[SUCCESS] ✅ Paper trading started successfully!
[INFO] 👂 Listening for new signals... (Press Ctrl+C to stop)
```

**You're live!** 🎉

---

## What Happens Next?

### When Signal Arrives

```
[INFO] 📥 New signal: LONG BTCUSDT | TP: 52000 | SL: 48000
[INFO] ➕ Signal queued: LONG BTCUSDT
[INFO] 🔄 Processing 1 queued signals...
[SUCCESS] 🟢 Opened LONG BTCUSDT @ $50123.45 | Qty: 0.1995 | TP: 52000 | SL: 48000
```

### Position Monitoring (every 5 seconds)

```
[INFO] 🔄 Checking exit conditions for 1 positions...
[INFO] BTCUSDT: Current $50,456 | TP: $52,000 | SL: $48,000 | PnL: +$66.45
```

### When TP/SL Hit

```
[SUCCESS] 🟢 Closed LONG BTCUSDT @ $52000.00 | PnL: +$374.25 (+3.74%) | Reason: TP
```

---

## How to Monitor

### View Portfolio (Press Ctrl+C first)

```
💼 PORTFOLIO SUMMARY
================================================================================
Balance:          $10,374.25
Equity:           $10,374.25
Total PnL:        $   374.25
Total Return:           3.74%
Total Fees:       $     6.01
--------------------------------------------------------------------------------
Open Positions:            0
Total Trades:              1
Wins:                      1
Losses:                    0
Win Rate:              100.0%
================================================================================
```

### Resume Trading

```powershell
python run_paper_trading.py
```

(Portfolio state is saved, trading resumes from where you left off)

---

## How to Stop

**Graceful shutdown:**
```
Press Ctrl+C
```

**Expected:**
```
⏹️ Stopping paper trading...

📊 Final Portfolio Summary:
[Shows current state]

👋 Paper trading stopped by user
```

---

## Troubleshooting

### "Telegram client not connecting"

**Check .env file:**
```powershell
Get-Content .env | Select-String "TELEGRAM"
```

**Expected:**
```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123...
TELEGRAM_PHONE_NUMBER=+1234567890
```

**Fix:** Update .env with correct values from https://my.telegram.org/

---

### "Cannot access channel"

**Verify channel username:**
- Open Telegram desktop/web
- Go to channel
- Check URL: t.me/**channel_username**
- Use channel_username (without @)

**Add to config:**
```python
CHANNELS = ["channel_username"]  # No @ symbol
```

---

### "No signals detected"

**Check channels:**
1. Verify you're in the channels (join if not)
2. Check recent messages (should have BUY/SELL signals)
3. Test parser with example message

**Manual test:**
```powershell
python -c "from telegram.parser import parse_message; print(parse_message({'text': 'YOUR_MESSAGE_HERE', 'timestamp': '2025-01-01T00:00:00', 'source': 'test'}))"
```

---

### "Script crashes"

**Check logs:**
```powershell
Get-Content logs\trading.log -Tail 50
Get-Content logs\errors.log -Tail 50
```

**Common fixes:**
1. Update dependencies: `pip install --upgrade -r requirements.txt`
2. Clear session: Delete `signal_listener_session.session`
3. Check network: Ensure internet connection stable
4. Check API keys: Verify .env credentials

---

## Next Steps

### Day 1-7 (Week 1)
- [ ] Let it run 24/7 (or as much as possible)
- [ ] Check portfolio daily
- [ ] Monitor for errors
- [ ] Expect 20-30 trades

### Day 8-14 (Week 2)
- [ ] Analyze first week performance
- [ ] Review win rate (target >50%)
- [ ] Check max drawdown (should be <20%)
- [ ] Continue running

### Day 15-28 (Week 3-4)
- [ ] Aim for 100+ total trades
- [ ] Target win rate >60%
- [ ] Max drawdown <15%
- [ ] If validated → Prepare for live

### After Validation
- [ ] Read `DEPLOYMENT_CHECKLIST.md`
- [ ] Complete all pre-live steps
- [ ] Start live with $500-1000 (5-10% capital)
- [ ] Scale gradually

---

## Important Reminders

### ✅ DO
- Run 24/7 for best results
- Monitor daily
- Let system handle trades automatically
- Trust the risk limits
- Keep logs for analysis

### ❌ DON'T
- Interfere with trades manually
- Change config mid-run
- Skip paper trading validation
- Rush to live trading
- Panic on losing trades (normal!)

---

## Success Metrics

### Week 1 Target
- Uptime: >80%
- Trades: 20-30
- Win rate: >50%
- System stable

### Week 4 Target
- Trades: 100+
- Win rate: >60%
- Max drawdown: <15%
- Ready for live

---

## Emergency Actions

### Stop Trading
```powershell
# Press Ctrl+C in terminal
# Or close terminal window
```

### View Portfolio
```powershell
python -c "from trading.portfolio import Portfolio; from config.trading_config import PaperConfig; p = Portfolio(10000, PaperConfig.PORTFOLIO_FILE); p.print_summary()"
```

### Clear Portfolio (Start Fresh)
```powershell
Remove-Item data\paper_portfolio.json
Remove-Item data\paper_trades.jsonl
# Next run will start with $10K again
```

---

## Support Files

- **Full manual:** TRADING_PIPELINE_README.md
- **Deployment guide:** DEPLOYMENT_CHECKLIST.md
- **Implementation details:** IMPLEMENTATION_SUMMARY.md
- **Configuration:** config/trading_config.py
- **Logs:** logs/trading.log

---

## 🎯 You're Ready!

**Start now:**
```powershell
python run_paper_trading.py
```

**Monitor:**
- Terminal output (real-time logs)
- data/paper_portfolio.json (current state)
- data/paper_trades.jsonl (trade history)
- logs/trading.log (detailed logs)

**Goal:**
- Run for 2-4 weeks
- Achieve 100+ trades
- Validate >60% win rate
- Then go live! 🚀

---

**Questions? Check:**
1. TRADING_PIPELINE_README.md (troubleshooting section)
2. logs/errors.log (error details)
3. Verify config/trading_config.py settings

**Good luck! 💰📈🎉**
