"""Quick script to check signals file on Railway"""
import os
from pathlib import Path

file_path = Path("data/signals_raw.jsonl")

if file_path.exists():
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            print(f"Total lines: {len(lines)}")
            if lines:
                print(f"\nLast 3 signals:")
                for line in lines[-3:]:
                    print(line.strip()[:150])
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print("File does not exist!")
