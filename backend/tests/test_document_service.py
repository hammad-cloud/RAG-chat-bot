import pytest

from app.core.config import settings
from app.services.document_service import DocumentService


class FakeStore:
    def __init__(self):
        self.added = []

    def add_chunks(self, document_id, document_name, chunks, uploaded_at, *, owner_id):
        self.added.append(document_id)
        return len(chunks)


def uploads():
    user_dir = settings.upload_dir / "user-a"
    return set(user_dir.iterdir()) if user_dir.exists() else set()


def test_valid_upload_is_indexed_and_saved():
    store = FakeStore()
    before = uploads()
    stored = DocumentService(vector_store=store).process_upload("notes.txt", b"hello", owner_id="user-a")
    assert stored.chunk_count == 1
    assert store.added == [stored.document_id]
    assert [p.name for p in uploads() - before] == [f"{stored.document_id}_notes.txt"]


def test_rejected_upload_leaves_no_file():
    store = FakeStore()
    before = uploads()
    with pytest.raises(ValueError):
        DocumentService(vector_store=store).process_upload("empty.txt", b"   ", owner_id="user-a")
    assert uploads() == before
    assert store.added == []


def test_path_in_filename_is_stripped():
    service = DocumentService(vector_store=FakeStore())
    stored = service.process_upload("../../evil.txt", b"x", owner_id="user-a")
    assert stored.filename == "evil.txt"


@pytest.mark.parametrize("name", ["broken.pdf", "broken.docx"])
def test_corrupt_file_is_a_clear_value_error(name):
    with pytest.raises(ValueError, match="corrupted"):
        DocumentService(vector_store=FakeStore()).process_upload(name, b"not a real file", owner_id="user-a")
