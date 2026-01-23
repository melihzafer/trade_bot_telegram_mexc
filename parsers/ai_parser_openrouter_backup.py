"""
AI-Powered Signal Parser using DeepSeek R1 via OpenRouter API.
Part of Project Chimera - Neuro-Symbolic Architecture.

This module uses LLM-based parsing as a fallback for complex or ambiguous signals
that the rule-based parser cannot handle with high confidence.

Author: Project Chimera Team
Created: 2025
"""

import os
import json
import re
import asyncio
from typing import Dict, Optional
from openai import AsyncOpenAI

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AIParser:
    """AI-powered parser using DeepSeek R1 through OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: int = 120):
        """
        Initialize the AI parser.

        Args:
            api_key: OpenRouter API key. If None, loads from OPENROUTER_API_KEY env var.
            model: Model to use. Defaults to deepseek/deepseek-r1.
            timeout: API request timeout in seconds (default: 120)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            raise ValueError("OPENROUTER_API_KEY must be set")

        # Default to DeepSeek R1, fallback to GPT-4o if specified
        self.model = model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1")
        self.timeout = timeout

        # Initialize AsyncOpenAI client with OpenRouter base URL and timeout
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=self.timeout
        )

        # System prompt for strict JSON parsing
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

        logger.info(f"AIParser initialized with model: {self.model} (timeout: {self.timeout}s)")

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

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"AI Parser processing (attempt {attempt}/{max_retries}): {text[:100]}...")

                # Call OpenRouter API with streaming disabled for clean JSON response
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1,  # Low temperature for consistent parsing
                    max_tokens=8000,  # Increased for DeepSeek R1 reasoning tokens
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )

                # Extract the response content
                raw_response = response.choices[0].message.content
                
                # Check if response is empty or None
                if not raw_response or not raw_response.strip():
                    logger.warn(f"AI Parser: Empty response (attempt {attempt}/{max_retries})")
                    logger.warn(f"Response ID: {response.id if hasattr(response, 'id') else 'N/A'}")
                    logger.warn(f"Model: {response.model if hasattr(response, 'model') else 'N/A'}")
                    logger.warn(f"Finish Reason: {response.choices[0].finish_reason if response.choices else 'N/A'}")
                    
                    # Log the full response object for debugging
                    try:
                        logger.warn(f"Full response object: {response.model_dump_json(indent=2) if hasattr(response, 'model_dump_json') else str(response)}")
                    except Exception as e:
                        logger.warn(f"Could not serialize response: {e}")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": "Empty response from AI after all retries"}
                
                raw_response = raw_response.strip()
                logger.debug(f"Raw AI response: {raw_response}")

                # Sanitize response: Remove markdown code blocks if AI added them despite instructions
                sanitized = self._sanitize_json_response(raw_response)

                # Parse JSON
                try:
                    parsed_data = json.loads(sanitized)
                except json.JSONDecodeError as e:
                    logger.error(f"AI Parser: JSON decode error (attempt {attempt}/{max_retries})")
                    logger.error(f"Error: {e}")
                    logger.error(f"Raw response (first 500 chars): {raw_response[:500]}")
                    logger.error(f"Sanitized response: {sanitized[:500]}")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": f"JSON decode error: {str(e)}"}

                # Validate the response structure
                if not isinstance(parsed_data, dict):
                    logger.error(f"AI returned non-dict response: {type(parsed_data)}")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": "Invalid response format"}

                # Check if signal was detected
                if parsed_data.get("signal") is False:
                    logger.info("AI Parser: No signal detected")
                    return {"signal": False}

                # Validate required fields for a valid signal
                required_fields = ["symbol", "side", "entry", "tp", "sl"]
                missing_fields = [f for f in required_fields if f not in parsed_data]

                if missing_fields:
                    logger.warn(f"AI Parser: Missing required fields: {missing_fields}")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying with more explicit prompt...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        return {"signal": False, "error": f"Missing fields: {missing_fields}"}

                # Additional validation
                parsed_data = self._validate_and_normalize(parsed_data)

                logger.success(f"AI Parser: Successfully parsed {parsed_data['symbol']} {parsed_data['side']}")
                return parsed_data

            except Exception as e:
                logger.error(f"AI Parser: Unexpected error (attempt {attempt}/{max_retries}) - {type(e).__name__}: {e}")
                
                if attempt < max_retries:
                    logger.info(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                    continue
                else:
                    return {"signal": False, "error": f"Parser error: {str(e)}"}
        
        # Should never reach here, but just in case
        return {"signal": False, "error": "Max retries exceeded"}

    def _sanitize_json_response(self, response: str) -> str:
        """
        Remove markdown formatting, thinking tokens, and extract pure JSON.
        
        DeepSeek R1 may output reasoning in <think>...</think> tags before JSON.
        We need to strip everything except the JSON object.

        Args:
            response: Raw API response

        Returns:
            Sanitized JSON string
        """
        # Remove DeepSeek R1 thinking tokens (appears between <think> and </think>)
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)

        # Remove any leading/trailing whitespace
        response = response.strip()

        # If response starts with something other than {, try to find JSON object
        if not response.startswith('{'):
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                response = match.group(0)

        return response

    def _validate_and_normalize(self, data: Dict) -> Dict:
        """
        Validate and normalize parsed signal data.

        Args:
            data: Parsed signal dictionary

        Returns:
            Validated and normalized dictionary
        """
        # Ensure symbol is uppercase
        if "symbol" in data:
            data["symbol"] = str(data["symbol"]).upper()

        # Ensure side is uppercase
        if "side" in data:
            data["side"] = str(data["side"]).upper()

        # Ensure entry is a list of floats
        if "entry" in data:
            if not isinstance(data["entry"], list):
                data["entry"] = [float(data["entry"])]
            else:
                data["entry"] = [float(x) for x in data["entry"]]

        # Ensure tp is a list of floats
        if "tp" in data:
            if not isinstance(data["tp"], list):
                data["tp"] = [float(data["tp"])]
            else:
                data["tp"] = [float(x) for x in data["tp"]]

        # Ensure sl is a float
        if "sl" in data:
            data["sl"] = float(data["sl"])

        # Ensure leverage is an int (or set default)
        if "leverage" in data:
            data["leverage"] = int(data["leverage"])
        else:
            data["leverage"] = 10  # Default leverage

        # Ensure confidence is a float between 0 and 1
        if "confidence" in data:
            data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
        else:
            data["confidence"] = 0.8  # Default confidence for AI parsing

        return data


# Convenience function for standalone usage
async def parse_signal_with_ai(text: str, api_key: Optional[str] = None) -> Dict:
    """
    Standalone function to parse a signal using AI.

    Args:
        text: Signal text to parse
        api_key: Optional API key (loads from env if not provided)

    Returns:
        Parsed signal dictionary
    """
    parser = AIParser(api_key=api_key)
    return await parser.parse_signal(text)


# Example usage (for testing)
if __name__ == "__main__":
    import asyncio

    async def test():
        # Test signal
        test_signal = """
        🔥 BTC/USDT LONG
        Entry: 42,000 - 41,500
        Targets: 43,000 / 44,000 / 45,000
        Stop Loss: 40,000
        Leverage: 10x
        """

        parser = AIParser()
        result = await parser.parse_signal(test_signal)
        print(json.dumps(result, indent=2))

    asyncio.run(test())
