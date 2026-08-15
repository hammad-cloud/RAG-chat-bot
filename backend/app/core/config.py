"""Backend configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "RAG Chatbot API"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = ["http://localhost:8501"]

    upload_dir: Path = BASE_DIR / "uploads"
    chroma_dir: Path = BASE_DIR / "data" / "chroma"
    collection_name: str = "company_documents"

    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_top_k: int = 4
    min_similarity_score: float = 0.05

    llm_provider: str = "gemini"  # gemini | openai
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
