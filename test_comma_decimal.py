from parsers.number_normalizer import normalize_number, normalize_number_list

# Test comma decimals
test_cases = [
    ("0,125", 0.125),
    ("0,130", 0.13),
    ("0,135", 0.135),
    ("0,085", 0.085),
    ("112,5k", 112500),
    ("114,2k", 114200),
]

print("=== COMMA DECIMAL TEST ===\n")
for text, expected in test_cases:
    result = normalize_number(text)
    status = "✅" if result == expected else "❌"
    print(f"{status} normalize_number('{text}') = {result} (expected {expected})")

print("\n=== LIST EXTRACTION TEST ===\n")
list_tests = [
    ("giriş 0,125 hedef 0,130 - 0,135", [0.125, 0.13, 0.135]),
    ("hedef 0,130 - 0,135 stop", [0.13, 0.135]),
    ("giriş 112,5k hedef 114,2k", [112500, 114200]),
]

for text, expected in list_tests:
    result = normalize_number_list(text)
    status = "✅" if result == expected else "❌"
    print(f"{status} normalize_number_list('{text}')")
    print(f"   Result:   {result}")
    print(f"   Expected: {expected}")
    print()
