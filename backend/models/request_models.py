from __future__ import annotations

from pydantic import BaseModel, Field


class SafeSettings(BaseModel):
    """User-tunable inference settings. API keys and DB credentials are NEVER accepted here."""
    groq_model: str | None = None
    groq_max_tokens: int | None = Field(default=None, ge=64, le=4096)
    groq_temperature: float | None = Field(default=None, ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=4000)
    portfolio_id: str | None = None
    settings: SafeSettings | None = None
