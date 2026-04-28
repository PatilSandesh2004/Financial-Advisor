from __future__ import annotations

import json
import time
from dataclasses import dataclass


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


class InMemorySessionStore:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, list[dict]]] = {}

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
