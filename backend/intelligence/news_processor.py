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
        # Normalize holdings: portfolio may store holdings under a dict with
        # keys like 'stocks' and 'mutual_funds'. Support both shapes.
        raw_holdings = portfolio.get("holdings", {}) or {}
        stocks_holdings = []
        mutual_fund_holdings = []
        if isinstance(raw_holdings, dict):
            stocks_holdings = raw_holdings.get("stocks", []) or []
            mutual_fund_holdings = raw_holdings.get("mutual_funds", []) or []
        elif isinstance(raw_holdings, list):
            # older format: flat list of stock dicts
            stocks_holdings = raw_holdings

        # Collect symbols from stock entries and from mutual fund top_holdings
        symbols: set[str] = set()
        sectors: set[str] = set()

        for h in stocks_holdings:
            if isinstance(h, dict):
                sym = h.get("symbol")
                sec = h.get("sector")
                if sym:
                    symbols.add(sym)
                if sec:
                    sectors.add(sec)
            elif isinstance(h, str):
                symbols.add(h)

        for mf in mutual_fund_holdings:
            # mutual fund top holdings may be a list of strings
            if isinstance(mf, dict):
                top = mf.get("top_holdings", []) or []
                for t in top:
                    if isinstance(t, str):
                        symbols.add(t)
            elif isinstance(mf, list):
                for t in mf:
                    if isinstance(t, str):
                        symbols.add(t)

        relevant = []
        for n in news_items:
            # news stocks/sectors may be lists of strings
            news_stocks = set(n.get("stocks", []) or [])
            news_sectors = set(n.get("sectors", []) or [])

            if symbols.intersection(news_stocks):
                relevant.append(n)
                continue
            if sectors.intersection(news_sectors):
                relevant.append(n)
                continue
            if n.get("scope") == "MARKET_WIDE":
                relevant.append(n)
        return relevant
