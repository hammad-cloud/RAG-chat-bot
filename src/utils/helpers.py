"""Helpers: detect and redact likely credentials in text that leaves the backend.

Rules are deliberately narrow (known token formats, or `key: value` assignments whose
value looks like a real secret) so ordinary document text is left alone.
"""

from __future__ import annotations

import logging
import logging.handlers
import re
import traceback
from functools import lru_cache

from src.utils.config import settings

# Prefix-anchored token formats that practically never occur in normal prose.
TOKEN_RULES: dict[str, str] = {
    "private_key": (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
    ),
    "aws_access_key": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "google_api_key": r"\bAIza[0-9A-Za-z_\-]{35}",
    "openai_key": r"\bsk-[A-Za-z0-9_\-]{20,}",  # also covers sk-proj-, sk-ant-
    "github_token": r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})",
    "slack_token": r"\bxox[abposr]-[A-Za-z0-9-]{10,}",
    "stripe_key": r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}",
    "jwt": r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}",
    "bearer_token": r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{20,}=*",
    "url_credentials": r"(?<=://)[^\s/:@]+:[^\s/@]+(?=@)",
}

# `password: X`, `DB_PASSWORD=X`, `"api_key": "X"` ... The value must be 8+ chars and
# contain a digit, so prose ("password: must be rotated") and placeholders
# ("api_key: your_api_key_here") are not redacted.
_ASSIGNMENT = re.compile(
    r"(?i)\b([\w-]*(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token)\b"
    r"[\"']?\s*[:=]\s*[\"']?)([^\s\"',;]{8,})"
)
# Settings fields whose string values are real credentials and must never leak verbatim.
_SECRET_FIELD = re.compile(r"api_key|secret|token|password", re.IGNORECASE)


@lru_cache
def _compiled_rules(extra: tuple[str, ...]) -> list[tuple[str, re.Pattern[str]]]:
    rules = [(name, re.compile(pattern)) for name, pattern in TOKEN_RULES.items()]
    rules += [("custom", re.compile(pattern)) for pattern in extra]
    return rules


def _configured_secrets() -> list[str]:
    values = [
        value
        for name, value in settings.model_dump().items()
        if isinstance(value, str) and len(value) >= 8 and _SECRET_FIELD.search(name)
    ]
    return sorted(values, key=len, reverse=True)


def _redact_assignment(match: re.Match[str]) -> str:
    key, value = match.groups()
    if not any(ch.isdigit() for ch in value) or value.startswith("[REDACTED"):
        return match.group(0)
    return f"{key}[REDACTED:credential]"


def redact(text: str) -> str:
    """Return `text` with likely credentials replaced by `[REDACTED:<rule>]`."""
    if not text or not settings.redact_secrets:
        return text
    for value in _configured_secrets():
        text = text.replace(value, "[REDACTED:configured_secret]")
    for name, pattern in _compiled_rules(tuple(settings.secret_patterns)):
        text = pattern.sub(f"[REDACTED:{name}]", text)
    return _ASSIGNMENT.sub(_redact_assignment, text)


def install_log_redaction() -> None:
    """Redact every log record's message and traceback, for all loggers."""
    previous = logging.getLogRecordFactory()
    if getattr(previous, "redacting", False):
        return

    def factory(*args, **kwargs) -> logging.LogRecord:
        record = previous(*args, **kwargs)
        try:
            # Redact msg and args separately: formatters like uvicorn's read record.args.
            if isinstance(record.msg, str):
                record.msg = redact(record.msg)
            if isinstance(record.args, tuple):
                record.args = tuple(
                    a if isinstance(a, (int, float)) else redact(str(a))
                    for a in record.args
                )
            if record.exc_info and record.exc_info[0] is not None:
                # Formatters reuse a pre-set exc_text instead of re-formatting.
                record.exc_text = redact(
                    "".join(traceback.format_exception(*record.exc_info)).rstrip("\n")
                )
        except Exception:  # never let redaction break logging
            pass
        return record

    factory.redacting = True  # type: ignore[attr-defined]
    logging.setLogRecordFactory(factory)


def setup_logging() -> None:
    """Log to the console and to a rotating `settings.log_file` (logs/app.log by default)."""
    install_log_redaction()
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    if any(getattr(h, "rag_app_handler", False) for h in root.handlers):
        return  # already configured (e.g. module re-imported)

    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    file_handler.rag_app_handler = True  # type: ignore[attr-defined]
    root.addHandler(file_handler)
