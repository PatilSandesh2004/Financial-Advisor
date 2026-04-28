from __future__ import annotations

from collections.abc import AsyncIterator

from tenacity import retry, stop_after_attempt, wait_exponential

from backend.groq_client.streaming import stream_openai_compatible


class GroqClient:
    def __init__(self, api_key: str | None, model: str, max_tokens: int, temperature: float):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    async def stream_chat(self, messages: list[dict]) -> AsyncIterator[str]:
        if not self.api_key:
            async def _fallback() -> AsyncIterator[str]:
                yield "Groq is not configured (missing GROQ_API_KEY). Running in local fallback mode."
            return _fallback()

        return stream_openai_compatible(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
