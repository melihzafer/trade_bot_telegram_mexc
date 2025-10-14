"""
Telegram multi-channel collector using Telethon.
Listens to configured channels and saves raw messages to JSONL.
"""
import asyncio
import json
import base64
import os
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from utils.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    TELEGRAM_CHANNELS,
    DATA_DIR,
)
from utils.logger import info, warn, error

RAW_PATH = DATA_DIR / "signals_raw.jsonl"


# Global lock for file writing (thread-safe)
_file_lock = asyncio.Lock()

async def run_collector():
    """
    Main collector function. Connects to Telegram and listens to configured channels.
    Saves raw messages to JSONL file (append-only).
    """
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        error("Telegram API credentials not configured. Check .env file.")
        return

    if not TELEGRAM_CHANNELS:
        warn("No Telegram channels configured. Check TELEGRAM_CHANNELS in .env.")
        return

    # Check for session string (for Railway deployment)
    session_string = os.getenv("TELEGRAM_SESSION_STRING", "")
    
    # Create Telethon client
    if session_string:
        info("📱 Using session string from environment variable")
        client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    else:
        info("📱 Using local session file")
        client = TelegramClient("session", TELEGRAM_API_ID, TELEGRAM_API_HASH)

    try:
        # Start client with phone number
        await client.start(phone=TELEGRAM_PHONE)
        info(f"✅ Connected to Telegram as {TELEGRAM_PHONE}")

        # Resolve all channel entities first (handles both @username and -100... IDs)
        info("🔍 Resolving channel entities...")
        resolved_channels = []
        for ch in TELEGRAM_CHANNELS:
            try:
                # Convert string numeric IDs to integers for Telethon
                if isinstance(ch, str) and ch.lstrip('-').isdigit():
                    ch = int(ch)
                
                entity = await client.get_entity(ch)
                resolved_channels.append(entity)
                channel_name = getattr(entity, "title", getattr(entity, "username", str(ch)))
                info(f"   ✅ {channel_name} ({ch})")
            except Exception as e:
                warn(f"   ⚠️  Could not resolve channel {ch}: {e}")
        
        if not resolved_channels:
            error("No channels could be resolved. Check TELEGRAM_CHANNELS in .env")
            return
        
        info(f"📡 Successfully resolved {len(resolved_channels)}/{len(TELEGRAM_CHANNELS)} channels")

        # Register message handler for resolved channels
        @client.on(events.NewMessage(chats=resolved_channels))
        async def handle_new_message(event):
            """Handle incoming messages from monitored channels."""
            try:
                chat = await event.get_chat() if event.chat is None else event.chat
                source = getattr(chat, "username", None) or getattr(chat, "title", None) or str(event.chat_id)
                timestamp = event.message.date.isoformat()
                text = event.raw_text or ""

                if not text.strip():
                    return  # Skip empty/non-text messages

                msg = {"source": source, "ts": timestamp, "text": text}

                # Thread-safe file writing with explicit flush
                try:
                    async with _file_lock:
                        # Ensure data directory exists
                        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(RAW_PATH, "a", encoding="utf-8", buffering=1) as f:
                            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
                            f.flush()  # Force write to disk
                            os.fsync(f.fileno())  # Ensure OS writes to disk
                    
                    preview = text[:80].replace("\n", " ")
                    info(f"📩 RAW >> {source} | {timestamp} | {preview}...")
                except Exception as write_error:
                    error(f"⚠️ File write failed: {write_error} | Path: {RAW_PATH}")

            except Exception as e:
                error(f"⚠️ Collector write failed: {e}")

        info(f"👂 Listening to channels: {', '.join(TELEGRAM_CHANNELS)}")
        info(f"💾 Saving raw messages to: {RAW_PATH}")

        # Run until disconnected
        await client.run_until_disconnected()

    except Exception as e:
        error(f"Telegram collector error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Run collector standalone for testing
    asyncio.run(run_collector())
