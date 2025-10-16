"""Quick debug - Check why TR keywords not working"""
from parsers.enhanced_parser import EnhancedParser
import re

parser = EnhancedParser()

# Test Turkish keyword matching
text = "XRP alım 0.65 hedef 0.70-0.75 zarar durdur 0.60"

print("Text:", text)
print("\nKeyword patterns:")
print(f"ENTRY_KEYWORDS: {parser.ENTRY_KEYWORDS}")
print(f"TP_KEYWORDS: {parser.TP_KEYWORDS}")
print(f"SL_KEYWORDS: {parser.SL_KEYWORDS}")

print("\nPattern matches:")
print("Entry match:", re.search(parser.ENTRY_KEYWORDS, text, re.IGNORECASE))
print("TP match:", re.search(parser.TP_KEYWORDS, text, re.IGNORECASE))
print("SL match:", re.search(parser.SL_KEYWORDS, text, re.IGNORECASE))

print("\n" + "="*60)
result = parser.parse(text)
print("\nParsed result:")
print(f"Symbol: {result.symbol}")
print(f"Side: {result.side}")
print(f"Entries: {result.entries}")
print(f"TPs: {result.tps}")
print(f"SL: {result.sl}")
print(f"Confidence: {result.confidence}")
print("\nNotes:")
for note in result.parsing_notes:
    print(f"  - {note}")
