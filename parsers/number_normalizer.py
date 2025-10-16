"""
📊 Number Normalizer
Handles TR/EN number formats: 112.191, 112,191, 112k, 112 bin, 112bin → normalized float
"""
import re
from typing import Optional, List


def normalize_number(text: str) -> Optional[float]:
    """
    Normalize various number formats to float.
    
    Supports:
    - 112.191 (US decimal) → 112.191
    - 112,191 (TR decimal) → 112.191
    - 112k, 112 k, 112K → 112000
    - 112bin, 112 bin → 112000
    - 112kilo → 112000
    - 112,5k → 112500
    - 112.5k → 112500
    
    Args:
        text: Raw number string
    
    Returns:
        Normalized float or None if invalid
    """
    if not text:
        return None
    
    # Clean whitespace, single quotes, double quotes
    text = text.strip().replace("'", "").replace('"', "").replace(" ", "")
    
    if not text:
        return None
    
    # Handle k/bin/kilo multiplier
    multiplier = 1.0
    
    # Check for k/K/kilo/bin suffix
    k_pattern = r'(\d+(?:[.,]\d+)?)(k|K|kilo|bin|BIN)$'
    k_match = re.search(k_pattern, text, re.IGNORECASE)
    
    if k_match:
        text = k_match.group(1)  # Extract number part
        multiplier = 1000.0
    
    # Now normalize decimal separator
    # Strategy: If contains both comma and dot, determine format by position
    # If comma comes after dot: US format (1,234.56 - comma=thousands, dot=decimal)
    # If dot comes after comma: EU format (1.234,56 - dot=thousands, comma=decimal)
    # If only comma: Turkish decimal
    # If only dot: US decimal
    
    if ',' in text and '.' in text:
        # Determine format by position
        comma_pos = text.find(',')
        dot_pos = text.find('.')
        
        if dot_pos < comma_pos:
            # European format: 1.234,56 → remove dots, replace comma with dot
            text = text.replace('.', '').replace(',', '.')
        else:
            # US format: 1,234.56 → remove commas
            text = text.replace(',', '')
    elif ',' in text:
        # Turkish decimal: 112,191 → replace comma with dot
        text = text.replace(',', '.')
    # else: US format, keep as-is
    
    # Parse float
    try:
        value = float(text) * multiplier
        return value
    except ValueError:
        return None


def normalize_number_list(text: str) -> List[float]:
    """
    Extract and normalize all numbers from text.
    
    Examples:
    - "113k-114k-115k" → [113000, 114000, 115000]
    - "tp1:114k tp2:116k" → [114000, 116000]
    - "113,500 - 114,000 - 115,000" → [113500, 114000, 115000]
    
    Args:
        text: Raw text with numbers
    
    Returns:
        List of normalized floats
    """
    # Pattern: number with optional k/bin/kilo suffix
    # Avoid matching single digits (like tp1, tp2)
    pattern = r'\b\d+(?:[.,]\d+)?(?:\s*(?:k|K|kilo|bin|BIN))?\b'
    
    # Check if text has repeated comma patterns like "113,500 - 114,000 - 115,000"
    # This indicates thousands separators, not decimals
    # IMPORTANT: Must have exactly 3 digits after comma (not 1 or 2)
    # 0,125 is decimal (2-3 digits but starts with 0)
    # 113,500 is thousands (3 digits, doesn't start with 0)
    comma_thousands_pattern = r'(?<!\d)(?!0,)\d{1,3},\d{3}(?:\s*[-–—]\s*(?!0,)\d{1,3},\d{3})+'
    has_comma_thousands = bool(re.search(comma_thousands_pattern, text))
    
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Build set of label positions to skip (tp1, tp2, hedef1, "Hedef 1:", etc.)
    label_pattern = r'\b(?:tp|hedef|target|sl|stop)\s*(\d{1,2})\s*:?'
    label_numbers = set(re.findall(label_pattern, text, re.IGNORECASE))
    
    normalized = []
    for match in matches:
        # Skip if this number is a label (tp1, tp2, hedef3, etc.)
        if match.strip() in label_numbers:
            continue
        
        # If we detected comma thousands pattern, pre-process to remove commas
        processed_match = match
        if has_comma_thousands and ',' in match and 'k' not in match.lower() and 'bin' not in match.lower():
            processed_match = match.replace(',', '')
        
        value = normalize_number(processed_match)
        if value is not None and value >= 0.000001:  # Allow small decimals (crypto like PEPE), skip only near-zero
            normalized.append(value)
    
    return normalized


