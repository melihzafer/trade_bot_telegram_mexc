import asyncio
import os
from telethon import TelegramClient, events
from utils.logger import info, error, warn, success, debug

class TelegramSignalListener:
    """
    Listens to new messages from specific Telegram channels using Telethon.
    """
    def __init__(self, api_id, api_hash, phone_number, channels):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.channels = channels
        self.client = TelegramClient('session_chimera', self.api_id, self.api_hash)
        self.on_message_callback = None

    async def start(self, callback=None):
        """
        Starts the Telegram client and registers the event handler.
        """
        self.on_message_callback = callback
        
        info("📡 Telegram Client connecting...")
        try:
            await self.client.start(phone=self.phone_number)
            
            if not await self.client.is_user_authorized():
                info("🔐 Authorization required. Please check your console/phone.")
                await self.client.send_code_request(self.phone_number)
                # Note: In a non-interactive script, this might hang if auth is needed.
                # Assuming session is already saved or interactive terminal.
            
            success("✅ Telegram Client connected")
            
            # Register event handler for New Messages
            @self.client.on(events.NewMessage(chats=self.channels))
            async def handler(event):
                if self.on_message_callback:
                    await self.on_message_callback(event)
            
            info(f"👂 Listening to channels: {', '.join(str(c) for c in self.channels)}")
            
            # Keep the client running (if run directly, but here main_loop handles loop)
            # await self.client.run_until_disconnected() 
            
        except Exception as e:
            error(f"❌ Telegram Connection Error: {e}")
            raise e

    async def stop(self):
        """Disconnects the client."""
        if self.client:
            await self.client.disconnect()
            info("🔌 Telegram Client disconnected")