# 🚀 Quick Start Guide

## Complete Workflow: From Signal Collection to Backtest

### Prerequisites
✅ Python 3.10+ installed  
✅ Dependencies installed: `pip install -r requirements.txt`  
✅ `.env` configured with Telegram credentials  
✅ Telegram channels added to `TELEGRAM_CHANNELS`  

---

## Step 1: Collect Signals (24-48 hours)

### Option A: Real-Time Collection (Recommended)
Collects signals as they arrive:

```bash
# Collect and auto-parse signals
python collect_signals.py --parse
```

**What it does:**
- Connects to your Telegram channels
- Monitors incoming messages in real-time
- Parses valid trading signals (BUY/SELL with entry/TP/SL)
- Saves to `data/signals_parsed.jsonl`

**Run it in background:**
```bash
# Windows (PowerShell)
Start-Process python -ArgumentList "collect_signals.py --parse" -WindowStyle Hidden

# Linux/Mac
nohup python collect_signals.py --parse > collector.log 2>&1 &
```

⏰ **Let it run for 24-48 hours** to gather enough data for backtest.

---

### Option B: Historical Collection (Quick Start)
Fetches past messages immediately:

```bash
# Collect last 500 messages per channel
python collect_signals.py --mode historical --limit 500 --parse
```

**What it does:**
- Fetches last 500 messages from each channel
- Parses valid signals
- Saves to `data/signals_parsed.jsonl`
- Takes ~2-5 minutes

⚡ **Use this if you want to start backtesting immediately.**

---

## Step 2: Check Collected Data

```bash
# Windows
Get-Content data\signals_parsed.jsonl | Measure-Object -Line

# Linux/Mac
wc -l data/signals_parsed.jsonl
```

**Minimum recommended:** 50+ signals for meaningful backtest results.

---

## Step 3: Run Backtest

### Basic Backtest
Uses default settings (10k capital, 2% risk, MEXC fees):

```bash
python run_backtest.py
```

### Custom Backtest
Adjust parameters to your needs:

```bash
# Custom capital and risk
python run_backtest.py --capital 50000 --risk 0.03

# Filter by date range
python run_backtest.py --start-date 2024-01-01 --end-date 2024-12-31

# Lower fees (VIP account)
python run_backtest.py --maker-fee 0.0001 --taker-fee 0.0003
```

**What it does:**
- Fetches historical OHLCV data from MEXC
- Simulates trades with realistic fees and slippage
- Calculates comprehensive performance metrics
- Generates charts and HTML report

⏱️ **Takes 5-15 minutes** depending on number of signals.

---

## Step 4: Review Results

Open the HTML report in your browser:

```bash
# Windows
start reports\backtest_report_TIMESTAMP.html

# Linux
xdg-open reports/backtest_report_TIMESTAMP.html

# Mac
open reports/backtest_report_TIMESTAMP.html
```

### Key Metrics to Check

✅ **Win Rate**: Should be >60% for profitable strategy  
✅ **Profit Factor**: Should be >1.5 (2.0+ is excellent)  
✅ **Max Drawdown**: Should be <15% (lower is better)  
✅ **Sharpe Ratio**: Should be >1.0 (risk-adjusted performance)  
✅ **Expectancy**: Should be positive (profit per trade)  

---

## Step 5: Decision Time

### ✅ Good Results?
If metrics meet validation criteria:

```bash
# Start paper trading (simulated live trading)
python run_paper_trading.py
```

**Paper trading runs 24/7:**
- Uses real-time prices
- Opens/closes virtual positions
- No real money at risk
- Run for 2-4 weeks

---

### ❌ Poor Results?
If metrics are below targets:

1. **Adjust parser**: Channels might have unique formats
2. **Filter channels**: Remove low-quality sources
3. **Tune parameters**: Adjust risk %, TP/SL distances
4. **Collect more data**: Longer collection = better sample

---

## Quick Reference Commands

```bash
# Collect signals (real-time, parsed)
python collect_signals.py --parse

# Collect historical (500 messages)
python collect_signals.py --mode historical --limit 500 --parse

# Run backtest (default)
python run_backtest.py

# Run backtest (custom)
python run_backtest.py --capital 50000 --risk 0.03

# Start paper trading
python run_paper_trading.py

# Check paper portfolio
python -c "from trading.portfolio import Portfolio; from config.trading_config import PaperConfig; p = Portfolio(10000, PaperConfig.PORTFOLIO_FILE); p.print_summary()"
```

---

## Troubleshooting

### "No signals found"
- Check `.env` has correct `TELEGRAM_CHANNELS`
- Verify channels are accessible (not private without invitation)
- Try historical collection first

### "Failed to fetch OHLCV"
- Symbol might not be available on MEXC
- Check internet connection
- Try with different symbols

### "Matplotlib not installed"
- Run: `pip install matplotlib`
- Or use: `python run_backtest.py --no-charts`

### "Telegram authentication failed"
- Check `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `.env`
- Verify phone number format: `+1234567890`
- Complete 2FA if prompted

---

## Expected Timeline

| Phase | Duration | Action |
|-------|----------|--------|
| **Setup** | 15 min | Install dependencies, configure .env |
| **Collection** | 24-48 hrs | Run collector (or 5 min for historical) |
| **Backtest** | 5-15 min | Analyze collected signals |
| **Review** | 30 min | Check metrics and reports |
| **Paper Trading** | 2-4 weeks | Validate strategy with real-time sim |
| **Live Trading** | Optional | Only after successful paper trading |

---

## Success Criteria

Before moving to paper trading, ensure:
- ✅ 100+ trades in backtest
- ✅ Win rate >60%
- ✅ Profit factor >1.5
- ✅ Max drawdown <15%
- ✅ Positive expectancy
- ✅ Sharpe ratio >1.0

**Remember:** Past performance doesn't guarantee future results. Paper trading is essential before risking real money.
