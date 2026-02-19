"""
Rate Limiter — Per-Key Request Throttling

Simple sliding window rate limiter backed by an in-memory dict.
Phase 4 (enterprise) replaces this with Redis-backed limiting.

Limits are configurable per-tier:
  - Free tier: 20 requests/minute, 200/hour
  - Standard:  60 requests/minute, 1000/hour
  - No limit:  disabled (dev mode when auth is off)
"""

from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException


@dataclass
class RateWindow:
    """Sliding window counter."""
    timestamps: list[float] = field(default_factory=list)

    def count_within(self, window_seconds: float) -> int:
        """Count requests within the sliding window."""
        cutoff = time.time() - window_seconds
        self.timestamps = [t for t in self.timestamps if t > cutoff]
        return len(self.timestamps)

    def record(self):
        """Record a new request."""
        self.timestamps.append(time.time())


@dataclass
class RateLimits:
    """Rate limit configuration."""
    per_minute: int = 60
    per_hour: int = 1000


# Default limits — override via env
DEFAULT_LIMITS = RateLimits(
    per_minute=int(os.getenv("BIASCLEAR_RATE_PER_MINUTE", "60")),
    per_hour=int(os.getenv("BIASCLEAR_RATE_PER_HOUR", "1000")),
)

# In-memory store: key_hash → RateWindow
_windows: dict[str, RateWindow] = {}
_lock = threading.Lock()

# Whether rate limiting is active
RATE_LIMIT_ENABLED = os.getenv("BIASCLEAR_RATE_LIMIT", "true").lower() == "true"


def check_rate_limit(
    key_id: Optional[str],
    limits: Optional[RateLimits] = None,
) -> None:
    """
    Check and enforce rate limits for a given key.

    Args:
        key_id: The key identifier (hash prefix from auth). None = no limit.
        limits: Override default limits.

    Raises:
        HTTPException 429 if rate limit exceeded.
    """
    if not RATE_LIMIT_ENABLED:
        return
    if key_id is None:
        return  # Dev mode — no limits

    limits = limits or DEFAULT_LIMITS

    with _lock:
        if key_id not in _windows:
            _windows[key_id] = RateWindow()

        window = _windows[key_id]

        # Check per-minute
        minute_count = window.count_within(60)
        if minute_count >= limits.per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limits.per_minute} requests/minute. "
                       f"Retry after {60 - int(time.time() % 60)} seconds.",
                headers={"Retry-After": str(60 - int(time.time() % 60))},
            )

        # Check per-hour
        hour_count = window.count_within(3600)
        if hour_count >= limits.per_hour:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limits.per_hour} requests/hour.",
                headers={"Retry-After": "3600"},
            )

        # Record the request
        window.record()


def get_usage(key_id: str) -> dict:
    """Get current usage stats for a key."""
    with _lock:
        window = _windows.get(key_id)
        if not window:
            return {"minute": 0, "hour": 0}
        return {
            "minute": window.count_within(60),
            "hour": window.count_within(3600),
        }


def cleanup_stale_windows(max_age: float = 7200):
    """Remove windows with no recent activity. Call periodically."""
    cutoff = time.time() - max_age
    with _lock:
        stale = [
            k for k, w in _windows.items()
            if not w.timestamps or w.timestamps[-1] < cutoff
        ]
        for k in stale:
            del _windows[k]
