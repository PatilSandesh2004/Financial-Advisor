from __future__ import annotations

import uuid
import time

import streamlit as st


def _new_session_data(portfolio_id: str | None = None) -> dict:
    return {
        "title": "New Chat",
        "messages": [],
        "portfolio_id": portfolio_id,
        "created_at": time.time(),
    }


def init_state() -> None:
    if "sessions" not in st.session_state:
        st.session_state.sessions: dict[str, dict] = {}
    if "session_order" not in st.session_state:
        st.session_state.session_order: list[str] = []
    if "current_session_id" not in st.session_state:
        create_new_session()
    if "user_settings" not in st.session_state:
        st.session_state.user_settings = {
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.2,
            "max_tokens": 512,
        }


def create_new_session(portfolio_id: str | None = None) -> str:
    session_id = str(uuid.uuid4())
    st.session_state.sessions[session_id] = _new_session_data(portfolio_id)
    st.session_state.session_order.insert(0, session_id)
    st.session_state.current_session_id = session_id
    return session_id


def switch_session(session_id: str) -> None:
    st.session_state.current_session_id = session_id


def get_current_session() -> dict:
    return st.session_state.sessions[st.session_state.current_session_id]


def current_messages() -> list[dict]:
    return get_current_session()["messages"]


def append_message(role: str, content: str) -> None:
    get_current_session()["messages"].append({"role": role, "content": content})


def update_session_title(session_id: str, title: str) -> None:
    if session_id in st.session_state.sessions:
        st.session_state.sessions[session_id]["title"] = title


def delete_session(session_id: str) -> None:
    if session_id in st.session_state.sessions:
        del st.session_state.sessions[session_id]
    if session_id in st.session_state.session_order:
        st.session_state.session_order.remove(session_id)
    if st.session_state.current_session_id == session_id:
        if st.session_state.session_order:
            st.session_state.current_session_id = st.session_state.session_order[0]
        else:
            create_new_session()
