import asyncio
import os
import sys
import traceback
from datetime import datetime, time, timezone

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram.signal_listener import TelegramSignalListener
from parsers.enhanced_parser import EnhancedParser
from trading.trading_engine import TradingEngine
from trading.risk_manager import RiskSentinel
from reporting.notifier import TelegramNotifier
from utils.logger import info, error, warn, success, debug
from config.trading_config import TRADING_MODE

# Global components
notifier = TelegramNotifier()
sentinel = RiskSentinel(initial_equity=0.0) 
engine = TradingEngine(mode=TRADING_MODE)
parser = EnhancedParser()

# --- DÜZELTME BURADA BAŞLIYOR ---
# Kanal listesini .env'den al ve ID'leri sayıya (int) çevir
channels_env = os.getenv("TELEGRAM_CHANNELS", "")
raw_channels = [c.strip() for c in channels_env.split(",") if c.strip()]
channels = []

for c in raw_channels:
    # Eğer -100 ile başlıyorsa veya tamamen sayıysa Integer yap
    if c.startswith("-") or c.isdigit():
        try:
            channels.append(int(c))
        except ValueError:
            channels.append(c) # Çevrilemezse olduğu gibi kalsın
    else:
        channels.append(c) # @username ise olduğu gibi kalsın

# Loglayıp kontrol edelim
info(f"📋 Parsed Channels: {channels}")
# --- DÜZELTME BURADA BİTİYOR ---

listener = TelegramSignalListener(
    api_id=os.getenv("TELEGRAM_API_ID"),
    api_hash=os.getenv("TELEGRAM_API_HASH"),
    phone_number=os.getenv("TELEGRAM_PHONE"),
    channels=channels 
)

async def main_loop():
    """The Infinite Autonomous Loop."""
    info("🔥 CHIMERA AUTONOMOUS SYSTEM STARTING...")
    
    # 1. Start Components
    await notifier.start()
    await engine.start()
    
    if engine.mode == "live":
        balance = await engine.exchange.fetch_balance()
        current_equity = balance['total']['USDT']
        sentinel.update_equity(current_equity)
    else:
        sentinel.update_equity(engine.portfolio.get_equity())

    await notifier.send_startup_alert(TRADING_MODE)
    success("✅ All Systems Operational. Waiting for signals...")

    # Listener'ı başlat
    await listener.start(callback=process_message)

    last_report_date = datetime.now(timezone.utc).date()

    try:
        while True:
            await asyncio.sleep(10)

            # Daily Reporting Check
            current_date = datetime.now(timezone.utc).date()
            if current_date > last_report_date:
                stats = {
                    "pnl": sentinel.daily_pnl,
                    "drawdown": 0.0,
                    "trade_count": len(engine.portfolio.get_all_positions()),
                    "wins": 0, "losses": 0
                }
                await notifier.send_daily_report(stats)
                sentinel.update_equity(sentinel.equity) 
                last_report_date = current_date

    except Exception as e:
        error(f"❌ CRITICAL LOOP CRASH: {e}")
        error(traceback.format_exc())
        await notifier.send_risk_alert("SYSTEM CRASH", str(e))
        raise 

async def process_message(event):
    """
    Callback function triggering on EVERY new message.
    """
    try:
        text = event.raw_text
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Unknown')
        
        # LOG: Gelen mesajı ekrana bas (Satır sonlarını temizle)
        clean_text = text.replace('\n', ' ')[:100]
        info(f"📩 MSG from [{chat_title}]: {clean_text}...")

        # 2. Parse (Hybrid)
        parsed = await parser.parse(text)
        
        if not parsed.is_valid():
            # debug(f"❌ NO SIGNAL: {clean_text}") 
            return 

        # 3. Sinyal Yakalandı!
        success(f"✅ SIGNAL DETECTED: {parsed.symbol} {parsed.side}")
        
        # 4. Risk Validation
        current_positions = engine.portfolio.get_all_positions()
        validation = sentinel.validate_signal(parsed.symbol, parsed.side, current_positions)
        
        if not validation.valid:
            warn(f"🛡️ Risk Block: {validation.reason}")
            await notifier.send_trade_notification(parsed, False, validation.reason)
            return

        # 5. Execution
        success_exec = await engine.execute_parsed_signal(parsed)
        
        # 6. Notification
        if success_exec:
            await notifier.send_trade_notification(parsed, True)
            if engine.mode == "live":
                bal = await engine.exchange.fetch_balance()
                sentinel.update_equity(bal['total']['USDT'])

    except Exception as e:
        error(f"⚠️ Error processing message: {e}")
        traceback.print_exc()

async def run_resilient():
    """Wrapper to restart the bot on failure."""
    while True:
        try:
            await main_loop()
        except KeyboardInterrupt:
            warn("🛑 Manual Stop Received.")
            break
        except Exception as e:
            error(f"🔄 System restarting in 10s due to: {e}")
            await asyncio.sleep(10)
        finally:
            await notifier.stop()
            await engine.stop()

if __name__ == "__main__":
    try:
        asyncio.run(run_resilient())
    except KeyboardInterrupt:
        pass