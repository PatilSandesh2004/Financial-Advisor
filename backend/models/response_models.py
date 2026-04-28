from __future__ import annotations

from pydantic import BaseModel


class PortfolioSummary(BaseModel):
    portfolio_id: str
    name: str
    day_pnl_percent: float | None = None
    concentration_risk: str | None = None
