from __future__ import annotations

import os
from typing import Iterable

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def list_portfolios() -> list[dict]:
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/v1/portfolios", timeout=10)
        resp.raise_for_status()
        items = resp.json()
        return [
            {
                "portfolio_id": p["portfolio_id"],
                "label": f"{p['portfolio_id']} — {p['name']}",
            }
            for p in items
        ]
    except Exception:
        return []


def get_portfolio(portfolio_id: str) -> dict | None:
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/v1/portfolios/{portfolio_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def get_market_snapshot() -> dict | None:
    # Minimal snapshot via /health for now
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        if resp.status_code == 200:
            return {"sentiment": "unknown"}
    except Exception:
        return None
    return None


def stream_chat(*, session_id: str, message: str, portfolio_id: str | None) -> Iterable[str]:
    payload = {"session_id": session_id, "message": message, "portfolio_id": portfolio_id}
    # Use the streaming endpoint for SSE
    with httpx.Client(timeout=None) as client:
        with client.stream("POST", f"{API_BASE_URL}/api/v1/chat/stream", json=payload) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                line = line.strip()
                # SSE lines may be 'event: ...' or 'data: ...'
                if line.startswith("data:"):
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        return
                    yield data
                # ignore other SSE metadata lines
