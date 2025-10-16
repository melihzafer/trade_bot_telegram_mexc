import re

text = "giriş 0,125 hedef 0,130 - 0,135"
pattern = r'\b\d+(?:[.,]\d+)?(?:\s*(?:k|K|kilo|bin|BIN))?\b'

matches = re.findall(pattern, text)
print(f"Text: {text}")
print(f"Pattern: {pattern}")
print(f"Matches: {matches}")
print()

# Test with different patterns
patterns = [
    (r'\b\d+(?:[.,]\d+)?(?:\s*(?:k|K|kilo|bin|BIN))?\b', "Current (with \\b)"),
    (r'\d+(?:[.,]\d+)?(?:\s*(?:k|K|kilo|bin|BIN))?', "Without \\b"),
    (r'(?<!\d)\d+(?:[.,]\d+)?(?:\s*(?:k|K|kilo|bin|BIN))?(?!\d)', "Lookahead/behind"),
]

for pat, desc in patterns:
    matches = re.findall(pat, text)
    print(f"{desc}:")
    print(f"  Matches: {matches}")
