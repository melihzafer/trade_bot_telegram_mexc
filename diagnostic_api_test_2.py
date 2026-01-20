import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

# Load keys
load_dotenv()

async def test_mexc_futures_capability():
    print("🕵️ MEXC Futures API Diagnostic Starting...\n")
    
    api_key = os.getenv("MEXC_API_KEY")
    api_secret = os.getenv("MEXC_API_SECRET")
    
    if not api_key or "your_key" in api_key:
        print("❌ ERROR: API Key not set in .env file!")
        return

    # Initialize CCXT for MEXC Futures (Contract)
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'options': {
            'defaultType': 'future',  # <--- CRITICAL: Requesting Futures API
        },
        'enableRateLimit': True
    })

    try:
        print("1️⃣  Testing Connection...")
        await exchange.load_markets()
        print("✅ Connection Successful!")
        
        print("\n2️⃣  Checking Market Type...")
        # Check if BTC/USDT:USDT (Futures symbol) exists
        if 'BTC/USDT:USDT' in exchange.markets:
            print("✅ Futures Markets Loaded (BTC/USDT:USDT found)")
        else:
            print("⚠️ WARNING: Futures symbols not found. Defaults might be SPOT.")

        print("\n3️⃣  Checking Permissions & Balance...")
        balance = await exchange.fetch_balance()
        
        # Futures balance structure is different from Spot
        usdt_free = balance.get('USDT', {}).get('free', 0)
        total_equity = balance.get('total', {}).get('USDT', 0)
        
        print(f"💰 Futures Wallet Balance: {usdt_free} USDT")
        print(f"📊 Total Equity: {total_equity} USDT")

        if usdt_free == 0 and total_equity == 0:
            print("\n⚠️  NOTE: Balance is 0. Make sure you transferred funds to 'Futures Account'!")
        else:
            print("✅ Balance check passed.")

        print("\n4️⃣  Simulating Order Check (Dry Run)...")
        # Just checking if we can fetch open orders (requires Trade permission)
        try:
            await exchange.fetch_open_orders('BTC/USDT:USDT')
            print("✅ Trade Permissions likely ACTIVE (Fetched open orders)")
        except Exception as e:
            print(f"❌ Trade Permission Error: {e}")
            print("   -> Check if 'Futures Trading' is enabled in API Management settings on MEXC website.")

    except ccxt.AuthenticationError:
        print("❌ Authentication Failed! Check your API Key and Secret.")
    except ccxt.PermissionDenied:
        print("❌ Permission Denied! This API key might not have Futures access.")
    except ccxt.ExchangeNotAvailable:
        print("❌ Exchange Not Available (Maintenance or Geoblocking).")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    finally:
        await exchange.close()
        print("\n🕵️ Diagnostic Complete.")

if __name__ == "__main__":
    asyncio.run(test_mexc_futures_capability())