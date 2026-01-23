"""
📥 Signal Collection Script
Simple CLI for collecting signals from Telegram channels in real-time or historically.
"""
import asyncio
import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, BACKTEST_CHANNELS, DATA_DIR
from utils.logger import info, warn, error, success
from telegram.parser import parse_message

try:
    from parsers.multi_ai_parser import MultiAIParser
except ImportError:
    MultiAIParser = None
    warn("Multi AI Parser not available - install openai package for AI-powered parsing")


# Global lock for thread-safe file writing
_file_lock = asyncio.Lock()


async def collect_realtime(output_file: Path, parse_signals: bool = False):
    """
    Collect signals in real-time from Telegram channels.
    
    Args:
        output_file: Path to save raw or parsed signals
        parse_signals: If True, parse and filter signals before saving
    """
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        error("Telegram API credentials not configured. Check .env file.")
        return
    
    if not BACKTEST_CHANNELS:
        error("No Telegram channels configured. Set BACKTEST_CHANNELS in .env")
        return
    
    phone = os.getenv("TELEGRAM_PHONE")
    if not phone:
        error("TELEGRAM_PHONE not set in .env file")
        return
    
    info("=" * 70)
    info("REAL-TIME SIGNAL COLLECTION")
    info("=" * 70)
    info(f"Mode: {'PARSED' if parse_signals else 'RAW'}")
    info(f"Output: {output_file}")
    info(f"Channels: {len(BACKTEST_CHANNELS)}")
    
    # Create Telegram client
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        # Authenticate
        info(f"Connecting to Telegram with phone: {phone}")
        await client.start(phone=phone)
        success(f"Connected successfully!")
        
        # Resolve channel entities
        info("Resolving channel entities...")
        resolved_channels = []
        for ch in BACKTEST_CHANNELS:
            try:
                if isinstance(ch, str) and ch.lstrip('-').isdigit():
                    ch = int(ch)
                
                entity = await client.get_entity(ch)
                resolved_channels.append(entity)
                channel_name = getattr(entity, "title", getattr(entity, "username", str(ch)))
                info(f"  ✓ {channel_name}")
            except Exception as e:
                warn(f"  ✗ Could not resolve {ch}: {e}")
        
        if not resolved_channels:
            error("No channels could be resolved. Check your configuration.")
            return
        
        success(f"Resolved {len(resolved_channels)}/{len(BACKTEST_CHANNELS)} channels")
        
        # Message counter
        message_count = [0]  # Use list for closure
        
        # Register message handler
        @client.on(events.NewMessage(chats=resolved_channels))
        async def handle_message(event):
            """Handle incoming messages."""
            try:
                chat = await event.get_chat() if event.chat is None else event.chat
                source = getattr(chat, "username", None) or getattr(chat, "title", None) or str(event.chat_id)
                timestamp = event.message.date.isoformat()
                text = event.raw_text or ""
                
                if not text.strip():
                    return
                
                # Prepare message data
                msg_data = {
                    "source": source,
                    "timestamp": timestamp,
                    "text": text
                }
                
                # Parse if requested
                if parse_signals:
                    parsed = parse_message(msg_data)
                    if not parsed or not parsed.get("symbol"):
                        return  # Skip non-signal messages
                    
                    msg_data = {
                        "symbol": parsed["symbol"],
                        "side": parsed["side"],
                        "entry": parsed.get("entry"),
                        "tp": parsed.get("tp"),
                        "sl": parsed.get("sl"),
                        "timestamp": timestamp,
                        "source": source
                    }
                
                # Save to file (thread-safe)
                async with _file_lock:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(msg_data, ensure_ascii=False) + "\n")
                        f.flush()
                
                message_count[0] += 1
                preview = text[:60].replace("\n", " ")
                info(f"[{message_count[0]}] {source} | {preview}...")
            
            except Exception as e:
                error(f"Error handling message: {e}")
        
        info("\n" + "=" * 70)
        success("LISTENING FOR SIGNALS (Press Ctrl+C to stop)")
        info("=" * 70)
        
        # Run until disconnected
        await client.run_until_disconnected()
    
    except KeyboardInterrupt:
        info("\nStopping collector...")
    except Exception as e:
        error(f"Collection error: {e}")
    finally:
        await client.disconnect()
        success(f"\nCollection complete! Saved {message_count[0]} messages to {output_file}")


