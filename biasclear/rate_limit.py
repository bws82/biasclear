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
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException


# Maximum number of unique keys tracked before LRU eviction
MAX_RATE_LIMIT_KEYS = 5000


@dataclass
class RateWindow:
    """Sliding window counter."""
    timestamps: list[float] = field(default_factory=list)

    def count_within(self, window_seconds: float) -> int:
        """Count requests within the sliding window (non-mutating)."""
        cutoff = time.time() - window_seconds
        return sum(1 for t in self.timestamps if t > cutoff)

    def record(self):
        """Record a new request and trim stale entries."""
        now = time.time()
        self.timestamps.append(now)
        # Trim entries older than max window (1 hour) to bound memory
        if len(self.timestamps) > 100:
            self.timestamps = [t for t in self.timestamps if t > now - 3600]


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

# Stricter limits for unauthenticated (playground) traffic
PLAYGROUND_LIMITS = RateLimits(
    per_minute=int(os.getenv("BIASCLEAR_PLAYGROUND_RATE_PER_MINUTE", "10")),
    per_hour=int(os.getenv("BIASCLEAR_PLAYGROUND_RATE_PER_HOUR", "100")),
)

# LRU-bounded store: key_hash → RateWindow
# OrderedDict tracks access order for eviction
_windows: OrderedDict[str, RateWindow] = OrderedDict()
_lock = threading.Lock()

# Whether rate limiting is active
RATE_LIMIT_ENABLED = os.getenv("BIASCLEAR_RATE_LIMIT", "true").lower() == "true"


def _hash_ip(ip: str) -> str:
    """Hash IP for rate limit key — don't use raw IPs as dict keys."""
    import hashlib
    return f"ip:{hashlib.sha256(ip.encode()).hexdigest()[:16]}"


def check_rate_limit(
    key_id: Optional[str],
    limits: Optional[RateLimits] = None,
    ip: Optional[str] = None,
) -> None:
    """
    Check and enforce rate limits for a given key or IP.

    Args:
        key_id: The key identifier (hash prefix from auth). None = unauthenticated.
        limits: Override default limits.
        ip: Client IP address. Used for rate limiting when key_id is None.

    Raises:
        HTTPException 429 if rate limit exceeded.
    """
    if not RATE_LIMIT_ENABLED:
        return

    # Unauthenticated requests: rate limit by IP with stricter playground limits
    if key_id is None:
        if ip:
            key_id = _hash_ip(ip)
            limits = limits or PLAYGROUND_LIMITS
        else:
            return  # Dev mode — no IP, no limits

    limits = limits or DEFAULT_LIMITS

    with _lock:
        if key_id not in _windows:
            # Evict oldest entry if at capacity
            if len(_windows) >= MAX_RATE_LIMIT_KEYS:
                _windows.popitem(last=False)  # Remove least-recently-used
            _windows[key_id] = RateWindow()
        else:
            # Move to end (most recently used)
            _windows.move_to_end(key_id)

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

