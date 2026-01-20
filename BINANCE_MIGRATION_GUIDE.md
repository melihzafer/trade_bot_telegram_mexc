# 🔄 Binance Futures Migration Guide

## Overview

The Trading Engine has been refactored to use **Binance Futures** instead of MEXC due to geoblocking issues.

---

## 🔑 Key Changes

### 1. **Exchange Platform**
- **Before:** MEXC Futures
- **After:** Binance Futures

### 2. **Environment Variables**
```bash
# Old (MEXC)
MEXC_API_KEY=...
MEXC_API_SECRET=...

# New (Binance)
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

### 3. **Symbol Format**
- **Telegram Signals:** `BTCUSDT` (no slash)
- **Binance CCXT:** `BTC/USDT` (with slash)
- **Solution:** Automatic normalization via `_normalize_symbol()`

### 4. **Position Mode**
- **Binance Default:** Hedge Mode (dual-side positions)
- **Project Chimera:** One-Way Mode (single direction per symbol)
- **Implementation:** Automatically set to One-Way on initialization

### 5. **Precision Handling**
- **Issue:** Binance rejects orders with invalid precision (e.g., `0.123456789` BTC)
- **Solution:** Use `exchange.amount_to_precision()` and `exchange.price_to_precision()`

---

## 📋 Migration Steps

### Step 1: Get Binance API Keys

1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Click **"Create API"**
3. Complete security verification
4. **Important:** Enable **"Enable Futures"** permission
5. Copy API Key and Secret Key
6. **Whitelist IP** (optional but recommended for security)

### Step 2: Update Environment Variables

Edit your `.env` file:

```bash
# Replace MEXC credentials with Binance
BINANCE_API_KEY=your_actual_binance_api_key
BINANCE_API_SECRET=your_actual_binance_secret_key
```

### Step 3: Update Code (Already Done)

The following changes have been implemented in `trading/trading_engine.py`:

- ✅ Exchange initialization switched to `ccxt.binance`
- ✅ Environment variables updated (`BINANCE_API_KEY`, `BINANCE_API_SECRET`)
- ✅ Symbol normalization added (`_normalize_symbol()`)
- ✅ Position mode set to One-Way
- ✅ Precision handling implemented

### Step 4: Test in Paper Mode

```bash
# Test with paper trading first
python main_autonomous.py
```

Verify:
- Parser correctly detects signals
- Risk Sentinel validates properly
- No errors in logs

### Step 5: Test in Dry Run Mode

Edit `.env`:
```bash
TRADING_MODE=live
```

Edit `config/trading_config.py`:
```python
DRY_RUN_FIRST = True  # Will log orders without executing
```

Run:
```bash
python main_autonomous.py
```

Check logs for:
- "🧪 DRY RUN: Would place order..."
- Ensure no actual orders are placed

### Step 6: Go Live (When Ready)

Edit `config/trading_config.py`:
```python
DRY_RUN_FIRST = False
REQUIRE_CONFIRMATION = False  # Or implement confirmation mechanism
```

Run:
```bash
python main_autonomous.py
```

⚠️ **Monitor closely for the first few trades!**

---

## 🔧 Technical Details

### Symbol Normalization

The `_normalize_symbol()` method handles conversion:

```python
# Input formats supported:
BTCUSDT       → BTC/USDT
BTC/USDT      → BTC/USDT (unchanged)
ETHUSDT       → ETH/USDT
SOLUSDT       → SOL/USDT
```

### Position Mode Setting

On initialization, the engine sets Binance to One-Way Mode:

```python
await exchange.fapiPrivate_post_positionside_dual({
    'dualSidePosition': 'false'
})
```

**Why One-Way Mode?**
- Simpler position management
- Avoids hedge mode complexity
- Aligns with Risk Sentinel logic (one position per symbol)

### Precision Handling

Before placing orders:

```python
# Get market precision
market = self.markets[symbol]

