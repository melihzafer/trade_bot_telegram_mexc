# Risk Sentinel - Documentation

## 🛡️ Overview

The Risk Sentinel is the **guardian of capital** for Project Chimera. It acts as a strict gatekeeper that validates every signal and enforces risk limits to prevent catastrophic losses.

## 🎯 Key Features

### 1. Circuit Breaker System
- **Daily Loss Limit**: Automatically halts trading if daily losses exceed threshold (default: 5%)
- **Weekly Loss Limit**: Monitors weekly performance for sustained drawdowns
- **Auto-Reset**: Resets at midnight UTC, allowing fresh start each day

### 2. Symbol Management
- **Whitelist**: Only approved symbols can be traded
- **Blacklist**: Permanently blocks scam/delisted coins
- **Dynamic Updates**: Add/remove symbols on the fly

### 3. Correlation Protection
- **Grouped Assets**: Prevents over-exposure to correlated assets (BTC, ETH, etc.)
- **Configurable Limits**: Set max positions per correlation group
- **Smart Detection**: Automatically identifies related symbols

### 4. Kill Switch
- **File-Based**: Create `data/EMERGENCY_STOP` to halt all trading
- **Instant**: Checked before every validation
- **Remote Control**: Can be activated via API/script

### 5. Advanced Position Sizing
- **Risk-Per-Trade**: Calculates size based on stop loss distance
- **Equity-Based**: Scales with account size
- **Safe Guards**: Prevents over-leveraging

## 📦 Installation

Already included in Project Chimera. No additional installation needed.

## ⚙️ Configuration

### Basic Setup

```python
from trading.risk_manager import RiskSentinel

# Initialize with default settings
sentinel = RiskSentinel(initial_equity=10000)

# Or load from config file
sentinel = RiskSentinel(
    initial_equity=10000,
    config_file=Path("config/risk_config.json")
)
```

### Configuration File (`config/risk_config.json`)

```json
{
  "allowed_symbols": [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT"
  ],
  "blacklisted_symbols": [
    "LUNAUSTD",
    "USTUSDT",
    "FTXUSDT"
  ],
  "max_correlated_trades": 2,
  "updated_at": "2025-01-20T00:00:00Z"
}
```

### Risk Parameters (`config/trading_config.py`)

```python
class RiskConfig:
    DAILY_LOSS_LIMIT_PCT = 0.05  # 5% daily stop
    WEEKLY_LOSS_LIMIT_PCT = 0.15  # 15% weekly stop
    MAX_CONCURRENT_TRADES = 5
    RISK_PER_TRADE_PCT = 0.01  # Risk 1% per trade
    MAX_LEVERAGE = 3
```

## 🎯 Usage

### 1. Validate Signals

```python
# Validate before executing
result = sentinel.validate_signal(
    symbol="BTCUSDT",
    side="LONG",
    entry=42000.0,
    sl=40000.0,
    tp=45000.0,
    open_positions=[{'symbol': 'ETHUSDT'}]  # Optional
)

if result.valid:
    print("✅ Signal approved!")
    # Execute trade
else:
    print(f"❌ Signal rejected: {result.reason}")

# Check for warnings
if result.warnings:
    print(f"⚠️  Warnings: {', '.join(result.warnings)}")
```

### 2. Calculate Position Size

```python
# Calculate safe quantity based on risk
sizing = sentinel.calculate_safe_quantity(
    equity=10000,
    entry_price=42000,
    sl_price=40000,  # Required for accurate sizing
    risk_pct=0.01  # Optional, uses config default
)

print(f"Quantity: {sizing['quantity']}")
print(f"Position Value: ${sizing['position_value']}")
print(f"Risk Amount: ${sizing['risk_amount']}")
```

### 3. Monitor Circuit Breaker

```python
# Update equity after each trade
sentinel.update_equity(new_equity=9500)

# Check if circuit breaker triggered
if sentinel.check_circuit_breaker():
    print("🔴 Circuit breaker active - stop trading!")
else:
    print("🟢 Within limits - trading allowed")
```

