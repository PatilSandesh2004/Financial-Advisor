from __future__ import annotations

import json
import time
from dataclasses import dataclass

RESPONSE_CACHE_TTL = 600  # 10 minutes


@dataclass
class RedisSessionStore:
    client: any
    ttl_seconds: int

    async def get_messages(self, session_id: str) -> list[dict]:
        raw = await self.client.get(f"session:{session_id}")
        if not raw:
            return []
        try:
            return json.loads(raw)
        except Exception:
            return []

    async def set_messages(self, session_id: str, messages: list[dict]) -> None:
        await self.client.setex(
            f"session:{session_id}", self.ttl_seconds, json.dumps(messages, ensure_ascii=False)
        )

    async def get_response(self, key: str) -> str | None:
        return await self.client.get(f"resp:{key}")

    async def set_response(self, key: str, response: str) -> None:
        await self.client.setex(f"resp:{key}", RESPONSE_CACHE_TTL, response)

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

    async def get_messages(self, session_id: str) -> list[dict]:
        entry = self._store.get(session_id)
        if not entry:
            return []
        expires_at, messages = entry
        if time.time() > expires_at:
            self._store.pop(session_id, None)
            return []
        return messages

    async def set_messages(self, session_id: str, messages: list[dict]) -> None:
        self._store[session_id] = (time.time() + self.ttl_seconds, messages)

    async def get_response(self, key: str) -> str | None:
        entry = self._response_cache.get(key)
        if not entry:
            return None
        expires_at, response = entry
        if time.time() > expires_at:
            self._response_cache.pop(key, None)
            return None
        return response

    async def set_response(self, key: str, response: str) -> None:
        self._response_cache[key] = (time.time() + RESPONSE_CACHE_TTL, response)

    async def get_title(self, session_id: str) -> str:
        return self._titles.get(session_id, "New Chat")

    async def set_title(self, session_id: str, title: str) -> None:
        self._titles[session_id] = title
