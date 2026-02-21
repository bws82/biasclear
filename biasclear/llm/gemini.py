"""
Gemini Provider — Google Gemini API implementation.

Uses the google.genai SDK. Client is lazily initialized —
app loads without an API key and only fails on actual LLM call.

Features:
- Model fallback chain: primary model → gemini-2.5-flash on failure
- Circuit breaker: after consecutive failures, return local-only signal for 60s
- Exponential backoff retry on transient errors
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional

from google import genai
from google.genai import types

from biasclear.llm import LLMProvider

logger = logging.getLogger("biasclear.llm.gemini")

FALLBACK_MODEL = "gemini-2.5-flash"

# Circuit breaker settings
_CB_FAILURE_THRESHOLD = 3   # Open after this many consecutive failures
_CB_RECOVERY_TIMEOUT = 60   # Seconds before trying again (half-open)


class CircuitBreaker:
    """Simple circuit breaker: closed → open → half-open → closed.

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


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider with fallback and circuit breaker."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client: Optional[genai.Client] = None
        self.circuit_breaker = CircuitBreaker()

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY not set. Get one from "
                    "https://aistudio.google.com/apikey"
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def _call_model(
        self,
        model: str,
        prompt: str,
        config: types.GenerateContentConfig,
        max_retries: int = 3,
    ) -> str:
        """Call a specific model with retry logic."""
        client = self._get_client()
        last_error = None
        for attempt in range(max_retries):
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                return response.text
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                is_transient = any(k in error_str for k in [
                    "429", "503", "500", "rate", "quota", "timeout",
                    "connection", "unavailable", "overloaded",
                ])
                if is_transient and attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        raise last_error  # type: ignore[misc]

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
        max_retries: int = 3,
    ) -> str:
        # Circuit breaker — fast-fail when LLM is known to be down
        if self.circuit_breaker.is_open:
            raise CircuitOpenError(
                "LLM circuit breaker is open — too many consecutive failures. "
                "Falling back to local-only scanning."
            )

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )
        if json_mode:
            config.response_mime_type = "application/json"

        try:
            # Try primary model
            try:
                result = await self._call_model(
                    self._model, prompt, config, max_retries=2,
                )
                self.circuit_breaker.record_success()
                return result
            except Exception as primary_err:
                # If primary model fails and it's not already the fallback, try fallback
                if self._model != FALLBACK_MODEL:
                    logger.warning(
                        "Primary model %s failed (%s), falling back to %s",
                        self._model, primary_err, FALLBACK_MODEL,
                    )
                    try:
                        result = await self._call_model(
                            FALLBACK_MODEL, prompt, config, max_retries=1,
                        )
                        self.circuit_breaker.record_success()
                        return result
                    except Exception as fallback_err:
                        logger.error(
                            "Fallback model %s also failed: %s",
                            FALLBACK_MODEL, fallback_err,
                        )
                        self.circuit_breaker.record_failure()
                        raise fallback_err from primary_err
                self.circuit_breaker.record_failure()
                raise
        except CircuitOpenError:
            raise
        except Exception:
            # Already recorded failure above
            raise
