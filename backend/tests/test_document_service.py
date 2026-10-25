import pytest

from app.core.config import settings
from app.services.document_service import DocumentService


class FakeStore:
    def __init__(self):
        self.added = []

    def add_chunks(self, document_id, document_name, chunks, uploaded_at):
        self.added.append(document_id)
        return len(chunks)


def uploads():
    return set(settings.upload_dir.iterdir())


def test_valid_upload_is_indexed_and_saved():
    store = FakeStore()
    before = uploads()
    stored = DocumentService(vector_store=store).process_upload("notes.txt", b"hello")
    assert stored.chunk_count == 1
    assert store.added == [stored.document_id]
    assert [p.name for p in uploads() - before] == [f"{stored.document_id}_notes.txt"]


def test_rejected_upload_leaves_no_file():
    store = FakeStore()
    before = uploads()
    with pytest.raises(ValueError):
        DocumentService(vector_store=store).process_upload("empty.txt", b"   ")
    assert uploads() == before
    assert store.added == []


def test_path_in_filename_is_stripped():
    stored = DocumentService(vector_store=FakeStore()).process_upload("../../evil.txt", b"x")
    assert stored.filename == "evil.txt"


@pytest.mark.parametrize("name", ["broken.pdf", "broken.docx"])
def test_corrupt_file_is_a_clear_value_error(name):
    with pytest.raises(ValueError, match="corrupted"):
        DocumentService(vector_store=FakeStore()).process_upload(name, b"not a real file")
