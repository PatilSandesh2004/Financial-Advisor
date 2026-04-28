from __future__ import annotations

import streamlit as st

from frontend.utils.api_client import get_portfolio


def render_portfolio_panel(portfolio_id: str | None) -> None:
    if not portfolio_id:
        st.caption("Select a portfolio to begin.")
        return
    p = get_portfolio(portfolio_id)
    if not p:
        st.caption("Portfolio not found.")
        return
    st.write(p.get("name", portfolio_id))
    meta = p.get("meta", {})
    if meta:
        st.metric("Day P&L %", f"{meta.get('day_pnl_percent', 0):.2f}%")
