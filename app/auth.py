"""
Auth Middleware — API Key Validation

Simple API key authentication. Keys are stored as environment
variables for now. Phase 4 (enterprise) replaces this with
multi-tenant key management backed by a database.

Keys are checked via a FastAPI dependency that can be injected
into any route.
"""

from __future__ import annotations

import os
import hashlib
import secrets
from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader

# Header name for API key
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Load valid keys from environment
# Format: comma-separated list of keys
# Example: BIASCLEAR_API_KEYS=key1,key2,key3
_RAW_KEYS = os.getenv("BIASCLEAR_API_KEYS", "")
_VALID_KEY_HASHES: set[str] = set()

# Store hashes, not plaintext — keys should never sit in memory as strings
for key in _RAW_KEYS.split(","):
    key = key.strip()
    if key:
        _VALID_KEY_HASHES.add(hashlib.sha256(key.encode()).hexdigest())

# Dev mode: if no keys configured, auth is disabled
AUTH_ENABLED = len(_VALID_KEY_HASHES) > 0


def _verify_key(api_key: str) -> bool:
    """Verify an API key against stored hashes."""
    if not api_key:
        return False
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return key_hash in _VALID_KEY_HASHES


async def require_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> Optional[str]:
    """
    FastAPI dependency — validates the API key.

    If BIASCLEAR_API_KEYS is not set, auth is disabled (dev mode).
    If set, all requests must include a valid X-API-Key header.

    Returns the key hash (for audit logging) or None in dev mode.
    """
    if not AUTH_ENABLED:
        return None  # Dev mode — no auth required

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
        )

    if not _verify_key(api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

    # Return hash for audit logging (never log the actual key)
    return hashlib.sha256(api_key.encode()).hexdigest()[:12]


def generate_api_key() -> str:
    """Generate a new API key. Utility for key provisioning."""
    return f"bc_{secrets.token_urlsafe(32)}"
