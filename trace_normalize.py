from parsers.number_normalizer import normalize_number_list

text = "88-91-94"
print(f"Text: '{text}'")
numbers = normalize_number_list(text)
print(f"Result: {numbers}")
