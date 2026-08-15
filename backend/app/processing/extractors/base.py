"""Extractor interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.domain import ExtractedDocument


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, filename: str, content: bytes) -> ExtractedDocument:
        raise NotImplementedError
