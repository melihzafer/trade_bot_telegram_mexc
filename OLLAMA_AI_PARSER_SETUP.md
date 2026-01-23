================================================================
✅ AI PARSER UPDATED TO USE LOCAL OLLAMA
================================================================

## What Changed

### OLD (ai_parser.py)
- Used OpenRouter API (cloud, rate limited)
- Model: deepseek/deepseek-r1 via OpenRouter
- Required API key
- Rate limits and costs

### NEW (ai_parser.py)
- Uses Local Ollama (your D: drive instance)
- Model: deepseek-r1:8b (local)
- No API key needed
- Unlimited, free usage
- Fallback to OpenRouter if Ollama unavailable

## Key Features

1. **Automatic Detection**
   - Tries Ollama first (http://localhost:11434/v1)
   - Falls back to OpenRouter if Ollama not running
   - Clear error messages

2. **DeepSeek-R1 Thinking Block Handling**
   - Strips <think>...</think> tags automatically
   - Only processes final JSON output
   - Robust regex extraction

3. **Error Messages**
   - "Local Ollama not found. Is it running?"
   - Clear troubleshooting steps in logs

4. **Model Configuration**
   - Environment variable: LOCAL_MODEL_NAME
   - Default: deepseek-r1:8b
   - Alternative: qwen2.5-coder:7b

## Configuration (.env)

\\\nv
# -------------------- AI Parser (Local Ollama) --------------------
OLLAMA_URL=http://localhost:11434/v1
LOCAL_MODEL_NAME=deepseek-r1:8b
OLLAMA_MODEL=deepseek-r1:8b

# -------------------- AI Parser (Fallback - OpenRouter) --------------------
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=deepseek/deepseek-r1-0528:free
\\\

## Setup Instructions

### 1. Ensure Ollama is Running
\\\powershell
# Check if Ollama is running
Get-Process ollama -ErrorAction SilentlyContinue

# If not running, start it
ollama serve
\\\

### 2. Pull the Model (if not already)
\\\powershell
# Pull deepseek-r1:8b (4.7GB)
ollama pull deepseek-r1:8b

# Or alternative (lighter model)
ollama pull qwen2.5-coder:7b
\\\

### 3. Test the Parser
\\\powershell
python parsers\ai_parser.py
\\\

## Usage

### In collect_signals.py
\\\ash
# Will automatically use your local Ollama instance
python collect_signals.py --mode historical --limit 500 --parse
\\\

### Programmatic Usage
\\\python
from parsers.ai_parser import AIParser
import asyncio

async def parse_signal():
    parser = AIParser()  # Auto-detects Ollama
    
    result = await parser.parse_signal(\"\"\"
        LONG BTCUSDT
        Entry: 50000
        TP: 52000
        SL: 48000
    \"\"\")
    
    print(result)

asyncio.run(parse_signal())
\\\

## Features

✅ **Thinking Block Stripping**
   - Removes <think>...</think> from DeepSeek-R1
   - Removes markdown code blocks
   - Extracts pure JSON

✅ **Retry Logic**
   - 3 automatic retries on failure
   - 1-2 second delays between retries
   - Graceful degradation

✅ **Error Handling**
   - Connection refused → "Is Ollama running?"
   - Timeout → Automatic retry
   - Rate limit → Suggests local Ollama
   - Invalid JSON → Shows raw content for debugging

✅ **Fallback Strategy**
   - Ollama not available → OpenRouter
   - Both fail → Returns {"signal": false, "error": "..."}

## Troubleshooting

### "Local Ollama not found. Is it running?"
\\\powershell
# Start Ollama server
ollama serve

# Check it's running
curl http://localhost:11434/v1/models
\\\

### "Invalid JSON" errors
- Model might not be following instructions well
- Try a different model: LOCAL_MODEL_NAME=qwen2.5-coder:7b
- Check raw content in logs to see what model returned

### Slow performance
- First request always slower (model loading)
- Subsequent requests faster (model cached)
- Use smaller model: qwen2.5-coder:7b vs deepseek-r1:8b

### Falls back to OpenRouter
- Check OLLAMA_URL is correct (default: http://localhost:11434/v1)
- Verify Ollama is running on correct port
- Check firewall not blocking localhost

## Benefits

✅ **Unlimited Usage** - No rate limits, no costs
✅ **Privacy** - Data never leaves your machine
✅ **Speed** - No network latency after first load
✅ **Offline** - Works without internet
✅ **Control** - Switch models anytime

## Files Modified

1. parsers/ai_parser.py - Complete rewrite for Ollama
2. .env - Added OLLAMA_URL, LOCAL_MODEL_NAME
3. parsers/ai_parser_openrouter_backup.py - Backup of old version

================================================================
🚀 You're now using unlimited local AI parsing!
================================================================
