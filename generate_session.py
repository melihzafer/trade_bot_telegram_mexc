import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 28115427
api_hash = 'dee3e8cdaf87c416dabd1db1a224cee1'
phone = '+359892958483'  # From .env

async def main():
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print(f'Sending code to {phone}...')
        await client.send_code_request(phone)
        code = input('Enter the code you received: ')
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            print(f"Error: {e}")
            password = input('Enter your 2FA password (if enabled): ')
            await client.sign_in(password=password)
    
    print("\n=== YOUR NEW SESSION STRING ===")
    print(client.session.save())
    print("===============================\n")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
