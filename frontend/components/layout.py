"""Shared Streamlit UI helpers."""

from __future__ import annotations

import streamlit as st

from config.settings import settings


def apply_page_config(page_title: str | None = None) -> None:
    """Apply consistent Streamlit page configuration."""
    st.set_page_config(
        page_title=page_title or settings.app_title,
        page_icon=settings.app_icon,
        layout=settings.page_layout,
        initial_sidebar_state="expanded",
    )


def render_sidebar() -> None:
    """Render shared sidebar branding and navigation hints."""
    with st.sidebar:
        st.markdown(f"### {settings.app_title}")
        st.caption("Document-grounded Q&A")
        st.divider()
        st.markdown("**Navigate**")
        st.markdown("- Home")
        st.markdown("- Upload Documents")
        st.markdown("- Chat")
        st.divider()
        st.caption("Answers are based only on uploaded documents.")
