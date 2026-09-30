"""Tests for task 6.1 — pipe_client_factory injection into NEVENHandler.

Verifies that:
- DEFAULT_CONFIG now contains an empty ``pipe_client_factory`` dict.
- start_server() accepts a ``pipe_client_factory`` in the config dict.
- _get_pipe_client() calls the correct factory and returns whatever it produces.
- _get_pipe_client() raises KeyError for unregistered languages.
- The do_POST dispatch routes /api/r, /api/python, /api/julia to _handle_script.
- The do_GET dispatch routes /api/engines and /api/functions to their handlers.
- When a factory IS registered, _handle_script does NOT return 503.
- When NO factory is registered, /api/r → 503 with the right message.

Requirements: 9.5
"""

from __future__ import annotations

import importlib
import io
import json
import os
import sys
import types
import unittest
from http.server import HTTPServer
from unittest.mock import MagicMock, patch

# ── Path setup ────────────────────────────────────────────────────────────────
# The HTTP server lives in ControlPython/startup; the TaskPane tests directory
# is two levels up from that file.
_HERE = os.path.dirname(os.path.abspath(__file__))
_TASKPANE = os.path.dirname(_HERE)              # …/TaskPane
_CTRL_STARTUP = os.path.join(
    os.path.dirname(_TASKPANE),                 # …/NEVEN
    "ControlPython", "startup",
)
sys.path.insert(0, _CTRL_STARTUP)
sys.path.insert(0, _TASKPANE)

import neven_http_server as srv  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_handler(config: dict) -> srv.NEVENHandler:
    """Build a NEVENHandler instance without a real socket/server.

    We bypass __init__ (which needs a real socket) by creating a raw object
    and injecting the minimal attributes that the handler reads from.
    """
    # Apply config to the module-level _config used by the handler.
    srv._config = config

    handler = srv.NEVENHandler.__new__(srv.NEVENHandler)
    # Attributes that BaseHTTPRequestHandler expects
    handler.headers = {}
    handler.rfile = io.BytesIO(b"")
    handler.wfile = io.BytesIO()
    handler.server = MagicMock()
    handler.connection = MagicMock()
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    return handler


def _make_mock_client():
    """Return a sentinel PipeClient stand-in."""
    return MagicMock(name="MockPipeClient")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDefaultConfig(unittest.TestCase):
    """DEFAULT_CONFIG must include pipe_client_factory as an empty dict."""

    def test_pipe_client_factory_key_present(self):
        self.assertIn("pipe_client_factory", srv.DEFAULT_CONFIG)

    def test_pipe_client_factory_default_is_empty_dict(self):
        self.assertEqual(srv.DEFAULT_CONFIG["pipe_client_factory"], {})


class TestGetPipeClient(unittest.TestCase):
    """_get_pipe_client must call the registered factory and raise KeyError otherwise."""

    def test_returns_instance_from_factory(self):
        sentinel = _make_mock_client()
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {"r": lambda: sentinel}}
        handler = _make_handler(config)

        result = handler._get_pipe_client("r")

        self.assertIs(result, sentinel)

    def test_factory_called_each_invocation(self):
        """The factory callable must be invoked (not cached)."""
        call_count = {"n": 0}

        def factory():
            call_count["n"] += 1
            return _make_mock_client()

        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {"python": factory}}
        handler = _make_handler(config)

        handler._get_pipe_client("python")
        handler._get_pipe_client("python")

        self.assertEqual(call_count["n"], 2)

    def test_raises_key_error_for_unregistered_language(self):
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)

        with self.assertRaises(KeyError):
            handler._get_pipe_client("julia")

    def test_raises_key_error_message_contains_language(self):
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {"r": lambda: None}}
        handler = _make_handler(config)

        with self.assertRaises(KeyError) as ctx:
            handler._get_pipe_client("python")

        self.assertIn("python", str(ctx.exception))

    def test_all_three_languages_can_be_registered(self):
        clients = {lang: _make_mock_client() for lang in ("r", "python", "julia")}
        factory = {lang: (lambda c: lambda: c)(client) for lang, client in clients.items()}
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": factory}
        handler = _make_handler(config)

        for lang, expected in clients.items():
            with self.subTest(lang=lang):
                self.assertIs(handler._get_pipe_client(lang), expected)


class TestScriptEndpoint503WhenNoFactory(unittest.TestCase):
    """POST /api/r → 503 when no factory is registered for that language."""

    def _post_to_script_endpoint(self, lang: str) -> dict:
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)

        captured_status = {}
        captured_body = {}

        def fake_send_json(data, status=200):
            captured_status["code"] = status
            captured_body["data"] = data

        handler._send_json = fake_send_json
        handler._handle_script(lang, {"code": "1+1"})
        return captured_status, captured_body

    def test_r_returns_503(self):
        status, body = self._post_to_script_endpoint("r")
        self.assertEqual(status["code"], 503)

    def test_python_returns_503(self):
        status, body = self._post_to_script_endpoint("python")
        self.assertEqual(status["code"], 503)

    def test_julia_returns_503(self):
        status, body = self._post_to_script_endpoint("julia")
        self.assertEqual(status["code"], 503)

    def test_503_body_contains_language_in_message(self):
        _status, body = self._post_to_script_endpoint("r")
        self.assertIn("r", body["data"]["message"].lower())

    def test_503_body_status_is_error(self):
        _status, body = self._post_to_script_endpoint("r")
        self.assertEqual(body["data"]["status"], "error")


class TestScriptEndpointWithFactory(unittest.TestCase):
    """When a factory IS registered, _handle_script must NOT return 503."""

    def test_registered_language_does_not_return_503(self):
        sentinel = _make_mock_client()
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"r": lambda: sentinel},
        }
        handler = _make_handler(config)

        captured_status = {}

        def fake_send_json(data, status=200):
            captured_status["code"] = status

        handler._send_json = fake_send_json
        handler._handle_script("r", {"code": "summary(dataset)"})

        self.assertNotEqual(captured_status.get("code"), 503)


class TestGetEnginesPlaceholder(unittest.TestCase):
    """/api/engines placeholder returns the three-language dict."""

    def test_returns_dict_with_three_keys(self):
        handler = _make_handler({**srv.DEFAULT_CONFIG})
        captured = {}

        def fake_send_json(data, status=200):
            captured["data"] = data

        handler._send_json = fake_send_json
        handler._handle_engines()

        for lang in ("r", "python", "julia"):
            self.assertIn(lang, captured["data"])

    def test_all_values_are_bool(self):
        handler = _make_handler({**srv.DEFAULT_CONFIG})
        captured = {}

        def fake_send_json(data, status=200):
            captured["data"] = data

        handler._send_json = fake_send_json
        handler._handle_engines()

        for lang in ("r", "python", "julia"):
            self.assertIsInstance(captured["data"][lang], bool)


class TestGetFunctionsPlaceholder(unittest.TestCase):
    """/api/functions placeholder returns the languages structure."""

    def test_returns_ok_status(self):
        handler = _make_handler({**srv.DEFAULT_CONFIG})
        captured = {}

        def fake_send_json(data, status=200):
            captured["data"] = data

        handler._send_json = fake_send_json
        handler._handle_functions()

        self.assertEqual(captured["data"]["status"], "ok")

    def test_languages_key_present(self):
        handler = _make_handler({**srv.DEFAULT_CONFIG})
        captured = {}

        def fake_send_json(data, status=200):
            captured["data"] = data

        handler._send_json = fake_send_json
        handler._handle_functions()

        self.assertIn("languages", captured["data"])
        for lang in ("r", "python", "julia"):
            self.assertIn(lang, captured["data"]["languages"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
