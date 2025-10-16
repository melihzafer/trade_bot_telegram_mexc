import re
from parsers.number_normalizer import normalize_number_list

TP_KEYWORDS = r'(?i)\b(?:tp\d*|take\s*profit|hedef\d*|targets?|sell)\b'

text = "LTC long 85 tp:88-91-94 sl:82 20x"
print(f"Text: {text}")
print()

# Find TP
tp_match = re.search(TP_KEYWORDS, text)
if tp_match:
    print(f"TP keyword matched at {tp_match.start()}-{tp_match.end()}: '{tp_match.group()}'")
    
    # Original remaining (with colon)
    remaining_original = text[tp_match.end():]
    print(f"Remaining (original): '{remaining_original}'")
    
    # After lstrip
    remaining_stripped = text[tp_match.end():].lstrip(' \t:')
    print(f"Remaining (stripped): '{remaining_stripped}'")
    
    # Find next keyword
    next_keyword_pattern = r'\b(?:sl|stop|zarar|entry|giriş|buy|alım|lev|leverage|kaldıraç)\b'
    next_match = re.search(next_keyword_pattern, remaining_stripped)
    if next_match:
        print(f"Next keyword at {next_match.start()}-{next_match.end()}: '{next_match.group()}'")
        tp_text = remaining_stripped[:next_match.start()]
        print(f"TP text: '{tp_text}'")
        
        # Normalize
        numbers = normalize_number_list(tp_text)
        print(f"Numbers: {numbers}")
    else:
        print("No next keyword found")
