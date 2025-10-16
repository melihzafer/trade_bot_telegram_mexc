"""
Advanced signal parser for multiple Telegram channel formats.
Extracts trading signals (LONG/SHORT, Entry, TP, SL, Leverage, Symbol) from raw messages.
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class SignalParser:
    """
    Parser for crypto trading signals from Telegram channels.
    Supports multiple formats and variations.
    """
    
    def __init__(self):
        """Initialize regex patterns for signal extraction."""
        
        # Signal direction patterns
        self.direction_patterns = [
            r'(?:🟢|✅|🔵|🟣|🟠)?\s*(?:LONG|long|Long|BUY|buy|Buy)',
            r'(?:🔴|❌|🟣|🔵|🟠)?\s*(?:SHORT|short|Short|SELL|sell|Sell)',
        ]
        
        # Symbol patterns (with optional emoji prefixes)
        self.symbol_patterns = [
            r'(?:❇️|💎|🪙)?\s*([A-Z]{2,10}USDT?)',  # BTCUSDT, 1000BONKUSDT
            r'(?:Coin|Symbol|Pair)[\s:]*([A-Z]{2,10}USDT?)',
            r'\$([A-Z]{2,10})',  # $BTC
        ]
        
        # Entry price patterns
        self.entry_patterns = [
            r'(?:Entry|entry|ENTRY)[\s:]*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)',  # Range: 64800-65000
            r'(?:Entry|entry|ENTRY)[\s:]*(\d+\.?\d*)',  # Single: 64800
            r'(?:☣|⚡️)[\s]*Entry[\s:]*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)',  # With emoji
            r'(?:☣|⚡️)[\s]*Entry[\s:]*(\d+\.?\d*)',  # Single with emoji
            r'Open[\s:]*(\d+\.?\d*)',  # Open: 1.1584
        ]
        
        # Take Profit patterns (supports TP1-TP8, Target 1-8)
        self.tp_patterns = [
            r'(?:TP|tp|Target|target)[\s]*(\d+)[\s:]*(\d+\.?\d*)',  # TP1: 65500
            r'(?:☪)[\s]*Target[\s]*(\d+)[\s-]*(\d+\.?\d*)',  # ☪ Target 1 - 1.1729
        ]
        
        # Stop Loss patterns
        self.sl_patterns = [
            r'(?:SL|sl|Stop Loss|stop loss|STOP LOSS)[\s:]*(\d+\.?\d*)',
            r'(?:⛔️)[\s]*Stop Loss[\s:]*(\d+\.?\d*)',
        ]
        
        # Leverage patterns
        self.leverage_patterns = [
            r'Leverage[\s:]*(\d+)[xX]?',
            r'(\d+)[xX]\s*leverage',
        ]
    
    def parse_direction(self, text: str) -> Optional[str]:
        """
        Extract signal direction (LONG/SHORT).
        
        Args:
            text: Message text
            
        Returns:
            'LONG' or 'SHORT' or None
        """
        text_upper = text.upper()
        
        # Check for SHORT first (more specific)
        if re.search(r'(?:🔴|❌)?\s*SHORT', text_upper):
            return 'SHORT'
        
        # Check for LONG
        if re.search(r'(?:🟢|✅)?\s*LONG', text_upper):
            return 'LONG'
        
        # Check for BUY/SELL
        if 'BUY' in text_upper:
            return 'LONG'
        if 'SELL' in text_upper:
            return 'SHORT'
        
        return None
    
    def parse_symbol(self, text: str) -> Optional[str]:
        """
        Extract trading symbol (e.g., BTCUSDT, ETHUSDT).
        
        Args:
            text: Message text
            
        Returns:
            Symbol string or None
        """
        for pattern in self.symbol_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1).upper()
                # Ensure it ends with USDT
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'
                return symbol
        
        return None
    
    def parse_entry(self, text: str) -> Dict[str, Optional[float]]:
        """
        Extract entry price (single or range).
        
        Args:
            text: Message text
            
        Returns:
            Dict with 'entry_min' and 'entry_max' (or both same if single price)
        """
        for pattern in self.entry_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 2 and groups[1]:
                    # Range format
                    return {
                        'entry_min': float(groups[0]),
                        'entry_max': float(groups[1])
                    }
                elif len(groups) >= 1 and groups[0]:
                    # Single price
                    price = float(groups[0])
                    return {
                        'entry_min': price,
                        'entry_max': price
                    }
        
        return {'entry_min': None, 'entry_max': None}
    
    def parse_take_profits(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all Take Profit targets.
        
        Args:
            text: Message text
            
        Returns:
            List of dicts with 'tp_number' and 'tp_price'
        """
        tps = []
        
        for pattern in self.tp_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tp_num = int(match.group(1))
                tp_price = float(match.group(2))
                tps.append({
                    'tp_number': tp_num,
                    'tp_price': tp_price
                })
        
        # Sort by TP number
        tps.sort(key=lambda x: x['tp_number'])
        
        return tps
    
    def parse_stop_loss(self, text: str) -> Optional[float]:
        """
        Extract Stop Loss price.
        
        Args:
            text: Message text
            
        Returns:
            Stop Loss price or None
        """
        for pattern in self.sl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return None
    
    def parse_leverage(self, text: str) -> Optional[int]:
        """
        Extract leverage value.
        
        Args:
            text: Message text
            
        Returns:
            Leverage as integer or None
        """
        for pattern in self.leverage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def parse_signal(self, message_data: Dict) -> Optional[Dict]:
        """
        Parse a complete trading signal from message data.
        
        Args:
            message_data: Dict from signals_raw.jsonl
            
        Returns:
            Parsed signal dict or None if not a valid signal
        """
        text = message_data.get('text', '')
        
        if not text:
            return None
        
        # Extract all components
        direction = self.parse_direction(text)
        symbol = self.parse_symbol(text)
        entry = self.parse_entry(text)
        tps = self.parse_take_profits(text)
        sl = self.parse_stop_loss(text)
        leverage = self.parse_leverage(text)
        
        # Must have at least direction OR (entry and TP)
        if not direction and not (entry['entry_min'] and tps):
            return None
        
        # Build parsed signal
        parsed = {
            'timestamp': message_data.get('timestamp'),
            'channel_id': message_data.get('channel_id'),
            'channel_title': message_data.get('channel_title'),
            'message_id': message_data.get('message_id'),
            'direction': direction,
            'symbol': symbol,
            'entry_min': entry['entry_min'],
            'entry_max': entry['entry_max'],
            'stop_loss': sl,
            'leverage': leverage,
            'take_profits': tps,
            'num_targets': len(tps),
            'raw_text': text[:200],  # Keep first 200 chars for reference
        }
        
        return parsed
    
    def is_signal_complete(self, parsed: Dict) -> bool:
        """
        Check if parsed signal has minimum required fields for backtesting.
        
        Args:
            parsed: Parsed signal dict
            
        Returns:
            True if signal is complete enough for backtesting
        """
        required = [
            parsed.get('direction'),
            parsed.get('symbol'),
            parsed.get('entry_min'),
            parsed.get('take_profits') and len(parsed['take_profits']) > 0,
        ]
        
        return all(required)


