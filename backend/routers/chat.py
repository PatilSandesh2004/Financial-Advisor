from __future__ import annotations

import hashlib
import json
import re
import time
import traceback
from collections.abc import AsyncIterator
from typing import Optional

from fastapi import APIRouter, Depends, Body, Request
from sse_starlette.sse import EventSourceResponse

from groq import AsyncGroq

from backend.agent.agent import AdvisorAgent
from backend.config import get_settings
from backend.dependencies import groq_client_dep, session_store_dep
from backend.memory.conversation_manager import ConversationManager
from backend.memory.session_manager import RedisSessionStore
from backend.observability.tracing import (
    capture_exception,
    create_trace,
    end_span,
    start_span,
    track_event,
)
from backend.utils.logger import logger


def _cache_key(portfolio_id: str | None, query: str) -> str:
    content = f"{portfolio_id}:{query.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()


async def _get_cached(store, portfolio_id: str | None, query: str, trace=None) -> str | None:
    try:
        return await store.get_response(_cache_key(portfolio_id, query), trace=trace)
    except Exception as exc:
        capture_exception(trace, exc, stage="response-cache-get")
        return None


async def _set_cached(store, portfolio_id: str | None, query: str, response: str, trace=None) -> None:
    try:
        await store.set_response(_cache_key(portfolio_id, query), response, trace=trace)
    except Exception as exc:
        capture_exception(trace, exc, stage="response-cache-set")
        pass


router = APIRouter(tags=["chat"])


@router.post("/_debug_echo")
async def _debug_echo(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = (await request.body()).decode(errors="replace")
    return {"received": data}


@router.post("/chat/complete")
async def chat_complete(
    session_id: str = Body(...),
    message: str = Body(...),
    portfolio_id: Optional[str] = Body(None),
    request: Request = None,
    store=Depends(session_store_dep),
    groq=Depends(groq_client_dep),
):
    """Non-streaming fallback endpoint: returns the full assistant answer as JSON."""
    settings = get_settings()
    trace = create_trace(
        "financial-advisor-chat",
        session_id=session_id,
        portfolio_id=portfolio_id,
        endpoint="/api/v1/chat/complete",
        transport="http",
        query=message,
    )
    conversation = ConversationManager(store)
    agent = AdvisorAgent(
        groq=groq,
        conversation=conversation,
        api_key=settings.groq_api_key,
        router_model=settings.groq_router_model,
    )

    try:
        raw_body = (await request.body()).decode(errors="replace") if request is not None else "<no request>"
    except Exception as exc:  # pragma: no cover - defensive logging
        raw_body = f"<error reading body: {exc}>"
    logger.info("chat/complete endpoint called", session_id=session_id, message=message, portfolio_id=portfolio_id, raw_body=raw_body)
    track_event(trace, "user-input", input=message)
    try:
        cached = await _get_cached(store, portfolio_id, message, trace=trace)
        if cached:
            logger.info("cache hit (non-stream)", session_id=session_id)
            track_event(trace, "cache-hit", cache_type="response")
            return {"answer": cached}

        answer_text = await agent.answer(
            session_id=session_id,
            query=message,
            portfolio_id=portfolio_id,
            trace=trace,
        )
        await _set_cached(store, portfolio_id, message, answer_text, trace=trace)
        return {"answer": answer_text}
    except Exception as exc:  # pragma: no cover - surface server errors gracefully
        tb = traceback.format_exc()
        error_msg = str(exc)
        logger.error("chat/complete handler error", session_id=session_id, error=error_msg, traceback=tb)
        print("\n" + "="*60)
        print(f"[CHAT COMPLETE ENDPOINT ERROR]")
        print(f"Session: {session_id}")
        print(f"Message: {message}")
        print(f"Portfolio: {portfolio_id}")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error Message: {error_msg}")
        print(f"Traceback:\n{tb}")
        print("="*60 + "\n")

        if "401" in error_msg or "Unauthorized" in error_msg:
            fallback_answer = (
                "**API Key Error (401 Unauthorized)**\n\n"
                "The Groq API key is invalid or expired.\n\n"
                "**Fix:** Update `GROQ_API_KEY` in your `.env` file and restart the backend."
            )
        elif "429" in error_msg or "Rate limited" in error_msg or "Too Many Requests" in error_msg:
            fallback_answer = (
                "**Rate Limit Reached (Groq Free Tier)**\n\n"
                "Too many requests. Please wait 1–2 minutes and try again."
            )
        else:
            fallback_answer = f"**Backend Error**\n\n{error_msg}"
        return {"answer": fallback_answer}
    finally:
        trace.close()


@router.post("/chat", response_class=EventSourceResponse)
@router.post("/chat/stream", include_in_schema=False, response_class=EventSourceResponse)
async def chat_stream(
    session_id: str = Body(...),
    message: str = Body(...),
    portfolio_id: Optional[str] = Body(None),
    request: Request = None,
    store=Depends(session_store_dep),
    groq=Depends(groq_client_dep),
):
    """Streaming endpoint (SSE): yields tokens as events for client-side streaming."""
    settings = get_settings()
    trace = create_trace(
        "financial-advisor-chat",
        session_id=session_id,
        portfolio_id=portfolio_id,
        endpoint="/api/v1/chat",
        transport="sse",
        query=message,
    )
    conversation = ConversationManager(store)
    agent = AdvisorAgent(
        groq=groq,
        conversation=conversation,
        api_key=settings.groq_api_key,
        router_model=settings.groq_router_model,
    )

    try:
        raw_body = (await request.body()).decode(errors="replace") if request is not None else "<no request>"
    except Exception as exc:  # pragma: no cover - defensive logging
        raw_body = f"<error reading body: {exc}>"
    
    print("\n" + "="*80)
    print(f"[CHAT STREAM] ⭐ USER QUERY RECEIVED")
    print(f"  Session: {session_id}")
    print(f"  Portfolio: {portfolio_id}")
    print(f"  Message: {message}")
    print(f"  Request Body: {raw_body[:200]}...")
    print("="*80)
    
    logger.info(
        "chat endpoint called",
        session_id=session_id,
        message=message,
        portfolio_id=portfolio_id,
        raw_body=raw_body,
    )
    track_event(trace, "user-input", input=message)

    async def event_generator() -> AsyncIterator[dict]:
        def _format_text(text: str) -> str:
            out = re.sub(r"\n{3,}", "\n\n", text)
            out = re.sub(r" +\n", "\n", out)
            return out.strip()

        sse_span = start_span(
            trace,
            "sse-stream",
            session_id=session_id,
            portfolio_id=portfolio_id,
            endpoint="/api/v1/chat",
            transport="sse",
        )
        start = time.perf_counter()
        full = ""
        token_count = 0
        first_token_time: float | None = None

        try:
            cached = await _get_cached(store, portfolio_id, message, trace=trace)
            if cached:
                logger.info("cache hit (stream)", session_id=session_id)
                track_event(trace, "cache-hit", cache_type="response")
                yield {"event": "token", "data": json.dumps(cached)}
                yield {"event": "final", "data": cached}
                yield {"event": "done", "data": "[DONE]"}
                return

            async for event in agent.stream_answer(
                session_id=session_id,
                query=message,
                portfolio_id=portfolio_id,
                trace=trace,
            ):
                if event["type"] == "thinking":
                    yield {"event": "thinking", "data": json.dumps(event)}
                elif event["type"] == "token":
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                        sse_span.set_metadata(
                            first_token_latency_ms=round((first_token_time - start) * 1000, 2)
                        )
                        track_event(trace, "stream-started")
                    full += event["content"]
                    token_count += 1
                    yield {"event": "token", "data": json.dumps(event["content"])}

            final_text = _format_text(full)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            sse_span.set_metadata(
                token_count=token_count,
                stream_completed=True,
                total_stream_duration_ms=duration_ms,
            )
            logger.info("stream done", session_id=session_id, length=len(final_text))
            await _set_cached(store, portfolio_id, message, final_text, trace=trace)
            yield {"event": "final", "data": final_text}
        except Exception as exc:
            tb = traceback.format_exc()
            error_msg = str(exc)
            logger.error("stream error", session_id=session_id, error=error_msg, traceback=tb)
            capture_exception(trace, exc, stage="sse-stream", session_id=session_id)
            sse_span.set_metadata(stream_interrupted=True, error=error_msg)
            print(f"\n[chat_stream] ERROR: {error_msg}\n{tb}")
            if "401" in error_msg or "Unauthorized" in error_msg:
                friendly = (
                    "**API Key Error (401 Unauthorized)**\n\n"
                    "The Groq API key is invalid or expired.\n\n"
                    "**Fix:** Update `GROQ_API_KEY` in `.env` and restart the backend."
                )
            elif "429" in error_msg or "Rate limited" in error_msg or "Too Many Requests" in error_msg:
                friendly = (
                    "**Rate Limit Reached (Groq Free Tier)**\n\n"
                    "Too many requests. Please wait 1–2 minutes and try again."
                )
            else:
                friendly = f"**Backend Error**\n\n{error_msg}"
            yield {"event": "error", "data": friendly}
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            sse_span.set_metadata(total_stream_duration_ms=duration_ms, token_count=token_count)
            end_span(sse_span, duration_ms=duration_ms)
            trace.close()
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())


