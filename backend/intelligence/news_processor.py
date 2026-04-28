from __future__ import annotations


class NewsProcessor:
    def classify(self, news_data: dict) -> list[dict]:
        # Mock dataset is pre-tagged; just return it normalized.
        items = news_data.get("news", [])
        normalized = []
        for n in items:
            entities = n.get("entities", {}) or {}
            normalized.append(
                {
                    "id": n.get("id"),
                    "headline": n.get("headline"),
                    "sentiment": n.get("sentiment"),
                    "impact_level": n.get("impact_level"),
                    "scope": n.get("scope"),
                    "sectors": entities.get("sectors", []) or [],
                    "stocks": entities.get("stocks", []) or [],
                    "indices": entities.get("indices", []) or [],
                }
            )
        return normalized

    def map_to_portfolio(self, news_items: list[dict], portfolio: dict) -> list[dict]:
        holdings = portfolio.get("holdings", [])
        symbols = {h.get("symbol") for h in holdings if h.get("symbol")}
        sectors = {h.get("sector") for h in holdings if h.get("sector")}
        relevant = []
        for n in news_items:
            if symbols.intersection(set(n.get("stocks", []))):
                relevant.append(n)
                continue
            if sectors.intersection(set(n.get("sectors", []))):
                relevant.append(n)
                continue
            if n.get("scope") == "MARKET_WIDE":
                relevant.append(n)
        return relevant
