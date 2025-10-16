"""
API Diagnostic Tool - Test which API works better and identify problematic symbols.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent))

from utils.binance_api import BinanceClient
from utils.logger import info, success, warn, error


def load_unique_symbols():
    """Load all unique symbols from parsed signals."""
    parsed_path = Path("data/signals_parsed.jsonl")
    symbols = set()
    
    if not parsed_path.exists():
        error("❌ signals_parsed.jsonl not found!")
        return []
    
    with open(parsed_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                signal = json.loads(line)
                if signal.get('symbol'):
                    symbols.add(signal['symbol'])
    
    return sorted(list(symbols))


def test_symbol_on_binance(client, symbol):
    """
    Test if symbol exists and is tradeable on Binance.
    
    Returns:
        Dict with status and price if available
    """
    try:
        price = client.get_current_price(symbol)
        if price:
            return {
                'status': 'success',
                'price': price,
                'api': 'binance'
            }
        else:
            return {
                'status': 'not_found',
                'error': 'Symbol not found or no price',
                'api': 'binance'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'api': 'binance'
        }


def run_diagnostic():
    """Run comprehensive API diagnostic."""
    print("\n" + "="*80)
    print("🔬 API DIAGNOSTIC TOOL")
    print("="*80)
    
    # Initialize clients
    info("\n📡 Initializing API clients...")
    binance = BinanceClient()
    
    # Test basic connectivity
    print("\n" + "="*80)
    print("1️⃣ CONNECTIVITY TEST")
    print("="*80)
    
    binance_ok = binance.test_connection()
    
    if not binance_ok:
        error("❌ Binance API not accessible! Aborting.")
        return
    
    # Load symbols
    print("\n" + "="*80)
    print("2️⃣ SYMBOL VALIDATION TEST")
    print("="*80)
    
    symbols = load_unique_symbols()
    info(f"\n📚 Found {len(symbols)} unique symbols to test")
    
    # Test each symbol
    results = {
        'success': [],
        'not_found': [],
        'error': []
    }
    
    print("\n🔄 Testing symbols on Binance API...")
    print("   (This may take a few minutes...)\n")
    
    for i, symbol in enumerate(symbols, 1):
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(symbols)} ({i*100//len(symbols)}%)")
        
        result = test_symbol_on_binance(binance, symbol)
        results[result['status']].append({
            'symbol': symbol,
            **result
        })
        
        # Small delay to avoid rate limiting
        time.sleep(0.05)
    
    # Print results
    print("\n" + "="*80)
    print("📊 DIAGNOSTIC RESULTS")
    print("="*80)
    
    success_count = len(results['success'])
    not_found_count = len(results['not_found'])
    error_count = len(results['error'])
    total = len(symbols)
    
    print(f"\n✅ Success:     {success_count}/{total} ({success_count*100//total}%)")
    print(f"❌ Not Found:   {not_found_count}/{total} ({not_found_count*100//total}%)")
    print(f"⚠️  Errors:      {error_count}/{total} ({error_count*100//total}%)")
    
    # Show successful major coins
    if results['success']:
        print("\n" + "-"*80)
        print("✅ WORKING SYMBOLS (Sample - Top 20):")
        print("-"*80)
        for item in results['success'][:20]:
            print(f"   {item['symbol']:<15} ${item['price']:>10,.4f}")
    
    # Show problematic symbols
    if results['not_found']:
        print("\n" + "-"*80)
        print("❌ NOT FOUND ON BINANCE (Garbage/Invalid):")
        print("-"*80)
        for item in results['not_found']:
            print(f"   {item['symbol']:<15} - {item.get('error', 'Not found')}")
    
    if results['error']:
        print("\n" + "-"*80)
        print("⚠️  API ERRORS:")
        print("-"*80)
        for item in results['error'][:10]:  # Show first 10
            print(f"   {item['symbol']:<15} - {item.get('error', 'Unknown error')}")
    
    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    
    if success_count / total > 0.85:
        success(f"\n✅ EXCELLENT! {success_count*100//total}% of symbols work on Binance API!")
        print("   Recommendation: Continue using Binance API")
        print("   Action: Add invalid symbols to parser blacklist")
    elif success_count / total > 0.70:
        info(f"\n⚠️  GOOD - {success_count*100//total}% success rate")
        print("   Recommendation: Use Binance API with error handling")
        print("   Action: Filter out invalid symbols before price collection")
    else:
        warn(f"\n❌ LOW SUCCESS RATE: {success_count*100//total}%")
        print("   Recommendation: Review parser - too many garbage symbols")
        print("   Action: Improve parser regex and blacklist")
    
    # Generate blacklist
    if results['not_found']:
        print("\n" + "-"*80)
        print("📝 PARSER BLACKLIST (Add these to telegram/parser.py):")
        print("-"*80)
        
        # Extract base words from invalid symbols
        invalid_bases = set()
        for item in results['not_found']:
            symbol = item['symbol']
            # Remove USDT suffix
            if symbol.endswith('USDT'):
                base = symbol[:-4]
                invalid_bases.add(base)
        
        print("\nBLACKLIST = {")
        print("    # ... existing entries ...")
        for base in sorted(invalid_bases):
            print(f'    "{base}",')
        print("}")
    
    # Save results to file
    output_file = Path("data/api_diagnostic_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Full results saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    run_diagnostic()
