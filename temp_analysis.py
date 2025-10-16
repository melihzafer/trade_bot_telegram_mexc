#!/usr/bin/env python3
"""Quick analysis script for backtest results"""
import json
from collections import Counter, defaultdict
from datetime import datetime

# Load data
print("Loading data...")
results = [json.loads(line) for line in open('data/backtest_results.jsonl', encoding='utf-8')]
signals = [json.loads(line) for line in open('data/signals_parsed.jsonl', encoding='utf-8')]

print("\n" + "="*80)
print("📊 DETAILED BACKTEST ANALYSIS")
print("="*80)

# Symbol frequency
print("\n=== TOP 20 SYMBOLS BY SIGNAL COUNT ===")
symbol_counts = Counter([s.get('symbol') for s in signals if s.get('symbol')])
for sym, cnt in symbol_counts.most_common(20):
    print(f"  {sym:15} {cnt:3} signals")

print(f"\n  Total unique symbols: {len(symbol_counts)}")
print(f"  Total signals: {len(signals)}")

# Status breakdown
print("\n=== STATUS BREAKDOWN ===")
status_counts = Counter([r.get('status') for r in results])
for status, cnt in status_counts.most_common():
    pct = (cnt / len(results)) * 100
    print(f"  {status:10} {cnt:3} ({pct:5.1f}%)")

# Price data availability by symbol
print("\n=== PRICE DATA AVAILABILITY (Top 15) ===")
symbol_results = defaultdict(lambda: {"total": 0, "with_price": 0, "unknown": 0, "error": 0})
for i, sig in enumerate(signals):
    sym = sig.get('symbol')
    if not sym:
        continue
    res = results[i]
    status = res.get('status')
    
    symbol_results[sym]["total"] += 1
    if status == "unknown":
        symbol_results[sym]["with_price"] += 1
        symbol_results[sym]["unknown"] += 1
    elif status == "error":
        symbol_results[sym]["error"] += 1
    elif status in ["win", "loss"]:
        symbol_results[sym]["with_price"] += 1

# Sort by total signals
sorted_symbols = sorted(symbol_results.items(), key=lambda x: x[1]["total"], reverse=True)
print(f"{'Symbol':<15} {'Total':>6} {'W/Price':>8} {'Unknown':>8} {'Error':>6} {'Success%':>9}")
print("-" * 70)
for sym, stats in sorted_symbols[:15]:
    success_rate = (stats["with_price"] / stats["total"]) * 100 if stats["total"] > 0 else 0
    print(f"{sym:<15} {stats['total']:>6} {stats['with_price']:>8} {stats['unknown']:>8} {stats['error']:>6} {success_rate:>8.1f}%")

# Timestamp distribution
print("\n=== SIGNAL DATE DISTRIBUTION ===")
date_counts = defaultdict(int)
for sig in signals:
    ts = sig.get('timestamp', '')
    if ts:
        try:
            date = datetime.fromisoformat(ts.replace('Z', '+00:00')).date()
            date_counts[date] += 1
        except:
            pass

# Show last 14 days
sorted_dates = sorted(date_counts.items())
print(f"{'Date':<12} {'Signals':>8}")
print("-" * 22)
for date, cnt in sorted_dates[-14:]:
    print(f"{date} {cnt:>8}")

print(f"\nOldest signal: {sorted_dates[0][0] if sorted_dates else 'N/A'}")
print(f"Newest signal: {sorted_dates[-1][0] if sorted_dates else 'N/A'}")
print(f"Date range: {len(sorted_dates)} days")

# Channel/source distribution
print("\n=== TOP SIGNAL SOURCES ===")
source_counts = Counter([s.get('source', 'unknown') for s in signals])
for source, cnt in source_counts.most_common(15):
    pct = (cnt / len(signals)) * 100
    print(f"  {source[:40]:40} {cnt:3} ({pct:5.1f}%)")

print("\n" + "="*80)
print("✅ Analysis complete!")
print("="*80)
