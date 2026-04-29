from __future__ import annotations

import hashlib
import json
import re
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
from backend.utils.logger import logger


def _cache_key(portfolio_id: str | None, query: str) -> str:
    content = f"{portfolio_id}:{query.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()


async def _get_cached(store, portfolio_id: str | None, query: str) -> str | None:
    try:
        return await store.get_response(_cache_key(portfolio_id, query))
    except Exception:
        return None


async def _set_cached(store, portfolio_id: str | None, query: str, response: str) -> None:
    try:
        await store.set_response(_cache_key(portfolio_id, query), response)
    except Exception:
        pass


router = APIRouter(tags=["chat"])


@router.post("/_debug_echo")
async def _debug_echo(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = (await request.body()).decode(errors="replace")
    return {"received": data}


@router.post("/chat")
async def chat(
    session_id: str = Body(...),
    message: str = Body(...),
    portfolio_id: Optional[str] = Body(None),
    request: Request = None,
    store=Depends(session_store_dep),
    groq=Depends(groq_client_dep),
):
    """Non-streaming endpoint: returns the full assistant answer as JSON."""
    settings = get_settings()
    conversation = ConversationManager(store)
    agent = AdvisorAgent(
        groq=groq,
        conversation=conversation,
        api_key=settings.groq_api_key,
        router_model=settings.groq_router_model,
    )

    # Try to capture raw request body for debugging (may be empty if body already consumed)
    try:
        raw_body = (await request.body()).decode(errors="replace") if request is not None else "<no request>"
    except Exception as exc:  # pragma: no cover - defensive logging
        raw_body = f"<error reading body: {exc}>"
    logger.info("chat endpoint called", session_id=session_id, message=message, portfolio_id=portfolio_id, raw_body=raw_body)
    try:
        cached = await _get_cached(store, portfolio_id, message)
        if cached:
            logger.info("cache hit (non-stream)", session_id=session_id)
            return {"answer": cached}

        answer_text = await agent.answer(
            session_id=session_id,
            query=message,
            portfolio_id=portfolio_id,
        )
        await _set_cached(store, portfolio_id, message, answer_text)
        return {"answer": answer_text}
    except Exception as exc:  # pragma: no cover - surface server errors gracefully
        tb = traceback.format_exc()
        error_msg = str(exc)
        logger.error("chat handler error", session_id=session_id, error=error_msg, traceback=tb)
        # Print detailed logs to stdout for debugging
        print("\n" + "="*60)
        print(f"[CHAT ENDPOINT ERROR]")
        print(f"Session: {session_id}")
        print(f"Message: {message}")
        print(f"Portfolio: {portfolio_id}")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error Message: {error_msg}")
        print(f"Traceback:\n{tb}")
        print("="*60 + "\n")
        
        # Return a fallback response so UI doesn't break
        if "401" in error_msg or "Unauthorized" in error_msg:
            fallback_answer = (
                "**API Key Error (401 Unauthorized)**\n\n"
                "The Groq API key is invalid or expired.\n\n"
                "**To fix:**\n"
                "1. Go to [console.groq.com](https://console.groq.com)\n"
                "2. Generate a new API key\n"
                "3. Update `GROQ_API_KEY` in your `.env` file\n"
                "4. Restart the backend service\n"
            )
        elif "429" in error_msg or "Too Many Requests" in error_msg or "Rate limited" in error_msg:
            fallback_answer = (
                "**Rate Limit Reached (Groq Free Tier)**\n\n"
                "The Groq free tier has strict usage limits. The backend retried with exponential backoff but still hit the limit.\n\n"
                "**Solutions:**\n"
                "1. Wait 2–5 minutes and try again\n"
                "2. Try a simpler question\n"
                "3. Upgrade to a Groq paid plan for higher limits\n"
            )
        else:
            fallback_answer = (
                f"**Backend Error**\n\n"
                f"```\n{error_msg}\n```\n\n"
                "**Next Steps**\n"
                "- Restart the backend service\n"
                "- Verify API credentials in `.env`\n"
                "- Check backend logs for details\n"
            )
        return {"answer": fallback_answer}


@router.post("/chat/stream")
async def chat_stream(
    session_id: str = Body(...),
    message: str = Body(...),
    portfolio_id: Optional[str] = Body(None),
    request: Request = None,
    store=Depends(session_store_dep),
    groq=Depends(groq_client_dep),
):
    """Streaming endpoint (SSE): yields tokens as events for client-side streaming tests."""
    settings = get_settings()
    conversation = ConversationManager(store)
    agent = AdvisorAgent(
        groq=groq,
        conversation=conversation,
        api_key=settings.groq_api_key,
        router_model=settings.groq_router_model,
    )

    # Try to capture raw request body for debugging (may be empty if body already consumed)
    try:
        raw_body = (await request.body()).decode(errors="replace") if request is not None else "<no request>"
    except Exception as exc:  # pragma: no cover - defensive logging
        raw_body = f"<error reading body: {exc}>"
    logger.info(
        "chat/stream endpoint called",
        session_id=session_id,
        message=message,
        portfolio_id=portfolio_id,
        raw_body=raw_body,
    )

    async def event_generator() -> AsyncIterator[dict]:
        def _format_text(text: str) -> str:
            out = re.sub(r"\n{3,}", "\n\n", text)
            out = re.sub(r" +\n", "\n", out)
            return out.strip()

        # Return cached response immediately without calling Groq
        cached = await _get_cached(store, portfolio_id, message)
        if cached:
            logger.info("cache hit (stream)", session_id=session_id)
            yield {"event": "token", "data": json.dumps(cached)}
            yield {"event": "final", "data": cached}
            yield {"event": "done", "data": "[DONE]"}
            return

        full = ""
        try:
            async for event in agent.stream_answer(
                session_id=session_id,
                query=message,
                portfolio_id=portfolio_id,
            ):
                if event["type"] == "thinking":
                    yield {"event": "thinking", "data": json.dumps(event)}
                elif event["type"] == "token":
                    full += event["content"]
                    # JSON-encode so \n characters survive SSE line-based transport
                    yield {"event": "token", "data": json.dumps(event["content"])}

            final_text = _format_text(full)
            logger.info("stream done", session_id=session_id, length=len(final_text))
            await _set_cached(store, portfolio_id, message, final_text)
            yield {"event": "final", "data": final_text}
        except Exception as exc:
            tb = traceback.format_exc()
            error_msg = str(exc)
            logger.error("stream error", session_id=session_id, error=error_msg, traceback=tb)
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
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())


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
