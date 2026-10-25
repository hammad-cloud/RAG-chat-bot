from fastapi.testclient import TestClient

from app.api.routes import chat, documents
from app.main import app

client = TestClient(app)


class Boom:
    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise KeyError("secret internal detail")
        return fail


def test_chat_500_hides_internal_error(monkeypatch):
    monkeypatch.setattr(chat, "get_chat_service", Boom)
    response = client.post("/chat/ask", json={"question": "hi"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to generate answer."}


def test_upload_500_hides_internal_error(monkeypatch):
    monkeypatch.setattr(documents, "get_document_service", Boom)
    response = client.post("/documents/upload", files={"file": ("a.txt", b"hi")})
    assert response.status_code == 500
    assert "secret" not in response.text


class FakeLLM:
    def generate_answer(self, question, context):
        return f"answer from: {context.splitlines()[0]}"


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_upload_list_ask_delete_flow(monkeypatch):
    from app.services.chat_service import ChatService
    from app.services.dependencies import get_vector_store

    monkeypatch.setattr(
        chat,
        "get_chat_service",
        lambda: ChatService(vector_store=get_vector_store(), llm_service=FakeLLM()),
    )

    uploaded = client.post(
        "/documents/upload", files={"file": ("handbook.txt", b"Office opens at 9am.")}
    )
    assert uploaded.status_code == 200
    doc_id = uploaded.json()["document_id"]

    listed = client.get("/documents").json()
    assert {"document_id": doc_id, "filename": "handbook.txt", "chunk_count": 1}.items() <= listed[0].items()

    answer = client.post("/chat/ask", json={"question": "When does the office open?"}).json()
    assert answer["answer"].startswith("answer from: [1] Document: handbook.txt")
    assert answer["source"]["document_id"] == doc_id

    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.delete(f"/documents/{doc_id}").status_code == 404


def test_upload_rejections(monkeypatch):
    assert client.post("/documents/upload", files={"file": ("a.exe", b"x")}).status_code == 400
    assert client.post("/documents/upload", files={"file": ("a.txt", b"")}).status_code == 400

    monkeypatch.setattr(documents.settings, "max_upload_mb", 0)
    assert client.post("/documents/upload", files={"file": ("a.txt", b"x")}).status_code == 413


def test_ask_validates_question():
    assert client.post("/chat/ask", json={"question": ""}).status_code == 422
    assert client.post("/chat/ask", json={}).status_code == 422
