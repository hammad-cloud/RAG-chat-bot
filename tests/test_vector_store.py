from src.models.domain import TextChunk
from src.vectordb.vector_store import VectorStoreService


def chunks(*texts):
    return [TextChunk(content=t, chunk_index=i, page_number=1) for i, t in enumerate(texts)]


def test_list_search_and_delete_documents():
    store = VectorStoreService()
    store.add_chunks("doc-a", "a.txt", chunks("cats purr", "cats nap"), "2026-01-01T00:00:00", owner_id="u1")
    store.add_chunks("doc-b", "b.txt", chunks("rockets launch"), "2026-02-01T00:00:00", owner_id="u1")

    listed = [(d.document_id, d.filename, d.chunk_count) for d in store.list_documents(owner_id="u1")]
    assert listed[:2] == [("doc-b", "b.txt", 1), ("doc-a", "a.txt", 2)]

    assert store.similarity_search("spaceflight", top_k=1, owner_id="u1")[0].document_id == "doc-b"

    assert store.delete_by_document_id("doc-a", owner_id="u1") == 2
    assert store.delete_by_document_id("doc-a", owner_id="u1") == 0
    assert "doc-a" not in [d.document_id for d in store.list_documents(owner_id="u1")]