async def collect_historical(output_file: Path, limit: int = 100, parse_signals: bool = False):
    """
    Collect historical messages from Telegram channels.
    
    Args:
        output_file: Path to save signals
        limit: Number of messages to fetch per channel
        parse_signals: If True, parse and filter signals
    """
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        error("Telegram API credentials not configured. Check .env file.")
        return
    
    if not BACKTEST_CHANNELS:
        error("No Telegram channels configured. Set BACKTEST_CHANNELS in .env")
        return
    
    phone = os.getenv("TELEGRAM_PHONE")
    if not phone:
        error("TELEGRAM_PHONE not set in .env file")
        return
    
    info("=" * 70)
    info("HISTORICAL SIGNAL COLLECTION")
    info("=" * 70)
    info(f"Mode: {'PARSED' if parse_signals else 'RAW'}")
    info(f"Messages per channel: {limit}")
    info(f"Output: {output_file}")
    
    # Initialize AI parser if parsing enabled (Ollama-only for backtest)
    ai_parser = None
    if parse_signals and MultiAIParser:
        try:
            ai_parser = MultiAIParser(ollama_only=True)  # Backtest uses Ollama only
            success("Ollama-only AI Parser initialized (for backtest)")
        except Exception as e:
            warn(f"AI Parser unavailable: {e}")
            info("Will use regex-only parsing")
    
    # Create client
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    all_messages = []
    stats = {"regex": 0, "ai": 0, "skipped": 0, "total_checked": 0}
    
    try:
        # Connect
        await client.start(phone=phone)
        success("Connected to Telegram")
        
        # Collect from each channel
        for channel in BACKTEST_CHANNELS:
            try:
                info(f"\nCollecting from: {channel}")
                
                # Resolve entity
                if isinstance(channel, str) and channel.lstrip('-').isdigit():
                    channel = int(channel)
                
                entity = await client.get_entity(channel)
                channel_name = getattr(entity, "title", getattr(entity, "username", str(channel)))
                
                # Fetch messages
                count = 0
                async for message in client.iter_messages(entity, limit=limit):
                    if message.text:
                        stats["total_checked"] += 1
                        
                        # Quick filter: skip messages that clearly aren't signals
                        text_lower = message.text.lower()
                        if not any(keyword in text_lower for keyword in [
                            'long', 'short', 'buy', 'sell', 'al', 'sat',
                            'entry', 'giriş', 'giris', 'tp', 'target', 'hedef',
                            'sl', 'stop', 'zarar', 'usdt', 'btc', 'eth'
                        ]):
                            stats["skipped"] += 1
                            continue
                        
                        msg_data = {
                            "source": channel_name,
                            "timestamp": message.date.isoformat(),
                            "text": message.text
                        }
                        
                        # Parse if requested
                        if parse_signals:
                            # ALWAYS try regex first (fast, no rate limits)
                            parsed = parse_message(msg_data)
                            
                            if parsed and parsed.get("symbol"):
                                # Regex success!
                                stats["regex"] += 1
                            # Only try AI if regex completely failed AND AI parser available
                            elif ai_parser:
                                try:
                                    ai_result = await ai_parser.parse_signal(message.text)
                                    if ai_result.get("signal") != False and ai_result.get("symbol"):
                                        # Convert AI format to standard format
                                        parsed = {
                                            "symbol": ai_result["symbol"],
                                            "side": ai_result.get("side", "LONG").upper(),
                                            "entry": ai_result.get("entry", [0])[0] if ai_result.get("entry") else 0,
                                            "tp": ai_result.get("tp", [0])[0] if ai_result.get("tp") else 0,
                                            "sl": ai_result.get("sl", 0),
                                            "leverage": ai_result.get("leverage", 1),
                                            "confidence": ai_result.get("confidence", 0.5),
                                            "parsed_by": "ai"
                                        }
                                        stats["ai"] += 1
                                        info(f"   AI parsed: {parsed['symbol']} {parsed['side']}")
                                    else:
                                        parsed = None
                                        stats["skipped"] += 1
                                except Exception as e:
                                    # AI failed (rate limit, timeout, etc.) - just skip
                                    error_msg = str(e).lower()
                                    if 'rate limit' in error_msg or '429' in error_msg:
                                        warn(f"   AI rate limit hit - skipping AI for remaining messages")
                                        ai_parser = None  # Disable AI for rest of collection
                                    else:
                                        warn(f"   AI error: {e}")
                                    parsed = None
                                    stats["skipped"] += 1
                            else:
                                # No AI parser or already disabled
                                parsed = None
                                stats["skipped"] += 1
                            
                            # Skip if still no valid signal
                            if not parsed or not parsed.get("symbol"):
                                continue
                            
                            msg_data = {
                                "symbol": parsed["symbol"],
                                "side": parsed["side"],
                                "entry": parsed.get("entry"),
                                "tp": parsed.get("tp"),
                                "sl": parsed.get("sl"),
                                "timestamp": msg_data["timestamp"],
                                "source": channel_name
                            }
                        
                        all_messages.append(msg_data)
                        count += 1
                
                success(f"  Collected {count} messages")
            
            except Exception as e:
                error(f"  Failed to collect from {channel}: {e}")
        
        # Save all messages
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            for msg in all_messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        
        success(f"\nTotal: {len(all_messages)} messages from {len(BACKTEST_CHANNELS)} channels")
        success(f"Saved to: {output_file}")
        
        # Show parsing stats if applicable
        if parse_signals and stats["total_checked"] > 0:
            info("\nParsing Statistics:")
            info(f"  Total messages checked: {stats['total_checked']}")
            info(f"  Parsed by regex: {stats['regex']}")
            info(f"  Parsed by AI: {stats['ai']}")
            info(f"  Skipped: {stats['skipped']}")
            success_rate = ((stats['regex'] + stats['ai']) / stats['total_checked'] * 100) if stats['total_checked'] > 0 else 0
            info(f"  Success rate: {success_rate:.1f}%")
            
            # Show AI provider stats if available
            if ai_parser and hasattr(ai_parser, 'get_stats'):
                provider_stats = ai_parser.get_stats()
                if provider_stats:
                    info("\nAI Provider Statistics:")
                    for name, data in provider_stats.items():
                        status = "ACTIVE" if data['enabled'] else "DISABLED"
                        info(f"  {name} ({data['model']}): {status} - {data['success_count']} success, {data['failure_count']} failures")
    
    except Exception as e:
        error(f"Collection error: {e}")
    finally:
        await client.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Collect trading signals from Telegram channels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect real-time raw signals (default)
  python collect_signals.py
  
  # Collect real-time and auto-parse signals
  python collect_signals.py --parse
  
  # Collect historical messages (last 500 per channel)
  python collect_signals.py --mode historical --limit 500
  
  # Collect and parse historical signals
  python collect_signals.py --mode historical --limit 1000 --parse
  
  # Custom output file
  python collect_signals.py --output data/my_signals.jsonl
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['realtime', 'historical'],
        default='realtime',
        help='Collection mode (default: realtime)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Messages per channel for historical mode (default: 100)'
    )
    parser.add_argument(
        '--parse',
        action='store_true',
        help='Parse signals and filter valid ones only'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: data/signals_raw.jsonl or data/signals_parsed.jsonl)'
    )
    
    args = parser.parse_args()
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        if args.parse:
            output_file = DATA_DIR / "signals_parsed.jsonl"
        else:
            output_file = DATA_DIR / "signals_raw.jsonl"
    
    # Run collection
    if args.mode == 'realtime':
        asyncio.run(collect_realtime(output_file, args.parse))
    else:
        asyncio.run(collect_historical(output_file, args.limit, args.parse))


if __name__ == "__main__":
    main()
