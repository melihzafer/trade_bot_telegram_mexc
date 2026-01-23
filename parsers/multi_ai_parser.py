"""
Multi-Provider AI Signal Parser
Supports multiple AI providers with automatic failover and load balancing.

Priority Order (configurable via .env):
1. Groq (PRIMARY) - Ultra-fast, 30 req/min limit
2. Ollama (FALLBACK 1) - Local, unlimited, fast with 8k context
3. OpenRouter (FALLBACK 2) - Cloud, 200/day limit
4. Local API (FALLBACK 3) - Custom server

Features:
- Automatic failover on rate limits or errors
- Provider health tracking (success/failure counts)
- Round-robin load balancing
- Configurable Ollama context size for speed optimization

Author: Project Chimera
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import from config (after load_dotenv)
try:
    from utils.config import (
        GROQ_API_KEY, GROQ_MODEL,
        OLLAMA_URL, OLLAMA_MODEL, OLLAMA_CONTEXT_SIZE,
        OPENROUTER_API_KEY, OPENROUTER_MODEL,
        LOCAL_AI_URL, LOCAL_AI_KEY, LOCAL_AI_MODEL
    )
except ImportError:
    # Fallback if config import fails
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    OLLAMA_CONTEXT_SIZE = int(os.getenv("OLLAMA_CONTEXT_SIZE", "8192"))
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
    LOCAL_AI_URL = os.getenv("LOCAL_AI_URL", "")
    LOCAL_AI_KEY = os.getenv("LOCAL_AI_KEY", "")
    LOCAL_AI_MODEL = os.getenv("LOCAL_AI_MODEL", "gemini-3-flash")

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AIProvider:
    """Single AI provider configuration."""
    
    def __init__(self, name: str, base_url: str, api_key: str, model: str, timeout: int = 120):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.enabled = True
        self.failure_count = 0
        self.success_count = 0
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
    
    def disable(self):
        """Disable this provider due to repeated failures."""
        self.enabled = False
        logger.warn(f"Provider '{self.name}' disabled due to failures")
    
    def record_success(self):
        """Record successful API call."""
        self.success_count += 1
        self.failure_count = 0  # Reset failure count on success
    
    def record_failure(self):
        """Record failed API call."""
        self.failure_count += 1
        if self.failure_count >= 3:
            self.disable()


class MultiAIParser:
    """
    AI-powered parser with multiple provider support and automatic failover.
    
    Providers are tried in order until one succeeds. Rate-limited providers
    are automatically disabled for the session.
    
    Can be configured for Ollama-only mode (for backtest/historical parsing).
    """
    
    def __init__(self, ollama_only: bool = False):
        """
        Initialize AI parser with configured providers.
        
        Args:
            ollama_only: If True, only use Ollama (saves Groq rate limit for live trading)
        """
        self.providers: List[AIProvider] = []
        self.current_index = 0
        self.ollama_only = ollama_only
        
        # System prompt for strict JSON parsing
        self.system_prompt = """You are a JSON parser for cryptocurrency trading signals. Return ONLY valid JSON.

OUTPUT FORMAT - You must return EXACTLY this structure:
{"symbol": "BTCUSDT", "side": "LONG", "entry": [42000.0], "tp": [43000.0, 44000.0], "sl": 40000.0, "leverage": 10, "confidence": 0.9}

OR if no signal detected:
{"signal": false}

CRITICAL RULES:
1. Return ONLY the JSON object - NO explanations, NO markdown, NO extra text
2. Use double quotes for all strings and property names
3. Property names: symbol, side, entry, tp, sl, leverage, confidence
4. side must be "LONG" or "SHORT" (uppercase)
5. entry and tp are arrays of numbers: [42000.0, 43000.0]
6. sl, leverage are numbers: 40000.0, 10
7. confidence is 0.0 to 1.0: 0.9
8. If you see "BTC" or "ETH" without USDT, append USDT: "BTCUSDT"

