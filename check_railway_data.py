import os
import json

print("=" * 60)
print("📂 Railway Data Folder Check")
print("=" * 60)

# Check if data folder exists
if os.path.exists('data'):
    print("✅ data/ folder exists")
    
    # List all files
    files = os.listdir('data')
    print(f"\n📁 Files in data/: {len(files)}")
    
    for f in files:
        path = os.path.join('data', f)
        size = os.path.getsize(path)
        print(f"  - {f}: {size:,} bytes")
        
        # If signals_raw.jsonl exists, show stats
        if f == 'signals_raw.jsonl':
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                print(f"    📊 Total signals: {len(lines)}")
                
                if lines:
                    # Show first signal
                    first = json.loads(lines[0])
                    print(f"    🔥 First signal: {first.get('source')} at {first.get('ts')}")
                    
                    # Show last signal
                    last = json.loads(lines[-1])
                    print(f"    🔥 Last signal: {last.get('source')} at {last.get('ts')}")
else:
    print("❌ data/ folder does not exist!")
    print("💡 Creating data/ folder...")
    os.makedirs('data', exist_ok=True)
    print("✅ data/ folder created")
