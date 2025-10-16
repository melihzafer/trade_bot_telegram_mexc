"""
View parsed signals summary.
"""
import json
from pathlib import Path

def view_parsed_signals():
    """Display summary of parsed signals."""
    parsed_file = Path("data/signals_parsed.jsonl")
    
    if not parsed_file.exists():
        print("❌ signals_parsed.jsonl not found!")
        return
    
    # Load all signals
    all_signals = []
    complete_signals = []
    
    with open(parsed_file, 'r', encoding='utf-8') as f:
        for line in f:
            signal = json.loads(line)
            all_signals.append(signal)
            if signal.get('is_complete'):
                complete_signals.append(signal)
    
    print("\n" + "="*80)
    print("📊 PARSED SIGNALS SUMMARY")
    print("="*80)
    
    print(f"\nTotal Parsed: {len(all_signals)}")
    print(f"Complete Signals: {len(complete_signals)}")
    print(f"Incomplete Signals: {len(all_signals) - len(complete_signals)}")
    
    print("\n" + "="*80)
    print("🎯 FIRST 10 COMPLETE SIGNALS")
    print("="*80)
    
    for i, signal in enumerate(complete_signals[:10], 1):
        print(f"\n{i}. {signal['direction']} {signal['symbol']}")
        print(f"   Entry: {signal['entry_min']} - {signal['entry_max']}")
        print(f"   Targets: {signal['num_targets']} (First: {signal['take_profits'][0]['tp_price'] if signal['take_profits'] else 'N/A'})")
        print(f"   Stop Loss: {signal['stop_loss']}")
        print(f"   Leverage: {signal.get('leverage', 'Not specified')}")
        print(f"   Channel: {signal['channel_title']}")
        print(f"   Date: {signal['timestamp'][:10]}")
    
    # Symbol distribution
    symbols = {}
    for sig in complete_signals:
        sym = sig.get('symbol', 'UNKNOWN')
        symbols[sym] = symbols.get(sym, 0) + 1
    
    print("\n" + "="*80)
    print("🪙 TOP 10 SYMBOLS")
    print("="*80)
    
    for sym, count in sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {sym}: {count} signals")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    view_parsed_signals()
