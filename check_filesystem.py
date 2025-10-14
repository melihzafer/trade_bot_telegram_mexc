"""Check Railway filesystem and data directory"""
import os
from pathlib import Path

print("=" * 60)
print("🔍 Railway Filesystem Check")
print("=" * 60)

print(f"\n📂 Current Working Directory: {os.getcwd()}")
print(f"📋 Directory listing:")
for item in os.listdir('.'):
    print(f"   - {item}")

data_path = Path("data")
print(f"\n📁 data/ exists: {data_path.exists()}")

if not data_path.exists():
    print("⚠️ Creating data/ directory...")
    data_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created: {data_path}")

signals_file = data_path / "signals_raw.jsonl"
print(f"\n📄 signals_raw.jsonl exists: {signals_file.exists()}")

if signals_file.exists():
    size = signals_file.stat().st_size
    print(f"📊 File size: {size} bytes")
    
    with open(signals_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print(f"📊 Total lines: {len(lines)}")

print("\n" + "=" * 60)
