from __future__ import annotations


class MarketIntelligence:
    def analyze_indices(self, market_data: dict) -> dict:
        indices = market_data.get("indices", [])
        if not indices:
            return {"sentiment": "neutral", "top_movers": []}
        changes = [float(i.get("change_percent", 0.0)) for i in indices]
        avg = sum(changes) / len(changes)
        if avg <= -0.5:
            sentiment = "bearish"
        elif avg >= 0.5:
            sentiment = "bullish"
        else:
            sentiment = "neutral"
        top = sorted(indices, key=lambda x: abs(float(x.get("change_percent", 0.0))), reverse=True)[:3]
        return {"sentiment": sentiment, "top_movers": top}

    def get_sector_trends(self, market_data: dict) -> list[dict]:
        sectors = market_data.get("sectors", [])
        return sorted(sectors, key=lambda s: float(s.get("day_change_percent", 0.0)), reverse=True)
