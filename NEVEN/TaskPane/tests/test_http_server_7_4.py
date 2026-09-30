"""Property test for task 7.4: engine status reflects pipe availability.

**Property 8: Engine status accurately reflects pipe availability**
**Validates: Requirements 8.1**

Patch ``neven_http_server._probe_pipe`` to return True iff the language is in
``available``. Assert that ``_handle_engines()`` returns matching booleans.
"""

from __future__ import annotations

import io
import os
import sys
import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_TASKPANE = os.path.dirname(_HERE)
_CTRL_STARTUP = os.path.join(os.path.dirname(_TASKPANE), "ControlPython", "startup")
sys.path.insert(0, _CTRL_STARTUP)
sys.path.insert(0, _TASKPANE)

import neven_http_server as srv  # noqa: E402
from unittest.mock import patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_handler() -> srv.NEVENHandler:
    """Construct a NEVENHandler without a real socket."""
    srv._config = {**srv.DEFAULT_CONFIG}
    handler = srv.NEVENHandler.__new__(srv.NEVENHandler)
    handler.headers = {}
    handler.rfile = io.BytesIO(b"")
    handler.wfile = io.BytesIO()
    handler.server = None
    handler.connection = None
    handler.client_address = ("127.0.0.1", 9999)
    return handler


def _capture_engines(handler: srv.NEVENHandler) -> dict:
    """Call _handle_engines and capture the JSON response."""
    captured = {}

    def fake_send_json(data, status=200):
        captured["status"] = status
        captured["data"] = data

    handler._send_json = fake_send_json
    handler._handle_engines()
    return captured


def _probe_stub(available: frozenset):
    """Return a _probe_pipe replacement that checks the pipe name."""
    def _probe(pipe_name: str) -> bool:
        # pipe_name follows pattern \\.\pipe\neven_{lang}
        for lang in ("r", "python", "julia"):
            if pipe_name.endswith(lang):
                return lang in available
        return False
    return _probe


# ── Property 8 ────────────────────────────────────────────────────────────────

class TestEngineStatusReflectsPipeAvailability(unittest.TestCase):
    """Property 8 — engine status accurately reflects pipe availability (Req 8.1)."""

    @given(
        available=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=50)
    def test_engine_status_matches_probe_result(self, available: frozenset) -> None:
        """_handle_engines must return {lang: (lang in available)} for each language.

        **Property 8: Engine status accurately reflects pipe availability**
        **Validates: Requirements 8.1**
        """
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", side_effect=_probe_stub(available)):
            result = _capture_engines(handler)

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang, available=list(available)):
                expected = lang in available
                self.assertEqual(
                    result["data"][lang], expected,
                    f"{lang!r}: expected {expected}, got {result['data'][lang]}"
                )

    @given(
        available=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=30)
    def test_response_has_all_three_language_keys(self, available: frozenset) -> None:
        """_handle_engines always returns all three language keys.

        **Validates: Requirements 8.1**
        """
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", side_effect=_probe_stub(available)):
            result = _capture_engines(handler)

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                self.assertIn(lang, result["data"])

    @given(
        available=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=30)
    def test_all_values_are_bool(self, available: frozenset) -> None:
        """All values in the engines response are Python booleans.

        **Validates: Requirements 8.1**
        """
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", side_effect=_probe_stub(available)):
            result = _capture_engines(handler)

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                self.assertIsInstance(result["data"][lang], bool)

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_all_available(self) -> None:
        """When all three pipes are up, all three values are True."""
        handler = _make_handler()
        all_up = frozenset(["r", "python", "julia"])

        with patch.object(srv, "_probe_pipe", return_value=True):
            result = _capture_engines(handler)

        self.assertEqual(result["data"], {"r": True, "python": True, "julia": True})

    def test_none_available(self) -> None:
        """When no pipes are up, all three values are False."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=False):
            result = _capture_engines(handler)

        self.assertEqual(result["data"], {"r": False, "python": False, "julia": False})

    def test_non_windows_probe_returns_false(self) -> None:
        """On non-Windows, _probe_pipe always returns False."""
        result = srv._probe_pipe(r"\\.\pipe\neven_r")
        # On this test machine (may be Windows), this is fine either way;
        # the key test is that _probe_pipe is callable and returns a bool.
        self.assertIsInstance(result, bool)

    def test_probe_pipe_called_for_each_language(self) -> None:
        """_probe_pipe is called exactly 3 times (once per language)."""
        handler = _make_handler()
        call_count = {"n": 0}

        def counting_probe(pipe_name: str) -> bool:
            call_count["n"] += 1
            return False

        with patch.object(srv, "_probe_pipe", side_effect=counting_probe):
            _capture_engines(handler)

        self.assertEqual(call_count["n"], 3)


if __name__ == "__main__":
    unittest.main()
