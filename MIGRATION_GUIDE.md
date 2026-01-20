# Migration Guide: Enhanced Parser → Hybrid Parser

## 🔄 Breaking Change: Async Conversion

The `EnhancedParser.parse()` method is now **async** to support AI integration.

## ⚠️ Required Changes

### Before (Synchronous)
```python
from parsers.enhanced_parser import EnhancedParser

parser = EnhancedParser()
result = parser.parse(signal_text)  # ❌ This will break!

if result.is_valid():
    print(f"Symbol: {result.symbol}")
```

### After (Asynchronous)
```python
import asyncio
from parsers.enhanced_parser import EnhancedParser

parser = EnhancedParser(enable_ai=True)
result = await parser.parse(signal_text)  # ✅ Use await

if result.is_valid():
    print(f"Symbol: {result.symbol}")
```

## 📝 Migration Checklist

### 1. Update Function Signatures
All functions that call `parser.parse()` must become async:

```python
# Before
def process_signal(text):
    parser = EnhancedParser()
    result = parser.parse(text)
    return result

# After
async def process_signal(text):
    parser = EnhancedParser(enable_ai=True)
    result = await parser.parse(text)
    return result
```

### 2. Update Main/Entry Points
Add `asyncio.run()` or event loop handling:

```python
# Before
if __name__ == "__main__":
    process_signal(text)

# After
if __name__ == "__main__":
    asyncio.run(process_signal(text))
```

### 3. Update Telegram Bot Handlers
Telethon already supports async, just add `await`:

```python
# Before
@client.on(events.NewMessage)
def handler(event):
    parser = EnhancedParser()
    result = parser.parse(event.text)
    # ...

# After
@client.on(events.NewMessage)
async def handler(event):
    parser = EnhancedParser(enable_ai=True)
    result = await parser.parse(event.text)
    # ...
```

### 4. Update Test Files
Convert test functions to async:

```python
# Before
def test_parser():
    parser = EnhancedParser()
    result = parser.parse(test_signal)
    assert result.symbol == "BTCUSDT"

# After
async def test_parser():
    parser = EnhancedParser(enable_ai=True)
    result = await parser.parse(test_signal)
    assert result.symbol == "BTCUSDT"

# Run with asyncio
if __name__ == "__main__":
    asyncio.run(test_parser())
```

## 🎛️ Configuration Options

### Enable/Disable AI
```python
# With AI (default)
parser = EnhancedParser(enable_ai=True)

# Without AI (regex-only, no breaking changes needed)
parser = EnhancedParser(enable_ai=False)
```

### Custom Confidence Threshold
```python
# Default threshold is 0.85
result = await parser.parse(text)

# Custom threshold (more aggressive AI usage)
result = await parser.parse(text, confidence_threshold=0.75)

# Higher threshold (less AI usage, more cost-effective)
result = await parser.parse(text, confidence_threshold=0.90)
```

## 📦 Files That Need Updates

Based on project structure, these files likely need updates:

### High Priority
- `main.py` - Main bot entry point
- `paper_trading_bot.py` - Paper trading loop
- `download_signals.py` - Signal collection
- Any test files in `tests/` directory

### Medium Priority
- `collect_and_analyze.py` - Analysis scripts
- `debug_parser.py` - Debug utilities
- Custom scripts using the parser

### Low Priority (No changes if not using parser)
- `api.py` - API layer (if it calls parser)
- Email reporter (if it formats signals)

## 🔍 Find Affected Code

Run this to find all files that import EnhancedParser:

```bash
# Windows
findstr /S /I "EnhancedParser" *.py

# Unix/Mac
grep -r "EnhancedParser" --include="*.py"
```

## 🛠️ Quick Fix Template

For each file that uses the parser:

```python
# 1. Add import at top
import asyncio

# 2. Make your function async
async def your_function():
    parser = EnhancedParser(enable_ai=True)
    result = await parser.parse(text)
    # ... rest of code

# 3. Update caller
if __name__ == "__main__":
    asyncio.run(your_function())
```

## 🚨 Common Pitfalls

### 1. Forgetting `await`
```python
# ❌ Wrong - Will return coroutine object
result = parser.parse(text)

# ✅ Correct
result = await parser.parse(text)
```

