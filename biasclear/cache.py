"""
Scan Result Cache

In-memory TTL cache for scan results.
Key = SHA-256(text + domain + mode). TTL = 1 hour.

Prevents duplicate Gemini API calls for identical inputs.
Thread-safe via asyncio lock.

Usage:
    from biasclear.cache import scan_cache
    cached = await scan_cache.get(text, domain, mode)
    if cached:
        return cached
    result = await scan(...)
    await scan_cache.put(text, domain, mode, result)
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Optional


class ScanCache:
    """Thread-safe in-memory cache with TTL eviction."""

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 500):
        self._cache: dict[str, tuple[float, dict]] = {}
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(text: str, domain: str, mode: str, extra: str = "") -> str:
        """SHA-256 hash of text+domain+mode+extra (e.g., learning ring version)."""
        raw = f"{text}||{domain}||{mode}||{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(
        self, text: str, domain: str, mode: str, extra: str = "",
    ) -> Optional[dict]:
        """Return cached result if exists and not expired."""
        key = self._make_key(text, domain, mode, extra)
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            ts, result = entry
            if time.monotonic() - ts > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return {**result, "_cached": True}

    async def put(
        self, text: str, domain: str, mode: str, result: dict, extra: str = "",
    ) -> None:
        """Store result in cache. Evicts oldest if over max."""
        key = self._make_key(text, domain, mode, extra)
        async with self._lock:
            # Evict oldest entries if at capacity
            if len(self._cache) >= self._max_entries:
                oldest_key = min(
                    self._cache, key=lambda k: self._cache[k][0],
                )
                del self._cache[oldest_key]

            self._cache[key] = (time.monotonic(), result)

    async def invalidate(
        self, text: str, domain: str, mode: str, extra: str = "",
    ) -> None:
        """Remove a specific entry."""
        key = self._make_key(text, domain, mode, extra)
        async with self._lock:
            self._cache.pop(key, None)

    @property
    def stats(self) -> dict:
        """Cache hit/miss statistics."""
        total = self._hits + self._misses
        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0.0,
        }


# Singleton — shared across the application
scan_cache = ScanCache()
