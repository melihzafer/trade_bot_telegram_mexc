text = "YENİ"
print(f"Original: {text}")
print(f"Lower: {text.lower()}")
print(f"'yeni' == text.lower(): {'yeni' == text.lower()}")
print(f"'yenı' == text.lower(): {'yenı' == text.lower()}")  # with Turkish ı (dotless i)
print(f"'yenİ' == text.lower(): {'yenİ' == text.lower()}")  # with capital İ
print()

# Check each character
for char in text.lower():
    print(f"'{char}' -> Unicode: U+{ord(char):04X}")
