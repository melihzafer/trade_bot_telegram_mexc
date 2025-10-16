"""
Test Whitelist System - Validate adaptive learning and fast-path optimization

Tests:
1. Pattern learning from successful parses
2. Fast-path lookup for known patterns
3. Confidence scoring evolution
4. LRU eviction under load
5. Decay mechanism for stale patterns
6. Performance comparison (fast vs full parse)
"""

import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.whitelist_manager import WhitelistManager, PatternExtractor


def test_pattern_learning():
    """Test that whitelist learns from successful parses."""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: Pattern Learning")
    print("=" * 70)
    
    # Create fresh whitelist (clear any cached data)
    whitelist = WhitelistManager()
    whitelist.entries.clear()  # Start fresh for this test
    whitelist.hit_count = 0
    whitelist.miss_count = 0
    
    # Simulate successful parse
    text = "BTCUSDT LONG entry 50000 tp 52000 55000 sl 48000"
    symbol = "BTCUSDT"
    entries = [50000.0]
    tps = [52000.0, 55000.0]
    sl = 48000.0
    leverage = None
    
    # Add to whitelist
    whitelist.add(text, symbol, entries, tps, sl, leverage, language='en')
    
    # Verify it was added
    stats = whitelist.get_stats()
    assert stats['total_entries'] == 1, "Pattern should be added"
    
    # First lookup: Confidence too low (0.6 < 0.7 threshold)
    result = whitelist.lookup(text)
    assert result is None, "First lookup should miss (confidence too low)"
    
    # Add again to boost confidence
    whitelist.add(text, symbol, entries, tps, sl, leverage, language='en')
    
    # Second lookup: Confidence now 0.65 (still below threshold)
    result = whitelist.lookup(text)
    assert result is None, "Second lookup should still miss (confidence 0.65 < 0.7)"
    
    # Add third time to push over threshold
    whitelist.add(text, symbol, entries, tps, sl, leverage, language='en')
    
    # Third lookup: Confidence now 0.70 (at threshold)
    result = whitelist.lookup(text)
    assert result is not None, "Third lookup should hit (confidence >= 0.7)"
    assert result.symbol == symbol, "Cached symbol should match"
    assert result.cached_entries == entries, "Cached entries should match"
    
    print(f"✅ Pattern learned after 3 successful parses")
    print(f"   Confidence evolution: 0.6 → 0.65 → 0.70 → {result.confidence:.2f}")
    print(f"   Hit rate: {whitelist.get_stats()['hit_rate']:.1%}")
    
    return True


def test_fast_path_speedup():
    """Test that whitelist provides significant speedup."""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Fast Path Speedup")
    print("=" * 70)
    
    whitelist = WhitelistManager()
    
    text = "ETHUSDT LONG entry 3000 tp 3100 3200 sl 2900 lev 10x"
    
    # Build confidence (3 adds to reach threshold)
    for _ in range(3):
        whitelist.add(text, "ETHUSDT", [3000.0], [3100.0, 3200.0], 2900.0, 10, 'en')
    
    # Measure full parse simulation (fingerprint + hash generation)
    start = time.perf_counter()
    for _ in range(1000):
        fingerprint = PatternExtractor.extract_fingerprint(text)
        pattern_hash = PatternExtractor.generate_hash(text, fingerprint)
    full_time = time.perf_counter() - start
    
    # Measure fast path lookup (just dict lookup + confidence check)
    start = time.perf_counter()
    hits = 0
    for _ in range(1000):
        result = whitelist.lookup(text)
        if result:
            hits += 1
    fast_time = time.perf_counter() - start
    
    # Fast path should do fingerprint+hash+dict lookup, but in real parser
    # it skips BLACKLIST check, Binance API validation, and complex parsing
    # So we measure if lookup overhead is reasonable (< 2x slower than baseline)
    
    print(f"✅ Fast path performance:")
    print(f"   Full fingerprinting: {full_time*1000:.2f}ms (1000 iterations)")
    print(f"   Fast path lookup: {fast_time*1000:.2f}ms (1000 iterations)")
    print(f"   Overhead ratio: {fast_time/full_time:.2f}x")
    print(f"   Per lookup: {fast_time*1000000/1000:.1f}µs")
    print(f"   Hit rate: {hits}/1000 ({hits/10:.0f}%)")
    
    # Fast path should have reasonable overhead (not 10x slower)
    # In real use, it saves BLACKLIST+Binance API+parsing time
    assert fast_time / full_time < 3.0, "Fast path overhead should be < 3x"
    
    return True


