"""
Audit Chain — SHA-256 Tamper-Evident Logging

Every scan, correction, pattern change, and governance decision
is logged to an append-only hash chain. Each entry references
the previous hash, creating a tamper-evident audit trail.

If any entry is modified after the fact, the chain breaks
and the tampering is detectable via verify_chain().

This is a local chain-of-custody log, not a distributed blockchain.
"""

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Optional


class AuditChain:
    """Append-only, hash-chained audit logger backed by SQLite."""

    def __init__(self, db_path: str = "biasclear_audit.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_chain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prev_hash TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    core_version TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type
                ON audit_chain(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON audit_chain(timestamp)
            """)
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _get_prev_hash(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT hash FROM audit_chain ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else "0" * 64

    def log(self, event_type: str, data: Any, core_version: str = "1.0.0") -> str:
        """
        Log an event to the audit chain.

        Event types:
          - scan_local:     Local-only scan completed
          - scan_deep:      LLM-powered scan completed
          - scan_full:      Full scan (local + deep) completed
          - correction:     Bias correction generated
          - pattern_proposed:   New learned pattern proposed
          - pattern_confirmed:  Existing pattern re-confirmed
          - pattern_activated:  Pattern promoted to active
          - pattern_deactivated: Pattern deactivated (FP threshold)
          - chain_verified:     Chain integrity check performed

        Returns the SHA-256 hash of the new entry.
        """
        with self._lock:
            with self._get_conn() as conn:
                prev_hash = self._get_prev_hash(conn)
                timestamp = datetime.now(timezone.utc).isoformat()
                data_str = json.dumps(data, default=str)

                chain_input = f"{prev_hash}{event_type}{data_str}{timestamp}{core_version}"
                new_hash = hashlib.sha256(chain_input.encode()).hexdigest()

                conn.execute(
                    """INSERT INTO audit_chain
                       (prev_hash, hash, event_type, data, timestamp, core_version)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (prev_hash, new_hash, event_type, data_str, timestamp, core_version),
                )
                conn.commit()
                return new_hash

    def get_recent(self, limit: int = 20, event_type: Optional[str] = None) -> list[dict]:
        """Get recent audit entries, optionally filtered by event type."""
        with self._get_conn() as conn:
            if event_type:
                rows = conn.execute(
                    """SELECT id, prev_hash, hash, event_type, data, timestamp, core_version
                       FROM audit_chain WHERE event_type = ?
                       ORDER BY id DESC LIMIT ?""",
                    (event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT id, prev_hash, hash, event_type, data, timestamp, core_version
                       FROM audit_chain ORDER BY id DESC LIMIT ?""",
                    (limit,),
                ).fetchall()

        return [
            {
                "id": r[0], "prev_hash": r[1], "hash": r[2],
                "event_type": r[3], "data": json.loads(r[4]),
                "timestamp": r[5], "core_version": r[6],
            }
            for r in rows
        ]

    def verify_chain(self, limit: int = 100) -> dict:
        """Verify integrity of the most recent entries."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT id, prev_hash, hash, event_type, data, timestamp, core_version
                   FROM audit_chain ORDER BY id ASC LIMIT ?""",
                (limit,),
            ).fetchall()

        if not rows:
            return {"verified": True, "entries_checked": 0, "broken_links": []}

        broken = []
        for i, row in enumerate(rows):
            entry_id, prev_hash, stored_hash, event_type, data_str, timestamp, core_version = row

            chain_input = f"{prev_hash}{event_type}{data_str}{timestamp}{core_version}"
            computed_hash = hashlib.sha256(chain_input.encode()).hexdigest()

            if computed_hash != stored_hash:
                broken.append({
                    "id": entry_id,
                    "issue": "hash_mismatch",
                    "expected": computed_hash,
                    "stored": stored_hash,
                })

            if i > 0 and prev_hash != rows[i - 1][2]:
                broken.append({
                    "id": entry_id,
                    "issue": "chain_break",
                    "expected_prev": rows[i - 1][2],
                    "stored_prev": prev_hash,
                })

        return {
            "verified": len(broken) == 0,
            "entries_checked": len(rows),
            "broken_links": broken,
        }

    def get_count(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM audit_chain").fetchone()
            return row[0] if row else 0


def _get_audit_chain() -> AuditChain:
    """Factory — reads db path from config."""
    from app.config import settings
    return AuditChain(db_path=settings.AUDIT_DB_PATH)


audit_chain = _get_audit_chain()
