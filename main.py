"""Entry point of the application: builds the FastAPI app.

Run with `python main.py` or `uvicorn main:app --reload`.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat_router, documents_router, health_router
from src.utils.config import settings
from src.utils.helpers import install_log_redaction

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

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.backend_host, port=settings.backend_port, reload=True)
