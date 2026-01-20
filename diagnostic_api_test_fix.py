import asyncio
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv

load_dotenv()

async def test_mexc_force_connection():
    print("🕵️ MEXC Connectivity Fix Attempt...\n")
    
    api_key = os.getenv("MEXC_API_KEY")
    api_secret = os.getenv("MEXC_API_SECRET")

    # YÖNTEM: Varsayılan URL'leri manuel olarak değiştiriyoruz
    # Bazen ana sunucu engellidir ama bu çalışır.
    exchange = ccxt.mexc({
        'apiKey': api_key,
        'secret': api_secret,
        'options': {
            'defaultType': 'future', 
            'adjustForTimeDifference': True
        },
        'urls': {
            'api': {
                'public': 'https://contract.mexc.com',
                'private': 'https://contract.mexc.com',
            }
        },
        'enableRateLimit': True
    })

    try:
        print("1️⃣  Testing Forced Connection (contract.mexc.com)...")
        # Sadece sunucu zamanını çekmeyi deneyelim (En basit işlem)
        time = await exchange.fetch_time()
        print(f"✅ Connection Successful! Server Time: {time}")
        
        print("2️⃣  Checking Markets...")
        await exchange.load_markets()
        print("✅ Markets Loaded!")

        if 'BTC/USDT:USDT' in exchange.markets:
             print("🎉 SUCCESS! Futures API is accessible via override.")
        
    except Exception as e:
        print(f"❌ Still Failed: {e}")
        print("\n--- DIAGNOSIS ---")
        print("Bu yöntem de çalışmadıysa, sorun %100 IP adresinle ilgilidir.")
        print("Lütfen bir VPN açarak (Almanya, Hollanda vb.) tekrar dene.")
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_mexc_force_connection())