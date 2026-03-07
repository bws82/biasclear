"""
LLM Provider — base interface and factory.

Re-exports from submodules for clean imports.
"""

from biasclear.llm import LLMProvider


def get_provider(provider_name: str = "gemini") -> LLMProvider:
    """Factory — returns the configured LLM provider."""
    if provider_name == "gemini":
        from biasclear.llm.gemini import GeminiProvider
        return GeminiProvider()
    elif provider_name == "bedrock":
        from biasclear.llm.bedrock import BedrockProvider
        return BedrockProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
