"""
Filter crypto-related channels from channels.csv
"""
import csv
import re

# Kripto ile ilgili keywords (case-insensitive)
CRYPTO_KEYWORDS = [
    'kripto', 'crypto', 'bitcoin', 'btc', 'binance', 'mexc', 'okx', 'bitget',
    'bingx', 'hyperliquid', 'backpack', 'ranger', 'aster',
    'coin', 'trading', 'signal', 'futures', 'spot', 'pump',
    'whale', 'trader', 'altcoin', 'nft', 'airdrop',
    'borsa', 'para mühendisi', 'fed. russian', 'fat pig',
    'wolfx', 'prime trading', 'gorilla', 'devil', 'bulls',
    'inner circle', 'planet', 'knights', 'king crypto',
    'deep web kripto', 'neon', 'sihirbaz', 'delisi', 'star',
    'test', 'attila', 'deep', 'simpsons', 'capris', 'buğra',
    'kurmay', 'levent', 'genç trader', 'donanım', 'kampi',
    'pratik', 'kralı', 'goat', 'rsi alert', 'price change',
    'marduk', 'chief', 'rush', 'waves', 'four', 'güler trade',
    'profit', 'just profit', 'market killer', 'capchain',
    'green rock', 'amiral', 'bp trades', 'halil güneş',
    'savaş çüm', 'elite', 'oscar crypto', 'benz crypto',
    'black crypto', 'zwolfe', 'donanım', 'işlem'
]

# Alakasız keywords (exclude)
EXCLUDE_KEYWORDS = [
    'bet', 'slot', 'casino', 'ifşa', 'beleş', 'tips',
    'openbullet', 'config', 'mine', 'mining', 'sohbet',
    'topluluk', 'chat', 'army', 'ailesi', 'amg',
    'academy', 'putenca', 'promo', 'stanisław',
    'cosma', 'asdasd', 'dwk yedek', 'vip altcoin signals',
    'crypto 100', 'martíng', 'trippa'
]

def is_crypto_channel(title):
    """Check if channel is crypto-related"""
    title_lower = title.lower()
    
    # Exclude list check first
    for exclude in EXCLUDE_KEYWORDS:
        if exclude in title_lower:
            return False
    
    # Check for crypto keywords
    for keyword in CRYPTO_KEYWORDS:
        if keyword in title_lower:
            return True
    
    return False

def main():
    crypto_channels = []
    
    with open('channels.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['title']
            channel_id = row['id']
            username = row['username']
            
            if is_crypto_channel(title):
                crypto_channels.append({
                    'id': channel_id,
                    'title': title,
                    'username': username
                })
    
    # Sort by title
    crypto_channels.sort(key=lambda x: x['title'])
    
    print(f"\n{'='*80}")
    print(f"🔍 FILTERED CRYPTO CHANNELS")
    print(f"{'='*80}\n")
    
    print(f"📊 Total: {len(crypto_channels)} channels\n")
    
    # Print list
    for i, channel in enumerate(crypto_channels, 1):
        print(f"{i:2d}. {channel['title'][:50]:50s} | ID: {channel['id']}")
    
    # Generate .env format
    print(f"\n{'='*80}")
    print(f"📝 .ENV FORMAT (copy this)")
    print(f"{'='*80}\n")
    
    channel_ids = [ch['id'] for ch in crypto_channels]
    env_line = ','.join(channel_ids)
    
    print(f"TELEGRAM_CHANNELS={env_line}")
    
    # Save to file
    with open('crypto_channels_filtered.txt', 'w', encoding='utf-8') as f:
        f.write(f"Total: {len(crypto_channels)} channels\n\n")
        for i, channel in enumerate(crypto_channels, 1):
            f.write(f"{i:2d}. {channel['title'][:60]:60s} | ID: {channel['id']:20s} | @{channel['username']}\n")
        f.write(f"\n{'='*80}\n")
        f.write(f".ENV FORMAT:\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"TELEGRAM_CHANNELS={env_line}\n")
    
    print(f"\n✅ Saved to: crypto_channels_filtered.txt")

if __name__ == "__main__":
    main()
