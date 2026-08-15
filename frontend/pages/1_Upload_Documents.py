"""Admin page for uploading knowledge-base documents."""

from __future__ import annotations

import streamlit as st

from components.layout import apply_page_config, render_sidebar
from services.api_client import api_client
from utils.helpers import is_allowed_file

apply_page_config(page_title="Upload Documents")
render_sidebar()

st.title("Upload Documents")
st.markdown("Upload PDF, DOC/DOCX, or TXT files to build the knowledge base.")

uploaded_files = st.file_uploader(
    "Select documents",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
    help="Supported formats: PDF, DOCX, TXT",
)

if st.button("Upload & Process", type="primary", disabled=not uploaded_files):
    if not uploaded_files:
        st.warning("Please select at least one file.")
    else:
        progress = st.progress(0)
        status = st.empty()

        for index, uploaded_file in enumerate(uploaded_files, start=1):
            if not is_allowed_file(uploaded_file.name):
                st.error(f"Unsupported file type: {uploaded_file.name}")
                continue

            status.info(f"Uploading `{uploaded_file.name}`...")
            try:
                result = api_client.upload_document(
                    file_name=uploaded_file.name,
                    file_bytes=uploaded_file.getvalue(),
                    content_type=uploaded_file.type or "application/octet-stream",
                )
                st.success(
                    f"Processed `{uploaded_file.name}` "
                    f"(id: {result.get('document_id', 'n/a')}, "
                    f"chunks: {result.get('chunk_count', 'n/a')})"
                )
            except Exception as exc:
                st.error(f"Failed to upload `{uploaded_file.name}`: {exc}")

            progress.progress(index / len(uploaded_files))

        status.empty()
        st.info("Documents are extracted, chunked, embedded, and stored in the knowledge base.")
