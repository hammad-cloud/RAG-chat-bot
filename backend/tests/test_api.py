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
