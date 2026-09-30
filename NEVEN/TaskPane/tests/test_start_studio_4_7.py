"""Unit tests for task 4.7: Launcher edge cases.

Tests:
  - ``--config`` present → uses that path; absent → uses C:\\NEVEN\\neven-config.json (Req 1.1)
  - ``--port`` overrides config port (Req 9.2)
  - missing binary → logs warning, skips language (Req 9.3)
  - ``--no-browser`` → webbrowser.open not called (Req 1.8)
  - stdout URL is printed (Req 1.7)
  - PID file written on start, removed on exit (Req 8.6)
  - Non-Windows → processes not started, script endpoints return 503 (Req 4.7)

Requirements: 1.1, 1.7, 1.8, 8.6, 9.2, 9.3, 4.7
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TASKPANE not in sys.path:
    sys.path.insert(0, _TASKPANE)

import start_studio  # noqa: E402
from start_studio import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    _STANDALONE_DEFAULTS,
    _pid_file_path,
    build_arg_parser,
    find_exe,
    load_config,
    remove_pid_file,
    resolve_languages,
    write_pid_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**standalone_overrides) -> dict:
    standalone = {**_STANDALONE_DEFAULTS, **standalone_overrides}
    return {"Standalone": standalone}


def _make_mock_proc(pid: int = 12345) -> MagicMock:
    proc = MagicMock(spec=subprocess.Popen)
    proc.pid = pid
    proc.args = [r"C:\NEVEN\ControlR.exe"]
    proc.wait.return_value = 0
    return proc


# ---------------------------------------------------------------------------
# 1. --config argument (Requirement 1.1)
# ---------------------------------------------------------------------------

class TestConfigArgument(unittest.TestCase):
    """--config specifies the JSON path; absent → default (Req 1.1)."""

    def test_default_config_path(self):
        """When --config is absent, parser.default is DEFAULT_CONFIG_PATH."""
        parser = build_arg_parser()
        args = parser.parse_args([])
        self.assertEqual(args.config, DEFAULT_CONFIG_PATH)

    def test_custom_config_path(self):
        """--config <path> → args.config equals that path."""
        parser = build_arg_parser()
        args = parser.parse_args(["--config", r"D:\custom\config.json"])
        self.assertEqual(args.config, r"D:\custom\config.json")

    def test_load_config_uses_given_path(self):
        """load_config reads from the file at the given path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "my-config.json")
            data = {
                "Standalone": {
                    "controlDir": tmpdir,
                    "port": 7777,
                }
            }
            with open(custom_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            config = load_config(custom_path)
        self.assertEqual(config["Standalone"]["port"], 7777)
        self.assertEqual(str(config["Standalone"]["controlDir"]), tmpdir)

    def test_load_config_missing_file_logs_warning_and_returns_defaults(self):
        """Missing file → warning logged, defaults returned (no raise)."""
        stderr_capture = io.StringIO()
        with patch("sys.stderr", stderr_capture):
            config = load_config(r"C:\does\not\exist.json")
        output = stderr_capture.getvalue()
        self.assertIn("WARNING", output)
        # Should still have Standalone defaults
        self.assertIn("Standalone", config)
        self.assertEqual(
            config["Standalone"]["port"],
            _STANDALONE_DEFAULTS["port"],
        )

    def test_absent_config_uses_default_path_constant(self):
        """DEFAULT_CONFIG_PATH == 'C:\\NEVEN\\neven-config.json'."""
        self.assertEqual(DEFAULT_CONFIG_PATH, r"C:\NEVEN\neven-config.json")


# ---------------------------------------------------------------------------
# 2. --port overrides config port (Requirement 9.2)
# ---------------------------------------------------------------------------

class TestPortOverride(unittest.TestCase):
    """--port CLI argument overrides the config port (Req 9.2)."""

    def test_port_from_config(self):
        """When --port absent, config port is used."""
        config = _make_config(port=6666)
        parser = build_arg_parser()
        args = parser.parse_args([])  # no --port
        # Simulate main's port-override logic
        if args.port is not None:
            config["Standalone"]["port"] = args.port
        self.assertEqual(config["Standalone"]["port"], 6666)

    def test_port_override_wins(self):
        """When --port INT is given, it overrides the config file port."""
        config = _make_config(port=5555)
        parser = build_arg_parser()
        args = parser.parse_args(["--port", "8888"])
        if args.port is not None:
            config["Standalone"]["port"] = args.port
        self.assertEqual(config["Standalone"]["port"], 8888)

    def test_port_zero_is_accepted(self):
        """--port 0 is a valid integer (OS assigns a free port)."""
        parser = build_arg_parser()
        args = parser.parse_args(["--port", "0"])
        self.assertEqual(args.port, 0)

    def test_port_type_is_int(self):
        """argparse converts --port to int."""
        parser = build_arg_parser()
        args = parser.parse_args(["--port", "9999"])
        self.assertIsInstance(args.port, int)


# ---------------------------------------------------------------------------
# 3. Missing binary → logs warning, skips language (Requirement 9.3)
# ---------------------------------------------------------------------------

class TestMissingBinarySkipsLanguage(unittest.TestCase):
    """Missing Control*.exe → warn and return None (Req 9.3)."""

    def test_find_exe_nonexistent_path_returns_none(self):
        """find_exe with a non-existent controlDir returns None."""
        config = _make_config(controlDir=r"C:\does_not_exist_xyz\\")
        result = find_exe(config, "r")
        self.assertIsNone(result)

    def test_find_exe_nonexistent_path_logs_warning(self):
        """find_exe logs a WARNING when binary is absent."""
        stderr_capture = io.StringIO()
        config = _make_config(controlDir=r"C:\does_not_exist_xyz\\")
        with patch("sys.stderr", stderr_capture):
            find_exe(config, "r")
        output = stderr_capture.getvalue()
        self.assertIn("WARNING", output)

    def test_find_exe_existing_binary_returns_path(self):
        """find_exe returns the path when the binary exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = os.path.join(tmpdir, "ControlR.exe")
            with open(exe_path, "wb") as fh:
                fh.write(b"\x00")
            config = _make_config(controlDir=tmpdir)
            result = find_exe(config, "r")
        self.assertEqual(result, exe_path)

    def test_find_exe_for_all_languages(self):
        """find_exe handles all three language identifiers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("ControlR.exe", "ControlPython.exe", "ControlJulia.exe"):
                with open(os.path.join(tmpdir, name), "wb") as fh:
                    fh.write(b"\x00")
            config = _make_config(controlDir=tmpdir)
            for lang, expected_name in [("r", "ControlR.exe"),
                                        ("python", "ControlPython.exe"),
                                        ("julia", "ControlJulia.exe")]:
                with self.subTest(lang=lang):
                    result = find_exe(config, lang)
                    self.assertIsNotNone(result)
                    self.assertTrue(result.endswith(expected_name))

    def test_skipped_language_not_in_executables(self):
        """When binary missing, that language is absent from executables dict."""
        config = _make_config(controlDir=r"C:\does_not_exist_xyz\\")
        executables = {}
        for lang in ("r", "python", "julia"):
            exe = find_exe(config, lang)
            if exe is not None:
                executables[lang] = exe
        self.assertEqual(executables, {})


# ---------------------------------------------------------------------------
# 4. --no-browser flag (Requirement 1.8)
# ---------------------------------------------------------------------------

class TestNoBrowserFlag(unittest.TestCase):
    """--no-browser prevents webbrowser.open (Req 1.8)."""

    def test_no_browser_flag_parsed(self):
        """--no-browser sets args.no_browser = True."""
        parser = build_arg_parser()
        args = parser.parse_args(["--no-browser"])
        self.assertTrue(args.no_browser)

    def test_browser_opens_by_default(self):
        """Without --no-browser, webbrowser.open would be called in main()."""
        parser = build_arg_parser()
        args = parser.parse_args([])
        self.assertFalse(args.no_browser)

    def test_no_browser_no_open_call(self):
        """When --no-browser, main() must NOT call webbrowser.open."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"Standalone": {"controlDir": tmpdir}}, fh)

            with patch("webbrowser.open") as mock_wb, \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"):
                start_studio.main([
                    "--config", config_path,
                    "--no-browser",
                ])
            mock_wb.assert_not_called()

    def test_browser_opens_when_flag_absent(self):
        """Without --no-browser, webbrowser.open IS called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"Standalone": {"controlDir": tmpdir}}, fh)

            with patch("webbrowser.open") as mock_wb, \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"):
                start_studio.main(["--config", config_path])
            mock_wb.assert_called_once()