### 2. Mixing Sync/Async
```python
# ❌ Wrong - Can't await in non-async function
def sync_function():
    result = await parser.parse(text)  # SyntaxError!

# ✅ Correct
async def async_function():
    result = await parser.parse(text)
```

### 3. Event Loop Issues
```python
# ❌ Wrong - Creating multiple event loops
for signal in signals:
    asyncio.run(process(signal))  # Creates new loop each time!

# ✅ Correct - Reuse event loop
async def process_all():
    for signal in signals:
        await process(signal)

asyncio.run(process_all())
```

## ⚡ Performance Tips

### Batch Processing
Process multiple signals concurrently:

```python
async def process_batch(signals):
    parser = EnhancedParser(enable_ai=True)
    
    # Process all signals concurrently
    results = await asyncio.gather(
        *[parser.parse(signal) for signal in signals]
    )
    
    return results
```

### Reuse Parser Instance
Don't create a new parser for each signal:

```python
# ❌ Inefficient
async def process_many(signals):
    results = []
    for signal in signals:
        parser = EnhancedParser(enable_ai=True)  # Creates AI client each time!
        result = await parser.parse(signal)
        results.append(result)
    return results

# ✅ Efficient
async def process_many(signals):
    parser = EnhancedParser(enable_ai=True)  # Create once
    results = []
    for signal in signals:
        result = await parser.parse(signal)
        results.append(result)
    return results
```

## 🧪 Testing Strategy

### 1. Test Regex-Only First
Disable AI to ensure regex logic still works:

```python
parser = EnhancedParser(enable_ai=False)
result = await parser.parse(test_signal)
assert result.confidence >= 0.8
```

### 2. Test AI Fallback
Use ambiguous signals to trigger AI:

```python
parser = EnhancedParser(enable_ai=True)
ambiguous = "BTC looking good around 42k, targets 45-48-50"
result = await parser.parse(ambiguous)
# Check if AI was used
assert any("AI Path" in note for note in result.parsing_notes)
```

### 3. Test Whitelist Learning
Parse same signal twice, second should be fast path:

```python
parser = EnhancedParser(enable_ai=True)
await parser.parse(signal)  # First parse (full)
result = await parser.parse(signal)  # Second parse (fast path)
assert any("Fast-path" in note for note in result.parsing_notes)
```

## 📊 Monitoring

Track parser performance in production:

```python
parser = EnhancedParser(enable_ai=True)

# ... process signals ...

stats = parser.get_stats()
print(f"Fast Path Hit Rate: {stats['hit_rate']}")
print(f"AI Usage Rate: {stats['ai_usage_rate']}")
print(f"Total Parses: {stats['total_parses']}")
```

## 🔧 Rollback Plan

If issues occur, disable AI temporarily:

```python
# Emergency rollback to regex-only
parser = EnhancedParser(enable_ai=False)
```

Or set in environment:

```env
# In .env file
PARSER_ENABLE_AI=false
```

Then in code:

```python
import os
enable_ai = os.getenv("PARSER_ENABLE_AI", "true").lower() == "true"
parser = EnhancedParser(enable_ai=enable_ai)
```

## ✅ Verification

After migration, verify:

1. ✅ All imports work without errors
2. ✅ Async functions use `await` keyword
3. ✅ Main entry points use `asyncio.run()`
4. ✅ Tests pass with `enable_ai=False`
5. ✅ Tests pass with `enable_ai=True` (if API key set)
6. ✅ No "coroutine was never awaited" warnings
7. ✅ Parser stats show reasonable hit rates

## 📞 Support

If you encounter issues:

1. Check `HYBRID_ARCHITECTURE.md` for architecture details
2. Review `parsers/enhanced_parser.py` inline comments
3. Run `python test_hybrid_parser.py` for validation
4. Check logs for routing decisions

## 🎯 Next Steps

After migration:

1. Monitor AI usage rates in production
2. Adjust `confidence_threshold` based on accuracy
3. Review whitelist hit rates (should increase over time)
4. Consider cost optimization strategies
5. Implement Phase 2 features (CCXT, Risk Sentinel)
