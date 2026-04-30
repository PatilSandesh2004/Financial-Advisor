from __future__ import annotations

import time
from backend.observability.tracing import capture_exception, end_span, start_span


class ConversationManager:
    def __init__(self, store, max_turns: int = 5):
        self.store = store
        self.max_turns = max_turns

    async def load(self, session_id: str, trace=None) -> list[dict]:
        span = start_span(
            trace,
            "history-load",
            session_id=session_id,
            storage_backend=type(self.store).__name__,
        )
        start = time.perf_counter()
        try:
            messages = await self.store.get_messages(session_id, trace=trace)
            span.set_metadata(loaded_message_count=len(messages))
            return messages
        except Exception as exc:
            capture_exception(trace, exc, session_id=session_id, stage="history-load")
            raise
        finally:
            end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))

    async def append(self, session_id: str, role: str, content: str, trace=None) -> list[dict]:
        span = start_span(
            trace,
            "history-append",
            session_id=session_id,
            storage_backend=type(self.store).__name__,
        )
        start = time.perf_counter()
        try:
            history = await self.load(session_id, trace=trace)
            history.append({"role": role, "content": content})
            history = history[-(self.max_turns * 2) :]
            await self.store.set_messages(session_id, history, trace=trace)
            span.set_metadata(pruned_message_count=len(history), saved_message_count=len(history))
            return history
        except Exception as exc:
            capture_exception(trace, exc, session_id=session_id, stage="history-append")
            raise
        finally:
            end_span(span, latency_ms=round((time.perf_counter() - start) * 1000, 2))
