"""Application configuration for the Streamlit frontend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass(frozen=True)
class Settings:
    app_title: str = os.getenv("APP_TITLE", "RAG Chatbot")
    app_icon: str = "📄"
    backend_api_url: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    page_layout: str = "wide"


settings = Settings()
