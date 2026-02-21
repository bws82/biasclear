"""
Structured Logging — JSON Output for Production

Configures Python logging to emit structured JSON logs.
Each log entry includes timestamp, level, module, and
any additional context fields.

Usage:
    from biasclear.logging import get_logger
    logger = get_logger("detector")
    logger.info("Scan complete", extra={"truth_score": 72, "domain": "legal"})
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone


LOG_LEVEL = os.getenv("BIASCLEAR_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("BIASCLEAR_LOG_FORMAT", "json")  # "json" or "text"


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields
        for key in ("truth_score", "domain", "scan_mode", "flags_count",
                     "audit_hash", "key_id", "pattern_id", "error",
                     "duration_ms", "status_code", "method", "path",
                     "email", "error_type"):
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val

        # Include exception info
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable format for development."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging():
    """Configure root logger. Call once at app startup."""
    root = logging.getLogger("biasclear")
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return root


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the biasclear namespace."""
    return logging.getLogger(f"biasclear.{name}")
