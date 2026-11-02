"""Document upload endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.redaction import redact
from app.models.schemas import DocumentInfo, DocumentUploadResponse
from app.processing.extractors.factory import UnsupportedFileTypeError
from app.services.dependencies import get_document_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...), user_id: str = Depends(get_current_user)
) -> DocumentUploadResponse:
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
        stored = service.process_upload(file.filename, content, owner_id=user_id)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=redact(str(exc))) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=redact(str(exc))) from exc
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
def list_documents(user_id: str = Depends(get_current_user)) -> list[DocumentInfo]:
    return [
        DocumentInfo(
            document_id=doc.document_id,
            filename=doc.filename,
            chunk_count=doc.chunk_count,
            uploaded_at=doc.uploaded_at,
        )
        for doc in get_document_service().list_documents(owner_id=user_id)
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID, user_id: str = Depends(get_current_user)) -> None:
    # UUID-only ids block glob/wildcard tricks; someone else's id looks the same as a missing one.
    if not get_document_service().delete_document(str(document_id), owner_id=user_id):
        raise HTTPException(status_code=404, detail="Document not found.")
