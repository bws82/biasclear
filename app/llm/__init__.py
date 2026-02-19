"""
LLM Provider — Abstract Interface

All LLM calls go through this interface. Swap providers
by changing BIASCLEAR_LLM_PROVIDER in env.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


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
