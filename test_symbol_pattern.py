import re

SYMBOL_PATTERN = re.compile(r'\b([A-Z]{2,12})(?:USDT|USD)?\b', re.IGNORECASE)

text = """📊 YENİ SİNYAL

Coin: #MATIC
Yön: LONG 📈"""

matches = SYMBOL_PATTERN.findall(text)
print(f"Symbol matches: {matches}")
