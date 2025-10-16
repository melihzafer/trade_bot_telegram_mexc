"""
Enhanced Signal Parser with Confidence Scoring & Adaptive Whitelist
Supports TR/EN mixed signals with ML-inspired pattern learning.

Author: OMNI Tech Solutions
Created: 2025
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from parsers.number_normalizer import normalize_number, normalize_number_list, parse_tp_sequence, clean_text
from utils.whitelist_manager import WhitelistManager


@dataclass
class ParsedSignal:
    """Parsed trading signal with confidence scoring."""
    
    # Raw input
    raw_text: str
    
    # Detected fields
    symbol: Optional[str] = None
    market: Optional[str] = None  # "futures" or "spot"
    side: Optional[str] = None  # "long" or "short"
    leverage_x: Optional[int] = None
    entries: List[float] = field(default_factory=list)
    tps: List[float] = field(default_factory=list)
    sl: Optional[float] = None
    
    # Metadata
    confidence: float = 0.0  # 0-1 score
    timestamp_iso: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    locale: str = "mixed"  # "tr", "en", or "mixed"
    parsing_notes: List[str] = field(default_factory=list)
    
    @property
    def entry_min(self) -> Optional[float]:
        """Get minimum entry price (first entry or None)."""
        return self.entries[0] if self.entries else None
    
    @property
    def entry_max(self) -> Optional[float]:
        """Get maximum entry price (last entry or None)."""
        return self.entries[-1] if self.entries else None
    
    @property
    def source(self) -> str:
        """Alias for parsing_notes compatibility."""
        return ' | '.join(self.parsing_notes) if self.parsing_notes else "Unknown"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def is_valid(self, min_confidence: float = 0.6) -> bool:
        """Check if signal has minimum confidence."""
        return self.confidence >= min_confidence and self.symbol is not None


class EnhancedParser:
    """
    Production-ready parser for TR/EN trading signals.
    
    Features:
    - Symbol detection: btc, btcusdt, btc/usdt, #btc
    - TR/EN keywords: entry|giriş, tp|hedef, sl|stop, lev|kaldıraç
    - Number normalization: 112.191, 112,191, 112k, 112 bin
    - Confidence scoring: +0.2 per field (symbol, side, entry, tp, sl)
    - TP sequence: tp: 1-2-3 → percentage-based targets
    """
    
    # Symbol pattern: matches btc, btcusdt, btc/usdt, #btc (case insensitive)
    SYMBOL_PATTERN = re.compile(
        r'(?i)\b#?([a-z]{2,10})(?:/|)(?:usdt|usd)?\b',
        re.IGNORECASE
    )
    
    # TR/EN keywords (non-capturing groups)
    LONG_KEYWORDS = r'(?i)\b(?:long|buy|al|alım|giriş)\b'
    SHORT_KEYWORDS = r'(?i)\b(?:short|sell|sat|satış|kısa)\b'
    
    ENTRY_KEYWORDS = r'(?i)\b(?:entry|giriş|buy|alım|long\s*entry|short\s*entry)\b'
    TP_KEYWORDS = r'(?i)\b(?:tp\d*|take\s*profit|hedef\d*|targets?|sell)\b'
    SL_KEYWORDS = r'(?i)\b(?:sl|stop|stoploss|stop\s*loss|zarar\s*durdur)\b'
    LEVERAGE_KEYWORDS = r'(?i)\b(?:lev|leverage|kaldıraç|(\d{1,3})x)\b'
    
    # Common garbage symbols to reject
    BLACKLIST = {
        # Base currency
        'usdt', 'usd', 'busd', 'usdc', 'dai', 'tusd',
        
        # Trading keywords (prevent as symbols)
        'leverage', 'target', 'targets', 'cross', 'isolated',
        'tp', 'sl', 'lev', 'take', 'profit', 'loss', 'stop', 'entry',
        'long', 'short', 'buy', 'sell', 'sale', 'coin',
        
        # Major coin full names (typos)
        'bitcoin', 'ethereum', 'solana', 'binancecoin', 'cardano',
        'ripple', 'polkadot', 'dogecoin', 'shiba', 'avalanche',
        
        # Exchange brands
        'binance', 'mexc', 'kucoin', 'bybit', 'okx', 'kraken',
        'coinbase', 'huobi', 'gateio', 'bitget',
        
        # Pump/marketing words
        'signal', 'signals', 'pump', 'pumps', 'moon', 'rocket',
        'gem', 'gems', 'group', 'channel', 'vip', 'free', 'join',
        
        # Market/trading terms
        'market', 'markets', 'trading', 'trader', 'trade', 'trend',
        'order', 'orders', 'limit', 'swing', 'spot', 'futures',
        'going', 'coming', 'next', 'new', 'hot', 'top',
        
        # Turkish words (include both ASCII and Unicode variants)
        'yeni', 'yenı', 'yeni\u0307',  # YENİ variants
        'sinyal', 'sınyal', 's\u0131nyal', 'si\u0307nyal',  # SİNYAL variants
        'hedef', 'hedey',  # Turkish "target"
        'giris', 'giriş', 'giri\u015f',  # Turkish "entry"
        'zarar', 'durdur',  # Turkish "stop"
        'gidiyor', 'geliyor',  # Turkish "going/coming"
        'sipariş', 'siparis',  # Turkish "order"
        'piyasa', 'alım', 'satım',  # Turkish "market/buy/sell"
        
        # Known garbage coins (delisted/invalid)
        'kamikaze', 'vine', 'zora',
    }
    
    def __init__(self):
        """Initialize parser with whitelist."""
        self.whitelist = WhitelistManager()
        self.fast_path_hits = 0
        self.full_parse_count = 0
    
    def parse(self, text: str) -> ParsedSignal:
        """
        Parse trading signal from text with adaptive whitelist fast-path.
        
        Flow:
        1. Check whitelist for known pattern → fast path
        2. If miss → full validation → learn on success
        
        Args:
            text: Raw signal text (TR/EN mixed)
        
        Returns:
            ParsedSignal with confidence score
        """
        # FAST PATH: Check whitelist for known pattern
        whitelist_entry = self.whitelist.lookup(text)
        
        if whitelist_entry:
            # Fast path: use cached extraction
            self.fast_path_hits += 1
            return self._fast_parse(text, whitelist_entry)
        
        # FULL PARSE: Standard validation
        self.full_parse_count += 1
        
        signal = ParsedSignal(raw_text=text)
        
        # Clean text (remove URLs, emojis, extra whitespace)
        cleaned = clean_text(text)
        
        # Detect locale (TR vs EN vs mixed)
        signal.locale = self._detect_locale(cleaned)
        
        # Extract fields
        signal.symbol = self._extract_symbol(cleaned, signal)
        signal.side = self._extract_side(cleaned, signal)
        signal.leverage_x = self._extract_leverage(cleaned, signal)
        signal.entries = self._extract_entries(cleaned, signal)
        signal.tps = self._extract_tps(cleaned, signal)
        signal.sl = self._extract_sl(cleaned, signal)
        signal.market = self._infer_market(signal)
        
        # Calculate confidence score
        signal.confidence = self._calculate_confidence(signal)
        
        # LEARN: Add successful parse to whitelist
        if signal.symbol and signal.confidence >= 0.6:
            self.whitelist.add(
                text=text,
                symbol=signal.symbol,
                entries=signal.entries,
                tps=signal.tps,
                sl=signal.sl,
                leverage=signal.leverage_x,
                language=signal.locale
            )
        
        return signal
    
    def _fast_parse(self, text: str, whitelist_entry) -> ParsedSignal:
        """
        Ultra-fast parsing using whitelist cached data.
        
        Skips BLACKLIST, validation, and complex extraction.
        """
        signal = ParsedSignal(raw_text=text)
        
        # Use cached values
        signal.symbol = whitelist_entry.symbol
        signal.entries = whitelist_entry.cached_entries.copy()
        signal.tps = whitelist_entry.cached_tps.copy()
        signal.sl = whitelist_entry.cached_sl
        signal.leverage_x = whitelist_entry.cached_leverage
        signal.locale = whitelist_entry.language
        
        # Infer side from text (quick check)
        signal.side = self._extract_side(text, signal)
        
        # Infer market
        signal.market = self._infer_market(signal)
        
        # Use whitelist confidence
        signal.confidence = whitelist_entry.confidence
        
        signal.parsing_notes.append(
            f"✨ Fast-path from whitelist (confidence: {whitelist_entry.confidence:.2f}, "
            f"success_count: {whitelist_entry.success_count})"
        )
        
        return signal
    
    def get_stats(self) -> Dict:
        """Get parser performance statistics."""
        total = self.fast_path_hits + self.full_parse_count
        hit_rate = self.fast_path_hits / total if total > 0 else 0
        
        whitelist_stats = self.whitelist.get_stats()
        
        return {
            'total_parses': total,
            'fast_path_hits': self.fast_path_hits,
            'full_parses': self.full_parse_count,
            'hit_rate': f"{hit_rate*100:.1f}%",
            'whitelist_patterns': whitelist_stats.get('total_entries', 0),
            'whitelist_hit_rate': f"{whitelist_stats.get('hit_rate', 0)*100:.1f}%",
        }
    
    def _detect_locale(self, text: str) -> str:
        """Detect text locale (tr, en, or mixed)."""
        tr_keywords = r'(giriş|alım|hedef|zarar|durdur|kaldıraç|bin)'
        en_keywords = r'(entry|take|profit|stop|loss|leverage)'
        
        has_tr = bool(re.search(tr_keywords, text, re.IGNORECASE))
        has_en = bool(re.search(en_keywords, text, re.IGNORECASE))
        
        if has_tr and has_en:
            return "mixed"
        elif has_tr:
            return "tr"
        elif has_en:
            return "en"
        else:
            return "unknown"
    
    def _extract_symbol(self, text: str, signal: ParsedSignal) -> Optional[str]:
        """
        Extract trading symbol.
        
        Formats:
        - #btc, btc, btcusdt, btc/usdt, BTC-USDT
        """
        # Find all potential symbols
        matches = self.SYMBOL_PATTERN.findall(text)
        
        if not matches:
            signal.parsing_notes.append("No symbol detected")
            return None
        
        # Filter out blacklist and common words
        valid_symbols = []
        for match in matches:
            # Normalize: uppercase and strip USDT/USD suffix BEFORE blacklist check
            symbol_upper = match.upper()
            
            # Strip suffix to get base symbol
            base_symbol = symbol_upper
            if base_symbol.endswith('USDT'):
                base_symbol = base_symbol[:-4]  # Remove USDT
            elif base_symbol.endswith('USD'):
                base_symbol = base_symbol[:-3]  # Remove USD
            
            symbol_lower = base_symbol.lower()
            
            # Skip blacklist (now checking base symbol, not full pair)
            if symbol_lower in self.BLACKLIST:
                continue
            
            # Skip very short symbols (likely not crypto)
            if len(symbol_lower) < 2:
                continue
            
            # Skip if it's a common English word
            if symbol_lower in {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'what', 'when'}:
                continue
            
            valid_symbols.append(base_symbol)  # Store base symbol, will add USDT later
        
        if not valid_symbols:
            signal.parsing_notes.append(f"All symbols filtered (blacklist): {matches}")
            return None
        
        # Take first valid symbol and normalize to USDT pair
        symbol = valid_symbols[0]
        if not symbol.endswith('USDT') and not symbol.endswith('USD'):
            symbol = f"{symbol}USDT"
        
        # Validate against Binance API
        from utils.binance_validator import is_valid_symbol
        if not is_valid_symbol(symbol):
            signal.parsing_notes.append(f"Symbol not found on Binance: {symbol}")
            return None
        
        signal.parsing_notes.append(f"Symbol detected and validated: {symbol}")
        return symbol
    
    def _extract_side(self, text: str, signal: ParsedSignal) -> Optional[str]:
        """Extract trade side (long/short)."""
        text_lower = text.lower()
        
        # Check for long keywords
        if re.search(self.LONG_KEYWORDS, text_lower):
            signal.parsing_notes.append("Side: LONG")
            return "long"
        
        # Check for short keywords
        if re.search(self.SHORT_KEYWORDS, text_lower):
            signal.parsing_notes.append("Side: SHORT")
            return "short"
        
        signal.parsing_notes.append("Side not detected (defaulting to LONG)")
        return "long"  # Default to long if not specified
    
    def _extract_leverage(self, text: str, signal: ParsedSignal) -> Optional[int]:
        """Extract leverage value."""
        # Pattern: 10x, lev 10, leverage 5, kaldıraç 20
        # Must have either 'x' suffix OR keyword (lev/leverage/kaldıraç)
        lev_pattern = r'(?i)(?:lev|leverage|kaldıraç)\s*(\d{1,3})|(\d{1,3})\s*x\b'
        
        matches = re.findall(lev_pattern, text)
        
        if matches:
            # Extract first non-empty group
            lev = None
            for match in matches:
                if match[0]:  # Keyword + number
                    lev = int(match[0])
                    break
                elif match[1]:  # Number + x
                    lev = int(match[1])
                    break
            
            if lev and 1 <= lev <= 125:  # Sanity check
                signal.parsing_notes.append(f"Leverage: {lev}x")
                return lev
        
        signal.parsing_notes.append("Leverage not detected")
        return None
    
    def _extract_entries(self, text: str, signal: ParsedSignal) -> List[float]:
        """Extract entry prices."""
        # Try finding entry keyword and extract numbers AFTER it
        match = re.search(self.ENTRY_KEYWORDS, text, re.IGNORECASE)
        
        if match:
            # Get position where keyword ends
            start_pos = match.end()
            
            # Extract substring from keyword end, skipping optional colon/whitespace
            remaining = text[start_pos:].lstrip(' \t:')
            
            # Find FIRST newline
            first_newline = remaining.find('\n')
            
            # Find next keyword boundary (TP, SL, leverage, etc.)
            # Include tp1, tp2, hedef1, hedef2, target1, target2 labels, and "take profit"
            next_keyword_pattern = r'\b(?:tp\d*|take\s*profit|hedef\d*|target\s*\d*|targets|sell|sl|stop|zarar|lev|leverage|kaldıraç)\b'
            next_match = re.search(next_keyword_pattern, remaining, re.IGNORECASE)
            
            # Take WHICHEVER comes first: newline or next keyword
            if first_newline != -1 and (not next_match or first_newline < next_match.start()):
                # Newline comes first - take until newline
                entry_text = remaining[:first_newline]
            elif next_match:
                # Keyword comes first - take until keyword
                entry_text = remaining[:next_match.start()]
            else:
                # No boundary - take first 100 chars
                entry_text = remaining[:100]
            
            numbers = normalize_number_list(entry_text)
            
            if numbers:
                signal.parsing_notes.append(f"Entries: {numbers}")
                return numbers
        
        # Fallback: if side is detected, look for number right after side keyword (with or without space)
        if signal.side:
            side_pattern = rf'{self.LONG_KEYWORDS if signal.side == "long" else self.SHORT_KEYWORDS}\s*(\d+(?:[\.,]\d+)?(?:\s*\b(?:k|K|bin|BIN)\b)?)'
            side_matches = re.findall(side_pattern, text, re.IGNORECASE)
            
            if side_matches:
                entry_text = side_matches[0].strip()
                numbers = normalize_number_list(entry_text)
                
                if numbers:
                    signal.parsing_notes.append(f"Entry (after side): {numbers}")
                    return numbers
        
        signal.parsing_notes.append("Entry not detected")
        return []
    
    def _extract_tps(self, text: str, signal: ParsedSignal) -> List[float]:
        """Extract take profit targets."""
        # Try finding TP keyword and extract numbers AFTER it
        match = re.search(self.TP_KEYWORDS, text, re.IGNORECASE)
        
        if match:
            # Get position where keyword ends
            start_pos = match.end()
            
            # Extract substring from keyword end
            remaining = text[start_pos:]
            
            # Skip optional label (e.g., "Hedef 1:" → skip " 1:")
            label_skip_pattern = r'^\s*\d{1,2}\s*:\s*'
            label_match = re.match(label_skip_pattern, remaining)
            if label_match:
                remaining = remaining[label_match.end():]
            else:
                # Just skip whitespace and colon
                remaining = remaining.lstrip(' \t:')
            
            # Find next keyword boundary (SL, entry, leverage, etc.)
            next_keyword_pattern = r'\b(?:sl|stop|zarar|entry|giriş|buy|alım|lev|leverage|kaldıraç)\b'
            next_match = re.search(next_keyword_pattern, remaining, re.IGNORECASE)
            
            if next_match:
                # Extract only until next keyword
                tp_text = remaining[:next_match.start()]
            else:
                # Take first 2 lines (TPs often span multiple lines)
                lines = remaining.split('\n')
                tp_text = '\n'.join(lines[:2]) if len(lines) > 1 else lines[0] if lines else remaining[:150]
            
            # Use TP sequence parser (handles "tp: 1-2-3" and absolute prices)
            entry_price = signal.entries[0] if signal.entries else None
            tps = parse_tp_sequence(tp_text, entry_price)
            
            if tps:
                signal.parsing_notes.append(f"TPs: {tps}")
                return tps
        
        signal.parsing_notes.append("TPs not detected")
        return []
    
    def _extract_sl(self, text: str, signal: ParsedSignal) -> Optional[float]:
        """Extract stop loss."""
        # Try finding SL keyword and extract numbers AFTER it
        match = re.search(self.SL_KEYWORDS, text, re.IGNORECASE)
        
        if match:
            # Get position where keyword ends
            start_pos = match.end()
            
            # Extract substring from keyword end, skipping optional colon/whitespace
            remaining = text[start_pos:].lstrip(' \t:')
            
            # Find next keyword boundary (TP, entry, leverage, etc.)
            next_keyword_pattern = r'\b(?:tp|hedef|target|entry|giriş|buy|alım|lev|leverage|kaldıraç)\b'
            next_match = re.search(next_keyword_pattern, remaining, re.IGNORECASE)
            
            if next_match:
                # Extract only until next keyword
                sl_text = remaining[:next_match.start()]
            else:
                # Take first line only
                first_line_end = remaining.find('\n')
                sl_text = remaining[:first_line_end] if first_line_end != -1 else remaining[:100]
            
            numbers = normalize_number_list(sl_text)
            
            if numbers:
                signal.parsing_notes.append(f"SL: {numbers[0]}")
                return numbers[0]
        
        signal.parsing_notes.append("SL not detected")
        return None
    
    def _infer_market(self, signal: ParsedSignal) -> str:
        """Infer market type (futures/spot) from signal."""
        # If leverage detected → futures
        if signal.leverage_x and signal.leverage_x > 1:
            return "futures"
        
        # If short → futures (spot doesn't allow shorting)
        if signal.side == "short":
            return "futures"
        
        # Default to spot
        return "spot"
    
    def _calculate_confidence(self, signal: ParsedSignal) -> float:
        """
        Calculate confidence score (0-1).
        
        Scoring:
        - Symbol detected: +0.2
        - Side detected: +0.2
        - Entry detected: +0.2
        - TP detected: +0.2
        - SL detected: +0.2
        """
        score = 0.0
        
        if signal.symbol:
            score += 0.2
        
        if signal.side:
            score += 0.2
        
        if signal.entries:
            score += 0.2
        
        if signal.tps:
            score += 0.2
        
        if signal.sl:
            score += 0.2
        
        return round(score, 2)


# Example usage and test
if __name__ == "__main__":
    parser = EnhancedParser()
    
    print("🧪 Enhanced Parser Tests\n")
    
    test_signals = [
        # TR example
        "#btc long entry: 112.191 tp: 113k-114k-115k sl 109500 lev 10x",
        
        # EN example
        "BTCUSDT SHORT\nEntry 112 bin\nTP1 111k, TP2 110k\nSTOP 113200\nkaldıraç 5x",
        
        # Relative TP example
        "eth long 3500 tp: 1-2-3 sl 3400 leverage 20x",
        
        # Missing fields
        "sol pump 200 🚀",
        
        # Garbage
        "join our vip group for signals",
    ]
    
    for i, signal_text in enumerate(test_signals, 1):
        print(f"{'='*60}")
        print(f"Test #{i}")
        print(f"{'='*60}")
        print(f"Input: {signal_text[:80]}...")
        print()
        
        result = parser.parse(signal_text)
        
        print(f"✅ Symbol:     {result.symbol}")
        print(f"✅ Side:       {result.side}")
        print(f"✅ Market:     {result.market}")
        print(f"✅ Leverage:   {result.leverage_x}x" if result.leverage_x else "✅ Leverage:   None")
        print(f"✅ Entries:    {result.entries}")
        print(f"✅ TPs:        {result.tps}")
        print(f"✅ SL:         {result.sl}")
        print(f"✅ Confidence: {result.confidence:.2f}")
        print(f"✅ Locale:     {result.locale}")
        print(f"✅ Valid:      {result.is_valid(min_confidence=0.6)}")
        print()
        print("📝 Notes:")
        for note in result.parsing_notes:
            print(f"   - {note}")
        print()
