"""
Test to demonstrate AI Parser improvements with retry mechanism.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.ai_parser import AIParser

async def test_ai_improvements():
    """Test AI parser with error handling and retry."""
    
    # Test signal that might cause issues
    test_signal = """📊 İŞLEM TÜRÜ: LONG
COİN ADI: ZEC/USDT
✅ Giriş Bölgesi: 366.7 - 356
⚡️ Hedefler: 375 - 379.6 - 385"""
    
    print("="*60)
    print("TESTING AI PARSER WITH IMPROVED ERROR HANDLING")
    print("="*60)
    print(f"\nInput Signal:\n{test_signal}\n")
    
    try:
        # Initialize AI parser
        parser = AIParser()
        
        # Parse with retry mechanism
        result = await parser.parse_signal(test_signal, max_retries=3)
        
        # Display results
        print("="*60)
        print("AI PARSER RESULT:")
        print("="*60)
        
        if result.get("signal") is False:
            print(f"❌ No signal detected")
            if "error" in result:
                print(f"Error: {result['error']}")
        else:
            print(f"✅ Signal parsed successfully!")
            print(f"Symbol: {result.get('symbol')}")
            print(f"Side: {result.get('side')}")
            print(f"Entry: {result.get('entry')}")
            print(f"TP: {result.get('tp')}")
            print(f"SL: {result.get('sl')}")
            print(f"Leverage: {result.get('leverage')}")
            print(f"Confidence: {result.get('confidence')}")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_improvements())
