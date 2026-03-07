"""
LLM Provider — base interface and factory.

Re-exports from submodules for clean imports.
Supports automatic fallback: if the primary provider fails on first call,
the factory can return the other provider as a fallback.
"""

import logging
import os

from biasclear.llm import LLMProvider

logger = logging.getLogger("biasclear.llm.factory")


def get_provider(provider_name: str = "bedrock") -> LLMProvider:
    """Factory — returns the configured LLM provider."""
    if provider_name == "gemini":
        from biasclear.llm.gemini import GeminiProvider
        return GeminiProvider()
    elif provider_name == "bedrock":
        from biasclear.llm.bedrock import BedrockProvider
        return BedrockProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")


def get_provider_with_fallback() -> LLMProvider:
    """Return the configured provider, wrapped with automatic fallback.

    If the primary provider (from BIASCLEAR_LLM_PROVIDER) fails,
    automatically tries the other provider. This prevents outages
    when one provider's credentials are misconfigured.
    """
    primary_name = os.getenv("BIASCLEAR_LLM_PROVIDER", "bedrock")

    # Determine fallback
    if primary_name == "bedrock":
        fallback_name = "gemini"
        # Only set up fallback if Gemini API key exists
        has_fallback = bool(os.getenv("GEMINI_API_KEY", ""))
    else:
        fallback_name = "bedrock"
        # Bedrock uses AWS credential chain — always worth trying
        has_fallback = True

    primary = get_provider(primary_name)

    if not has_fallback:
        return primary

    return _FallbackProvider(primary, primary_name, fallback_name)


class _FallbackProvider(LLMProvider):
    """Wraps a primary provider with automatic fallback to another."""

    def __init__(self, primary: LLMProvider, primary_name: str, fallback_name: str):
        self._primary = primary
        self._primary_name = primary_name
        self._fallback_name = fallback_name
        self._fallback: LLMProvider | None = None
        self._primary_failed = False

    def _get_fallback(self) -> LLMProvider:
        if self._fallback is None:
            self._fallback = get_provider(self._fallback_name)
        return self._fallback

    @property
    def circuit_breaker(self):
        """Expose circuit breaker from the active provider."""
        if self._primary_failed:
            return self._get_fallback().circuit_breaker
        return self._primary.circuit_breaker

    async def generate(
        self,
        prompt: str,
        system_instruction=None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        # If primary already failed once, go straight to fallback
        if self._primary_failed:
            return await self._get_fallback().generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                json_mode=json_mode,
            )

        try:
            return await self._primary.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                json_mode=json_mode,
            )
        except Exception as e:
            error_str = str(e).lower()
            # Credential/config errors → switch to fallback permanently
            is_credential_error = any(k in error_str for k in [
                "unable to locate credentials", "invalid security token",
                "access denied", "not authorized", "forbidden",
                "api_key", "api key", "authentication",
            ])
            if is_credential_error:
                logger.warning(
                    "Primary provider %s failed with credential error: %s. "
                    "Switching to fallback provider %s.",
                    self._primary_name, e, self._fallback_name,
                )
                self._primary_failed = True
                return await self._get_fallback().generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    json_mode=json_mode,
                )

            # Transient error — try fallback once without permanently switching
            logger.warning(
                "Primary provider %s transient error: %s. "
                "Trying fallback %s for this request.",
                self._primary_name, e, self._fallback_name,
            )
            try:
                return await self._get_fallback().generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    json_mode=json_mode,
                )
            except Exception:
                raise e  # re-raise original if fallback also fails
