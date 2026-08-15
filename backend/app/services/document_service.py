"""Document upload and indexing pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.constants import ALLOWED_EXTENSIONS
from app.models.domain import StoredDocument
from app.processing.chunking import chunk_document
from app.processing.extractors.factory import UnsupportedFileTypeError, get_extractor
from app.services.vector_store import VectorStoreService


class DocumentService:
    def __init__(self, vector_store: VectorStoreService | None = None) -> None:
        self.vector_store = vector_store or VectorStoreService()

    def process_upload(self, filename: str, content: bytes) -> StoredDocument:
        safe_name = Path(filename).name
        extension = Path(safe_name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{extension}'. Allowed: PDF, DOCX, TXT."
            )

        document_id = str(uuid4())
        uploaded_at = datetime.now(timezone.utc).isoformat()

        saved_path = settings.upload_dir / f"{document_id}_{safe_name}"
        saved_path.write_bytes(content)

        extractor = get_extractor(safe_name)
        extracted = extractor.extract(safe_name, content)
        if not extracted.text.strip():
            raise ValueError("No readable text found in the uploaded document.")

        chunks = chunk_document(extracted)
        if not chunks:
            raise ValueError("Document could not be split into searchable chunks.")

        chunk_count = self.vector_store.add_chunks(
            document_id=document_id,
            document_name=safe_name,
            chunks=chunks,
            uploaded_at=uploaded_at,
        )

        return StoredDocument(
            document_id=document_id,
            filename=safe_name,
            chunk_count=chunk_count,
            uploaded_at=uploaded_at,
        )
