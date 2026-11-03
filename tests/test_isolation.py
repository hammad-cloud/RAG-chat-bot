"""Cross-user document isolation, through the real API, vector store and upload folder.

User A and User B each upload a PDF with a unique fact. The LLM is replaced by one that
returns its whole context, so any chunk retrieved for the asker is visible in the answer.
"""

from __future__ import annotations

from uuid import uuid4

import fitz
import pytest
from conftest import AUTH_A, AUTH_B
from fastapi.testclient import TestClient

from main import app
from scripts.assign_owner import assign_unowned
from src.api.routes import chat
from src.core.config import settings
from src.retrieval.retriever import ChatService
from src.services.dependencies import get_vector_store

FACT_A = "Project Falcon's launch code word is MANGO."
FACT_B = "Project Heron's approved budget is 9,999 dinars."
client = TestClient(app)


def make_pdf(text: str) -> bytes:
    with fitz.open() as pdf:
        pdf.new_page().insert_text((50, 72), text, fontsize=11)
        return pdf.tobytes()


class ContextLLM:
    def generate_answer(self, question, context):
        return context


@pytest.fixture(autouse=True)
def leaky_llm(monkeypatch):
    monkeypatch.setattr(
        chat, "get_chat_service", lambda: ChatService(get_vector_store(), ContextLLM())
    )


@pytest.fixture
def docs():
    """User A uploads PDF A, User B uploads PDF B; both removed afterwards."""

    def upload(name, text, auth):
        response = client.post(
            "/documents/upload",
            files={"file": (name, make_pdf(text), "application/pdf")},
            headers=auth,
        )
        assert response.status_code == 200, response.text
        return response.json()["document_id"]

    doc_a = upload("pdf_a.pdf", FACT_A, AUTH_A)
    doc_b = upload("pdf_b.pdf", FACT_B, AUTH_B)
    yield doc_a, doc_b
    client.delete(f"/documents/{doc_a}", headers=AUTH_A)
    client.delete(f"/documents/{doc_b}", headers=AUTH_B)


