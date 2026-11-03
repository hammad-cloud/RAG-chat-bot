"""Secret detection and redaction.

Every credential below is SYNTHETIC: each contains "FAKE" and is assembled at runtime,
so it is obviously not real and secret scanners don't flag this file.
"""

import logging

import pytest
from conftest import AUTH_A
from fastapi.testclient import TestClient

from main import app
from src.api import routes
from src.retrieval.retriever import ChatService
from src.utils import helpers as redaction
from src.utils.config import settings
from src.utils.helpers import redact
from src.utils.models import RetrievedChunk

FAKE = {
    "google_api_key": "AIza" + "FAKE0TEST0KEY0" + "x" * 21,
    "aws_access_key": "AKIA" + "FAKETEST" + "0" * 8,
    "openai_key": "sk-" + "proj-FAKE-test-key-" + "0" * 20,
    "github_token": "ghp_" + "FAKE" + "0" * 32,
    "slack_token": "xox" + "b-FAKE-0000000000",
    "stripe_key": "sk_" + "live_" + "FAKE" + "0" * 16,
    "jwt": "eyJ" + "FAKEhead00." + "eyJ" + "FAKEbody00." + "FAKEsig000",
    "private_key": "-----BEGIN " + "PRIVATE KEY-----\nFAKEKEYDATA\n-----END PRIVATE KEY-----",
}


@pytest.mark.parametrize("rule", FAKE)
def test_known_token_formats_are_redacted(rule):
    out = redact(f"Use {FAKE[rule]} to connect.")
    assert FAKE[rule] not in out
    assert out == f"Use [REDACTED:{rule}] to connect."


@pytest.mark.parametrize(
    "text",
    [
        "password: FakePass2024",
        "DB_PASSWORD=FakePass2024",
        '{"api_key": "FAKE-1234-abcd"}',
        "Authorization: Bearer FAKEbearer0000000000000",
        "postgres://admin:FakePass2024@db.local/app",
    ],
)
def test_credential_assignments_are_redacted(text):
    out = redact(text)
    assert "FakePass2024" not in out and "FAKE-1234" not in out and "FAKEbearer" not in out
    assert "[REDACTED:" in out


@pytest.mark.parametrize(
    "text",
    [
        "The password policy requires at least 12 characters.",
        "Passwords: must be rotated every 90 days.",
        "api_key: your_api_key_here",
        "Token amount: 5000 SAR. Invoice INV-2024-0001 totals $1,250.00.",
        "The risk-assessment-framework-document-2024 is on page 3.",
        "Create a key at https://aistudio.google.com/apikey",
        "Contact hr@company.com or call +966 50 123 4567.",
    ],
)
def test_normal_text_is_untouched(text):
    assert redact(text) == text


def test_configured_backend_secret_is_redacted(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "FAKE-configured-value-123")
    assert redact("error: key FAKE-configured-value-123 rejected") == (
        "error: key [REDACTED:configured_secret] rejected"
    )


def test_custom_patterns_and_disable_switch(monkeypatch):
    monkeypatch.setattr(settings, "secret_patterns", [r"EMP-\d{6}"])
    assert redact("Badge EMP-123456") == "Badge [REDACTED:custom]"
    monkeypatch.setattr(settings, "redact_secrets", False)
    assert redact("Badge EMP-123456") == "Badge EMP-123456"


class FakeStore:
    def __init__(self, text):
        self.text = text

    def similarity_search(self, query, owner_id):
        return [RetrievedChunk(content=self.text, document_id="d1", document_name="a.pdf",
                               page_number=1, chunk_index=0, score=0.9)]


class EchoLLM:
    def generate_answer(self, question, context):
        self.context = context
        return f"The key is {FAKE['google_api_key']}. Office opens at 9am."


def test_chat_redacts_context_and_answer_but_keeps_facts():
    llm = EchoLLM()
    doc = f"Office opens at 9am. password: FakePass2024 token {FAKE['github_token']}"
    response = ChatService(vector_store=FakeStore(doc), llm_service=llm).ask("When?", owner_id="user-a")
    assert "FakePass2024" not in llm.context and FAKE["github_token"] not in llm.context
    assert "Office opens at 9am." in llm.context
    assert FAKE["google_api_key"] not in response.answer
    assert "Office opens at 9am." in response.answer


def test_error_detail_is_redacted(monkeypatch):
    class Failing:
        def ask(self, question, owner_id):
            raise RuntimeError(f"Gemini request failed: key={FAKE['google_api_key']}")

    monkeypatch.setattr(routes, "get_chat_service", Failing)
    response = TestClient(app, headers=AUTH_A).post("/chat/ask", json={"question": "hi"})
    assert response.status_code == 503
    assert FAKE["google_api_key"] not in response.text


def test_logs_are_redacted(caplog):
    redaction.install_log_redaction()  # idempotent; main.py already installed it
    log = logging.getLogger("test.redaction")
    log.error("using %s on port %d", FAKE["openai_key"], 8000)
    log.error("failed: %s", RuntimeError(FAKE["aws_access_key"]))
    try:
        raise RuntimeError(f"bad token {FAKE['github_token']}")
    except RuntimeError:
        log.exception("failed")
    assert FAKE["openai_key"] not in caplog.text
    assert FAKE["github_token"] not in caplog.text
    assert FAKE["aws_access_key"] not in caplog.text
    assert "port 8000" in caplog.text
    assert "[REDACTED:openai_key]" in caplog.text


def test_logs_are_written_to_log_file_redacted():
    redaction.setup_logging()
    logging.getLogger("rag.test").warning("leaked AKIAABCDEFGHIJKLMNOP in a log line")
    for handler in logging.getLogger().handlers:
        handler.flush()
    text = settings.log_file.read_text(encoding="utf-8")
    assert "[REDACTED:aws_access_key]" in text
    assert "AKIAABCDEFGHIJKLMNOP" not in text