### 4. Check Kill Switch

```python
if sentinel.check_kill_switch():
    print("🔪 Kill switch active - all trading halted!")
else:
    print("✅ Kill switch not active")
```

### 5. Manage Whitelist/Blacklist

```python
# Add to whitelist
sentinel.add_to_whitelist("ADAUSDT")

# Remove from whitelist
sentinel.remove_from_whitelist("ADAUSDT")

# Add to blacklist
sentinel.add_to_blacklist("SCAMCOIN")

# Remove from blacklist
sentinel.remove_from_blacklist("SCAMCOIN")
```

### 6. Activate/Deactivate Kill Switch

```python
# Activate (creates emergency stop file)
sentinel.activate_kill_switch(reason="Manual intervention")

# Deactivate (removes file)
sentinel.deactivate_kill_switch()
```

### 7. Get Risk Metrics

```python
metrics = sentinel.get_risk_metrics()

print(f"Equity: ${metrics.current_equity:,.2f}")
print(f"Daily PnL: ${metrics.daily_pnl:+,.2f} ({metrics.daily_pnl_pct:+.2f}%)")
print(f"Circuit Breaker: {'🔴 ACTIVE' if metrics.circuit_breaker_active else '🟢 Normal'}")
print(f"Kill Switch: {'🔴 ACTIVE' if metrics.kill_switch_active else '🟢 Normal'}")
```

### 8. Print Status Report

```python
sentinel.print_status()
# Outputs comprehensive status to console
```

## 🔍 Validation Rules

### Critical Checks (Signal Rejected)

1. **Kill Switch**: `data/EMERGENCY_STOP` file exists
2. **Circuit Breaker**: Daily/weekly loss limits exceeded
3. **Whitelist**: Symbol not in allowed list (if enforced)
4. **Blacklist**: Symbol in blacklist
5. **Invalid Prices**: Entry, SL, or TP <= 0
6. **Invalid TP/SL**: 
   - LONG: SL must be below entry, TP above
   - SHORT: SL must be above entry, TP below

### Warning Checks (Signal Approved with Warnings)

1. **Correlation**: Too many positions in same group
2. **R:R Ratio**: Risk/Reward ratio < 1.5
3. **Wide Stop**: Stop loss > 10% from entry

## 📊 Correlation Groups

Pre-defined correlation groups to prevent over-exposure:

```python
CORRELATION_GROUPS = {
    'BTC_GROUP': ['BTCUSDT', 'BTCUSD', 'BTCBUSD'],
    'ETH_GROUP': ['ETHUSDT', 'ETHUSD', 'ETHBUSD'],
    'BNB_GROUP': ['BNBUSDT', 'BNBUSD', 'BNBBUSD'],
    'LAYER1': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT'],
    'DEFI': ['UNIUSDT', 'AAVEUSDT', 'LINKUSDT', 'MKRUSDT'],
    'MEME': ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT'],
}
```

Example: If `max_correlated_trades = 2` and you already have positions in `BTCUSDT` and `ETHUSDT` (both in LAYER1 group), a new signal for `SOLUSDT` will trigger a warning.

## 🚨 Emergency Procedures

### Manual Kill Switch Activation

```bash
# Create emergency stop file
touch data/EMERGENCY_STOP

# Or via Python
python -c "from trading.risk_manager import RiskSentinel; RiskSentinel().activate_kill_switch('Manual stop')"
```

### Manual Kill Switch Deactivation

```bash
# Remove emergency stop file
rm data/EMERGENCY_STOP

# Or via Python
python -c "from trading.risk_manager import RiskSentinel; RiskSentinel().deactivate_kill_switch()"
```

### Reset Circuit Breaker

Circuit breaker automatically resets at midnight UTC. To manually reset:

```python
sentinel.circuit_breaker_active = False
sentinel.circuit_breaker_triggered_at = None
```

## 📈 Integration with Trading Engine

```python
from trading.trading_engine import TradingEngine
from trading.risk_manager import RiskSentinel

# Initialize both
engine = TradingEngine(mode="live")
sentinel = RiskSentinel(initial_equity=10000)

# Before executing signal
parsed_signal = await parser.parse(signal_text)

# Validate with sentinel
result = sentinel.validate_signal(
    symbol=parsed_signal.symbol,
    side=parsed_signal.side,
    entry=parsed_signal.entry_min,
    sl=parsed_signal.sl,
    tp=parsed_signal.tps[0] if parsed_signal.tps else None,
    open_positions=engine.portfolio.get_all_positions()
)

if result.valid:
    # Calculate safe size
    sizing = sentinel.calculate_safe_quantity(
        equity=engine.portfolio.get_equity(),
        entry_price=parsed_signal.entry_min,
        sl_price=parsed_signal.sl
    )
    
    # Execute with calculated size
    await engine.execute_signal(signal)
    
    # Update sentinel equity
    sentinel.update_equity(engine.portfolio.get_equity())
else:
    logger.error(f"Signal rejected: {result.reason}")
```

## 📊 Monitoring & Alerts

### Real-Time Metrics

```python
import asyncio

async def monitor_risk():
    sentinel = RiskSentinel()
    
    while True:
        metrics = sentinel.get_risk_metrics()
        
        # Check for problems
        if metrics.circuit_breaker_active:
            send_alert("Circuit breaker active!")
        
        if metrics.kill_switch_active:
            send_alert("Kill switch active!")
        
        if metrics.daily_pnl_pct < -3:
            send_alert(f"Down {metrics.daily_pnl_pct:.1f}% today")
        
        await asyncio.sleep(60)  # Check every minute
```

### Statistics

```python
stats = sentinel.get_stats()
print(f"Total Validations: {stats['total_validations']}")
print(f"Approval Rate: {stats['approval_rate']:.1f}%")
print(f"Circuit Breaker Triggers: {stats['circuit_breaker_triggers']}")
```

## 🧪 Testing

Run the built-in tests:

```bash
python trading/risk_manager.py
```

Or use the comprehensive test suite:

```bash
python test_risk_sentinel.py
```

## ⚡ Performance

| Operation | Time | Notes |
|-----------|------|-------|
| validate_signal | ~1ms | Fast validation |
| check_circuit_breaker | ~0.5ms | Very fast |
| check_kill_switch | ~0.1ms | File existence check |
| calculate_safe_quantity | ~0.5ms | Simple math |

## 🔧 Troubleshooting

### Circuit Breaker Won't Reset
- Waits until midnight UTC
- Manually reset if needed (see Emergency Procedures)

### Kill Switch Not Working
- Check file path: `data/EMERGENCY_STOP`
- Ensure file exists and is readable
- Check permissions

### Whitelist Too Restrictive
- Set `allowed_symbols = set()` to disable whitelist
- Or add more symbols to config

### Position Sizing Too Small
- Increase `RISK_PER_TRADE_PCT`
- Check equity is sufficient
- Verify stop loss isn't too tight

## 🎯 Best Practices

1. **Always validate before trading**
2. **Update equity after each trade**
3. **Monitor circuit breaker status**
4. **Review rejected signals periodically**
5. **Keep whitelist updated**
6. **Test with paper trading first**
7. **Set conservative loss limits initially**
8. **Monitor correlation warnings**

## 📞 Support

For issues:
1. Check logs in `logs/` directory
2. Review sentinel status with `print_status()`
3. Check config file is valid JSON
4. Verify risk parameters in `trading_config.py`

## 🚀 Next Steps

Phase 3 Complete! Ready for:
- Phase 4: 24/7 autonomous operation
- Advanced alerting systems
- Machine learning risk models
- Multi-exchange support