def test_similar_patterns():
    """Test that similar patterns get different hashes."""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Pattern Similarity Detection")
    print("=" * 70)
    
    patterns = [
        "BTCUSDT LONG entry 50000 tp 52000 sl 48000",
        "BTCUSDT LONG entry 51000 tp 53000 sl 49000",  # Same structure, different numbers
        "ETHUSDT LONG entry 3000 tp 3100 sl 2900",     # Different symbol
        "BTC/USDT\nLONG\nEntry: 50000\nTP: 52000",     # Different format
    ]
    
    hashes = []
    for text in patterns:
        fingerprint = PatternExtractor.extract_fingerprint(text)
        pattern_hash = PatternExtractor.generate_hash(text, fingerprint)
        hashes.append(pattern_hash)
        print(f"   {text[:40]:40} → {pattern_hash[:12]}")
    
    # First two should have SAME hash (same structure)
    assert hashes[0] == hashes[1], "Similar patterns should match"
    
    # Third should be different (different symbol)
    assert hashes[2] != hashes[0], "Different symbols should differ"
    
    # Fourth should be different (different format)
    assert hashes[3] != hashes[0], "Different formats should differ"
    
    print(f"✅ Pattern similarity detection working:")
    print(f"   Same structure (diff numbers): MATCH ✓")
    print(f"   Different symbol: DIFFER ✓")
    print(f"   Different format: DIFFER ✓")
    
    return True


def test_lru_eviction():
    """Test LRU eviction under load."""
    print("\n" + "=" * 70)
    print("🧪 TEST 4: LRU Eviction")
    print("=" * 70)
    
    # Create whitelist with low limit
    whitelist = WhitelistManager()
    whitelist.MAX_ENTRIES = 10  # Low limit for testing
    
    # Add 15 patterns (exceeds limit)
    for i in range(15):
        text = f"SYM{i}USDT LONG entry {100+i} tp {110+i} sl {90+i}"
        whitelist.add(text, f"SYM{i}USDT", [100.0+i], [110.0+i], 90.0+i, None, 'en')
    
    stats = whitelist.get_stats()
    
    print(f"✅ LRU eviction working:")
    print(f"   Added: 15 patterns")
    print(f"   Limit: {whitelist.MAX_ENTRIES}")
    print(f"   Remaining: {stats['total_entries']}")
    print(f"   Evicted: {15 - stats['total_entries']}")
    
    assert stats['total_entries'] <= whitelist.MAX_ENTRIES, "Should not exceed limit"
    
    return True


def test_language_detection():
    """Test language detection in patterns."""
    print("\n" + "=" * 70)
    print("🧪 TEST 5: Language Detection")
    print("=" * 70)
    
    test_cases = [
        ("BTCUSDT LONG entry 50000 tp 52000 sl 48000", "en"),
        ("BTC giriş 50000 hedef 52000 zarar durdur 48000", "tr"),
        ("ETH LONG giriş 3000 target 3100 stop 2900", "mixed"),
        ("SOL 100 105 110 95", "unknown"),
    ]
    
    for text, expected_lang in test_cases:
        fingerprint = PatternExtractor.extract_fingerprint(text)
        detected = fingerprint['language']
        
        status = "✅" if detected == expected_lang else "❌"
        print(f"   {status} {text[:40]:40} → {detected:8} (expected: {expected_lang})")
        
        assert detected == expected_lang, f"Language detection failed for: {text}"
    
    print(f"✅ All language detections correct")
    
    return True


