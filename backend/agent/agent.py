from __future__ import annotations

import time
from collections.abc import AsyncIterator

from backend.agent.context_selector import ContextSelector
from backend.agent.prompt_builder import PromptBuilder
from backend.agent.router import DataRouter
from backend.agent.data_extractor import DataExtractor
from backend.groq_client.client import GroqClient
from backend.intelligence.data_loader import get_portfolio, load_all_data_with_trace
from backend.intelligence.market_intelligence import MarketIntelligence
from backend.intelligence.news_processor import NewsProcessor
from backend.intelligence.portfolio_analytics import PortfolioAnalytics
from backend.memory.conversation_manager import ConversationManager
from backend.observability.tracing import capture_exception, start_span, track_generation


class AdvisorAgent:
    def __init__(
        self,
        *,
        groq: GroqClient,
        conversation: ConversationManager,
        api_key: str | None = None,
        router_model: str = "llama-3.1-8b-instant",
        context_selector: ContextSelector | None = None,
        prompt_builder: PromptBuilder | None = None,
    ):
        self.groq = groq
        self.conversation = conversation
        self.context_selector = context_selector or ContextSelector()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.market = MarketIntelligence()
        self.portfolio = PortfolioAnalytics()
        self.news = NewsProcessor()
        # Router → Extractor → Reasoner pattern
        self.router = DataRouter(api_key=api_key, router_model=router_model)
        self.extractor = DataExtractor()

    async def stream_answer(
        self, *, session_id: str, query: str, portfolio_id: str | None, trace=None
    ) -> AsyncIterator[dict]:
        """
        Stream answer using Router → Extractor → Reasoner pattern.
        Yields dicts with a "type" field:
          {"type": "thinking", "step": ..., ...}  — intermediate reasoning steps shown in UI
          {"type": "token",    "content": str}     — response tokens streamed to the user
        """
        data = load_all_data_with_trace(trace)
        portfolio = get_portfolio(portfolio_id) if portfolio_id else None

        # Step 1: Route — fast model decides what data is needed
        print(f"\n[AGENT STEP 1] 🧭 ROUTING - Fast model analyzing what data is needed...")
        yield {"type": "thinking", "step": "routing", "message": "Analyzing your question…"}
        routing_decision = await self.router.route_query(query, trace=trace)
        print(f"[AGENT STEP 1] ✅ Routing decision made:")
        print(f"    - Stocks needed: {routing_decision.get('stocks', [])}")
        print(f"    - Sectors needed: {routing_decision.get('sectors', [])}")
        print(f"    - News needed: {routing_decision.get('news', [])}")
        print(f"    - Funds needed: {routing_decision.get('funds', {}).get('ids', [])}")
        print(f"    - Reasoning: {routing_decision.get('reasoning', 'N/A')[:100]}...")

        stocks = routing_decision.get("stocks", [])
        sectors = routing_decision.get("sectors", [])
        news = routing_decision.get("news", [])
        funds = (routing_decision.get("funds") or {}).get("ids", [])
        yield {
            "type": "thinking",
            "step": "routed",
            "stocks": stocks,
            "sectors": sectors,
            "news": news,
            "funds": funds,
            "reasoning": routing_decision.get("reasoning", ""),
        }

        # Add portfolio analytics if a portfolio is selected
        if portfolio:
            market_insights = self.market.analyze_indices(data.get("market", {}))
            pnl = self.portfolio.compute_day_pnl(portfolio)
            alloc = self.portfolio.sector_allocation(portfolio)
            risk = self.portfolio.concentration_risk(alloc)
            portfolio_insights = {**pnl, "sector_allocation": alloc, "concentration_risk": risk}
            news_items = self.news.classify(data.get("news", {}))
            relevant_news = self.news.map_to_portfolio(news_items, portfolio)
            data.update({
                "portfolio": portfolio,
                "market_insights": market_insights,
                "portfolio_insights": portfolio_insights,
                "relevant_news": relevant_news,
            })

        # Step 2: Extract — pull only the relevant slices from the dataset
        print(f"\n[AGENT STEP 2] 📊 EXTRACTING - Filtering relevant data from knowledge base...")
        yield {"type": "thinking", "step": "extracting", "message": "Filtering relevant data…"}
        filtered_data_json = self.extractor.extract(routing_decision, data, trace=trace)
        filtered_kb = round(len(filtered_data_json) / 1024, 1)
        print(f"[AGENT STEP 2] ✅ Data extraction complete:")
        print(f"    - Total data size: {len(filtered_data_json)} characters ({filtered_kb} KB)")
        print(f"    - Data preview: {filtered_data_json[:150]}...")
        yield {
            "type": "thinking",
            "step": "extracted",
            "filtered_chars": len(filtered_data_json),
            "filtered_kb": filtered_kb,
        }

        # Step 3: Reason — full model streams the answer using only filtered context
        print(f"\n[AGENT STEP 3] 🧠 REASONING - Full LLM generating answer using filtered context...")
        yield {"type": "thinking", "step": "reasoning", "model": self.groq.model}

        history = await self.conversation.load(session_id, trace=trace)
        print(f"[AGENT STEP 3]   Conversation history loaded: {len(history)} previous messages")
        await self.conversation.append(session_id, "user", query, trace=trace)
        
        print(f"[AGENT STEP 3]   Building reasoning prompt...")
        messages = self._build_reasoner_prompt(
            query=query,
            filtered_data=filtered_data_json,
            history=history,
            trace=trace,
        )
        print(f"[AGENT STEP 3] ✅ Reasoning prompt built with {len(messages)} message turns")

        generation = track_generation(
            trace,
            "reasoning-llm",
            reasoner_model=self.groq.model,
            streamed=True,
            compact_extracted_context_size=len(filtered_data_json),
            user_query=query,
        )
        start = time.perf_counter()
        full = ""
        token_count = 0
        first_token_emitted = False
        try:
            print(f"[AGENT STEP 3] 📤 Sending to Groq {self.groq.model}...")
            stream_iter = await self.groq.stream_chat(messages, trace=trace)
            print(f"[AGENT STEP 3] ✅ Stream opened, tokens incoming...")
            async for token in stream_iter:
                if not first_token_emitted:
                    first_token_emitted = True
                    latency = round((time.perf_counter() - start) * 1000, 2)
                    print(f"[AGENT STEP 3] 🚀 First token received in {latency}ms")
                    generation.set_metadata(first_token_latency_ms=latency)
                full += token
                token_count += 1
                if token_count % 50 == 0:
                    print(f"[AGENT STEP 3]   {token_count} tokens received...")
                generation.add_output(token)
                yield {"type": "token", "content": token}
        except Exception as exc:
            capture_exception(trace, exc, stage="reasoning-llm")
            generation.set_metadata(error=str(exc), token_chunks=token_count)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            generation.set_metadata(
                output_text=full,
                token_chunks=token_count,
                latency_ms=duration_ms,
            )
            generation.end()
            print(f"[AGENT STEP 3] 🏁 COMPLETE - Reasoning finished:")
            print(f"[AGENT STEP 3]   Total tokens: {token_count}")
            print(f"[AGENT STEP 3]   Duration: {duration_ms}ms")
            print(f"[AGENT STEP 3]   Response: {full[:200]}...")
            print("="*80 + "\n")

        await self.conversation.append(session_id, "assistant", full, trace=trace)

    async def answer(self, *, session_id: str, query: str, portfolio_id: str | None, trace=None) -> str:
        """Return the full assistant answer as a single string (non-streaming).

        This reuses the streaming implementation and aggregates tokens.
        """
        print(f"\n[Agent.answer] Starting for session={session_id}, portfolio={portfolio_id}")
        print(f"[Agent.answer] Query: {query[:100]}...")
        
        full = ""
        token_count = 0
        try:
            async for event in self.stream_answer(
                session_id=session_id, query=query, portfolio_id=portfolio_id, trace=trace
            ):
                if event.get("type") == "token":
                    full += event["content"]
                    token_count += 1
                    if token_count % 50 == 0:
                        print(f"[Agent.answer] Received {token_count} tokens so far...")
        except Exception as e:
            print(f"[Agent.answer] ERROR during streaming: {type(e).__name__}: {str(e)}")
            raise
        
        print(f"[Agent.answer] Streaming complete. Total tokens: {token_count}, chars: {len(full)}")

        def _format_advisor_response(text: str) -> str:
            import re

            out = text
            # Collapse runs of 3+ blank lines into 2 (preserve paragraph breaks)
            out = re.sub(r"\n{3,}", "\n\n", out)
            # Remove trailing spaces on each line
            out = re.sub(r" +\n", "\n", out)
            return out.strip()

        formatted = _format_advisor_response(full)
        await self.conversation.append(session_id, "assistant", formatted)
        return formatted

    def _build_reasoner_prompt(self, query: str, filtered_data: str, history: list, trace=None) -> list[dict]:
        history_formatted = [msg for msg in history if msg.get("role") in ["user", "assistant"]]
        return self.prompt_builder.build(
            query=query,
            context={"filtered_data": filtered_data},
            history=history_formatted,
            trace=trace,
        )
