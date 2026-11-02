"""Chat endpoints for RAG Q&A."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.core.redaction import redact
from app.models.schemas import AskRequest, AskResponse
from app.services.dependencies import get_chat_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, user_id: str = Depends(get_current_user)) -> AskResponse:
    service = get_chat_service()
    try:
        return service.ask(payload.question, owner_id=user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=redact(str(exc))) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=redact(str(exc))) from exc
    except Exception as exc:
        logger.exception("Unexpected error in chat route")
        raise HTTPException(status_code=500, detail="Failed to generate answer.") from exc
