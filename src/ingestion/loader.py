"""Load text from uploaded files: PDF (PyMuPDF), DOCX (python-docx) and TXT."""

from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import fitz
from docx import Document

from src.utils.models import ExtractedDocument

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}


class UnsupportedFileTypeError(ValueError):
    """Raised when the uploaded file type is not supported."""


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        raise NotImplementedError


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


class DocxExtractor(BaseExtractor):
    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        document = Document(BytesIO(content))
        paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        pages = [(1, text)] if text else []
        return ExtractedDocument(filename=filename, text=text, pages=pages)


class TxtExtractor(BaseExtractor):
    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        text = content.decode("utf-8", errors="ignore").strip()
        pages = [(1, text)] if text else []
        return ExtractedDocument(filename=filename, text=text, pages=pages)


def get_extractor(filename: str) -> BaseExtractor:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return PdfExtractor()
    if extension == ".doc":
        raise UnsupportedFileTypeError(
            "Legacy .doc is not supported. Please upload .docx, .pdf, or .txt."
        )
    if extension == ".docx":
        return DocxExtractor()
    if extension == ".txt":
        return TxtExtractor()

    raise UnsupportedFileTypeError(
        f"Unsupported file type '{extension}'. Allowed: PDF, DOCX, TXT."
    )
