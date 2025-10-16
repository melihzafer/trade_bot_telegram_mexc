"""
Batch processor for parsing all signals in signals_raw.jsonl.
Creates signals_parsed.jsonl with structured trading signals.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.parser import SignalParser
from utils.logger import info, success, warn, error


def load_raw_signals(raw_path: Path) -> List[Dict]:
    """
    Load all raw signals from JSONL file.
    
    Args:
        raw_path: Path to signals_raw.jsonl
        
    Returns:
        List of message dicts
    """
    signals = []
    
    if not raw_path.exists():
        error(f"❌ File not found: {raw_path}")
        return signals
    
    try:
        with open(raw_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        data = json.loads(line)
                        signals.append(data)
                    except json.JSONDecodeError as e:
                        warn(f"⚠️ Invalid JSON at line {line_num}: {e}")
                        continue
        
        info(f"📚 Loaded {len(signals)} raw messages")
        
    except Exception as e:
        error(f"❌ Error loading raw signals: {e}")
    
    return signals


def parse_all_signals(raw_signals: List[Dict], parser: SignalParser) -> tuple:
    """
    Parse all raw signals.
    
    Args:
        raw_signals: List of raw message dicts
        parser: SignalParser instance
        
    Returns:
        Tuple of (parsed_signals, stats_dict)
    """
    parsed_signals = []
    stats = {
        'total': len(raw_signals),
        'parsed': 0,
        'complete': 0,
        'incomplete': 0,
        'failed': 0,
        'by_channel': {},
        'by_direction': {'LONG': 0, 'SHORT': 0, 'UNKNOWN': 0}
    }
    
    info(f"🔄 Parsing {stats['total']} messages...")
    
    for i, raw_msg in enumerate(raw_signals, 1):
        # Progress indicator
        if i % 500 == 0:
            info(f"   Progress: {i}/{stats['total']} ({i*100//stats['total']}%)")
        
        try:
            # Parse signal
            parsed = parser.parse_signal(raw_msg)
            
            if parsed:
                stats['parsed'] += 1
                
                # Check if complete
                if parser.is_signal_complete(parsed):
                    stats['complete'] += 1
                    parsed['is_complete'] = True
                else:
                    stats['incomplete'] += 1
                    parsed['is_complete'] = False
                
                # Track by channel
                channel = parsed.get('channel_title', 'Unknown')
                stats['by_channel'][channel] = stats['by_channel'].get(channel, 0) + 1
                
                # Track by direction
                direction = parsed.get('direction', 'UNKNOWN')
                stats['by_direction'][direction] = stats['by_direction'].get(direction, 0) + 1
                
                parsed_signals.append(parsed)
            else:
                stats['failed'] += 1
                
        except Exception as e:
            stats['failed'] += 1
            warn(f"⚠️ Error parsing message {raw_msg.get('message_id')}: {e}")
    
    return parsed_signals, stats


def save_parsed_signals(parsed_signals: List[Dict], output_path: Path):
    """
    Save parsed signals to JSONL file.
    
    Args:
        parsed_signals: List of parsed signal dicts
        output_path: Path to save signals_parsed.jsonl
    """
    if not parsed_signals:
        warn("⚠️ No signals to save")
        return
    
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for signal in parsed_signals:
                json_line = json.dumps(signal, ensure_ascii=False)
                f.write(json_line + '\n')
        
        success(f"💾 Saved {len(parsed_signals)} parsed signals to {output_path}")
        
    except Exception as e:
        error(f"❌ Error saving parsed signals: {e}")


def print_statistics(stats: Dict):
    """
    Print detailed parsing statistics.
    
    Args:
        stats: Statistics dictionary
    """
    print("\n" + "="*80)
    print("📊 PARSING STATISTICS")
    print("="*80)
    
    print(f"\n📈 Overall Results:")
    print(f"   Total Messages: {stats['total']}")
    print(f"   ✅ Successfully Parsed: {stats['parsed']} ({stats['parsed']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"   🎯 Complete Signals: {stats['complete']} ({stats['complete']*100//stats['parsed'] if stats['parsed'] > 0 else 0}%)")
    print(f"   ⚠️ Incomplete Signals: {stats['incomplete']}")
    print(f"   ❌ Failed to Parse: {stats['failed']}")
    
    print(f"\n🎭 By Direction:")
    for direction, count in stats['by_direction'].items():
        direction_str = direction if direction else 'UNKNOWN'
        print(f"   {direction_str}: {count}")
    
    print(f"\n📱 By Channel:")
    for channel, count in sorted(stats['by_channel'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {channel}: {count}")
    
    print("\n" + "="*80)


def main():
    """Main entry point for batch parsing."""
    print("\n" + "="*80)
    print("🚀 BATCH SIGNAL PARSER")
    print("="*80)
    
    # Paths
    data_dir = Path("data")
    raw_path = data_dir / "signals_raw.jsonl"
    parsed_path = data_dir / "signals_parsed.jsonl"
    
    # Initialize parser
    parser = SignalParser()
    info("✅ Parser initialized")
    
    # Load raw signals
    raw_signals = load_raw_signals(raw_path)
    
    if not raw_signals:
        error("❌ No raw signals found. Run historical collector first!")
        return
    
    # Parse all signals
    parsed_signals, stats = parse_all_signals(raw_signals, parser)
    
    # Save parsed signals
    save_parsed_signals(parsed_signals, parsed_path)
    
    # Print statistics
    print_statistics(stats)
    
    # Success summary
    if stats['complete'] > 0:
        success(f"\n🎉 SUCCESS! {stats['complete']} complete signals ready for backtesting!")
        info(f"📁 Parsed data: {parsed_path}")
    else:
        warn("\n⚠️ No complete signals found. Check parser patterns.")


if __name__ == "__main__":
    main()
