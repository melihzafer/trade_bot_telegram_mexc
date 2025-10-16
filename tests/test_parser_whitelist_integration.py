"""
Integration Test: Parser with Adaptive Whitelist

Tests the complete parser workflow with whitelist fast-path.
"""

import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent))

from parsers.enhanced_parser import EnhancedParser


def test_parser_whitelist_integration():
    """Test parser with whitelist fast-path optimization."""
    print("\n" + "=" * 70)
    print("🧪 PARSER + WHITELIST INTEGRATION TEST")
    print("=" * 70)
    
    parser = EnhancedParser()
    
    # Test signal (will be learned and cached)
    test_signal = """
    BTCUSDT LONG
    Entry: 50000
    TP1: 52000
    TP2: 55000
    TP3: 58000
    SL: 48000
    Leverage: 10x
    """
    
    print("\n--- First Parse (Full Validation) ---")
    start = time.perf_counter()
    result1 = parser.parse(test_signal)
    time1 = (time.perf_counter() - start) * 1000
    
    print(f"Symbol: {result1.symbol}")
    print(f"Side: {result1.side}")
    print(f"Entries: {result1.entries}")
    print(f"TPs: {result1.tps}")
    print(f"SL: {result1.sl}")
    print(f"Leverage: {result1.leverage_x}x")
    print(f"Confidence: {result1.confidence:.2f}")
    print(f"Notes: {result1.parsing_notes}")
    print(f"Parse time: {time1:.2f}ms")
    
    # Parse AGAIN - should hit whitelist after building confidence
    print("\n--- Second Parse (Should Learn) ---")
    result2 = parser.parse(test_signal)
    print(f"Confidence: {result2.confidence:.2f}")
    
    print("\n--- Third Parse (Should Learn More) ---")
    result3 = parser.parse(test_signal)
    print(f"Confidence: {result3.confidence:.2f}")
    
    # Fourth parse should hit whitelist fast-path
    print("\n--- Fourth Parse (Fast Path!) ---")
    start = time.perf_counter()
    result4 = parser.parse(test_signal)
    time4 = (time.perf_counter() - start) * 1000
    
    print(f"Symbol: {result4.symbol}")
    print(f"Confidence: {result4.confidence:.2f}")
    print(f"Notes: {result4.parsing_notes}")
    print(f"Parse time: {time4:.2f}ms")
    print(f"Speedup: {time1/time4:.1f}x faster")
    
    # Test similar pattern (different numbers)
    print("\n--- Similar Pattern (Different Numbers) ---")
    similar_signal = """
    BTCUSDT LONG
    Entry: 51000
    TP1: 53000
    TP2: 56000
    TP3: 59000
    SL: 49000
    Leverage: 10x
    """
    
    start = time.perf_counter()
    result5 = parser.parse(similar_signal)
    time5 = (time.perf_counter() - start) * 1000
    
    print(f"Symbol: {result5.symbol}")
    print(f"Confidence: {result5.confidence:.2f}")
    print(f"Parse time: {time5:.2f}ms")
    
    if "Fast-path" in str(result5.parsing_notes):
        print("✅ Similar pattern matched! (structural similarity)")
    else:
        print("⚠️ Similar pattern missed (will learn separately)")
    
    # Print statistics
    print("\n--- Parser Statistics ---")
    stats = parser.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Validate
    assert result1.symbol == "BTCUSDT", "Symbol should be extracted"
    assert result1.side == "long", "Side should be long"
    assert len(result1.tps) >= 3, "Should have multiple TPs"
    assert result4.confidence >= 0.7, "Whitelist entry should have high confidence"
    
    print("\n✅ Integration test passed!")
    print(f"   Fast-path hit rate: {stats['hit_rate']}")
    print(f"   Whitelist patterns: {stats['whitelist_patterns']}")
    
    return True


def test_parser_real_signals():
    """Test parser with real-world signal variations."""
    print("\n" + "=" * 70)
    print("🧪 REAL-WORLD SIGNAL VARIATIONS")
    print("=" * 70)
    
    parser = EnhancedParser()
    
    signals = [
        # English compact
        "ETHUSDT LONG entry 3000 tp 3100 3200 3300 sl 2900",
        
        # Turkish multiline
        """
        SOLUSDT
        LONG
        Giriş: 100
        Hedef1: 105
        Hedef2: 110
        Hedef3: 115
        Zarar Durdur: 95
        """,
        
        # Mixed language
        "BTC long giriş 50000 target 52000 55000 stop 48000",
        
        # Compact with leverage
        "ETHUSDT LONG 3000 tp 3100 3200 sl 2900 lev 20x",
        
        # Hashtag symbol
        "#AVAX long 35 hedef 38 40 zarar 33",
    ]
    
    for i, signal_text in enumerate(signals, 1):
        print(f"\n--- Signal {i} ---")
        print(f"Text: {signal_text[:50]}...")
        
        # Parse twice to trigger learning
        result1 = parser.parse(signal_text)
        result2 = parser.parse(signal_text)
        result3 = parser.parse(signal_text)  # Should hit whitelist
        
        print(f"Symbol: {result3.symbol}")
        print(f"Side: {result3.side}")
        print(f"Confidence: {result3.confidence:.2f}")
        
        if "Fast-path" in str(result3.parsing_notes):
            print("✨ Fast-path HIT")
        else:
            print("⏳ Full parse (learning)")
    
    # Final stats
    print("\n--- Final Statistics ---")
    stats = parser.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Processed {stats['total_parses']} signals")
    print(f"   Fast-path optimization: {stats['hit_rate']}")
    
    return True


def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("🚀 PARSER + WHITELIST INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Parser Whitelist Integration", test_parser_whitelist_integration),
        ("Real-World Signals", test_parser_real_signals),
    ]
    
    passed = 0
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name}: PASSED")
        except Exception as e:
            print(f"\n❌ {name}: FAILED")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"📊 RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 70)
    
    return passed == len(tests)


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
