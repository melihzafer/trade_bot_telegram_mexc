# 📥 Signal Collection System - Complete

## Overview
Created unified signal collection script for easy data gathering from Telegram channels.

## What Was Added

### New Script: `collect_signals.py`
A simple, all-in-one CLI for collecting signals with two modes:

#### 1. Real-Time Collection
Monitors channels live and saves signals as they arrive:
```bash
# Raw signals (everything)
python collect_signals.py

# Parsed signals (filtered, ready for backtest)
python collect_signals.py --parse
```

**Best for:** 
- Continuous monitoring (24/7 operation)
- Building historical dataset over time
- Production use

#### 2. Historical Collection
Fetches past messages immediately:
```bash
# Last 100 messages per channel (default)
python collect_signals.py --mode historical --parse

# Last 500 messages per channel
python collect_signals.py --mode historical --limit 500 --parse

# Large dataset (1000 messages)
python collect_signals.py --mode historical --limit 1000 --parse
```

**Best for:**
- Quick start / immediate testing
- Backfilling data
- One-time data collection

## Features

✅ **Auto-parsing**: Use `--parse` flag to automatically filter valid trading signals  
✅ **Dual mode**: Real-time monitoring or historical fetching  
✅ **Flexible output**: Custom file paths with `--output`  
✅ **Thread-safe**: Safe for concurrent writes  
✅ **Resume support**: Appends to existing files (real-time mode)  
✅ **Error handling**: Gracefully handles channel access issues  

## Command Reference

### Basic Usage
```bash
# Start real-time collection (press Ctrl+C to stop)
python collect_signals.py --parse

# Collect historical signals
python collect_signals.py --mode historical --limit 500 --parse
```

### Advanced Options
```bash
# Custom output file
python collect_signals.py --output data/custom_signals.jsonl --parse

# Raw collection (no parsing)
python collect_signals.py --mode historical --limit 1000

# Parse later with separate parser
python telegram/parser.py
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--mode` | `realtime` or `historical` | `realtime` |
| `--limit` | Messages per channel (historical only) | `100` |
| `--parse` | Auto-parse and filter signals | `False` |
| `--output` | Custom output file path | `data/signals_raw.jsonl` or `data/signals_parsed.jsonl` |

## Output Format

### Raw Signals (`data/signals_raw.jsonl`)
```json
{
  "source": "crypto_signals",
  "timestamp": "2024-01-15T10:30:00",
  "text": "🟢 LONG\n💲 BTCUSDT\n📈 Entry: 43500\n🎯 TP: 44200\n🛑 SL: 43100"
}
```

### Parsed Signals (`data/signals_parsed.jsonl`)
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "entry": 43500.0,
  "tp": 44200.0,
  "sl": 43100.0,
  "timestamp": "2024-01-15T10:30:00",
  "source": "crypto_signals"
}
```

## Integration with Backtest

Parsed signals are ready for direct backtesting:

```bash
# Step 1: Collect signals
python collect_signals.py --mode historical --limit 500 --parse

# Step 2: Run backtest
python run_backtest.py
```

The backtest script automatically reads from `data/signals_parsed.jsonl`.

## Running in Background

### Windows (PowerShell)
```powershell
# Start hidden
Start-Process python -ArgumentList "collect_signals.py --parse" -WindowStyle Hidden

# Stop (find PID and kill)
Get-Process python | Where-Object {$_.CommandLine -like "*collect_signals*"}
Stop-Process -Id <PID>
```

### Linux/Mac
```bash
# Start in background
nohup python collect_signals.py --parse > collector.log 2>&1 &

# Check if running
ps aux | grep collect_signals

# Stop
pkill -f collect_signals.py
```

## Comparison with Old Scripts

### Old System
- `telegram/collector.py` - Real-time only, no parsing
- `collect_and_analyze.py` - Historical + analysis, complex
- Separate scripts for each mode

### New System (`collect_signals.py`)
- ✅ Unified interface for both modes
- ✅ Built-in parsing option
- ✅ Simple CLI with examples
- ✅ Production-ready error handling
- ✅ Clear output format

## Requirements

**Telegram Configuration:**
- `TELEGRAM_API_ID` in `.env`
- `TELEGRAM_API_HASH` in `.env`
- `TELEGRAM_PHONE` in `.env`
- `TELEGRAM_CHANNELS` in `.env` (comma-separated)

**Example `.env`:**
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_hash_here
TELEGRAM_PHONE=+1234567890
TELEGRAM_CHANNELS=@crypto_signals,@btc_alerts,-1001234567890
```

## Troubleshooting

### "No channels configured"
- Check `TELEGRAM_CHANNELS` in `.env`
- Format: `@username` or `-1001234567890` (channel ID)

### "Could not resolve channel"
- Verify you have access to the channel
- Join private channels before running script
- Check channel username/ID is correct

### "Authentication failed"
- Verify API credentials from https://my.telegram.org/apps
- Check phone number format: `+countrycode1234567890`
- Complete 2FA verification if prompted

### Script stops/crashes
- Check logs in terminal output
- Verify internet connection
- Ensure channels are still accessible

## Usage in Complete Workflow

```bash
# 1. Collect signals (run for 24-48 hours)
python collect_signals.py --parse

# 2. Check collected data
python -c "import json; signals = [json.loads(l) for l in open('data/signals_parsed.jsonl')]; print(f'{len(signals)} signals collected')"

# 3. Run backtest
python run_backtest.py

# 4. Review results
# Open reports/backtest_report_TIMESTAMP.html

# 5. If good results, start paper trading
python run_paper_trading.py
```

## Testing

Test with sample data:
```bash
# Create test environment variable (add to .env temporarily)
# Then run historical collection with limit=10
python collect_signals.py --mode historical --limit 10 --parse
```

## Files Modified/Created

### New Files:
- `collect_signals.py` (11.4 KB) - Main collection script
- `SIGNAL_COLLECTION_COMPLETE.md` (this file)
- `QUICK_START_GUIDE.md` - Complete workflow guide

### Modified Files:
- `README.md` - Added Step 1: Signal Collection section
- `C:/Users/melih/.copilot/session-state/.../plan.md` - Updated with completion

## Status

✅ **Production Ready**

The signal collection system is complete and ready for use. Users can now:
1. Collect signals easily with one command
2. Choose real-time or historical mode
3. Auto-parse signals for direct backtesting
4. Run complete workflow: collect → backtest → paper trade

## Next Steps for User

1. **Configure Telegram** credentials in `.env`
2. **Add channels** to `TELEGRAM_CHANNELS`
3. **Run collector** for 24-48 hours: `python collect_signals.py --parse`
4. **Backtest** collected signals: `python run_backtest.py`
5. **Review results** and proceed to paper trading if good
