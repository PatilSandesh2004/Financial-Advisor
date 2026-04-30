from __future__ import annotations

import json
import time
from dataclasses import dataclass

from backend.observability.tracing import capture_exception, end_span, start_span

RESPONSE_CACHE_TTL = 600  # 10 minutes


@dataclass
class RedisSessionStore:
    client: any
    ttl_seconds: int

    async def get_messages(self, session_id: str, trace=None) -> list[dict]:
        span = start_span(
            trace,
            "history-load",
            session_id=session_id,
            storage_backend="redis",
            fallback=False,
        )
        start = time.perf_counter()
        raw = await self.client.get(f"session:{session_id}")
        messages: list[dict] = []
        if raw:
            try:
                messages = json.loads(raw)
            except Exception as exc:
                capture_exception(trace, exc, session_id=session_id, stage="session-load")
                messages = []
        span.set_metadata(loaded_message_count=len(messages))
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
        return messages

    async def set_messages(self, session_id: str, messages: list[dict], trace=None) -> None:
        span = start_span(
            trace,
            "history-append",
            session_id=session_id,
            storage_backend="redis",
            fallback=False,
            saved_message_count=len(messages),
        )
        start = time.perf_counter()
        await self.client.setex(
            f"session:{session_id}", self.ttl_seconds, json.dumps(messages, ensure_ascii=False)
        )
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))

    async def get_response(self, key: str, trace=None) -> str | None:
        span = start_span(
            trace,
            "response-cache-get",
            cache_key=key,
            storage_backend="redis",
        )
        start = time.perf_counter()
        response = await self.client.get(f"resp:{key}")
        span.set_metadata(cache_hit=response is not None)
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
        return response

    async def set_response(self, key: str, response: str, trace=None) -> None:
        span = start_span(
            trace,
            "response-cache-set",
            cache_key=key,
            storage_backend="redis",
        )
        start = time.perf_counter()
        await self.client.setex(f"resp:{key}", RESPONSE_CACHE_TTL, response)
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))

    async def get_title(self, session_id: str) -> str:
        return await self.client.get(f"title:{session_id}") or "New Chat"

    async def set_title(self, session_id: str, title: str) -> None:
        await self.client.setex(f"title:{session_id}", self.ttl_seconds, title)


class InMemorySessionStore:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, list[dict]]] = {}
        self._response_cache: dict[str, tuple[float, str]] = {}
        self._titles: dict[str, str] = {}

    async def get_messages(self, session_id: str, trace=None) -> list[dict]:
        span = start_span(
            trace,
            "history-load",
            session_id=session_id,
            storage_backend="memory",
            fallback=True,
        )
        start = time.perf_counter()
        entry = self._store.get(session_id)
        messages: list[dict] = []
        if not entry:
            end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
            return []
        expires_at, messages = entry
        if time.time() > expires_at:
            self._store.pop(session_id, None)
            messages = []
        span.set_metadata(loaded_message_count=len(messages))
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
        return messages

    async def set_messages(self, session_id: str, messages: list[dict], trace=None) -> None:
        span = start_span(
            trace,
            "history-append",
            session_id=session_id,
            storage_backend="memory",
            fallback=True,
            saved_message_count=len(messages),
        )
        start = time.perf_counter()
        self._store[session_id] = (time.time() + self.ttl_seconds, messages)
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))

    async def get_response(self, key: str, trace=None) -> str | None:
        span = start_span(
            trace,
            "response-cache-get",
            cache_key=key,
            storage_backend="memory",
            fallback=True,
        )
        start = time.perf_counter()
        entry = self._response_cache.get(key)
        response: str | None = None
        if entry:
            expires_at, response = entry
            if time.time() > expires_at:
                self._response_cache.pop(key, None)
                response = None
        span.set_metadata(cache_hit=response is not None)
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
        return response

    async def set_response(self, key: str, response: str, trace=None) -> None:
        span = start_span(
            trace,
            "response-cache-set",
            cache_key=key,
            storage_backend="memory",
            fallback=True,
        )
        start = time.perf_counter()
        self._response_cache[key] = (time.time() + RESPONSE_CACHE_TTL, response)
        end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))

    async def get_title(self, session_id: str) -> str:
        return self._titles.get(session_id, "New Chat")

    async def set_title(self, session_id: str, title: str) -> None:
        self._titles[session_id] = title
