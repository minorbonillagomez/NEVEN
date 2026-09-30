"""Unit tests for task 7.6: rpivot and engines edge cases.

Tests:
  - /api/rpivot with R engine down → 503 (Req 5.5)
  - /api/rpivot with no dataset → 400 (Req 5.7)
  - /api/functions with no engine running → all empty lists (Req 7.4)
  - Non-Windows _probe_pipe always returns False

Requirements: 5.5, 5.7, 7.4
"""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_TASKPANE = os.path.dirname(_HERE)
_CTRL_STARTUP = os.path.join(os.path.dirname(_TASKPANE), "ControlPython", "startup")
sys.path.insert(0, _CTRL_STARTUP)
sys.path.insert(0, _TASKPANE)

import neven_http_server as srv  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_handler(config: dict | None = None) -> srv.NEVENHandler:
    """Construct a NEVENHandler without a real socket."""
    srv._config = config or {**srv.DEFAULT_CONFIG}
    handler = srv.NEVENHandler.__new__(srv.NEVENHandler)
    handler.headers = {}
    handler.rfile = io.BytesIO(b"")
    handler.wfile = io.BytesIO()
    handler.server = None
    handler.connection = None
    handler.client_address = ("127.0.0.1", 9999)
    return handler


def _capture(handler: srv.NEVENHandler, method: str, body: dict = None) -> dict:
    """Call a handler method and capture the JSON response."""
    captured = {}

    def fake_send_json(data, status=200):
        captured["status"] = status
        captured["data"] = data

    handler._send_json = fake_send_json
    if method == "rpivot":
        handler._handle_rpivot(body or {})
    elif method == "engines":
        handler._handle_engines()
    elif method == "functions":
        handler._handle_functions()
    return captured


# ── 1. /api/rpivot with R engine down → 503 (Req 5.5) ────────────────────────

class TestRPivotREngineDown(unittest.TestCase):
    """/api/rpivot with R engine down → 503 (Req 5.5)."""

    def test_r_engine_down_returns_503(self):
        """When _probe_pipe returns False for R, /api/rpivot returns 503."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=False):
            result = _capture(handler, "rpivot")

        self.assertEqual(result["status"], 503)

    def test_r_engine_down_body_status_is_error(self):
        """503 body has status: 'error'."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=False):
            result = _capture(handler, "rpivot")

        self.assertEqual(result["data"]["status"], "error")

    def test_r_engine_down_message_mentions_r(self):
        """503 message mentions 'R' or 'engine'."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=False):
            result = _capture(handler, "rpivot")

        msg = result["data"]["message"].lower()
        self.assertTrue("r" in msg or "engine" in msg,
                        f"Expected 'R' or 'engine' in message: {msg!r}")

    def test_r_engine_down_no_factory_also_503(self):
        """Even with no factory registered, R engine down → 503."""
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)

        with patch.object(srv, "_probe_pipe", return_value=False):
            result = _capture(handler, "rpivot")

        self.assertEqual(result["status"], 503)


# ── 2. /api/rpivot with no dataset → 400 (Req 5.7) ───────────────────────────

class TestRPivotNoDataset(unittest.TestCase):
    """/api/rpivot with no dataset loaded → 400 (Req 5.7)."""

    def test_no_dataset_returns_400(self):
        """When DuckDB has no 'dataset' table, /api/rpivot returns 400."""
        handler = _make_handler()

        # Simulate R engine up but no dataset
        with patch.object(srv, "_probe_pipe", return_value=True):
            # Drop the dataset table to ensure it's absent
            try:
                db = srv._get_db()
                db.execute("DROP TABLE IF EXISTS dataset")
            except Exception:
                pass
            result = _capture(handler, "rpivot")

        self.assertEqual(result["status"], 400)

    def test_no_dataset_body_status_is_error(self):
        """400 body has status: 'error'."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=True):
            try:
                db = srv._get_db()
                db.execute("DROP TABLE IF EXISTS dataset")
            except Exception:
                pass
            result = _capture(handler, "rpivot")

        self.assertEqual(result["data"]["status"], "error")

    def test_no_dataset_message_mentions_dataset(self):
        """400 message mentions 'dataset' or 'load'."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=True):
            try:
                db = srv._get_db()
                db.execute("DROP TABLE IF EXISTS dataset")
            except Exception:
                pass
            result = _capture(handler, "rpivot")

        msg = result["data"]["message"].lower()
        self.assertTrue("dataset" in msg or "load" in msg,
                        f"Expected 'dataset' or 'load' in message: {msg!r}")

    def test_engine_up_but_no_dataset_is_400_not_503(self):
        """With R engine up but no dataset, response is 400, not 503."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=True):
            try:
                db = srv._get_db()
                db.execute("DROP TABLE IF EXISTS dataset")
            except Exception:
                pass
            result = _capture(handler, "rpivot")

        self.assertNotEqual(result["status"], 503)
        self.assertEqual(result["status"], 400)


