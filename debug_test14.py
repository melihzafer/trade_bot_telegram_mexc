import re

# Current pattern
next_keyword_pattern = r'\b(?:tp\d*|hedef\d*|target\s*\d*|targets|sell|sl|stop|zarar|lev|leverage|kaldıraç)\b'

text = "entry 5.8-6.0 take profit 6.5 stop loss 5.5 lev 12x"

# Find where "entry" ends
entry_match = re.search(r'entry', text, re.IGNORECASE)
if entry_match:
    remaining = text[entry_match.end():]
    print(f"Remaining after 'entry': '{remaining}'")
    
    # Find next keyword
    next_match = re.search(next_keyword_pattern, remaining, re.IGNORECASE)
    if next_match:
        print(f"Next keyword found at position {next_match.start()}: '{next_match.group()}'")
        entry_text = remaining[:next_match.start()]
        print(f"Entry text: '{entry_text}'")
    else:
        print("No next keyword found")
