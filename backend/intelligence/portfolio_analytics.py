from __future__ import annotations

from collections import defaultdict


class PortfolioAnalytics:
    def compute_day_pnl(self, portfolio: dict) -> dict:
        holdings = portfolio.get("holdings", [])
        if isinstance(holdings, dict):
            holdings = (holdings.get("stocks", []) or []) + (holdings.get("mutual_funds", []) or [])
        if not holdings:
            return {"day_pnl": 0.0, "day_pnl_percent": 0.0}

        # Prefer precomputed fields from mock dataset when present
        meta = portfolio.get("meta", {})
        if "day_pnl_percent" in meta:
            return {
                "day_pnl": float(meta.get("day_pnl", 0.0)),
                "day_pnl_percent": float(meta.get("day_pnl_percent", 0.0)),
            }

        total_value = 0.0
        day_pnl = 0.0
        for h in holdings:
            qty = float(h.get("quantity", 0.0))
            price = float(h.get("current_price", 0.0))
            pct = float(h.get("day_change_percent", 0.0))
            value = qty * price
            total_value += value
            day_pnl += value * (pct / 100.0)

        day_pnl_percent = (day_pnl / total_value * 100.0) if total_value else 0.0
        return {"day_pnl": day_pnl, "day_pnl_percent": day_pnl_percent}

    def sector_allocation(self, portfolio: dict) -> dict[str, float]:
        totals = defaultdict(float)
        holdings = portfolio.get("holdings", [])
        if isinstance(holdings, dict):
            holdings = (holdings.get("stocks", []) or []) + (holdings.get("mutual_funds", []) or [])
        total_weight = 0.0
        for h in holdings:
            w = float(h.get("weight_in_portfolio", 0.0))
            sector = h.get("sector") or "UNKNOWN"
            totals[sector] += w
            total_weight += w
        if total_weight <= 0:
            return dict(totals)
        return {k: (v / total_weight * 100.0) for k, v in totals.items()}

    def concentration_risk(self, sector_alloc: dict[str, float], threshold: float = 40.0) -> str:
        max_sector = max(sector_alloc.values(), default=0.0)
        if max_sector >= 80:
            return "CRITICAL"
        if max_sector >= threshold:
            return "HIGH"
        return "LOW"
