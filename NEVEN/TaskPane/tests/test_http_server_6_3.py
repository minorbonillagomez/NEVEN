"""Property test for task 6.3: empty/whitespace code rejected with HTTP 400.

**Property 6: Empty or whitespace-only code is rejected with HTTP 400**
**Validates: Requirements 3.3**

For all strings where ``code.strip() == ""``, calling
``handler._handle_script(lang, {"code": code})`` must return HTTP 400 with
``{"status": "error", "message": "Missing 'code' field"}``.
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest

from hypothesis import assume, given, settings
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


def _capture_response(handler: srv.NEVENHandler, lang: str, body: dict):
    """Call _handle_script and capture status/body via _send_json."""
    captured = {}

    def fake_send_json(data, status=200):
        captured["status"] = status
        captured["data"] = data

    handler._send_json = fake_send_json
    handler._handle_script(lang, body)
    return captured


# ── Property 6 ────────────────────────────────────────────────────────────────

class TestEmptyCodeRejected400(unittest.TestCase):
    """Property 6 — empty/whitespace code → HTTP 400 (Req 3.3)."""

    @given(
        lang=st.sampled_from(["r", "python", "julia"]),
        # Generate strings composed only of whitespace characters directly
        # to avoid high filter rates from assume().
        code=st.one_of(
            st.just(""),
            st.just("   "),
            st.just("\t\t"),
            st.just("\n\n"),
            st.just("  \t  \n  "),
            # Variable-length whitespace strings
            st.integers(min_value=1, max_value=50).flatmap(
                lambda n: st.builds(
                    lambda s, r: s * n,
                    st.sampled_from([" ", "\t", "\n", "\r", "\r\n"]),
                    st.just(None),
                )
            ),
        ),
    )
    @settings(max_examples=150)
    def test_whitespace_only_code_returns_400(self, lang: str, code: str) -> None:
        """Any code string that is empty after strip must return HTTP 400.

        **Property 6: Empty or whitespace-only code is rejected with HTTP 400**
        **Validates: Requirements 3.3**
        """
        # All generated strings are whitespace-only by construction
        # but guard with assume just in case of edge behaviour
        assume(code.strip() == "")

        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, lang, {"code": code})

        self.assertEqual(result["status"], 400,
                         f"Expected 400 for lang={lang!r}, code={code!r}")
        self.assertEqual(result["data"]["status"], "error")
        self.assertIn("code", result["data"]["message"].lower())

    @given(
        lang=st.sampled_from(["r", "python", "julia"]),
    )
    @settings(max_examples=30)
    def test_empty_string_returns_400(self, lang: str) -> None:
        """Explicit empty string must return HTTP 400.

        **Validates: Requirements 3.3**
        """
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, lang, {"code": ""})
        self.assertEqual(result["status"], 400)
        self.assertEqual(result["data"]["status"], "error")

    @given(
        lang=st.sampled_from(["r", "python", "julia"]),
    )
    @settings(max_examples=30)
    def test_missing_code_field_returns_400(self, lang: str) -> None:
        """Missing 'code' key returns HTTP 400.

        **Validates: Requirements 3.3**
        """
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, lang, {})  # no 'code' key
        self.assertEqual(result["status"], 400)
        self.assertEqual(result["data"]["status"], "error")

    @given(
        lang=st.sampled_from(["r", "python", "julia"]),
        spaces=st.integers(min_value=0, max_value=100).map(lambda n: " " * n),
    )
    @settings(max_examples=30)
    def test_space_only_returns_400(self, lang: str, spaces: str) -> None:
        """Pure space string returns HTTP 400.

        **Validates: Requirements 3.3**
        """
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, lang, {"code": spaces})
        self.assertEqual(result["status"], 400)

    @given(
        lang=st.sampled_from(["r", "python", "julia"]),
    )
    @settings(max_examples=30)
    def test_only_newlines_returns_400(self, lang: str) -> None:
        """Code containing only newlines must return HTTP 400."""
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, lang, {"code": "\n\n\n"})
        self.assertEqual(result["status"], 400)

    def test_error_message_exact_text(self) -> None:
        """Error message must be exactly 'Missing \\'code\\' field'."""
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, "r", {"code": "   "})
        self.assertEqual(result["data"]["message"], "Missing 'code' field")

    @given(
        lang=st.sampled_from(["r", "python", "julia"]),
        code=st.text(min_size=1).filter(lambda c: c.strip() != ""),
    )
    @settings(max_examples=50)
    def test_non_empty_code_does_not_return_400_for_missing_code_reason(
        self, lang: str, code: str
    ) -> None:
        """Non-whitespace code is NOT rejected with the 'Missing code' error.

        (It may still fail for other reasons, like 503 when no engine is up.)
        """
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture_response(handler, lang, {"code": code})
        # If status is 400 it must NOT be due to 'Missing code' validation
        if result.get("status") == 400:
            self.assertNotEqual(
                result["data"].get("message"),
                "Missing 'code' field",
                "Non-empty code should not be rejected as 'Missing code'",
            )


if __name__ == "__main__":
    unittest.main()
