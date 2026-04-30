from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from backend.groq_client.streaming import stream_openai_compatible
from backend.observability.tracing import capture_exception, end_span, start_span


def _before_retry(retry_state: Any) -> None:
    fn = getattr(retry_state, "fn", None)
    self_obj = getattr(fn, "__self__", None)
    if self_obj is not None and hasattr(self_obj, "_retry_attempts"):
        self_obj._retry_attempts += 1


class GroqClient:
    def __init__(self, api_key: str | None, model: str, max_tokens: int, temperature: float):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._retry_attempts = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
        before=_before_retry,
    )
    async def stream_chat(self, messages: list[dict], trace=None) -> AsyncIterator[str]:
        self._retry_attempts = 0
        span = start_span(
            trace,
            "dependency-groq-reasoner",
            dependency_name="groq",
            model=self.model,
            streamed=True,
        )
        start = time.perf_counter()
        
        print(f"\n[GROQ CLIENT] 🚀 Calling Groq API")
        print(f"[GROQ CLIENT]   Model: {self.model}")
        print(f"[GROQ CLIENT]   Temperature: {self.temperature}")
        print(f"[GROQ CLIENT]   Max tokens: {self.max_tokens}")
        print(f"[GROQ CLIENT]   Message count: {len(messages)}")
        
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            preview = content[:100] if len(content) <= 100 else content[:100] + "..."
            print(f"[GROQ CLIENT]   Message {i}: [{role}] {preview}")

        if not self.api_key:
            print("[GroqClient.stream_chat] WARNING: No API key configured, using fallback")
            async def _fallback() -> AsyncIterator[str]:
                yield "Groq is not configured (missing GROQ_API_KEY). Running in local fallback mode."
            span.set_metadata(retry_count=self._retry_attempts, fallback=True)
            end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
            return _fallback()

        try:
            result = stream_openai_compatible(
                api_key=self.api_key,
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            span.set_metadata(retry_count=self._retry_attempts)
            print("[GROQ CLIENT] ✅ Stream connection opened")
            return result
        except Exception as e:
            capture_exception(trace, e, dependency_name="groq", retry_count=self._retry_attempts)
            span.set_metadata(retry_count=self._retry_attempts, error=str(e))
            print(f"[GROQ CLIENT] ❌ Error: {type(e).__name__}: {str(e)}")
            raise
        finally:
            end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
