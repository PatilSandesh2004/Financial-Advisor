from __future__ import annotations

import json


SYSTEM_PROMPT = (
    "You are an Autonomous Financial Advisor Chat Agent. "
    "Explain portfolio movements using a causal chain: Macro News → Sector Trend → Stock → Portfolio Impact. "
    "Be concise, specific, and explicit about uncertainty."
)


class PromptBuilder:
    def build(self, *, query: str, context: dict, history: list[dict]) -> list[dict]:
        context_block = json.dumps(context, ensure_ascii=False)[:12000]
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)
        messages.append(
            {
                "role": "user",
                "content": f"CONTEXT:\n{context_block}\n\nUSER_QUERY:\n{query}",
            }
        )
        return messages
