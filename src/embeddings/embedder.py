"""Embedding model used to turn text chunks and questions into vectors."""

from __future__ import annotations

from functools import lru_cache

from chromadb.api.types import EmbeddingFunction
from chromadb.utils import embedding_functions


@lru_cache
def get_embedding_function() -> EmbeddingFunction:
    """ChromaDB's default local model (all-MiniLM-L6-v2, ONNX). Loaded once per process."""
    return embedding_functions.DefaultEmbeddingFunction()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts; mostly useful for debugging and tests."""
    return [list(map(float, vector)) for vector in get_embedding_function()(texts)]
