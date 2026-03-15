"""
Outage Simulation Tests — Degraded Mode Verification

Tests covering graceful degradation under failure conditions:
  - LLM provider unavailable
  - Circuit breaker open
  - Batch partial failures
  - Fallback from deep/full to local scan
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limiter state between tests."""
    from biasclear.rate_limit import _windows, _lock
    with _lock:
        _windows.clear()
    yield
    with _lock:
        _windows.clear()


# ============================================================
# LOCAL SCAN RESILIENCE
# ============================================================

class TestLocalScanResilience:
    """Verify local scan always works regardless of LLM state."""

    def test_local_scan_works_always(self, client):
        """Local scan has zero LLM dependency."""
        res = client.post("/scan", json={
            "text": "All experts agree this is settled science.",
            "mode": "local", "domain": "general",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["scan_mode"] == "local"
        assert data["truth_score"] < 80  # Should detect structural bias

    def test_local_scan_clean_text(self, client):
        """Clean text should score high on local scan."""
        res = client.post("/scan", json={
            "text": "The study found a 15% increase in yield.",
            "mode": "local", "domain": "general",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["truth_score"] >= 70


# ============================================================
# BATCH PARTIAL FAILURES
# ============================================================

class TestBatchPartialFailure:
    """Verify batch scan handles partial failures without crashing."""

    def test_batch_local_scans_always_succeed(self, client):
        """Local-only batch should always succeed regardless of LLM state."""
        res = client.post("/scan/batch", json={
            "items": [
                {"text": "Clean factual statement.", "mode": "local", "domain": "general"},
                {"text": "All experts universally agree.", "mode": "local", "domain": "general"},
            ],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert data["scanned"] == 2

    def test_batch_error_items_have_valid_schema(self):
        """Error placeholder items must satisfy ScanResponse schema."""
        from biasclear.schemas.scan import ScanResponse

        error_placeholder = {
            "text": "",
            "truth_score": 0,
            "knowledge_type": "unknown",
            "bias_detected": False,
            "bias_types": [],
            "pit_tier": "none",
            "pit_detail": "",
            "severity": "none",
            "confidence": 0.0,
            "explanation": "Scan failed for this item.",
            "flags": [],
            "impact_projection": None,
            "scan_mode": "error",
            "source": "error",
            "core_version": "1.2.0",
        }
        validated = ScanResponse(**error_placeholder)
        assert validated.scan_mode == "error"
        assert validated.truth_score == 0


# ============================================================
# HEALTH UNDER STRESS
# ============================================================

class TestHealthUnderStress:
    """Verify health endpoint works even when other things are broken."""

    def test_health_when_llm_unavailable(self, client):
        """Health should still respond when LLM check fails."""
        with patch("api.main._get_llm", side_effect=Exception("Connection refused")):
            res = client.get("/health")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "operational"
            assert data["llm_available"] is False

    def test_health_response_schema(self, client):
        """Health response should always have required fields."""
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        required_fields = [
            "status", "version", "core_version", "llm_provider",
            "llm_available", "total_scans", "uptime_seconds",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_stats_endpoint_works(self, client):
        """Stats endpoint should return valid data."""
        res = client.get("/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_scans" in data
        assert "scans_by_mode" in data
        assert "score_distribution" in data
        assert "top_patterns_fired" in data
        assert "last_24h" in data
        assert "learning_ring" in data


# ============================================================
# AUDIT CHAIN RESILIENCE
# ============================================================

class TestAuditResilience:
    """Verify audit chain handles edge cases."""

    def test_verify_empty_chain(self):
        """Verification on empty chain should return verified=True."""
        from biasclear.audit import AuditChain
        import tempfile, os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            chain = AuditChain(db_path=tmp)
            result = chain.verify_chain(limit=100)
            assert result["verified"] is True
            assert result["entries_checked"] == 0
        finally:
            os.unlink(tmp)

    def test_verify_single_entry(self):
        """Single entry chain should verify."""
        from biasclear.audit import AuditChain
        import tempfile, os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            chain = AuditChain(db_path=tmp)
            chain.log("test_event", {"data": "value"}, "1.0.0")
            result = chain.verify_chain(limit=100)
            assert result["verified"] is True
            assert result["entries_checked"] == 1
        finally:
            os.unlink(tmp)

    def test_verify_checks_recent_entries(self):
        """Verification with limit should check most recent entries."""
        from biasclear.audit import AuditChain
        import tempfile, os
        tmp = tempfile.mktemp(suffix=".db")
        try:
            chain = AuditChain(db_path=tmp)
            for i in range(10):
                chain.log("test_event", {"index": i}, "1.0.0")
            result = chain.verify_chain(limit=3)
            assert result["verified"] is True
            assert result["entries_checked"] == 3
        finally:
            os.unlink(tmp)

    def test_tampered_entry_detected(self):
        """Tampered entry should break chain verification."""
        from biasclear.audit import AuditChain
        import tempfile, os, sqlite3
        tmp = tempfile.mktemp(suffix=".db")
        try:
            chain = AuditChain(db_path=tmp)
            for i in range(5):
                chain.log("test_event", {"index": i}, "1.0.0")

            # Tamper with the 3rd entry's data
            conn = sqlite3.connect(tmp)
            conn.execute(
                "UPDATE audit_chain SET data = ? WHERE id = 3",
                ('{"index": 999, "tampered": true}',)
            )
            conn.commit()
            conn.close()

            result = chain.verify_chain(limit=10)
            assert result["verified"] is False
            assert len(result["broken_links"]) > 0
        finally:
            os.unlink(tmp)


# ============================================================
# DEGRADED MODE TRUTHFULNESS
# ============================================================

class TestDegradedModeTruth:
    """Verify degraded state is explicit in API responses — not hidden."""

    def test_degraded_fields_in_schema(self):
        """ScanResponse must include degraded and degradation_warning fields."""
        from biasclear.schemas.scan import ScanResponse

        # Default: not degraded
        resp = ScanResponse(
            text="test", truth_score=90, knowledge_type="neutral",
            bias_detected=False, bias_types=[], pit_tier="none",
            pit_detail="", severity="none", confidence=0.0,
            explanation="", flags=[], scan_mode="full",
            source="llm+local", core_version="1.2.0",
        )
        assert resp.degraded is False
        assert resp.degradation_warning is None

    def test_degraded_fields_survive_serialization(self):
        """Degraded fields must not be stripped by Pydantic serialization."""
        from biasclear.schemas.scan import ScanResponse

        resp = ScanResponse(
            text="test", truth_score=85, knowledge_type="neutral",
            bias_detected=False, bias_types=[], pit_tier="none",
            pit_detail="", severity="none", confidence=0.0,
            explanation="", flags=[], scan_mode="full",
            source="local_fallback", core_version="1.2.0",
            degraded=True,
            degradation_warning="LLM was unavailable.",
        )
        data = resp.model_dump()
        assert data["degraded"] is True
        assert data["degradation_warning"] == "LLM was unavailable."
        assert data["source"] == "local_fallback"

    def test_circuit_breaker_fallback_sets_degraded(self, client):
        """Route-level CircuitOpenError fallback must set degraded=True."""
        from biasclear.llm import CircuitOpenError

        with patch("api.main._get_llm", side_effect=CircuitOpenError("open")):
            res = client.post("/scan", json={
                "text": "All experts agree this is settled science.",
                "mode": "full", "domain": "general",
            })
            assert res.status_code == 200
            data = res.json()
            assert data["degraded"] is True
            assert data["degradation_warning"] is not None
            assert data["truth_score"] <= 85

    def test_health_has_llm_status_fields(self, client):
        """Health response must include llm_status and llm_last_success_ago."""
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert "llm_status" in data
        assert "llm_last_success_ago" in data

    def test_health_reports_circuit_open(self, client):
        """Health should report circuit_open when circuit breaker is tripped."""
        mock_provider = MagicMock()
        mock_provider.circuit_breaker.is_open = True
        with patch("api.main._get_llm", return_value=mock_provider):
            res = client.get("/health")
            data = res.json()
            assert data["llm_available"] is False
            assert data["llm_status"] == "circuit_open"

    def test_local_scan_never_degraded(self, client):
        """Local-only scan should never be marked as degraded."""
        res = client.post("/scan", json={
            "text": "The study found a 15% increase in yield.",
            "mode": "local", "domain": "general",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["degraded"] is False
        assert data["degradation_warning"] is None
