"""Shared constants for the RAG backend."""

from __future__ import annotations

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}

UNKNOWN_ANSWER = (
    "Mujhe provided documents mein is question ka relevant answer nahi mila."
)

SYSTEM_PROMPT = """You are a company document assistant.
Answer ONLY using the provided context from uploaded documents.
If the context does not contain enough information, reply exactly with:
Mujhe provided documents mein is question ka relevant answer nahi mila.
Do not invent facts. Keep answers clear and concise.
When possible, mention the document name and page number naturally.
"""
