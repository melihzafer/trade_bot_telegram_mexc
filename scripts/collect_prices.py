"""
Batch processor to fetch historical price data for all parsed signals.
Downloads OHLC data from MEXC (fallback to Binance) and caches locally.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mexc_api import MEXCClient
from utils.binance_api import BinanceClient
from utils.logger import info, success, warn, error


class PriceDataCollector:
    """Collects and caches historical price data for signals."""
    
    def __init__(self, cache_dir: Path, use_mexc: bool = True):
        """
        Initialize collector.
        
        Args:
            cache_dir: Directory to cache price data
            use_mexc: If True, use MEXC API (primary), else Binance (fallback)
        """
        self.use_mexc = use_mexc
        
        if use_mexc:
            self.client = MEXCClient()
            info(f"🔄 Using MEXC API (supports more symbols)")
        else:
            self.client = BinanceClient()
            info(f"🔄 Using Binance API (fallback)")
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        info(f"📁 Price data cache: {cache_dir}")
    
    def get_cache_filename(self, symbol: str, date: str) -> Path:
        """
        Get cache filename for symbol and date.
        
        Args:
            symbol: Trading symbol
            date: Date string (YYYY-MM-DD)
            
        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{symbol}_{date}.json"
    
    def load_cached_price(self, symbol: str, timestamp: datetime) -> Dict:
        """
        Load cached price data if available.
        
        Args:
            symbol: Trading symbol
            timestamp: Signal timestamp
            
        Returns:
            Cached price data or None
        """
        date_str = timestamp.strftime("%Y-%m-%d")
        cache_file = self.get_cache_filename(symbol, date_str)
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    def save_cached_price(self, symbol: str, timestamp: datetime, price_data: Dict):
        """
        Save price data to cache.
        
        Args:
            symbol: Trading symbol
            timestamp: Signal timestamp
            price_data: Price data dict
        """
        date_str = timestamp.strftime("%Y-%m-%d")
        cache_file = self.get_cache_filename(symbol, date_str)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(price_data, f, indent=2)
        except Exception as e:
            warn(f"⚠️ Failed to cache price data: {e}")
    
    def fetch_price_for_signal(self, signal: Dict) -> Dict:
        """
        Fetch price data for a single signal.
        
        Args:
            signal: Parsed signal dict
            
        Returns:
            Dict with price data and status
        """
        symbol = signal.get('symbol')
        timestamp_str = signal.get('timestamp')
        
        if not symbol or not timestamp_str:
            return {'status': 'error', 'error': 'Missing symbol or timestamp'}
        
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Check cache first
            cached = self.load_cached_price(symbol, timestamp)
            if cached:
                return {'status': 'cached', 'price_data': cached}
            
            # Fetch from API
            price_data = self.client.get_price_at_time(symbol, timestamp, interval="15m")
            
            if price_data:
                # Save to cache
                self.save_cached_price(symbol, timestamp, price_data)
                return {'status': 'fetched', 'price_data': price_data}
            else:
                return {'status': 'error', 'error': 'No price data returned'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


def load_parsed_signals(parsed_path: Path) -> List[Dict]:
    """
    Load complete parsed signals.
    
    Args:
        parsed_path: Path to signals_parsed.jsonl
        
    Returns:
        List of complete signal dicts
    """
    signals = []
    
    if not parsed_path.exists():
        error(f"❌ File not found: {parsed_path}")
        return signals
    
    try:
        with open(parsed_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    signal = json.loads(line)
                    # Only load complete signals
                    if signal.get('is_complete'):
                        signals.append(signal)
        
        info(f"📚 Loaded {len(signals)} complete signals")
        
    except Exception as e:
        error(f"❌ Error loading signals: {e}")
    
    return signals


def collect_price_data():
    """Main function to collect price data for all signals."""
    print("\n" + "="*80)
    print("💹 HISTORICAL PRICE DATA COLLECTOR")
    print("="*80)
    
    # Paths
    data_dir = Path("data")
    parsed_path = data_dir / "signals_parsed.jsonl"
    cache_dir = data_dir / "historical_prices"
    
    # Try MEXC first (supports more symbols)
    info("\n🔍 Testing API connections...")
    mexc_client = MEXCClient()
    binance_client = BinanceClient()
    
    mexc_ok = mexc_client.test_connection()
    binance_ok = binance_client.test_connection()
    
    if not mexc_ok and not binance_ok:
        error("❌ Neither MEXC nor Binance API available. Aborting.")
        return
    
    # Choose primary API
    use_mexc = mexc_ok  # Prefer MEXC if available
    api_name = "MEXC" if use_mexc else "Binance"
    success(f"\n✅ Using {api_name} API as primary")
    
    # Initialize collector
    collector = PriceDataCollector(cache_dir, use_mexc=use_mexc)
    
    # Load signals
    signals = load_parsed_signals(parsed_path)
    
    if not signals:
        error("❌ No complete signals found!")
        return
    
    # Collect price data
    info(f"\n🔄 Fetching price data for {len(signals)} signals...")
    
    stats = {
        'total': len(signals),
        'cached': 0,
        'fetched': 0,
        'error': 0,
        'unique_symbols': set()
    }
    
    for i, signal in enumerate(signals, 1):
        # Progress indicator
        if i % 20 == 0 or i == 1:
            info(f"   Progress: {i}/{stats['total']} ({i*100//stats['total']}%)")
        
        symbol = signal.get('symbol')
        stats['unique_symbols'].add(symbol)
        
        # Fetch price
        result = collector.fetch_price_for_signal(signal)
        
        if result['status'] == 'cached':
            stats['cached'] += 1
        elif result['status'] == 'fetched':
            stats['fetched'] += 1
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        else:
            stats['error'] += 1
            warn(f"⚠️ Error for {symbol}: {result.get('error')}")
    
    # Print statistics
    print("\n" + "="*80)
    print("📊 COLLECTION STATISTICS")
    print("="*80)
    print(f"\n📈 Results:")
    print(f"   Total Signals: {stats['total']}")
    print(f"   ✅ From Cache: {stats['cached']}")
    print(f"   🌐 Newly Fetched: {stats['fetched']}")
    print(f"   ❌ Errors: {stats['error']}")
    print(f"   🪙 Unique Symbols: {len(stats['unique_symbols'])}")
    
    print(f"\n📁 Cache Directory: {cache_dir}")
    print(f"   Total Files: {len(list(cache_dir.glob('*.json')))}")
    
    # Success rate
    success_rate = ((stats['cached'] + stats['fetched']) / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"\n✅ Success Rate: {success_rate:.1f}%")
    
    if success_rate > 90:
        success("\n🎉 Excellent! Price data collection complete!")
    elif success_rate > 70:
        info("\n✅ Good! Most price data collected successfully.")
    else:
        warn("\n⚠️ Some issues during collection. Check errors above.")
    
    print("="*80)


if __name__ == "__main__":
    collect_price_data()
