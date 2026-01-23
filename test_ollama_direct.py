"""
Quick Ollama connectivity test
"""
import asyncio
from openai import AsyncOpenAI

async def test_ollama():
    print("Testing Ollama connectivity...")
    print("=" * 60)
    
    try:
        client = AsyncOpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1",
            timeout=30
        )
        
        print("\n1. Testing basic chat completion...")
        response = await client.chat.completions.create(
            model="qwen3:8b",
            messages=[
                {"role": "user", "content": "Say 'Hello' in JSON format like {\"message\": \"Hello\"}"}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        print(f"   Response: {response.choices[0].message.content}")
        
        print("\n2. Testing with trading signal...")
        response = await client.chat.completions.create(
            model="qwen3:8b",
            messages=[
                {"role": "system", "content": "You are a JSON parser. Output ONLY valid JSON, no explanations."},
                {"role": "user", "content": 'Extract trading info and return JSON: {"symbol": "BTCUSDT", "side": "LONG"}'}
            ],
            temperature=0.0,
            max_tokens=100
        )
        
        print(f"   Response: {response.choices[0].message.content}")
        
        print("\n✓ Ollama is working!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is Ollama running?")
        print("     Windows: Check Task Manager for 'ollama'")
        print("     Or run: Get-Process ollama")
        print("")
        print("  2. Start Ollama if not running:")
        print("     ollama serve")
        print("")
        print("  3. Is the model downloaded?")
        print("     ollama list")
        print("     ollama pull qwen3:8b")
        print("")
        print("  4. Test directly:")
        print("     ollama run qwen3:8b 'Hello'")

if __name__ == "__main__":
    asyncio.run(test_ollama())
