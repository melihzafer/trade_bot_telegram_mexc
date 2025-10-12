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

        # Register message handler for configured channels
        @client.on(events.NewMessage(chats=TELEGRAM_CHANNELS))
        async def handle_new_message(event):
            """Handle incoming messages from monitored channels."""
            try:
                # Extract message data
                source = (
                    event.chat.username
                    if event.chat and hasattr(event.chat, "username")
                    else str(event.chat_id)
                )
                timestamp = event.message.date.isoformat()
                text = event.raw_text

                # Create message object
                msg = {"source": source, "ts": timestamp, "text": text}

                # Append to JSONL file
                with open(RAW_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")

                # Log receipt
                preview = text[:80].replace("\n", " ")
                info(f"📩 RAW >> {source} | {timestamp} | {preview}...")

            except Exception as e:
                error(f"Error handling message: {e}")

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
