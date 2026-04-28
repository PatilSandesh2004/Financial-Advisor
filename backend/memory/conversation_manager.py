from __future__ import annotations


class ConversationManager:
    def __init__(self, store, max_turns: int = 5):
        self.store = store
        self.max_turns = max_turns

    async def load(self, session_id: str) -> list[dict]:
        return await self.store.get_messages(session_id)

    async def append(self, session_id: str, role: str, content: str) -> list[dict]:
        history = await self.load(session_id)
        history.append({"role": role, "content": content})
        # Keep last N turns (user+assistant pairs => 2N messages)
        history = history[-(self.max_turns * 2) :]
        await self.store.set_messages(session_id, history)
        return history
