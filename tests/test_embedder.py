from src.embeddings.embedder import embed_texts, get_embedding_function


def test_embedding_function_is_shared():
    assert get_embedding_function() is get_embedding_function()


def test_embed_texts_returns_one_vector_per_text():
    vectors = embed_texts(["refund policy", "office hours"])
    assert len(vectors) == 2
    assert len(vectors[0]) == len(vectors[1]) > 0
