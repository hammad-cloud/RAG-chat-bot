from app.models.domain import ExtractedDocument
from app.processing.chunking import chunk_document, clean_text


def test_clean_text_collapses_whitespace_and_nulls():
    assert clean_text("a\x00b  \t c\n\n\n\nd ") == "a b c\n\nd"


def test_short_text_is_one_chunk():
    doc = ExtractedDocument(filename="a.txt", text="hello", pages=[(1, "hello")])
    chunks = chunk_document(doc, chunk_size=100, overlap=10)
    assert [c.content for c in chunks] == ["hello"]
    assert chunks[0].page_number == 1


def test_chunks_overlap_and_cover_text():
    text = "".join(str(i % 10) for i in range(250))
    doc = ExtractedDocument(filename="a.txt", text=text, pages=[(1, text)])
    chunks = chunk_document(doc, chunk_size=100, overlap=20)
    assert [len(c.content) for c in chunks] == [100, 100, 90]
    assert chunks[0].content[-20:] == chunks[1].content[:20]
    assert [c.chunk_index for c in chunks] == [0, 1, 2]


def test_chunk_index_continues_across_pages_and_skips_empty():
    doc = ExtractedDocument(
        filename="a.pdf", text="", pages=[(1, "one"), (2, "   "), (3, "three")]
    )
    chunks = chunk_document(doc, chunk_size=100, overlap=10)
    assert [(c.page_number, c.chunk_index) for c in chunks] == [(1, 0), (3, 1)]


def test_falls_back_to_full_text_without_pages():
    doc = ExtractedDocument(filename="a.txt", text="body")
    chunks = chunk_document(doc, chunk_size=100, overlap=10)
    assert chunks[0].content == "body"
    assert chunks[0].page_number is None
