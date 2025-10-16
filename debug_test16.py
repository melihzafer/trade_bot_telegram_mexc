from parsers.enhanced_parser import EnhancedParser

parser = EnhancedParser()

text = "LTC long 85 tp:88-91-94 sl:82 20x"
print(f"Input: {text}")
print()

result = parser.parse(text)
print(f"Symbol: {result.symbol}")
print(f"Side: {result.side}")
print(f"Entries: {result.entries}")
print(f"TPs: {result.tps}")
print(f"SL: {result.sl}")
print(f"Leverage: {result.leverage_x}")
print(f"Confidence: {result.confidence}")
print()
print("Parsing notes:")
for note in result.parsing_notes:
    print(f"  - {note}")