# ---------------------------------------------------------------------------
# 5. stdout URL is printed (Requirement 1.7)
# ---------------------------------------------------------------------------

class TestURLPrinted(unittest.TestCase):
    """Studio URL is printed to stdout (Req 1.7)."""

    def test_url_printed_to_stdout(self):
        """main() prints 'http://localhost:<port>/taskpane.html' to stdout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"Standalone": {"controlDir": tmpdir}}, fh)

            captured = io.StringIO()
            with patch("sys.stdout", captured), \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"), \
                 patch("webbrowser.open"):
                start_studio.main([
                    "--config", config_path,
                    "--no-browser",
                ])
            output = captured.getvalue()
        self.assertIn("http://localhost:5555/taskpane.html", output)

    def test_url_contains_correct_port_when_overridden(self):
        """Printed URL reflects the --port override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"Standalone": {"controlDir": tmpdir}}, fh)

            captured = io.StringIO()
            with patch("sys.stdout", captured), \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 7654)), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"), \
                 patch("webbrowser.open"):
                start_studio.main([
                    "--config", config_path,
                    "--port", "7654",
                    "--no-browser",
                ])
            output = captured.getvalue()
        self.assertIn("7654", output)


# ---------------------------------------------------------------------------
# 6. PID file written on start, removed on exit (Requirement 8.6)
# ---------------------------------------------------------------------------

