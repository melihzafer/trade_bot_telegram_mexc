"""
Adaptive Whitelist Manager - ML-inspired pattern recognition for signals

Learns from successful parses to speed up future processing.
Maintains a cache of proven signal patterns with confidence scores.

Usage:
    whitelist = WhitelistManager()
    
    # Fast path: Check if we've seen this before
    if cached := whitelist.lookup(text):
        return cached  # Instant result!
    
    # Normal path: Parse and learn
    signal = parser.parse(text)
    if signal.symbol:
        whitelist.add(text, signal)  # Learn for next time
"""

import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class WhitelistEntry:
    """Represents a learned signal pattern."""
    
    # Core identification
    pattern_hash: str           # Unique fingerprint
    symbol: str                 # Extracted symbol (e.g., BTCUSDT)
    
    # Pattern features
    fingerprint: Dict[str, any] # Pattern characteristics
    
    # Learning metrics
    success_count: int          # Times successfully parsed
    confidence: float           # 0.0-1.0 confidence score
    
    # Metadata
    first_seen: str            # ISO timestamp
    last_seen: str             # ISO timestamp
    language: str              # tr/en/mixed
    format_type: str           # compact/multiline/labeled
    
    # Extraction cache (for fast path)
    cached_entries: List[float]
    cached_tps: List[float]
    cached_sl: Optional[float]
    cached_leverage: Optional[int]


class PatternExtractor:
    """Extracts characteristic features from signal text."""
    
    @staticmethod
    def extract_fingerprint(text: str) -> Dict[str, any]:
        """
        Generate pattern fingerprint for similarity matching.
        
        Features extracted:
        - Keyword positions (entry, tp, sl positions)
        - Number patterns (how many numbers, where)
        - Language markers (TR/EN keywords)
        - Format type (compact/multiline/labeled)
        """
        text_lower = text.lower()
        
        # Detect keywords and positions
        has_entry = bool(re.search(r'\b(entry|giri[şs]|buy|al[iı]m)\b', text_lower))
        has_tp = bool(re.search(r'\b(tp|take\s*profit|hedef|target|sell)\b', text_lower))
        has_sl = bool(re.search(r'\b(sl|stop|zarar\s*durdur)\b', text_lower))
        has_lev = bool(re.search(r'\b(lev|leverage|kald[iı]ra[çc]|\d+x)\b', text_lower))
        
        # Entry position (relative: start/middle/end)
        entry_match = re.search(r'\b(entry|giri[şs])\b', text_lower)
        entry_pos = 'start' if entry_match and entry_match.start() < len(text) * 0.3 else \
                    'middle' if entry_match and entry_match.start() < len(text) * 0.7 else \
                    'end' if entry_match else None
        
        # Count numbers
        numbers = re.findall(r'\d+(?:[.,]\d+)?', text)
        num_count = len(numbers)
        
        # Detect format type
        has_newlines = '\n' in text
        has_labels = bool(re.search(r'(tp|hedef|target)\s*\d+\s*[:.]', text_lower))
        format_type = 'labeled' if has_labels else \
                      'multiline' if has_newlines else \
                      'compact'
        
        # Detect language
        has_turkish = bool(re.search(r'\b(giri[şs]|hedef|zarar|durdur|kald[iı]ra[çc])\b', text_lower))
        has_english = bool(re.search(r'\b(entry|target|stop|leverage|take|profit)\b', text_lower))
        language = 'mixed' if has_turkish and has_english else \
                   'tr' if has_turkish else \
                   'en' if has_english else \
                   'unknown'
        
        # Symbol position (first word, hashtag, after colon, etc.)
        symbol_context = 'unknown'
        if re.match(r'^\s*[#@]?\w+', text):
            symbol_context = 'first_word'
        elif re.search(r':\s*\w+', text):
            symbol_context = 'after_colon'
        
        return {
            'has_entry': has_entry,
            'has_tp': has_tp,
            'has_sl': has_sl,
            'has_lev': has_lev,
            'entry_pos': entry_pos,
            'num_count': num_count,
            'format_type': format_type,
            'language': language,
            'symbol_context': symbol_context,
        }
    
    @staticmethod
    def generate_hash(text: str, fingerprint: Dict) -> str:
        """
        Generate unique hash for pattern STRUCTURE.
        
        Ignores specific number values to match similar patterns.
        """
        # Normalize text: remove numbers and collapse whitespace
        normalized = re.sub(r'\d+(?:[.,]\d+)?', 'NUM', text.lower())  # Replace numbers with placeholder
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        normalized = re.sub(r'[^\w\s.,:/\-]', '', normalized)  # Remove emojis/special chars
        
        # Create composite key based on STRUCTURE only
        key_parts = [
            normalized[:100],  # Structure (no specific numbers)
            fingerprint.get('format_type', ''),
            fingerprint.get('language', ''),
            fingerprint.get('entry_pos', ''),
            str(fingerprint.get('num_count', 0)),
        ]
        
        composite = '|'.join(str(p) for p in key_parts)
        return hashlib.md5(composite.encode()).hexdigest()


