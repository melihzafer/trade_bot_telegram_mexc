import os
import requests

os.environ['OPENROUTER_API_KEY'] = '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'

headers = {
    'Authorization': f'Bearer {os.environ["OPENROUTER_API_KEY"]}'
}

print("Testing OpenRouter API key...")
r = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"Error: {r.text}")
else:
    print("API key is valid!")
    # Check if model exists
    models = r.json()
    deepseek_models = [m for m in models.get('data', []) if 'deepseek' in m.get('id', '').lower()]
    print(f"\nAvailable DeepSeek models: {len(deepseek_models)}")
    for model in deepseek_models[:5]:
        print(f"  - {model.get('id')}")
