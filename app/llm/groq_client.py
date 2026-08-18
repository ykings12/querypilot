"""Groq chat completion client — OpenAI-compatible API, free tier for dev."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings


@dataclass(frozen=True)
class ChatCompletion:
    content: dict[str, Any]
    prompt_tokens: int | None
    completion_tokens: int | None
    raw_content: str


class GroqClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def chat_json(
        self, *, system: str, user: str, model: str | None = None
    ) -> ChatCompletion:
        if not self.settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        payload = {
            "model": model or self.settings.sql_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        max_attempts = 5
        body: dict[str, Any] | None = None
        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(max_attempts):
                try:
                    response = await client.post(
                        f"{self.settings.groq_base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                except httpx.TransportError:
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(min(2**attempt, 15))
                        continue
                    raise
                if response.status_code == 429 and attempt < max_attempts - 1:
                    retry_after = response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else min(2**attempt, 30)
                    await asyncio.sleep(delay)
                    continue
                if response.status_code in (502, 503, 504) and attempt < max_attempts - 1:
                    await asyncio.sleep(min(2**attempt, 15))
                    continue
                response.raise_for_status()
                body = response.json()
                break

        if body is None:
            raise RuntimeError("Groq chat completion failed after retries")

        raw_content = body["choices"][0]["message"]["content"]
        usage = body.get("usage") or {}
        return ChatCompletion(
            content=json.loads(raw_content),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            raw_content=raw_content,
        )
