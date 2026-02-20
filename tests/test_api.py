"""
API Integration Tests — Endpoint Verification

Tests every public API endpoint using FastAPI's TestClient.
No real LLM calls — we test local scan mode and mock-free
paths (health, audit, patterns).

These tests catch:
  - Schema mismatches (response model vs actual data)
  - Route registration issues
  - Middleware/dependency injection bugs
  - Response format regressions
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# --- Fixtures ---

@pytest.fixture(scope="module")
def client():
    """Create a test client for the BiasClear API."""
    from api.main import app
    with TestClient(app) as c:
        yield c


# ============================================================
# HEALTH & META
# ============================================================

class TestHealth:
    """Verify /health returns correct structure."""

    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_fields(self, client):
        data = client.get("/health").json()
        assert data["status"] == "operational"
        assert "core_version" in data
        assert "llm_provider" in data
        assert "audit_entries" in data
        assert "learning_enabled" in data

    def test_root_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_demo_redirects(self, client):
        r = client.get("/demo", follow_redirects=False)
        assert r.status_code in (301, 302, 307)


# ============================================================
# SCAN — LOCAL MODE (no LLM required)
# ============================================================

class TestScanLocal:
    """Verify /scan local mode returns correct structure."""

    def test_clean_text_returns_high_score(self, client):
        r = client.post("/scan", json={
            "text": "The court held in Smith v. Jones, 500 U.S. 100 (2000), that the statute applies.",
            "mode": "local",
            "domain": "legal",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["truth_score"] >= 80
        assert data["bias_detected"] is False
        assert data["scan_mode"] == "local"
        assert data["core_version"]

    def test_biased_text_returns_flags(self, client):
        r = client.post("/scan", json={
            "text": "All credible legal scholars agree this case is plainly frivolous. "
                    "The well-settled law makes clear that no reasonable court would entertain such arguments.",
            "mode": "local",
            "domain": "legal",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["truth_score"] < 80
        assert data["bias_detected"] is True
        assert len(data["flags"]) > 0
        assert data["scan_mode"] == "local"

    def test_response_schema_fields(self, client):
        """Verify all ScanResponse fields are present."""
        r = client.post("/scan", json={
            "text": "This is a neutral factual statement with no bias indicators.",
            "mode": "local",
            "domain": "general",
        })
        data = r.json()
        required_fields = [
            "text", "truth_score", "knowledge_type", "bias_detected",
            "bias_types", "pit_tier", "pit_detail", "severity",
            "confidence", "explanation", "flags", "scan_mode",
            "source", "core_version",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_flag_structure(self, client):
        """Verify flag objects have correct shape."""
        r = client.post("/scan", json={
            "text": "All experts unanimously agree this is settled science.",
            "mode": "local",
            "domain": "general",
        })
        data = r.json()
        assert len(data["flags"]) > 0
        flag = data["flags"][0]
        assert "category" in flag
        assert "pattern_id" in flag
        assert "matched_text" in flag
        assert "severity" in flag
        assert "pit_tier" in flag

    def test_domain_legal(self, client):
        r = client.post("/scan", json={
            "text": "This is plainly meritless and wholly frivolous litigation.",
            "mode": "local",
            "domain": "legal",
        })
        data = r.json()
        legal_flags = [f for f in data["flags"] if f["pattern_id"].startswith("LEGAL_")]
        assert len(legal_flags) > 0

    def test_domain_media(self, client):
        r = client.post("/scan", json={
            "text": "The embattled leader's controversial policy sparked growing concern "
                    "among many experts who say the move is ill-conceived.",
            "mode": "local",
            "domain": "media",
        })
        data = r.json()
        assert data["bias_detected"] is True
        assert len(data["flags"]) > 0

    def test_empty_text_rejected(self, client):
        r = client.post("/scan", json={
            "text": "",
            "mode": "local",
            "domain": "general",
        })
        assert r.status_code == 422

    def test_invalid_mode_rejected(self, client):
        r = client.post("/scan", json={
            "text": "Some text.",
            "mode": "invalid",
            "domain": "general",
        })
        assert r.status_code == 422

    def test_score_breakdown_present(self, client):
        r = client.post("/scan", json={
            "text": "All experts agree this settled science proves my point.",
            "mode": "local",
            "domain": "general",
        })
        data = r.json()
        assert "score_breakdown" in data


# ============================================================
# SCAN BATCH — LOCAL MODE
# ============================================================

class TestScanBatch:

    def test_batch_returns_results(self, client):
        r = client.post("/scan/batch", json={
            "items": [
                {"text": "Clean factual statement.", "mode": "local", "domain": "general"},
                {"text": "All experts agree this is true.", "mode": "local", "domain": "general"},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert data["scanned"] == 2
        assert len(data["results"]) == 2

    def test_batch_empty_rejected(self, client):
        r = client.post("/scan/batch", json={"items": []})
        assert r.status_code == 422


# ============================================================
# CORRECT — THRESHOLD GATE (no LLM call needed)
# ============================================================

class TestCorrectThreshold:
    """Test correction threshold gate — no LLM calls needed."""

    def test_below_threshold_returns_no_correction(self, client):
        """Clean text should not trigger correction."""
        r = client.post("/correct", json={
            "text": "The court ruled on the matter.",
            "scan_result": {
                "truth_score": 95,
                "bias_detected": False,
                "flags": [],
            },
            "domain": "general",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["correction_triggered"] is False
        assert data["original"] == data["corrected"]
        assert data["confidence"] == 1.0

    def test_correct_response_schema(self, client):
        """Verify CorrectResponse fields are present."""
        r = client.post("/correct", json={
            "text": "Some text.",
            "scan_result": {"truth_score": 100, "bias_detected": False, "flags": []},
            "domain": "general",
        })
        data = r.json()
        required = ["original", "corrected", "changes_made", "bias_removed", "confidence"]
        for field in required:
            assert field in data, f"Missing field: {field}"


# ============================================================
# AUDIT
# ============================================================

class TestAudit:

    def test_audit_returns_entries(self, client):
        r = client.get("/audit?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert "entries" in data
        assert "total_count" in data

    def test_audit_verify(self, client):
        r = client.get("/audit/verify?limit=10")
        assert r.status_code == 200
        data = r.json()
        assert "verified" in data
        assert "entries_checked" in data
        assert "broken_links" in data


# ============================================================
# PATTERNS
# ============================================================

class TestPatterns:

    def test_patterns_returns_list(self, client):
        r = client.get("/patterns?domain=general")
        assert r.status_code == 200
        data = r.json()
        assert data["frozen_patterns"] > 0
        assert "patterns" in data

    def test_patterns_legal(self, client):
        r = client.get("/patterns?domain=legal")
        assert r.status_code == 200
        data = r.json()
        assert data["frozen_patterns"] > data.get("learned_patterns", 0)

    def test_learned_patterns_endpoint(self, client):
        r = client.get("/patterns/learned")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "active" in data
        assert "staging" in data
        assert "activation_threshold" in data
