"""
BiasClear Configuration

Central settings loaded from environment variables.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# Render sets RENDER=true automatically
_ON_RENDER = os.getenv("RENDER", "").lower() == "true"
_DEFAULT_AUDIT_PATH = "/data/biasclear_audit.db" if _ON_RENDER else "biasclear_audit.db"


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    # --- Core Versioning ---
    CORE_VERSION: str = "1.1.0"
    API_VERSION: str = "1"

    # --- LLM Provider ---
    LLM_PROVIDER: str = os.getenv("BIASCLEAR_LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- Audit ---
    AUDIT_DB_PATH: str = os.getenv("BIASCLEAR_AUDIT_DB", _DEFAULT_AUDIT_PATH)

    # --- Learning Ring ---
    PATTERN_AUTO_ACTIVATE_THRESHOLD: int = int(
        os.getenv("BIASCLEAR_PATTERN_THRESHOLD", "5")
    )
    PATTERN_FALSE_POSITIVE_LIMIT: float = float(
        os.getenv("BIASCLEAR_FP_LIMIT", "0.15")
    )

    # --- Server ---
    HOST: str = os.getenv("BIASCLEAR_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BIASCLEAR_PORT", "8000"))

    # --- CORS ---
    CORS_ORIGINS: str = os.getenv("BIASCLEAR_CORS_ORIGINS", "*")


settings = Settings()

