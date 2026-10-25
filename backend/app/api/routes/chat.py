"""Chat endpoints for RAG Q&A."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import AskRequest, AskResponse
from app.services.dependencies import get_chat_service

logger = logging.getLogger(__name__)
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
        logger.exception("Unexpected error in chat route")
        raise HTTPException(status_code=500, detail="Failed to generate answer.") from exc
