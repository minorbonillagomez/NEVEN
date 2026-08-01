"""Tests for task 4.2: start_studio.py — process launch, pipe readiness
polling, and PID file management.

Requirements: 1.3, 1.4, 1.5, 8.5, 8.6, 9.3
"""

from __future__ import annotations

import atexit
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Path setup: make start_studio importable from the TaskPane directory
# ---------------------------------------------------------------------------
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TASKPANE not in sys.path:
    sys.path.insert(0, _TASKPANE)

import start_studio  # noqa: E402 — must come after sys.path setup
from start_studio import (  # noqa: E402
    _STANDALONE_DEFAULTS,
    _pid_file_path,
    _pipe_name_for,
    _probe_pipe_once,
    launch_control,
    load_config,
    remove_pid_file,
    wait_for_pipes,
    write_pid_file,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_config(**standalone_overrides) -> dict:
    """Return a minimal config dict with a Standalone section."""
    standalone = {**_STANDALONE_DEFAULTS, **standalone_overrides}
    return {"Standalone": standalone}


def _make_mock_proc(pid: int = 12345, lang: str = "r") -> MagicMock:
    """Return a mock subprocess.Popen-like object."""
    proc = MagicMock(spec=subprocess.Popen)
    proc.pid = pid
    proc.lang = lang  # extra attribute for convenience
    return proc


# ===========================================================================
# 1. _pipe_name_for — helper
# ===========================================================================

class TestPipeNameFor(unittest.TestCase):

    def test_r_pipe_name(self):
        self.assertEqual(_pipe_name_for("r"), r"\\.\pipe\neven_r")

    def test_python_pipe_name(self):
        self.assertEqual(_pipe_name_for("python"), r"\\.\pipe\neven_python")

    def test_julia_pipe_name(self):
        self.assertEqual(_pipe_name_for("julia"), r"\\.\pipe\neven_julia")

    def test_pattern_is_correct(self):
        r"""Pipe name must follow \\.\pipe\neven_{lang}."""
        for lang in ("r", "python", "julia"):
            pipe = _pipe_name_for(lang)
            self.assertTrue(pipe.startswith(r"\\.\pipe\neven_"))
            self.assertTrue(pipe.endswith(lang))


# ===========================================================================
# 2. launch_control — process launch (Requirements 1.3, 1.4)
# ===========================================================================

class TestLaunchControl(unittest.TestCase):

    def setUp(self):
        self.config = _make_config(controlDir=r"C:\NEVEN\\")

    def _mock_popen(self, pid: int = 99):
        """Return a context-manager patch for subprocess.Popen."""
        mock_proc = MagicMock(spec=subprocess.Popen)
        mock_proc.pid = pid
        return mock_proc

    # ------------------------------------------------------------------
    # Pipe name passed to the process (Requirement 1.3)
    # ------------------------------------------------------------------

    def test_launches_with_correct_pipe_arg_r(self):
        r"""launch_control passes -p \\.\pipe\neven_r for lang='r' (Req 1.3)."""
        mock_proc = self._mock_popen()
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            launch_control(r"C:\NEVEN\ControlR.exe", "r", self.config)
        args_passed = mock_popen.call_args[0][0]  # positional first arg = cmd list
        self.assertIn("-p", args_passed)
        pipe_idx = args_passed.index("-p")
        self.assertEqual(args_passed[pipe_idx + 1], r"\\.\pipe\neven_r")

    def test_launches_with_correct_pipe_arg_python(self):
        r"""launch_control passes -p \\.\pipe\neven_python for lang='python'."""
        mock_proc = self._mock_popen()
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            launch_control(r"C:\NEVEN\ControlPython.exe", "python", self.config)
        args_passed = mock_popen.call_args[0][0]
        pipe_idx = args_passed.index("-p")
        self.assertEqual(args_passed[pipe_idx + 1], r"\\.\pipe\neven_python")

    def test_launches_with_correct_pipe_arg_julia(self):
        r"""launch_control passes -p \\.\pipe\neven_julia for lang='julia'."""
        mock_proc = self._mock_popen()
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            launch_control(r"C:\NEVEN\ControlJulia.exe", "julia", self.config)
        args_passed = mock_popen.call_args[0][0]
        pipe_idx = args_passed.index("-p")
        self.assertEqual(args_passed[pipe_idx + 1], r"\\.\pipe\neven_julia")

    # ------------------------------------------------------------------
    # exe is first element of the command (Requirement 1.3)
    # ------------------------------------------------------------------

    def test_exe_is_first_argument(self):
        """The exe path is the first element of the Popen command list."""
        mock_proc = self._mock_popen()
        exe = r"C:\NEVEN\ControlR.exe"
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            launch_control(exe, "r", self.config)
        args_passed = mock_popen.call_args[0][0]
        self.assertEqual(args_passed[0], exe)

    # ------------------------------------------------------------------
    # RJ2XCL_HOME set in the environment (Requirement 1.4)
    # ------------------------------------------------------------------

    def test_rj2xcl_home_set_in_env(self):
        """RJ2XCL_HOME is set to controlDir in the child environment (Req 1.4)."""
        mock_proc = self._mock_popen()
        config = _make_config(controlDir=r"D:\custom_neven\\")
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            launch_control(r"D:\custom_neven\ControlR.exe", "r", config)
        kwargs = mock_popen.call_args[1]
        env = kwargs["env"]
        self.assertEqual(env["RJ2XCL_HOME"], r"D:\custom_neven\\")

    def test_env_inherits_os_environ(self):
        """The child environment includes the parent's os.environ entries."""
        mock_proc = self._mock_popen()
        sentinel_key = "_NEVEN_TEST_SENTINEL_"
        sentinel_val = "test_value_12345"
        with patch.dict(os.environ, {sentinel_key: sentinel_val}):
            with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
                launch_control(r"C:\NEVEN\ControlR.exe", "r", self.config)
        env = mock_popen.call_args[1]["env"]
        self.assertEqual(env[sentinel_key], sentinel_val)

    def test_rj2xcl_home_overrides_existing_env(self):
        """RJ2XCL_HOME in the child env always equals controlDir, even if
        the parent process has a different RJ2XCL_HOME set."""
        mock_proc = self._mock_popen()
        config = _make_config(controlDir=r"C:\MY_NEVEN\\")
        with patch.dict(os.environ, {"RJ2XCL_HOME": r"C:\OLD\\"}):
            with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
                launch_control(r"C:\MY_NEVEN\ControlR.exe", "r", config)
        env = mock_popen.call_args[1]["env"]
        self.assertEqual(env["RJ2XCL_HOME"], r"C:\MY_NEVEN\\")

    # ------------------------------------------------------------------
    # Returns the Popen object
    # ------------------------------------------------------------------

    def test_returns_popen_object(self):
        """launch_control returns the Popen instance."""
        mock_proc = self._mock_popen(pid=42)
        with patch("subprocess.Popen", return_value=mock_proc):
            result = launch_control(r"C:\NEVEN\ControlR.exe", "r", self.config)
        self.assertIs(result, mock_proc)

    def test_returned_process_has_correct_pid(self):
        """The returned object exposes the PID of the launched process."""
        mock_proc = self._mock_popen(pid=777)
        with patch("subprocess.Popen", return_value=mock_proc):
            result = launch_control(r"C:\NEVEN\ControlR.exe", "r", self.config)
        self.assertEqual(result.pid, 777)

    # ------------------------------------------------------------------
    # Uses default controlDir when absent from config
    # ------------------------------------------------------------------

    def test_uses_default_control_dir_for_rj2xcl_home(self):
        """When controlDir absent from config, default is used for RJ2XCL_HOME."""
        mock_proc = self._mock_popen()
        config = {"Standalone": {}}  # no controlDir
        with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
            launch_control(r"C:\NEVEN\ControlR.exe", "r", config)
        env = mock_popen.call_args[1]["env"]
        self.assertEqual(
            env["RJ2XCL_HOME"],
            str(_STANDALONE_DEFAULTS["controlDir"]),
        )


# ===========================================================================
# 3. wait_for_pipes — pipe readiness polling (Requirement 1.5)
# ===========================================================================

class TestWaitForPipes(unittest.TestCase):

    # ------------------------------------------------------------------
    # Non-Windows path (Requirement 4.7)
    # ------------------------------------------------------------------

    def test_non_windows_logs_info_and_returns(self):
        """On non-Windows, wait_for_pipes logs INFO and returns without polling."""
        import io
        processes = {"r": _make_mock_proc()}
        with patch.object(start_studio, "_IS_WINDOWS", False):
            with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                wait_for_pipes(processes, timeout=0.1)
                output = mock_err.getvalue()
        self.assertIn("INFO", output)
        self.assertIn("Non-Windows", output)

    def test_non_windows_does_not_modify_processes(self):
        """On non-Windows, processes dict is unchanged (no timeout removal)."""
        mock_proc = _make_mock_proc()
        processes = {"r": mock_proc}
        with patch.object(start_studio, "_IS_WINDOWS", False):
            wait_for_pipes(processes, timeout=0.1)
        # Should still be there
        self.assertIn("r", processes)

    # ------------------------------------------------------------------
    # Windows path: pipes become ready
    # ------------------------------------------------------------------

    def test_ready_pipe_stays_in_processes(self):
        """When a pipe probe succeeds immediately, the lang stays in processes."""
        mock_proc = _make_mock_proc()
        processes = {"r": mock_proc}
        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(start_studio, "_probe_pipe_once", return_value=True):
                wait_for_pipes(processes, timeout=1.0)
        self.assertIn("r", processes)

    def test_all_ready_pipes_stay(self):
        """When all three pipes become ready, all three langs stay in processes."""
        processes = {
            "r":      _make_mock_proc(pid=1),
            "python": _make_mock_proc(pid=2),
            "julia":  _make_mock_proc(pid=3),
        }
        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(start_studio, "_probe_pipe_once", return_value=True):
                wait_for_pipes(processes, timeout=1.0)
        self.assertEqual(set(processes.keys()), {"r", "python", "julia"})

    # ------------------------------------------------------------------
    # Windows path: timeout — pipe never becomes ready
    # ------------------------------------------------------------------

    def test_timed_out_lang_removed_from_processes(self):
        """When a pipe never becomes ready, the lang is removed from processes."""
        mock_proc = _make_mock_proc()
        processes = {"r": mock_proc}
        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(start_studio, "_probe_pipe_once", return_value=False):
                wait_for_pipes(processes, timeout=0.05)  # very short timeout
        self.assertNotIn("r", processes)

    def test_timed_out_lang_logs_warning(self):
        """Timeout removal logs a WARNING with the lang name."""
        import io
        processes = {"python": _make_mock_proc()}
        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(start_studio, "_probe_pipe_once", return_value=False):
                with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                    wait_for_pipes(processes, timeout=0.05)
                    output = mock_err.getvalue()
        self.assertIn("WARNING", output)
        self.assertIn("python", output)
        self.assertIn("timeout", output.lower())

    def test_partial_timeout_removes_only_slow_lang(self):
        """Only the language whose pipe doesn't respond in time is removed."""
        processes = {
            "r":      _make_mock_proc(pid=1),
            "python": _make_mock_proc(pid=2),
        }
        # r's pipe responds immediately; python's pipe never responds
        def _probe_side_effect(pipe_name: str) -> bool:
            return "neven_r" in pipe_name

        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(
                start_studio, "_probe_pipe_once", side_effect=_probe_side_effect
            ):
                wait_for_pipes(processes, timeout=0.05)

        self.assertIn("r", processes)
        self.assertNotIn("python", processes)

    # ------------------------------------------------------------------
    # Empty processes dict — no-op
    # ------------------------------------------------------------------

    def test_empty_processes_no_error(self):
        """wait_for_pipes on an empty dict completes without error."""
        with patch.object(start_studio, "_IS_WINDOWS", True):
            try:
                wait_for_pipes({}, timeout=1.0)
            except Exception as exc:
                self.fail(f"wait_for_pipes raised unexpectedly: {exc}")

    # ------------------------------------------------------------------
    # Polling interval: probe is called multiple times before timeout
    # ------------------------------------------------------------------

    def test_probe_called_repeatedly_before_timeout(self):
        """Probe is retried on each poll interval, not just once."""
        processes = {"r": _make_mock_proc()}
        probe_calls = []

        def counting_probe(name):
            probe_calls.append(name)
            return False  # never ready

        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(
                start_studio, "_probe_pipe_once", side_effect=counting_probe
            ):
                wait_for_pipes(processes, timeout=0.25)

        # With 100 ms poll interval and 250 ms timeout, we expect at least 2 calls
        self.assertGreaterEqual(len(probe_calls), 2)


# ===========================================================================
# 4. _pid_file_path — helper (Requirement 8.5)
# ===========================================================================

class TestPidFilePath(unittest.TestCase):

    def test_pid_file_in_control_dir(self):
        """PID file path is <controlDir>/studio.pid."""
        config = _make_config(controlDir=r"C:\NEVEN\\")
        path = _pid_file_path(config)
        self.assertTrue(path.endswith("studio.pid"))
        self.assertIn("NEVEN", path)

    def test_uses_control_dir_from_config(self):
        """PID file path uses the controlDir from config."""
        config = _make_config(controlDir=r"D:\my_dir")
        path = _pid_file_path(config)
        self.assertTrue(path.startswith(r"D:\my_dir"))

    def test_uses_default_when_config_absent(self):
        """Falls back to default controlDir when Standalone absent."""
        config = {}
        path = _pid_file_path(config)
        self.assertIn("studio.pid", path)


# ===========================================================================
# 5. write_pid_file — PID file creation (Requirement 8.5, 8.6)
# ===========================================================================

class TestWritePidFile(unittest.TestCase):

    def _make_config_with_tmpdir(self, tmpdir: str) -> dict:
        return _make_config(controlDir=tmpdir)

    # ------------------------------------------------------------------
    # File content
    # ------------------------------------------------------------------

    def test_pid_file_contains_launcher_pid(self):
        """PID file contains the launcher PID under 'launcher' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            write_pid_file(config, {}, launcher_pid=9001)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data["launcher"], 9001)

    def test_pid_file_contains_process_pids(self):
        """PID file contains a key for each language with its PID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            processes = {
                "r":      _make_mock_proc(pid=100),
                "python": _make_mock_proc(pid=200),
            }
            write_pid_file(config, processes, launcher_pid=50)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data["r"], 100)
        self.assertEqual(data["python"], 200)
        self.assertEqual(data["launcher"], 50)

    def test_pid_file_omits_languages_not_started(self):
        """Languages not in processes are not present in the PID file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            processes = {"r": _make_mock_proc(pid=111)}
            write_pid_file(config, processes, launcher_pid=10)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertIn("r", data)
        self.assertNotIn("python", data)
        self.assertNotIn("julia", data)

    def test_pid_file_is_valid_json(self):
        """The PID file is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            processes = {"r": _make_mock_proc(pid=1), "julia": _make_mock_proc(pid=2)}
            write_pid_file(config, processes, launcher_pid=99)
            path = _pid_file_path(config)
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except json.JSONDecodeError as exc:
                self.fail(f"PID file is not valid JSON: {exc}")
        self.assertIsInstance(data, dict)

    def test_all_three_langs_in_pid_file(self):
        """PID file with all three languages contains all four keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            processes = {
                "r":      _make_mock_proc(pid=10),
                "python": _make_mock_proc(pid=20),
                "julia":  _make_mock_proc(pid=30),
            }
            write_pid_file(config, processes, launcher_pid=1)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(set(data.keys()), {"launcher", "r", "python", "julia"})

    def test_launcher_only_pid_file(self):
        """Empty processes dict → PID file has only the 'launcher' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            write_pid_file(config, {}, launcher_pid=55)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(list(data.keys()), ["launcher"])
        self.assertEqual(data["launcher"], 55)

    # ------------------------------------------------------------------
    # File location
    # ------------------------------------------------------------------

    def test_pid_file_written_to_control_dir(self):
        """PID file is written inside controlDir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            write_pid_file(config, {}, launcher_pid=1)
            expected_path = os.path.join(tmpdir, "studio.pid")
            self.assertTrue(
                os.path.isfile(expected_path),
                f"Expected PID file at {expected_path}",
            )

    # ------------------------------------------------------------------
    # atexit registration (Requirement 8.6)
    # ------------------------------------------------------------------

    def test_atexit_remove_pid_file_registered(self):
        """write_pid_file registers remove_pid_file with atexit (Req 8.6)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            with patch("atexit.register") as mock_register:
                write_pid_file(config, {}, launcher_pid=1)
            # atexit.register should have been called with remove_pid_file and config
            mock_register.assert_called_once_with(remove_pid_file, config)

    # ------------------------------------------------------------------
    # Overwrite behaviour
    # ------------------------------------------------------------------

    def test_pid_file_overwritten_on_second_call(self):
        """Calling write_pid_file twice overwrites the first file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._make_config_with_tmpdir(tmpdir)
            write_pid_file(config, {}, launcher_pid=111)
            write_pid_file(config, {"r": _make_mock_proc(pid=222)}, launcher_pid=333)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data["launcher"], 333)
        self.assertEqual(data["r"], 222)


# ===========================================================================
# 6. remove_pid_file (Requirement 8.6)
# ===========================================================================

class TestRemovePidFile(unittest.TestCase):

    def test_removes_existing_pid_file(self):
        """remove_pid_file deletes an existing PID file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            path = _pid_file_path(config)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{"launcher": 1}')
            self.assertTrue(os.path.isfile(path))
            remove_pid_file(config)
            self.assertFalse(os.path.isfile(path))

    def test_remove_nonexistent_pid_file_does_not_raise(self):
        """remove_pid_file does not raise when the file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            # No file written — should be a no-op
            try:
                remove_pid_file(config)
            except Exception as exc:
                self.fail(f"remove_pid_file raised unexpectedly: {exc}")

    def test_remove_logs_info(self):
        """remove_pid_file logs an INFO message when it deletes the file."""
        import io
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            path = _pid_file_path(config)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('{}')
            with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                remove_pid_file(config)
                output = mock_err.getvalue()
        self.assertIn("INFO", output)
        self.assertIn("studio.pid", output)


# ===========================================================================
# 7. _probe_pipe_once — pipe probe helper
# ===========================================================================

class TestProbePipeOnce(unittest.TestCase):

    def test_returns_false_on_non_windows(self):
        """_probe_pipe_once always returns False on non-Windows."""
        with patch.object(start_studio, "_IS_WINDOWS", False):
            result = _probe_pipe_once(r"\\.\pipe\neven_r")
        self.assertFalse(result)

    def test_returns_true_when_pywin32_succeeds(self):
        """_probe_pipe_once returns True when win32file.CreateFile succeeds."""
        mock_handle = MagicMock()
        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(start_studio, "_WIN32_BACKEND", "pywin32"):
                with patch.object(start_studio, "win32file") as mock_wf:
                    with patch.object(start_studio, "win32api") as mock_wa:
                        mock_wf.GENERIC_READ = 0x80000000
                        mock_wf.GENERIC_WRITE = 0x40000000
                        mock_wf.OPEN_EXISTING = 3
                        mock_wf.CreateFile.return_value = mock_handle
                        result = _probe_pipe_once(r"\\.\pipe\neven_r")
                        mock_wa.CloseHandle.assert_called_once_with(mock_handle)
        self.assertTrue(result)

    def test_returns_false_when_pywin32_raises(self):
        """_probe_pipe_once returns False when CreateFile raises pywintypes.error."""
        with patch.object(start_studio, "_IS_WINDOWS", True):
            with patch.object(start_studio, "_WIN32_BACKEND", "pywin32"):
                with patch.object(start_studio, "win32file") as mock_wf:
                    with patch.object(start_studio, "pywintypes") as mock_pt:
                        mock_pt.error = OSError  # make pywintypes.error = OSError
                        mock_wf.GENERIC_READ = 0x80000000
                        mock_wf.GENERIC_WRITE = 0x40000000
                        mock_wf.OPEN_EXISTING = 3
                        mock_wf.CreateFile.side_effect = OSError("pipe not found")
                        result = _probe_pipe_once(r"\\.\pipe\neven_r")
        self.assertFalse(result)


# ===========================================================================
# 8. Integration: full write_pid_file + remove_pid_file lifecycle
# ===========================================================================

class TestPidLifecycle(unittest.TestCase):

    def test_write_then_remove_cleans_up(self):
        """Writing then removing the PID file leaves no file behind (Req 8.6)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            processes = {"r": _make_mock_proc(pid=42)}
            with patch("atexit.register"):  # don't actually register in test
                write_pid_file(config, processes, launcher_pid=10)
            pid_path = _pid_file_path(config)
            self.assertTrue(os.path.isfile(pid_path), "PID file should exist after write")
            remove_pid_file(config)
            self.assertFalse(os.path.isfile(pid_path), "PID file should be gone after remove")

    def test_pid_file_content_round_trips(self):
        """Writing and reading back the PID file produces the same data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = _make_config(controlDir=tmpdir)
            processes = {
                "r":      _make_mock_proc(pid=100),
                "python": _make_mock_proc(pid=200),
                "julia":  _make_mock_proc(pid=300),
            }
            with patch("atexit.register"):
                write_pid_file(config, processes, launcher_pid=999)
            path = _pid_file_path(config)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        self.assertEqual(data, {"launcher": 999, "r": 100, "python": 200, "julia": 300})


if __name__ == "__main__":
    unittest.main()
