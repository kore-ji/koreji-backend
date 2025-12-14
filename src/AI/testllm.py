# testllm.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # 只讀 .env

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found")

def call_llm(prompt: str):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "koreji-test",
    }
    payload = {
        # "model": "openai/gpt-oss-120b:free",
        #"model": "google/gemini-2.0-flash-exp:free",
        "model": "google/gemma-3n-e2b-it:free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(call_llm("用一句話跟我打招呼"))

