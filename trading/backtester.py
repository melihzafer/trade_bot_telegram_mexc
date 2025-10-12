"""
Backtester - tests parsed signals against historical OHLCV data from MEXC.
Determines WIN/LOSS/OPEN outcomes based on TP/SL hits.
"""
import ccxt
import pandas as pd
from pathlib import Path
from typing import Optional

from utils.config import DATA_DIR, DEFAULT_TIMEFRAME, MAX_CANDLES
from utils.logger import info, warn, error
from trading.models import Signal, BacktestResult

PARSED_PATH = DATA_DIR / "signals_parsed.csv"
RESULTS_PATH = DATA_DIR / "backtest_results.csv"


def fetch_ohlcv(
    symbol: str, timeframe: str = DEFAULT_TIMEFRAME, limit: int = MAX_CANDLES
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from MEXC.

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        timeframe: Candle timeframe (e.g., 15m, 1h)
        limit: Number of candles to fetch

    Returns:
        DataFrame with columns: ts, open, high, low, close, volume
    """
    try:
        exchange = ccxt.mexc()
        # Convert BTCUSDT -> BTC/USDT for ccxt
        ccxt_symbol = symbol.replace("USDT", "/USDT")

        bars = exchange.fetch_ohlcv(ccxt_symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=["ts", "open", "high", "low", "close", "volume"])
        return df
    except Exception as e:
        error(f"Error fetching OHLCV for {symbol}: {e}")
        return pd.DataFrame()


def evaluate_signal(
    row: pd.Series, df_ohlcv: pd.DataFrame, lookahead: int = 96
) -> str:
    """
    Evaluate a signal against historical candles to determine outcome.

    Args:
        row: Parsed signal row (symbol, side, entry, tp, sl)
        df_ohlcv: Historical OHLCV DataFrame
        lookahead: Number of candles to check forward (96 * 15m = 24h)

    Returns:
        Outcome: "WIN", "LOSS", "OPEN", or "ERROR"
    """
    try:
        # Use entry price from signal, or fallback to last close
        entry = row.get("entry")
        if not entry or pd.isna(entry):
            if len(df_ohlcv) == 0:
                return "ERROR"
            entry = float(df_ohlcv.iloc[-1]["close"])

        tp = row.get("tp")
        sl = row.get("sl")
        side = row["side"]

        # Take lookahead candles
        subset = df_ohlcv.tail(lookahead)
        if len(subset) == 0:
            return "OPEN"

        hit_tp = False
        hit_sl = False

        if side == "BUY":
            # For BUY: TP is above entry, SL is below
            if tp and not pd.isna(tp):
                hit_tp = (subset["high"] >= float(tp)).any()
            if sl and not pd.isna(sl):
                hit_sl = (subset["low"] <= float(sl)).any()
        else:  # SELL
            # For SELL: TP is below entry, SL is above
            if tp and not pd.isna(tp):
                hit_tp = (subset["low"] <= float(tp)).any()
            if sl and not pd.isna(sl):
                hit_sl = (subset["high"] >= float(sl)).any()

        # Determine which hit first
        if hit_tp and hit_sl:
            # Find indices of first hit
            if side == "BUY":
                tp_idx = subset[subset["high"] >= float(tp)].index.min() if hit_tp else None
                sl_idx = subset[subset["low"] <= float(sl)].index.min() if hit_sl else None
            else:
                tp_idx = subset[subset["low"] <= float(tp)].index.min() if hit_tp else None
                sl_idx = subset[subset["high"] >= float(sl)].index.min() if hit_sl else None

            if tp_idx is not None and sl_idx is not None:
                hit_tp = tp_idx < sl_idx
                hit_sl = not hit_tp

        if hit_tp:
            return "WIN"
        if hit_sl:
            return "LOSS"

        return "OPEN"

    except Exception as e:
        error(f"Error evaluating signal: {e}")
        return "ERROR"


def run_backtest():
    """
    Run backtest on all parsed signals.
    Fetches historical data for each symbol and evaluates outcomes.
    """
    if not PARSED_PATH.exists():
        warn(f"Parsed signals file not found: {PARSED_PATH}")
        return

    info(f"📈 Starting backtest from {PARSED_PATH}")

    # Load parsed signals
    df_signals = pd.read_csv(PARSED_PATH)
    results = []

    for idx, row in df_signals.iterrows():
        try:
            symbol = row["symbol"]
            info(f"[{idx + 1}/{len(df_signals)}] Testing {symbol} {row['side']}...")

            # Fetch OHLCV
            df_ohlcv = fetch_ohlcv(symbol)
            if df_ohlcv.empty:
                results.append({**row.to_dict(), "outcome": "ERROR", "error_msg": "No OHLCV data"})
                continue

            # Evaluate signal
            outcome = evaluate_signal(row, df_ohlcv)

            # Store result
            result = {**row.to_dict(), "outcome": outcome}
            results.append(result)

        except Exception as e:
            error(f"Error backtesting signal {idx}: {e}")
            results.append({**row.to_dict(), "outcome": "ERROR", "error_msg": str(e)})

    # Save results to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(RESULTS_PATH, index=False)

    # Summary statistics
    win_count = len(df_results[df_results["outcome"] == "WIN"])
    loss_count = len(df_results[df_results["outcome"] == "LOSS"])
    open_count = len(df_results[df_results["outcome"] == "OPEN"])
    error_count = len(df_results[df_results["outcome"] == "ERROR"])

    info(f"\n{'='*50}")
    info(f"📊 Backtest Results Summary")
    info(f"{'='*50}")
    info(f"Total Signals: {len(df_results)}")
    info(f"✅ Wins: {win_count}")
    info(f"❌ Losses: {loss_count}")
    info(f"⏳ Open: {open_count}")
    info(f"⚠️  Errors: {error_count}")

    if win_count + loss_count > 0:
        win_rate = (win_count / (win_count + loss_count)) * 100
        info(f"📈 Win Rate: {win_rate:.2f}%")

    info(f"💾 Results saved to: {RESULTS_PATH}")
    info(f"{'='*50}\n")


if __name__ == "__main__":
    run_backtest()
