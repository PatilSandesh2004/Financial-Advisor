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
    ) -> AsyncIterator[str]:
        """
        Stream answer using Router → Extractor → Reasoner pattern:
        1. Router: Fast small model determines what data is needed
        2. Extractor: Filter data based on routing decision
        3. Reasoner: Full model gets only relevant data + query
        """
        data = load_all_data()
        portfolio = get_portfolio(portfolio_id) if portfolio_id else None

        # Step 1: Route query to determine data needs
        routing_decision = await self.router.route_query(query)
        print(f"[Router] Routing decision: {routing_decision}")

        # Add portfolio context if available
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

        # Step 2: Extract only requested data (minimal context)
        filtered_data_json = self.extractor.extract(routing_decision, data)
        print(f"[Extractor] Filtered data size: {len(filtered_data_json)} chars")

        # Step 3: Build prompt with filtered data for reasoning
        history = await self.conversation.load(session_id)
        await self.conversation.append(session_id, "user", query)
        
        # Create reasoner prompt with minimal context
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
            yield token
        await self.conversation.append(session_id, "assistant", full)

    async def answer(self, *, session_id: str, query: str, portfolio_id: str | None) -> str:
        """Return the full assistant answer as a single string (non-streaming).

        This reuses the streaming implementation and aggregates tokens.
        """
        full = ""
        async for token in self.stream_answer(
            session_id=session_id, query=query, portfolio_id=portfolio_id
        ):
            full += token
        return full

    def _build_reasoner_prompt(self, query: str, filtered_data: str, history: list) -> dict:
        """Build prompt for reasoner (full model) with minimal context."""
        system_prompt = """You are an expert financial advisor with deep knowledge of Indian markets, stocks, mutual funds, and portfolio analysis.

Your role is to explain portfolio movements and market events through a causal chain:
Market News → Sector Impact → Stock Movement → Portfolio Impact

Rules:
1. Always explain WHY, not just WHAT
2. Use the filtered data provided to support your analysis
3. Reference specific stocks, sectors, and holdings
4. Explain the causal chain clearly
5. If data is missing, acknowledge it
6. Be concise but thorough

Format answers as:
- Key insights first
- Supporting causal chain
- Specific recommendations if applicable"""

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
