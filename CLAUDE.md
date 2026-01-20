# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MEXC Multi-Source Trading System** - An automated crypto trading bot that monitors Telegram channels for trading signals, backtests them against historical data, and executes trades in paper or live mode with comprehensive risk management.

## Common Commands

### Development & Testing

```powershell
# Run paper trading (simulated trading with real-time prices)
python run_paper_trading.py

# Run live trading (⚠️ REAL MONEY - requires validation first)
python run_live_trading.py

# View portfolio summary (paper mode)
python -c "from trading.portfolio import Portfolio; from config.trading_config import PaperConfig; p = Portfolio(10000, PaperConfig.PORTFOLIO_FILE); p.print_summary()"

# Test signal parser with example message
python -c "from telegram.parser import parse_message; result = parse_message({'text': '🟢 LONG\n💲 BTCUSDT\n📈 Entry: 50000\n🎯 Target: 52000\n🛑 Stop Loss: 48000', 'timestamp': '2025-01-01T00:00:00', 'source': 'test'}); print(result)"

# Validate configuration
python config/trading_config.py

# View trading logs
Get-Content logs\trading.log -Tail 50

# View error logs
Get-Content logs\errors.log -Tail 50

# View recent trades (paper mode)
Get-Content data\paper_trades.jsonl | Select-Object -Last 10
```

### Python Imports

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify Python version (3.10+ required)
python --version
```

### Emergency Actions

```powershell
# EMERGENCY STOP (live trading only) - stops NEW trades immediately
New-Item -Path "data\EMERGENCY_STOP" -ItemType File

# Resume trading after emergency stop
Remove-Item data\EMERGENCY_STOP
```

## Architecture

### Core Trading Pipeline

```
Telegram Signals → Parser → Risk Manager → Trading Engine → Portfolio
                                                ↓
                                        Exchange API (MEXC/Binance)
```

**Key Flow:**
1. **Signal Listener** (`telegram/signal_listener.py`) monitors Telegram channels in real-time
2. **Parser** (`telegram/parser.py`) extracts BUY/SELL, symbol, entry, TP, SL using 4 regex patterns
3. **Risk Manager** (`trading/risk_manager.py`) validates against position limits, loss limits, drawdown
4. **Trading Engine** (`trading/trading_engine.py`) executes trades based on mode (paper/live)
5. **Portfolio** (`trading/portfolio.py`) tracks positions, PnL, equity, win rate

### Trading Modes (Configured in `config/trading_config.py`)

- **`backtest`**: Test signals on historical data (no real-time execution)
- **`paper`**: Simulated trading with live prices, fees (0.02% maker / 0.06% taker), and slippage (0.1%)
- **`live`**: Real MEXC API orders with triple confirmation and emergency stop

**Critical:** Always set `TRADING_MODE` in `config/trading_config.py` before running.

### Directory Structure

- **`telegram/`**: Telethon-based signal collection and parsing
  - `signal_listener.py`: Real-time channel monitoring
  - `parser.py`: 4 regex patterns for English/Turkish signal formats
  - `collector.py`: Message collection to JSONL

- **`trading/`**: Core trading logic
  - `trading_engine.py`: Main orchestrator, handles signal queue and exit monitoring
  - `portfolio.py`: Position tracking, PnL calculation, state persistence
  - `risk_manager.py`: Pre-trade validation (position size, limits, drawdown)
  - `paper_trader.py`: Paper mode simulator

- **`parsers/`**: Advanced parsing utilities
  - `enhanced_parser.py`: Channel-specific parser profiles
  - `number_normalizer.py`: Handles Turkish number formats (comma as decimal)

- **`utils/`**: Infrastructure
  - `config.py`: Loads `.env` environment variables
  - `binance_api.py`: Live price data (fallback from MEXC)
  - `mexc_api.py`: MEXC exchange API client (ccxt wrapper)
  - `logger.py`: Rich console + rotating file logs

- **`config/`**: Configuration
  - `trading_config.py`: **Central config file** - risk limits, mode selection, all trading parameters
  - `channels.csv`: List of monitored Telegram channels

### Data Persistence

- **`data/paper_portfolio.json`**: Paper trading portfolio state (balance, positions, PnL)
- **`data/paper_trades.jsonl`**: Append-only paper trade history
- **`data/live_positions.json`**: Live trading portfolio state
- **`data/live_trades.jsonl`**: Append-only live trade history
- **`data/signals_raw.jsonl`**: Raw Telegram messages
- **`data/EMERGENCY_STOP`**: When exists, halts new trades in live mode

### Risk Management System

**Position Sizing Formula:**
```
Risk Amount = Account Equity × (Risk % / 100)
Position Size = (Risk Amount / |Entry - SL|) × Leverage / Entry
```

**Safety Limits** (configured in `RiskConfig`):
- **Daily Loss Limit**: 5% → stops new trades
- **Weekly Loss Limit**: 15% → stops new trades
- **Max Drawdown**: 25% → emergency halt
- **Max Concurrent Trades**: 5 → queues new signals
- **Max Position Size**: 10% of capital per trade
- **Min Position Size**: 10 USDT (exchange minimum)

## Signal Parser Patterns

The parser (`telegram/parser.py`) supports 4 formats:

1. **Emoji Format**: `🟢 LONG`, `💲 BTCUSDT`, `📈 Entry: 50000`
2. **Keyword Format**: `BUY BTCUSDT ENTRY 50000 TP 52000 SL 48000`
3. **Turkish Format**: `AL BTCUSDT GİRİŞ 50000 HEDEF 52000 ZARAR 48000`
4. **Label Format**: `Symbol: BTCUSDT`, `Entry: 50000`, `Target: 52000`

**Number Normalization**: Turkish channels use commas as decimals (e.g., `50,000` → `50000.0`), handled by `number_normalizer.py`.

## Configuration Priority

**Order of precedence:**
1. **`config/trading_config.py`** - Primary config for all trading parameters
2. **`.env`** - Secrets (API keys, Telegram credentials)
3. Code defaults (fallback only)

**Critical `.env` variables:**
```env
# Telegram (required for signal listener)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE_NUMBER=+1234567890

