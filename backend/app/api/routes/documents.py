"""Document upload endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models.schemas import DocumentInfo, DocumentUploadResponse
from app.processing.extractors.factory import UnsupportedFileTypeError
from app.services.dependencies import get_document_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is larger than {settings.max_upload_mb} MB.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    service = get_document_service()

    try:
        stored = service.process_upload(file.filename, content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error in documents route")
        raise HTTPException(status_code=500, detail="Failed to process document.") from exc

    return DocumentUploadResponse(
        document_id=stored.document_id,
        filename=stored.filename,
        chunk_count=stored.chunk_count,
        uploaded_at=stored.uploaded_at,
    )


@router.get("", response_model=list[DocumentInfo])
def list_documents() -> list[DocumentInfo]:
    return [
        DocumentInfo(
            document_id=doc.document_id,
            filename=doc.filename,
            chunk_count=doc.chunk_count,
            uploaded_at=doc.uploaded_at,
        )
        for doc in get_document_service().list_documents()
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str) -> None:
    if not get_document_service().delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
