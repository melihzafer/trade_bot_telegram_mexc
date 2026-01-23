"""
Enhanced Signal Parser with Confidence Scoring & Adaptive Whitelist
Supports TR/EN mixed signals with ML-inspired pattern learning.

🧠 NEURO-SYMBOLIC HYBRID ARCHITECTURE (Project Chimera)
- Fast Path: Whitelist lookup (cached patterns)
- Symbolic Path: Regex-based parsing (rule-based)
- Neural Path: AI-powered parsing (DeepSeek R1)

Author: OMNI Tech Solutions
Created: 2025
Updated: 2025 (Chimera Integration)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from parsers.number_normalizer import normalize_number, normalize_number_list, parse_tp_sequence, clean_text
from utils.whitelist_manager import WhitelistManager

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


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
    
    # TR/EN keywords (non-capturing groups) - ENHANCED WITH TURKISH FORMATS
    LONG_KEYWORDS = r'(?i)\b(?:long|buy|al|alım|giriş|işlem\s*türü:\s*long|yön:\s*long)\b'
    SHORT_KEYWORDS = r'(?i)\b(?:short|sell|sat|satış|kısa|işlem\s*türü:\s*short|yön:\s*short)\b'
    
    ENTRY_KEYWORDS = r'(?i)\b(?:entry|giriş|giriş\s*bölgesi|buy|alım|long\s*entry|short\s*entry)\b'
    TP_KEYWORDS = r'(?i)\b(?:tp\d*|take\s*profit|hedef\d*|hedefler|targets?|sell)\b'
    SL_KEYWORDS = r'(?i)\b(?:sl|stop|stoploss|stop\s*loss|zarar\s*durdur|zarar\s*kes)\b'
    LEVERAGE_KEYWORDS = r'(?i)\b(?:lev|leverage|kaldıraç|(\d{1,3})x)\b'
    
    # Turkish-specific symbol keywords for better detection
    SYMBOL_KEYWORDS = r'(?i)\b(?:coin\s*adı|coin\s*adi|sembol|symbol|pair|çift)\b'
    
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
    
    def __init__(self, enable_ai: bool = True):
        """
        Initialize parser with whitelist and AI fallback.
        
        Args:
            enable_ai: Enable AI parser for low-confidence signals (default: True)
        """
        self.whitelist = WhitelistManager()
        self.fast_path_hits = 0
        self.regex_path_hits = 0
        self.ai_path_hits = 0
        self.full_parse_count = 0
        
        # Initialize AI parser (lazy loading to avoid import errors)
        self.ai_parser = None
        self.enable_ai = enable_ai
        
        if enable_ai:
            try:
                from parsers.multi_ai_parser import MultiAIParser
                self.ai_parser = MultiAIParser()
                logger.info("🧠 AI Parser enabled (Multi-Provider: Groq → Ollama → OpenRouter → Local)")
            except Exception as e:
                logger.warn(f"⚠️  AI Parser initialization failed: {e}")
                logger.warn("Falling back to Regex-only mode")
                self.enable_ai = False
    
    async def parse(self, text: str, confidence_threshold: float = 0.75) -> ParsedSignal:
        """
        Parse trading signal using Hybrid Neuro-Symbolic Architecture.
        
        🏗️ ARCHITECTURE (3-Tier Routing):
        
        Tier 1 (⚡ FAST PATH): Check whitelist for known pattern
        ├─ If hit → Return cached result (ultra-fast, no validation)
        └─ If miss → Continue to Tier 2
        
        Tier 2 (🦁 REGEX PATH): Rule-based parsing
        ├─ If confidence >= 0.85 → Return regex result (trust symbolic logic)
        └─ If confidence < 0.85 → Continue to Tier 3
        
        Tier 3 (🧠 AI PATH): Neural network fallback
        ├─ Call DeepSeek R1 for complex/ambiguous signals
        ├─ If AI succeeds → Return AI result (neural override)
        └─ If AI fails → Return low-confidence regex result (best effort)
        
        Args:
            text: Raw signal text (TR/EN mixed)
            confidence_threshold: Threshold to trigger AI fallback (default: 0.75)
        
        Returns:
            ParsedSignal with confidence score and routing metadata
        """
        # ============================================================
        # TIER 1: FAST PATH (Whitelist Lookup)
        # ============================================================
        whitelist_entry = self.whitelist.lookup(text)
        
        if whitelist_entry:
            self.fast_path_hits += 1
            logger.debug("⚡ Fast Path: Whitelist hit")
            signal = self._fast_parse(text, whitelist_entry)
            signal.parsing_notes.append("🔥 Routing: Fast Path (Whitelist)")
            return signal
        
        # ============================================================
        # TIER 2: REGEX PATH (Rule-Based Parsing)
        # ============================================================
        self.full_parse_count += 1
        
        # Run full regex-based extraction
        regex_signal = await self._full_regex_parse(text)
        
        # Check confidence threshold
        if regex_signal.confidence >= confidence_threshold:
            self.regex_path_hits += 1
            logger.info(f"🦁 Regex Path: High confidence ({regex_signal.confidence:.2f}) - Symbol: {regex_signal.symbol}")
            regex_signal.parsing_notes.append(f"🦁 Routing: Regex Path (Confidence: {regex_signal.confidence:.2f})")
            
            # LEARN: Add successful parse to whitelist
            if regex_signal.symbol and regex_signal.confidence >= 0.6:
                self.whitelist.add(
                    text=text,
                    symbol=regex_signal.symbol,
                    entries=regex_signal.entries,
                    tps=regex_signal.tps,
                    sl=regex_signal.sl,
                    leverage=regex_signal.leverage_x,
                    language=regex_signal.locale
                )
            
            return regex_signal
        
        # ============================================================
        # TIER 3: AI PATH (Neural Fallback)
        # ============================================================
        if self.enable_ai and self.ai_parser:
            logger.info(f"🧠 AI Path: Low confidence ({regex_signal.confidence:.2f}) - Calling AI Parser...")
            
            try:
                ai_result = await self.ai_parser.parse_signal(text)
                
                # Check if AI successfully parsed the signal
                if ai_result.get("signal") is not False:
                    self.ai_path_hits += 1
                    
                    # Convert AI result to ParsedSignal
                    ai_signal = self._convert_ai_to_parsed_signal(text, ai_result)
                    
                    # Defensive logging with None checks
                    symbol_str = ai_signal.symbol or "UNKNOWN"
                    side_str = ai_signal.side or "UNKNOWN"
                    confidence_str = f"{ai_signal.confidence:.2f}" if ai_signal.confidence else "0.00"
                    
                    logger.success(f"🧠 AI Path: Successfully parsed {symbol_str} {side_str} (Confidence: {confidence_str})")
                    ai_signal.parsing_notes.append(f"🧠 Routing: AI Path (Regex confidence too low: {regex_signal.confidence:.2f})")
                    
                    # LEARN: Add AI-parsed signal to whitelist (with None checks)
                    if (ai_signal.symbol and 
                        ai_signal.confidence is not None and 
                        ai_signal.confidence >= 0.6):
                        self.whitelist.add(
                            text=text,
                            symbol=ai_signal.symbol,
                            entries=ai_signal.entries,
                            tps=ai_signal.tps,
                            sl=ai_signal.sl,
                            leverage=ai_signal.leverage_x,
                            language=ai_signal.locale
                        )
                    
                    return ai_signal
                else:
                    # AI couldn't parse it either
                    error_msg = ai_result.get("error", "Unknown")
                    logger.warn(f"🧠 AI Path: Failed to parse - {error_msg}")
                    regex_signal.parsing_notes.append(f"🧠 AI Path attempted but failed: {error_msg}")
            
            except Exception as e:
                logger.error(f"🧠 AI Path: Exception - {type(e).__name__}: {e}")
                regex_signal.parsing_notes.append(f"🧠 AI Path error: {str(e)}")
        else:
            # AI disabled or not available
            logger.debug("🧠 AI Path: Disabled or unavailable")
            regex_signal.parsing_notes.append("🧠 AI Path: Disabled")
        
        # ============================================================
        # FALLBACK: Return low-confidence regex result
        # ============================================================
        logger.warn(f"⚠️  Fallback: Returning low-confidence regex result ({regex_signal.confidence:.2f})")
        regex_signal.parsing_notes.append(f"⚠️  Routing: Fallback (Low confidence: {regex_signal.confidence:.2f})")
        return regex_signal
    
    async def _full_regex_parse(self, text: str) -> ParsedSignal:
        """
        Full regex-based parsing (legacy logic, now async-compatible).
        
        This is the original rule-based parser extracted into a separate method
        to support the hybrid architecture.
        """
        signal = ParsedSignal(raw_text=text)
        
        # Clean text (remove URLs, emojis, extra whitespace)
        cleaned = clean_text(text)
        
        # Detect locale (TR vs EN vs mixed)
        signal.locale = self._detect_locale(cleaned)
        
        # Try Turkish format first (if detected as Turkish)
        if signal.locale in ["tr", "mixed"]:
            turkish_signal = self._parse_turkish_format(text, signal)
            if turkish_signal and turkish_signal.confidence >= 0.8:
                logger.info(f"🇹🇷 Turkish Format Parser: High confidence ({turkish_signal.confidence:.2f})")
                return turkish_signal
        
        # Extract fields using standard regex patterns
        signal.symbol = self._extract_symbol(cleaned, signal)
        signal.side = self._extract_side(cleaned, signal)
        signal.leverage_x = self._extract_leverage(cleaned, signal)
        signal.entries = self._extract_entries(cleaned, signal)
        signal.tps = self._extract_tps(cleaned, signal)
        signal.sl = self._extract_sl(cleaned, signal)
        signal.market = self._infer_market(signal)
        
        # Calculate confidence score
        signal.confidence = self._calculate_confidence(signal)
        
        return signal
    
    def _parse_turkish_format(self, text: str, base_signal: ParsedSignal) -> Optional[ParsedSignal]:
        """
        Dedicated parser for Turkish signal format.
        
        Expected format:
        📊 İŞLEM TÜRÜ: LONG
        COİN ADI: ZEC/USDT
        ✅ Giriş Bölgesi: 366.7 - 356
        ⚡️ Hedefler: 375 - 379.6 - 385
        
        Returns:
            ParsedSignal if successfully parsed, None otherwise
        """
        signal = ParsedSignal(raw_text=text)
        signal.locale = "tr"
        
        # Extract Side (İŞLEM TÜRÜ or YÖN)
        side_pattern = r'(?:İŞLEM\s*TÜRÜ|YÖN)\s*:\s*(LONG|SHORT)'
        side_match = re.search(side_pattern, text, re.IGNORECASE)
        if side_match:
            signal.side = side_match.group(1).lower()
            signal.parsing_notes.append(f"Turkish Side: {signal.side}")
        
        # Extract Symbol (COİN ADI or SEMBOL)
        symbol_pattern = r'(?:COİN\s*AD[IİıI]|SEMBOL)\s*:\s*([A-Z0-9/\-]+)'
        symbol_match = re.search(symbol_pattern, text, re.IGNORECASE)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper()
            # Normalize: remove slashes and dashes
            raw_symbol = raw_symbol.replace('/', '').replace('-', '')
            
            # Ensure USDT suffix
            if not raw_symbol.endswith('USDT') and not raw_symbol.endswith('USD'):
                raw_symbol = f"{raw_symbol}USDT"
            
            # Validate
            from utils.binance_validator import is_valid_symbol
            if is_valid_symbol(raw_symbol):
                signal.symbol = raw_symbol
                signal.parsing_notes.append(f"Turkish Symbol: {signal.symbol}")
        
        # Extract Entry (Giriş Bölgesi or GİRİŞ)
        entry_pattern = r'(?:Giriş\s*Bölgesi|GİRİŞ)\s*:\s*([\d\.\s\-]+)'
        entry_match = re.search(entry_pattern, text, re.IGNORECASE)
        if entry_match:
            entry_text = entry_match.group(1)
            from parsers.number_normalizer import normalize_number_list
            signal.entries = normalize_number_list(entry_text)
            signal.parsing_notes.append(f"Turkish Entries: {signal.entries}")
        
        # Extract Take Profits (Hedefler or HEDEF)
        tp_pattern = r'(?:Hedefler|HEDEF)\s*:\s*([\d\.\s\-]+)'
        tp_match = re.search(tp_pattern, text, re.IGNORECASE)
        if tp_match:
            tp_text = tp_match.group(1)
            from parsers.number_normalizer import normalize_number_list
            signal.tps = normalize_number_list(tp_text)
            signal.parsing_notes.append(f"Turkish TPs: {signal.tps}")
        
        # Extract Stop Loss (Zararı Durdur or STOP)
        sl_pattern = r'(?:Zarar[ıi]\s*Durdur|Zarar\s*Kes|STOP)\s*:\s*([\d\.]+)'
        sl_match = re.search(sl_pattern, text, re.IGNORECASE)
        if sl_match:
            from parsers.number_normalizer import normalize_number
            signal.sl = normalize_number(sl_match.group(1))
            signal.parsing_notes.append(f"Turkish SL: {signal.sl}")
        
        # Calculate confidence
        signal.confidence = self._calculate_confidence(signal)
        signal.market = self._infer_market(signal)
        
        # Only return if we have at least symbol and side
        if signal.symbol and signal.side:
            signal.parsing_notes.append("🇹🇷 Parsed with Turkish Format Parser")
            return signal
        
        return None
    
    def _convert_ai_to_parsed_signal(self, text: str, ai_result: Dict) -> ParsedSignal:
        """
        Convert AI parser result (dict) to ParsedSignal object.
        
        Args:
            text: Original signal text
            ai_result: Dictionary from AIParser.parse_signal()
        
        Returns:
            ParsedSignal object with AI-extracted data
        """
        signal = ParsedSignal(raw_text=text)
        
        # Map AI fields to ParsedSignal
        signal.symbol = ai_result.get("symbol")
        
        # Normalize side (handle None, empty string, or lowercase)
        side_raw = ai_result.get("side")
        if side_raw and isinstance(side_raw, str):
            signal.side = side_raw.strip().lower()
        else:
            signal.side = None
        
        signal.leverage_x = ai_result.get("leverage")
        signal.entries = ai_result.get("entry", [])
        signal.tps = ai_result.get("tp", [])
        signal.sl = ai_result.get("sl")
        
        # Handle confidence with default fallback
        confidence_raw = ai_result.get("confidence")
        if confidence_raw is not None and isinstance(confidence_raw, (int, float)):
            signal.confidence = float(confidence_raw)
        else:
            signal.confidence = 0.8  # Default if missing
        
        # Infer market and locale
        signal.market = self._infer_market(signal)
        signal.locale = self._detect_locale(text)
        
        # Add AI metadata to notes
        if hasattr(self.ai_parser, 'get_stats'):
            # Multi-provider stats
            stats = self.ai_parser.get_stats()
            active_providers = [name for name, data in stats.items() if data['enabled']]
            signal.parsing_notes.append(f"AI Providers: {', '.join(active_providers)}")
        else:
            signal.parsing_notes.append(f"AI Provider: Multi-Provider System")
        
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
            'regex_path_hits': self.regex_path_hits,
            'ai_path_hits': self.ai_path_hits,
            'full_parses': self.full_parse_count,
            'hit_rate': f"{hit_rate*100:.1f}%",
            'ai_usage_rate': f"{(self.ai_path_hits/total*100) if total > 0 else 0:.1f}%",
            'whitelist_patterns': whitelist_stats.get('total_entries', 0),
            'whitelist_hit_rate': f"{whitelist_stats.get('hit_rate', 0)*100:.1f}%",
            'ai_enabled': self.enable_ai,
        }
    
    def _detect_locale(self, text: str) -> str:
        """Detect text locale (tr, en, or mixed)."""
        tr_keywords = r'(giriş|giriş\s*bölgesi|alım|hedef|hedefler|zarar|durdur|kes|kaldıraç|bin|işlem\s*türü|coin\s*ad[iı]|sembol)'
        en_keywords = r'(entry|take\s*profit|stop\s*loss|leverage|targets)'
        
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
        - COİN ADI: ZECUSDT, SEMBOL: BTCUSDT (Turkish format)
        """
        # Check for Turkish symbol keyword first (COİN ADI, SEMBOL, etc.)
        symbol_keyword_match = re.search(
            r'(?i)(?:coin\s*ad[iı]|sembol|symbol|pair|çift)\s*:\s*([A-Za-z]{2,10}(?:/|)(?:usdt|usd)?)',
            text
        )
        
        if symbol_keyword_match:
            # Extract the symbol after keyword
            symbol_text = symbol_keyword_match.group(1).strip().upper()
            
            # Normalize (remove slashes, ensure USDT suffix)
            symbol_text = symbol_text.replace('/', '').replace('-', '')
            
            # Get base symbol
            if symbol_text.endswith('USDT'):
                base_symbol = symbol_text[:-4]
            elif symbol_text.endswith('USD'):
                base_symbol = symbol_text[:-3]
            else:
                base_symbol = symbol_text
            
            # Check blacklist
            if base_symbol.lower() not in self.BLACKLIST and len(base_symbol) >= 2:
                symbol = f"{base_symbol}USDT"
                
                # Validate against Binance API
                from utils.binance_validator import is_valid_symbol
                if is_valid_symbol(symbol):
                    signal.parsing_notes.append(f"Symbol detected from Turkish keyword: {symbol}")
                    return symbol
        
        # Fallback to regex-based symbol detection
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
            # Include tp1, tp2, hedef1, hedef2, hedefler, target1, target2 labels, and "take profit"
            next_keyword_pattern = r'\b(?:tp\d*|take\s*profit|hedef\d*|hedefler|target\s*\d*|targets|sell|sl|stop|zarar|lev|leverage|kaldıraç)\b'
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
    import asyncio
    
    async def main():
        parser = EnhancedParser(enable_ai=True)
        
        print("🧪 Enhanced Parser Tests (Hybrid Neuro-Symbolic)\n")
        
        test_signals = [
            # TR example
            "#btc long entry: 112.191 tp: 113k-114k-115k sl 109500 lev 10x",
            
            # EN example
            "BTCUSDT SHORT\nEntry 112 bin\nTP1 111k, TP2 110k\nSTOP 113200\nkaldıraç 5x",
            
            # Relative TP example
            "eth long 3500 tp: 1-2-3 sl 3400 leverage 20x",
            
            # Missing fields (should trigger AI)
            "sol pump 200 🚀",
            
            # Ambiguous signal (should trigger AI)
            "BNB looks good here, targeting 500-550-600, cut at 450, 10x",
            
            # Garbage
            "join our vip group for signals",
        ]
        
        for i, signal_text in enumerate(test_signals, 1):
            print(f"{'='*60}")
            print(f"Test #{i}")
            print(f"{'='*60}")
            print(f"Input: {signal_text[:80]}...")
            print()
            
            result = await parser.parse(signal_text)
            
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
        
        # Print statistics
        print(f"{'='*60}")
        print("📊 Parser Statistics")
        print(f"{'='*60}")
        stats = parser.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        print()
    
    asyncio.run(main())
