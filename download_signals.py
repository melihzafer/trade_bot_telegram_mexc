"""
Download signals from Railway deployment
"""
import requests
import sys

print("📥 Downloading signals from Railway...")

url = "https://tradebottelegrammexc-production.up.railway.app/download/raw"

try:
    response = requests.get(url, timeout=30)
    
    if response.status_code == 200:
        filename = "signals_raw_downloaded.jsonl"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        # Count lines
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            count = len(lines)
        
        print(f"✅ Downloaded: {filename}")
        print(f"📊 Total signals: {count}")
        
        # Show first and last signal
        if count > 0:
            print(f"\n🔥 First signal preview:")
            print(lines[0][:200] + "...")
            print(f"\n🔥 Last signal preview:")
            print(lines[-1][:200] + "...")
    
    elif response.status_code == 404:
        print("❌ No signals file found on Railway yet.")
        print("💡 Collector is running but hasn't saved any signals yet.")
        sys.exit(1)
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        sys.exit(1)

except requests.exceptions.Timeout:
    print("❌ Request timeout. Railway might be slow or down.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
