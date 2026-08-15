"""Domain models used inside services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_number: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    filename: str
    text: str
    pages: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class StoredDocument:
    document_id: str
    filename: str
    chunk_count: int
    uploaded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class RetrievedChunk:
    content: str
    document_id: str
    document_name: str
    page_number: int | None
    chunk_index: int
    score: float
