# list_channels.py
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
import csv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")

async def main():
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start(phone=PHONE)


    dialogs = await client.get_dialogs(limit=None)
    rows = []
    print("\n" + "="*80)
    print("📋 SCANNING ALL CHANNELS...")
    print("="*80 + "\n")
    
    for d in dialogs:
        if not d.is_channel:
            continue
        ent = d.entity
        
        # Format ID as Telethon expects (-100...)
        channel_id = getattr(ent, "id", "")
        if channel_id and not str(channel_id).startswith("-"):
            channel_id = f"-100{channel_id}"
        elif channel_id:
            channel_id = str(channel_id)
            
        row = {
            "title": getattr(ent, "title", ""),
            "id": channel_id,
            "access_hash": getattr(ent, "access_hash", ""),
            "username": f"@{getattr(ent, 'username', '')}" if getattr(ent, "username", None) else "PRIVATE",
            "megagroup": getattr(ent, "megagroup", False)
        }
        rows.append(row)
        
        # Print to console
        print(f"📺 {row['title']}")
        print(f"   ID: {row['id']}")
        print(f"   Username: {row['username']}")
        print(f"   Megagroup: {row['megagroup']}")
        print("-" * 80)

    with open("channels.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Saved {len(rows)} channels to channels.csv")
    print("💡 Use ID column for private channels in .env TELEGRAM_CHANNELS")
    await client.disconnect()

asyncio.run(main())
