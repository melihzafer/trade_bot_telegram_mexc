# telethon_test_read.py
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telethon import TelegramClient
from telethon.tl.types import PeerChannel

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")

# Test with your test channel
CHANNEL = "@kriptotestmz"  # Your test channel


async def main():
    print("🔄 Connecting to Telegram...")
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start(phone=PHONE)

    print("✅ Connected!")
    try:
        # Kanal objesini al
        entity = await client.get_entity(CHANNEL)
        print(f"📡 Reading last 5 messages from: {entity.title}")

        async for msg in client.iter_messages(entity, limit=5):
            print(f"[{msg.date}] {msg.sender_id}: {msg.text[:100]}")
    except Exception as e:
        print("❌ Error:", e)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
