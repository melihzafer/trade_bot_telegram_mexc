# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

### Environment & installation

- Create and activate virtual environment (examples):
  - Windows PowerShell:
    - `python -m venv .venv`
    - `.venv\\Scripts\\Activate.ps1`
  - Linux/Mac:
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
- Install dependencies:
  - `pip install --upgrade pip`
  - `pip install -r requirements.txt`
- Create environment file from template (if present):
  - Windows: `copy .env.sample .env`
  - Linux/Mac: `cp .env.sample .env`

Most runtime configuration comes from `.env` (Telegram, exchange, risk defaults) plus `config/trading_config.py` (trading mode, risk, logging).

### Core execution entrypoints

#### Legacy 3-stage pipeline (collector → parser → backtest)

- Full system (collector + periodic parser + basic paper trading engine):
  - `python main.py`
  - or `python main.py --mode full`
- Collector only (gather raw messages into `data/signals_raw.jsonl`):
  - `python main.py --mode collector`
- Backtest only (use pre-parsed signals to generate backtest results):
  - `python main.py --mode backtest`
- Run individual components:
  - Parser over raw JSONL → `data/signals_parsed.jsonl`:
    - `python telegram/parser.py`
  - Backtester over parsed signals (uses MEXC/Binance data):
    - `python trading/backtester.py`

This pipeline is still supported and is what `README.md`, `SETUP_GUIDE.md`, and `QUICK_REFERENCE.md` mainly describe.

#### Unified trading engine pipeline (paper & live)

These entrypoints use `config/trading_config.py`, `trading/trading_engine.py`, `trading/portfolio.py`, and `telegram/signal_listener.py`.

- Paper trading (recommended primary entrypoint for current work):
  - `python run_paper_trading.py`
  - Preconditions:
    - `TRADING_MODE = "paper"` in `config/trading_config.py`.
    - `.env` has Telegram credentials and channels.
  - Behavior:
    - Initializes `TradingEngine(mode="paper")`.
    - Starts `SignalListener` which connects to Telegram and parses signals in real time.
    - Uses Binance public API for live prices.
    - Persists portfolio to `data/paper_portfolio.json` and trades to `data/paper_trades.jsonl`.

- Live trading (only after paper-mode validation; heavily safety-wrapped):
  - `python run_live_trading.py`
  - Preconditions (enforced in code):
    - `TRADING_MODE = "live"` in `config/trading_config.py`.
    - Live config passes `validate_config()` checks.
    - `.env` provides valid `MEXC_API_KEY` / `MEXC_API_SECRET`.
    - No `data/EMERGENCY_STOP` file present.
  - Behavior:
    - Prints a detailed risk banner.
    - Requires triple interactive confirmation.
    - Uses `TradingEngine(mode="live")` and the same `SignalListener` pipeline.
    - Writes live portfolio to `data/live_positions.json` and trades to `data/live_trades.jsonl`.

### Testing & parser validation

There is a dedicated test corpus and integration suite for the advanced parser under `tests/`.

- Main parser accuracy gate (26 real TR/EN signals, ≥95% pass target):
  - `python run_test_suite.py`
    - Wraps `tests/parser_test_corpus.py` and enforces a 95% pass threshold via exit code.
- Run the corpus directly (useful when modifying `parsers/enhanced_parser.py` or number normalization):
  - `python tests/parser_test_corpus.py`
- Whitelist/fast-path integration & real-signal variations:
  - `python tests/test_parser_whitelist_integration.py`

For quick one-off sanity checks, `QUICK_START.md` includes inline commands to:
- Verify trading mode:
  - `python -c "from config.trading_config import TRADING_MODE; print(f'Mode: {TRADING_MODE}')"`
- Smoke-test the simple Telegram parser:
  - `python -c "from telegram.parser import parse_message; result = parse_message({'text': '🟢 LONG\\n💲 BTCUSDT\\n📈 Entry: 50000\\n🎯 Target: 52000\\n🛑 Stop Loss: 48000', 'timestamp': '2025-01-01T00:00:00', 'source': 'test'}); print('✅ Parser works!' if result else '❌ Parser failed')"`