def parse_tp_sequence(text: str, entry_price: Optional[float] = None) -> List[float]:
    """
    Parse TP sequence formats.
    
    Formats:
    - "tp: 1-2-3" → [entry+1%, entry+2%, entry+3%]
    - "tp1:114k tp2:116k" → [114000, 116000]
    - "113k-114k-115k" → [113000, 114000, 115000]
    - "tp: 1, 2, 3" → [entry+1%, entry+2%, entry+3%]
    
    Args:
        text: Raw TP text
        entry_price: Entry price for relative TPs
    
    Returns:
        List of absolute TP prices
    """
    # Check if it's percentage format (ONLY if % symbol is present)
    if '%' in text and entry_price:
        percentage_pattern = r'%?\s*(\d+)\s*%?\s*[-,/]\s*%?\s*(\d+)\s*%?\s*[-,/]\s*%?\s*(\d+)\s*%?'
        percentage_match = re.search(percentage_pattern, text)
        
        if percentage_match:
            # Percentage format: %5-%10-%15 or 5%-10%-15%
            offsets = [int(percentage_match.group(i)) for i in range(1, 4)]
            
            # Interpret as percentage offsets
            return [entry_price * (1 + o/100) for o in offsets]
    
    # Check if it's relative format (single digits like "1-2-3", but NOT if any number > 10)
    # Pattern must match ONLY single/double digit sequences (not prefixed with %)
    relative_pattern = r'\b([1-9]|10)\s*[-,/]\s*([1-9]|10)\s*[-,/]\s*([1-9]|10)\b'
    relative_match = re.search(relative_pattern, text)
    
    if relative_match and entry_price:
        # Relative format: tp: 1-2-3 (percentages)
        offsets = [int(relative_match.group(i)) for i in range(1, 4)]
        
        # Interpret as percentage offsets
        return [entry_price * (1 + o/100) for o in offsets]
    
    # Otherwise, extract absolute prices
    numbers = normalize_number_list(text)
    
    # Don't filter by size - small decimals are valid for some cryptos
    return numbers


def clean_text(text: str) -> str:
    """
    Clean text from noise: URLs, emojis, extra whitespace.
    
    Args:
        text: Raw text
    
    Returns:
        Cleaned text
    """
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remove emojis (basic - removes most common)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    
    # Remove hashtags (but keep symbol)
    # #btc → btc
    text = re.sub(r'#(\w+)', r'\1', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


# Test cases
if __name__ == "__main__":
    test_cases = [
        # (input, expected)
        ("112.191", 112.191),
        ("112,191", 112.191),
        ("112k", 112000.0),
        ("112 k", 112000.0),
        ("112K", 112000.0),
        ("112bin", 112000.0),
        ("112 bin", 112000.0),
        ("112kilo", 112000.0),
        ("112,5k", 112500.0),
        ("112.5k", 112500.0),
        ("1,234.56", 1234.56),
        ("1.234,56", 1234.56),
        ("'112.191'", 112.191),
        ("  112  ", 112.0),
    ]
    
    print("🧪 Number Normalizer Tests\n")
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = normalize_number(input_text)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{input_text}' → {result} (expected: {expected})")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    # Test list extraction
    print("\n🧪 List Extraction Tests\n")
    
    list_tests = [
        ("113k-114k-115k", [113000, 114000, 115000]),
        ("tp1:114k tp2:116k", [114000, 116000]),
        ("113,500 - 114,000 - 115,000", [113500, 114000, 115000]),
    ]
    
    for input_text, expected in list_tests:
        result = normalize_number_list(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' → {result}")
    
    # Test TP sequence
    print("\n🧪 TP Sequence Tests\n")
    
    tp_tests = [
        ("tp: 1-2-3", 112000, [113120, 114240, 115360]),  # +1%, +2%, +3%
        ("tp1:114k tp2:116k", None, [114000, 116000]),
        ("113k-114k-115k", None, [113000, 114000, 115000]),
    ]
    
    for input_text, entry, expected in tp_tests:
        result = parse_tp_sequence(input_text, entry)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' (entry={entry}) → {result}")
