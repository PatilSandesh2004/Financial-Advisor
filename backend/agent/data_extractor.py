"""
Data Extractor - Filters raw data based on router decision.
Extracts only requested fields to minimize token usage in reasoner call.
"""

from __future__ import annotations

import json


class DataExtractor:
    """Extracts and filters data based on routing decision."""

    def extract(self, routing: dict, all_data: dict) -> str:
        """
        Filter all_data based on routing decision.
        Returns compact JSON string with only requested data.
        """
        result = {}

        # Extract funds
        if routing.get("funds") and routing["funds"].get("ids"):
            result["funds"] = self._extract_funds(
                fund_ids=routing["funds"]["ids"],
                fields=routing["funds"].get("fields", ["basic"]),
                all_data=all_data,
            )

        # Extract stocks
        if routing.get("stocks"):
            result["stocks"] = self._extract_stocks(
                stock_symbols=routing["stocks"],
                all_data=all_data,
            )

        # Extract sectors
        if routing.get("sectors"):
            result["sectors"] = self._extract_sectors(
                sector_names=routing["sectors"],
                all_data=all_data,
            )

        # Extract market data
        if routing.get("market"):
            result["market"] = self._extract_market(
                market_types=routing["market"],
                all_data=all_data,
            )

        # Extract news
        if routing.get("news"):
            result["news"] = self._extract_news(
                news_types=routing["news"],
                all_data=all_data,
            )

        # Include portfolio if available (from context)
        if "portfolio" in all_data:
            result["portfolio"] = all_data["portfolio"]

        if "market_insights" in all_data:
            result["market_insights"] = all_data["market_insights"]

        if "portfolio_insights" in all_data:
            result["portfolio_insights"] = all_data["portfolio_insights"]

        if "relevant_news" in all_data:
            result["relevant_news"] = all_data["relevant_news"]

        return json.dumps(result, indent=2)

    def _extract_funds(self, fund_ids: list, fields: list, all_data: dict) -> dict:
        """Extract fund data with requested fields."""
        mf_data = all_data.get("mutual_funds", {})
        if "mutual_funds" in mf_data:
            funds = mf_data["mutual_funds"]
        else:
            funds = mf_data
            
        result = {}

        for fund_id in fund_ids:
            if fund_id not in funds:
                continue

            fund = funds[fund_id]
            filtered = {}

            if "basic" in fields:
                filtered.update({
                    "id": fund_id,
                    "scheme_name": fund.get("scheme_name"),
                    "current_nav": fund.get("current_nav"),
                    "nav_change_percent": fund.get("nav_change_percent"),
                    "category": fund.get("category"),
                    "risk_rating": fund.get("risk_rating"),
                })

            if "returns" in fields:
                filtered["returns"] = {
                    "1y": fund.get("returns", {}).get("1y"),
                    "3y": fund.get("returns", {}).get("3y"),
                    "5y": fund.get("returns", {}).get("5y"),
                }

            if "holdings" in fields:
                holdings = fund.get("top_holdings", [])
                filtered["top_holdings"] = holdings[:5]  # Top 5

            if "allocations" in fields:
                filtered["sector_allocation"] = fund.get("sector_allocation", {})

            result[fund_id] = filtered

        return result

    def _extract_stocks(self, stock_symbols: list, all_data: dict) -> dict:
        """Extract stock data."""
        market = all_data.get("market", {})
        stocks = market.get("stocks", {})
        result = {}

        for symbol in stock_symbols:
            if symbol in stocks:
                stock = stocks[symbol]
                result[symbol] = {
                    "name": stock.get("name"),
                    "price": stock.get("current_price"),
                    "change_percent": stock.get("change_percent"),
                    "sector": stock.get("sector"),
                    "market_cap_cr": stock.get("market_cap_cr"),
                    "pe_ratio": stock.get("pe_ratio"),
                }

        return result

    def _extract_sectors(self, sector_names: list, all_data: dict) -> dict:
        """Extract sector performance data."""
        market = all_data.get("market", {})
        sector_performance = market.get("sector_performance", {})
        stocks = market.get("stocks", {})
        result = {}

        for sector in sector_names:
            if sector in sector_performance:
                perf = sector_performance[sector]
                result[sector] = {
                    "change_percent": perf.get("change_percent"),
                    "sentiment": perf.get("sentiment"),
                    "key_drivers": perf.get("key_drivers", [])[:2],
                    "top_gainers": perf.get("top_gainers", [])[:3],
                    "top_losers": perf.get("top_losers", [])[:3],
                }
            else:
                # Find stocks in this sector to calculate average change
                stocks_in_sector = [
                    (sym, data.get("change_percent", 0))
                    for sym, data in stocks.items()
                    if data.get("sector") == sector
                ]
                
                if stocks_in_sector:
                    avg_change = sum(change for _, change in stocks_in_sector) / len(stocks_in_sector)
                    result[sector] = {
                        "avg_change_percent": round(avg_change, 2),
                        "stocks_count": len(stocks_in_sector),
                        "stocks_sample": [sym for sym, _ in stocks_in_sector[:3]]
                    }

        return result

    def _extract_market(self, market_types: list, all_data: dict) -> dict:
        """Extract market indices and breadth."""
        market_data = all_data.get("market", {})
        indices = market_data.get("indices", {})
        historical = all_data.get("historical", {})
        result = {}

        if "indices" in market_types and indices:
            result["indices"] = {
                name: {
                    "value": data.get("current_value"),
                    "change_percent": data.get("change_percent"),
                    "sentiment": data.get("sentiment"),
                }
                for name, data in indices.items()
            }

        if "breadth" in market_types and "breadth" in historical:
            result["breadth"] = historical.get("breadth")

        if "fii_dii" in market_types and "fii_dii" in historical:
            result["fii_dii"] = historical.get("fii_dii")

        return result

    def _extract_news(self, news_types: list, all_data: dict) -> list:
        """Extract relevant news."""
        # Handle both array and object with "news" key
        news_data = all_data.get("news", [])
        if isinstance(news_data, dict) and "news" in news_data:
            all_news = news_data["news"]
        elif isinstance(news_data, list):
            all_news = news_data
        else:
            all_news = []
        
        result = []

        if "all" in news_types:
            # Return all news titles and sentiment
            result = [
                {
                    "headline": news.get("headline") if isinstance(news, dict) else None,
                    "sentiment": news.get("sentiment") if isinstance(news, dict) else None,
                    "scope": news.get("scope") if isinstance(news, dict) else None,
                }
                for news in all_news
                if isinstance(news, dict)
            ][:10]  # Limit to top 10
        else:
            # Filter by scope/category
            result = [
                {
                    "headline": news.get("headline") if isinstance(news, dict) else None,
                    "sentiment": news.get("sentiment") if isinstance(news, dict) else None,
                    "scope": news.get("scope") if isinstance(news, dict) else None,
                }
                for news in all_news
                if isinstance(news, dict) and (
                    news.get("scope") in news_types or 
                    any(sector in news_types for sector in news.get("entities", {}).get("sectors", []))
                )
            ][:10]  # Limit to top 10

        return result
