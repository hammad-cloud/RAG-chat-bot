"""Plain text extraction."""

from __future__ import annotations

from app.models.domain import ExtractedDocument
from app.processing.extractors.base import BaseExtractor


class TxtExtractor(BaseExtractor):
    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        text = content.decode("utf-8", errors="ignore").strip()
        pages = [(1, text)] if text else []
        return ExtractedDocument(filename=filename, text=text, pages=pages)
