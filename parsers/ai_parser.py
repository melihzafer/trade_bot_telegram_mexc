"""
AI-Powered Signal Parser with Ollama Primary + OpenRouter Fallback
Uses local Ollama (qwen3:8b) as primary with configurable context size.

Context Size Optimization:
- 8k tokens: Fastest inference (2-4 seconds)
- 16k tokens: More context, slower (4-8 seconds)

Author: Project Chimera Team
"""

import os
import re
import json
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import from config (after load_dotenv)
try:
    from utils.config import (
        OLLAMA_URL, OLLAMA_MODEL, OLLAMA_CONTEXT_SIZE,
        OPENROUTER_API_KEY, OPENROUTER_MODEL
    )
except ImportError:
    # Fallback if config import fails
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    OLLAMA_CONTEXT_SIZE = int(os.getenv("OLLAMA_CONTEXT_SIZE", "16384"))
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AIParser:
    """AI-powered parser using Local Ollama or OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: int = 120):
        """
        Initialize the AI parser with Local Ollama as primary, OpenRouter as fallback.

        Args:
            api_key: API key (for OpenRouter). If None, tries local Ollama first.
            model: Model to use. If None, auto-detects based on available service.
            timeout: API request timeout in seconds (default: 120)
        """
        self.timeout = timeout
        self.use_local = False
        self.client = None
        self.model = None
        
        # Try Local Ollama first
        local_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
        local_model = os.getenv("LOCAL_MODEL_NAME") or os.getenv("OLLAMA_MODEL", "qwen3:8b")
        
        try:
            # Test if Ollama is available
            self.client = AsyncOpenAI(
                api_key="ollama",  # Ollama doesn't need real API key
                base_url=local_url,
                timeout=30  # Quick timeout for initial check
            )
            self.model = local_model
            self.use_local = True
            logger.info(f"AI Parser using Local Ollama: {self.model} @ {local_url}")
        
        except Exception as e:
            logger.warn(f"Local Ollama not available: {e}")
            
            # Fallback to OpenRouter
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                logger.error("No AI provider available! Set OLLAMA or OPENROUTER_API_KEY")
                raise ValueError("No AI provider configured")
            
            self.model = model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=timeout
            )
            self.use_local = False
            logger.info(f"AI Parser using OpenRouter: {self.model}")

        # System prompt for strict JSON parsing
        # Simpler for local models to follow
        if self.use_local:
            self.system_prompt = """You are a trading signal parser. Extract data and return ONLY valid JSON.

Output format (no explanations, no thinking, just JSON):
{"symbol": "BTCUSDT", "side": "LONG", "entry": [50000], "tp": [52000], "sl": 48000, "leverage": 1, "confidence": 0.9}

If no valid signal: {"signal": false}

Rules:
- Symbol: uppercase, add USDT if missing
- Side: LONG or SHORT only
- Numbers: convert commas to dots
- Output ONLY the JSON object"""
        else:
            # More detailed prompt for cloud models
            self.system_prompt = """You are a financial data parser specialized in cryptocurrency trading signals.

Your ONLY task is to extract structured data from trading signals and return PURE JSON without any markdown formatting.

