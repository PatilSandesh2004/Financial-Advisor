from __future__ import annotations


class ContextSelector:
    def select(self, *, query: str, portfolio: dict | None, data: dict) -> dict:
        # Simple rules-based relevance filter. Keep only what is likely useful.
        selected = {"market": data.get("market"), "historical": data.get("historical")}
        if portfolio:
            selected["portfolio"] = portfolio
            selected["mutual_funds"] = data.get("mutual_funds")
            selected["sector_mapping"] = data.get("sector_mapping")
            selected["news"] = data.get("news")
        return selected