## Architecture overview

### High-level system responsibilities

At a high level this repo implements three related but partially overlapping flows:

1. **Legacy backtest-only flow** (driven by `main.py`, `telegram/collector.py`, `telegram/parser.py`, `trading/backtester.py`):
   - Collect raw Telegram messages → `data/signals_raw.jsonl`.
   - Parse them into structured signals → `data/signals_parsed.jsonl`.
   - Run batch backtests against exchange OHLCV data → `data/backtest_results.csv`.

2. **Unified trading engine flow** (backtest/paper/live capable) built around `trading/trading_engine.py` and `trading/portfolio.py`.

3. **Advanced parser pipeline** for high-accuracy parsing and adaptive whitelisting, centered on `parsers/enhanced_parser.py` and `tests/`.

The documentation in `README.md`, `TRADING_PIPELINE_README.md`, `QUICK_START.md`, `SETUP_GUIDE.md`, and `IMPLEMENTATION_SUMMARY.md` together describe these flows; this section focuses on how the code is actually wired.

### Telegram ingestion layer

There are two main ingestion strategies, both using Telethon but serving different flows.

1. **File-based collector** — `telegram/collector.py` + `main.py`:
   - `telegram.collector.run_collector()` connects using `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`, and `TELEGRAM_CHANNELS` from `utils.config`.
   - For each `NewMessage` in the configured channels, writes a compact JSON object `{source, ts, text}` to `data/signals_raw.jsonl` using an asyncio lock and explicit `fsync` to avoid partial writes.
   - `main.py` orchestrates:
     - `run_collector()` (async listener),
     - a periodic `parser_worker()` (every 5 seconds calling `telegram.parser.run_parser()`),
     - and a basic `trading.paper_trader.run_paper()` engine.

2. **Real-time signal listener** — `telegram/signal_listener.py` + `run_paper_trading.py` / `run_live_trading.py`:
   - `SignalListener` owns its own Telethon client and channel list driven by `SignalConfig.CHANNELS` in `config/trading_config.py`.
   - It uses the simpler `telegram.parser.parse_message()` (via `parse_raw_message`) to turn each incoming `Message` into a minimal signal dict, then converts that into a `trading.trading_engine.Signal` and enqueues it on the engine.
   - Maintains a small in-memory dedupe window keyed on symbol/side/timestamp to avoid acting twice on near-duplicate posts.
   - Provides both `listen()` (continuous streaming) and `fetch_recent_signals(limit=N)` (initial warmup from channel history).

The ingestion choice depends on which entrypoint is used: `main.py` uses the file-based collector; the `run_*_trading.py` scripts use `SignalListener`.

### Parsing stack

There are **three parser layers**, each with a distinct purpose:

1. **Simple Telegram parser** — `telegram/parser.py`:
   - Stateless regex-based parsing tuned for a handful of English/Turkish formats (LONG/SHORT with emojis, Turkish "giriş/tp/sl", `#SYMBOL SHORT SETUP`, and compact BUY/SELL lines).
   - Normalizes symbols to `SYMBOLUSDT`, rejects obviously-invalid symbols via a hardcoded blacklist (common words and known bad tickers), and requires an entry price to treat a message as a valid signal.
   - Writes a compact, backtest-friendly JSON schema including `entry_min/entry_max`, `tp`, `sl`, and a short `note` snippet.
   - Used in two places:
     - Batch mode via `run_parser()` over `data/signals_raw.jsonl`.
     - Real-time, via `SignalListener.parse_raw_message()`.

