"""Shared utility helpers."""

from __future__ import annotations

from typing import Any


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def is_allowed_file(filename: str) -> bool:
    """Return True when the uploaded filename has an allowed extension."""
    lower_name = filename.lower()
    return any(lower_name.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def format_source(source: dict | None) -> str | None:
    """Format a single source metadata object."""
    if not source:
        return None

    name = source.get("document_name", "Unknown document")
    page = source.get("page_number")
    if page is not None:
        return f"Source: {name} — Page {page}"
    return f"Source: {name}"


def format_sources(response: dict[str, Any]) -> str | None:
    """Format one or many sources from an ask response."""
    sources = response.get("sources") or []
    if sources:
        lines = [format_source(item) for item in sources]
        return "\n".join(line for line in lines if line)

    return format_source(response.get("source"))
