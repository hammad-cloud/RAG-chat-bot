# RAG Chatbot

Ask questions in plain language about your own documents. Upload PDF, DOCX or TXT files, and the chatbot answers using only what those documents say, with the source document and page for every answer.

Built with **FastAPI**, **ChromaDB**, **Streamlit** and **Google Gemini** (or **OpenAI**).

## How it works

```
Upload ──► Extract text ──► Clean + chunk ──► Embed ──► ChromaDB
                (PDF/DOCX/TXT)   (900 chars, 150 overlap)

Question ──► Similarity search (top 4) ──► Context + question ──► LLM ──► Answer + sources
```

1. **Ingest:** each uploaded file is read by a type-specific extractor (PyMuPDF for PDF, python-docx for DOCX), cleaned and split into overlapping chunks. Chunks are embedded and stored in a persistent ChromaDB collection with their document name and page number.
2. **Retrieve:** a question is matched against the stored chunks by cosine similarity.
3. **Generate:** the best chunks are sent to the LLM with a system prompt that restricts it to the given context (temperature 0.1).
4. **Fallback:** when no documents match, or the context does not hold the answer, the chatbot replies with a fixed "I could not find a relevant answer…" message (set in `core/constants.py`) instead of guessing.

## Features

- Upload PDF, DOCX and TXT documents
- Grounded answers with source document and page number
- Switch between Gemini and OpenAI with one setting
- Automatic fallback through newer Gemini Flash models if the configured one is unavailable
- Clear error messages for missing or invalid API keys
- Retrieval settings (chunk size, overlap, top-k, similarity threshold) configurable from `.env`

## Tech stack

| Layer | Tools |
|-------|-------|
| API | FastAPI, Uvicorn, Pydantic, pydantic-settings |
| Retrieval | ChromaDB (persistent, cosine), default embedding function |
| Document parsing | PyMuPDF, python-docx |
| LLM | Google Gemini (`google-genai`) or OpenAI |
| Frontend | Streamlit (multi-page) |

## Project structure

```
RAG-chat-bot/
├── backend/                     # FastAPI service
│   ├── app/
│   │   ├── main.py              # App entry point, CORS, routers
│   │   ├── api/routes/
│   │   │   ├── chat.py          # POST /chat/ask
│   │   │   ├── documents.py     # POST /documents/upload
│   │   │   └── health.py        # GET /health
│   │   ├── core/
│   │   │   ├── config.py        # Settings loaded from .env
│   │   │   └── constants.py     # System prompt, fallback answer
│   │   ├── models/
│   │   │   ├── domain.py        # Internal data classes (chunks, documents)
│   │   │   └── schemas.py       # Request/response models
│   │   ├── processing/
│   │   │   ├── chunking.py      # Text cleaning + overlapping chunks
│   │   │   └── extractors/      # PDF, DOCX, TXT extractors + factory
│   │   └── services/
│   │       ├── chat_service.py      # Retrieve → build context → answer
│   │       ├── document_service.py  # Upload → extract → chunk → store
│   │       ├── llm_service.py       # Gemini / OpenAI calls
│   │       ├── vector_store.py      # ChromaDB wrapper
│   │       └── dependencies.py      # Shared service instances
│   ├── data/                    # ChromaDB storage (created at runtime)
│   ├── uploads/                 # Uploaded files
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # Streamlit app
│   ├── Home.py                  # Landing page
│   ├── pages/
│   │   ├── 1_Upload_Documents.py
│   │   └── 2_Chat.py
│   ├── components/layout.py     # Shared page layout
│   ├── services/api_client.py   # Calls the FastAPI backend
│   ├── config/settings.py       # Frontend settings from .env
│   ├── utils/helpers.py
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Getting started

Requires Python 3.10+ and a [Gemini API key](https://aistudio.google.com/apikey) (or an OpenAI key).

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

Open `backend/.env` and set `GEMINI_API_KEY` (or set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`). Then start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend (second terminal)

```bash
cd frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run Home.py
```

Open http://localhost:8501, upload a document on **Upload Documents**, then ask questions on **Chat**.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service status |
| POST | `/documents/upload` | Upload a PDF, DOCX or TXT file (multipart `file`) |
| POST | `/chat/ask` | `{"question": "..."}` → answer and sources |

## Configuration

All settings live in `backend/.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | `gemini` | `gemini` or `openai` |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | — | Key for the chosen provider |
| `GEMINI_MODEL` / `OPENAI_MODEL` | `gemini-3.5-flash` / `gpt-4o-mini` | Model name |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `900` / `150` | Chunk length and overlap (characters) |
| `RETRIEVAL_TOP_K` | `4` | Chunks sent to the LLM |
| `MIN_SIMILARITY_SCORE` | `0.05` | Minimum similarity for a chunk to count as relevant |

Never commit your `.env` files.

## Author

Muhammad Hammad · [GitHub](https://github.com/hammad-cloud)
