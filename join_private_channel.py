# join_private_channel.py
"""
Join private Telegram channels using invite links.
After joining, run list_channel.py again to get the channel IDs.
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")

# Add your private channel invite links here
# Format: "ABC123XYZ" from https://t.me/+ABC123XYZ
# Or: "ABC123XYZ" from https://t.me/joinchat/ABC123XYZ
INVITE_HASHES = [
    # "ABC123XYZ",  # Example
    # "DEF456ABC",  # Example
]

async def main():
    if not INVITE_HASHES:
        print("⚠️  No invite hashes configured!")
        print("📝 Edit this file and add invite hashes to INVITE_HASHES list")
        print("\nExample:")
        print('INVITE_HASHES = [')
        print('    "ABC123XYZ",  # from https://t.me/+ABC123XYZ')
        print('    "DEF456ABC",  # from https://t.me/joinchat/DEF456ABC')
        print(']')
        return

    client = TelegramClient("session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    print("\n" + "="*80)
    print("📱 JOINING PRIVATE CHANNELS")
    print("="*80 + "\n")
    
    for invite_hash in INVITE_HASHES:
        try:
            print(f"🔄 Attempting to join: {invite_hash}")
            result = await client(ImportChatInviteRequest(invite_hash))
            
            # Get channel info
            chat = result.chats[0] if result.chats else None
            if chat:
                print(f"✅ Joined: {chat.title}")
                print(f"   ID: {chat.id}")
                print(f"   Type: {'Megagroup' if getattr(chat, 'megagroup', False) else 'Channel'}")
            else:
                print(f"✅ Joined successfully (no chat info)")
            print("-" * 80)
            
        except Exception as e:
            if "INVITE_HASH_EXPIRED" in str(e):
                print(f"❌ Invite link expired: {invite_hash}")
            elif "USER_ALREADY_PARTICIPANT" in str(e):
                print(f"✅ Already a member: {invite_hash}")
            else:
                print(f"❌ Error joining {invite_hash}: {e}")
            print("-" * 80)
    
    print("\n💡 Next steps:")
    print("1. Run: python list_channel.py")
    print("2. Find the newly joined channels in channels.csv")
    print("3. Copy their IDs to .env TELEGRAM_CHANNELS")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
