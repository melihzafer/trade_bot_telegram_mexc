# Quick Reference: Adding More AI Providers

## Add Groq (Recommended - Very Fast!)

1. Get API key: https://console.groq.com/keys
2. Add to .env:
   \\\
   GROQ_API_KEY=gsk_your_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   \\\
3. Done! System will automatically use it

## Add Ollama (100% Local, No API Keys)

1. Install Ollama:
   - Windows: https://ollama.com/download/windows
   - Mac: \rew install ollama\
   - Linux: \curl -fsSL https://ollama.com/install.sh | sh\

2. Start Ollama server:
   \\\ash
   ollama serve
   \\\

3. Pull a model:
   \\\ash
   ollama pull llama3.2
   \\\

4. Add to .env:
   \\\
   OLLAMA_URL=http://localhost:11434/v1
   OLLAMA_MODEL=llama3.2
   \\\

5. Done! System will automatically use it

## Priority Order (Recommended)

Edit parsers/multi_ai_parser.py, change order in \_load_providers():
\\\python
# For speed priority:
1. Local API (gemini-3-flash)
2. Groq (llama-3.3-70b)
3. Ollama (llama3.2)
4. OpenRouter (deepseek-r1)

# For quality priority:
1. Groq (llama-3.3-70b)
2. OpenRouter (deepseek-r1)
3. Local API (gemini-3-flash)
4. Ollama (llama3.2)
\\\

Current order is optimized for: OpenRouter → Local → Ollama → Groq
