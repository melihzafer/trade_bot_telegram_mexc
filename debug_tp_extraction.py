from parsers.enhanced_parser import EnhancedParser
import re

parser = EnhancedParser()

# Test #9 in detail
text = "DOGE long giriş 0,125 hedef 0,130 - 0,135 stop 0,120 15x"
print("=" * 60)
print(f"Test #9: {text}")
print("=" * 60)

# Find where TP extraction happens
tp_match = re.search(parser.TP_KEYWORDS, text, re.IGNORECASE)
if tp_match:
    print(f"\nTP keyword found at position {tp_match.start()}-{tp_match.end()}: '{tp_match.group()}'")
    remaining = text[tp_match.end():]
    print(f"Remaining text after keyword: '{remaining}'")
    
    # Find next keyword
    next_kw = re.search(r'\b(?:tp|hedef|target|targets|sell|sl|stop|zarar|lev|leverage|kaldıraç)\b', remaining, re.IGNORECASE)
    if next_kw:
        print(f"Next keyword at {next_kw.start()}-{next_kw.end()}: '{next_kw.group()}'")
        tp_text = remaining[:next_kw.start()]
        print(f"TP text extracted: '{tp_text}'")
    else:
        print("No next keyword found")

result = parser.parse(text)
print(f"\nFinal parsed TPs: {result.tps}")
print(f"Expected TPs: [0.13, 0.135]")
