"""Shared service instances."""

from __future__ import annotations

from functools import lru_cache

from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService


@lru_cache
def get_vector_store() -> VectorStoreService:
    return VectorStoreService()


@lru_cache
def get_document_service() -> DocumentService:
    return DocumentService(vector_store=get_vector_store())


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(
        vector_store=get_vector_store(),
        llm_service=LLMService(),
    )
