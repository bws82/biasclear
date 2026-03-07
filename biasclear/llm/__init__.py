"""
LLM Provider — Abstract Interface

All LLM calls go through this interface. Swap providers
by changing BIASCLEAR_LLM_PROVIDER in env.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("biasclear.llm")

# ---------------------------------------------------------------------------
# Circuit breaker — shared across all providers
# ---------------------------------------------------------------------------

_CB_FAILURE_THRESHOLD = 3   # Open after this many consecutive failures
_CB_RECOVERY_TIMEOUT = 60   # Seconds before trying again (half-open)


class CircuitBreaker:
    """Simple circuit breaker: closed -> open -> half-open -> closed.

    When open, generate() raises CircuitOpenError immediately so the
    caller can fall back to local-only scanning instead of waiting
    for the LLM to time out.
    """

    def __init__(
        self,
        failure_threshold: int = _CB_FAILURE_THRESHOLD,
        recovery_timeout: float = _CB_RECOVERY_TIMEOUT,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._last_failure_time: float = 0
        self._state = "closed"  # closed | open | half-open

    @property
    def state(self) -> str:
        if self._state == "open":
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
        return self._state

    def record_success(self) -> None:
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                "Circuit breaker OPEN — %d consecutive LLM failures. "
                "Local-only mode for %ds.",
                self._failures, self.recovery_timeout,
            )

    @property
    def is_open(self) -> bool:
        return self.state == "open"


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open."""


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        """Generate a text response from the LLM."""
        ...

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> dict:
        """Generate and parse a JSON response."""
        import json
        text = await self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            json_mode=True,
        )
        # Strip markdown fences if the LLM wraps JSON in ```json blocks
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON: {e}. Raw response: {text[:300]}"
            ) from e
