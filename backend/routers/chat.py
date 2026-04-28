from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from backend.agent.agent import AdvisorAgent
from backend.config import get_settings
from backend.dependencies import groq_client_dep, session_store_dep
from backend.memory.conversation_manager import ConversationManager
from backend.models.request_models import ChatRequest


router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    chat_request: ChatRequest,
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

    answer_text = await agent.answer(
        session_id=chat_request.session_id,
        query=chat_request.message,
        portfolio_id=chat_request.portfolio_id,
    )

    return {"answer": answer_text}


@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatRequest,
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

    async def event_generator() -> AsyncIterator[dict]:
        async for token in agent.stream_answer(
            session_id=chat_request.session_id,
            query=chat_request.message,
            portfolio_id=chat_request.portfolio_id,
        ):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
