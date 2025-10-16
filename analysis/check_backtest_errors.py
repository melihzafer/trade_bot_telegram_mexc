"""Quick script to analyze backtest errors"""
import json
from pathlib import Path

results_path = Path("data/backtest_results.jsonl")

results = []
with open(results_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            results.append(json.loads(line))

print(f"Total Results: {len(results)}")

# Count by status
status_count = {}
for r in results:
    status = r.get('status', 'unknown')
    status_count[status] = status_count.get(status, 0) + 1

print("\nStatus Breakdown:")
for status, count in sorted(status_count.items()):
    print(f"  {status}: {count}")

# Show error details
errors = [r for r in results if r.get('status') == 'error']
print(f"\nError Details ({len(errors)} total):")

error_types = {}
for e in errors:
    err_msg = e.get('error', 'Unknown')
    error_types[err_msg] = error_types.get(err_msg, 0) + 1

for err_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {err_type}: {count} times")
