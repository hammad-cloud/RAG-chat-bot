"""PDF text extraction using PyMuPDF."""

from __future__ import annotations

import fitz

from app.models.domain import ExtractedDocument
from app.processing.extractors.base import BaseExtractor


class PdfExtractor(BaseExtractor):
    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        pages: list[tuple[int, str]] = []
        with fitz.open(stream=content, filetype="pdf") as document:
            for index, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages.append((index, text))

        combined = "\n\n".join(text for _, text in pages).strip()
        return ExtractedDocument(filename=filename, text=combined, pages=pages)
