"""
Historical message collector for Telegram channels.
Fetches last 500-1000 messages from all configured channels and saves to JSONL.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ChannelPrivateError, ChannelInvalidError

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_CHANNELS,
    DATA_DIR,
)
from utils.logger import info, warn, error, success

RAW_PATH = DATA_DIR / "signals_raw.jsonl"


def load_existing_message_ids():
    """
    Load all existing message IDs from signals_raw.jsonl to avoid duplicates.
    Returns set of (channel_id, message_id) tuples.
    """
    existing_ids = set()
    if RAW_PATH.exists():
        try:
            with open(RAW_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            channel_id = data.get('channel_id')
                            message_id = data.get('message_id')
                            if channel_id and message_id:
                                existing_ids.add((channel_id, message_id))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            warn(f"Error loading existing message IDs: {e}")
    
    info(f"📚 Loaded {len(existing_ids)} existing message IDs")
    return existing_ids


async def fetch_channel_history(client, channel_identifier, limit=1000, existing_ids=None):
    """
    Fetch historical messages from a single channel.
    
    Args:
        client: TelegramClient instance
        channel_identifier: Channel username (@channel) or ID (-100...)
        limit: Maximum number of messages to fetch (default: 1000)
        existing_ids: Set of existing (channel_id, message_id) tuples to skip
    
    Returns:
        List of message dictionaries
    """
    if existing_ids is None:
        existing_ids = set()
    
    messages = []
    
    try:
        # Convert string numeric IDs to integers for Telethon (same as collector.py)
        if isinstance(channel_identifier, str) and channel_identifier.lstrip('-').isdigit():
            channel_identifier = int(channel_identifier)
        
        # Get channel entity
        info(f"🔍 Fetching history from: {channel_identifier}")
        entity = await client.get_entity(channel_identifier)
        channel_id = entity.id
        channel_title = getattr(entity, 'title', channel_identifier)
        
        # Fetch messages
        async for message in client.iter_messages(entity, limit=limit):
            # Skip if no text
            if not message.text:
                continue
            
            # Skip if already exists
            if (channel_id, message.id) in existing_ids:
                continue
            
            # Create message data structure (same format as collector.py)
            message_data = {
                "timestamp": message.date.isoformat() if message.date else datetime.now().isoformat(),
                "channel_id": channel_id,
                "channel_title": channel_title,
                "message_id": message.id,
                "text": message.text,
                "raw": {
                    "sender_id": message.sender_id,
                    "fwd_from": str(message.fwd_from) if message.fwd_from else None,
                    "reply_to": message.reply_to_msg_id if message.reply_to else None,
                    "views": message.views,
                    "forwards": message.forwards,
                }
            }
            
            messages.append(message_data)
        
        success(f"✅ Fetched {len(messages)} new messages from {channel_title} (ID: {channel_id})")
        
    except ChannelPrivateError:
        error(f"❌ Channel is private and you don't have access: {channel_identifier}")
    except ChannelInvalidError:
        error(f"❌ Invalid channel identifier: {channel_identifier}")
    except Exception as e:
        error(f"❌ Error fetching from {channel_identifier}: {e}")
    
    return messages


async def save_messages_to_jsonl(messages):
    """
    Append messages to signals_raw.jsonl file.
    
    Args:
        messages: List of message dictionaries
    """
    if not messages:
        warn("⚠️ No messages to save")
        return
    
    try:
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Append messages to file
        with open(RAW_PATH, 'a', encoding='utf-8') as f:
            for msg in messages:
                json_line = json.dumps(msg, ensure_ascii=False)
                f.write(json_line + '\n')
            
            # Explicit flush and fsync for reliability
            f.flush()
            os.fsync(f.fileno())
        
        success(f"💾 Saved {len(messages)} messages to {RAW_PATH}")
        
    except Exception as e:
        error(f"❌ Error saving messages: {e}")


async def run_history_collector(limit_per_channel=1000):
    """
    Main function to collect historical messages from all configured channels.
    
    Args:
        limit_per_channel: Maximum number of messages to fetch per channel (default: 1000)
    """
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        error("❌ Telegram API credentials not configured. Check .env file.")
        return
    
    if not TELEGRAM_CHANNELS:
        error("❌ No Telegram channels configured. Check TELEGRAM_CHANNELS in .env.")
        return
    
    info("=" * 60)
    info("🚀 STARTING HISTORICAL MESSAGE COLLECTION")
    info("=" * 60)
    
    # Load existing message IDs to avoid duplicates
    existing_ids = load_existing_message_ids()
    
    # Create Telethon client (no session - will ask for code each time)
    info("📱 Creating fresh Telegram session (will ask for verification code)")
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        # Connect to Telegram and authenticate with phone
        phone = os.getenv("TELEGRAM_PHONE")
        if not phone:
            error("❌ TELEGRAM_PHONE not set in .env file")
            return
        
        info(f"📞 Starting authentication with phone: {phone}")
        await client.start(phone=phone)
        info("✅ Connected to Telegram successfully!")
        
        # Split channels list
        channels = [ch.strip() for ch in TELEGRAM_CHANNELS if ch.strip()]
        info(f"📡 Processing {len(channels)} channels...")
        
        all_messages = []
        
        # Fetch history from each channel
        for i, channel in enumerate(channels, 1):
            info(f"\n[{i}/{len(channels)}] Processing channel: {channel}")
            messages = await fetch_channel_history(
                client, 
                channel, 
                limit=limit_per_channel,
                existing_ids=existing_ids
            )
            
            if messages:
                all_messages.extend(messages)
                # Save after each channel (incremental saves)
                await save_messages_to_jsonl(messages)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Final summary
        info("\n" + "=" * 60)
        success(f"🎉 COLLECTION COMPLETE!")
        info(f"📊 Total new messages collected: {len(all_messages)}")
        info(f"📊 Total existing messages skipped: {len(existing_ids)}")
        info(f"📁 Data saved to: {RAW_PATH}")
        info("=" * 60)
        
    except Exception as e:
        error(f"❌ Fatal error during collection: {e}")
        raise
    
    finally:
        await client.disconnect()
        info("👋 Disconnected from Telegram")


if __name__ == "__main__":
    # Run with default limit of 1000 messages per channel
    # Change this number if you want more/fewer messages
    asyncio.run(run_history_collector(limit_per_channel=1000))
