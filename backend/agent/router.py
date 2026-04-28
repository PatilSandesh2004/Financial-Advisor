"""
Router LLM - Fast, small model to extract data requirements from user query.
Uses cheaper/faster model (llama-3.1-8b) to determine what data is needed.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from groq import Groq


ROUTER_PROMPT = """You are a data router for a financial advisor system.
Given a user query, return ONLY a valid JSON object specifying what data is needed.
Do not include any other text or explanation.

Available data sources:
- funds: [MF001, MF002, MF003, MF004, MF005, MF006, MF007, MF008, MF009, MF010, MF011, MF012]
- stocks: [HDFCBANK, ICICIBANK, SBIN, TCS, INFY, RELIANCE, SUNPHARMA]
- sectors: [BANKING, IT, PHARMA, FMCG, ENERGY, METALS, REALTY]
- market: [indices, breadth, fii_dii, volatility]
- news: [all, banking, it, pharma, metals, realty, fmcg]

Available field types for funds:
- basic: name, nav, nav_change_percent, category, risk
- returns: returns_1y, returns_3y, returns_5y
- holdings: top_holdings
- allocations: sector_allocation

Available field types for stocks:
- price, change_percent, sector, market_cap

Respond ONLY with valid JSON like:
{
  "funds": {
    "ids": ["MF001", "MF002"],
    "fields": ["basic", "returns"]
  },
  "stocks": ["HDFCBANK", "INFY"],
  "sectors": ["BANKING", "IT"],
  "market": ["indices", "breadth"],
  "news": ["banking", "it"],
  "reasoning": "User asked about tech fund performance vs banking stocks"
}

If a field is not needed, omit it. Always return valid JSON."""


class DataRouter:
    def __init__(self, api_key: str | None, router_model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.router_model = router_model
        self.client = Groq(api_key=api_key) if api_key else None

    async def route_query(self, query: str) -> dict:
        """
        Call router LLM to determine what data is needed for the query.
        Returns structured routing decision as JSON.
        """
        if not self.client:
            return self._default_routing()

        try:
            response = self.client.chat.completions.create(
                model=self.router_model,
                messages=[
                    {"role": "system", "content": ROUTER_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,  # Deterministic
                max_tokens=500,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            try:
                routing = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON if there's extra text
                import re
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    routing = json.loads(json_match.group())
                else:
                    routing = self._default_routing()
            
            return routing
        except Exception as e:
            print(f"Router error: {e}")
            return self._default_routing()

    def _default_routing(self) -> dict:
        """Fallback routing when API fails or not configured."""
        return {
            "funds": {"ids": [], "fields": []},
            "stocks": [],
            "sectors": [],
            "market": ["indices"],
            "news": ["all"],
            "reasoning": "fallback routing - API not available"
        }
