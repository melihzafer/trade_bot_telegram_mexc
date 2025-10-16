from parsers.enhanced_parser import EnhancedParser

parser = EnhancedParser()

# Test case 1: "HEDEF" kelimesi symbol olarak algılanmamalı
test1 = "HEDEF long 85 tp:88-91-94 sl:82 20x"
result1 = parser.parse(test1)
print("Test 1: 'HEDEF' as symbol")
print(f"  Input: {test1}")
print(f"  Symbol: {result1.symbol} (expected: None - HEDEF should be blacklisted)")
print(f"  Side: {result1.side}")
print()

# Test case 2: "Hedef 1:" keyword olarak kullanılmalı (TP için)
test2 = """BTC LONG
Giriş: 85000
Hedef 1: 88000
Hedef 2: 91000
Stop: 82000"""
result2 = parser.parse(test2)
print("Test 2: 'Hedef' as keyword")
print(f"  Symbol: {result2.symbol} (expected: BTCUSDT)")
print(f"  Entries: {result2.entries} (expected: [85000])")
print(f"  TPs: {result2.tps} (expected: [88000, 91000])")
print()

# Test case 3: Real signal with both (from test corpus)
test3 = """📊 YENİ SİNYAL

Coin: #MATIC
Yön: LONG 📈
Giriş: 0,85
Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95
Stop: 0,82
Kaldıraç: 10x"""
result3 = parser.parse(test3)
print("Test 3: Real signal (test #25)")
print(f"  Symbol: {result3.symbol} (expected: MATICUSDT)")
print(f"  Entries: {result3.entries} (expected: [0.85])")
print(f"  TPs: {result3.tps} (expected: [0.88, 0.91, 0.95])")
print()

# Summary
print("="*60)
print("SUMMARY:")
print("="*60)
if result1.symbol is None:
    print("✅ Test 1 PASS: 'HEDEF' correctly blacklisted as symbol")
else:
    print(f"❌ Test 1 FAIL: Got symbol '{result1.symbol}' (expected None)")

if result2.symbol == "BTCUSDT" and result2.tps == [88000.0, 91000.0]:
    print("✅ Test 2 PASS: 'Hedef' correctly used as keyword")
else:
    print(f"❌ Test 2 FAIL: Symbol={result2.symbol}, TPs={result2.tps}")

if result3.symbol == "MATICUSDT" and result3.tps == [0.88, 0.91, 0.95]:
    print("✅ Test 3 PASS: Real signal parsed correctly")
else:
    print(f"❌ Test 3 FAIL: Symbol={result3.symbol}, TPs={result3.tps}")