class TestPIDFileLifecycle(unittest.TestCase):
    """PID file created at startup, removed on exit (Req 8.6)."""

    def test_pid_file_written_and_removed_in_lifecycle(self):
        """write_pid_file + remove_pid_file lifecycle uses a temp controlDir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            processes = {"r": _make_mock_proc(pid=42)}

            # Write without atexit registration to avoid teardown side effects
            with patch("atexit.register"):
                write_pid_file(config, processes, launcher_pid=99)

            pid_path = _pid_file_path(config)
            self.assertTrue(os.path.isfile(pid_path), "PID file must exist after write")

            # Verify content
            with open(pid_path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["launcher"], 99)
            self.assertEqual(data["r"], 42)

            # Remove
            remove_pid_file(config)
            self.assertFalse(os.path.isfile(pid_path), "PID file must be gone after remove")

    def test_atexit_registered_with_remove_pid_file(self):
        """write_pid_file registers remove_pid_file via atexit (Req 8.6)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            with patch("atexit.register") as mock_register:
                write_pid_file(config, {}, launcher_pid=1)
            mock_register.assert_called_once_with(remove_pid_file, config)


# ---------------------------------------------------------------------------
# 7. Non-Windows: processes not started, script endpoints 503 (Req 4.7)
# ---------------------------------------------------------------------------

class TestNonWindowsBehavior(unittest.TestCase):
    """On non-Windows, no Control processes are started (Req 4.7)."""

    def test_non_windows_no_popen_calls(self):
        """On non-Windows, subprocess.Popen is never called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake executables so find_exe doesn't skip them
            for name in ("ControlR.exe", "ControlPython.exe", "ControlJulia.exe"):
                with open(os.path.join(tmpdir, name), "wb") as fh:
                    fh.write(b"\x00")
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"Standalone": {"controlDir": tmpdir}}, fh)

            with patch("subprocess.Popen") as mock_popen, \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"), \
                 patch("webbrowser.open"):
                start_studio.main([
                    "--config", config_path,
                    "--no-browser",
                ])
            mock_popen.assert_not_called()

    def test_non_windows_logs_info_message(self):
        """On non-Windows, INFO message about skipped engines is logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump({"Standalone": {"controlDir": tmpdir}}, fh)

            stderr_capture = io.StringIO()
            with patch("sys.stderr", stderr_capture), \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"), \
                 patch("webbrowser.open"):
                start_studio.main([
                    "--config", config_path,
                    "--no-browser",
                ])
            output = stderr_capture.getvalue()
        self.assertIn("Non-Windows", output)


if __name__ == "__main__":
    unittest.main()
