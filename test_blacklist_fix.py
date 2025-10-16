"""
Test script to validate BLACKLIST fix for USDT suffix stripping.
Tests that TARGETSUSDT, SOLANAUSDT, ETHEREUMUSDT are correctly filtered.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.enhanced_parser import EnhancedParser

def test_blacklist_filtering():
    """Test that garbage symbols with USDT suffix are filtered."""
    parser = EnhancedParser()
    
    test_cases = [
        {
            "text": "TARGETSUSDT LONG entry 100",
            "expected_symbol": None,
            "reason": "TARGETS in BLACKLIST"
        },
        {
            "text": "SOLANAUSDT LONG entry 50",
            "expected_symbol": None,
            "reason": "SOLANA in BLACKLIST"
        },
        {
            "text": "ETHEREUMUSDT LONG entry 2000",
            "expected_symbol": None,
            "reason": "ETHEREUM in BLACKLIST"
        },
        {
            "text": "EXCHANGEUSDT LONG entry 10",
            "expected_symbol": None,
            "reason": "EXCHANGE in BLACKLIST"
        },
        {
            "text": "CROSSUSDT LONG entry 5",
            "expected_symbol": None,
            "reason": "CROSS in BLACKLIST"
        },
        {
            "text": "LEVERAGEUSDT LONG entry 20",
            "expected_symbol": None,
            "reason": "LEVERAGE in BLACKLIST"
        },
        {
            "text": "SIGNALUSDT LONG entry 1",
            "expected_symbol": None,
            "reason": "SIGNAL in BLACKLIST"
        },
        # Valid symbols (should pass BLACKLIST, may fail Binance validation)
        {
            "text": "BTCUSDT LONG entry 50000",
            "expected_symbol": "BTCUSDT",
            "reason": "BTC is valid"
        },
        {
            "text": "ETHUSDT LONG entry 3000",
            "expected_symbol": "ETHUSDT",
            "reason": "ETH is valid"
        },
        {
            "text": "SOLUSDT LONG entry 100",
            "expected_symbol": "SOLUSDT",
            "reason": "SOL is valid (not SOLANA)"
        },
    ]
    
    print("=" * 70)
    print("Testing BLACKLIST Filtering with USDT Suffix Stripping")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        text = test["text"]
        expected = test["expected_symbol"]
        reason = test["reason"]
        
        signal = parser.parse(text)
        actual = signal.symbol
        
        # Check result
        if actual == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status} Test {i}: {reason}")
        print(f"   Text: {text[:60]}")
        print(f"   Expected: {expected}")
        print(f"   Actual: {actual}")
        
        if actual != expected:
            print(f"   Notes: {signal.parsing_notes}")
        print()
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED! BLACKLIST filtering is working correctly.")
        return True
    else:
        print("❌ SOME TESTS FAILED! BLACKLIST filtering needs fixes.")
        return False


if __name__ == "__main__":
    success = test_blacklist_filtering()
    sys.exit(0 if success else 1)
