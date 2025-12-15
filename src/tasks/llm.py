import os
import json
import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def openrouter_chat(messages: list[dict], *, model: str | None = None) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in environment variables") 
    
    model = model or os.getenv("OPENROUTER_MODEL", "google/gemma-3n-e2b-it:free")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost"),
        "X-Title": os.getenv("OPENROUTER_APP_NAME", "koreji-backend"),
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.2,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(OPENROUTER_URL, headers=headers, json=payload)

        if r.status_code >= 400:
            print("OpenRouter error:", r.status_code, r.text)
            
        r.raise_for_status()
        data = r.json()
    
    return data["choices"][0]["message"]["content"]