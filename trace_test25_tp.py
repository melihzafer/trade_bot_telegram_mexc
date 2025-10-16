import re

text = """📊 YENİ SİNYAL

Coin: #MATIC
Yön: LONG 📈
Giriş: 0,85
Hedef 1: 0,88
Hedef 2: 0,91
Hedef 3: 0,95
Stop: 0,82
Kaldıraç: 10x

Risk/Reward: 1:3 ⚡"""

TP_KEYWORDS = r'(?i)\b(?:tp\d*|take\s*profit|hedef\d*|targets?|sell)\b'

# Find TP keyword
tp_match = re.search(TP_KEYWORDS, text)
if tp_match:
    print(f"TP keyword matched at {tp_match.start()}-{tp_match.end()}: '{tp_match.group()}'")
    
    # Skip colon/whitespace
    remaining = text[tp_match.end():].lstrip(' \t:')
    print(f"\nRemaining (first 150 chars):\n{remaining[:150]}")
    
    # Find next keyword
    next_keyword_pattern = r'\b(?:sl|stop|zarar|entry|giriş|buy|alım|lev|leverage|kaldıraç)\b'
    next_match = re.search(next_keyword_pattern, remaining, re.IGNORECASE)
    
    if next_match:
        print(f"\nNext keyword at {next_match.start()}: '{next_match.group()}'")
        tp_text = remaining[:next_match.start()]
        print(f"\nTP text:\n{tp_text}")
    else:
        print("\nNo next keyword - taking first 2 lines")
