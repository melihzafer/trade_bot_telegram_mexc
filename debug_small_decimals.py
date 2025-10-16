from parsers.enhanced_parser import EnhancedParser
from parsers.number_normalizer import normalize_number_list
import re

# Test case: Small decimals (0.65, 0.70, 0.75, 0.60)
text = "XRP alım 0.65 hedef 0.70-0.75 zarar durdur 0.60"

print("Text:", text)
print()

# Test if number normalizer can handle small decimals
print("=== NUMBER NORMALIZER TEST ===")
test_strings = [
    "0.65",
    " 0.65 ",
    "alım 0.65 hedef",
    "hedef 0.70-0.75 zarar",
    "zarar durdur 0.60",
]

for s in test_strings:
    result = normalize_number_list(s)
    print(f"normalize_number_list('{s}') = {result}")

print()

# Test entry extraction
print("=== ENTRY EXTRACTION TEST ===")
ENTRY_KEYWORDS = r'(?i)\b(?:entry|giriş|buy|alım|buying)\b'
match = re.search(ENTRY_KEYWORDS, text, re.IGNORECASE)
if match:
    print(f"Entry keyword found at position {match.start()}-{match.end()}: '{match.group()}'")
    start_pos = match.end()
    remaining = text[start_pos:]
    print(f"Remaining text: '{remaining}'")
    
    next_keyword_pattern = r'\b(?:tp|hedef|target|sl|stop|zarar|lev|leverage|kaldıraç)\b'
    next_match = re.search(next_keyword_pattern, remaining, re.IGNORECASE)
    if next_match:
        entry_text = remaining[:next_match.start()]
        print(f"Entry text (until next keyword): '{entry_text}'")
        numbers = normalize_number_list(entry_text)
        print(f"Extracted numbers: {numbers}")

print()

# Test full parser
print("=== FULL PARSER TEST ===")
parser = EnhancedParser()
result = parser.parse(text)
print("Parsed result:")
print(f"  Symbol: {result.symbol}")
print(f"  Side: {result.side}")
print(f"  Entries: {result.entries}")
print(f"  TPs: {result.take_profits}")
print(f"  SL: {result.stop_loss}")
print(f"  Confidence: {result.confidence:.2f}")
print(f"  Notes: {result.parsing_notes}")
