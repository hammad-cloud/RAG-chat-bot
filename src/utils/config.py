"""Settings: config.yaml for defaults, .env / environment variables for overrides and secrets."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        yaml_file=str(BASE_DIR / "config.yaml"),
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Priority: environment > .env > config.yaml > defaults below.
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    app_name: str = "RAG Chatbot API"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = ["http://localhost:8501"]

    upload_dir: Path = BASE_DIR / "uploads"
    chroma_dir: Path = BASE_DIR / "data" / "chroma"
    collection_name: str = "company_documents"
    max_upload_mb: int = 20

    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_top_k: int = 4
    min_similarity_score: float = 0.05

    llm_provider: str = "gemini"  # gemini | openai
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Credential redaction for retrieved text, answers, errors and logs.
    redact_secrets: bool = True
    secret_patterns: list[str] = []  # extra regexes, e.g. SECRET_PATTERNS=["EMP-\d{6}"]

    # Access tokens: {"<sha256 hex of token>": "<user_id>"}. Empty rejects every request.
    # Only hashes are stored, so a leaked .env does not leak usable tokens.
    auth_tokens: dict[str, str] = {}

    @field_validator("auth_tokens")
    @classmethod
    def _valid_tokens(cls, tokens: dict[str, str]) -> dict[str, str]:
        for digest, user_id in tokens.items():
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("AUTH_TOKENS keys must be SHA-256 hex digests of tokens.")
            # user_id becomes a directory name, so keep it path-safe.
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", user_id):
                raise ValueError(f"Invalid user id in AUTH_TOKENS: {user_id!r}")
        return tokens

    @field_validator("upload_dir", "chroma_dir")
    @classmethod
    def _resolve_path(cls, path: Path) -> Path:
        # Relative paths (e.g. from config.yaml) are relative to the project root, not the cwd.
        return path if path.is_absolute() else BASE_DIR / path

    @field_validator("secret_patterns")
    @classmethod
    def _valid_patterns(cls, patterns: list[str]) -> list[str]:
        for pattern in patterns:
            re.compile(pattern)  # fail at startup, not mid-request
        return patterns


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
