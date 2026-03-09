"""
Red Team Tests — Adversarial Security Verification

Tests covering active attack scenarios:
  - Auth bypass attempts
  - Playground token abuse
  - Regex injection / ReDoS attempts
  - Batch flood protection
  - Rate limit hourly window integrity
  - Input injection
"""

from __future__ import annotations

import re
import time
import pytest
from unittest.mock import patch
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
# AUTH BYPASS ATTEMPTS
# ============================================================

class TestAuthBypass:
    """Attempt to bypass authentication through various vectors."""

    def test_missing_api_key_scan_allowed_playground(self, client):
        """Without auth enabled (test mode), scan should work."""
        res = client.post("/scan", json={
            "text": "Test text.", "mode": "local", "domain": "general",
        })
        assert res.status_code == 200

    def test_empty_api_key_header(self, client):
        """Empty X-API-Key header should not grant elevated access."""
        res = client.post("/scan", json={
            "text": "Test text.", "mode": "local", "domain": "general",
        }, headers={"X-API-Key": ""})
        assert res.status_code == 200  # Still playground mode

    def test_beta_signups_blocked_no_auth(self, client):
        """Beta signups endpoint should be gated when auth is disabled."""
        res = client.get("/beta-signups")
        assert res.status_code == 403

    def test_sql_injection_in_audit_hash(self, client):
        """SQL injection in certificate verify hash."""
        res = client.get("/certificate/verify/'; DROP TABLE audit_chain; --")
        assert res.status_code == 400

    def test_sql_injection_in_audit_type(self, client):
        """SQL injection in audit event_type filter."""
        res = client.get("/audit?event_type='; DROP TABLE audit_chain; --&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert data["entries"] == []

    def test_xss_in_scan_text(self, client):
        """XSS payload in scan text should be processed, not executed."""
        xss_payload = '<script>alert("xss")</script>'
        res = client.post("/scan", json={
            "text": xss_payload, "mode": "local", "domain": "general",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["text"] == xss_payload


# ============================================================
# TOKEN ABUSE
# ============================================================

class TestTokenAbuse:
    """Attempt to abuse playground tokens."""

    def test_reuse_across_ips(self):
        """Token from one IP should not work on another."""
        from biasclear.playground_token import (
            create_playground_token,
            validate_playground_token,
        )
        token = create_playground_token("10.0.0.1")
        valid, reason = validate_playground_token(token, "10.0.0.2")
        assert valid is False
        assert reason == "ip_mismatch"

    def test_forged_token_signature(self):
        """Forged HMAC signature should be rejected."""
        from biasclear.playground_token import (
            create_playground_token,
            validate_playground_token,
        )
        token = create_playground_token("10.0.0.1")
        parts = token.split(".")
        parts[1] = "0" * len(parts[1])
        forged = ".".join(parts)
        valid, reason = validate_playground_token(forged, "10.0.0.1")
        assert valid is False
        assert reason == "invalid_signature"

    def test_empty_token(self):
        """Empty token should be rejected."""
        from biasclear.playground_token import validate_playground_token
        valid, reason = validate_playground_token("", "10.0.0.1")
        assert valid is False
        assert reason == "missing_token"

    def test_garbage_token(self):
        """Random garbage token should be rejected."""
        from biasclear.playground_token import validate_playground_token
        valid, reason = validate_playground_token("abc.def.ghi.jkl", "10.0.0.1")
        assert valid is False


# ============================================================
# REGEX / REDOS ATTEMPTS
# ============================================================

class TestReDoSProtection:
    """Verify ReDoS-dangerous patterns are rejected."""

    def test_nested_quantifier_rejected(self):
        """Pattern with nested quantifiers should be rejected at proposal."""
        from biasclear.patterns.learned import learning_ring
        result = learning_ring.propose(
            pattern_id="redos_test_001",
            name="redos_test",
            description="ReDoS test pattern",
            regex="(a+)+b",
            pit_tier=1,
            severity="low",
            principle="truth",
            source_scan_hash="test_hash_redos",
        )
        assert result["accepted"] is False
        assert "nested quantifiers" in result["reason"].lower()

    def test_overly_long_regex_rejected(self):
        """Regex longer than 200 chars should be rejected."""
        from biasclear.patterns.learned import learning_ring
        result = learning_ring.propose(
            pattern_id="long_regex_001",
            name="long_regex_test",
            description="Too long",
            regex="a" * 201,
            pit_tier=1,
            severity="low",
            principle="truth",
            source_scan_hash="test_hash_long",
        )
        assert result["accepted"] is False
        assert "too long" in result["reason"].lower()

    def test_invalid_regex_rejected(self):
        """Syntactically invalid regex should be rejected."""
        from biasclear.patterns.learned import learning_ring
        result = learning_ring.propose(
            pattern_id="invalid_regex_001",
            name="invalid_regex_test",
            description="Invalid regex",
            regex="[unclosed",
            pit_tier=1,
            severity="low",
            principle="truth",
            source_scan_hash="test_hash_invalid",
        )
        assert result["accepted"] is False
        assert "invalid regex" in result["reason"].lower()

    def test_frozen_core_timeout_protection(self):
        """Frozen core regex execution has timeout protection."""
        from biasclear.frozen_core import _regex_with_timeout
        result = _regex_with_timeout(r"\btest\b", "this is a test", timeout=2)
        assert result == ["test"]

    def test_frozen_core_invalid_regex_handled(self):
        """Invalid regex in frozen core should return empty, not crash."""
        from biasclear.frozen_core import _regex_with_timeout
        result = _regex_with_timeout("[invalid", "test text", timeout=2)
        assert result == []


# ============================================================
# BATCH FLOOD PROTECTION
# ============================================================

class TestBatchFlood:
    """Verify batch scan limits are enforced."""

    def test_batch_over_50_rejected(self, client):
        """Batch with >50 items should be rejected."""
        items = [
            {"text": f"Item {i}", "mode": "local", "domain": "general"}
            for i in range(51)
        ]
        res = client.post("/scan/batch", json={"items": items})
        assert res.status_code == 400
        assert "50" in res.json()["detail"]

    def test_batch_at_limit_accepted(self, client):
        """Batch with exactly 50 items should be accepted."""
        items = [
            {"text": f"Clean factual statement number {i}.", "mode": "local", "domain": "general"}
            for i in range(50)
        ]
        res = client.post("/scan/batch", json={"items": items})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 50

    def test_batch_empty_rejected(self, client):
        """Empty batch should be rejected by Pydantic validation."""
        res = client.post("/scan/batch", json={"items": []})
        assert res.status_code == 422


# ============================================================
# RATE LIMIT HOURLY WINDOW INTEGRITY
# ============================================================

class TestRateLimitHourlyWindow:
    """Verify hourly rate limit survives the per-minute check."""

    def test_hourly_count_persists_after_minute_check(self):
        """Timestamps older than 60s must survive count_within(60)."""
        from biasclear.rate_limit import RateWindow
        window = RateWindow()

        now = time.time()
        window.timestamps = [
            now - 120,  # 2 minutes ago
            now - 90,   # 90s ago
            now - 30,   # 30s ago
            now - 10,   # 10s ago
            now,
        ]

        minute_count = window.count_within(60)
        assert minute_count == 3

        hour_count = window.count_within(3600)
        assert hour_count == 5, (
            "Hourly count should include all 5 timestamps — "
            "count_within must not mutate the list"
        )

    def test_trim_only_happens_in_record(self):
        """Trimming should only happen in record(), not in count_within()."""
        from biasclear.rate_limit import RateWindow
        window = RateWindow()

        now = time.time()
        window.timestamps = [now - 7200, now - 3601, now - 30, now]

        original_len = len(window.timestamps)
        window.count_within(60)
        assert len(window.timestamps) == original_len

        window.count_within(3600)
        assert len(window.timestamps) == original_len


# ============================================================
# INPUT VALIDATION
# ============================================================

class TestInputValidation:
    """Verify input boundaries are enforced."""

    def test_empty_text_scan(self, client):
        """Empty text should still return a valid response."""
        res = client.post("/scan", json={
            "text": "", "mode": "local", "domain": "general",
        })
        assert res.status_code in (200, 422)

    def test_very_long_text_scan(self, client):
        """Very long text should not crash the server."""
        long_text = "This is a test sentence. " * 5000
        res = client.post("/scan", json={
            "text": long_text, "mode": "local", "domain": "general",
        })
        # 200 (processed) or 422 (length validation) — both are correct
        assert res.status_code in (200, 422)

    def test_invalid_scan_mode(self, client):
        """Invalid scan mode should be rejected."""
        res = client.post("/scan", json={
            "text": "Test.", "mode": "invalid_mode", "domain": "general",
        })
        assert res.status_code == 422

    def test_unicode_text_scan(self, client):
        """Unicode text should not crash."""
        res = client.post("/scan", json={
            "text": "Les experts sont unanimes. This is fine.",
            "mode": "local", "domain": "general",
        })
        assert res.status_code == 200
