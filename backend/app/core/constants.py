"""Shared constants for the RAG backend."""

from __future__ import annotations

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

UNKNOWN_ANSWER = (
    "I could not find a relevant answer to this question in the provided documents."
)

SYSTEM_PROMPT = """You are a company document assistant.
Answer ONLY using the provided context from uploaded documents.
If the context does not contain enough information, reply exactly with:
I could not find a relevant answer to this question in the provided documents.
Do not invent facts. Keep answers clear and concise.
When possible, mention the document name and page number naturally.
"""
