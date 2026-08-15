"""RAG Chatbot — Streamlit entry point."""

from __future__ import annotations

import streamlit as st

from components.layout import apply_page_config, render_sidebar
from config.settings import settings
from services.api_client import api_client


def main() -> None:
    apply_page_config()
    render_sidebar()

    st.title(settings.app_title)
    st.markdown(
        "Ask questions about your company documents. "
        "Answers are generated only from the uploaded knowledge base."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**1. Upload**\n\nAdd PDF, DOC/DOCX, or TXT files.")
    with col2:
        st.info("**2. Process**\n\nDocuments are chunked and indexed.")
    with col3:
        st.info("**3. Chat**\n\nAsk questions and view sources.")

    st.divider()
    st.subheader("System Status")

    try:
        health = api_client.health_check()
        st.success(f"Backend connected — {health.get('status', 'ok')}")
    except Exception:
        st.warning(
            "Backend is not reachable yet. "
            "Start the API server, then refresh this page."
        )

    st.caption("Use the sidebar to open Upload Documents or Chat.")


if __name__ == "__main__":
    main()