@router.post("/router")
async def router_endpoint(
    query: str = Body(...),
    session_id: Optional[str] = Body(None),
    store=Depends(session_store_dep),
):
    """Internal router endpoint: returns the DataRouter decision for a query."""
    trace = create_trace(
        "financial-advisor-router",
        session_id=session_id,
        endpoint="/api/v1/router",
        query=query,
        transport="http",
    )
    track_event(trace, "user-input", input=query)
    settings = get_settings()
    router = DataRouter(api_key=settings.groq_api_key, router_model=settings.groq_router_model)
    try:
        decision = await router.route_query(query, trace=trace)
        track_event(trace, "router-output", decision=decision)
        logger.info("router endpoint called", session_id=session_id, query=query, decision=decision)
        return decision
    except Exception as exc:
        capture_exception(trace, exc, stage="financial-advisor-router")
        raise
    finally:
        trace.close()


@router.post("/chat/title")
async def generate_title(
    session_id: str = Body(...),
    message: str = Body(...),
    store=Depends(session_store_dep),
):
    """Generate a short session title from the user's first message using the fast model."""
    settings = get_settings()
    if not settings.groq_api_key:
        title = message[:40].strip()
        await store.set_title(session_id, title)
        return {"title": title}
    try:
        client = AsyncGroq(api_key=settings.groq_api_key)
        response = await client.chat.completions.create(
            model=settings.groq_router_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a concise 4-6 word title for the user's query. "
                        "Return ONLY the title text. No quotes, no punctuation at the end."
                    ),
                },
                {"role": "user", "content": message},
            ],
            max_tokens=20,
            temperature=0.3,
        )
        title = response.choices[0].message.content.strip().strip('"').strip("'")
    except Exception:
        title = message[:40].strip()
    await store.set_title(session_id, title)
    return {"title": title}
