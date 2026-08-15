"""ChromaDB vector store for document chunks."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import chromadb
from chromadb.utils import embedding_functions

from app.core.config import settings
from app.models.domain import RetrievedChunk, TextChunk


class VectorStoreService:
    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        document_id: str,
        document_name: str,
        chunks: list[TextChunk],
        uploaded_at: str,
    ) -> int:
        if not chunks:
            return 0

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            ids.append(f"{document_id}_{chunk.chunk_index}_{uuid4().hex[:8]}")
            documents.append(chunk.content)
            metadatas.append(
                {
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number if chunk.page_number is not None else -1,
                    "uploaded_at": uploaded_at,
                }
            )

        self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def similarity_search(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        limit = top_k or settings.retrieval_top_k
        if self._collection.count() == 0:
            return []

        result = self._collection.query(
            query_texts=[query],
            n_results=min(limit, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for content, metadata, distance in zip(documents, metadatas, distances):
            # Cosine distance -> similarity score approximation
            score = 1 - float(distance)
            page_number = metadata.get("page_number")
            retrieved.append(
                RetrievedChunk(
                    content=content,
                    document_id=str(metadata.get("document_id", "")),
                    document_name=str(metadata.get("document_name", "Unknown")),
                    page_number=None if page_number in (None, -1) else int(page_number),
                    chunk_index=int(metadata.get("chunk_index", 0)),
                    score=score,
                )
            )
        return retrieved

    def delete_by_document_id(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})
