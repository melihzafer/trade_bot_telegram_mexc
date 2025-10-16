"""
Telegram Channel ID Finder
Finds the numeric IDs for specified channel names to add to .env
"""
import asyncio
import os
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ChannelPrivateError, ChannelInvalidError

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import TELEGRAM_API_ID, TELEGRAM_API_HASH


# Target channels for paper trading
TARGET_CHANNELS = [
    "Crypto Neon",
    "DeepWeb Kripto",
    "Kripto Kampı",
    "Kripto Star",
    "Kripto Simpsonlar",
    "Crypro Tradin",
    "Kripto Delisi VIP"
]


async def find_channel_ids():
    """Find channel IDs by searching through user's dialogs."""
    
    print("=" * 70)
    print("🔍 TELEGRAM CHANNEL ID FINDER")
    print("=" * 70)
    
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
        
        found_channels = {}
        all_channels = []
        
        print("📡 Scanning your channels and groups...\n")
        
        # Get all dialogs (channels, groups, chats)
        async for dialog in client.iter_dialogs():
            # Skip users (only interested in channels/groups)
            if not dialog.is_channel and not dialog.is_group:
                continue
            
            channel_name = dialog.title or dialog.name or ""
            channel_id = dialog.id
            
            # Skip if no name
            if not channel_name:
                continue
            
            all_channels.append((channel_name, channel_id))
            
            # Check if this is one of our target channels (case-insensitive partial match)
            for target in TARGET_CHANNELS:
                # Avoid duplicate matches
                if target in found_channels:
                    continue
                    
                if target.lower() in channel_name.lower() or channel_name.lower() in target.lower():
                    found_channels[target] = {
                        'full_name': channel_name,
                        'id': channel_id
                    }
                    print(f"✅ FOUND: {target}")
                    print(f"   Full name: {channel_name}")
                    print(f"   ID: {channel_id}\n")
        
        # Summary
        print("=" * 70)
        print("📊 SEARCH SUMMARY")
        print("=" * 70)
        print(f"Found {len(found_channels)}/{len(TARGET_CHANNELS)} target channels\n")
        
        if found_channels:
            print("✅ FOUND CHANNELS - Add these to .env:")
            print("-" * 70)
            
            # Generate .env format
            channel_ids = []
            for target in TARGET_CHANNELS:
                if target in found_channels:
                    channel_id = found_channels[target]['id']
                    channel_ids.append(str(channel_id))
                    print(f"{found_channels[target]['full_name']}: {channel_id}")
            
            print("\n" + "=" * 70)
            print("📝 .ENV FORMAT (copy this):")
            print("=" * 70)
            print(f'PAPER_TRADING_CHANNELS="{",".join(channel_ids)}"')
            print()
            
            # Also print with names for reference
            print("# Channel mapping:")
            for target in TARGET_CHANNELS:
                if target in found_channels:
                    print(f"# {found_channels[target]['id']} = {found_channels[target]['full_name']}")
        
        # List missing channels
        missing = [t for t in TARGET_CHANNELS if t not in found_channels]
        if missing:
            print("\n" + "=" * 70)
            print("⚠️ NOT FOUND - Please check channel names:")
            print("=" * 70)
            for channel in missing:
                print(f"   ❌ {channel}")
            
            print("\n💡 Tip: Searching all channels with similar names...")
            print("-" * 70)
            for target in missing:
                matches = []
                for name, cid in all_channels:
                    # Fuzzy matching for missing channels
                    target_words = set(target.lower().split())
                    name_words = set(name.lower().split())
                    
                    if target_words & name_words:  # If any word matches
                        matches.append((name, cid))
                
                if matches:
                    print(f"\n🔍 Possible matches for '{target}':")
                    for match_name, match_id in matches[:5]:  # Show top 5
                        print(f"   • {match_name} (ID: {match_id})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()
        print("\n" + "=" * 70)
        print("✅ Done!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(find_channel_ids())
