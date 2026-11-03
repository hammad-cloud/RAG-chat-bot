"""Retrieve relevant chunks by similarity search, then answer with the LLM."""

from __future__ import annotations

from html import escape

from src.api.schemas import AskResponse, SourceInfo
from src.llm.llm_client import LLMService
from src.prompts.prompt_templates import UNKNOWN_ANSWER, strip_delimiters
from src.utils.config import settings
from src.utils.helpers import redact
from src.utils.models import RetrievedChunk
from src.vectordb.vector_store import VectorStoreService


class ChatService:
    def __init__(
        self,
        vector_store: VectorStoreService | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.vector_store = vector_store or VectorStoreService()
        self.llm_service = llm_service or LLMService()

    def ask(self, question: str, *, owner_id: str) -> AskResponse:
        cleaned_question = question.strip()
        if not cleaned_question:
            return AskResponse(answer=UNKNOWN_ANSWER, source=None, sources=[])

        retrieved = self.vector_store.similarity_search(cleaned_question, owner_id=owner_id)
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
        if not context:
            return AskResponse(answer=UNKNOWN_ANSWER, source=None, sources=[])
        answer = redact(self.llm_service.generate_answer(cleaned_question, context))
        sources = self._to_sources(relevant)

        return AskResponse(
            answer=answer,
            source=sources[0] if sources else None,
            sources=sources,
        )

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        """Wrap each untrusted chunk in its own <document> block."""
        blocks: list[str] = []
        for chunk in chunks:
            # Credentials in documents never reach the LLM.
            content = redact(strip_delimiters(chunk.content or "")).strip()
            if not content:
                continue
            # Filenames are user-controlled too: strip tags, then escape for the attribute.
            name = escape(strip_delimiters(chunk.document_name or "Unknown"), quote=True)
            page = chunk.page_number if chunk.page_number is not None else "n/a"
            blocks.append(
                f'<document index="{len(blocks) + 1}" name="{name}" page="{page}">\n'
                f"{content}\n</document>"
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
