"""
MEXC Exchange API wrapper for historical price data.
Supports both Spot and Futures markets.

Documentation: https://mexcdevelop.github.io/apidocs/spot_v3_en/
"""
import time
import hmac
import hashlib
import requests
import sys
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import info, warn, error, success


class MEXCClient:
    """
    MEXC Exchange API client.
    Supports public endpoints (no API key required for historical data).
    """
    
    # API Base URLs
    SPOT_BASE_URL = "https://api.mexc.com"
    FUTURES_BASE_URL = "https://contract.mexc.com"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, use_futures: bool = True):
        """
        Initialize MEXC client.
        
        Args:
            api_key: MEXC API key (optional, not needed for public data)
            api_secret: MEXC API secret (optional)
            use_futures: If True, use Futures API, else Spot API
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_futures = use_futures
        self.base_url = self.FUTURES_BASE_URL if use_futures else self.SPOT_BASE_URL
        
        info(f"📡 MEXC Client initialized ({'Futures' if use_futures else 'Spot'} mode)")
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Dict:
        """
        Make HTTP request to MEXC API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            signed: Whether to sign the request (for private endpoints)
            
        Returns:
            JSON response as dict
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if params is None:
            params = {}
        
        # Add signature for private endpoints
        if signed and self.api_key and self.api_secret:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            headers['X-MEXC-APIKEY'] = self.api_key
        
        try:
            response = requests.request(method, url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error(f"❌ MEXC API request failed: {e}")
            return {}
    
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
            symbol: Trading pair (e.g., 'BTCUSDT', 'BTC_USDT' for futures)
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of candles to fetch (max 2000)
            
        Returns:
            List of klines: [[timestamp, open, high, low, close, volume], ...]
        """
        if self.use_futures:
            # Futures API endpoint
            endpoint = "/api/v1/contract/kline"
            
            # Futures uses underscore format: BTC_USDT
            if 'USDT' in symbol and '_' not in symbol:
                symbol = symbol.replace('USDT', '_USDT')
            
            params = {
                "symbol": symbol,
                "interval": interval,
            }
            
            if start_time:
                params["start"] = start_time
            if end_time:
                params["end"] = end_time
            
            response = self._request("GET", endpoint, params)
            
            # Futures API returns different format
            if response.get("success") and response.get("data"):
                klines = []
                for candle in response["data"]["time"]:
                    klines.append([
                        candle["t"],      # timestamp
                        candle["o"],      # open
                        candle["h"],      # high
                        candle["l"],      # low
                        candle["c"],      # close
                        candle["v"],      # volume
                    ])
                return klines
            
        else:
            # Spot API endpoint
            endpoint = "/api/v3/klines"
            
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            }
            
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
            
            response = self._request("GET", endpoint, params)
            
            if isinstance(response, list):
                return response
        
        return []
    
    def get_price_at_time(self, symbol: str, timestamp: datetime, interval: str = "15m") -> Optional[Dict]:
        """
        Get OHLC price data at specific timestamp.
        
        Args:
            symbol: Trading pair
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
    
    def test_connection(self) -> bool:
        """
        Test API connection by fetching BTC price.
        
        Returns:
            True if connection successful
        """
        try:
            if self.use_futures:
                klines = self.get_klines("BTC_USDT", "1h", limit=1)
            else:
                klines = self.get_klines("BTCUSDT", "1h", limit=1)
            
            if klines:
                success("✅ MEXC API connection successful!")
                return True
            else:
                error("❌ MEXC API connection failed!")
                return False
                
        except Exception as e:
            error(f"❌ MEXC API test failed: {e}")
            return False


def test_mexc_api():
    """Test MEXC API with sample queries."""
    print("\n" + "="*80)
    print("🧪 TESTING MEXC API")
    print("="*80)
    
    # Test Spot API first (usually more stable)
    print("\n📊 Testing Spot API...")
    spot_client = MEXCClient(use_futures=False)
    
    spot_works = False
    if spot_client.test_connection():
        spot_works = True
        print("\n📈 Fetching BTCUSDT 15m candles...")
        klines = spot_client.get_klines("BTCUSDT", "15m", limit=5)
        
        if klines:
            print(f"✅ Received {len(klines)} candles")
            print(f"Latest close price: {klines[-1][4]}")
    
    # Test Futures API
    print("\n� Testing Futures API...")
    futures_client = MEXCClient(use_futures=True)
    
    futures_works = False
    if futures_client.test_connection():
        futures_works = True
        print("\n📈 Fetching BTC_USDT 15m candles...")
        klines = futures_client.get_klines("BTC_USDT", "15m", limit=5)
        
        if klines:
            print(f"✅ Received {len(klines)} candles")
            print(f"Latest close price: {klines[-1][4]}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Spot API: {'✅ Working' if spot_works else '❌ Failed'}")
    print(f"Futures API: {'✅ Working' if futures_works else '❌ Failed'}")
    print("="*80)


if __name__ == "__main__":
    test_mexc_api()
