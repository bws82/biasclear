"""
Playground Session Tokens — Anti-Abuse Gate

HMAC-SHA256 signed, short-lived tokens for anonymous playground access.
No database needed — tokens are stateless and self-validating.

Token lifecycle:
  1. Frontend calls GET /playground/token → receives a signed token
  2. Frontend attaches X-Playground-Token to each /scan request
  3. Server validates signature, expiry, IP binding, and use count
  4. After 50 uses or 1 hour, token expires → frontend requests a new one

Token format (base64-encoded JSON):
  {iat: timestamp, exp: timestamp, ip: hashed_ip, nonce: random}
  + HMAC-SHA256 signature appended
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from typing import Optional


# Server-side secret — auto-generated if not set in env
_PLAYGROUND_SECRET = os.getenv(
    "BIASCLEAR_PLAYGROUND_SECRET",
    secrets.token_hex(32),  # Random per-process if not configured
)

# Token limits
TOKEN_TTL_SECONDS = 3600       # 1 hour
TOKEN_MAX_USES = 50            # Max scans per token
TOKEN_ISSUE_RATE_PER_MIN = 5   # Max token requests per IP per minute

# In-memory use counter: token_id → uses_remaining
# Bounded LRU — evicts oldest entries to prevent memory exhaustion
_MAX_TOKEN_ENTRIES = 10000
_token_uses: dict[str, int] = {}
_token_issue_log: dict[str, list[float]] = {}
_lock = threading.Lock()


def _hash_ip(ip: str) -> str:
    """Hash IP for binding — don't store raw IPs in tokens."""
    return hashlib.sha256(
        f"{ip}:{_PLAYGROUND_SECRET[:16]}".encode()
    ).hexdigest()[:16]


def _sign(payload: str) -> str:
    """HMAC-SHA256 sign a payload."""
    return hmac.new(
        _PLAYGROUND_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def _check_issue_rate(ip: str) -> bool:
    """Check if IP has exceeded token issuance rate limit."""
    ip_hash = _hash_ip(ip)
    now = time.time()
    cutoff = now - 60

    with _lock:
        timestamps = _token_issue_log.get(ip_hash, [])
        timestamps = [t for t in timestamps if t > cutoff]
        _token_issue_log[ip_hash] = timestamps

        if len(timestamps) >= TOKEN_ISSUE_RATE_PER_MIN:
            return False

        timestamps.append(now)

        # LRU eviction on issue log
        if len(_token_issue_log) > _MAX_TOKEN_ENTRIES:
            oldest_key = next(iter(_token_issue_log))
            del _token_issue_log[oldest_key]

        return True


def create_playground_token(ip: str) -> Optional[str]:
    """
    Issue a signed playground token for the given IP.

    Returns None if the IP has exceeded the issuance rate limit.
    """
    if not _check_issue_rate(ip):
        return None

    now = time.time()
    nonce = secrets.token_hex(8)
    ip_hash = _hash_ip(ip)

    payload = json.dumps({
        "iat": int(now),
        "exp": int(now + TOKEN_TTL_SECONDS),
        "ip": ip_hash,
        "nonce": nonce,
    }, separators=(",", ":"))

    signature = _sign(payload)
    token_id = hashlib.sha256(f"{nonce}{now}".encode()).hexdigest()[:16]

    # Register use counter
    with _lock:
        if len(_token_uses) >= _MAX_TOKEN_ENTRIES:
            # Evict oldest
            oldest_key = next(iter(_token_uses))
            del _token_uses[oldest_key]
        _token_uses[token_id] = TOKEN_MAX_USES

    # Token = base64(payload) + "." + signature + "." + token_id
    encoded_payload = base64.urlsafe_b64encode(payload.encode()).decode()
    return f"{encoded_payload}.{signature}.{token_id}"


def validate_playground_token(token: str, ip: str) -> tuple[bool, str]:
    """
    Validate a playground token.

    Returns (valid, reason) tuple.
    """
    if not token:
        return False, "missing_token"

    parts = token.split(".")
    if len(parts) != 3:
        return False, "malformed"

    encoded_payload, signature, token_id = parts

    # Decode payload
    try:
        payload_bytes = base64.urlsafe_b64decode(encoded_payload)
        payload_str = payload_bytes.decode()
        payload = json.loads(payload_str)
    except Exception:
        return False, "decode_error"

    # Verify signature
    expected_sig = _sign(payload_str)
    if not hmac.compare_digest(signature, expected_sig):
        return False, "invalid_signature"

    # Check expiry
    now = time.time()
    if now > payload.get("exp", 0):
        return False, "expired"

    # Check IP binding
    ip_hash = _hash_ip(ip)
    if payload.get("ip") != ip_hash:
        return False, "ip_mismatch"

    # Check remaining uses
    with _lock:
        remaining = _token_uses.get(token_id)
        if remaining is None:
            return False, "unknown_token"
        if remaining <= 0:
            return False, "exhausted"
        _token_uses[token_id] = remaining - 1

    return True, "ok"


def cleanup_expired_tokens() -> int:
    """Remove expired token use counters. Call periodically."""
    removed = 0
    with _lock:
        # Tokens without remaining uses
        expired = [k for k, v in _token_uses.items() if v <= 0]
        for k in expired:
            del _token_uses[k]
            removed += 1
    return removed
