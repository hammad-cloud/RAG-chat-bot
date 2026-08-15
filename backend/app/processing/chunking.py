"""Text cleaning and chunking utilities."""

from __future__ import annotations

import re

from app.core.config import settings
from app.models.domain import ExtractedDocument, TextChunk


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_document(
    document: ExtractedDocument,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[TextChunk]:
    """Split extracted pages into overlapping text chunks."""
    size = chunk_size or settings.chunk_size
    overlap_size = overlap or settings.chunk_overlap
    chunks: list[TextChunk] = []
    chunk_index = 0

    source_pages = document.pages or [(None, document.text)]

    for page_number, page_text in source_pages:
        text = clean_text(page_text)
        if not text:
            continue

        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    TextChunk(
                        content=piece,
                        chunk_index=chunk_index,
                        page_number=page_number,
                        metadata={"filename": document.filename},
                    )
                )
                chunk_index += 1

            if end >= len(text):
                break
            start = max(0, end - overlap_size)

    return chunks
