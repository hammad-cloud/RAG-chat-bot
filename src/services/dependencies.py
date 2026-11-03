"""Shared service instances."""

from __future__ import annotations

from functools import lru_cache

from src.ingestion.pipeline import DocumentService
from src.retrieval.retriever import ChatService
from src.services.llm_service import LLMService
from src.vectordb.vector_store import VectorStoreService


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
