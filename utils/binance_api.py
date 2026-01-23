"""
Binance Exchange API wrapper for historical price data.
More stable alternative to MEXC API, supports same coins.

Documentation: https://binance-docs.github.io/apidocs/spot/en/
"""
import requests
import sys
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import info, warn, error, success


class BinanceClient:
    """
    Binance Exchange API client.
    Public endpoints only (no API key required).
    """
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(self):
        """Initialize Binance client."""
        info("Binance Client initialized")
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> any:
        """
        Make HTTP request to Binance API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response or None on error
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            # Handle specific HTTP errors
            if e.response.status_code == 400:
                symbol = params.get('symbol', 'Unknown') if params else 'Unknown'
                warn(f"⚠️ Symbol {symbol} not found on Binance (400 Bad Request)")
                return None
            else:
                error(f"Binance API HTTP error: {e}")
                return None
                
        except requests.exceptions.RequestException as e:
            error(f"Binance API request failed: {e}")
            return None
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "15m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List]:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of candles to fetch (max 1000)
            
        Returns:
            List of klines: [[timestamp, open, high, low, close, volume, ...], ...]
        """
        endpoint = "/api/v3/klines"
        
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),  # Binance max is 1000
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        response = self._request(endpoint, params)
        
        if isinstance(response, list):
            return response
        
        return []
    
    def get_price_at_time(self, symbol: str, timestamp: datetime, interval: str = "15m") -> Optional[Dict]:
        """
        Get OHLC price data at specific timestamp.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timestamp: Target datetime
            interval: Candle interval
            
        Returns:
            Dict with open, high, low, close, volume
        """
        # Convert datetime to milliseconds
        target_ms = int(timestamp.timestamp() * 1000)
        
        # Fetch klines around target time (1 hour window)
        start_ms = target_ms - (60 * 60 * 1000)  # 1 hour before
        end_ms = target_ms + (60 * 60 * 1000)    # 1 hour after
        
        klines = self.get_klines(symbol, interval, start_ms, end_ms, limit=100)
        
        if not klines:
            return None
        
        # Find closest candle to target time
        closest_candle = min(klines, key=lambda x: abs(x[0] - target_ms))
        
        return {
            "timestamp": closest_candle[0],
            "datetime": datetime.fromtimestamp(closest_candle[0] / 1000).isoformat(),
            "open": float(closest_candle[1]),
            "high": float(closest_candle[2]),
            "low": float(closest_candle[3]),
            "close": float(closest_candle[4]),
            "volume": float(closest_candle[5]),
        }
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Current price or None if symbol not found
        """
        endpoint = "/api/v3/ticker/price"
        response = self._request(endpoint, {"symbol": symbol})
        
        if response and "price" in response:
            return float(response["price"])
        
        # Symbol not found on Binance
        return None
    
    def is_symbol_available(self, symbol: str) -> bool:
        """
        Check if a symbol is available on Binance.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            True if symbol exists on Binance
        """
        price = self.get_current_price(symbol)
        return price is not None
    
    def test_connection(self) -> bool:
        """
        Test API connection by fetching BTC price.
        
        Returns:
            True if connection successful
        """
        try:
            price = self.get_current_price("BTCUSDT")
            
            if price:
                success(f"✅ Binance API connection successful! BTC: ${price:,.2f}")
                return True
            else:
                error("❌ Binance API connection failed!")
                return False
                
        except Exception as e:
            error(f"❌ Binance API test failed: {e}")
            return False


def test_binance_api():
    """Test Binance API with sample queries."""
    print("\n" + "="*80)
    print("🧪 TESTING BINANCE API")
    print("="*80)
    
    client = BinanceClient()
    
    if client.test_connection():
        # Get recent klines
        print("\n📈 Fetching BTCUSDT 15m candles...")
        klines = client.get_klines("BTCUSDT", "15m", limit=5)
        
        if klines:
            print(f"✅ Received {len(klines)} candles")
            for i, k in enumerate(klines, 1):
                dt = datetime.fromtimestamp(k[0] / 1000)
                print(f"   {i}. {dt.strftime('%Y-%m-%d %H:%M')} | O:{k[1]} H:{k[2]} L:{k[3]} C:{k[4]}")
        
        # Get price at specific time
        print("\n🕐 Fetching price at specific timestamp...")
        test_time = datetime.now() - timedelta(hours=2)
        price_data = client.get_price_at_time("BTCUSDT", test_time)
        
        if price_data:
            print(f"✅ Price data retrieved:")
            print(f"   Time: {price_data['datetime']}")
            print(f"   Open: ${price_data['open']:,.2f}")
            print(f"   High: ${price_data['high']:,.2f}")
            print(f"   Low: ${price_data['low']:,.2f}")
            print(f"   Close: ${price_data['close']:,.2f}")
        
        # Test DOGE (most popular in signals)
        print("\n🐕 Testing DOGEUSDT...")
        doge_price = client.get_current_price("DOGEUSDT")
        if doge_price:
            print(f"✅ DOGE current price: ${doge_price}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_binance_api()
