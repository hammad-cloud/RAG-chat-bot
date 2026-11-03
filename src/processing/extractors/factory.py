"""Factory for selecting the correct document extractor."""

from __future__ import annotations

from pathlib import Path

from src.processing.extractors.base import BaseExtractor
from src.processing.extractors.docx_extractor import DocxExtractor
from src.processing.extractors.pdf_extractor import PdfExtractor
from src.processing.extractors.txt_extractor import TxtExtractor


class UnsupportedFileTypeError(ValueError):
    """Raised when the uploaded file type is not supported."""


def get_extractor(filename: str) -> BaseExtractor:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return PdfExtractor()
    if extension in {".doc", ".docx"}:
        if extension == ".doc":
            raise UnsupportedFileTypeError(
                "Legacy .doc is not supported. Please upload .docx, .pdf, or .txt."
            )
        return DocxExtractor()
    if extension == ".txt":
        return TxtExtractor()

    raise UnsupportedFileTypeError(
        f"Unsupported file type '{extension}'. Allowed: PDF, DOCX, TXT."
    )
