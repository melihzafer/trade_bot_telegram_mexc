"""
Binance Symbol Validator

Pre-validates parsed symbols against Binance exchange to filter garbage.
Uses /exchangeInfo API endpoint with caching for efficiency.

Usage:
    validator = BinanceValidator()
    if validator.is_valid_symbol("BTCUSDT"):
        # Process signal
"""

import requests
from typing import Set, Optional
from datetime import datetime, timedelta
import json
import os


class BinanceValidator:
    """Validates crypto symbols against Binance exchange."""
    
    CACHE_FILE = "data/binance_symbols_cache.json"
    CACHE_DURATION = timedelta(hours=24)  # Refresh daily
    API_URL = "https://api.binance.com/api/v3/exchangeInfo"
    
    def __init__(self):
        """Initialize validator with cached symbols."""
        self.valid_symbols: Set[str] = set()
        self.last_update: Optional[datetime] = None
        self._load_cache()
        
        # If cache empty or stale, fetch from API
        if not self.valid_symbols or self._is_cache_stale():
            self._fetch_from_binance()
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if symbol exists on Binance.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            True if symbol exists on Binance
            
        Example:
            >>> validator = BinanceValidator()
            >>> validator.is_valid_symbol("BTCUSDT")
            True
            >>> validator.is_valid_symbol("TARGETSUSDT")
            False
        """
        if not symbol:
            return False
        
        # Normalize to uppercase
        symbol_upper = symbol.upper()
        
        # Check cache
        return symbol_upper in self.valid_symbols
    
    def _fetch_from_binance(self) -> None:
        """Fetch valid symbols from Binance API."""
        try:
            print("🔄 Fetching valid symbols from Binance...")
            
            response = requests.get(self.API_URL, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            symbols = data.get("symbols", [])
            
            # Extract USDT pairs only (futures trading)
            self.valid_symbols = {
                s["symbol"] 
                for s in symbols 
                if s.get("symbol", "").endswith("USDT") and 
                   s.get("status") == "TRADING"
            }
            
            self.last_update = datetime.now()
            
            print(f"✅ Loaded {len(self.valid_symbols)} valid USDT symbols from Binance")
            
            # Save to cache
            self._save_cache()
            
        except Exception as e:
            print(f"⚠️ Failed to fetch from Binance: {e}")
            print("⚠️ Using cached symbols (may be stale)")
    
    def _load_cache(self) -> None:
        """Load cached symbols from file."""
        if not os.path.exists(self.CACHE_FILE):
            return
        
        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            self.valid_symbols = set(cache.get("symbols", []))
            last_update_str = cache.get("last_update")
            
            if last_update_str:
                self.last_update = datetime.fromisoformat(last_update_str)
            
            print(f"📦 Loaded {len(self.valid_symbols)} symbols from cache")
            
        except Exception as e:
            print(f"⚠️ Failed to load cache: {e}")
    
    def _save_cache(self) -> None:
        """Save symbols to cache file."""
        try:
            os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
            
            cache = {
                "symbols": list(self.valid_symbols),
                "last_update": self.last_update.isoformat() if self.last_update else None,
            }
            
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
            
            print(f"💾 Cached {len(self.valid_symbols)} symbols to {self.CACHE_FILE}")
            
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")
    
    def _is_cache_stale(self) -> bool:
        """Check if cache needs refresh."""
        if not self.last_update:
            return True
        
        age = datetime.now() - self.last_update
        return age > self.CACHE_DURATION
    
    def refresh(self) -> None:
        """Force refresh symbols from Binance API."""
        self._fetch_from_binance()
    
    def get_stats(self) -> dict:
        """Get validator statistics."""
        return {
            "total_symbols": len(self.valid_symbols),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "cache_age_hours": (datetime.now() - self.last_update).total_seconds() / 3600 
                               if self.last_update else None,
            "is_stale": self._is_cache_stale(),
        }


# Singleton instance for efficiency
_validator_instance: Optional[BinanceValidator] = None


def get_validator() -> BinanceValidator:
    """Get or create singleton validator instance."""
    global _validator_instance
    
    if _validator_instance is None:
        _validator_instance = BinanceValidator()
    
    return _validator_instance


# Convenience function
def is_valid_symbol(symbol: str) -> bool:
    """
    Check if symbol is valid on Binance (convenience function).
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        
    Returns:
        True if valid
        
    Example:
        >>> from utils.binance_validator import is_valid_symbol
        >>> is_valid_symbol("BTCUSDT")
        True
    """
    validator = get_validator()
    return validator.is_valid_symbol(symbol)


if __name__ == "__main__":
    # Test validator
    validator = BinanceValidator()
    
    print("\n🧪 Testing validator:")
    print()
    
    test_cases = [
        ("BTCUSDT", True),
        ("ETHUSDT", True),
        ("SOLUSDT", True),
        ("TARGETSUSDT", False),
        ("CROSSUSDT", False),
        ("SOLANAUSDT", False),
        ("ETHEREUMUSDT", False),
        ("LEVERAGEUSDT", False),
    ]
    
    for symbol, expected in test_cases:
        result = validator.is_valid_symbol(symbol)
        status = "✅" if result == expected else "❌"
        print(f"{status} {symbol}: {result} (expected {expected})")
    
    print()
    print("📊 Validator stats:")
    stats = validator.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
