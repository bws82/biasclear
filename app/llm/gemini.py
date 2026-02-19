"""
Gemini Provider — Google Gemini API implementation.

Uses the google.genai SDK. Client is lazily initialized —
app loads without an API key and only fails on actual LLM call.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from google import genai
from google.genai import types

from app.llm import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY not set. Get one from "
                    "https://aistudio.google.com/apikey"
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
        max_retries: int = 3,
    ) -> str:
        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )
        if json_mode:
            config.response_mime_type = "application/json"

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await client.aio.models.generate_content(
                    model=self._model,
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

        raise last_error