class WhitelistManager:
    """Manages learned signal patterns with adaptive confidence scoring."""
    
    CACHE_FILE = Path("data/signal_whitelist.json")
    MAX_ENTRIES = 1000  # LRU eviction
    CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for fast path
    DECAY_DAYS = 30  # Patterns older than this lose confidence
    
    def __init__(self):
        """Initialize whitelist manager."""
        self.entries: Dict[str, WhitelistEntry] = {}
        self.hit_count = 0
        self.miss_count = 0
        self._load_cache()
    
    def lookup(self, text: str) -> Optional[WhitelistEntry]:
        """
        Ultra-fast path: Check if we've seen this pattern before.
        
        Returns cached entry if confidence is high enough.
        Does NOT update anything (pure read).
        """
        fingerprint = PatternExtractor.extract_fingerprint(text)
        pattern_hash = PatternExtractor.generate_hash(text, fingerprint)
        
        entry = self.entries.get(pattern_hash)
        
        if entry and entry.confidence >= self.CONFIDENCE_THRESHOLD:
            self.hit_count += 1
            return entry
        
        self.miss_count += 1
        return None
    
    def update_after_hit(self, pattern_hash: str) -> None:
        """
        Update entry after successful fast-path use.
        
        Call this AFTER using the fast path result.
        """
        if pattern_hash in self.entries:
            entry = self.entries[pattern_hash]
            entry.last_seen = datetime.now().isoformat()
            entry.success_count += 1
            entry.confidence = min(1.0, entry.confidence + 0.01)  # Small boost
    
    def add(self, text: str, symbol: str, entries: List[float], 
            tps: List[float], sl: Optional[float], leverage: Optional[int],
            language: str = 'unknown') -> None:
        """
        Learn from successful parse.
        
        Adds pattern to whitelist with initial confidence.
        """
        fingerprint = PatternExtractor.extract_fingerprint(text)
        pattern_hash = PatternExtractor.generate_hash(text, fingerprint)
        
        now = datetime.now().isoformat()
        
        if pattern_hash in self.entries:
            # Update existing entry
            entry = self.entries[pattern_hash]
            entry.success_count += 1
            entry.last_seen = now
            entry.confidence = min(1.0, entry.confidence + 0.05)  # Boost confidence
        else:
            # Create new entry
            entry = WhitelistEntry(
                pattern_hash=pattern_hash,
                symbol=symbol,
                fingerprint=fingerprint,
                success_count=1,
                confidence=0.6,  # Initial confidence (below threshold, needs validation)
                first_seen=now,
                last_seen=now,
                language=language,
                format_type=fingerprint['format_type'],
                cached_entries=entries,
                cached_tps=tps,
                cached_sl=sl,
                cached_leverage=leverage,
            )
            self.entries[pattern_hash] = entry
        
        # LRU eviction if too many entries
        if len(self.entries) > self.MAX_ENTRIES:
            self._evict_lru()
        
        # Auto-save periodically
        if len(self.entries) % 10 == 0:
            self.save()
    
    def _evict_lru(self) -> None:
        """Remove least recently used entries."""
        # Sort by last_seen, remove oldest
        sorted_entries = sorted(
            self.entries.items(),
            key=lambda x: (x[1].last_seen, x[1].confidence)
        )
        
        # Remove bottom 10%
        remove_count = self.MAX_ENTRIES // 10
        for pattern_hash, _ in sorted_entries[:remove_count]:
            del self.entries[pattern_hash]
    
    def _apply_decay(self) -> None:
        """Reduce confidence of stale patterns."""
        now = datetime.now()
        decay_threshold = now - timedelta(days=self.DECAY_DAYS)
        
        for entry in self.entries.values():
            last_seen = datetime.fromisoformat(entry.last_seen)
            
            if last_seen < decay_threshold:
                # Decay confidence
                days_stale = (now - last_seen).days - self.DECAY_DAYS
                decay_factor = 0.95 ** (days_stale / 7)  # 5% per week
                entry.confidence *= decay_factor
    
    def save(self) -> None:
        """Persist whitelist to disk."""
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Apply decay before saving
            self._apply_decay()
            
            data = {
                'entries': [asdict(e) for e in self.entries.values()],
                'stats': {
                    'total_entries': len(self.entries),
                    'hit_count': self.hit_count,
                    'miss_count': self.miss_count,
                    'hit_rate': self.hit_count / (self.hit_count + self.miss_count)
                                if (self.hit_count + self.miss_count) > 0 else 0,
                },
                'last_updated': datetime.now().isoformat(),
            }
            
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Whitelist saved: {len(self.entries)} patterns, "
                  f"{data['stats']['hit_rate']:.1%} hit rate")
        
        except Exception as e:
            print(f"⚠️ Failed to save whitelist: {e}")
    
    def _load_cache(self) -> None:
        """Load whitelist from disk."""
        if not self.CACHE_FILE.exists():
            return
        
        try:
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry_dict in data.get('entries', []):
                entry = WhitelistEntry(**entry_dict)
                self.entries[entry.pattern_hash] = entry
            
            stats = data.get('stats', {})
            self.hit_count = stats.get('hit_count', 0)
            self.miss_count = stats.get('miss_count', 0)
            
            print(f"📦 Whitelist loaded: {len(self.entries)} patterns, "
                  f"{stats.get('hit_rate', 0):.1%} historical hit rate")
        
        except Exception as e:
            print(f"⚠️ Failed to load whitelist: {e}")
    
    def get_stats(self) -> Dict:
        """Get whitelist statistics."""
        if not self.entries:
            return {'total_entries': 0}
        
        high_confidence = sum(1 for e in self.entries.values() if e.confidence >= 0.9)
        
        return {
            'total_entries': len(self.entries),
            'high_confidence': high_confidence,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': self.hit_count / (self.hit_count + self.miss_count)
                        if (self.hit_count + self.miss_count) > 0 else 0,
            'avg_confidence': sum(e.confidence for e in self.entries.values()) / len(self.entries),
        }


