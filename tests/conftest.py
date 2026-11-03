"""Point storage at a temp dir before the app reads its settings."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="rag-tests-"))
os.environ["UPLOAD_DIR"] = str(_tmp / "uploads")
os.environ["CHROMA_DIR"] = str(_tmp / "chroma")
os.environ["LOG_FILE"] = str(_tmp / "logs" / "app.log")

# Two dummy users. The backend only ever sees the SHA-256 hashes of their tokens.
import hashlib  # noqa: E402
import json  # noqa: E402

TOKEN_A, TOKEN_B = "test-token-user-a", "test-token-user-b"
AUTH_A = {"Authorization": f"Bearer {TOKEN_A}"}
AUTH_B = {"Authorization": f"Bearer {TOKEN_B}"}
os.environ["AUTH_TOKENS"] = json.dumps({
    hashlib.sha256(TOKEN_A.encode()).hexdigest(): "user-a",
    hashlib.sha256(TOKEN_B.encode()).hexdigest(): "user-b",
})
