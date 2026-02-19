"""
Tests for auth middleware and rate limiting.
"""

import os
import time
import pytest
from unittest.mock import patch


class TestAuth:
    """API key authentication tests."""

    def test_generate_key_format(self):
        from app.auth import generate_api_key
        key = generate_api_key()
        assert key.startswith("bc_")
        assert len(key) > 30

    def test_verify_key_valid(self):
        import hashlib
        from app.auth import _verify_key

        test_key = "bc_test_key_12345"
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()

        # Temporarily add to valid hashes
        from app import auth
        original = auth._VALID_KEY_HASHES.copy()
        auth._VALID_KEY_HASHES.add(key_hash)
        try:
            assert _verify_key(test_key) is True
        finally:
            auth._VALID_KEY_HASHES = original

    def test_verify_key_invalid(self):
        from app.auth import _verify_key
        assert _verify_key("totally_fake_key") is False

    def test_verify_key_empty(self):
        from app.auth import _verify_key
        assert _verify_key("") is False


class TestRateLimiter:
    """Rate limiting tests."""

    def test_under_limit_passes(self):
        from app.rate_limit import check_rate_limit, RateLimits, _windows, _lock

        with _lock:
            _windows.pop("test_under", None)

        # Should not raise
        check_rate_limit("test_under", RateLimits(per_minute=10, per_hour=100))

    def test_over_minute_limit_raises(self):
        from app.rate_limit import check_rate_limit, RateLimits, RateWindow, _windows, _lock
        from fastapi import HTTPException

        # Pre-fill the window
        with _lock:
            window = RateWindow()
            now = time.time()
            window.timestamps = [now - i for i in range(10)]  # 10 recent requests
            _windows["test_minute"] = window

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit("test_minute", RateLimits(per_minute=10, per_hour=1000))
        assert exc_info.value.status_code == 429

    def test_none_key_skips(self):
        from app.rate_limit import check_rate_limit
        # Should not raise — None means dev mode
        check_rate_limit(None)

    def test_get_usage(self):
        from app.rate_limit import get_usage, check_rate_limit, RateLimits, _windows, _lock

        with _lock:
            _windows.pop("test_usage", None)

        check_rate_limit("test_usage", RateLimits(per_minute=100, per_hour=1000))
        usage = get_usage("test_usage")
        assert usage["minute"] == 1
        assert usage["hour"] == 1

    def test_cleanup_stale(self):
        from app.rate_limit import cleanup_stale_windows, RateWindow, _windows, _lock

        with _lock:
            stale_window = RateWindow()
            stale_window.timestamps = [time.time() - 10000]  # Very old
            _windows["stale_key"] = stale_window

        cleanup_stale_windows(max_age=100)

        with _lock:
            assert "stale_key" not in _windows


class TestLogging:
    """Structured logging tests."""

    def test_json_formatter(self):
        import json
        import logging
        from app.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="biasclear.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_json_formatter_extra_fields(self):
        import json
        import logging
        from app.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="biasclear.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Scan done",
            args=(),
            exc_info=None,
        )
        record.truth_score = 72
        record.domain = "legal"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["truth_score"] == 72
        assert parsed["domain"] == "legal"

    def test_get_logger(self):
        from app.logging import get_logger
        log = get_logger("detector")
        assert log.name == "biasclear.detector"
