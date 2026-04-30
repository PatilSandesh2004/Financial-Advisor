from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.config import get_settings
from backend.utils.exceptions import DataError


def _candidate_data_dirs() -> list[Path]:
    settings = get_settings()
    root = Path(__file__).resolve().parents[2]
    candidates = [root / settings.data_dir, root]
    return candidates


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DataError(f"Failed to load JSON: {path}") from exc


@lru_cache
def load_all_data() -> dict:
    files = {
        "market": "market_data.json",
        "news": "news_data.json",
        "portfolios": "portfolios.json",
        "mutual_funds": "mutual_funds.json",
        "historical": "historical_data.json",
        "sector_mapping": "sector_mapping.json",
    }
    for base in _candidate_data_dirs():
        if all((base / name).exists() for name in files.values()):
            return {k: _read_json(base / v) for k, v in files.items()}

    raise DataError(
        "Data files not found. Expected either ./data/*.json or repository root JSON files."
    )


def list_portfolios() -> list[dict]:
    data = load_all_data()["portfolios"]
    portfolios = data.get("portfolios", [])
    if isinstance(portfolios, dict):
        out = []
        for portfolio_id, p in portfolios.items():
            if isinstance(p, dict):
                out.append({"portfolio_id": portfolio_id, **p})
        return out
    if isinstance(portfolios, list):
        return portfolios
    return []


def get_portfolio(portfolio_id: str) -> dict | None:
    data = load_all_data()["portfolios"]
    portfolios = data.get("portfolios", {})
    if isinstance(portfolios, dict):
        p = portfolios.get(portfolio_id)
        return {"portfolio_id": portfolio_id, **p} if isinstance(p, dict) else None

    for p in list_portfolios():
        if isinstance(p, dict) and p.get("portfolio_id") == portfolio_id:
            return p
    return None
