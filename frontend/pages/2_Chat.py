"""Chat page for asking questions against the knowledge base."""

from __future__ import annotations

import streamlit as st

from components.layout import apply_page_config, render_sidebar
from services.api_client import api_client
from utils.helpers import format_sources

apply_page_config(page_title="Chat")
render_sidebar()

st.title("Chat")
st.markdown("Ask questions in natural language. Answers include source references when available.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("source"):
            st.caption(message["source"])

prompt = st.chat_input("Ask a question about your documents...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            try:
                response = api_client.ask_question(prompt)
                answer = response.get(
                    "answer",
                    "Mujhe provided documents mein is question ka relevant answer nahi mila.",
                )
                source_text = format_sources(response)
            except Exception as exc:
                answer = (
                    "Chat service is unavailable right now. "
                    "Please ensure the backend is running and your API key is set."
                )
                source_text = f"Error: {exc}"

        st.markdown(answer)
        if source_text:
            st.caption(source_text)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "source": source_text,
        }
    )
