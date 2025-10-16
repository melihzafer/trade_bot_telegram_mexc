from parsers.enhanced_parser import EnhancedParser

text = """📊 YENİ SİNYAL

Coin: #MATIC
Yön: LONG 📈
Giriş: 0,85
Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95
Stop: 0,82
Kaldıraç: 10x

Risk/Reward: 1:3 ⚡"""

parser = EnhancedParser()
result = parser.parse(text)

print(f"Symbol: {result.symbol} (expected: MATICUSDT)")
print(f"Entries: {result.entries} (expected: [0.85])")
print(f"TPs: {result.tps} (expected: [0.88, 0.91, 0.95])")
print()
print("Parsing notes:")
for note in result.parsing_notes:
    print(f"  {note}")