# MEXC (required for live trading)
MEXC_API_KEY=mx0v...
MEXC_API_SECRET=your_secret

# Binance (price data fallback)
BINANCE_API_KEY=optional
BINANCE_API_SECRET=optional
```

## Paper Trading Validation Criteria

Before live trading, paper mode must achieve:
- **Duration**: 2-4 weeks continuous operation
- **Trade Count**: Minimum 100 trades
- **Win Rate**: > 60%
- **Max Drawdown**: < 15%
- **Consistency**: Positive PnL trend

## Important Gotchas

1. **Never commit `.env`** - Contains API keys and session strings
2. **Telegram session file** (`signal_listener_session.session`) is sensitive, don't share
3. **Emergency stop only prevents NEW trades** - existing positions remain open, must close manually on MEXC
4. **Parser order matters** - Patterns tested sequentially, first match wins
5. **Turkish number format** - Commas used as decimal separators in some channels
6. **MEXC API rate limits** - Binance used as fallback for price data if MEXC fails
7. **Position sync in live mode** - Every 30 seconds, reconciles local state with MEXC positions
8. **Triple confirmation for live trading** - Requires three explicit confirmations to prevent accidental real money usage

## Deployment Notes

- **Railway**: Use `Procfile` for cloud deployment (`web: python api.py` for API, `worker: python main.py --mode collector` for signal collection)
- **24/7 Operation**: Paper trading should run continuously for validation
- **Monitoring**: Check `logs/trading.log` and portfolio state regularly
- **Recovery**: Portfolio state persists to JSON, safe to restart scripts

## Technology Stack

- **Telegram**: Telethon (async MTProto client)
- **Exchange**: ccxt (MEXC/Binance unified API)
- **Data Validation**: Pydantic
- **Logging**: Rich (colored terminal) + rotating file logs
- **Data Processing**: Pandas, NumPy
- **Web API**: Flask (optional, for Railway dashboard)

## Code Style

- **Type Hints**: Required for all new functions (Python 3.10+)
- **Error Handling**: Wrap all external API calls in try/except with logging
- **No Hardcoded Secrets**: Use `os.getenv()` or `Config` classes
- **Docstrings**: Include for all public classes/functions
- **Configuration**: All tunable parameters in `config/trading_config.py`, not scattered in code

## Testing Philosophy

- **No unit tests** currently in codebase
- **Testing approach**: Run paper trading for validation
- **Debug scripts**: Multiple `debug_*.py` and `test_*.py` files for manual testing
- **Validation**: Real-world paper trading performance over weeks

## When Modifying Code

1. **Changing risk parameters**: Edit `config/trading_config.py`, not individual files
2. **Adding new signal formats**: Update `telegram/parser.py` regex patterns array
3. **Exchange integration**: Use ccxt for consistency, add to `utils/` directory
4. **Logging changes**: Follow existing pattern with `utils/logger.py`
5. **State persistence**: Always use JSON for portfolio state, JSONL for trade history (append-only)