def test_parser():
    """Test parser with sample messages."""
    parser = SignalParser()
    
    test_messages = [
        {
            'text': '🟢 LONG BTCUSDT\nEntry: 64800-65000\nTP1: 65500\nTP2: 66000\nSL: 64200\nLeverage: 5x',
            'channel_title': 'Test',
            'message_id': 1,
            'timestamp': '2025-10-15T00:00:00'
        },
        {
            'text': '🔴 SHORT\n❇️ 1000BONKUSDT\n☣ Entry : 0.016353 - 0.016305\n☪ Target 1 - 0.016126\n☪ Target 2 - 0.015946\n⛔️ Stop Loss : 0.017498',
            'channel_title': 'Test',
            'message_id': 2,
            'timestamp': '2025-10-15T00:00:00'
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTING PARSER")
    print("="*80)
    
    for msg in test_messages:
        print(f"\n📝 Input: {msg['text'][:100]}...")
        result = parser.parse_signal(msg)
        if result:
            print(f"✅ Parsed Successfully!")
            print(f"   Direction: {result['direction']}")
            print(f"   Symbol: {result['symbol']}")
            print(f"   Entry: {result['entry_min']} - {result['entry_max']}")
            print(f"   TPs: {len(result['take_profits'])}")
            print(f"   SL: {result['stop_loss']}")
            print(f"   Leverage: {result['leverage']}")
            print(f"   Complete: {parser.is_signal_complete(result)}")
        else:
            print("❌ Failed to parse")


if __name__ == '__main__':
    test_parser()
