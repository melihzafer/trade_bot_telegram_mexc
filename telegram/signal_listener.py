"""
📡 Real-Time Signal Listener
Monitors Telegram channels for trading signals.
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, Set
from pathlib import Path

from telethon import TelegramClient, events
from telethon.tl.types import Message

from config.trading_config import SignalConfig
from trading.trading_engine import TradingEngine, Signal
from utils.logger import info, warn, error, success
from telegram.parser import parse_message


def parse_raw_message(text: str) -> Optional[dict]:
    """Wrapper for parse_message to work with raw text."""
    raw_obj = {
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "source": "telegram"
    }
    return parse_message(raw_obj)


class SignalListener:
    """Listens for trading signals from Telegram channels."""
    
    def __init__(self, trading_engine: TradingEngine):
        self.engine = trading_engine
        self.client: Optional[TelegramClient] = None
        
        # Deduplication tracking
        self.seen_signals: Set[str] = set()
        self.seen_window = timedelta(minutes=SignalConfig.DUPLICATE_WINDOW_MINUTES)
        self.last_cleanup = datetime.now()
        
        # Channel list
        self.channels = SignalConfig.CHANNELS
        
        info(f"📡 Signal Listener initialized for {len(self.channels)} channels")
    
    async def init_client(self):
        """Initialize Telegram client."""
        try:
            # Use credentials from config
            from utils.config import (
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH,
                TELEGRAM_PHONE_NUMBER,
            )
            
            self.client = TelegramClient(
                'signal_listener_session',
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH
            )
            
            await self.client.start(phone=TELEGRAM_PHONE_NUMBER)
            info("✅ Telegram client connected")
            
            # Verify channel access
            for channel in self.channels:
                try:
                    entity = await self.client.get_entity(channel)
                    success(f"✅ Access to {channel}: {entity.title}")
                except Exception as e:
                    error(f"❌ Cannot access {channel}: {e}")
        
        except Exception as e:
            error(f"❌ Failed to initialize Telegram client: {e}")
            raise
    
    def _generate_signal_hash(self, signal: Signal) -> str:
        """Generate unique hash for deduplication."""
        return f"{signal.symbol}_{signal.side}_{signal.timestamp[:16]}"
    
    def _is_duplicate(self, signal: Signal) -> bool:
        """Check if signal is duplicate."""
        signal_hash = self._generate_signal_hash(signal)
        
        # Cleanup old entries periodically
        now = datetime.now()
        if (now - self.last_cleanup) > timedelta(minutes=10):
            self.seen_signals.clear()
            self.last_cleanup = now
        
        # Check if seen
        if signal_hash in self.seen_signals:
            return True
        
        # Mark as seen
        self.seen_signals.add(signal_hash)
        return False
    
    async def process_message(self, message: Message):
        """Process incoming Telegram message."""
        try:
            # Parse message
            parsed = parse_raw_message(message.text)
            
            if not parsed:
                return  # Not a trading signal
            
            # Convert to Signal object
            signal = Signal(
                symbol=parsed.get('symbol'),
                side=parsed.get('side'),
                entry=parsed.get('entry'),
                tp=parsed.get('tp'),
                sl=parsed.get('sl'),
                timestamp=datetime.now().isoformat(),
                source=message.chat.title if hasattr(message.chat, 'title') else 'unknown'
            )
            
            # Validate signal
            if not signal.symbol or not signal.side:
                warn(f"⚠️ Invalid signal: {parsed}")
                return
            
            # Check for duplicate
            if SignalConfig.ENABLE_DUPLICATE_DETECTION:
                if self._is_duplicate(signal):
                    info(f"⏭️ Duplicate signal ignored: {signal.symbol}")
                    return
            
            # Add to engine
            success(f"📥 New signal: {signal.side} {signal.symbol} | TP: {signal.tp} | SL: {signal.sl}")
            self.engine.add_signal(signal)
        
        except Exception as e:
            error(f"❌ Failed to process message: {e}")
    
    async def listen(self):
        """Start listening for signals."""
        if not self.client:
            await self.init_client()
        
        info(f"👂 Listening for signals from {len(self.channels)} channels...")
        
        # Register event handler
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            await self.process_message(event.message)
        
        # Keep running
        await self.client.run_until_disconnected()
    
    async def fetch_recent_signals(self, limit: int = 50):
        """Fetch recent messages from channels (for initial sync)."""
        if not self.client:
            await self.init_client()
        
        info(f"🔄 Fetching last {limit} messages from channels...")
        
        total_processed = 0
        
        for channel in self.channels:
            try:
                entity = await self.client.get_entity(channel)
                messages = await self.client.get_messages(entity, limit=limit)
                
                info(f"📥 Processing {len(messages)} messages from {channel}")
                
                for message in reversed(messages):  # Process oldest first
                    if message.text:
                        await self.process_message(message)
                        total_processed += 1
                
            except Exception as e:
                error(f"❌ Failed to fetch from {channel}: {e}")
        
        success(f"✅ Processed {total_processed} historical messages")
    
    def start_background(self):
        """Start listener in background."""
        try:
            asyncio.run(self.listen())
        except KeyboardInterrupt:
            info("⏹️ Signal listener stopped by user")
        except Exception as e:
            error(f"❌ Signal listener error: {e}")
            raise


async def main():
    """Test signal listener."""
    # Create trading engine
    from config.trading_config import TRADING_MODE
    engine = TradingEngine(mode=TRADING_MODE)
    
    # Create listener
    listener = SignalListener(engine)
    
    # Fetch recent signals first
    await listener.fetch_recent_signals(limit=20)
    
    # Start listening
    await listener.listen()


if __name__ == "__main__":
    asyncio.run(main())
