"""
Test script for AI Parser module.
Tests the AIParser with sample signals.

Run: python test_ai_parser.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.ai_parser import AIParser
from utils import logger


async def test_ai_parser():
    """Test AI parser with various signal formats."""
    
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("⚠️  OPENROUTER_API_KEY not set in environment")
        logger.info("Please set OPENROUTER_API_KEY in your .env file")
        return

    logger.info("🧪 Testing AI Parser Module...")
    
    # Initialize parser
    try:
        parser = AIParser()
        logger.success("✅ AIParser initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AIParser: {e}")
        return

    # Test cases
    test_signals = [
        {
            "name": "Standard English Signal",
            "text": """
            🔥 BTC/USDT LONG
            Entry: 42,000 - 41,500
            Targets: 43,000 / 44,000 / 45,000
            Stop Loss: 40,000
            Leverage: 10x
            """
        },
        {
            "name": "Turkish Signal",
            "text": """
            📊 ETH/USDT SHORT
            Giriş: 2.250 - 2.300
            Hedefler: 2.200 / 2.150 / 2.100
            Stop: 2.400
            Kaldıraç: 20x
            """
        },
        {
            "name": "Mixed Format",
            "text": """
            COIN: SOL
            Direction: LONG 🚀
            Entry Zone: $95.50 to $94.00
            TP1: $98.00
            TP2: $100.00  
            TP3: $105.00
            SL: $92.00
            Use 15x leverage
            """
        },
        {
            "name": "No Signal",
            "text": "Just some random text about crypto markets today."
        }
    ]

    # Run tests
    for i, test_case in enumerate(test_signals, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test {i}: {test_case['name']}")
        logger.info(f"{'='*60}")
        
        try:
            result = await parser.parse_signal(test_case["text"])
            
            if result.get("signal") is False:
                logger.warn(f"❌ No signal detected: {result.get('error', 'N/A')}")
            else:
                logger.success("✅ Signal parsed successfully!")
                logger.info(f"   Symbol: {result.get('symbol')}")
                logger.info(f"   Side: {result.get('side')}")
                logger.info(f"   Entry: {result.get('entry')}")
                logger.info(f"   Take Profits: {result.get('tp')}")
                logger.info(f"   Stop Loss: {result.get('sl')}")
                logger.info(f"   Leverage: {result.get('leverage')}")
                logger.info(f"   Confidence: {result.get('confidence')}")
        
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")

    logger.info(f"\n{'='*60}")
    logger.success("🎉 AI Parser tests completed!")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_ai_parser())
