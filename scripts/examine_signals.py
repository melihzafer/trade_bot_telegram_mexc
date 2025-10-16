"""
Quick script to examine signal message formats.
"""
import json
from pathlib import Path

def examine_signals(num_samples=30):
    """Print sample messages to understand formats."""
    data_file = Path("data/signals_raw.jsonl")
    
    if not data_file.exists():
        print("❌ signals_raw.jsonl not found!")
        return
    
    print("=" * 80)
    print("📋 EXAMINING SIGNAL FORMATS")
    print("=" * 80)
    
    with open(data_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            
            try:
                data = json.loads(line)
                text = data.get('text', '')
                channel = data.get('channel_title', 'Unknown')
                
                # Only show messages that look like signals
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in ['long', 'short', 'buy', 'sell', 'entry', 'tp', 'sl']):
                    print(f"\n{'='*80}")
                    print(f"📱 Channel: {channel}")
                    print(f"🆔 Message ID: {data.get('message_id')}")
                    print(f"📅 Date: {data.get('timestamp')}")
                    print(f"{'='*80}")
                    print(text[:500])  # First 500 chars
                    print()
                    
            except json.JSONDecodeError:
                continue
    
    print("\n" + "=" * 80)
    print("✅ Examination complete!")
    print("=" * 80)


if __name__ == "__main__":
    examine_signals(num_samples=50)
