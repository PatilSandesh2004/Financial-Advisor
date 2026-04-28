from __future__ import annotations

from collections.abc import AsyncIterator

import redis.asyncio as redis

from backend.config import Settings, get_settings
from backend.groq_client.client import GroqClient
from backend.memory.session_manager import InMemorySessionStore, RedisSessionStore


def settings_dep() -> Settings:
    return get_settings()


async def session_store_dep(settings: Settings = settings_dep()) -> AsyncIterator[RedisSessionStore | InMemorySessionStore]:
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        yield RedisSessionStore(client=client, ttl_seconds=settings.session_ttl_seconds)
    except Exception:
        yield InMemorySessionStore(ttl_seconds=settings.session_ttl_seconds)


def groq_client_dep(settings: Settings = settings_dep()) -> GroqClient:
    return GroqClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        max_tokens=settings.groq_max_tokens,
        temperature=settings.groq_temperature,
    )
