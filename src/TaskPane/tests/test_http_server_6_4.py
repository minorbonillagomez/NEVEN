"""Property test for task 6.4: rate limiter and payload size limit.

**Property 7: Rate limiter and payload size limit apply to all Script endpoints**
**Validates: Requirements 3.11, 3.12**

Sub-test A: Exhaust rate limiter → HTTP 429.
Sub-test B: Payload size > maxPayloadMB → HTTP 413.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
import threading
import unittest
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_TASKPANE = os.path.dirname(_HERE)
_CTRL_STARTUP = os.path.join(os.path.dirname(_TASKPANE), "ControlPython", "startup")
sys.path.insert(0, _CTRL_STARTUP)
sys.path.insert(0, _TASKPANE)

import neven_http_server as srv  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_handler(config: dict) -> srv.NEVENHandler:
    """Construct a NEVENHandler without a real socket."""
    srv._config = config
    handler = srv.NEVENHandler.__new__(srv.NEVENHandler)
    handler.headers = {}
    handler.rfile = io.BytesIO(b"")
    handler.wfile = io.BytesIO()
    handler.server = None
    handler.connection = None
    handler.client_address = ("127.0.0.1", 9999)
    return handler


def _build_post_handler(path: str, content_length: int, body_bytes: bytes,
                         config: dict) -> srv.NEVENHandler:
    """Build a handler as if do_POST were called with given path & body."""
    srv._config = config
    handler = srv.NEVENHandler.__new__(srv.NEVENHandler)
    handler.path = "/" + path
    handler.headers = {"Content-Length": str(content_length)}
    handler.rfile = io.BytesIO(body_bytes)
    handler.wfile = io.BytesIO()
    handler.server = None
    handler.connection = None
    handler.client_address = ("127.0.0.1", 9999)
    return handler


def _run_do_post(handler: srv.NEVENHandler) -> dict:
    """Run do_POST and capture the first JSON response written."""
    captured = {}

    def fake_send_json(data, status=200):
        if not captured:
            captured["status"] = status
            captured["data"] = data

    def fake_send_error_json(message, status=400):
        if not captured:
            captured["status"] = status
            captured["data"] = {"status": "error", "message": message}

    handler._send_json = fake_send_json
    handler._send_error_json = fake_send_error_json
    handler.do_POST()
    return captured


# ── Property 7 ────────────────────────────────────────────────────────────────

class TestRateLimiterAndPayloadSize(unittest.TestCase):
    """Property 7 — rate limiter and payload size apply to all Script endpoints (Req 3.11, 3.12)."""

    # ── Sub-test A: rate limiter ──────────────────────────────────────────────

    @given(endpoint=st.sampled_from(["api/r", "api/python", "api/julia"]))
    @settings(max_examples=50)
    def test_rate_limit_reached_returns_429(self, endpoint: str) -> None:
        """After exhausting the rate limiter, do_POST returns HTTP 429.

        **Property 7 Sub-A: Rate limiter applies to all Script endpoints**
        **Validates: Requirements 3.11**
        """
        # Replace the module-level limiter with a fresh one that's pre-exhausted
        depleted_limiter = srv.RateLimiter(max_requests=1, window_sec=60)
        # Consume the one allowed request
        depleted_limiter.allow()  # returns True
        # Now it will return False

        body_bytes = json.dumps({"code": "1+1"}).encode()

        handler = _build_post_handler(
            endpoint,
            len(body_bytes),
            body_bytes,
            {**srv.DEFAULT_CONFIG},
        )

        with patch.object(srv, "_rate_limiter", depleted_limiter):
            result = _run_do_post(handler)

        self.assertEqual(result["status"], 429,
                         f"Expected 429 for {endpoint} after rate limit exhausted")

    @given(endpoint=st.sampled_from(["api/r", "api/python", "api/julia"]))
    @settings(max_examples=30)
    def test_rate_limiter_allow_returns_false_causes_429(self, endpoint: str) -> None:
        """When _rate_limiter.allow() returns False, response is 429.

        **Validates: Requirements 3.11**
        """
        body_bytes = json.dumps({"code": "print(1)"}).encode()
        handler = _build_post_handler(
            endpoint,
            len(body_bytes),
            body_bytes,
            {**srv.DEFAULT_CONFIG},
        )

        # Mock the rate limiter to always deny
        mock_limiter = MagicMock()
        mock_limiter.allow.return_value = False

        with patch.object(srv, "_rate_limiter", mock_limiter):
            result = _run_do_post(handler)

        self.assertEqual(result["status"], 429)

    # ── Sub-test B: payload size ───────────────────────────────────────────────

    @given(endpoint=st.sampled_from(["api/r", "api/python", "api/julia"]))
    @settings(max_examples=50)
    def test_oversized_content_length_returns_413(self, endpoint: str) -> None:
        """Content-Length > maxPayloadMB * 1024^2 → HTTP 413.

        **Property 7 Sub-B: Payload size limit applies to all Script endpoints**
        **Validates: Requirements 3.12**
        """
        max_mb = srv.DEFAULT_CONFIG.get("maxPayloadMB", 50)
        oversized = max_mb * 1024 * 1024 + 1  # one byte over the limit

        # Body bytes themselves don't matter — the check is on Content-Length
        body_bytes = b"{}"

        handler = _build_post_handler(
            endpoint,
            oversized,
            body_bytes,
            {**srv.DEFAULT_CONFIG},
        )

        # Allow the rate limiter so it doesn't interfere
        permissive_limiter = srv.RateLimiter(max_requests=10000, window_sec=60)

        with patch.object(srv, "_rate_limiter", permissive_limiter):
            result = _run_do_post(handler)

        self.assertEqual(result["status"], 413,
                         f"Expected 413 for {endpoint} with oversized Content-Length")

    @given(endpoint=st.sampled_from(["api/r", "api/python", "api/julia"]))
    @settings(max_examples=30)
    def test_exactly_at_limit_not_413(self, endpoint: str) -> None:
        """Content-Length exactly equal to the limit is NOT rejected with 413.

        **Validates: Requirements 3.12**
        """
        max_mb = 1  # use a small limit for speed
        config = {**srv.DEFAULT_CONFIG, "maxPayloadMB": max_mb}
        at_limit = max_mb * 1024 * 1024  # exactly at limit

        body_bytes = json.dumps({"code": "1+1"}).encode()

        handler = _build_post_handler(
            endpoint,
            at_limit,
            body_bytes,
            config,
        )

        permissive_limiter = srv.RateLimiter(max_requests=10000, window_sec=60)

        with patch.object(srv, "_rate_limiter", permissive_limiter):
            result = _run_do_post(handler)

        # Must not be 413 (may be 503 or other status — that's fine)
        self.assertNotEqual(result.get("status"), 413,
                            f"Content-Length exactly at limit should not be 413 for {endpoint}")

    # ── Both limits apply to all three endpoints ──────────────────────────────

    def test_all_three_endpoints_respect_rate_limit(self) -> None:
        """Rate limiter applies consistently to r, python, and julia endpoints."""
        mock_limiter = MagicMock()
        mock_limiter.allow.return_value = False

        body_bytes = json.dumps({"code": "1"}).encode()

        for endpoint in ["api/r", "api/python", "api/julia"]:
            with self.subTest(endpoint=endpoint):
                handler = _build_post_handler(
                    endpoint, len(body_bytes), body_bytes, {**srv.DEFAULT_CONFIG}
                )
                with patch.object(srv, "_rate_limiter", mock_limiter):
                    result = _run_do_post(handler)
                self.assertEqual(result["status"], 429)

    def test_all_three_endpoints_respect_payload_size(self) -> None:
        """Payload size limit applies consistently to r, python, and julia."""
        max_mb = srv.DEFAULT_CONFIG.get("maxPayloadMB", 50)
        oversized = max_mb * 1024 * 1024 + 1
        permissive = srv.RateLimiter(max_requests=10000, window_sec=60)

        for endpoint in ["api/r", "api/python", "api/julia"]:
            with self.subTest(endpoint=endpoint):
                handler = _build_post_handler(
                    endpoint, oversized, b"{}", {**srv.DEFAULT_CONFIG}
                )
                with patch.object(srv, "_rate_limiter", permissive):
                    result = _run_do_post(handler)
                self.assertEqual(result["status"], 413)


if __name__ == "__main__":
    unittest.main()
