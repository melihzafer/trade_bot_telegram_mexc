text = "SİNYAL"
print(f"Original: {text}")
print(f"Lower: {text.lower()}")
print(f"Characters:")
for char in text.lower():
    print(f"  '{char}' -> U+{ord(char):04X}")
