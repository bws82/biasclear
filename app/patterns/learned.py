"""
Learning Ring — Audited Pattern Expansion

The outer ring of BiasClear's two-ring architecture.

This module manages LEARNED patterns — new distortion indicators
discovered through LLM analysis that extend the frozen core's
detection capability.

Governance Model (Option B with guardrails):
  1. The LLM layer proposes new patterns during deep analysis
  2. Proposed patterns go into a staging table
  3. Auto-activate after N independent confirmations (default: 5)
  4. Pattern MUST map to an existing PIT tier (cannot create new categories)
  5. If false positive rate exceeds threshold, auto-deactivate
  6. Every state change is logged to the SHA-256 audit chain
  7. Patterns can ONLY extend detection — never redefine what a distortion is

The frozen core holds the DEFINITIONS.
This module holds the expanding DETECTION CAPABILITY.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.frozen_core import StructuralPattern, PIT_TIERS


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class LearnedPattern:
    """A pattern proposed by the LLM layer and tracked for promotion."""
    pattern_id: str
    name: str
    description: str
    pit_tier: int
    severity: str
    principle: str
    regex: str
    # Governance fields
    status: str             # "staging" | "active" | "deactivated"
    confirmations: int      # Independent detections of this pattern
    false_positives: int    # Reported false positive count
    total_evaluations: int  # Times this pattern was evaluated
    proposed_at: str        # ISO timestamp
    activated_at: Optional[str]
    deactivated_at: Optional[str]
    source_scan_hash: str   # Audit hash of the scan that first proposed it


class LearningRing:
    """
    Manages the lifecycle of learned patterns:
    propose → stage → confirm → activate → monitor → (deactivate if bad)

    Backed by SQLite. Every state transition logged to audit chain.
    """

    def __init__(
        self,
        db_path: str = "biasclear_patterns.db",
        activation_threshold: int = 5,
        fp_limit: float = 0.15,
    ):
        self.db_path = db_path
        self.activation_threshold = activation_threshold
        self.fp_limit = fp_limit
        self._lock = threading.Lock()
        self._audit_fn = None  # Set by app startup to wire in audit logger
        self._init_db()

    def set_audit_logger(self, audit_fn):
        """Wire in the audit logger function: fn(event_type, data) -> hash."""
        self._audit_fn = audit_fn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    pit_tier INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    principle TEXT NOT NULL,
                    regex TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'staging',
                    confirmations INTEGER NOT NULL DEFAULT 1,
                    false_positives INTEGER NOT NULL DEFAULT 0,
                    total_evaluations INTEGER NOT NULL DEFAULT 0,
                    proposed_at TEXT NOT NULL,
                    activated_at TEXT,
                    deactivated_at TEXT,
                    source_scan_hash TEXT NOT NULL
                )
            """)
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _audit(self, event_type: str, data: dict) -> Optional[str]:
        """Log to audit chain if logger is wired."""
        if self._audit_fn:
            return self._audit_fn(event_type, data)
        return None

    def propose(
        self,
        pattern_id: str,
        name: str,
        description: str,
        pit_tier: int,
        severity: str,
        principle: str,
        regex: str,
        source_scan_hash: str,
    ) -> dict:
        """
        Propose a new pattern discovered by the LLM layer.

        Governance checks:
        1. PIT tier must be 1, 2, or 3 (cannot create new tiers)
        2. Pattern ID must be unique or increment existing confirmation
        3. All proposals are audited
        """
        # Guard: Must map to existing PIT tier
        if pit_tier not in PIT_TIERS:
            return {
                "accepted": False,
                "reason": f"PIT tier {pit_tier} does not exist. Cannot create new tiers.",
            }

        # Guard: Validate severity
        valid_severities = {"low", "moderate", "high", "critical"}
        if severity not in valid_severities:
            return {"accepted": False, "reason": f"Invalid severity: {severity}"}

        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_conn() as conn:
                existing = conn.execute(
                    "SELECT pattern_id, status, confirmations FROM learned_patterns WHERE pattern_id = ?",
                    (pattern_id,),
                ).fetchone()

                if existing:
                    # Pattern already proposed — increment confirmations
                    old_confirmations = existing[2]
                    new_confirmations = old_confirmations + 1
                    conn.execute(
                        "UPDATE learned_patterns SET confirmations = ? WHERE pattern_id = ?",
                        (new_confirmations, pattern_id),
                    )
                    conn.commit()

                    self._audit("pattern_confirmed", {
                        "pattern_id": pattern_id,
                        "confirmations": new_confirmations,
                        "source_scan_hash": source_scan_hash,
                    })

                    # Check for auto-activation
                    if (
                        existing[1] == "staging"
                        and new_confirmations >= self.activation_threshold
                    ):
                        return self._activate(conn, pattern_id)

                    return {
                        "accepted": True,
                        "action": "confirmed",
                        "confirmations": new_confirmations,
                        "threshold": self.activation_threshold,
                    }
                else:
                    # New pattern — insert as staging
                    conn.execute(
                        """INSERT INTO learned_patterns
                           (pattern_id, name, description, pit_tier, severity,
                            principle, regex, status, confirmations,
                            false_positives, total_evaluations,
                            proposed_at, source_scan_hash)
                           VALUES (?, ?, ?, ?, ?, ?, ?, 'staging', 1, 0, 0, ?, ?)""",
                        (
                            pattern_id, name, description, pit_tier, severity,
                            principle, regex, now, source_scan_hash,
                        ),
                    )
                    conn.commit()

                    self._audit("pattern_proposed", {
                        "pattern_id": pattern_id,
                        "name": name,
                        "pit_tier": pit_tier,
                        "severity": severity,
                        "source_scan_hash": source_scan_hash,
                    })

                    return {
                        "accepted": True,
                        "action": "proposed",
                        "confirmations": 1,
                        "threshold": self.activation_threshold,
                    }

    def _activate(self, conn: sqlite3.Connection, pattern_id: str) -> dict:
        """Activate a staging pattern that has reached the confirmation threshold."""
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE learned_patterns SET status = 'active', activated_at = ? WHERE pattern_id = ?",
            (now, pattern_id),
        )
        conn.commit()

        self._audit("pattern_activated", {
            "pattern_id": pattern_id,
            "activated_at": now,
        })

        return {
            "accepted": True,
            "action": "activated",
            "pattern_id": pattern_id,
        }

    def report_false_positive(self, pattern_id: str) -> dict:
        """
        Report a false positive for a learned pattern.
        If FP rate exceeds the limit, auto-deactivate.
        """
        with self._lock:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT false_positives, total_evaluations, status FROM learned_patterns WHERE pattern_id = ?",
                    (pattern_id,),
                ).fetchone()

                if not row:
                    return {"error": f"Pattern {pattern_id} not found"}

                fps = row[0] + 1
                total = row[1]
                status = row[2]

                conn.execute(
                    "UPDATE learned_patterns SET false_positives = ? WHERE pattern_id = ?",
                    (fps, pattern_id),
                )

                # Check FP rate
                if total > 0 and (fps / total) > self.fp_limit and status == "active":
                    now = datetime.now(timezone.utc).isoformat()
                    conn.execute(
                        "UPDATE learned_patterns SET status = 'deactivated', deactivated_at = ? WHERE pattern_id = ?",
                        (now, pattern_id),
                    )
                    conn.commit()

                    self._audit("pattern_deactivated", {
                        "pattern_id": pattern_id,
                        "reason": "false_positive_threshold_exceeded",
                        "fp_rate": fps / total,
                        "deactivated_at": now,
                    })

                    return {
                        "action": "deactivated",
                        "pattern_id": pattern_id,
                        "reason": f"FP rate {fps}/{total} exceeds limit {self.fp_limit}",
                    }

                conn.commit()
                return {"action": "recorded", "false_positives": fps}

    def record_evaluation(self, pattern_id: str) -> None:
        """Increment evaluation count for a pattern (for FP rate calculation)."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE learned_patterns SET total_evaluations = total_evaluations + 1 WHERE pattern_id = ?",
                (pattern_id,),
            )
            conn.commit()

    def get_active_patterns(self) -> list[StructuralPattern]:
        """
        Return all active learned patterns as StructuralPattern objects,
        compatible with the frozen core's evaluation engine.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT pattern_id, name, description, pit_tier, severity,
                          principle, regex
                   FROM learned_patterns WHERE status = 'active'"""
            ).fetchall()

        return [
            StructuralPattern(
                id=row[0],
                name=row[1],
                description=row[2],
                pit_tier=row[3],
                severity=row[4],
                principle=row[5],
                indicators=[row[6]],
                min_matches=1,
            )
            for row in rows
        ]

    def get_all_patterns(self) -> list[dict]:
        """Return all learned patterns with full metadata."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT pattern_id, name, description, pit_tier, severity,
                          principle, regex, status, confirmations,
                          false_positives, total_evaluations,
                          proposed_at, activated_at, deactivated_at
                   FROM learned_patterns ORDER BY proposed_at DESC"""
            ).fetchall()

        return [
            {
                "pattern_id": r[0], "name": r[1], "description": r[2],
                "pit_tier": r[3], "severity": r[4], "principle": r[5],
                "regex": r[6], "status": r[7], "confirmations": r[8],
                "false_positives": r[9], "total_evaluations": r[10],
                "proposed_at": r[11], "activated_at": r[12],
                "deactivated_at": r[13],
            }
            for r in rows
        ]


def _get_learning_ring() -> LearningRing:
    """Factory — reads thresholds from config."""
    from app.config import settings
    return LearningRing(
        db_path="biasclear_patterns.db",
        activation_threshold=settings.PATTERN_AUTO_ACTIVATE_THRESHOLD,
        fp_limit=settings.PATTERN_FALSE_POSITIVE_LIMIT,
    )


learning_ring = _get_learning_ring()
