"""Document upload endpoints."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import DocumentUploadResponse
from app.processing.extractors.factory import UnsupportedFileTypeError
from app.services.dependencies import get_document_service

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    content = await file.read()
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {exc}",
        ) from exc

    return DocumentUploadResponse(
        document_id=stored.document_id,
        filename=stored.filename,
        chunk_count=stored.chunk_count,
        uploaded_at=stored.uploaded_at,
    )