2. **Structured trading parser** — `trading/parser.py` with `SignalParser` + `scripts/parse_signals.py`:
   - More granular extraction focused on:
     - multiple entry ranges,
     - multiple explicit TP targets (with `TP1`, `Target 2`, etc.),
     - richer leverage and SL patterns.
   - `scripts/parse_signals.py` wires this parser into a batch pipeline:
     - loads `data/signals_raw.jsonl`,
     - calls `SignalParser.parse_signal()` on each message,
     - classifies results as complete/incomplete/failed,
     - then writes `data/signals_parsed.jsonl` plus detailed per-channel and per-direction stats.
   - This path is designed for higher-quality datasets and richer analytics than the legacy CSV/JSONL parser.

3. **Enhanced ML-style parser** — `parsers/enhanced_parser.py` + `tests/`:
   - Implements `EnhancedParser` with a `ParsedSignal` dataclass and **confidence scoring + adaptive whitelist**:
     - Handles TR/EN mixed messages, comma/"k"/"bin" number formats, percentage TP sequences, etc., via `parsers.number_normalizer`.
     - Validates symbols via `utils.binance_validator.is_valid_symbol` and an extensive blacklist to filter out generic words and garbage tickers.
     - Maintains a `WhitelistManager` of successful patterns; known structures can skip full parsing via a "fast-path" cache for performance.
   - Thoroughly tested using:
     - `tests/parser_test_corpus.py` — 26 curated real-world signals with tolerance-based numeric comparisons and a 95% success target.
     - `tests/test_parser_whitelist_integration.py` — exercises learning and fast-path behavior across repeated and similar patterns.
   - This parser is currently used in **offline evaluation and the older `paper_trading_bot.py`**, and is not yet wired into the `SignalListener` → `TradingEngine` path.

When changing parsing behavior, be aware of which layer you are touching and how it feeds into tests or runtime:
- `telegram/parser.py` changes affect both batch parsing and the real-time engine.
- `parsers/enhanced_parser.py` changes must keep the test corpus and whitelist integration suite green.

### Trading engine & portfolio

The unified trading flow is built around `trading/trading_engine.py` and `trading/portfolio.py`, configured via `config/trading_config.py`.

- `TradingEngine` responsibilities:
  - Owns a `mode` (`backtest`, `paper`, or `live`), a `Portfolio` (except in pure backtest mode), and a `BinanceClient` for live price data.
  - Maintains an on-disk signal queue (`data/signal_queue.jsonl`) so pending signals survive restarts.
  - For each `Signal` (symbol, side, entry/TP/SL, timestamp, source):
    - Validates that there is no existing open position for the symbol.
    - Enforces `RiskConfig.MAX_CONCURRENT_TRADES`.
    - Calculates position size from equity and `RiskConfig.MAX_POSITION_SIZE_PCT`, respecting `MIN_POSITION_SIZE_USDT`.
    - Applies paper-trading fees and slippage (`PaperConfig`) in paper mode.
    - Opens/closes positions via `Portfolio.open_position()` / `Portfolio.close_position()` and logs trades to a JSONL file.
  - Periodically checks TP/SL for all open positions using current prices and closes them with reason `TP` or `SL`.
  - In live mode, additionally consults `LiveConfig` (emergency stop file, confirmation requirements). Actual MEXC order execution is still stubbed out with TODOs; safety scaffolding and configuration validation are implemented.

- `Portfolio` responsibilities (`trading/portfolio.py`):
  - Persists balance, open positions, and closed trade history in JSON format.
  - Computes equity, realized PnL, unrealized PnL, fees, win/loss counts, and win rate.
  - Provides `print_summary()` for human-readable portfolio overviews (used at startup/shutdown of paper and live entrypoints).

The engine and portfolio are used by:
- `run_paper_trading.py` (paper mode) and `run_live_trading.py` (live mode), which handle configuration validation, banners, and graceful shutdown.
- `telegram/signal_listener.py`, which is responsible for feeding signals into the engine in real time.

### Configuration model

There are **two main configuration layers**, plus `.env`:

