"""Property test for task 7.5: /api/functions returns empty lists for stopped engines.

**Property 9: /api/functions returns lists for running engines, empty for stopped ones**
**Validates: Requirements 7.3, 7.4**

Register mock PipeClient factories only for ``running`` languages.
Assert: running langs return a list (possibly []), others return [].
"""

from __future__ import annotations

import io
import os
import sys
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


def _capture_functions(handler: srv.NEVENHandler) -> dict:
    """Call _handle_functions and capture the JSON response."""
    captured = {}

    def fake_send_json(data, status=200):
        captured["status"] = status
        captured["data"] = data

    handler._send_json = fake_send_json
    handler._handle_functions()
    return captured


def _make_function_client(functions: list | None = None):
    """Return a mock PipeClient that returns a list of function descriptors."""
    # variable_to_python returns {"columns": ["name", "description"], "rows": [...]}
    # for arr variables.
    if functions is None:
        functions = [{"name": "test_fn", "description": "A test function"}]

    mock_var = MagicMock()
    mock_client = MagicMock()

    rows = [[fn["name"], fn.get("description", "")] for fn in functions]
    mock_client.send_function_call.return_value = mock_var

    return mock_client, mock_var, rows


def _make_error_client():
    """Return a mock PipeClient whose send_function_call raises PipeClientError."""
    client = MagicMock()
    client.send_function_call.side_effect = srv._PipeClientError("engine down")
    return client


# ── Property 9 ────────────────────────────────────────────────────────────────

class TestFunctionsEmptyForStoppedEngines(unittest.TestCase):
    """Property 9 — /api/functions returns [] for stopped, list for running (Req 7.3, 7.4)."""

    @given(
        running=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=50)
    def test_stopped_engines_return_empty_list(self, running: frozenset) -> None:
        """Languages NOT in running return [] in the functions response.

        **Property 9: /api/functions returns lists for running engines, empty for stopped**
        **Validates: Requirements 7.3, 7.4**
        """
        # Register factories only for running languages
        factory = {
            lang: (lambda l=lang: _make_function_client()[0])
            for lang in running
        }
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": factory}
        handler = _make_handler(config)

        # Patch variable_to_python to return a proper arr structure
        def _vtp(var):
            return {"columns": ["name", "description"], "rows": [["fn1", "desc1"]]}

        with patch.object(srv, "_variable_to_python", side_effect=_vtp):
            # Also need to patch the import inside _handle_functions
            with patch("neven_http_server.NEVENHandler._get_pipe_client",
                       side_effect=handler._get_pipe_client):
                result = _capture_functions(handler)

        # Languages NOT running must have empty list
        stopped = {"r", "python", "julia"} - set(running)
        for lang in stopped:
            with self.subTest(lang=lang, running=list(running)):
                self.assertEqual(
                    result["data"]["languages"][lang], [],
                    f"Stopped {lang!r} should return []"
                )

    @given(
        running=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=50)
    def test_running_engines_return_list_type(self, running: frozenset) -> None:
        """Languages in running return a list (possibly empty) in the response.

        **Property 9**
        **Validates: Requirements 7.3, 7.4**
        """
        # Build factory — running clients succeed
        factory = {}
        for lang in running:
            client = MagicMock()
            client.send_function_call.return_value = MagicMock()
            factory[lang] = (lambda c=client: c)

        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": factory}
        handler = _make_handler(config)

        def _vtp(var):
            return {"columns": ["name", "description"], "rows": [["my_fn", "does stuff"]]}

        with patch.object(srv, "_variable_to_python", side_effect=_vtp):
            result = _capture_functions(handler)

        for lang in running:
            with self.subTest(lang=lang):
                self.assertIsInstance(
                    result["data"]["languages"][lang], list,
                    f"Running {lang!r} should return a list"
                )

    @given(
        running=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=30)
    def test_response_always_has_all_three_keys(self, running: frozenset) -> None:
        """The languages dict always has r, python, and julia keys.

        **Validates: Requirements 7.3, 7.4**
        """
        factory = {lang: (lambda: MagicMock()) for lang in running}
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": factory}
        handler = _make_handler(config)

        with patch.object(srv, "_variable_to_python", return_value={"columns": [], "rows": []}):
            result = _capture_functions(handler)

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                self.assertIn(lang, result["data"]["languages"])

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_no_engines_all_empty(self) -> None:
        """When no factory registered, all three languages return [].

        **Validates: Requirements 7.4**
        """
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)
        result = _capture_functions(handler)
        langs = result["data"]["languages"]
        self.assertEqual(langs["r"], [])
        self.assertEqual(langs["python"], [])
        self.assertEqual(langs["julia"], [])

    def test_pipe_client_error_returns_empty_list(self) -> None:
        """PipeClientError during list-functions returns [] for that language (Req 7.4)."""
        error_client = _make_error_client()
        config = {
            **srv.DEFAULT_CONFIG,
            "pipe_client_factory": {"r": lambda: error_client},
        }
        handler = _make_handler(config)
        result = _capture_functions(handler)
        self.assertEqual(result["data"]["languages"]["r"], [])

    def test_all_running_returns_functions(self) -> None:
        """When all three engines run, all three return a non-empty list."""
        factory = {}
        for lang in ("r", "python", "julia"):
            client = MagicMock()
            client.send_function_call.return_value = MagicMock()
            factory[lang] = (lambda c=client: c)

        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": factory}
        handler = _make_handler(config)

        # _handle_functions imports variable_to_python locally from pipe_client.
        # Patch the function in the pipe_client module (the source), and also
        # patch the module-level alias so both import paths are covered.
        arr_result = {"columns": ["name", "description"], "rows": [["fn_x", "desc"]]}

        def _vtp(var):
            return arr_result

        # Patch both the local import path and the module-level alias
        try:
            import pipe_client as _pc
            with patch.object(_pc, "variable_to_python", side_effect=_vtp), \
                 patch.object(srv, "_variable_to_python", side_effect=_vtp):
                result = _capture_functions(handler)
        except ImportError:
            with patch.object(srv, "_variable_to_python", side_effect=_vtp):
                result = _capture_functions(handler)

        for lang in ("r", "python", "julia"):
            with self.subTest(lang=lang):
                funcs = result["data"]["languages"][lang]
                self.assertIsInstance(funcs, list)
                self.assertGreater(len(funcs), 0)

    def test_response_status_is_ok(self) -> None:
        """Response body always has status: 'ok'."""
        config = {**srv.DEFAULT_CONFIG, "pipe_client_factory": {}}
        handler = _make_handler(config)
        result = _capture_functions(handler)
        self.assertEqual(result["data"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
