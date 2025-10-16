"""
Test which channels from .env are accessible
"""
import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')
TELEGRAM_CHANNELS = os.getenv('TELEGRAM_CHANNELS', '').split(',')

async def main():
    print("\n" + "="*80)
    print("🔍 TESTING CHANNEL ACCESSIBILITY")
    print("="*80 + "\n")
    
    # Create fresh session (will ask for code)
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE)
        print(f"✅ Connected to Telegram as {PHONE}\n")
        
        # Test each channel
        total = len(TELEGRAM_CHANNELS)
        accessible = []
        inaccessible = []
        
        print(f"📡 Testing {total} channels...\n")
        
        for i, ch in enumerate(TELEGRAM_CHANNELS, 1):
            ch = ch.strip()
            if not ch:
                continue
                
            try:
                # Convert string numeric IDs to integers for Telethon
                if isinstance(ch, str) and ch.lstrip('-').isdigit():
                    ch_id = int(ch)
                else:
                    ch_id = ch
                
                entity = await client.get_entity(ch_id)
                channel_name = getattr(entity, "title", getattr(entity, "username", str(ch)))
                
                print(f"[{i:3d}/{total}] ✅ {channel_name[:50]:50s} | {ch}")
                accessible.append({
                    'id': ch,
                    'name': channel_name,
                    'username': getattr(entity, "username", "PRIVATE")
                })
                
            except Exception as e:
                error_msg = str(e)
                if "ChannelPrivateError" in error_msg:
                    reason = "PRIVATE/KICKED"
                elif "ChannelInvalidError" in error_msg:
                    reason = "INVALID ID"
                elif "UsernameInvalidError" in error_msg:
                    reason = "INVALID USERNAME"
                else:
                    reason = error_msg[:30]
                
                print(f"[{i:3d}/{total}] ❌ {ch:50s} | {reason}")
                inaccessible.append({
                    'id': ch,
                    'reason': reason
                })
        
        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80 + "\n")
        print(f"✅ Accessible:   {len(accessible):3d} / {total} ({len(accessible)/total*100:.1f}%)")
        print(f"❌ Inaccessible: {len(inaccessible):3d} / {total} ({len(inaccessible)/total*100:.1f}%)")
        
        if inaccessible:
            print("\n" + "="*80)
            print("❌ CHANNELS TO REMOVE FROM .ENV")
            print("="*80 + "\n")
            for ch in inaccessible:
                print(f"   {ch['id']:20s} | {ch['reason']}")
        
        # Generate clean channel list
        if accessible:
            print("\n" + "="*80)
            print("✅ CLEAN CHANNEL LIST (copy to .env)")
            print("="*80 + "\n")
            clean_ids = [ch['id'] for ch in accessible]
            clean_line = ','.join(clean_ids)
            print(f"TELEGRAM_CHANNELS={clean_line}")
            
            # Save to file
            with open('accessible_channels.txt', 'w', encoding='utf-8') as f:
                f.write(f"Accessible Channels: {len(accessible)}\n\n")
                for ch in accessible:
                    f.write(f"{ch['id']:20s} | {ch['name'][:50]:50s} | @{ch['username']}\n")
                f.write(f"\n{'='*80}\n")
                f.write(f".ENV FORMAT:\n")
                f.write(f"{'='*80}\n\n")
                f.write(f"TELEGRAM_CHANNELS={clean_line}\n")
            
            print(f"\n✅ Saved to: accessible_channels.txt")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
