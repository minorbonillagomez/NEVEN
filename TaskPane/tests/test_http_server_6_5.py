"""Unit tests for task 6.5: script endpoint error paths.

Tests:
  - No PipeClient registered → 503 (Req 3.10)
  - PipeClientError → 200 with status: error (Req 3.8)
  - PipeTimeoutError → 408 (Req 3.9)
  - Broken pipe → one reconnect attempt before 503 (Req 8.4)

Requirements: 3.8, 3.9, 3.10, 8.4
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

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


def _capture(handler: srv.NEVENHandler, lang: str, body: dict) -> dict:
    """Call _handle_script and capture the JSON response."""
    captured: dict = {}

    def fake_send_json(data, status=200):
        captured["status"] = status
        captured["data"] = data

    handler._send_json = fake_send_json
    handler._handle_script(lang, body)
    return captured


def _make_mock_client():
    """Return a minimal mock PipeClient."""
    client = MagicMock()
    client._handle = MagicMock()  # non-None so rpivot lazy-connect doesn't trigger
    return client


# ── 1. No PipeClient → 503 (Req 3.10) ────────────────────────────────────────

class TestNoPipeClientReturns503(unittest.TestCase):
    """When no factory is registered, _handle_script returns 503 (Req 3.10)."""

    def _check_503(self, lang: str):
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture(handler, lang, {"code": "1 + 1"})
        self.assertEqual(result["status"], 503)
        self.assertEqual(result["data"]["status"], "error")
        self.assertIn(lang, result["data"]["message"].lower())

    def test_r_no_factory_503(self):
        self._check_503("r")

    def test_python_no_factory_503(self):
        self._check_503("python")

    def test_julia_no_factory_503(self):
        self._check_503("julia")

    def test_503_message_contains_engine_not_available(self):
        handler = _make_handler({**srv.DEFAULT_CONFIG, "pipe_client_factory": {}})
        result = _capture(handler, "r", {"code": "summary(x)"})
        self.assertIn("not available", result["data"]["message"].lower())


# ── 2. PipeClientError → 200 with status:error (Req 3.8) ─────────────────────

class TestPipeClientErrorReturns200Error(unittest.TestCase):
    """PipeClientError → HTTP 200 with status: error (Req 3.8)."""

    def _make_error_client(self, error_msg: str = "R error: object not found"):
        client = _make_mock_client()
        client.send_code.side_effect = srv._PipeClientError(error_msg)
        return client

    def test_pipe_client_error_returns_200(self):
        """PipeClientError → HTTP status 200 (Req 3.8)."""
        client = self._make_error_client("syntax error")
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"r": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "r", {"code": "bad code{"})
        self.assertEqual(result["status"], 200)

    def test_pipe_client_error_body_status_is_error(self):
        """Response body has status: 'error' for PipeClientError."""
        client = self._make_error_client("division by zero")
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"python": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "python", {"code": "1/0"})
        self.assertEqual(result["data"]["status"], "error")

    def test_pipe_client_error_message_propagated(self):
        """The error text from PipeClientError is in the response message."""
        error_msg = "custom error message xyz"
        client = self._make_error_client(error_msg)
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"julia": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "julia", {"code": "x = undefined_var"})
        self.assertEqual(result["data"]["message"], error_msg)

    def test_all_three_languages_handle_pipe_client_error(self):
        """PipeClientError behaviour is consistent across all three languages."""
        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                client = self._make_error_client(f"{lang} error")
                config = {
                    **srv.DEFAULT_CONFIG,
                    "pipe_client_factory": {lang: lambda c=client: c},
                }
                handler = _make_handler(config)
                result = _capture(handler, lang, {"code": "error()"})
                self.assertEqual(result["status"], 200)
                self.assertEqual(result["data"]["status"], "error")


# ── 3. PipeTimeoutError → 408 (Req 3.9) ──────────────────────────────────────

class TestPipeTimeoutErrorReturns408(unittest.TestCase):
    """PipeTimeoutError → HTTP 408 (Req 3.9)."""

    def _make_timeout_client(self):
        client = _make_mock_client()
        client.send_code.side_effect = srv._PipeTimeoutError("timed out")
        return client

    def test_timeout_error_returns_408(self):
        """PipeTimeoutError → HTTP status 408."""
        client = self._make_timeout_client()
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"r": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "r", {"code": "Sys.sleep(9999)"})
        self.assertEqual(result["status"], 408)

    def test_timeout_error_body_status_is_error(self):
        """Timeout response body has status: 'error'."""
        client = self._make_timeout_client()
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"python": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "python", {"code": "import time; time.sleep(9999)"})
        self.assertEqual(result["data"]["status"], "error")

    def test_timeout_message_mentions_timeout(self):
        """Timeout response message mentions 'timed out'."""
        client = self._make_timeout_client()
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"julia": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "julia", {"code": "sleep(9999)"})
        self.assertIn("timed out", result["data"]["message"].lower())

    def test_all_three_languages_handle_timeout(self):
        """Timeout behaviour is consistent across all three languages."""
        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                client = self._make_timeout_client()
                config = {
                    **srv.DEFAULT_CONFIG,
                    "pipe_client_factory": {lang: lambda c=client: c},
                }
                handler = _make_handler(config)
                result = _capture(handler, lang, {"code": "sleep_forever()"})
                self.assertEqual(result["status"], 408)


# ── 4. Broken pipe → one reconnect attempt before 503 (Req 8.4) ──────────────

class TestBrokenPipeReconnect(unittest.TestCase):
    """Broken pipe triggers one reconnect attempt before returning 503 (Req 8.4)."""

    def test_broken_pipe_triggers_reconnect_then_503(self):
        """When first send_code raises OSError (broken pipe), connect() is called once.

        If the reconnect also fails, the response is 503 (Req 8.4).
        """
        call_log = []

        client = MagicMock()
        client._handle = MagicMock()

        def _send_code_fail(*args, **kwargs):
            call_log.append("send_code")
            raise OSError("broken pipe: connection lost")

        client.send_code.side_effect = _send_code_fail
        client.close.side_effect = lambda: call_log.append("close")
        client.connect.side_effect = lambda: call_log.append("connect")

        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"r": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "r", {"code": "1 + 1"})

        # Must have called close() then connect() (the one reconnect)
        self.assertIn("close", call_log)
        self.assertIn("connect", call_log)

        # After reconnect also fails (send_code still raises), response is 503
        self.assertEqual(result["status"], 503)

    def test_broken_pipe_only_one_reconnect_attempt(self):
        """Only exactly ONE reconnect is attempted before giving up."""
        reconnect_count = {"n": 0}

        client = MagicMock()
        client._handle = MagicMock()
        client.send_code.side_effect = OSError("broken pipe")

        def _count_connect():
            reconnect_count["n"] += 1

        client.connect.side_effect = _count_connect
        client.close.return_value = None

        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"python": lambda: client},
        }
        handler = _make_handler(config)
        _capture(handler, "python", {"code": "print('x')"})

        self.assertEqual(reconnect_count["n"], 1,
                         "Exactly one reconnect attempt should be made")

    def test_successful_reconnect_returns_result(self):
        """When reconnect succeeds, the result is returned normally."""
        from unittest.mock import MagicMock as MM

        call_count = {"n": 0}

        # Simulate a real Variable-like return (just use a mock that variable_to_python handles)
        # We'll patch _variable_to_python to return a simple value.
        client = MM()
        client._handle = MM()

        def _send_code_side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise OSError("pipe closed")
            # Second call succeeds
            return MM()  # Mock variable

        client.send_code.side_effect = _send_code_side_effect
        client.close.return_value = None
        client.connect.return_value = None

        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"julia": lambda: client},
        }
        handler = _make_handler(config)

        # Patch variable_to_python to return a simple value so _send_script_result works
        with patch.object(srv, "_variable_to_python", return_value="hello"):
            result = _capture(handler, "julia", {"code": "println('hi')"})

        # On successful reconnect, response should NOT be 503
        self.assertNotEqual(result.get("status"), 503)

    def test_pipe_client_error_on_broken_pipe_message_triggers_reconnect(self):
        """PipeClientError with 'broken pipe' in message also triggers reconnect."""
        call_log = []

        client = MagicMock()
        client._handle = MagicMock()

        def _fail_send(*args, **kwargs):
            raise srv._PipeClientError("pipe closed unexpectedly")

        client.send_code.side_effect = _fail_send
        client.close.side_effect = lambda: call_log.append("close")
        client.connect.side_effect = lambda: call_log.append("connect")

        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"r": lambda: client},
        }
        handler = _make_handler(config)
        result = _capture(handler, "r", {"code": "x <- 1"})

        # Should have attempted a reconnect
        self.assertIn("connect", call_log)


if __name__ == "__main__":
    unittest.main()
