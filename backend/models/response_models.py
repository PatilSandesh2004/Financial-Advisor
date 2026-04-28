from __future__ import annotations

from pydantic import BaseModel


class PortfolioSummary(BaseModel):
    portfolio_id: str
    name: str
    day_pnl_percent: float | None = None
    concentration_risk: str | None = None


class HealthResponse(BaseModel):
    status: str
    environment: str | None = None
    version: str = "1.0.0"


class SafeSettingsResponse(BaseModel):
    """Settings response without sensitive API keys."""
    environment: str
    api_base_url: str
    log_level: str
    redis_url: str | None = None
    database_configured: bool = False  # Just indicate if DB is configured, don't expose URL
