"""Request and response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceInfo(BaseModel):
    document_name: str
    page_number: int | None = None
    document_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    source: SourceInfo | None = None
    sources: list[SourceInfo] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    uploaded_at: str
    status: str = "processed"
    message: str = "Document processed and indexed successfully."
