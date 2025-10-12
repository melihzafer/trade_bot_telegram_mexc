"""
Export Telegram session to Railway environment variable.
Run this locally after successful authentication.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")

if not API_ID or not API_HASH:
    print("❌ TELEGRAM_API_ID or TELEGRAM_API_HASH not found in .env")
    exit(1)

print("🔐 Exporting Telegram session...")
print("This will use your existing session file or create a new one.\n")

# Use existing session or create new
with TelegramClient("session", API_ID, API_HASH) as client:
    session_string = StringSession.save(client.session)
    
    print("✅ Session exported successfully!")
    print("\n" + "="*80)
    print("📋 Add this to Railway Environment Variables:")
    print("="*80)
    print(f"\nTELEGRAM_SESSION_STRING={session_string}")
    print("\n" + "="*80)
    print("\n💡 Steps:")
    print("1. Copy the line above")
    print("2. Go to Railway Dashboard → Variables")
    print("3. Add new variable: TELEGRAM_SESSION_STRING")
    print("4. Paste the value")
    print("5. Redeploy the service")
    print("\n✨ Your bot will work without authentication prompts!")
