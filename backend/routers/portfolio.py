from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.intelligence.data_loader import get_portfolio, list_portfolios
from backend.intelligence.portfolio_analytics import PortfolioAnalytics
from backend.models.response_models import PortfolioSummary


router = APIRouter(tags=["portfolio"])


@router.get("/portfolios", response_model=list[PortfolioSummary])
async def portfolios() -> list[PortfolioSummary]:
    analytics = PortfolioAnalytics()
    out: list[PortfolioSummary] = []
    for p in list_portfolios():
        pnl = analytics.compute_day_pnl(p)
        alloc = analytics.sector_allocation(p)
        risk = analytics.concentration_risk(alloc)
        out.append(
            PortfolioSummary(
                portfolio_id=p.get("portfolio_id", ""),
                name=p.get("name", ""),
                day_pnl_percent=pnl.get("day_pnl_percent"),
                concentration_risk=risk,
            )
        )
    return out


@router.get("/portfolios/{portfolio_id}")
async def portfolio(portfolio_id: str) -> dict:
    p = get_portfolio(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail={"error": "unknown portfolio_id"})
    return p
