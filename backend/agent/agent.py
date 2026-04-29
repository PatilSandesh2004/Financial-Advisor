from __future__ import annotations

from collections.abc import AsyncIterator

from backend.agent.context_selector import ContextSelector
from backend.agent.prompt_builder import PromptBuilder
from backend.agent.router import DataRouter
from backend.agent.data_extractor import DataExtractor
from backend.groq_client.client import GroqClient
from backend.intelligence.data_loader import get_portfolio, load_all_data
from backend.intelligence.market_intelligence import MarketIntelligence
from backend.intelligence.news_processor import NewsProcessor
from backend.intelligence.portfolio_analytics import PortfolioAnalytics
from backend.memory.conversation_manager import ConversationManager


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
        self, *, session_id: str, query: str, portfolio_id: str | None
    ) -> AsyncIterator[dict]:
        """
        Stream answer using Router → Extractor → Reasoner pattern.
        Yields dicts with a "type" field:
          {"type": "thinking", "step": ..., ...}  — intermediate reasoning steps shown in UI
          {"type": "token",    "content": str}     — response tokens streamed to the user
        """
        data = load_all_data()
        portfolio = get_portfolio(portfolio_id) if portfolio_id else None

        # Step 1: Route — fast model decides what data is needed
        yield {"type": "thinking", "step": "routing", "message": "Analyzing your question…"}
        routing_decision = await self.router.route_query(query)
        print(f"[Router] Routing decision: {routing_decision}")

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
        yield {"type": "thinking", "step": "extracting", "message": "Filtering relevant data…"}
        filtered_data_json = self.extractor.extract(routing_decision, data)
        filtered_kb = round(len(filtered_data_json) / 1024, 1)
        print(f"[Extractor] Filtered data size: {len(filtered_data_json)} chars ({filtered_kb} KB)")
        yield {
            "type": "thinking",
            "step": "extracted",
            "filtered_chars": len(filtered_data_json),
            "filtered_kb": filtered_kb,
        }

        # Step 3: Reason — full model streams the answer using only filtered context
        yield {"type": "thinking", "step": "reasoning", "model": self.groq.model}

        history = await self.conversation.load(session_id)
        await self.conversation.append(session_id, "user", query)
        reasoner_prompt = self._build_reasoner_prompt(
            query=query,
            filtered_data=filtered_data_json,
            history=history,
        )
        messages = [
            {"role": "system", "content": reasoner_prompt["system"]},
            *reasoner_prompt["history"],
            {"role": "user", "content": reasoner_prompt["user"]},
        ]

        stream_iter = await self.groq.stream_chat(messages)
        full = ""
        async for token in stream_iter:
            full += token
            yield {"type": "token", "content": token}
        await self.conversation.append(session_id, "assistant", full)

    async def answer(self, *, session_id: str, query: str, portfolio_id: str | None) -> str:
        """Return the full assistant answer as a single string (non-streaming).

        This reuses the streaming implementation and aggregates tokens.
        """
        print(f"\n[Agent.answer] Starting for session={session_id}, portfolio={portfolio_id}")
        print(f"[Agent.answer] Query: {query[:100]}...")
        
        full = ""
        token_count = 0
        try:
            async for event in self.stream_answer(
                session_id=session_id, query=query, portfolio_id=portfolio_id
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

    def _build_reasoner_prompt(self, query: str, filtered_data: str, history: list) -> dict:
        system_prompt = """You are a financial advisor analyzing Indian markets and portfolios.

IMPORTANT FORMATTING RULES:
1. Always use proper Markdown headers: ## for sections, ### for sub-sections.
2. Use bullet points (- item) for lists.
3. Use numbered lists (1. item) for recommendations.
4. Write human-readable stock and fund names — never abbreviated or split names.
   - Write "HDFC Bank" not "HDF CB ANK" or "HDFCBANK"
   - Write "TCS" not "T CS"
   - Write "Infosys" not "INF Y"
   - Write "Information Technology" not "INFORMATION_TECHNOLOGY"
   - Write "Diversified Mutual Fund" not "DIVERSIFIED_MF"
5. Never write sector codes — translate to plain English (e.g., FLEXICAP → Flexi Cap).

Respond strictly in this structure:

## Key Insights
- Insight 1
- Insight 2
- Insight 3

## Causal Chain
**Market News → Sector Impact → Stock → Portfolio**
- Market news: ...
- Sector impact: ...
- Stock impact: ...
- Portfolio impact: ...

## Holdings Mentioned
- Stock/fund name (Sector): brief note

## Recommendations
1. Recommendation 1
2. Recommendation 2
3. Recommendation 3

Be concise, specific, and actionable."""

        history_formatted = []
        for msg in history:
            if msg.get("role") in ["user", "assistant"]:
                history_formatted.append(msg)


        user_prompt = f"""Data Context (filtered for this query):
{filtered_data}

User Question: {query}

Using the provided data, explain the causal chain and provide your analysis."""

        return {
            "system": system_prompt,
            "history": history_formatted,
            "user": user_prompt,
        }
