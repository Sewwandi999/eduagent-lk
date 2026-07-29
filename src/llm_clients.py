from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from src.config import Settings


class LLMUnavailableError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str


class ChatClient:
    """Small OpenAI-compatible client for Groq and OpenRouter."""

    ENDPOINTS = {
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    }

    def __init__(self, settings: Settings, timeout: int = 90):
        self.settings = settings
        self.timeout = timeout

    def _api_key(self, provider: str) -> str:
        if provider == "groq":
            return self.settings.groq_api_key
        if provider == "openrouter":
            return self.settings.openrouter_api_key
        raise ValueError(f"Unsupported provider: {provider}")

    def complete(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 3500,
        json_mode: bool = False,
    ) -> LLMResponse:
        provider = provider.lower()
        key = self._api_key(provider)
        if not key:
            raise LLMUnavailableError(f"No API key configured for {provider}")

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/your-username/eduagent-lk"
            headers["X-Title"] = "EduAgent LK"

        try:
            response = requests.post(
                self.ENDPOINTS[provider],
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return LLMResponse(content=content, model=model, provider=provider)
        except requests.RequestException as exc:
            detail = ""
            if getattr(exc, "response", None) is not None:
                detail = f": {exc.response.text[:500]}"
            raise LLMUnavailableError(f"{provider} request failed{detail}") from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise LLMUnavailableError("Unexpected model API response format") from exc
