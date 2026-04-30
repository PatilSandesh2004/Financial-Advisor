"""
Router LLM - Fast, small model to extract data requirements from user query.
Uses cheaper/faster model (llama-3.1-8b) to determine what data is needed.
"""

from __future__ import annotations

import json
import re
import time

from groq import AsyncGroq
from backend.observability.tracing import capture_exception, track_generation


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
  "funds": {"ids": ["MF001", "MF002"], "fields": ["basic", "returns"]},
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
        self.client = AsyncGroq(api_key=api_key) if api_key else None

    async def route_query(self, query: str, trace=None) -> dict:
        if not self.client:
            return self._default_routing()

        generation = track_generation(
            trace,
            "intent-router",
            raw_user_query=query,
            router_prompt=ROUTER_PROMPT[:2000],
            router_model=self.router_model,
            streamed=False,
        )
        start = time.perf_counter()
        try:
            print(f"[ROUTER] 📡 Calling Groq router model: {self.router_model}")
            print(f"[ROUTER]   User query: {query[:100]}...")
            response = await self.client.chat.completions.create(
                model=self.router_model,
                messages=[
                    {"role": "system", "content": ROUTER_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            content = response.choices[0].message.content.strip()
            print(f"[ROUTER] 📨 Router response received:")
            print(f"[ROUTER]   Raw response: {content[:200]}...")
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as parse_exc:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                else:
                    capture_exception(
                        trace,
                        parse_exc,
                        stage="intent-router",
                        raw_output=content,
                        parse_error=str(parse_exc),
                    )
                    generation.set_metadata(parse_error=str(parse_exc), raw_output=content)
                    raise

            generation.set_metadata(
                raw_output=content,
                parsed_output=parsed,
                predicted_intent=parsed.get("intent"),
                requested_portfolios=parsed.get("portfolios"),
                requested_stocks=parsed.get("stocks"),
                requested_sectors=parsed.get("sectors"),
                requested_market_blocks=parsed.get("market"),
                requested_news_scope=parsed.get("news"),
                router_reasoning=parsed.get("reasoning"),
            )
            
            print(f"\n[ROUTER] 📋 ROUTING DECISION (JSON):")
            print(f"─" * 80)
            print(json.dumps(parsed, indent=2))
            print(f"─" * 80)
            
            print(f"\n[ROUTER] ✅ Routing decision breakdown:")
            print(f"  - Funds: {parsed.get('funds', {}).get('ids', [])} (fields: {parsed.get('funds', {}).get('fields', [])})")
            print(f"  - Stocks: {parsed.get('stocks', [])}")
            print(f"  - Sectors: {parsed.get('sectors', [])}")
            print(f"  - Market: {parsed.get('market', [])}")
            print(f"  - News: {parsed.get('news', [])}")
            print(f"  - Reasoning: {parsed.get('reasoning', 'N/A')}")
            
            return parsed
        except Exception as e:
            capture_exception(trace, e, stage="intent-router")
            generation.set_metadata(error=str(e))
            generation.end(status="failed")
            print(f"Router error: {e}")
            return self._default_routing()
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            generation.set_metadata(latency_ms=duration_ms)
            generation.end()

    def _default_routing(self) -> dict:
        return {
            "funds": {"ids": [], "fields": ["basic", "returns"]},
            "stocks": ["HDFCBANK", "TCS", "INFY", "RELIANCE"],
            "sectors": ["BANKING", "IT", "ENERGY"],
            "market": ["indices", "breadth"],
            "news": ["all"],
        }
