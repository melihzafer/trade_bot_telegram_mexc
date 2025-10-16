from parsers.number_normalizer import normalize_number, normalize_number_list

# Test case from test #9
text = "hedef 0,130 - 0,135"
print(f"Text: '{text}'")
print(f"Result: {normalize_number_list(text)}")
print()

# Test case from test #4
text2 = "hedef 114,2k"
print(f"Text: '{text2}'")
print(f"Result: {normalize_number_list(text2)}")
print()

# Test case from test #17
text3 = "hedef 0.085-0.09"
print(f"Text: '{text3}'")
print(f"Result: {normalize_number_list(text3)}")
print()

# Full signals
print("=" * 50)
full1 = "DOGE long giriş 0,125 hedef 0,130 - 0,135 stop 0,120 15x"
print(f"Full signal: {full1}")
print(f"All numbers: {normalize_number_list(full1)}")
print()

full2 = "SOL LONG giriş 112,5k hedef 114,2k stop 110k kaldıraç 15x"
print(f"Full signal: {full2}")
print(f"All numbers: {normalize_number_list(full2)}")