DO NOT return explanations, thoughts, or markdown. Just the JSON object."""
        
        self._load_providers()
        
        if self.ollama_only:
            logger.info("🏠 Ollama-only mode (for backtest)")
        else:
            logger.info(f"🔄 Multi-provider mode: {len(self.providers)} providers")
    
    def _load_providers(self):
        """Load all configured providers from environment variables."""
        
        # If Ollama-only mode, skip other providers
        if self.ollama_only:
            ollama_url = OLLAMA_URL or os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
            ollama_model = OLLAMA_MODEL or os.getenv("OLLAMA_MODEL", "qwen3:8b")
            
            if ollama_url:
                try:
                    provider = AIProvider(
                        name="Ollama",
                        base_url=ollama_url,
                        api_key="ollama",
                        model=ollama_model,
                        timeout=90
                    )
                    self.providers.append(provider)
                    logger.success(f"Ollama loaded (BACKTEST MODE) - {provider.model}")
                    return  # Skip loading other providers
                except Exception as e:
                    logger.error(f"Failed to load Ollama: {e}")
                    raise ValueError("Ollama-only mode requested but Ollama unavailable")
            else:
                raise ValueError("Ollama-only mode requested but OLLAMA_URL not configured")
        
        # Normal mode: Load all providers with priority order
        # Provider 1: Groq (FASTEST - Primary)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                provider = AIProvider(
                    name="Groq",
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_key,
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    timeout=30  # Groq is very fast
                )
                self.providers.append(provider)
                logger.info(f"Groq provider loaded ({provider.model}) - PRIMARY")
            except Exception as e:
                logger.warn(f"Failed to load Groq: {e}")
        
        # Provider 2: Ollama (Local - Fast fallback)
        ollama_url = os.getenv("OLLAMA_URL")
        if ollama_url:
            try:
                provider = AIProvider(
                    name="Ollama",
                    base_url=ollama_url,
                    api_key="ollama",  # Ollama doesn't require key
                    model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
                    timeout=60
                )
                self.providers.append(provider)
                logger.info(f"Ollama provider loaded ({provider.model}) - FALLBACK 1")
            except Exception as e:
                logger.warn(f"Failed to load Ollama: {e}")
        
        # Provider 3: OpenRouter (Cloud - Last resort)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                provider = AIProvider(
                    name="OpenRouter",
                    base_url="https://openrouter.ai/api/v1",
                    api_key=openrouter_key,
                    model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free"),
                    timeout=120
                )
                self.providers.append(provider)
                logger.info(f"OpenRouter provider loaded ({provider.model}) - FALLBACK 2")
            except Exception as e:
                logger.warn(f"Failed to load OpenRouter: {e}")
        
        # Provider 4: Local API (Gemini-3-flash)
        local_url = os.getenv("LOCAL_AI_URL")
        local_key = os.getenv("LOCAL_AI_KEY")
        if local_url and local_key:
            try:
                provider = AIProvider(
                    name="Local",
                    base_url=local_url,
                    api_key=local_key,
                    model=os.getenv("LOCAL_AI_MODEL", "gemini-3-flash"),
                    timeout=60
                )
                self.providers.append(provider)
                logger.info(f"Local provider loaded ({provider.model}) - FALLBACK 3")
            except Exception as e:
                logger.warn(f"Failed to load Local API: {e}")
        
        if not self.providers:
            logger.error("No AI providers configured! Set at least one provider in .env")
            raise ValueError("No AI providers available")
        
        logger.info(f"Total providers loaded: {len(self.providers)}")
    
    def _get_next_provider(self) -> Optional[AIProvider]:
        """Get next available provider using round-robin."""
        attempts = 0
        while attempts < len(self.providers):
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            
            if provider.enabled:
                return provider
            
            attempts += 1
        
        return None
    
    async def parse_signal(self, text: str, max_retries: int = 2) -> Dict:
        """
        Parse a trading signal using AI with automatic provider failover.
        
        Args:
            text: Raw signal text
            max_retries: Maximum number of provider attempts
            
        Returns:
            Dictionary with parsed signal data or {"signal": false}
        """
        if not text or not text.strip():
            return {"signal": False, "error": "Empty input"}
        
        # Try up to max_retries providers
        for attempt in range(max_retries):
            provider = self._get_next_provider()
            
            if not provider:
                logger.warn("No available AI providers")
                return {"signal": False, "error": "No providers available"}
            
            try:
                # Prepare API call parameters
                api_params = {
                    "model": provider.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"Parse this trading signal:\n\n{text}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 500
                }
                
                # Add Ollama-specific optimizations (faster inference)
                if provider.name == "Ollama":
                    api_params["extra_body"] = {
                        "num_ctx": OLLAMA_CONTEXT_SIZE,  # Configurable context window
                        "num_predict": 500  # Max output tokens
                    }
                    logger.debug(f"Ollama context size: {OLLAMA_CONTEXT_SIZE} tokens")
                
                # Make API call
                response = await provider.client.chat.completions.create(**api_params)
                
                # Extract response
                content = response.choices[0].message.content.strip()
                
                # Enhanced JSON extraction and cleaning
                content = self._extract_and_clean_json(content)
                
                if not content:
                    logger.warn(f"{provider.name} returned empty/invalid JSON")
                    provider.record_failure()
                    continue
                
                # Parse JSON
                result = json.loads(content)
                
                # Success!
                provider.record_success()
                logger.info(f"✓ Parsed by {provider.name}")
                return result
            
            except json.JSONDecodeError as e:
                logger.warn(f"{provider.name} returned invalid JSON: {e}")
                provider.record_failure()
                continue
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit
                if 'rate limit' in error_msg or '429' in error_msg:
                    logger.warn(f"{provider.name} rate limited - trying next provider")
                    provider.disable()
                    continue
                
                # Check for timeout
                elif 'timeout' in error_msg:
                    logger.warn(f"{provider.name} timed out - trying next provider")
                    provider.record_failure()
                    continue
                
                # Other errors
                else:
                    logger.warn(f"{provider.name} error: {e}")
                    provider.record_failure()
                    continue
        
        # All providers failed
        logger.error("❌ All AI providers failed")
        return {"signal": False, "error": "All providers failed"}
    
    def _extract_and_clean_json(self, content: str) -> str:
        """
        Extract and clean JSON from AI response.
        Handles markdown blocks, extra text, and malformed JSON.
        
        Args:
            content: Raw AI response
            
        Returns:
            Cleaned JSON string or empty string if invalid
        """
        import re
        
        if not content:
            return ""
        
        # Remove markdown code blocks
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Remove thinking blocks (DeepSeek-R1)
        if "<think>" in content:
            content = content.split("</think>")[-1].strip()
        
        # Try to find JSON object bounds
        if not content.startswith("{"):
            start_idx = content.find("{")
            if start_idx == -1:
                return ""
            content = content[start_idx:]
        
        if not content.endswith("}"):
            end_idx = content.rfind("}")
            if end_idx == -1:
                return ""
            content = content[:end_idx+1]
        
        # Fix common JSON issues
        # 1. Single quotes instead of double quotes (only if no double quotes exist)
        if "'" in content and '"' not in content:
            content = content.replace("'", '"')
        
        # 2. Unquoted property names (JavaScript style): symbol: → "symbol":
        # Match: word followed by colon (property name without quotes)
        content = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', content)
        
        # 3. Trailing commas before closing braces/brackets
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        return content.strip()
    
    def get_stats(self) -> Dict:
        """Get statistics for all providers."""
        return {
            provider.name: {
                "enabled": provider.enabled,
                "success_count": provider.success_count,
                "failure_count": provider.failure_count,
                "model": provider.model
            }
            for provider in self.providers
        }


# Convenience function for backward compatibility
async def parse_with_ai(text: str) -> Dict:
    """Parse a signal using the multi-provider AI parser."""
    parser = MultiAIParser()
    return await parser.parse_signal(text)


if __name__ == "__main__":
    # Test the multi-provider parser
    async def test():
        parser = MultiAIParser()
        
        test_signal = """
        🟢 LONG
        💲 BTCUSDT
        📈 Entry: 50000
        🎯 Target: 52000
        🛑 Stop Loss: 48000
        """
        
        result = await parser.parse_signal(test_signal)
        print(json.dumps(result, indent=2))
        
        print("\nProvider stats:")
        print(json.dumps(parser.get_stats(), indent=2))
    
    asyncio.run(test())
