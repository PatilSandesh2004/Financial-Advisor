from __future__ import annotations

import streamlit as st


def init_state() -> None:
    st.session_state.setdefault("session_id", "")
    st.session_state.setdefault("portfolio_id", None)
    st.session_state.setdefault("messages", [])
