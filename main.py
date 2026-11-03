"""Entry point of the application: builds the FastAPI app.

Run with `python main.py` or `uvicorn main:app --reload`.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat, documents, health
from src.core.config import settings
from src.core.redaction import install_log_redaction

install_log_redaction()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="RAG Chatbot backend API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
