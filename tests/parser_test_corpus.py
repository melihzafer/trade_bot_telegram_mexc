"""
Parser Test Corpus - 25+ TR/EN Mixed Real Signals
Target: ≥95% accuracy (24/25 minimum)

Author: OMNI Tech Solutions
Created: October 2025
"""

from typing import Dict, List, Optional
from parsers.enhanced_parser import EnhancedParser


# Test corpus - Real signals from Telegram channels
TEST_SIGNALS = [
    # 1. Turkish - Classic format
    {
        "id": 1,
        "input": "#btc long entry: 112.191 tp: 113k-114k-115k sl 109500 lev 10x",
        "expected": {
            "symbol": "BTCUSDT",
            "side": "long",
            "entries": [112191.0],
            "tps": [113000.0, 114000.0, 115000.0],
            "sl": 109500.0,
            "leverage_x": 10,
            "confidence": 1.0
        }
    },
    
    # 2. Turkish - Multi-line format with "bin"
    {
        "id": 2,
        "input": """BTCUSDT SHORT
Entry 112 bin
TP1 111k, TP2 110k
STOP 113200
kaldıraç 5x""",
        "expected": {
            "symbol": "BTCUSDT",
            "side": "short",
            "entries": [112000.0],
            "tps": [111000.0, 110000.0],
            "sl": 113200.0,
            "leverage_x": 5,
            "confidence": 1.0
        }
    },
    
    # 3. English - Relative TP sequence
    {
        "id": 3,
        "input": "eth long 3500 tp: 1-2-3 sl 3400 leverage 20x",
        "expected": {
            "symbol": "ETHUSDT",
            "side": "long",
            "entries": [3500.0],
            "tps": [3535.0, 3570.0, 3605.0],  # +1%, +2%, +3%
            "sl": 3400.0,
            "leverage_x": 20,
            "confidence": 1.0
        }
    },
    
    # 4. Turkish - Comma decimal format
    {
        "id": 4,
        "input": "SOL LONG giriş 112,5k hedef 114,2k stop 110k kaldıraç 15x",
        "expected": {
            "symbol": "SOLUSDT",
            "side": "long",
            "entries": [112500.0],
            "tps": [114200.0],
            "sl": 110000.0,
            "leverage_x": 15,
            "confidence": 1.0
        }
    },
    
    # 5. English - Multiple entries
    {
        "id": 5,
        "input": "AVAX/USDT LONG\nEntry: 25.5 - 26.0\nTP: 27k - 28k - 29k\nSL: 24.5\nLeverage: 10x",
        "expected": {
            "symbol": "AVAXUSDT",
            "side": "long",
            "entries": [25.5, 26.0],
            "tps": [27000.0, 28000.0, 29000.0],
            "sl": 24.5,
            "leverage_x": 10,
            "confidence": 1.0
        }
    },
    
    # 6. Turkish - No leverage (spot)
    {
        "id": 6,
        "input": "XRP alım 0.65 hedef 0.70-0.75 zarar durdur 0.60",
        "expected": {
            "symbol": "XRPUSDT",
            "side": "long",
            "entries": [0.65],
            "tps": [0.70, 0.75],
            "sl": 0.60,
            "leverage_x": None,
            "confidence": 1.0
        }
    },
    
    # 7. Mixed - Hashtag symbol
    {
        "id": 7,
        "input": "#LINK long entry 15.2 tp1 15.8 tp2 16.5 sl 14.8 lev 12x",
        "expected": {
            "symbol": "LINKUSDT",
            "side": "long",
            "entries": [15.2],
            "tps": [15.8, 16.5],
            "sl": 14.8,
            "leverage_x": 12,
            "confidence": 1.0
        }
    },
    
    # 8. English - Short with URL (should be cleaned)
    {
        "id": 8,
        "input": "BNB SHORT 🔴\nEntry: 312\nTP: 305-300-295\nSL: 320\n25x\nhttp://t.me/channel",
        "expected": {
            "symbol": "BNBUSDT",
            "side": "short",
            "entries": [312.0],
            "tps": [305.0, 300.0, 295.0],
            "sl": 320.0,
            "leverage_x": 25,
            "confidence": 1.0
        }
    },
    
    # 9. Turkish - Large numbers with comma thousands
    {
        "id": 9,
        "input": "DOGE long giriş 0,125 hedef 0,130 - 0,135 stop 0,120 15x",
        "expected": {
            "symbol": "DOGEUSDT",
            "side": "long",
            "entries": [0.125],
            "tps": [0.130, 0.135],
            "sl": 0.120,
            "leverage_x": 15,
            "confidence": 1.0
        }
    },
    
    # 10. English - Minimal info (low confidence)
    {
        "id": 10,
        "input": "ADA buy 0.45 target 0.50",
        "expected": {
            "symbol": "ADAUSDT",
            "side": "long",
            "entries": [0.45],
            "tps": [0.50],
            "sl": None,
            "leverage_x": None,
            "confidence": 0.8  # Missing SL
        }
    },
    
    # 11. Turkish - With emojis
    {
        "id": 11,
        "input": "🚀 TIA LONG 🚀\nGiriş: 8,5k\nHedef: 9k-9,5k-10k\nStop: 8k\nKaldıraç: 20x",
        "expected": {
            "symbol": "TIAUSDT",
            "side": "long",
            "entries": [8500.0],
            "tps": [9000.0, 9500.0, 10000.0],
            "sl": 8000.0,
            "leverage_x": 20,
            "confidence": 1.0
        }
    },
    
    # 12. English - Without symbol prefix
    {
        "id": 12,
        "input": "SUI long entry 1.25 tp 1.35-1.45 sl 1.15 leverage 10x",
        "expected": {
            "symbol": "SUIUSDT",
            "side": "long",
            "entries": [1.25],
            "tps": [1.35, 1.45],
            "sl": 1.15,
            "leverage_x": 10,
            "confidence": 1.0
        }
    },
    
    # 13. Turkish - Colon format
    {
        "id": 13,
        "input": "APT: LONG\nGiriş: 7.2\nTP: 7.5 / 7.8 / 8.0\nSL: 6.9\n15x",
        "expected": {
            "symbol": "APTUSDT",
            "side": "long",
            "entries": [7.2],
            "tps": [7.5, 7.8, 8.0],
            "sl": 6.9,
            "leverage_x": 15,
            "confidence": 1.0
        }
    },
    
    # 14. English - Range entry
    {
        "id": 14,
        "input": "TON long entry 5.8-6.0 take profit 6.5 stop loss 5.5 lev 12x",
        "expected": {
            "symbol": "TONUSDT",
            "side": "long",
            "entries": [5.8, 6.0],
            "tps": [6.5],
            "sl": 5.5,
            "leverage_x": 12,
            "confidence": 1.0
        }
    },
    
    # 15. Turkish - "bin" format with spaces
    {
        "id": 15,
        "input": "FLOKI alım 0.000123 hedef 0.000135 stop 0.000115 10x",
        "expected": {
            "symbol": "FLOKIUSDT",
            "side": "long",
            "entries": [0.000123],
            "tps": [0.000135],
            "sl": 0.000115,
            "leverage_x": 10,
            "confidence": 1.0
        }
    },
    
    # 16. Mixed - Compact format
    {
        "id": 16,
        "input": "LTC long 85 tp:88-91-94 sl:82 20x",
        "expected": {
            "symbol": "LTCUSDT",
            "side": "long",
            "entries": [85.0],
            "tps": [88.0, 91.0, 94.0],
            "sl": 82.0,
            "leverage_x": 20,
            "confidence": 1.0
        }
    },
    
    # 17. Turkish - No SL (risky)
    {
        "id": 17,
        "input": "HBAR long giriş 0.08 hedef 0.085-0.09 kaldıraç 8x",
        "expected": {
            "symbol": "HBARUSDT",
            "side": "long",
            "entries": [0.08],
            "tps": [0.085, 0.09],
            "sl": None,
            "leverage_x": 8,
            "confidence": 0.8  # Missing SL
        }
    },
    
    # 18. English - Short position
    {
        "id": 18,
        "input": "ETH SHORT\nEntry: 2500\nTargets: 2450 / 2400 / 2350\nStop: 2550\n10x",
        "expected": {
            "symbol": "ETHUSDT",
            "side": "short",
            "entries": [2500.0],
            "tps": [2450.0, 2400.0, 2350.0],
            "sl": 2550.0,
            "leverage_x": 10,
            "confidence": 1.0
        }
    },
    
    # 19. Turkish - k and bin mixed
    {
        "id": 19,
        "input": "SOL short 120 bin hedef 115k-110k stop 125k 12x",
        "expected": {
            "symbol": "SOLUSDT",
            "side": "short",
            "entries": [120000.0],
            "tps": [115000.0, 110000.0],
            "sl": 125000.0,
            "leverage_x": 12,
            "confidence": 1.0
        }
    },
    
    # 20. English - Spot trade (no leverage)
    {
        "id": 20,
        "input": "UNI buy 6.5 sell 7.2 stop 6.0",
        "expected": {
            "symbol": "UNIUSDT",
            "side": "long",
            "entries": [6.5],
            "tps": [7.2],
            "sl": 6.0,
            "leverage_x": None,
            "confidence": 1.0
        }
    },
    
    # 21. Low quality - Should be rejected
    {
        "id": 21,
        "input": "sol pump incoming 🚀🚀🚀",
        "expected": {
            "symbol": "SOLUSDT",
            "side": "long",
            "entries": [],
            "tps": [],
            "sl": None,
            "leverage_x": None,
            "confidence": 0.4,  # Should be rejected (< 0.6)
            "should_reject": True
        }
    },
    
    # 22. Garbage - Should be rejected
    {
        "id": 22,
        "input": "join our vip group for premium signals",
        "expected": {
            "should_reject": True,  # Can't parse meaningful signal
            "confidence": 0.4
        }
    },
    
    # 23. Turkish - Percentage format
    {
        "id": 23,
        "input": "AVAX LONG\nEntry: 35.5\nTP: %5-%10-%15\nSL: 33.8\n18x",
        "expected": {
            "symbol": "AVAXUSDT",
            "side": "long",
            "entries": [35.5],
            "tps": [37.275, 39.05, 40.825],  # +5%, +10%, +15%
            "sl": 33.8,
            "leverage_x": 18,
            "confidence": 1.0
        }
    },
    
    # 24. English - Multiple TP formats
    {
        "id": 24,
        "input": """BTC LONG SETUP
Entry Zone: 42000-42500
TP1: 43k ✅
TP2: 44k 🎯
TP3: 45k 🚀
Stop Loss: 41000
Leverage: 5x""",
        "expected": {
            "symbol": "BTCUSDT",
            "side": "long",
            "entries": [42000.0, 42500.0],
            "tps": [43000.0, 44000.0, 45000.0],
            "sl": 41000.0,
            "leverage_x": 5,
            "confidence": 1.0
        }
    },
    
    # 25. Turkish - Real channel format
    {
        "id": 25,
        "input": """📊 YENİ SİNYAL

Coin: #MATIC
Yön: LONG 📈
Giriş: 0,85
Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95
Stop: 0,82
Kaldıraç: 10x

Risk/Reward: 1:3 ⚡""",
        "expected": {
            "symbol": "MATICUSDT",
            "side": "long",
            "entries": [0.85],
            "tps": [0.88, 0.91, 0.95],
            "sl": 0.82,
            "leverage_x": 10,
            "confidence": 1.0
        }
    },
    
    # 26. Edge case - Very small numbers
    {
        "id": 26,
        "input": "PEPE long 0.00001234 tp 0.00001350 sl 0.00001100 15x",
        "expected": {
            "symbol": "PEPEUSDT",
            "side": "long",
            "entries": [0.00001234],
            "tps": [0.00001350],
            "sl": 0.00001100,
            "leverage_x": 15,
            "confidence": 1.0
        }
    },
]


