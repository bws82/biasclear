"""
Beta Signup Store

Stores raw beta-signup emails in a dedicated SQLite table so the audit chain
can stay privacy-safer. The audit log records only masked/hash metadata.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from datetime import datetime, timezone

from biasclear.config import settings


def mask_email(email: str) -> str:
    """Mask an email address for logs and audit entries."""
    local, _, domain = email.partition("@")
    if not local or not domain:
        return "***"
    if len(local) == 1:
        masked_local = "*"
    elif len(local) == 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[:2] + ("*" * (len(local) - 2))
    return f"{masked_local}@{domain}"


def hash_email(email: str) -> str:
    """Hash an email address for privacy-safe audit references."""
    return hashlib.sha256(email.encode()).hexdigest()


class BetaSignupStore:
    """Persistent beta-signup store backed by SQLite."""

    def __init__(self, db_path: str = settings.AUDIT_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS beta_signups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    email_sha256 TEXT NOT NULL UNIQUE,
                    email_masked TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_beta_signups_created_at
                ON beta_signups(created_at)
                """
            )
            conn.commit()

    def add(self, email: str, source: str = "website") -> dict:
        """Store or update a beta signup and return sanitized metadata."""
        normalized = email.strip().lower()
        email_sha256 = hash_email(normalized)
        email_masked = mask_email(normalized)
        created_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO beta_signups
                    (email, email_sha256, email_masked, source, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (normalized, email_sha256, email_masked, source, created_at),
                )
                row = conn.execute(
                    """
                    SELECT email, email_sha256, email_masked, source, created_at
                    FROM beta_signups
                    WHERE email_sha256 = ?
                    """,
                    (email_sha256,),
                ).fetchone()
                conn.commit()

        return {
            "email": row[0],
            "email_sha256": row[1],
            "email_masked": row[2],
            "source": row[3],
            "created_at": row[4],
        }

    def get_recent(self, limit: int = 500) -> list[dict]:
        """Return recent beta signups with raw email for authorized access only."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT email, email_sha256, email_masked, source, created_at
                FROM beta_signups
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "email": row[0],
                "email_sha256": row[1],
                "email_masked": row[2],
                "source": row[3],
                "timestamp": row[4],
            }
            for row in rows
        ]


signup_store = BetaSignupStore()
