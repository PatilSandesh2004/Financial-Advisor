from __future__ import annotations

import json
import os
from typing import Iterable

import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def list_portfolios() -> list[dict]:
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/v1/portfolios", timeout=10)
        resp.raise_for_status()
        return [
            {"portfolio_id": p["portfolio_id"], "label": f"{p['portfolio_id']} — {p['name']}"}
            for p in resp.json()
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


def generate_title(*, session_id: str, message: str) -> str:
    """Ask the backend to generate a short session title from the first user message."""
    try:
        resp = httpx.post(
            f"{API_BASE_URL}/api/v1/chat/title",
            json={"session_id": session_id, "message": message},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("title", message[:40])
    except Exception:
        return message[:40].strip()


def stream_chat(
    *,
    session_id: str,
    message: str,
    portfolio_id: str | None,
    settings: dict | None = None,
) -> Iterable[dict]:
    """Stream assistant events from the SSE endpoint.

    Yields dicts with a "type" field:
      {"type": "thinking", "step": ..., ...}  — intermediate reasoning steps
      {"type": "token",    "content": str}     — response tokens
      {"type": "error",    "content": str}     — error message

    ``settings`` may contain safe inference overrides: model, temperature, max_tokens.
    API keys are never sent from the frontend.
    """
    payload: dict = {
        "session_id": session_id,
        "message": message,
        "portfolio_id": portfolio_id,
    }
    if settings:
        safe = {
            k: v for k, v in settings.items()
            if k in ("groq_model", "groq_temperature", "groq_max_tokens")
        }
        if safe:
            payload["settings"] = safe

    headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=None) as client:
            with client.stream(
                "POST", f"{API_BASE_URL}/api/v1/chat/stream", json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                current_event = None
                for raw in resp.iter_lines():
                    if not raw:
                        continue
                    line = (
                        raw.decode("utf-8", errors="replace")
                        if isinstance(raw, (bytes, bytearray))
                        else str(raw)
                    )
                    line = line.rstrip("\r\n")
                    if line.startswith("event:"):
                        current_event = line[len("event:"):].strip()
                        continue
                    if line.startswith("data:"):
                        data = line[len("data:"):]
                        if data.strip() == "[DONE]":
                            return
                        if current_event == "thinking":
                            try:
                                yield json.loads(data)
                            except (json.JSONDecodeError, ValueError):
                                pass
                            continue
                        if current_event == "error":
                            yield {"type": "error", "content": f"**Error:** {data.strip()}"}
                            return
                        if current_event == "final":
                            return
                        # token event — server JSON-encodes so \n survives SSE transport
                        try:
                            yield {"type": "token", "content": json.loads(data)}
                        except (json.JSONDecodeError, ValueError):
                            yield {"type": "token", "content": data}
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code == 401:
            yield {
                "type": "error",
                "content": (
                    "**API Key Error (401 Unauthorized)**\n\n"
                    "The Groq API key is invalid or expired.\n\n"
                    "**Fix:** Go to [console.groq.com](https://console.groq.com), "
                    "generate a new key, update `GROQ_API_KEY` in `.env`, then restart the backend."
                ),
            }
        else:
            yield {"type": "error", "content": f"**Backend Error {code}:** {exc}"}
    except Exception as exc:
        yield {"type": "error", "content": f"**Connection Error:** {exc}"}
