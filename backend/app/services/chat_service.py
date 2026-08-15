"""RAG chat orchestration service."""

from __future__ import annotations

from app.core.config import settings
from app.core.constants import UNKNOWN_ANSWER
from app.models.domain import RetrievedChunk
from app.models.schemas import AskResponse, SourceInfo
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStoreService


class ChatService:
    def __init__(
        self,
        vector_store: VectorStoreService | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.vector_store = vector_store or VectorStoreService()
        self.llm_service = llm_service or LLMService()

    def ask(self, question: str) -> AskResponse:
        cleaned_question = question.strip()
        if not cleaned_question:
            return AskResponse(answer=UNKNOWN_ANSWER, source=None, sources=[])

        retrieved = self.vector_store.similarity_search(cleaned_question)
        if not retrieved:
            return AskResponse(answer=UNKNOWN_ANSWER, source=None, sources=[])

        # Keep chunks that clear the threshold; if none do (common for broad
        # questions), still use the best retrieved matches and let the LLM decide.
        relevant = [
            chunk
            for chunk in retrieved
            if chunk.score >= settings.min_similarity_score
        ] or retrieved

        context = self._build_context(relevant)
        answer = self.llm_service.generate_answer(cleaned_question, context)
        sources = self._to_sources(relevant)

        return AskResponse(
            answer=answer,
            source=sources[0] if sources else None,
            sources=sources,
        )

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        blocks: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            page = (
                f"Page {chunk.page_number}"
                if chunk.page_number is not None
                else "Page n/a"
            )
            blocks.append(
                f"[{index}] Document: {chunk.document_name} | {page}\n{chunk.content}"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def _to_sources(chunks: list[RetrievedChunk]) -> list[SourceInfo]:
        unique: list[SourceInfo] = []
        seen: set[tuple[str, int | None]] = set()

        for chunk in chunks:
            key = (chunk.document_name, chunk.page_number)
            if key in seen:
                continue
            seen.add(key)
            unique.append(
                SourceInfo(
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    document_id=chunk.document_id,
                )
            )
        return unique
