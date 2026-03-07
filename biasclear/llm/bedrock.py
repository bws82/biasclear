"""
Bedrock Provider — Amazon Bedrock Converse API implementation.

Uses boto3 bedrock-runtime client. Credentials are loaded via the
standard AWS credential chain (env vars, ~/.aws/credentials, IAM role).

Features:
- Circuit breaker: after consecutive failures, return local-only signal for 60s
- Exponential backoff retry on transient errors
- Async wrapper around synchronous boto3 calls
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from biasclear.llm import CircuitBreaker, CircuitOpenError, LLMProvider

logger = logging.getLogger("biasclear.llm.bedrock")


class BedrockProvider(LLMProvider):
    """Amazon Bedrock LLM provider using the Converse API."""

    def __init__(
        self,
        region: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        )
        self._client = None
        self.circuit_breaker = CircuitBreaker()

    def _get_client(self):
        """Lazy-init the bedrock-runtime client."""
        if self._client is None:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self._region,
                config=Config(
                    read_timeout=30,
                    connect_timeout=10,
                    retries={"max_attempts": 0},  # We handle retries ourselves
                ),
            )
        return self._client

    def _call_converse(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        json_mode: bool,
    ) -> str:
        """Synchronous Bedrock Converse call (run in thread for async)."""
        client = self._get_client()

        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ]

        kwargs = {
            "modelId": self._model_id,
            "messages": messages,
            "inferenceConfig": {
                "temperature": temperature,
                "maxTokens": 4096,
            },
        }

        # System instruction → Converse system parameter
        system_parts = []
        if system_instruction:
            system_parts.append({"text": system_instruction})
        if json_mode:
            system_parts.append(
                {"text": "You must respond with valid JSON only. No markdown fences, no explanation, just the JSON object."}
            )
        if system_parts:
            kwargs["system"] = system_parts

        response = client.converse(**kwargs)

        # Extract text from Converse response shape
        return response["output"]["message"]["content"][0]["text"]

    async def _call_with_retry(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        json_mode: bool,
        max_retries: int = 3,
    ) -> str:
        """Call Bedrock with retry logic for transient errors."""
        last_error = None
        for attempt in range(max_retries):
            try:
                result = await asyncio.to_thread(
                    self._call_converse,
                    prompt,
                    system_instruction,
                    temperature,
                    json_mode,
                )
                return result
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                is_transient = any(k in error_str for k in [
                    "throttling", "429", "503", "500", "rate",
                    "timeout", "connection", "unavailable",
                    "overloaded", "too many requests",
                    "serviceunav", "internalserver",
                ])
                if is_transient and attempt < max_retries - 1:
                    logger.warning(
                        "Bedrock transient error (attempt %d/%d): %s",
                        attempt + 1, max_retries, e,
                    )
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
    ) -> str:
        """Generate a text response from Bedrock."""
        # Circuit breaker — fast-fail when LLM is known to be down
        if self.circuit_breaker.is_open:
            raise CircuitOpenError(
                "LLM circuit breaker is open — too many consecutive failures. "
                "Falling back to local-only scanning."
            )

        try:
            result = await self._call_with_retry(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                json_mode=json_mode,
                max_retries=3,
            )
            self.circuit_breaker.record_success()
            return result
        except CircuitOpenError:
            raise
        except Exception:
            self.circuit_breaker.record_failure()
            raise
