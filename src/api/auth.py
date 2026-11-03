"""Bearer-token authentication. The user ID always comes from the verified token,
never from anything the client sends in the request body, query or path."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.utils.config import settings

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Return the user ID for a valid `Authorization: Bearer <token>`, else 401."""
    if credentials is not None:
        digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        # Compare against every entry so timing doesn't reveal how far a guess matched.
        user_id = None
        for known_digest, owner in settings.auth_tokens.items():
            if hmac.compare_digest(digest, known_digest):
                user_id = owner
        if user_id is not None:
            return user_id
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing access token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
