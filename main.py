"""
Main orchestrator - coordinates all system components.
Runs Telegram collector, parser, and paper trader concurrently.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram.collector import run_collector
from telegram.parser import run_parser
from trading.paper_trader import run_paper
from utils.logger import info, error, warn
from utils.config import TELEGRAM_CHANNELS


async def parser_worker():
    """
    Periodic parser worker - parses raw messages every 5 seconds.
    In production, this could be event-driven instead.
    """
    while True:
        try:
            run_parser()
        except Exception as e:
            error(f"Parser worker error: {e}")
        await asyncio.sleep(5)


async def main():
    """
    Main entry point - runs all components concurrently.
    """
    info("=" * 70)
    info("🚀 MEXC Multi-Source Trading System - Starting...")
    info("=" * 70)

    # Validate configuration
    if not TELEGRAM_CHANNELS:
        error("❌ No Telegram channels configured. Please set TELEGRAM_CHANNELS in .env")
        error("   Example: TELEGRAM_CHANNELS=@channel1,@channel2,@channel3")
        return

    info(f"📡 Monitoring channels: {', '.join(TELEGRAM_CHANNELS)}")
    info(f"📊 System components:")
    info(f"   1️⃣  Telegram Collector (async)")
    info(f"   2️⃣  Signal Parser (5s interval)")
    info(f"   3️⃣  Paper Trader (live simulation)")
    info("=" * 70)

    try:
        # Run all components concurrently
        await asyncio.gather(
            run_collector(),  # Telegram listener
            parser_worker(),  # Periodic parser
            run_paper(),      # Paper trading engine
        )
    except KeyboardInterrupt:
        info("\n⏹️  Shutting down gracefully...")
    except Exception as e:
        error(f"❌ System error: {e}")
        raise


def run_backtest_only():
    """
    Run backtest mode only (no live components).
    """
    from trading.backtester import run_backtest

    info("=" * 70)
    info("📈 Running Backtest Mode Only")
    info("=" * 70)

    try:
        run_backtest()
    except Exception as e:
        error(f"Backtest error: {e}")
        raise


def run_collector_only():
    """
    Run collector only (for initial message gathering).
    """
    info("=" * 70)
    info("📡 Running Collector Only Mode")
    info("=" * 70)

    try:
        asyncio.run(run_collector())
    except KeyboardInterrupt:
        info("\n⏹️  Collector stopped")
    except Exception as e:
        error(f"Collector error: {e}")
        raise


if __name__ == "__main__":
    # Check command line arguments for mode selection
    import argparse

    parser = argparse.ArgumentParser(description="MEXC Multi-Source Trading System")
    parser.add_argument(
        "--mode",
        choices=["full", "backtest", "collector"],
        default="full",
        help="Execution mode: full (default), backtest, or collector",
    )

    args = parser.parse_args()

    if args.mode == "backtest":
        run_backtest_only()
    elif args.mode == "collector":
        run_collector_only()
    else:
        asyncio.run(main())
