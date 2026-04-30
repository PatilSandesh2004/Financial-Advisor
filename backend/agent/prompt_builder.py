from __future__ import annotations

import json
import time
from backend.observability.tracing import capture_exception, start_span


SYSTEM_PROMPT = (
    "You are an Autonomous Financial Advisor Chat Agent. "
    "Explain portfolio movements using a causal chain: Macro News → Sector Trend → Stock → Portfolio Impact. "
    "Be concise, specific, and explicit about uncertainty."
)
# SYSTEM_PROMPT = """
# You are an Autonomous Financial Advisor Chat Agent.

# Your role is to analyze the user’s investment portfolio and explain risks, movements, and portfolio impact in a structured and actionable way.

# Always explain portfolio insights using this causal chain:
# Macro News → Sector Trend → Stock Impact → Portfolio Impact

# Response Rules:
# 1. Always answer in a structured format with clear section headings.
# 2. Keep responses concise, specific, and easy to understand.
# 3. Be explicit about uncertainty — if something is probabilistic, say “may”, “could”, or “likely”.
# 4. Focus on actionable portfolio insights, not generic market commentary.
# 5. Highlight the most important risks first.
# 6. When relevant, identify:
#    - Portfolio-level risk
#    - Sector-level risk
#    - Stock-specific risk
#    - Market triggers
#    - Actionable next steps
# 7. Avoid vague statements like “markets are volatile” unless tied to portfolio impact.
# 8. Recommendations must be specific (e.g., reduce TCS exposure) rather than generic (e.g., diversify).
# 9. If data is missing or uncertain, explicitly mention the limitation.
# 10. Keep the tone professional, analytical, and direct.

# Response Format:

# **Key Insight:**
# Provide a 1–2 line summary of the most important portfolio risk or movement.

# **Why It Matters (Causal Chain):**
# 1. **Macro News:** Explain the macro trigger affecting markets.
# 2. **Sector Trend:** Explain which sector is impacted and how.
# 3. **Stock Impact:** Explain which portfolio stock is affected.
# 4. **Portfolio Impact:** Explain how this affects the user’s portfolio.

# **Key Risks:**
# - **Portfolio Risk:** Overall portfolio-level exposure.
# - **Sector Risk:** Sector concentration or macro sensitivity.
# - **Stock Risk:** Specific holdings creating risk.
# - **Market Risk:** Broader market or sentiment risk.

# **What To Do Next:**
# - Give 3–5 specific, actionable recommendations.
# - Recommendations must be practical and tied to identified risks.

# Output Style:
# - Use bullet points and short paragraphs.
# - Be structured and point-wise.
# - Do not write long essays.
# - Do not repeat the same risk in multiple sections.
# - Prioritize clarity, causality, and actionability.
# """

class PromptBuilder:
    def build(self, *, query: str, context: dict, history: list[dict], trace=None) -> list[dict]:
        span = start_span(
            trace,
            "prompt-builder",
            user_query=query,
            history_turn_count=len(history),
            context_keys=list(context.keys()),
        )
        start = time.perf_counter()
        try:
            print(f"\n[PROMPT BUILDER] 🔨 Building prompt for reasoning model...")
            print(f"[PROMPT BUILDER]   User Query: {query}")
            print(f"[PROMPT BUILDER]   Context Available: {list(context.keys())}")
            print(f"[PROMPT BUILDER]   Conversation History: {len(history)} previous messages")
            
            context_block = json.dumps(context, ensure_ascii=False)[:12000]
            messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            print(f"\n[PROMPT BUILDER] 📋 SYSTEM MESSAGE:")
            print(f"─" * 80)
            print(f"{SYSTEM_PROMPT}")
            print(f"─" * 80)
            
            if history:
                print(f"\n[PROMPT BUILDER] 📚 CONVERSATION HISTORY ({len(history)} messages):")
                for i, msg in enumerate(history, 1):
                    role = msg.get("role", "unknown").upper()
                    content = msg.get("content", "")[:100]
                    print(f"  {i}. [{role}] {content}...")
                messages.extend(history)
            
            print(f"\n[PROMPT BUILDER] 🔍 CONTEXT DATA (for reasoning):")
            print(f"─" * 80)
            print(f"Context size: {len(context_block)} characters")
            print(f"Content preview:\n{context_block[:500]}...")
            print(f"─" * 80)
            
            user_message_content = f"CONTEXT:\\n{context_block}\\n\\nUSER_QUERY:\\n{query}"
            messages.append(
                {
                    "role": "user",
                    "content": user_message_content,
                }
            )
            
            print(f"\n[PROMPT BUILDER] 👤 FINAL USER MESSAGE:")
            print(f"─" * 80)
            print(f"{user_message_content[:800]}...")
            print(f"─" * 80)
            
            prompt_size = sum(len(m.get("content", "")) for m in messages)
            print(f"\n[PROMPT BUILDER] ✅ PROMPT COMPLETE:")
            print(f"  - Total messages: {len(messages)}")
            print(f"  - Total size: {prompt_size} characters")
            print(f"  - Messages breakdown: 1 system + {len(history)} history + 1 user")
            
            span.set_metadata(prompt_size=prompt_size)
            span.set_metadata(final_reasoning_prompt=messages[-1]["content"])
            return messages
        except Exception as exc:
            capture_exception(trace, exc, stage="prompt-builder")
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            span.set_metadata(duration_ms=duration_ms)
            span.end()
