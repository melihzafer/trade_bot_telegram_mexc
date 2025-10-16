# 🤖 Automated Trading Pipeline

Complete backtest → paper → live trading system for MEXC/Binance with Telegram signal integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Trading Modes](#trading-modes)
- [Safety Features](#safety-features)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

Automated trading system that:
- ✅ Monitors Telegram channels for trading signals
- ✅ Validates and deduplicates signals
- ✅ Executes trades with risk management
- ✅ Tracks portfolio and performance
- ✅ Supports backtest, paper, and live trading modes

### Key Features

- **Real-time signal parsing**: English/Turkish format support
- **Risk management**: Position sizing, loss limits, concurrent trade limits
- **Paper trading**: Simulated trading with fees/slippage
- **Live trading**: MEXC API integration with safety mechanisms
- **Portfolio tracking**: Balance, PnL, win rate, equity
- **Emergency stop**: Instant halt mechanism for live trading

---

## 🏗️ Architecture

```
trade_bot_telegram_mexc/
├── config/
│   └── trading_config.py          # All mode settings (risk, paper, live)
├── trading/
│   ├── portfolio.py                # Position/trade tracking
│   ├── trading_engine.py           # Unified trading orchestrator
│   ├── risk_manager.py             # Risk limits enforcement
│   └── paper_trader.py             # Paper trading simulator
├── telegram/
│   ├── parser.py                   # Signal parsing (4 patterns)
│   └── signal_listener.py          # Real-time Telegram monitoring
├── utils/
│   ├── config.py                   # Environment variables (.env)
│   ├── logger.py                   # Colored logging
│   └── binance_api.py              # Price data client
├── data/
│   ├── paper_portfolio.json        # Paper trading state
│   ├── paper_trades.jsonl          # Paper trade history
│   ├── live_positions.json         # Live trading state
│   ├── live_trades.jsonl           # Live trade history
│   └── EMERGENCY_STOP              # Emergency halt file
├── run_paper_trading.py            # Paper mode launcher
└── run_live_trading.py             # Live mode launcher
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MEXC account (for live trading)
- Telegram API credentials
- `.env` file configured

### Installation

```powershell
# Clone repository
cd "d:\OMNI Tech Solutions\trade_bot_telegram_mexc"

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Configuration

Edit `config/trading_config.py`:

```python
# Select trading mode
TRADING_MODE = "paper"  # backtest | paper | live

# Risk settings
class RiskConfig:
    INITIAL_CAPITAL = 10000.0           # Starting capital
    MAX_POSITION_SIZE_PCT = 0.10        # 10% per trade
    MAX_CONCURRENT_TRADES = 5           # Max open positions
    DAILY_LOSS_LIMIT_PCT = 0.05         # Stop at 5% daily loss
    WEEKLY_LOSS_LIMIT_PCT = 0.15        # Stop at 15% weekly loss
    MAX_DRAWDOWN_PCT = 0.25             # Emergency stop at 25%
```

### Run Paper Trading

```powershell
python run_paper_trading.py
```

### Run Live Trading (After validation!)

```powershell
# ⚠️ Only after 2-4 weeks of successful paper trading!
python run_live_trading.py
```

---

## ⚙️ Configuration

### Trading Mode Selection

**config/trading_config.py:**

```python
TRADING_MODE: TradingMode = "paper"  # Choose: backtest | paper | live
```

### Risk Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `INITIAL_CAPITAL` | 10,000 USDT | Starting balance |
| `MAX_POSITION_SIZE_PCT` | 10% | Maximum per trade |
| `MAX_CONCURRENT_TRADES` | 5 | Max open positions |
| `DAILY_LOSS_LIMIT_PCT` | 5% | Daily stop loss |
| `WEEKLY_LOSS_LIMIT_PCT` | 15% | Weekly stop loss |
| `MAX_DRAWDOWN_PCT` | 25% | Emergency stop threshold |
| `MIN_POSITION_SIZE_USDT` | 10 USDT | Minimum trade size |

### Paper Trading Settings

```python
class PaperConfig:
    INITIAL_BALANCE = 10000.0
    SIMULATE_FEES = True
    MAKER_FEE = 0.0002              # 0.02%
    TAKER_FEE = 0.0006              # 0.06%
    SIMULATE_SLIPPAGE = True
    AVG_SLIPPAGE_PCT = 0.001        # 0.1%
```

### Live Trading Settings

```python
class LiveConfig:
    REQUIRE_CONFIRMATION = True      # Manual approval
    DRY_RUN_FIRST = True            # Validate before submit
    ENABLE_EMERGENCY_STOP = True
    EMERGENCY_STOP_FILE = Path("data/EMERGENCY_STOP")
    SYNC_INTERVAL_SECONDS = 30      # Position sync frequency
```

### Signal Listener Settings

```python
class SignalConfig:
    CHANNELS = ["channelusername1", "channelusername2"]
    POLL_INTERVAL_SECONDS = 5
    ENABLE_DUPLICATE_DETECTION = True
    DUPLICATE_WINDOW_MINUTES = 10
```

---

## 📊 Trading Modes

### 1. Backtest Mode

Test strategies on historical data.

**Usage:**
```python
from trading.backtest import run_backtest

results = run_backtest(
    signals_file="data/signals_parsed.jsonl",
    prices_file="data/backtest_results.jsonl"
)
```

**Output:**
- Win rate
- Total PnL
- Max drawdown
- Trade statistics

### 2. Paper Trading Mode

Simulated trading with real-time prices.

**Features:**
- ✅ Real-time Telegram signal monitoring
- ✅ Live price data (Binance API)
- ✅ Simulated fees (0.02% maker / 0.06% taker)
- ✅ Simulated slippage (0.1% average)
- ✅ No real money risk

**Command:**
```powershell
python run_paper_trading.py
```

**Validation Criteria (before live):**
- Run for 2-4 weeks
- Minimum 100 trades
- Win rate > 60%
- Max drawdown < 15%
- Consistent positive PnL

### 3. Live Trading Mode

Real trading with MEXC API.

**⚠️ WARNING: REAL MONEY AT RISK**

**Safety Checklist:**
- [ ] Paper trading validated (2-4 weeks, 100+ trades)
- [ ] Win rate > 60% in paper mode
- [ ] Risk limits configured
- [ ] Emergency stop instructions understood
- [ ] MEXC API credentials configured
- [ ] Small initial capital (5-10% of total)
- [ ] Monitoring system in place

**Command:**
```powershell
python run_live_trading.py
```

**Triple confirmation required:**
1. "I UNDERSTAND THE RISKS"
2. "START LIVE TRADING"
3. "YES"

---

## 🛡️ Safety Features

### 1. Risk Limits

| Limit | Threshold | Action |
|-------|-----------|--------|
| Daily Loss | 5% | Stop new trades |
| Weekly Loss | 15% | Stop new trades |
| Max Drawdown | 25% | Emergency halt |
| Concurrent Trades | 5 | Queue new signals |

### 2. Emergency Stop (Live Mode)

**Create emergency stop file:**

```powershell
# Windows PowerShell
New-Item -Path "data\EMERGENCY_STOP" -ItemType File

# Windows CMD
type nul > data\EMERGENCY_STOP

# Linux/Mac
touch data/EMERGENCY_STOP
```

**Effect:**
- ⚠️ Stops NEW trades immediately
- ⚠️ Existing positions remain open
- ⚠️ Manual closure via MEXC required

**To resume:**
1. Delete `data\EMERGENCY_STOP` file
2. Restart trading script

### 3. Position Sync (Live Mode)

Every 30 seconds:
- Fetches open positions from MEXC
- Compares with local portfolio
- Reconciles differences
- Logs discrepancies

### 4. Order Validation (Live Mode)

Before each order:
- ✅ Check emergency stop file
- ✅ Validate symbol exists on MEXC
- ✅ Check risk limits (daily/weekly loss)
- ✅ Verify sufficient balance
- ✅ Validate position size
- ✅ Check max concurrent trades

---

## 📈 Monitoring

### Portfolio Summary

View anytime (paper mode):
```powershell
python -c "from trading.portfolio import Portfolio; from config.trading_config import PaperConfig; p = Portfolio(10000, PaperConfig.PORTFOLIO_FILE); p.print_summary()"
```

**Output:**
```
💼 PORTFOLIO SUMMARY
================================================================================
Balance:          $10,095.00
Equity:           $10,145.00
Total PnL:        $   145.00
Total Return:           1.45%
Total Fees:       $    10.00
--------------------------------------------------------------------------------
Open Positions:            1
Total Trades:              5
Wins:                      3
Losses:                    2
Win Rate:               60.0%
================================================================================

📊 OPEN POSITIONS:
  LONG  ETHUSDT      @ $3000.0000 | PnL:    +$50.00 (+1.67%)
```

### Trade History

**Paper trades:**
```powershell
Get-Content data\paper_trades.jsonl | Select-Object -Last 10
```

**Live trades:**
```powershell
Get-Content data\live_trades.jsonl | Select-Object -Last 10
```

### Logs

```powershell
# Trading logs
Get-Content logs\trading.log -Tail 50

# Order logs
Get-Content logs\orders.log -Tail 50

# Error logs
Get-Content logs\errors.log -Tail 50
```

---

## 🔧 Troubleshooting

### Issue: Telegram client not connecting

**Solution:**
```python
# Verify credentials in .env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE_NUMBER=+1234567890

# Test connection
python -c "from telegram.signal_listener import SignalListener; from trading.trading_engine import TradingEngine; import asyncio; asyncio.run(SignalListener(TradingEngine()).init_client())"
```

### Issue: MEXC API connection failed

**Symptoms:**
```
[WinError 10054] An existing connection was forcibly closed
```

**Solutions:**
1. Check firewall settings
2. Verify API credentials in `.env`
3. Try MEXC testnet first
4. Use Binance as fallback for price data

**Test MEXC connection:**
```python
import ccxt
exchange = ccxt.mexc({
    'apiKey': 'YOUR_KEY',
    'secret': 'YOUR_SECRET'
})
print(exchange.fetch_ticker('BTC/USDT'))
```

### Issue: Signals not being detected

**Check parser:**
```python
from telegram.parser import parse_message

test_message = """
🟢 LONG
💲 BTCUSDT
📈 Entry : 50000
🎯 Target : 52000
🛑 Stop Loss : 48000
"""

result = parse_message({
    "text": test_message,
    "timestamp": "2025-01-01T00:00:00",
    "source": "test"
})

print(result)
```

### Issue: Position not closing at TP/SL

**Verify price checks:**
```python
from trading.trading_engine import TradingEngine

engine = TradingEngine(mode="paper")
engine.check_exit_conditions()  # Manual check
```

**Check logs:**
```powershell
Get-Content logs\trading.log | Select-String -Pattern "TP|SL|close"
```

---

## 📚 Additional Resources

### Files

- **Configuration**: `config/trading_config.py`
- **Portfolio state**: `data/paper_portfolio.json` or `data/live_positions.json`
- **Trade history**: `data/paper_trades.jsonl` or `data/live_trades.jsonl`
- **Emergency stop**: `EMERGENCY_STOP_INSTRUCTIONS.txt`

### Commands

```powershell
# Run paper trading
python run_paper_trading.py

# Run live trading
python run_live_trading.py

# View portfolio
python -m trading.portfolio

# Test signal parser
python -m telegram.parser

# View logs
Get-Content logs\trading.log -Wait
```

### Support

- Check `PROJECT_PLAN.md` for development roadmap
- Review `data/` directory for portfolio/trade history
- Inspect `logs/` directory for detailed execution logs

---

## ⚠️ Disclaimer

**TRADING INVOLVES SUBSTANTIAL RISK OF LOSS**

- This software is provided "as is" without warranty
- You are fully responsible for your trading decisions
- Always test thoroughly in paper mode first
- Only trade with capital you can afford to lose
- Past performance does not guarantee future results
- The developers assume no liability for trading losses

**USE AT YOUR OWN RISK**

---

## 📝 License

[Your License Here]

---

## 🎯 Next Steps

After setup:

1. **Week 1-2**: Run paper trading, monitor closely
2. **Week 3-4**: Analyze results (min 100 trades)
3. **Validation**: Win rate > 60%, max drawdown < 15%
4. **Go Live**: Start with 5-10% capital
5. **Scale**: Gradually increase based on performance

**Good luck! 🚀**