CRITICAL RULES:
1. Output ONLY valid JSON - NO markdown code blocks, NO ```json tags, NO explanations
2. Return ONLY the JSON object starting with { and ending with }
3. If you detect a valid trading signal, extract these fields:
   - "symbol": Trading pair (e.g., "BTCUSDT", "ETHUSDT")
   - "side": "LONG" or "SHORT"
   - "entry": Array of entry prices as floats (e.g., [42000.5, 41500.0])
   - "tp": Array of take-profit targets as floats (e.g., [43000.0, 44000.0, 45000.0])
   - "sl": Stop-loss as float (e.g., 40000.0)
   - "leverage": Integer leverage (e.g., 10, 20, 50)
   - "confidence": Your confidence score from 0.0 to 1.0
4. If NO valid signal is detected, return: {"signal": false}

NORMALIZATION RULES:
- Symbol: Always uppercase, append USDT if not present (e.g., "BTC" -> "BTCUSDT")
- Side: Convert variations like "Long", "LONG", "Buy", "BUY" to "LONG"
- Side: Convert "Short", "SHORT", "Sell", "SELL" to "SHORT"
- Numbers: Handle both "." and "," as decimal separators
- Remove any currency symbols ($, €, etc.)

EXAMPLE OUTPUTS (your actual output should have NO markdown):
{"symbol": "BTCUSDT", "side": "LONG", "entry": [42000.0, 41500.0], "tp": [43000.0, 44000.0, 45000.0], "sl": 40000.0, "leverage": 10, "confidence": 0.95}

{"signal": false}"""

        logger.info(f"AI Parser initialized (timeout: {self.timeout}s)")

    def _strip_thinking_blocks(self, text: str) -> str:
        """
        Strip DeepSeek-R1 thinking blocks and markdown code blocks.
        
        DeepSeek-R1 outputs reasoning in <think>...</think> tags.
        We only want the final JSON output.
        
        Args:
            text: Raw model output
            
        Returns:
            Cleaned text with only JSON
        """
        # Remove thinking blocks
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove markdown code blocks
        text = text.replace("```json", "").replace("```", "")
        
        # Remove common prefixes
        text = re.sub(r'^(Here\'s?|Here is|Output:|Result:).*?(\{)', r'\1', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Trim whitespace
        text = text.strip()
        
        # Extract JSON object (first { to last })
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            text = text[start:end+1]
        
        return text

    async def parse_signal(self, text: str, max_retries: int = 3) -> Dict:
        """
        Parse a trading signal using AI with retry mechanism.

        Args:
            text: Raw signal text (may be in Turkish, English, or mixed)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Dictionary with parsed signal data or {"signal": false} if no signal found.
            On error, returns {"signal": false, "error": "description"}
        """
        if not text or not text.strip():
            return {"signal": False, "error": "Empty input"}

        for attempt in range(max_retries):
            try:
                # Adjust max_tokens based on provider (local models need more for thinking)
                max_tokens = 1000 if self.use_local else 500
                
                # Prepare API call parameters
                api_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"Parse this trading signal:\n\n{text}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": max_tokens
                }
                
                # Add Ollama-specific optimizations (faster inference)
                if self.use_local:
                    api_params["extra_body"] = {
                        "num_ctx": OLLAMA_CONTEXT_SIZE,  # Configurable context window
                        "num_predict": max_tokens  # Max output tokens
                    }
                    logger.debug(f"Ollama context size: {OLLAMA_CONTEXT_SIZE} tokens")
                
                # Make API call
                response = await self.client.chat.completions.create(**api_params)
                
                # Extract response
                content = response.choices[0].message.content
                
                # Check if content is empty
                if not content or not content.strip():
                    logger.warn(f"Empty response from AI (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": "Empty response from AI"}
                
                content = content.strip()
                
                # Log raw response for debugging (first 300 chars)
                if self.use_local:
                    logger.info(f"Ollama response (first 300 chars): {content[:300]}")
                
                # Strip thinking blocks and markdown (important for DeepSeek-R1)
                content = self._strip_thinking_blocks(content)
                
                # Check again after stripping
                if not content or not content.strip():
                    logger.warn(f"Empty after stripping (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": "Empty after stripping thinking blocks"}
                
                # Parse JSON
                try:
                    result = json.loads(content)
                    
                    # Success!
                    if self.use_local:
                        logger.info(f"Parsed by Local Ollama ({self.model})")
                    else:
                        logger.info(f"Parsed by OpenRouter ({self.model})")
                    
                    return result
                
                except json.JSONDecodeError as e:
                    logger.warn(f"Invalid JSON (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.warn(f"Content after stripping (first 500 chars): {content[:500]}")
                    
                    # Try to extract JSON if there's extra text
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(0))
                            logger.info("Extracted JSON from mixed content")
                            return result
                        except:
                            pass
                    
                    # Retry on JSON errors
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        return {"signal": False, "error": f"Invalid JSON after {max_retries} attempts"}
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for connection errors (Ollama not running)
                if 'connection' in error_msg or 'refused' in error_msg:
                    if self.use_local:
                        logger.error("Local Ollama not found. Is it running? (ollama serve)")
                        return {"signal": False, "error": "Local Ollama not running"}
                    else:
                        logger.error(f"Connection error: {e}")
                        return {"signal": False, "error": "Connection failed"}
                
                # Check for rate limit
                elif 'rate limit' in error_msg or '429' in error_msg:
                    logger.warn("Rate limit hit - consider using local Ollama")
                    return {"signal": False, "error": "Rate limited"}
                
                # Check for timeout
                elif 'timeout' in error_msg:
                    logger.warn(f"Timeout (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": "Timeout"}
                
                # Other errors
                else:
                    logger.warn(f"AI Parser error: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        return {"signal": False, "error": str(e)}
        
        # All retries failed
        return {"signal": False, "error": "All retries failed"}


# Convenience function for backward compatibility
async def parse_with_ai(text: str) -> Dict:
    """Parse a signal using the AI parser."""
    parser = AIParser()
    return await parser.parse_signal(text)


if __name__ == "__main__":
    # Test the AI parser
    async def test():
        print("Testing AI Parser with Local Ollama...")
        print("=" * 60)
        
        try:
            parser = AIParser()
            
            test_signals = [
                """
                LONG
                BTCUSDT
                Entry: 50000
                Target: 52000
                Stop Loss: 48000
                """,
                """
                BTC LONG
                giris: 50,000
                tp: 52,000
                sl: 48,000
                """,
                """
                Not a trading signal, just random text about crypto markets.
                """
            ]
            
            for i, signal in enumerate(test_signals, 1):
                print(f"\nTest {i}:")
                print(f"Input: {signal.strip()[:60]}...")
                
                result = await parser.parse_signal(signal)
                
                if result.get("signal") != False:
                    print(f"SUCCESS: {result.get('symbol')} {result.get('side')}")
                    print(f"  Entry: {result.get('entry')}, TP: {result.get('tp')}, SL: {result.get('sl')}")
                else:
                    print(f"No signal detected")
                    if result.get("error"):
                        print(f"  Error: {result['error']}")
        
        except Exception as e:
            print(f"\nError: {e}")
            print("\nTroubleshooting:")
            print("  1. Is Ollama running? (ollama serve)")
            print("  2. Is the model downloaded? (ollama pull qwen3:8b)")
            print("  3. Check OLLAMA_URL in .env (default: http://localhost:11434/v1)")
    
    asyncio.run(test())
