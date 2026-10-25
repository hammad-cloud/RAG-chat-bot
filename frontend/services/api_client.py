"""Backend API client for the Streamlit frontend."""

from __future__ import annotations

from typing import Any

import requests

from config.settings import settings


class ApiClient:
    """Thin HTTP client used by Streamlit pages."""

    def __init__(self, base_url: str | None = None, timeout: int = 120) -> None:
        self.base_url = (base_url or settings.backend_api_url).rstrip("/")
        self.timeout = timeout

    def health_check(self) -> dict[str, Any]:
        """Check backend availability."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def upload_document(self, file_name: str, file_bytes: bytes, content_type: str) -> dict[str, Any]:
        """Upload a document to the backend."""
        files = {"file": (file_name, file_bytes, content_type)}
        response = requests.post(
            f"{self.base_url}/documents/upload",
            files=files,
            timeout=self.timeout,
        )
        _raise_for_detail(response)
        return response.json()

    def list_documents(self) -> list[dict[str, Any]]:
        """List documents in the knowledge base, newest first."""
        response = requests.get(f"{self.base_url}/documents", timeout=self.timeout)
        _raise_for_detail(response)
        return response.json()

    def delete_document(self, document_id: str) -> None:
        """Remove a document from the knowledge base."""
        response = requests.delete(
            f"{self.base_url}/documents/{document_id}", timeout=self.timeout
        )
        _raise_for_detail(response)

    def ask_question(self, question: str) -> dict[str, Any]:
        """Send a chat question to the backend RAG endpoint."""
        payload = {"question": question}
        response = requests.post(
            f"{self.base_url}/chat/ask",
            json=payload,
            timeout=self.timeout,
        )
        _raise_for_detail(response)
        return response.json()


def _raise_for_detail(response: requests.Response) -> None:
    """Raise with the backend's error message instead of a bare HTTP status."""
    if response.ok:
        return
    try:
        detail = response.json().get("detail")
    except Exception:
        detail = response.text
    raise RuntimeError(detail or f"Request failed ({response.status_code})")


api_client = ApiClient()
