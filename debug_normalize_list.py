import re
from parsers.number_normalizer import normalize_number

text = "giriş 0,125 hedef 0,130 - 0,135"
pattern = r'\b\d+(?:[.,]\d+)?(?:\s*(?:k|K|kilo|bin|BIN))?\b'

matches = re.findall(pattern, text, re.IGNORECASE)
print(f"Text: {text}")
print(f"Regex matches: {matches}")
print()

comma_thousands_pattern = r'\d{1,3},\d{3}(?:\s*[-–—]\s*\d{1,3},\d{3})+'
has_comma_thousands = bool(re.search(comma_thousands_pattern, text))
print(f"Has comma thousands: {has_comma_thousands}")
print()

normalized = []
for match in matches:
    print(f"\nProcessing match: '{match}'")
    print(f"  Length: {len(match.strip())}")
    print(f"  Skip check (len<=2 and no k/bin): {len(match.strip()) <= 2 and not re.search(r'k|bin|kilo', match, re.IGNORECASE)}")
    
    # Skip single/double digits without k/bin suffix (likely labels like tp1, tp2)
    if len(match.strip()) <= 2 and not re.search(r'k|bin|kilo', match, re.IGNORECASE):
        print(f"  SKIPPED (too short)")
        continue
    
    # If we detected comma thousands pattern, pre-process to remove commas
    processed_match = match
    if has_comma_thousands and ',' in match and 'k' not in match.lower() and 'bin' not in match.lower():
        processed_match = match.replace(',', '')
        print(f"  Processed (removed comma): '{processed_match}'")
    
    value = normalize_number(processed_match)
    print(f"  normalize_number('{processed_match}') = {value}")
    
    if value is not None and value >= 0.000001:
        normalized.append(value)
        print(f"  ADDED: {value}")

print(f"\n\nFinal result: {normalized}")
