from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from backend.agent.agent import AdvisorAgent
from backend.dependencies import groq_client_dep, session_store_dep
from backend.memory.conversation_manager import ConversationManager
from backend.models.request_models import ChatRequest


router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    store=Depends(session_store_dep),
    groq=Depends(groq_client_dep),
):
    conversation = ConversationManager(store)
    agent = AdvisorAgent(groq=groq, conversation=conversation)

    async def event_generator() -> AsyncIterator[dict]:
        async for token in agent.stream_answer(
            session_id=request.session_id,
            query=request.message,
            portfolio_id=request.portfolio_id,
        ):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": "[DONE]"}

    return EventSourceResponse(event_generator())
