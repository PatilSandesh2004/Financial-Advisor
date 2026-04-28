from __future__ import annotations

import streamlit as st

from frontend.utils.api_client import get_market_snapshot


def render_market_snapshot() -> None:
    snap = get_market_snapshot()
    if not snap:
        st.caption("Market snapshot unavailable.")
        return
    st.subheader("Market")
    st.write(f"Sentiment: {snap.get('sentiment', 'neutral')}")
