"""
Signal parser - extracts structured signals from raw Telegram messages.
Uses regex patterns to identify BUY/SELL, ENTRY, TP, SL values.
"""
import re
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from utils.config import DATA_DIR
from utils.logger import info, warn

RAW_PATH = DATA_DIR / "signals_raw.jsonl"
PARSED_PATH = DATA_DIR / "signals_parsed.csv"

# CSV fields
FIELDS = ["source", "ts", "symbol", "side", "entry", "tp", "sl", "leverage", "note"]

# ==================== Pattern Definitions ====================

# Pattern 1: English format with LONG/SHORT + emoji
# Example: "🟢 LONG\n💲 DOGEUSDT\n📈 Entry : 0.18869 - 0.18925\n🎯 Target 1 - 0.19076"
PATTERN_ENGLISH = re.compile(
    r"(?:🟢|🔴|📊)?\s*(LONG|SHORT|BUY|SELL)\s+"
    r"(?:💲|#)?\s*([A-Z]{2,10}(?:USDT)?)\b.*?"
    r"(?:Entry|ENTRY|entry)[:\s-]+([\d.]+)(?:\s*-\s*([\d.]+))?.*?"
    r"(?:Target|TARGET|target)\s*(?:1)?[:\s-]+([\d.]+).*?"
    r"(?:Stop\s*Loss|STOP\s*LOSS|stop\s*loss|Stop)[:\s]+([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 2: Turkish format (giriş, tp, sl, stop)
# Example: "avax long\ngiriş: 21.60\nsl: 21.00\ntp: 22.30 - 23.40"
PATTERN_TURKISH = re.compile(
    r"(?:#)?([A-Za-z]{2,10})\s+(?:\$[A-Za-z]+\s+)?(?:\d+x\s+)?(?:kaldıraç\s+)?(long|short|LONG|SHORT)\b.*?"
    r"(?:giriş|giris|Entry|entry)[:\s]+([\d.]+).*?"
    r"(?:tp|TP)[:\s]+([\d.]+)(?:\s*-\s*([\d.]+))?.*?"
    r"(?:sl|SL|stop|STOP)[:\s]+([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 3: Setup format (#SYMBOL SETUP with numbered targets)
# Example: "#ICNT SHORT SETUP\nTarget 1: $0.2045\nTarget 2: $0.2015\nSTOP : $0.2190"
PATTERN_SETUP = re.compile(
    r"#([A-Z]{2,10})\s+(SHORT|LONG)\s+SETUP.*?"
    r"(?:Target\s*1)[:\s]+\$?([\d.]+).*?"
    r"(?:STOP|Stop\s*Loss)[:\s]+\$?([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)

# Pattern 4: Simple minimal format
# Example: "BUY BTCUSDT 45000 TP: 46000 SL: 44500"
PATTERN_SIMPLE = re.compile(
    r"\b(BUY|SELL|LONG|SHORT)\b\s+([A-Z]{2,10}(?:USDT)?)\s+([\d.]+).*?"
    r"(?:TP|tp)[:\s]+([\d.]+).*?"
    r"(?:SL|sl)[:\s]+([\d.]+)",
    re.IGNORECASE | re.DOTALL,
)


def parse_message(raw_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a raw message object into a structured signal.
    Tries multiple pattern matchers in order.

    Args:
        raw_obj: Dict with keys 'source', 'ts', 'text'

    Returns:
        Parsed signal dict or None if no valid signal found
    """
    text = raw_obj.get("text", "")
    source = raw_obj.get("source", "unknown")
    ts = raw_obj.get("ts", datetime.utcnow().isoformat())

    # Try Pattern 3: SETUP format (most specific, check first)
    result = try_pattern_setup(text)
    if result:
        return finalize_signal(result, source, ts, text)

    # Try Pattern 1: English format with emoji
    result = try_pattern_english(text)
    if result:
        return finalize_signal(result, source, ts, text)

    # Try Pattern 2: Turkish format
    result = try_pattern_turkish(text)
    if result:
        return finalize_signal(result, source, ts, text)

    # Try Pattern 4: Simple format
    result = try_pattern_simple(text)
    if result:
        return finalize_signal(result, source, ts, text)

    # No pattern matched
    return None


def try_pattern_english(text: str) -> Optional[Dict[str, Any]]:
    """Match English format: LONG/SHORT SYMBOL Entry Target Stop Loss"""
    match = PATTERN_ENGLISH.search(text)
    if not match:
        return None

    side = match.group(1).upper()
    symbol = match.group(2).upper()
    entry1 = float(match.group(3)) if match.group(3) else None
    entry2 = float(match.group(4)) if match.group(4) else None
    tp = float(match.group(5)) if match.group(5) else None
    sl = float(match.group(6)) if match.group(6) else None

    # Normalize side
    if side in ("BUY", "LONG"):
        side = "LONG"
    elif side in ("SELL", "SHORT"):
        side = "SHORT"

    # Use entry range midpoint if available
    entry = ((entry1 + entry2) / 2) if (entry1 and entry2) else entry1

    # Ensure symbol has USDT suffix
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    return {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "leverage": None,
    }


def try_pattern_turkish(text: str) -> Optional[Dict[str, Any]]:
    """Match Turkish format: SYMBOL long/short giriş: X tp: Y sl: Z"""
    # First try to match symbol and side
    symbol_match = re.search(
        r"(?:#)?([A-Za-z]{2,10})\s+(?:\$[A-Za-z]+\s+)?(?:\d+x\s+)?(?:kaldıraç\s+)?(long|short)",
        text,
        re.IGNORECASE,
    )
    if not symbol_match:
        return None

    symbol = symbol_match.group(1).upper()
    side = symbol_match.group(2).upper()

    # Extract values (order-independent)
    entry_match = re.search(r"(?:giriş|giris|Entry|entry)[:\s]+([\d.]+)", text, re.IGNORECASE)
    tp_match = re.search(r"(?:tp|TP)[:\s]+([\d.]+)(?:\s*-\s*([\d.]+))?", text, re.IGNORECASE)
    sl_match = re.search(r"(?:sl|SL|stop|STOP)[:\s]+([\d.]+)", text, re.IGNORECASE)

    entry = float(entry_match.group(1)) if entry_match else None
    tp1 = float(tp_match.group(1)) if tp_match else None
    tp2 = float(tp_match.group(2)) if (tp_match and tp_match.group(2)) else None
    sl = float(sl_match.group(1)) if sl_match else None

    # Extract leverage if present (e.g., "7x kaldıraç")
    lev_match = re.search(r"(\d+)x", text, re.IGNORECASE)
    leverage = int(lev_match.group(1)) if lev_match else None

    # Use TP range midpoint if available
    tp = ((tp1 + tp2) / 2) if (tp1 and tp2) else tp1

    # Ensure symbol has USDT suffix
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    return {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "leverage": leverage,
    }


def try_pattern_setup(text: str) -> Optional[Dict[str, Any]]:
    """Match SETUP format: #SYMBOL SHORT SETUP Target 1: X STOP: Y"""
    match = PATTERN_SETUP.search(text)
    if not match:
        return None

    symbol = match.group(1).upper()
    side = match.group(2).upper()
    tp = float(match.group(3)) if match.group(3) else None
    sl = float(match.group(4)) if match.group(4) else None

    # Extract leverage separately (e.g., "Lev: 20x")
    lev_match = re.search(r"Lev[:\s]+(\d+)x", text, re.IGNORECASE)
    leverage = int(lev_match.group(1)) if lev_match else None

    # Ensure symbol has USDT suffix
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    return {
        "symbol": symbol,
        "side": side,
        "entry": None,  # No entry specified in SETUP format
        "tp": tp,
        "sl": sl,
        "leverage": leverage,
    }


def try_pattern_simple(text: str) -> Optional[Dict[str, Any]]:
    """Match simple format: BUY BTCUSDT 45000 TP: 46000 SL: 44500"""
    match = PATTERN_SIMPLE.search(text)
    if not match:
        return None

    side = match.group(1).upper()
    symbol = match.group(2).upper()
    entry = float(match.group(3)) if match.group(3) else None
    tp = float(match.group(4)) if match.group(4) else None
    sl = float(match.group(5)) if match.group(5) else None

    # Normalize side
    if side in ("BUY", "LONG"):
        side = "LONG"
    elif side in ("SELL", "SHORT"):
        side = "SHORT"

    # Ensure symbol has USDT suffix
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    return {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "leverage": None,
    }


def finalize_signal(
    parsed: Dict[str, Any], source: str, ts: str, text: str
) -> Dict[str, Any]:
    """
    Add metadata and validate final signal.

    Args:
        parsed: Parsed signal data
        source: Channel source
        ts: Timestamp
        text: Original message text

    Returns:
        Complete signal dict
    """
    # Basic validation
    if not parsed.get("symbol") or not parsed.get("side"):
        return None

    return {
        "source": source,
        "ts": ts,
        "symbol": parsed["symbol"],
        "side": parsed["side"],
        "entry": parsed.get("entry"),
        "tp": parsed.get("tp"),
        "sl": parsed.get("sl"),
        "leverage": parsed.get("leverage"),
        "note": text[:200],  # Store snippet of original message
    }


def run_parser():
    """
    Parse all raw messages and append new signals to CSV.
    Skips duplicates based on (timestamp, source) tuple.
    """
    if not RAW_PATH.exists():
        warn(f"Raw messages file not found: {RAW_PATH}")
        return

    # Track existing signals to avoid duplicates
    existing = set()
    if PARSED_PATH.exists():
        with open(PARSED_PATH, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add((row["ts"], row["source"]))

    # Parse raw messages
    new_count = 0
    with open(PARSED_PATH, "a", newline="", encoding="utf-8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=FIELDS)

        # Write header if file is empty
        if out_file.tell() == 0:
            writer.writeheader()

        with open(RAW_PATH, "r", encoding="utf-8") as in_file:
            for line in in_file:
                try:
                    raw_obj = json.loads(line)
                    key = (raw_obj.get("ts"), raw_obj.get("source"))

                    # Skip if already processed
                    if key in existing:
                        continue

                    # Parse message
                    parsed = parse_message(raw_obj)
                    if parsed:
                        writer.writerow(parsed)
                        existing.add(key)
                        new_count += 1
                        info(
                            f"✅ Parsed signal: {parsed['side']} {parsed['symbol']} @ {parsed.get('entry', 'market')}"
                        )

                except json.JSONDecodeError as e:
                    warn(f"Invalid JSON line: {e}")
                except Exception as e:
                    warn(f"Error parsing message: {e}")

    info(f"📊 Parser complete. {new_count} new signals added to {PARSED_PATH}")


# Channel-specific parser profiles can be added here
def parse_style_a(text: str, source: str, ts: str) -> Optional[Dict[str, Any]]:
    """Example: Custom parser for specific channel format."""
    # Implement custom logic for channel-specific formatting
    pass


def parse_style_b(text: str, source: str, ts: str) -> Optional[Dict[str, Any]]:
    """Example: Another custom parser."""
    # Implement custom logic for different channel
    pass


if __name__ == "__main__":
    run_parser()
