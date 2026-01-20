"""
Test the enhanced parser with the Turkish signal format.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.enhanced_parser import EnhancedParser

async def test_turkish_signal():
    """Test Turkish signal parsing."""
    
    # The problematic signal from the user
    test_signal = """📊 İŞLEM TÜRÜ: LONG
COİN ADI: ZEC/USDT
✅ Giriş Bölgesi: 366.7 - 356
⚡️ Hedefler: 375 - 379.6 - 385"""
    
    print("="*60)
    print("TESTING ENHANCED PARSER WITH TURKISH SIGNAL")
    print("="*60)
    print(f"\nInput Signal:\n{test_signal}\n")
    
    # Initialize parser (without AI for this test)
    parser = EnhancedParser(enable_ai=False)
    
    # Parse
    result = await parser.parse(test_signal, confidence_threshold=0.6)
    
    # Display results
    print("="*60)
    print("PARSED RESULT:")
    print("="*60)
    print(f"Symbol: {result.symbol}")
    print(f"Side: {result.side}")
    print(f"Entries: {result.entries}")
    print(f"Take Profits: {result.tps}")
    print(f"Stop Loss: {result.sl}")
    print(f"Leverage: {result.leverage_x}")
    print(f"Confidence: {result.confidence}")
    print(f"Locale: {result.locale}")
    print(f"\nParsing Notes:")
    for note in result.parsing_notes:
        print(f"  - {note}")
    
    print("\n" + "="*60)
    print(f"VALID: {result.is_valid(min_confidence=0.6)}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_turkish_signal())
