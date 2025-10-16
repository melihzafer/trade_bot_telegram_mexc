from parsers.number_normalizer import normalize_number_list

text = """Giriş: 0,85
Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95
Stop: 0,82
Kaldıraç: 10x

Risk/Reward: 1:3"""

print("Full text test:")
numbers = normalize_number_list(text)
print(f"All numbers: {numbers}")
print()

# Test just TP section
tp_text = """Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95"""
print("TP section only:")
tp_numbers = normalize_number_list(tp_text)
print(f"TP numbers: {tp_numbers}")
