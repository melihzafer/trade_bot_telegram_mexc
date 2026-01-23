# AI Provider Priority Configuration

## Updated Priority Order (Optimized for Speed & Reliability)

### 1. Groq (PRIMARY) ⚡
- **Speed:** VERY FAST (<1 second)
- **Quality:** Excellent
- **Limits:** 30 req/min, 14,400/day (free tier)
- **Status:** Will use until rate limit hit

### 2. Ollama (FALLBACK 1) 🏠
- **Speed:** Fast (3-8 seconds)
- **Quality:** Good
- **Limits:** UNLIMITED (local)
- **Status:** Activates when Groq rate limited

### 3. OpenRouter (FALLBACK 2) ☁️
- **Speed:** Slow (5-10 seconds)
- **Quality:** Excellent
- **Limits:** 200 req/day (free tier)
- **Status:** Last resort cloud option

### 4. Local API (FALLBACK 3) 🖥️
- **Speed:** Fast (1-3 seconds)
- **Quality:** Good
- **Limits:** UNLIMITED (your server)
- **Status:** Final fallback

## Expected Behavior

### Normal Operation
```
Signal arrives
  ↓
Try Groq (PRIMARY) ← FAST! 100+ tokens/sec
  ✓ Success in <1 second
  ↓
Return parsed signal
```

### After Groq Rate Limit (30 requests)
```
Signal arrives
  ↓
Try Groq → Rate limited! (429)
  ↓
Auto-disable Groq for session
  ↓
Try Ollama (qwen3:8b) ← UNLIMITED!
  ✓ Success in 3-8 seconds
  ↓
Return parsed signal
```

### Statistics Example
After 500 signals collected:
```
Parsing Statistics:
  Total messages checked: 690
  Parsed by regex: 545 (fast!)
  Parsed by AI: 145
  
AI Provider Statistics:
  Groq (llama-3.3-70b): DISABLED - 30 success, 0 failures (rate limited)
  Ollama (qwen3:8b): ACTIVE - 115 success, 0 failures
  OpenRouter: ACTIVE - 0 success, 0 failures (not needed)
  Local: ACTIVE - 0 success, 0 failures (not needed)
  
  Success rate: 100%
```

## Setup Instructions

### 1. Get Groq API Key (Required)
```
1. Go to: https://console.groq.com/keys
2. Sign up (free)
3. Create new API key
4. Copy key (starts with 'gsk_')
```

### 2. Update .env
```env
# Add your Groq API key
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Ensure Ollama is configured
OLLAMA_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3:8b
```

### 3. Ensure Ollama Model Downloaded
```powershell
# Check if model exists
ollama list

# Pull if needed
ollama pull qwen3:8b

# Start Ollama
ollama serve
```

### 4. Test Setup
```powershell
# Test all providers
python parsers\multi_ai_parser.py
```

### 5. Run Collection
```powershell
python collect_signals.py --mode historical --limit 500 --parse
```

## Benefits of This Configuration

✅ **Speed:** Groq is 10x faster than other options
✅ **Unlimited Backup:** Ollama has no rate limits
✅ **Automatic Failover:** Seamless transition when Groq maxes out
✅ **Cost-Free:** All options are free
✅ **Reliability:** 4 fallback layers

## Groq Free Tier Limits

- **Requests per minute:** 30
- **Requests per day:** 14,400
- **Tokens per minute:** 15,000
- **Models available:** Llama 3.3 70B, Mixtral, Gemma

**When collecting 500 signals:**
- First 30 signals: Groq (ultra-fast)
- Remaining 470: Ollama (still fast, unlimited)
- Total time: Much faster than before!

## Monitoring

Watch the logs during collection:
```
[INFO] Groq provider loaded (llama-3.3-70b-versatile) - PRIMARY
[INFO] Ollama provider loaded (qwen3:8b) - FALLBACK 1
[INFO] Total providers loaded: 4

[INFO] Parsed by Groq        # First 30 signals
[WARN] Groq rate limited - trying next provider
[INFO] Provider 'Groq' disabled due to failures
[INFO] Parsed by Ollama      # Remaining signals
```

## Troubleshooting

### "No AI providers configured"
→ Add Groq API key to .env

### "Groq rate limited immediately"
→ Check if you've used it today (14,400/day limit)
→ Ollama will automatically take over

### "Ollama error: connection refused"
→ Start Ollama: `ollama serve`
→ Check model downloaded: `ollama list`

### All providers fail
→ Regex parser will handle it (no AI needed for standard formats)

## Performance Comparison

| Provider | Speed | Quality | Cost | Limits |
|----------|-------|---------|------|--------|
| **Groq** | ⚡⚡⚡⚡⚡ (0.5s) | ⭐⭐⭐⭐⭐ | Free | 30/min |
| **Ollama** | ⚡⚡⚡⚡ (5s) | ⭐⭐⭐⭐ | Free | None |
| **OpenRouter** | ⚡⚡ (10s) | ⭐⭐⭐⭐⭐ | Free | 200/day |
| **Local API** | ⚡⚡⚡⚡ (2s) | ⭐⭐⭐⭐ | Free | None |

## Recommended for Different Use Cases

### Heavy Collection (1000+ signals/day)
1. Groq (first 30)
2. Ollama (unlimited)
3. Skip cloud providers

### Quality Priority
1. Groq (fast + excellent)
2. OpenRouter (excellent but slower)
3. Ollama (backup)

### Speed Priority (your current setup)
1. Groq (PRIMARY - fastest)
2. Ollama (fast fallback)
3. Local API (fast backup)
4. OpenRouter (last resort)

This is the **optimal configuration** for your use case! 🚀