1. **Environment-driven config** — `utils/config.py`:
   - Reads `.env` using `python-dotenv`.
   - Provides basic paths (`DATA_DIR`, `LOG_DIR`), Telegram credentials and channel list, simple risk parameters, and some paper-trading toggles (`PAPER_TRADING_ENABLED`, `PAPER_TRADING_CHANNELS`).
   - Used primarily by older components such as `telegram/collector.py`, `paper_trading_bot.py`, and some debug/backtest scripts.

2. **Typed trading config** — `config/trading_config.py`:
   - Central configuration for the **unified trading engine** and new pipeline.
   - Key pieces:
     - `TRADING_MODE`: top-level mode switch (`backtest`, `paper`, `live`).
     - `RiskConfig`: capital, per-trade allocation, max concurrent trades, daily/weekly loss limits, max drawdown, leverage caps.
     - `PaperConfig` / `LiveConfig`: file locations for portfolios/trade logs, fee and slippage simulation, emergency stop file path, sync intervals.
     - `SignalConfig`: real-time listener settings, symbol validation toggle, duplicate window, queue file path.
     - `AnalyticsConfig` and `LogConfig`: performance metrics and log file organization.
   - `ensure_directories()` and `validate_config()` centralize directory creation and safety checks; both paper and live entrypoints call these early.

3. **Environment variables (.env):
   - Provide secrets and user-specific settings referenced across both config layers, including:
     - Telegram API credentials and phone number.
     - Channel lists (string-based `TELEGRAM_CHANNELS` and optional numeric `PAPER_TRADING_CHANNELS`).
     - Exchange selection and risk defaults.
   - Sample configuration and full variable list are documented in `README.md` and `SETUP_GUIDE.md`.

### Data & logs layout

The core data and log files that other tools and docs assume are:

- `data/signals_raw.jsonl` — append-only raw Telegram messages from `telegram/collector.py`.
- `data/signals_parsed.jsonl` — structured signals from advanced parsers (`telegram/parser.py` or `scripts/parse_signals.py`).
- `data/backtest_results.csv` — backtest export from `trading/backtester.py` / `main.py --mode backtest`.
- `data/paper_portfolio.json` / `data/live_positions.json` — portfolio state for paper/live trading.
- `data/paper_trades.jsonl` / `data/live_trades.jsonl` — trade history streams.
- `data/EMERGENCY_STOP` — presence of this file halts live trading (checked by `TradingEngine` and `run_live_trading.py`).
- `logs/` — multiple log streams (trading, orders, risk, errors) as configured in `LogConfig` and used by `utils.logger`.

Many of the markdown guides (especially `TRADING_PIPELINE_README.md`, `QUICK_START.md`, `QUICK_REFERENCE.md`, and `DEPLOYMENT*.md`) assume these paths and are written to be used alongside the commands listed earlier.

## Notes for future Warp usage in this repo

- There are **multiple overlapping parsing and trading implementations** (legacy vs new). Before changing behavior or wiring, identify which pipeline a change targets:
  - Simple collector/parser/backtester flow (`main.py`, `telegram/collector.py`, `telegram/parser.py`, `trading/backtester.py`).
  - Unified engine + signal listener flow (`run_paper_trading.py`, `run_live_trading.py`, `trading/trading_engine.py`, `trading/portfolio.py`, `telegram/signal_listener.py`).
  - Enhanced parser + whitelist tooling (`parsers/enhanced_parser.py`, `tests/parser_test_corpus.py`, `tests/test_parser_whitelist_integration.py`).
- When modifying the advanced parser stack, keep `run_test_suite.py` passing (≥95% of corpus) and verify whitelist integration tests, as many higher-level reports in this repo assume that target accuracy.
- For user-facing instructions or deployment changes, prefer updating the existing documentation files (`README.md`, `TRADING_PIPELINE_README.md`, `QUICK_START.md`, `SETUP_GUIDE.md`, `DEPLOYMENT*.md`) rather than duplicating their content here.
