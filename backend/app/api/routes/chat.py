"""Chat endpoints for RAG Q&A."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.dependencies import get_chat_service

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    service = get_chat_service()
    try:
        return service.ask(payload.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {exc}",
        ) from exc
