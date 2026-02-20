"""
API Schemas — Request and Response Models

Pydantic models for the BiasClear API.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ============================================================
# SCAN
# ============================================================

class ScanRequest(BaseModel):
    """POST /scan request body."""
    text: str = Field(..., min_length=1, max_length=50_000)
    mode: str = Field("full", pattern="^(local|deep|full)$")
    domain: str = Field("general", pattern="^(general|legal|media|financial|auto)$")


class ScanBatchRequest(BaseModel):
    """POST /scan/batch request body."""
    items: list[ScanRequest] = Field(..., min_length=1, max_length=100)


class FlagResponse(BaseModel):
    category: str
    pattern_id: str
    matched_text: str
    pit_tier: int
    severity: str
    description: str = ""
    source: str = "core"


class ImpactPath(BaseModel):
    title: str
    description: str


class ImpactProjection(BaseModel):
    path_a: ImpactPath
    path_b: ImpactPath


class ScanResponse(BaseModel):
    """POST /scan response body."""
    text: str
    truth_score: int
    knowledge_type: str
    bias_detected: bool
    bias_types: list[str]
    pit_tier: str
    pit_detail: str
    severity: str
    confidence: float
    explanation: str
    flags: list[FlagResponse]
    impact_projection: Optional[ImpactProjection] = None
    scan_mode: str
    source: str
    core_version: str
    audit_hash: Optional[str] = None
    learning_proposals: Optional[list[dict]] = None
    score_breakdown: Optional[dict] = None
    self_scan: Optional[dict] = None


class ScanBatchResponse(BaseModel):
    """POST /scan/batch response body."""
    results: list[ScanResponse]
    total: int
    scanned: int


# ============================================================
# CORRECT
# ============================================================

class CorrectRequest(BaseModel):
    """POST /correct request body."""
    text: str = Field(..., min_length=1, max_length=50_000)
    scan_result: dict  # The output from /scan


class CorrectResponse(BaseModel):
    """POST /correct response body."""
    original: str
    corrected: str
    changes_made: list[str]
    bias_removed: list[str]
    confidence: float
    note: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# AUDIT
# ============================================================

class AuditEntry(BaseModel):
    id: int
    prev_hash: str
    hash: str
    event_type: str
    data: dict
    timestamp: str
    core_version: str


class AuditResponse(BaseModel):
    entries: list[AuditEntry]
    total_count: int


class ChainVerification(BaseModel):
    verified: bool
    entries_checked: int
    broken_links: list[dict]


# ============================================================
# HEALTH
# ============================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    core_version: str
    llm_provider: str
    audit_entries: int
    learned_patterns: int
