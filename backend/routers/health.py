from __future__ import annotations

from fastapi import APIRouter

from backend.config import get_settings
from backend.models.response_models import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        environment=settings.environment,
    )