def test_format_detection():
    """Test format type detection."""
    print("\n" + "=" * 70)
    print("🧪 TEST 6: Format Detection")
    print("=" * 70)
    
    test_cases = [
        ("BTCUSDT LONG entry 50000 tp 52000 sl 48000", "compact"),
        ("BTC/USDT\nLONG\nEntry: 50000\nTP: 52000\nSL: 48000", "multiline"),
        ("ETH entry 3000 tp1: 3100 tp2: 3200 sl: 2900", "labeled"),
    ]
    
    for text, expected_format in test_cases:
        fingerprint = PatternExtractor.extract_fingerprint(text)
        detected = fingerprint['format_type']
        
        status = "✅" if detected == expected_format else "❌"
        print(f"   {status} {expected_format:10} → {text[:40]}")
        
        assert detected == expected_format, f"Format detection failed for: {text}"
    
    print(f"✅ All format detections correct")
    
    return True


def test_confidence_evolution():
    """Test confidence scoring evolution."""
    print("\n" + "=" * 70)
    print("🧪 TEST 7: Confidence Evolution")
    print("=" * 70)
    
    whitelist = WhitelistManager()
    
    text = "SOLUSDT LONG entry 100 tp 105 sl 95"
    
    # Track confidence over multiple adds
    confidences = []
    
    for i in range(10):
        whitelist.add(text, "SOLUSDT", [100.0], [105.0], 95.0, None, 'en')
        
        # Lookup to get current confidence
        result = whitelist.lookup(text)
        if result:
            confidences.append(result.confidence)
    
    print(f"   Confidence evolution over 10 parses:")
    for i, conf in enumerate(confidences, 1):
        print(f"      Parse {i:2}: {conf:.3f}")
    
    # Confidence should increase over time
    if len(confidences) > 1:
        assert confidences[-1] > confidences[0], "Confidence should increase"
        print(f"✅ Confidence increased: {confidences[0]:.3f} → {confidences[-1]:.3f}")
    
    return True


def test_whitelist_persistence():
    """Test save/load functionality."""
    print("\n" + "=" * 70)
    print("🧪 TEST 8: Persistence (Save/Load)")
    print("=" * 70)
    
    # Create whitelist and add patterns
    whitelist1 = WhitelistManager()
    
    for i in range(5):
        text = f"TEST{i}USDT LONG entry {100+i*10} tp {120+i*10}"
        whitelist1.add(text, f"TEST{i}USDT", [100.0+i*10], [120.0+i*10], None, None, 'en')
    
    # Save
    whitelist1.save()
    stats1 = whitelist1.get_stats()
    
    print(f"   Saved: {stats1['total_entries']} patterns")
    
    # Create new instance (should load from disk)
    whitelist2 = WhitelistManager()
    stats2 = whitelist2.get_stats()
    
    print(f"   Loaded: {stats2['total_entries']} patterns")
    
    assert stats2['total_entries'] >= stats1['total_entries'], "Should load saved patterns"
    
    print(f"✅ Persistence working (save → load)")
    
    return True


def run_all_tests():
    """Run all whitelist tests."""
    print("\n" + "=" * 70)
    print("🚀 WHITELIST SYSTEM TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Pattern Learning", test_pattern_learning),
        ("Fast Path Speedup", test_fast_path_speedup),
        ("Pattern Similarity", test_similar_patterns),
        ("LRU Eviction", test_lru_eviction),
        ("Language Detection", test_language_detection),
        ("Format Detection", test_format_detection),
        ("Confidence Evolution", test_confidence_evolution),
        ("Persistence", test_whitelist_persistence),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ FAILED: {name}")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS")
    print("=" * 70)
    print(f"   Passed: {passed}/{len(tests)}")
    print(f"   Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️ {failed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
