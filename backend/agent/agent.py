from __future__ import annotations

from collections.abc import AsyncIterator

from backend.agent.context_selector import ContextSelector
from backend.agent.prompt_builder import PromptBuilder
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

    async def stream_answer(
        self, *, session_id: str, query: str, portfolio_id: str | None
    ) -> AsyncIterator[str]:
        data = load_all_data()
        portfolio = get_portfolio(portfolio_id) if portfolio_id else None

        market_insights = self.market.analyze_indices(data.get("market", {}))
        portfolio_insights = None
        relevant_news = None
        if portfolio:
            pnl = self.portfolio.compute_day_pnl(portfolio)
            alloc = self.portfolio.sector_allocation(portfolio)
            risk = self.portfolio.concentration_risk(alloc)
            portfolio_insights = {**pnl, "sector_allocation": alloc, "concentration_risk": risk}

            news_items = self.news.classify(data.get("news", {}))
            relevant_news = self.news.map_to_portfolio(news_items, portfolio)

        selected_context = self.context_selector.select(
            query=query,
            portfolio=portfolio,
            data={
                **data,
                "market_insights": market_insights,
                "portfolio_insights": portfolio_insights,
                "relevant_news": relevant_news,
            },
        )

        history = await self.conversation.load(session_id)
        await self.conversation.append(session_id, "user", query)
        messages = self.prompt_builder.build(query=query, context=selected_context, history=history)

        stream_iter = await self.groq.stream_chat(messages)
        full = ""
        async for token in stream_iter:
            full += token
            yield token
        await self.conversation.append(session_id, "assistant", full)
