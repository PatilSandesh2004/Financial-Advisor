from __future__ import annotations

import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st

from frontend.utils.api_client import generate_title, list_portfolios, stream_chat, get_portfolio
from frontend.utils.state import (
    append_message,
    create_new_session,
    current_messages,
    delete_session,
    get_current_session,
    init_state,
    switch_session,
    update_session_title,
)


# ── Custom CSS ────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* Hide default Streamlit header / footer */
header { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Sidebar: dark background like ChatGPT */
[data-testid="stSidebar"] {
    background-color: #202123 !important;
}
[data-testid="stSidebar"] * { color: #ececec !important; }

/* Sidebar session buttons */
div[data-testid="stSidebar"] .stButton > button {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #ececec !important;
    font-size: 0.85rem;
    text-align: left;
    padding: 8px 12px;
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: background 0.15s;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #2a2b32 !important;
}

/* Active session button */
div[data-testid="stSidebar"] .active-session > button {
    background-color: #343541 !important;
    font-weight: 600;
}

/* New Chat button */
.new-chat-btn > button {
    background-color: #19c37d !important;
    color: #000 !important;
    font-weight: 700;
    border-radius: 8px;
}
.new-chat-btn > button:hover {
    background-color: #16a369 !important;
}

/* Main chat area max width */
.main .block-container {
    max-width: 780px;
    padding-top: 2rem;
    padding-bottom: 6rem;
}

/* User message bubble */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background-color: #343541;
    border-radius: 10px;
    padding: 4px 8px;
}

/* Metric cards in sidebar */
[data-testid="stMetric"] {
    background: #2a2b32;
    border-radius: 8px;
    padding: 6px 10px;
}
</style>
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _truncate(text: str, n: int = 35) -> str:
    return text if len(text) <= n else text[:n] + "…"


def _on_new_chat() -> None:
    create_new_session()
    st.rerun()


def _on_switch(sid: str) -> None:
    switch_session(sid)
    st.rerun()


def _on_delete(sid: str) -> None:
    delete_session(sid)
    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        # New Chat
        st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
        if st.button("＋  New Chat", use_container_width=True):
            _on_new_chat()
        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # Chat history list
        st.markdown("**Chats**", help="Click a chat to switch to it")
        current_sid = st.session_state.current_session_id

        for sid in st.session_state.session_order:
            session = st.session_state.sessions.get(sid, {})
            title = _truncate(session.get("title", "New Chat"))
            is_active = sid == current_sid

            cols = st.columns([0.85, 0.15])
            css_class = "active-session" if is_active else ""
            with cols[0]:
                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(title, key=f"sess_{sid}", use_container_width=True):
                    _on_switch(sid)
                st.markdown("</div>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("🗑", key=f"del_{sid}", help="Delete chat"):
                    _on_delete(sid)

        st.divider()

        # Portfolio selector (per-session)
        portfolios = list_portfolios()
        options = {p["label"]: p["portfolio_id"] for p in portfolios}
        if options:
            current_session = get_current_session()
            current_pid = current_session.get("portfolio_id")
            current_label = next(
                (lbl for lbl, pid in options.items() if pid == current_pid), None
            )
            selected_label = st.selectbox(
                "Portfolio",
                list(options.keys()),
                index=list(options.keys()).index(current_label) if current_label else 0,
                key=f"port_{st.session_state.current_session_id}",
            )
            new_pid = options[selected_label]
            if new_pid != current_pid:
                current_session["portfolio_id"] = new_pid

            # Show P&L metric
            p = get_portfolio(options[selected_label])
            if p:
                meta = p.get("meta", {})
                pnl = meta.get("day_pnl_percent", 0)
                st.metric("Day P&L", f"{pnl:+.2f}%", delta_color="normal")
        else:
            st.caption("Backend not reachable — portfolio list unavailable.")

        st.divider()


# ── Main chat area ────────────────────────────────────────────────────────────

def render_chat_area() -> None:
    session = get_current_session()
    title = session.get("title", "New Chat")

    st.markdown(f"### {title}")

    messages = current_messages()
    if not messages:
        st.markdown(
            """
            <div style="text-align:center; color:#6b6b7b; margin-top:4rem;">
            <h2 style="font-weight:700;">Autonomous Financial Advisor</h2>
            <p>Ask about your portfolio, market risks, sector trends, or specific holdings.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])


# ── Input handling ────────────────────────────────────────────────────────────

def handle_input() -> None:
    prompt = st.chat_input("Ask about your portfolio…")
    if not prompt:
        return

    session = get_current_session()
    session_id = st.session_state.current_session_id
    portfolio_id = session.get("portfolio_id")
    is_first_message = len(session["messages"]) == 0

    # Show user message immediately
    append_message("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant response
    def _chunk_text(chunk: dict | str) -> str:
        if isinstance(chunk, dict):
            chunk_type = chunk.get("type")
            if chunk_type == "token":
                return str(chunk.get("content", ""))
            if chunk_type == "error":
                raise RuntimeError(chunk.get("content", "Unknown error"))
            return str(chunk.get("content", ""))
        return str(chunk)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        status_placeholder = st.empty()
        placeholder.markdown("_Thinking…_")
        accumulated = ""
        try:
            for chunk in stream_chat(
                session_id=session_id,
                message=prompt,
                portfolio_id=portfolio_id,
            ):
                # Handle intermediate 'thinking' events to show resources/steps
                if isinstance(chunk, dict) and chunk.get("type") == "thinking":
                    step = chunk.get("step")
                    parts: list[str] = []
                    if step:
                        parts.append(f"**Step:** {step}")
                    # show available resource hints when present
                    if "stocks" in chunk:
                        parts.append(f"**Stocks:** {chunk.get('stocks')}")
                    if "sectors" in chunk:
                        parts.append(f"**Sectors:** {chunk.get('sectors')}")
                    if "news" in chunk:
                        parts.append(f"**News items:** {chunk.get('news')}")
                    if "funds" in chunk:
                        parts.append(f"**Funds:** {chunk.get('funds')}")
                    if "filtered_kb" in chunk:
                        parts.append(f"**Filtered KB:** {chunk.get('filtered_kb')} KB")
                    if "model" in chunk:
                        parts.append(f"**Model:** {chunk.get('model')}")

                    status_html = "<br>".join(parts) if parts else "_Thinking..._"
                    # update both the small status box and the assistant placeholder so users see it live
                    status_placeholder.markdown(status_html, unsafe_allow_html=True)
                    # show thinking inline in the assistant message while tokens stream
                    thinking_inline = f"<div style=\"color:#6b6b7b; margin-top:0.5rem; font-style:italic;\">{status_html}</div>"
                    placeholder.markdown((accumulated or "") + "\n\n" + thinking_inline + "▌", unsafe_allow_html=True)
                    continue

                content = _chunk_text(chunk)
                if content:
                    accumulated += content
                    placeholder.markdown(accumulated + "▌")
            placeholder.markdown(accumulated)
            status_placeholder.empty()
        except Exception as exc:
            accumulated = f"**Connection Error:** {exc}"
            placeholder.markdown(accumulated)
            status_placeholder.empty()

    append_message("assistant", accumulated)

    # Generate session title from first message
    if is_first_message:
        title = generate_title(session_id=session_id, message=prompt)
        update_session_title(session_id, title)
        st.rerun()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Financial Advisor",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_CSS, unsafe_allow_html=True)
    init_state()
    render_sidebar()
    render_chat_area()
    handle_input()


if __name__ == "__main__":
    main()
