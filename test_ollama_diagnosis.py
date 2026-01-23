"""
🔬 Ollama Diagnostic Script
Comprehensive testing for Ollama signal parsing issues.

Usage:
    python test_ollama_diagnosis.py
"""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from openai import AsyncOpenAI
from utils.logger import info, success, error, warn
from utils.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_CONTEXT_SIZE


class OllamaDiagnostic:
    """Diagnostic tool for Ollama issues."""
    
    def __init__(self):
        self.url = OLLAMA_URL or "http://localhost:11434/v1"
        self.model = OLLAMA_MODEL or "qwen3:8b"
        self.context_size = OLLAMA_CONTEXT_SIZE or 8192
        
        self.client = AsyncOpenAI(
            api_key="ollama",
            base_url=self.url,
            timeout=60
        )
    
    async def test_connection(self):
        """Test basic Ollama connection."""
        info("=" * 70)
        info("TEST 1: Connection Test")
        info("=" * 70)
        info(f"URL: {self.url}")
        info(f"Model: {self.model}")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Say 'hello' in JSON: {\"message\": \"hello\"}"}
                ],
                temperature=0.1,
                max_tokens=100,
                extra_body={
                    "num_ctx": self.context_size,
                    "num_predict": 100
                }
            )
            
            content = response.choices[0].message.content
            success(f"✅ Connection successful!")
            info(f"Raw response: {content}")
            
            return True
            
        except Exception as e:
            error(f"❌ Connection failed: {e}")
            error("   Is Ollama running? Try: ollama serve")
            return False
    
    async def test_simple_json(self):
        """Test simple JSON output."""
        info("\n" + "=" * 70)
        info("TEST 2: Simple JSON Response")
        info("=" * 70)
        
        prompt = """Return this exact JSON (no extra text):
{"test": "success", "number": 123}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=200,
                extra_body={
                    "num_ctx": self.context_size,
                    "num_predict": 200
                }
            )
            
            content = response.choices[0].message.content.strip()
            info(f"Raw response: {content}")
            info(f"Length: {len(content)} chars")
            
            # Try to parse
            try:
                parsed = json.loads(content)
                success(f"✅ Valid JSON! {parsed}")
                return True
            except json.JSONDecodeError as e:
                error(f"❌ Invalid JSON: {e}")
                
                # Try cleaning
                cleaned = self._clean_json(content)
                info(f"Cleaned: {cleaned}")
                
                try:
                    parsed = json.loads(cleaned)
                    warn(f"⚠️ Valid after cleaning: {parsed}")
                    return True
                except:
                    error("❌ Still invalid after cleaning")
                    return False
                    
        except Exception as e:
            error(f"❌ Request failed: {e}")
            return False
    
    async def test_signal_parsing(self):
        """Test actual signal parsing."""
        info("\n" + "=" * 70)
        info("TEST 3: Signal Parsing")
        info("=" * 70)
        
        test_signal = """🟢 LONG
💲 BTCUSDT
📈 Entry: 50000
🎯 Target: 52000
🛑 Stop Loss: 48000"""
        
        system_prompt = """You are a JSON parser for cryptocurrency trading signals. Return ONLY valid JSON.

OUTPUT FORMAT - You must return EXACTLY this structure:
{"symbol": "BTCUSDT", "side": "LONG", "entry": [42000.0], "tp": [43000.0, 44000.0], "sl": 40000.0, "leverage": 10, "confidence": 0.9}

OR if no signal detected:
{"signal": false}