def compare_float(actual: float, expected: float, tolerance: float = 0.01) -> bool:
    """Compare floats with tolerance."""
    if actual is None or expected is None:
        return actual == expected
    return abs(actual - expected) / max(abs(expected), 0.0001) < tolerance


def compare_list(actual: List[float], expected: List[float], tolerance: float = 0.01) -> bool:
    """Compare lists of floats with tolerance."""
    if len(actual) != len(expected):
        return False
    return all(compare_float(a, e, tolerance) for a, e in zip(actual, expected))


def run_tests():
    """Run all test cases and report results."""
    parser = EnhancedParser()
    
    print("🧪 PARSER TEST CORPUS - 26 Real Signals\n")
    print("=" * 80)
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for test in TEST_SIGNALS:
        test_id = test["id"]
        input_text = test["input"]
        expected = test["expected"]
        
        # Parse signal
        result = parser.parse(input_text)
        
        # Check if should be rejected
        if expected.get("should_reject"):
            if result.confidence < 0.6 or not result.symbol:
                passed += 1
                status = "✅ PASS"
                reason = "Correctly rejected low-quality signal"
            else:
                failed += 1
                status = "❌ FAIL"
                reason = f"Should reject but got confidence {result.confidence:.2f}"
                failed_tests.append((test_id, input_text[:50], reason))
        else:
            # Normal validation
            checks = []
            
            # Symbol
            if expected.get("symbol"):
                checks.append(("Symbol", result.symbol == expected["symbol"], 
                             f"{result.symbol} vs {expected['symbol']}"))
            
            # Side
            if expected.get("side"):
                checks.append(("Side", result.side == expected["side"],
                             f"{result.side} vs {expected['side']}"))
            
            # Entries
            if expected.get("entries"):
                match = compare_list(result.entries, expected["entries"])
                checks.append(("Entries", match,
                             f"{result.entries} vs {expected['entries']}"))
            
            # TPs
            if expected.get("tps"):
                match = compare_list(result.tps, expected["tps"])
                checks.append(("TPs", match,
                             f"{result.tps} vs {expected['tps']}"))
            
            # SL
            if "sl" in expected:
                match = compare_float(result.sl, expected["sl"]) if expected["sl"] else result.sl is None
                checks.append(("SL", match,
                             f"{result.sl} vs {expected['sl']}"))
            
            # Leverage
            if "leverage_x" in expected:
                match = result.leverage_x == expected["leverage_x"]
                checks.append(("Leverage", match,
                             f"{result.leverage_x} vs {expected['leverage_x']}"))
            
            # Confidence
            if expected.get("confidence"):
                match = abs(result.confidence - expected["confidence"]) < 0.1
                checks.append(("Confidence", match,
                             f"{result.confidence:.2f} vs {expected['confidence']:.2f}"))
            
            # Evaluate
            all_passed = all(check[1] for check in checks)
            
            if all_passed:
                passed += 1
                status = "✅ PASS"
                reason = "All checks passed"
            else:
                failed += 1
                status = "❌ FAIL"
                failed_reasons = [f"{name}: {detail}" for name, passed, detail in checks if not passed]
                reason = " | ".join(failed_reasons)
                failed_tests.append((test_id, input_text[:50], reason))
        
        # Print result
        print(f"Test #{test_id:2d}: {status}")
        if status == "❌ FAIL":
            print(f"  Input:  {input_text[:60]}...")
            print(f"  Reason: {reason}")
        
    # Summary
    print("\n" + "=" * 80)
    print(f"\n📊 TEST RESULTS SUMMARY\n")
    print(f"Total Tests:   {len(TEST_SIGNALS)}")
    print(f"✅ Passed:     {passed} ({passed/len(TEST_SIGNALS)*100:.1f}%)")
    print(f"❌ Failed:     {failed} ({failed/len(TEST_SIGNALS)*100:.1f}%)")
    
    # Target check
    target = len(TEST_SIGNALS) * 0.95
    if passed >= target:
        print(f"\n🎉 SUCCESS! Reached ≥95% target ({passed}/{len(TEST_SIGNALS)})")
    else:
        print(f"\n⚠️  BELOW TARGET! Need {int(target)} but got {passed}")
    
    # Failed tests detail
    if failed_tests:
        print(f"\n❌ FAILED TESTS DETAIL:\n")
        for test_id, input_text, reason in failed_tests:
            print(f"  #{test_id}: {input_text}...")
            print(f"    → {reason}\n")
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_tests()
    
    # Exit code for CI/CD
    exit(0 if passed >= len(TEST_SIGNALS) * 0.95 else 1)
