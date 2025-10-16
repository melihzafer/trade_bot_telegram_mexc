"""
List All Telegram Channels
Shows all channels/groups you're subscribed to with their IDs
"""
import asyncio
import os
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import TELEGRAM_API_ID, TELEGRAM_API_HASH


async def list_all_channels():
    """List all channels and groups with their IDs."""
    
    print("=" * 90)
    print("📋 ALL TELEGRAM CHANNELS & GROUPS")
    print("=" * 90)
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        print("❌ Telegram API credentials not set. Check .env file.")
        return
    
    phone = os.getenv("TELEGRAM_PHONE")
    if not phone:
        print("❌ TELEGRAM_PHONE not set in .env file")
        return
    
    print(f"📱 Connecting to Telegram...")
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        await client.start(phone=phone)
        print(f"✅ Connected as {phone}\n")
        
        channels = []
        groups = []
        
        print("📡 Scanning...")
        
        # Get all dialogs
        async for dialog in client.iter_dialogs():
            name = dialog.title or dialog.name or "(No name)"
            id_num = dialog.id
            
            if dialog.is_channel:
                channels.append((name, id_num))
            elif dialog.is_group:
                groups.append((name, id_num))
        
        # Print channels
        if channels:
            print("\n" + "=" * 90)
            print(f"📢 CHANNELS ({len(channels)} total)")
            print("=" * 90)
            for i, (name, cid) in enumerate(sorted(channels), 1):
                print(f"{i:3}. {name:60} | ID: {cid}")
        
        # Print groups
        if groups:
            print("\n" + "=" * 90)
            print(f"👥 GROUPS ({len(groups)} total)")
            print("=" * 90)
            for i, (name, gid) in enumerate(sorted(groups), 1):
                print(f"{i:3}. {name:60} | ID: {gid}")
        
        print("\n" + "=" * 90)
        print(f"✅ Total: {len(channels)} channels, {len(groups)} groups")
        print("=" * 90)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(list_all_channels())