# ── 3. /api/functions with no engine running → all empty (Req 7.4) ────────────

class TestFunctionsNoEngineAllEmpty(unittest.TestCase):
    """/api/functions with no engine running → all empty lists (Req 7.4)."""

    def test_no_factory_all_lists_empty(self):
        """With empty pipe_client_factory, all three languages return []."""
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)
        result = _capture(handler, "functions")

        langs = result["data"]["languages"]
        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                self.assertEqual(langs[lang], [])

    def test_no_factory_response_status_is_ok(self):
        """Response status is 'ok' even when no engine is running."""
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)
        result = _capture(handler, "functions")
        self.assertEqual(result["data"]["status"], "ok")

    def test_no_factory_all_three_keys_present(self):
        """Response includes r, python, julia keys even with no factory."""
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)
        result = _capture(handler, "functions")

        langs = result["data"]["languages"]
        for lang in ("r", "python", "julia"):
            self.assertIn(lang, langs)

    def test_pipe_client_error_also_yields_empty(self):
        """PipeClientError from a registered factory returns [] (Req 7.4)."""
        error_client = MagicMock()
        error_client.send_function_call.side_effect = srv._PipeClientError("failed")
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {
                "r": lambda: error_client,
                "python": lambda: error_client,
                "julia": lambda: error_client,
            },
        }
        handler = _make_handler(config)
        result = _capture(handler, "functions")

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                self.assertEqual(result["data"]["languages"][lang], [])


# ── 4. Non-Windows _probe_pipe always returns False ───────────────────────────

class TestNonWindowsProbe(unittest.TestCase):
    """_probe_pipe on non-Windows always returns False."""

    def test_probe_pipe_non_windows_returns_false(self):
        """When _WIN32_AVAILABLE is False, _probe_pipe returns False."""
        with patch.object(srv, "_WIN32_AVAILABLE", False):
            result = srv._probe_pipe(r"\\.\pipe\neven_r")
        self.assertFalse(result)

    def test_probe_pipe_non_windows_all_languages(self):
        """_probe_pipe returns False for all three pipe names on non-Windows."""
        with patch.object(srv, "_WIN32_AVAILABLE", False):
            for lang in ("r", "python", "julia"):
                pipe = rf"\\.\pipe\neven_{lang}"
                with self.subTest(lang=lang):
                    self.assertFalse(srv._probe_pipe(pipe))

    def test_engines_endpoint_all_false_on_non_windows(self):
        """GET /api/engines returns all False when probe always returns False."""
        handler = _make_handler()

        with patch.object(srv, "_probe_pipe", return_value=False):
            result = _capture(handler, "engines")

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                self.assertFalse(result["data"][lang])

    def test_probe_returns_bool_not_truthy(self):
        """_probe_pipe must return a Python bool, not a truthy/falsy value."""
        with patch.object(srv, "_WIN32_AVAILABLE", False):
            result = srv._probe_pipe(r"\\.\pipe\neven_r")
        self.assertIs(type(result), bool)


if __name__ == "__main__":
    unittest.main()
