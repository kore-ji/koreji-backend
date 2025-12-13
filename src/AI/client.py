# src/ai/llm_client.py

import json
import requests
from typing import List, Dict, Any


class LLMClient:
    """
    A unified interface for calling different LLM providers:
    - OpenRouter (Gemini, GPT, Claude)
    - Ollama (local models)
    """

    def __init__(self, provider: str, model: str, api_key: str = None):
        """
        provider: "openrouter" or "ollama"
        model: model name ("google/gemini-pro-1.5", "qwen2:7b", etc.)
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key

    # ==============================
    # OpenRouter
    # ==============================
    def _call_openrouter(self, prompt: str) -> str:
        url = "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"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    # ==============================
    # Ollama (本地模型)
    # ==============================
    def _call_ollama(self, prompt: str) -> str:
        url = "http://localhost:11434/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]

    # ==============================
    # Public function
    # ==============================
    def generate(self, prompt: str) -> str:
        """
        Automatically route to correct provider.
        """
        if self.provider == "openrouter":
            return self._call_openrouter(prompt)

        if self.provider == "ollama":
            return self._call_ollama(prompt)

        raise ValueError(f"Unknown provider: {self.provider}")
