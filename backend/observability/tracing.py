from __future__ import annotations

import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any

from backend.observability.langfuse_client import langfuse_client


def _safe_call(target: Any, methods: list[str], *args: Any, **kwargs: Any) -> Any:
    if not target:
        return None
    for method in methods:
        fn = getattr(target, method, None)
        if callable(fn):
            try:
                result = fn(*args, **kwargs)
                print(f"   ✓ Method '{method}' succeeded")
                return result
            except Exception as e:
                print(f"   ✗ Method '{method}' failed: {type(e).__name__}: {str(e)[:100]}")
                continue
    print(f"   ✗ All methods failed: {methods}")
    return None


class NoOpSpan:
    def __enter__(self) -> "NoOpSpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def set_metadata(self, **metadata: Any) -> None:
        return None

    def add_output(self, text: str) -> None:
        return None

    def capture_exception(self, exc: Exception, **metadata: Any) -> None:
        return None

    def end(self, **metadata: Any) -> None:
        return None


@dataclass
class SpanWrapper:
    _span: Any | None

    def __enter__(self) -> "SpanWrapper":
        if self._span and hasattr(self._span, "__enter__"):
            self._span.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._span and hasattr(self._span, "__exit__"):
            return self._span.__exit__(exc_type, exc, tb)
        return False

    def set_metadata(self, **metadata: Any) -> None:
        if not self._span:
            return
        try:
            if hasattr(self._span, 'set_metadata'):
                self._span.set_metadata(metadata if metadata else {})
            elif hasattr(self._span, 'metadata'):
                self._span.metadata = metadata if metadata else {}
        except Exception as e:
            print(f"   ✗ Metadata error: {type(e).__name__}: {str(e)[:100]}")

    def add_output(self, text: str) -> None:
        if not self._span:
            return
        try:
            if hasattr(self._span, 'add_output'):
                self._span.add_output(text)
            elif hasattr(self._span, 'output'):
                self._span.output = text
        except Exception as e:
            print(f"   ✗ Output error: {type(e).__name__}: {str(e)[:100]}")

    def capture_exception(self, exc: Exception, **metadata: Any) -> None:
        if not self._span:
            return
        try:
            if hasattr(self._span, 'capture_exception'):
                self._span.capture_exception(exc)
            elif hasattr(self._span, 'status_message'):
                self._span.status_message = f"Error: {type(exc).__name__}: {str(exc)}"
        except Exception as e:
            print(f"   ✗ Exception capture error: {type(e).__name__}: {str(e)[:100]}")

    def end(self, **metadata: Any) -> None:
        if not self._span:
            return
        try:
            # Langfuse end() only accepts metadata, not latency_ms
            # Filter out any non-metadata kwargs
            if hasattr(self._span, 'end'):
                self._span.end()  # end() doesn't take kwargs
            elif hasattr(self._span, 'finish'):
                self._span.finish()
        except Exception as e:
            print(f"   ✗ Span end error: {type(e).__name__}: {str(e)[:100]}")


