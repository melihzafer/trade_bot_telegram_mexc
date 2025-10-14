"""Delete old corrupted signals file on Railway volume"""
import os
from pathlib import Path

file_path = Path("data/signals_raw.jsonl")

if file_path.exists():
    os.remove(file_path)
    print(f"✅ Deleted: {file_path}")
else:
    print(f"ℹ️ File doesn't exist: {file_path}")

print("💾 Collector will create a fresh file on next message.")
