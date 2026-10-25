"""Point storage at a temp dir before the app reads its settings."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="rag-tests-"))
os.environ["UPLOAD_DIR"] = str(_tmp / "uploads")
os.environ["CHROMA_DIR"] = str(_tmp / "chroma")
