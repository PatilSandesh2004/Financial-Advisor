from __future__ import annotations

import uuid

import streamlit as st

from frontend.components.chat_window import render_chat
from frontend.components.market_snapshot import render_market_snapshot
from frontend.components.portfolio_panel import render_portfolio_panel
from frontend.utils.api_client import stream_chat, list_portfolios
from frontend.utils.state import init_state


def main() -> None:
    st.set_page_config(page_title="Financial Advisor", layout="wide")
    init_state()

    with st.sidebar:
        st.header("Portfolio")
        portfolios = list_portfolios()
        options = {p["label"]: p["portfolio_id"] for p in portfolios}
        selected_label = st.selectbox("Select", list(options.keys())) if options else None
        st.session_state.portfolio_id = options.get(selected_label) if selected_label else None
        render_portfolio_panel(st.session_state.portfolio_id)
        st.divider()
        render_market_snapshot()

    st.title("Autonomous Financial Advisor")
    render_chat()

    prompt = st.chat_input("Ask about your portfolio...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not st.session_state.session_id:
            st.session_state.session_id = str(uuid.uuid4())

        with st.chat_message("assistant"):
            def token_iter():
                return stream_chat(
                    session_id=st.session_state.session_id,
                    message=prompt,
                    portfolio_id=st.session_state.portfolio_id,
                )

            response_text = st.write_stream(token_iter())
        st.session_state.messages.append({"role": "assistant", "content": response_text})


if __name__ == "__main__":
    main()
