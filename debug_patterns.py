import re

# Test if patterns match with colon
LONG_KEYWORDS = r'(?i)\b(?:long|buy|al|alım|giriş)\b'
TP_KEYWORDS = r'(?i)\b(?:tp\d*|take\s*profit|hedef\d*|targets?|sell)\b'
SL_KEYWORDS = r'(?i)\b(?:sl|stop|stoploss|stop\s*loss|zarar\s*durdur)\b'

text = "LTC long 85 tp:88-91-94 sl:82 20x"

print("Testing patterns:")
print(f"Text: {text}")
print()

# Test LONG pattern
long_match = re.search(LONG_KEYWORDS, text)
if long_match:
    print(f"LONG matched: '{long_match.group()}' at position {long_match.start()}-{long_match.end()}")
    remaining = text[long_match.end():]
    print(f"Remaining: '{remaining}'")
else:
    print("LONG not matched")
print()

# Test TP pattern
tp_match = re.search(TP_KEYWORDS, text)
if tp_match:
    print(f"TP matched: '{tp_match.group()}' at position {tp_match.start()}-{tp_match.end()}")
    remaining = text[tp_match.end():]
    print(f"Remaining: '{remaining}'")
else:
    print("TP not matched")
print()

# Test SL pattern  
sl_match = re.search(SL_KEYWORDS, text)
if sl_match:
    print(f"SL matched: '{sl_match.group()}' at position {sl_match.start()}-{sl_match.end()}")
    remaining = text[sl_match.end():]
    print(f"Remaining: '{remaining}'")
else:
    print("SL not matched")
