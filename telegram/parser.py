"""
Signal parser - extracts structured signals from raw Telegram messages.
IMPROVED: 6 regex patterns + Turkish number normalization + better validation
"""
import re
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import info, warn

# ==================== Pattern Definitions (IMPROVED) ====================

# Pattern 1: English format with LONG/SHORT + emoji
PATTERN_ENGLISH = re.compile(
    r"(?:🟢|🔴|📊|📈|📉)?\s*(?:#)?\s*(LONG|SHORT|BUY|SELL)\s+"
    r"(?:💲|#|@|\$)?\s*([A-Z]{2,10}(?:USDT|USD|BTC|ETH)?)\b.*?"
    r"(?:Entry|ENTRY|entry|EN|Price|PRICE)[:\s\-]+([\d.,]+)(?:\s*[-~]\s*([\d.,]+))?.*?"
    r"(?:Target|TARGET|target|TP|tp|T1|Take\s*Profit)[:\s\-]+([\d.,]+).*?"
    r"(?:Stop\s*Loss|STOP\s*LOSS|stop\s*loss|Stop|SL|sl)[:\s\-]+([\d.,]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 2: Turkish format
PATTERN_TURKISH = re.compile(
    r"(?:#|@)?\s*([A-Za-z]{2,10})(?:USDT|USD)?\s+(?:\$[A-Za-z]+\s+)?(?:\d+x\s+)?(?:kaldıraç\s+)?(long|short|LONG|SHORT|al|AL|sat|SAT)\b.*?"
    r"(?:giriş|giris|GİRİŞ|GIRIS|Entry|entry|fiyat)[:\s\-]+([\d.,]+).*?"
    r"(?:tp|TP|hedef|HEDEF|target)[:\s\-]+([\d.,]+)(?:\s*[-~]\s*([\d.,]+))?.*?"
    r"(?:sl|SL|stop|STOP|zarar|ZARAR|Stop\s*Loss)[:\s\-]+([\d.,]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 3: Setup format
PATTERN_SETUP = re.compile(
    r"[#@]?([A-Z]{2,10})(?:USDT|USD)?\s+(SHORT|LONG|Buy|Sell)\s+(?:SETUP|Signal|Setup|signal).*?"
    r"(?:Target\s*1|T1|TP\s*1)[:\s\-]+\$?([\d.,]+).*?"
    r"(?:STOP|Stop\s*Loss|SL)[:\s\-]+\$?([\d.,]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 4: Simple minimal format
PATTERN_SIMPLE = re.compile(
    r"\b(BUY|SELL|LONG|SHORT)\b\s+([A-Z]{2,10}(?:USDT|USD|BTC|ETH)?)\s+([\d.,]+).*?"
    r"(?:TP|tp|Target|target)[:\s\-]+([\d.,]+).*?"
    r"(?:SL|sl|Stop|stop)[:\s\-]+([\d.,]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 5: Compact format (NEW)
PATTERN_COMPACT = re.compile(
    r"([A-Z]{2,10})(?:USDT|USD)?\s+(L|S|LONG|SHORT|BUY|SELL)\s+"
    r"([\d.,]+k?)(?:/|,|\s+)(?:TP:?\s*)?([\d.,]+k?)(?:/|,|\s+)(?:SL:?\s*)?([\d.,]+k?)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 6: Reverse order format (NEW)
PATTERN_REVERSE = re.compile(
    r"(LONG|SHORT|BUY|SELL)[:\s]+([A-Z]{2,10})(?:USDT|USD)?.*?"
    r"(?:Entry|entry|E|@)[:\s]+([\d.,]+).*?"
    r"(?:TP|tp|Target)[:\s]+([\d.,]+).*?"
    r"(?:SL|sl|Stop)[:\s]+([\d.,]+)",
    re.IGNORECASE | re.DOTALL,
)


def clean_number(s):
    """Convert string to float, handling Turkish/English number formats + k notation"""
    if not s:
        return 0.0
    s_clean = s.strip().upper()
    
    # Handle 'k' notation (50k = 50000)
    if 'K' in s_clean:
        return float(s_clean.replace('K', '').replace(',', '').replace('.', '')) * 1000
    
    # Determine if comma is decimal separator or thousands separator
    # Rule: If comma followed by exactly 3 digits (and possibly more commas), it's thousands
    #       Otherwise it's a decimal separator
    if ',' in s_clean:
        parts = s_clean.split(',')
        # Check if it looks like thousands separator: 50,000 or 1,234,567
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            # Thousands separator - remove commas
            return float(s_clean.replace(',', ''))
        else:
            # Decimal separator - replace with dot
            return float(s_clean.replace(',', '.'))
    
    # No comma, just parse normally
    return float(s_clean)


def parse_message(raw_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a raw message object into a structured signal.
    Tries multiple pattern matchers in order.

    Args:
        raw_obj: Dict with keys 'channel_title' (or 'source'), 'timestamp' (or 'ts'), 'text'

    Returns:
        Parsed signal dict or None if no valid signal found
    """
    text = raw_obj.get("text", "")
    source = raw_obj.get("channel_title") or raw_obj.get("source", "unknown")
    timestamp = raw_obj.get("timestamp") or raw_obj.get("ts", datetime.now().isoformat())

    if not text:
        return None

    # Try all patterns in order
    patterns = [
        ("english", PATTERN_ENGLISH),
        ("turkish", PATTERN_TURKISH),
        ("setup", PATTERN_SETUP),
        ("simple", PATTERN_SIMPLE),
        ("compact", PATTERN_COMPACT),
        ("reverse", PATTERN_REVERSE),
    ]

    for pattern_name, pattern in patterns:
        match = pattern.search(text)
        if match:
            try:
                groups = match.groups()
                
                # Different extraction based on pattern
                if pattern_name == "english":
                    side, symbol, entry, entry2, tp, sl = groups
                    entry = clean_number(entry)
                    tp = clean_number(tp)
                    sl = clean_number(sl)
                    
                elif pattern_name == "turkish":
                    symbol, side, entry, tp, tp2, sl = groups
                    entry = clean_number(entry)
                    tp = clean_number(tp)
                    sl = clean_number(sl)
                    # Use average TP if range given
                    if tp2:
                        tp = (tp + clean_number(tp2)) / 2
                    # Normalize Turkish side
                    if side.lower() in ['al']:
                        side = 'LONG'
                    elif side.lower() in ['sat']:
                        side = 'SHORT'
                
                elif pattern_name == "setup":
                    symbol, side, tp, sl = groups
                    entry = clean_number(tp) * 0.99 if side.upper() == "LONG" else clean_number(tp) * 1.01
                    tp = clean_number(tp)
                    sl = clean_number(sl)
                
                elif pattern_name == "simple":
                    side, symbol, entry, tp, sl = groups
                    entry = clean_number(entry)
                    tp = clean_number(tp)
                    sl = clean_number(sl)
                
                elif pattern_name == "compact":
                    symbol, side, entry, tp, sl = groups
                    entry = clean_number(entry)
                    tp = clean_number(tp)
                    sl = clean_number(sl)
                    if side.upper() == 'L':
                        side = 'LONG'
                    elif side.upper() == 'S':
                        side = 'SHORT'
                
                elif pattern_name == "reverse":
                    side, symbol, entry, tp, sl = groups
                    entry = clean_number(entry)
                    tp = clean_number(tp)
                    sl = clean_number(sl)
                
                # Ensure symbol has USDT suffix
                symbol = symbol.upper()
                if not any(symbol.endswith(suffix) for suffix in ['USDT', 'USD', 'BTC', 'ETH']):
                    symbol += 'USDT'
                
                # Normalize side
                side = side.upper()
                if side in ['BUY', 'LONG']:
                    side = 'LONG'
                elif side in ['SELL', 'SHORT']:
                    side = 'SHORT'
                
                # Basic validation
                if entry <= 0 or tp <= 0 or sl <= 0:
                    continue
                
                # Validate trade logic
                if side == 'LONG':
                    if tp <= entry or sl >= entry:
                        continue
                else:  # SHORT
                    if tp >= entry or sl <= entry:
                        continue
                
                return {
                    "source": source,
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "side": side,
                    "entry": entry,
                    "tp": tp,
                    "sl": sl,
                    "leverage": 1,
                    "parsed_by": f"regex_{pattern_name}",
                }
            
            except (ValueError, TypeError, AttributeError):
                continue
    
    return None


def parse_file(input_path: str, output_path: str):
    """Parse raw signals from input JSONL file and write to output JSONL file."""
    parsed_count = 0
    skipped_count = 0
    
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            try:
                raw_obj = json.loads(line)
                result = parse_message(raw_obj)
                
                if result:
                    outfile.write(json.dumps(result, ensure_ascii=False) + "\n")
                    parsed_count += 1
                else:
                    skipped_count += 1
            
            except json.JSONDecodeError:
                skipped_count += 1
                continue
    
    info(f"✅ Parsed {parsed_count} signals, skipped {skipped_count}")
    return parsed_count


if __name__ == "__main__":
    # Test parser
    test_messages = [
        {"text": "LONG BTCUSDT Entry: 50000 TP: 52000 SL: 48000", "source": "test", "timestamp": "2025-01-01T00:00:00"},
        {"text": "BTC LONG giris: 50,000 tp: 52,000 sl: 48,000", "source": "test", "timestamp": "2025-01-01T00:00:00"},
        {"text": "LONG BTCUSDT 50000 TP 52000 SL 48000", "source": "test", "timestamp": "2025-01-01T00:00:00"},
        {"text": "BTCUSDT L 50k/52k/48k", "source": "test", "timestamp": "2025-01-01T00:00:00"},
    ]
    
    passed = 0
    for msg in test_messages:
        result = parse_message(msg)
        if result:
            print(f"PASS: {result['symbol']} {result['side']} @ {result['entry']} ({result['parsed_by']})")
            passed += 1
        else:
            print(f"FAIL: {msg['text'][:50]}...")
    
    print(f"\nPassed {passed}/{len(test_messages)} tests")
