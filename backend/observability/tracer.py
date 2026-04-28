from __future__ import annotations

from contextlib import contextmanager

try:
    from langfuse import Langfuse
except Exception:  # pragma: no cover
    Langfuse = None


class Tracer:
    def __init__(self, public_key: str | None, secret_key: str | None, host: str):
        self._enabled = bool(public_key and secret_key and Langfuse)
        self._langfuse = (
            Langfuse(public_key=public_key, secret_key=secret_key, host=host)
            if self._enabled
            else None
        )

    @contextmanager
    def trace(self, name: str, **metadata):
        if not self._enabled:
            yield None
            return

        trace = self._langfuse.trace(name=name, metadata=metadata)
        try:
            yield trace
        finally:
            trace.flush()
