import re
from parsers.number_normalizer import normalize_number_list

text = """Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95"""

print(f"Text:\n{text}\n")

# Test label pattern
label_pattern = r'\b(?:tp|hedef|target|sl|stop)\s*(\d{1,2})\s*:?'
label_numbers = set(re.findall(label_pattern, text, re.IGNORECASE))
print(f"Label numbers detected: {label_numbers}")
print()

# Test normalize
numbers = normalize_number_list(text)
print(f"Normalized numbers: {numbers}")
