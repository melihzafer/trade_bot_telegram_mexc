# AI Parser Module - Documentation

## Overview
The `ai_parser.py` module provides AI-powered signal parsing using DeepSeek R1 (or GPT-4o) through the OpenRouter API. This is part of Project Chimera's Neuro-Symbolic architecture.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Add your OpenRouter API key to the `.env` file:
```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=deepseek/deepseek-r1  # Optional, defaults to deepseek-r1
```

Get your API key from: https://openrouter.ai/

## Usage

### Basic Usage
```python
import asyncio
from parsers.ai_parser import AIParser

async def main():
    # Initialize parser
    parser = AIParser()
    
    # Parse a signal
    signal_text = """
    BTC/USDT LONG
    Entry: 42,000 - 41,500
    Targets: 43,000 / 44,000 / 45,000
    Stop Loss: 40,000
    Leverage: 10x
    """
    
    result = await parser.parse_signal(signal_text)
    print(result)

asyncio.run(main())
```

### With Custom Model
```python
parser = AIParser(model="openai/gpt-4o")
result = await parser.parse_signal(signal_text)
```

### Standalone Function
```python
from parsers.ai_parser import parse_signal_with_ai

result = await parse_signal_with_ai(signal_text)
```

## Response Format

### Successful Parse
```json
{
  "symbol": "BTCUSDT",
  "side": "LONG",
  "entry": [42000.0, 41500.0],
  "tp": [43000.0, 44000.0, 45000.0],
  "sl": 40000.0,
  "leverage": 10,
  "confidence": 0.95
}
```

### No Signal Detected
```json
{
  "signal": false
}
```

### Error Response
```json
{
  "signal": false,
  "error": "Error description"
}
```

## Integration with Enhanced Parser

The AI Parser is designed to work as a fallback for the rule-based parser:

```python
from parsers.enhanced_parser import EnhancedParser
from parsers.ai_parser import AIParser

# Initialize both parsers
rule_parser = EnhancedParser()
ai_parser = AIParser()

# Try rule-based first
result = rule_parser.parse(signal_text)

# If confidence is low, use AI parser
if result.confidence < 0.7:
    ai_result = await ai_parser.parse_signal(signal_text)
    if ai_result.get("signal") != False:
        # Use AI result
        result = ai_result
```

## Supported Formats

The AI parser can handle:
- ✅ English signals
- ✅ Turkish signals
- ✅ Mixed language signals
- ✅ Various number formats (comma/period decimals)
- ✅ Different terminology (Long/Buy, Short/Sell)
- ✅ Emojis and special characters
- ✅ Flexible formatting

## Testing

Run the test suite:
```bash
python test_ai_parser.py
```

## Cost Considerations

- DeepSeek R1: ~$0.14 per 1M input tokens, ~$2.19 per 1M output tokens
- Average signal parse: ~200 input tokens, ~100 output tokens
- Estimated cost per parse: < $0.001

## Error Handling

The parser includes comprehensive error handling:
- API connection errors
- JSON parsing errors
- Invalid response formats
- Missing required fields
- Environment variable issues

All errors are logged using the `utils.logger` module.

## Security

- ✅ API keys loaded from environment variables
- ✅ No hardcoded credentials
- ✅ Secure HTTPS connection to OpenRouter
- ✅ Input sanitization

## Performance

- **Latency**: 1-3 seconds per parse (depends on model)
- **Async**: Fully async/await compatible
- **Concurrent**: Can process multiple signals in parallel

## Troubleshooting

### "OPENROUTER_API_KEY not found"
- Ensure `.env` file exists in project root
- Verify the key is set: `OPENROUTER_API_KEY=sk-or-...`

### "JSON decode error"
- Usually caused by model returning unexpected format
- Check logs for raw response
- Consider switching to GPT-4o if DeepSeek has issues

### Low confidence scores
- AI parser typically returns 0.8+ confidence
- Lower scores may indicate ambiguous signals
- Consider improving the system prompt

## Next Steps

1. ✅ Implement `ai_parser.py` (Complete)
2. ⏳ Integrate with `enhanced_parser.py` (Hybrid Router)
3. ⏳ Add unit tests with mocked API calls
4. ⏳ Monitor accuracy and cost in production

## Support

For issues or questions, refer to:
- `IMPLEMENTATION_PLAN_V2.md`
- `AI_AGENT_INSTRUCTIONS.md`
- Project Chimera documentation