class TraceWrapper(AbstractContextManager):
    def __init__(self, trace_obj: Any | None) -> None:
        self._trace = trace_obj

    def __enter__(self) -> "TraceWrapper":
        if self._trace and hasattr(self._trace, "__enter__"):
            self._trace.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._trace and hasattr(self._trace, "__exit__"):
            return self._trace.__exit__(exc_type, exc, tb)
        return False

    def close(self) -> None:
        if not self._trace:
            return
        try:
            # Langfuse spans need to be ended
            if hasattr(self._trace, 'end'):
                self._trace.end()
            elif hasattr(self._trace, 'finish'):
                self._trace.finish()
        except Exception as e:
            print(f"   ✗ Span close error: {type(e).__name__}: {str(e)[:100]}")

    def start_span(self, name: str, **metadata: Any) -> SpanWrapper:
        if not self._trace:
            return SpanWrapper(None)
        try:
            # Langfuse spans have start_span method to create child spans
            if hasattr(self._trace, 'start_span'):
                span_obj = self._trace.start_span(name=name, metadata=metadata if metadata else None)
            # Or start_observation for more recent API
            elif hasattr(self._trace, 'start_observation'):
                span_obj = self._trace.start_observation(name=name, as_type="span", metadata=metadata if metadata else None)
            else:
                print(f"   ✗ No span creation method found on trace object")
                return SpanWrapper(None)
            if span_obj:
                return SpanWrapper(span_obj)
            else:
                print(f"   ✗ Span creation returned None")
                return SpanWrapper(None)
        except Exception as e:
            print(f"   ✗ Span creation error: {type(e).__name__}: {str(e)[:100]}")
            return SpanWrapper(None)

    def track_event(self, name: str, **metadata: Any) -> None:
        if not self._trace:
            return
        try:
            # Langfuse observations can have events added via add_event method
            if hasattr(self._trace, 'add_event'):
                self._trace.add_event(name=name, metadata=metadata if metadata else None)
            elif hasattr(self._trace, 'create_event'):
                self._trace.create_event(name=name, metadata=metadata if metadata else None)
        except Exception as e:
            print(f"   ✗ Event tracking error: {type(e).__name__}: {str(e)[:100]}")

    def track_generation(self, name: str, **metadata: Any) -> SpanWrapper:
        if not self._trace:
            return SpanWrapper(None)
        try:
            # Langfuse spans can create generation child spans
            if hasattr(self._trace, 'start_span'):
                gen_obj = self._trace.start_span(name=name, metadata=metadata if metadata else None)
            elif hasattr(self._trace, 'start_observation'):
                gen_obj = self._trace.start_observation(name=name, as_type="generation", metadata=metadata if metadata else None)
            else:
                return SpanWrapper(None)
            if gen_obj is None:
                return SpanWrapper(None)
            return SpanWrapper(gen_obj)
        except Exception as e:
            print(f"   ✗ Generation creation error: {type(e).__name__}: {str(e)[:100]}")
            return SpanWrapper(None)

    def capture_exception(self, exc: Exception, **metadata: Any) -> None:
        if not self._trace:
            return
        try:
            # Try to set the exception as an error
            if hasattr(self._trace, 'set_status_message'):
                self._trace.set_status_message(f"Error: {type(exc).__name__}: {str(exc)}")
            if hasattr(self._trace, 'status_message'):
                self._trace.status_message = f"Error: {type(exc).__name__}: {str(exc)}"
        except Exception as e:
            print(f"   ✗ Exception capture error: {type(e).__name__}: {str(e)[:100]}")


def create_trace(name: str, **metadata: Any) -> TraceWrapper:
    if not langfuse_client.enabled:
        print(f"⚠️ [TRACE] Langfuse disabled - creating no-op trace for '{name}'")
        return TraceWrapper(None)

    print(f"📝 [TRACE] Creating trace '{name}' with metadata: {list(metadata.keys())}")
    try:
        # Langfuse SDK uses start_observation() to create traces
        trace_obj = langfuse_client.client.start_observation(
            name=name,
            as_type="span",
            metadata=metadata if metadata else None,
        )
        if trace_obj:
            print(f"✅ [TRACE] Trace '{name}' created successfully (ID: {trace_obj.trace_id if hasattr(trace_obj, 'trace_id') else 'N/A'})")
        else:
            print(f"❌ [TRACE] Failed to create trace '{name}' - returned None")
        return TraceWrapper(trace_obj)
    except Exception as e:
        print(f"❌ [TRACE] Exception creating trace '{name}': {type(e).__name__}: {str(e)[:100]}")
        return TraceWrapper(None)


def track_event(trace: TraceWrapper | None, name: str, **metadata: Any) -> None:
    if not trace:
        return
    trace.track_event(name, **metadata)


def start_span(trace: TraceWrapper | None, name: str, **metadata: Any) -> SpanWrapper:
    if not trace:
        return SpanWrapper(None)
    return trace.start_span(name, **metadata)


def end_span(span: SpanWrapper | None, **metadata: Any) -> None:
    if not span:
        return
    span.end(**metadata)


def track_generation(trace: TraceWrapper | None, name: str, **metadata: Any) -> SpanWrapper:
    if not trace:
        return SpanWrapper(None)
    return trace.track_generation(name, **metadata)


def capture_exception(trace: TraceWrapper | None, exc: Exception, **metadata: Any) -> None:
    if not trace:
        return
    trace.capture_exception(exc, **metadata)
