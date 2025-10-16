from parsers.number_normalizer import parse_tp_sequence

# Test from test #16
tp_text = "88-91-94"
entry_price = None  # No entry detected yet in test #16

print(f"TP text: '{tp_text}'")
print(f"Entry price: {entry_price}")
print()

tps = parse_tp_sequence(tp_text, entry_price)
print(f"Result: {tps}")