def ask(question, auth, **extra):
    response = client.post("/chat/ask", json={"question": question, **extra}, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


def listed(auth):
    return {d["document_id"] for d in client.get("/documents", headers=auth).json()}


def test_user_a_cannot_retrieve_pdf_b(docs):
    doc_a, doc_b = docs
    answer = ask("What is Project Heron's budget?", AUTH_A)
    assert "Heron" not in answer["answer"] and "9,999" not in answer["answer"]
    assert {s["document_id"] for s in answer["sources"]} <= {doc_a} | listed(AUTH_A)
    assert doc_b not in {s["document_id"] for s in answer["sources"]}


def test_user_b_cannot_retrieve_pdf_a(docs):
    doc_a, _ = docs
    answer = ask("What is Project Falcon's launch code word?", AUTH_B)
    assert "MANGO" not in answer["answer"] and "Falcon" not in answer["answer"]
    assert doc_a not in {s["document_id"] for s in answer["sources"]}


def test_each_user_still_gets_their_own_answers(docs):
    doc_a, doc_b = docs
    answer_a = ask("What is Project Falcon's launch code word?", AUTH_A)
    answer_b = ask("What is Project Heron's budget?", AUTH_B)
    assert "MANGO" in answer_a["answer"] and doc_a in {s["document_id"] for s in answer_a["sources"]}
    assert "9,999" in answer_b["answer"] and doc_b in {s["document_id"] for s in answer_b["sources"]}


def test_users_only_list_their_own_documents(docs):
    doc_a, doc_b = docs
    assert doc_a in listed(AUTH_A) and doc_b not in listed(AUTH_A)
    assert doc_b in listed(AUTH_B) and doc_a not in listed(AUTH_B)


def test_user_a_cannot_delete_pdf_b(docs):
    _, doc_b = docs
    assert client.delete(f"/documents/{doc_b}", headers=AUTH_A).status_code == 404
    assert doc_b in listed(AUTH_B)
    assert list((settings.upload_dir / "user-b").glob(f"{doc_b}_*"))  # file untouched


def test_user_b_cannot_access_pdf_a_by_id(docs):
    doc_a, _ = docs
    # Delete is the only id-addressed endpoint; another user's id looks exactly like a missing one.
    assert client.delete(f"/documents/{doc_a}", headers=AUTH_B).status_code == 404
    assert client.delete(f"/documents/{uuid4()}", headers=AUTH_B).status_code == 404
    assert doc_a in listed(AUTH_A)


@pytest.mark.parametrize("bad_id", ["*", "..", "not-a-uuid"])
def test_wildcard_or_malformed_ids_are_rejected(docs, bad_id):
    doc_a, _ = docs
    assert client.delete(f"/documents/{bad_id}", headers=AUTH_A).status_code in {404, 422}
    assert list((settings.upload_dir / "user-a").glob(f"{doc_a}_*"))


def test_files_are_stored_in_the_owners_folder(docs):
    doc_a, doc_b = docs
    assert list((settings.upload_dir / "user-a").glob(f"{doc_a}_pdf_a.pdf"))
    assert list((settings.upload_dir / "user-b").glob(f"{doc_b}_pdf_b.pdf"))
    assert not list((settings.upload_dir / "user-a").glob(f"{doc_b}_*"))


def test_client_supplied_user_id_is_ignored(docs):
    doc_a, doc_b = docs
    # A claims to be user-b in the body: still scoped to A.
    answer = ask("What is Project Heron's budget?", AUTH_A, user_id="user-b", owner_id="user-b")
    assert "9,999" not in answer["answer"]
    # A tries to upload "as" B via form fields and query string: A still owns it.
    response = client.post(
        "/documents/upload?owner_id=user-b&user_id=user-b",
        files={"file": ("spoof.txt", b"spoofed upload")},
        data={"owner_id": "user-b", "user_id": "user-b"},
        headers=AUTH_A,
    )
    spoof_id = response.json()["document_id"]
    assert spoof_id in listed(AUTH_A) and spoof_id not in listed(AUTH_B)
    client.delete(f"/documents/{spoof_id}", headers=AUTH_A)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong-token"},
        {"Authorization": "Bearer "},
        {"Authorization": "Basic dXNlci1hOnRlc3Q="},
        {"Authorization": AUTH_A["Authorization"].replace("Bearer ", "")},
    ],
    ids=["missing", "invalid", "empty", "wrong-scheme", "no-scheme"],
)
def test_missing_or_invalid_auth_is_rejected(docs, headers):
    doc_a, _ = docs
    requests = [
        client.get("/documents", headers=headers),
        client.post("/chat/ask", json={"question": "Falcon?"}, headers=headers),
        client.post("/documents/upload", files={"file": ("x.txt", b"x")}, headers=headers),
        client.delete(f"/documents/{doc_a}", headers=headers),
    ]
    assert [r.status_code for r in requests] == [401] * 4
    assert all("MANGO" not in r.text for r in requests)
    assert doc_a in listed(AUTH_A)


def test_no_configured_tokens_rejects_everyone(monkeypatch):
    monkeypatch.setattr(settings, "auth_tokens", {})
    assert client.get("/documents", headers=AUTH_A).status_code == 401


def test_health_needs_no_auth():
    assert client.get("/health").status_code == 200


def test_legacy_documents_are_hidden_until_migrated():
    store = get_vector_store()
    legacy_id = str(uuid4())
    store._collection.add(
        ids=[f"{legacy_id}_0"],
        documents=["Legacy memo: the Osprey office opens at 7am."],
        metadatas=[{"document_id": legacy_id, "document_name": "old.txt", "chunk_index": 0,
                    "page_number": -1, "uploaded_at": "2025-01-01T00:00:00"}],
    )
    legacy_file = settings.upload_dir / f"{legacy_id}_old.txt"
    legacy_file.write_bytes(b"Legacy memo")
    try:
        # Pre-isolation data is visible to nobody, but nothing is deleted.
        assert legacy_id not in listed(AUTH_A) | listed(AUTH_B)
        assert "Osprey" not in ask("When does the Osprey office open?", AUTH_A)["answer"]

        dry = assign_unowned(store, "user-a")
        assert sum(dry.values()) == 1 and legacy_id not in listed(AUTH_A)
        assert legacy_file.exists()

        assign_unowned(store, "user-a", apply=True)
        assert legacy_id in listed(AUTH_A) and legacy_id not in listed(AUTH_B)
        assert "Osprey" in ask("When does the Osprey office open?", AUTH_A)["answer"]
        assert not legacy_file.exists()
        assert (settings.upload_dir / "user-a" / legacy_file.name).read_bytes() == b"Legacy memo"
    finally:
        client.delete(f"/documents/{legacy_id}", headers=AUTH_A)
        store._collection.delete(where={"document_id": legacy_id})
        legacy_file.unlink(missing_ok=True)