# Singleton instance
_whitelist_instance: Optional[WhitelistManager] = None


def get_whitelist() -> WhitelistManager:
    """Get or create singleton whitelist manager."""
    global _whitelist_instance
    
    if _whitelist_instance is None:
        _whitelist_instance = WhitelistManager()
    
    return _whitelist_instance


if __name__ == "__main__":
    # Test whitelist system
    whitelist = WhitelistManager()
    
    print("=" * 70)
    print("🧪 Testing Whitelist System")
    print("=" * 70)
    
    # Test pattern extraction
    test_signals = [
        "BTCUSDT LONG entry 50000 tp 52000 55000 sl 48000",
        "ETH/USDT\nLONG\nEntry: 3000\nTP1: 3100\nTP2: 3200\nSL: 2900",
        "#SOL long 100 hedef 105 110 zarar 95",
    ]
    
    for i, text in enumerate(test_signals, 1):
        print(f"\n--- Test {i} ---")
        print(f"Text: {text[:60]}...")
        
        fingerprint = PatternExtractor.extract_fingerprint(text)
        print(f"Fingerprint: {fingerprint}")
        
        pattern_hash = PatternExtractor.generate_hash(text, fingerprint)
        print(f"Hash: {pattern_hash[:16]}...")
    
    print("\n" + "=" * 70)
    print("✅ Whitelist system initialized")
    print(f"📊 Stats: {whitelist.get_stats()}")