# Apply precision
quantity = float(exchange.amount_to_precision(symbol, quantity))
price = float(exchange.price_to_precision(symbol, price))
```

This prevents "Invalid Quantity" or "Invalid Price" errors.

---

## ⚠️ Important Differences: MEXC vs Binance

| Feature | MEXC | Binance |
|---------|------|---------|
| **Symbol Format** | `BTCUSDT` | `BTC/USDT` |
| **Position Mode** | One-Way (default) | Hedge Mode (default) |
| **Precision** | Less strict | Very strict |
| **API Rate Limits** | Moderate | Strict (1200 weight/min) |
| **Leverage Limits** | Up to 200x | Up to 125x (varies by symbol) |
| **Minimum Order** | Varies | Strict minimum notional ($5-10) |
| **Fees** | 0.02% taker | 0.04% taker (0.02% with BNB) |

---

## 🧪 Testing Checklist

Before going live, verify:

- [ ] Binance API keys set in `.env`
- [ ] Keys have "Enable Futures" permission
- [ ] Symbol normalization works (check logs)
- [ ] Position mode set to One-Way (check logs: "✅ Position mode set to One-Way")
- [ ] Precision applied correctly (check logs: "🎯 Applied precision")
- [ ] Paper trading executes without errors
- [ ] Dry run mode logs orders correctly
- [ ] Risk Sentinel blocks/allows trades appropriately
- [ ] Telegram notifications work
- [ ] Daily reports are accurate

---

## 🔍 Common Issues & Solutions

### Issue 1: "Missing Binance API credentials"

**Solution:**
```bash
# Check .env file
cat .env | grep BINANCE

# Should show:
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
```

### Issue 2: "Invalid symbol BTC/USDT"

**Solution:**
- Ensure markets are loaded (check logs: "✅ Loaded N market pairs")
- If fails, symbol normalization will still work but may lack precision

### Issue 3: "Invalid Quantity" error

**Solution:**
- Precision handling should fix this automatically
- Check logs for "🎯 Applied precision"
- If still fails, the order size may be below minimum notional

### Issue 4: "Hedge Mode error"

**Solution:**
- Engine automatically sets One-Way Mode
- If error persists, manually set in Binance UI:
  - Go to Futures → Settings → Position Mode → One-way Mode

### Issue 5: "Order rejected: insufficient balance"

**Solution:**
- Check Binance Futures wallet has USDT
- Transfer USDT from Spot to Futures wallet
- Reduce position size in `config/trading_config.py`

---

## 📊 Monitoring

### Check Exchange Connection

```python
# In Python console
from trading.trading_engine import TradingEngine
import asyncio

engine = TradingEngine(mode="live")
print("Exchange:", engine.exchange.name)  # Should show "Binance"
asyncio.run(engine.exchange.close())
```

### Check Symbol Normalization

```python
from trading.trading_engine import TradingEngine

engine = TradingEngine(mode="paper")
print(engine._normalize_symbol("BTCUSDT"))   # BTC/USDT
print(engine._normalize_symbol("ETHUSDT"))   # ETH/USDT
print(engine._normalize_symbol("BTC/USDT"))  # BTC/USDT (unchanged)
```

### Check Markets Loaded

```python
from trading.trading_engine import TradingEngine
import asyncio

async def check():
    engine = TradingEngine(mode="live")
    print(f"Markets loaded: {len(engine.markets)}")
    print("Sample:", list(engine.markets.keys())[:5])
    await engine.exchange.close()

asyncio.run(check())
```

---

## 🚀 Performance Optimization

### Enable BNB Fee Discount

1. Hold BNB in Futures wallet
2. Enable "Use BNB to pay fees" in settings
3. Fees reduce from 0.04% → 0.02%

### IP Whitelisting

1. Go to API Management
2. Add your server IP
3. Restricts API key to specific IPs (security++)

### Rate Limit Management

- CCXT automatically handles rate limits (`enableRateLimit: True`)
- Binance: 1200 weight per minute
- Orders: ~1 weight each
- Price fetching: ~1-2 weight

---

## 📚 Additional Resources

- [Binance Futures API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [CCXT Binance Documentation](https://docs.ccxt.com/#/exchanges/binance)
- [Binance Fees](https://www.binance.com/en/fee/schedule)
- [Binance Testnet](https://testnet.binancefuture.com/) (for testing without real money)

---

## ✅ Migration Checklist Summary

- [ ] Get Binance API keys with Futures enabled
- [ ] Update `.env` with Binance credentials
- [ ] Code changes (already done)
- [ ] Test in paper mode
- [ ] Test in dry run mode
- [ ] Monitor first live trades closely
- [ ] Verify Telegram notifications work
- [ ] Check daily reports
- [ ] Enable BNB fee discount (optional)
- [ ] Whitelist IP (optional)

---

## ⚖️ Disclaimer

**Switching exchanges changes risk profile.**

- Binance has different leverage limits
- Fee structure is different
- API behavior may vary
- **Test thoroughly before going live**
- Start with small positions
- Monitor closely for first 24 hours

**USE AT YOUR OWN RISK**

---

**Migration Date:** January 20, 2026  
**Status:** ✅ Complete  
**Version:** 1.0.0
