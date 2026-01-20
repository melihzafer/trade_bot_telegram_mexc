"""
Comprehensive test suite for Hybrid Neuro-Symbolic Parser.
Tests the 3-tier routing system (Whitelist → Regex → AI).

Run: python test_hybrid_parser.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.enhanced_parser import EnhancedParser
from utils import logger


async def test_hybrid_parser():
    """Test hybrid parser with various signal types and routing scenarios."""
    
    logger.info("🧪 Testing Hybrid Neuro-Symbolic Parser\n")
    
    # Initialize parser with AI enabled
    parser = EnhancedParser(enable_ai=True)
    
    # Test cases organized by expected routing path
    test_cases = {
        "High-Confidence Regex (Should NOT trigger AI)": [
            {
                "name": "Clear BTC Long Signal",
                "text": "#btc long entry: 42000-41500 tp: 43000-44000-45000 sl 40000 lev 10x",
                "expected_confidence": ">= 0.85"
            },
            {
                "name": "Clear ETH Short Signal",
                "text": "ETHUSDT SHORT\nEntry 2250-2300\nTP1 2200, TP2 2150, TP3 2100\nSTOP 2400\nlev 20x",
                "expected_confidence": ">= 0.85"
            },
        ],
        "Low-Confidence Regex (SHOULD trigger AI)": [
            {
                "name": "Ambiguous Signal - No Symbol",
                "text": "Long entry 100, targets 105-110-115, stop 95",
                "expected_confidence": "< 0.85"
            },
            {
                "name": "Natural Language Signal",
                "text": "I think SOL looks good here around $95-94. Targeting $98, $100, and $105. Cut losses at $92. Use 15x leverage.",
                "expected_confidence": "< 0.85"
            },
            {
                "name": "Turkish Informal Signal",
                "text": "BNB güzel gözüküyor, 500 civarı girelim, hedefler 550-600, stop 450",
                "expected_confidence": "< 0.85"
            },
        ],
        "Invalid/Garbage (Both should fail gracefully)": [
            {
                "name": "No Signal Content",
                "text": "Join our premium VIP group for exclusive signals!",
                "expected_confidence": "< 0.4"
            },
            {
                "name": "Just Random Numbers",
                "text": "123 456 789 000",
                "expected_confidence": "< 0.4"
            },
        ]
    }
    
    # Run all test cases
    for category, tests in test_cases.items():
        logger.info(f"\n{'='*70}")
        logger.info(f"📂 Category: {category}")
        logger.info(f"{'='*70}\n")
        
        for test in tests:
            logger.info(f"🧪 Test: {test['name']}")
            logger.info(f"📝 Input: {test['text'][:80]}...")
            logger.info(f"📊 Expected Confidence: {test['expected_confidence']}\n")
            
            try:
                result = await parser.parse(test["text"])
                
                # Display results
                if result.symbol:
                    logger.success(f"✅ Parsed Successfully!")
                    logger.info(f"   Symbol: {result.symbol}")
                    logger.info(f"   Side: {result.side}")
                    logger.info(f"   Entry: {result.entries}")
                    logger.info(f"   TPs: {result.tps}")
                    logger.info(f"   SL: {result.sl}")
                    logger.info(f"   Leverage: {result.leverage_x}x" if result.leverage_x else "   Leverage: None")
                    logger.info(f"   Confidence: {result.confidence:.2f}")
                else:
                    logger.warn(f"⚠️  No Valid Signal Detected (Confidence: {result.confidence:.2f})")
                
                # Show routing path
                logger.info(f"\n📍 Routing Path:")
                for note in result.parsing_notes:
                    if "Routing:" in note or "Path" in note:
                        logger.info(f"   {note}")
                
            except Exception as e:
                logger.error(f"❌ Test failed with exception: {type(e).__name__}: {e}")
            
            logger.info(f"\n{'-'*70}\n")
    
    # Display final statistics
    logger.info(f"\n{'='*70}")
    logger.success("📊 Parser Statistics (Final)")
    logger.info(f"{'='*70}\n")
    
    stats = parser.get_stats()
    for key, value in stats.items():
        logger.info(f"   {key.replace('_', ' ').title()}: {value}")
    
    logger.info(f"\n{'='*70}")
    logger.success("✅ All tests completed!")
    logger.info(f"{'='*70}\n")


async def test_whitelist_learning():
    """Test that the parser learns patterns and uses fast path on repeat."""
    
    logger.info("\n🧪 Testing Whitelist Learning\n")
    
    parser = EnhancedParser(enable_ai=True)
    
    # Same signal repeated 3 times
    signal_text = "#btc long entry: 42000 tp: 43000-44000-45000 sl 40000 lev 10x"
    
    logger.info("📝 Parsing the same signal 3 times...\n")
    
    for i in range(1, 4):
        logger.info(f"Parse #{i}")
        result = await parser.parse(signal_text)
        
        # Check routing
        routing_path = "Unknown"
        for note in result.parsing_notes:
            if "Routing:" in note:
                routing_path = note
                break
        
        logger.info(f"   {routing_path}")
        logger.info(f"   Confidence: {result.confidence:.2f}\n")
    
    stats = parser.get_stats()
    logger.info(f"Fast Path Hits: {stats['fast_path_hits']}")
    logger.info(f"Expected: Parse #1 = Full Parse, Parse #2-3 = Fast Path")
    
    if stats['fast_path_hits'] >= 2:
        logger.success("\n✅ Whitelist learning works correctly!\n")
    else:
        logger.warn("\n⚠️  Whitelist learning may not be working as expected\n")


async def test_ai_override():
    """Test that AI can override low-confidence regex results."""
    
    logger.info("\n🧪 Testing AI Override (Low Confidence → AI)\n")
    
    # This signal should have low regex confidence but AI should parse it
    ambiguous_signal = "BNB around 500, targeting 550 and 600, stop at 450"
    
    parser = EnhancedParser(enable_ai=True)
    
    logger.info(f"📝 Input: {ambiguous_signal}\n")
    
    result = await parser.parse(ambiguous_signal)
    
    # Check if AI was used
    ai_used = any("AI Path" in note for note in result.parsing_notes)
    
    if ai_used:
        logger.success("✅ AI Path was triggered!")
        logger.info(f"   Symbol: {result.symbol}")
        logger.info(f"   Confidence: {result.confidence:.2f}")
    else:
        logger.warn("⚠️  AI Path was NOT triggered")
        logger.info(f"   Confidence: {result.confidence:.2f}")
        
    logger.info(f"\n📍 Routing:")
    for note in result.parsing_notes:
        if "Routing:" in note or "Path" in note:
            logger.info(f"   {note}")
    
    logger.info("")


if __name__ == "__main__":
    async def main():
        # Run all tests
        await test_hybrid_parser()
        await test_whitelist_learning()
        await test_ai_override()
        
        logger.success("\n🎉 All hybrid parser tests completed!\n")
    
    asyncio.run(main())