CRITICAL: Return ONLY the JSON object. No explanations, no markdown, no extra text."""
        
        info(f"Signal to parse:\n{test_signal}\n")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this trading signal:\n\n{test_signal}"}
                ],
                temperature=0.1,
                max_tokens=500,
                extra_body={
                    "num_ctx": self.context_size,
                    "num_predict": 500
                }
            )
            
            content = response.choices[0].message.content.strip()
            info(f"Raw response:\n{content}\n")
            info(f"Length: {len(content)} chars")
            
            # Try to parse
            try:
                parsed = json.loads(content)
                success(f"✅ Valid JSON!")
                info(f"Parsed signal: {json.dumps(parsed, indent=2)}")
                return True
            except json.JSONDecodeError as e:
                error(f"❌ Invalid JSON: {e}")
                
                # Try cleaning
                cleaned = self._clean_json(content)
                info(f"\nCleaned JSON:\n{cleaned}\n")
                
                try:
                    parsed = json.loads(cleaned)
                    warn(f"⚠️ Valid after cleaning!")
                    info(f"Parsed signal: {json.dumps(parsed, indent=2)}")
                    return True
                except json.JSONDecodeError as e2:
                    error(f"❌ Still invalid after cleaning: {e2}")
                    return False
                    
        except Exception as e:
            error(f"❌ Request failed: {e}")
            return False
    
    async def test_multiple_signals(self):
        """Test multiple different signal formats."""
        info("\n" + "=" * 70)
        info("TEST 4: Multiple Signal Formats")
        info("=" * 70)
        
        test_signals = [
            {
                "name": "Emoji Format",
                "text": "🟢 LONG\n💲 ETHUSDT\n📈 Entry: 3000\n🎯 TP: 3200\n🛑 SL: 2900"
            },
            {
                "name": "Turkish Format",
                "text": "AL BTCUSDT\nGİRİŞ: 50000\nHEDEF: 52000\nZARAR: 48000"
            },
            {
                "name": "Short Format",
                "text": "SHORT SOLUSDT 100-105 TP 95 SL 110"
            },
            {
                "name": "Complex Format",
                "text": "#W SHORT SETUP\nSymbol: WUSDT\nEntry: 0.029-0.030\nTarget 1: 0.02945\nTarget 2: 0.029\nStop Loss: 0.0315"
            }
        ]
        
        results = []
        
        for test_case in test_signals:
            info(f"\nTesting: {test_case['name']}")
            info(f"Signal: {test_case['text'][:50]}...")
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Return only JSON: {\"symbol\": \"BTCUSDT\", \"side\": \"LONG\", \"entry\": [50000], \"tp\": [52000], \"sl\": 48000, \"confidence\": 0.9} or {\"signal\": false}"},
                        {"role": "user", "content": f"Parse:\n{test_case['text']}"}
                    ],
                    temperature=0.1,
                    max_tokens=300,
                    extra_body={"num_ctx": self.context_size, "num_predict": 300}
                )
                
                content = response.choices[0].message.content.strip()
                cleaned = self._clean_json(content)
                
                try:
                    parsed = json.loads(cleaned)
                    if parsed.get("signal") is False:
                        warn(f"  ⚠️ No signal detected")
                        results.append(False)
                    else:
                        success(f"  ✅ Parsed: {parsed.get('symbol')} {parsed.get('side')}")
                        results.append(True)
                except:
                    error(f"  ❌ Invalid JSON")
                    results.append(False)
                    
            except Exception as e:
                error(f"  ❌ Error: {e}")
                results.append(False)
        
        # Summary
        success_rate = (sum(results) / len(results)) * 100
        info(f"\n{'='*70}")
        info(f"Success Rate: {success_rate:.0f}% ({sum(results)}/{len(results)})")
        info(f"{'='*70}")
        
        return success_rate > 50
    
    def _clean_json(self, content: str) -> str:
        """Clean JSON response."""
        import re
        
        # Remove markdown
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Remove thinking blocks
        if "<think>" in content:
            content = content.split("</think>")[-1].strip()
        
        # Find JSON bounds
        if not content.startswith("{"):
            start = content.find("{")
            if start != -1:
                content = content[start:]
        
        if not content.endswith("}"):
            end = content.rfind("}")
            if end != -1:
                content = content[:end+1]
        
        # Fix common issues
        if "'" in content and '"' not in content:
            content = content.replace("'", '"')
        
        content = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        return content
    
    async def run_all_tests(self):
        """Run all diagnostic tests."""
        info("\n" + "🔬" * 35)
        info("OLLAMA DIAGNOSTIC SUITE")
        info("🔬" * 35)
        info(f"\nConfiguration:")
        info(f"  URL: {self.url}")
        info(f"  Model: {self.model}")
        info(f"  Context Size: {self.context_size}")
        info("")
        
        results = {}
        
        # Test 1: Connection
        results['connection'] = await self.test_connection()
        if not results['connection']:
            error("\n❌ Connection test failed. Cannot continue.")
            error("   Start Ollama: ollama serve")
            error(f"   Pull model: ollama pull {self.model}")
            return
        
        # Test 2: Simple JSON
        results['simple_json'] = await self.test_simple_json()
        
        # Test 3: Signal parsing
        results['signal_parsing'] = await self.test_signal_parsing()
        
        # Test 4: Multiple formats
        results['multiple_signals'] = await self.test_multiple_signals()
        
        # Final summary
        info("\n" + "=" * 70)
        info("DIAGNOSTIC SUMMARY")
        info("=" * 70)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            info(f"{test_name:20} {status}")
        
        total = len(results)
        passed = sum(results.values())
        
        info("=" * 70)
        info(f"Overall: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        info("=" * 70)
        
        # Recommendations
        if not all(results.values()):
            info("\n📋 Recommendations:")
            
            if not results.get('simple_json'):
                warn("  • Model struggles with JSON output")
                warn("    Try: ollama pull qwen2.5-coder:7b")
                warn("    Or: ollama pull llama3.3:8b")
            
            if not results.get('signal_parsing'):
                warn("  • Signal parsing needs improvement")
                warn("    Consider using Groq as primary (faster & more reliable)")
                warn("    Edit .env: GROQ_API_KEY=your_key")
            
            if results.get('connection') and not results.get('simple_json'):
                warn("  • Model may need different parameters")
                warn("    Try increasing temperature or max_tokens")
        else:
            success("\n🎉 All tests passed! Ollama is working correctly.")


async def main():
    diagnostic = OllamaDiagnostic()
    await diagnostic.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
