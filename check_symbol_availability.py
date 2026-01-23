"""
🔍 Check Symbol Availability on Binance
Quick script to verify which symbols are available on Binance.

Usage:
    python check_symbol_availability.py ZETAUSDT BTCUSDT ETHUSDT
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.binance_api import BinanceClient
from utils.logger import info, success, error, warn


def check_symbols(symbols: list):
    """Check if symbols are available on Binance."""
    api = BinanceClient()
    
    info("=" * 70)
    info("🔍 CHECKING SYMBOL AVAILABILITY ON BINANCE")
    info("=" * 70)
    
    results = {}
    
    for symbol in symbols:
        symbol = symbol.upper()
        if not symbol.endswith('USDT'):
            symbol = symbol + 'USDT'
        
        info(f"\nChecking {symbol}...")
        
        price = api.get_current_price(symbol)
        
        if price:
            results[symbol] = True
            success(f"  ✅ Available - Current price: ${price:,.4f}")
        else:
            results[symbol] = False
            error(f"  ❌ Not available on Binance")
    
    # Summary
    info("\n" + "=" * 70)
    info("SUMMARY")
    info("=" * 70)
    
    available = [s for s, avail in results.items() if avail]
    unavailable = [s for s, avail in results.items() if not avail]
    
    if available:
        success(f"\n✅ Available on Binance ({len(available)}):")
        for symbol in available:
            info(f"  • {symbol}")
    
    if unavailable:
        warn(f"\n❌ NOT available on Binance ({len(unavailable)}):")
        for symbol in unavailable:
            info(f"  • {symbol}")
        warn("\nThese symbols will be skipped during backtest.")
        warn("They may be available on MEXC but not on Binance.")
    
    info("\n" + "=" * 70)
    
    return results


def main():
    if len(sys.argv) < 2:
        # Default symbols to check
        symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT",
            "ZETAUSDT", "WUSDT", "SOLUSDT",
            "ADAUSDT", "DOGEUSDT", "XRPUSDT"
        ]
        info("No symbols provided. Checking common symbols...")
    else:
        symbols = sys.argv[1:]
    
    check_symbols(symbols)


if __name__ == "__main__":
    main()
