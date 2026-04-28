from __future__ import annotations


class MarketIntelligence:
    def analyze_indices(self, market_data: dict) -> dict:
        indices_data = market_data.get("indices", {})
        
        # Handle both dict and list formats
        if not indices_data:
            return {"sentiment": "neutral", "top_movers": []}
        
        # Convert to list of values if it's a dict
        if isinstance(indices_data, dict):
            indices_list = list(indices_data.values())
        else:
            indices_list = indices_data
        
        if not indices_list:
            return {"sentiment": "neutral", "top_movers": []}
            
        changes = [float(i.get("change_percent", 0.0)) for i in indices_list if isinstance(i, dict)]
        avg = sum(changes) / len(changes) if changes else 0.0
        
        if avg <= -0.5:
            sentiment = "bearish"
        elif avg >= 0.5:
            sentiment = "bullish"
        else:
            sentiment = "neutral"
            
        top = sorted(indices_list, key=lambda x: abs(float(x.get("change_percent", 0.0))), reverse=True)[:3]
        return {"sentiment": sentiment, "top_movers": top}

    def get_sector_trends(self, market_data: dict) -> list[dict]:
        sectors = market_data.get("sectors", [])
        return sorted(sectors, key=lambda s: float(s.get("day_change_percent", 0.0)), reverse=True)
