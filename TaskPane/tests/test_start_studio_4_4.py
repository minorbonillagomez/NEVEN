"""Property test for task 4.4: enabled languages control which processes are launched.

**Property 3: Enabled languages control exactly which processes are launched**
**Validates: Requirements 1.2, 1.3, 1.4, 7.1**

For any subset of {r, python, julia} configured as enabled, the launcher must
start exactly those Control processes — no more, no less.  Each launched process
must receive ``-p \\.\\pipe\\neven_{lang}`` as its pipe-name argument and must
have ``RJ2XCL_HOME`` set in its environment.

Strategy
--------
``subprocess.Popen`` is patched so it never spawns real processes.  The mock
factory captures (cmd, env) for each call.  We also patch ``_IS_WINDOWS = True``
so the launch branch executes, and stub out all I/O side-effects (wait_for_pipes,
write_pid_file, start_server, etc.) for a clean test exit.

Note: ``_make_mock_proc`` uses plain ``MagicMock()`` (no spec) because inside a
``patch("subprocess.Popen")`` context the real ``subprocess.Popen`` class is
replaced by a MagicMock, so specifying it as the spec raises ``InvalidSpecError``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TASKPANE not in sys.path:
    sys.path.insert(0, _TASKPANE)

import start_studio  # noqa: E402
from start_studio import (  # noqa: E402
    EXE_MAP,
    _pipe_name_for,
    _STANDALONE_DEFAULTS,
    launch_control,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_proc(pid: int = 9001) -> MagicMock:
    """Return a plain MagicMock that looks like a Popen object.

    No ``spec=subprocess.Popen`` — that raises InvalidSpecError when the
    real Popen is already patched to a MagicMock.
    """
    mock = MagicMock()
    mock.pid = pid
    mock.wait.return_value = 0
    mock.poll.return_value = None
    return mock


def _make_config(tmpdir: str, enabled: frozenset) -> dict:
    """Return a config dict with *tmpdir* as controlDir and *enabled* langs."""
    return {
        "Standalone": {
            **_STANDALONE_DEFAULTS,
            "controlDir": tmpdir,
            "languages": sorted(enabled),
        }
    }


def _write_fake_exes(tmpdir: str, langs: frozenset) -> None:
    """Create zero-byte fake executables in *tmpdir* for each language."""
    for lang in langs:
        exe_name = EXE_MAP[lang]
        with open(os.path.join(tmpdir, exe_name), "wb") as fh:
            fh.write(b"\x00")


def _run_main_with_mocked_popen(
    config_path: str,
    popen_calls: list,
) -> None:
    """Run main() with Popen patched, capturing every (cmd, env) pair."""

    def mock_popen(cmd, env=None, **kwargs):
        lang_detected = None
        for lang in ("r", "python", "julia"):
            if EXE_MAP[lang] in cmd[0]:
                lang_detected = lang
                break
        proc = _make_mock_proc(pid=len(popen_calls) + 1000)
        proc.args = cmd
        popen_calls.append({"lang": lang_detected, "cmd": cmd, "env": env})
        return proc

    with patch("subprocess.Popen", side_effect=mock_popen), \
         patch.object(start_studio, "_IS_WINDOWS", True), \
         patch("start_studio.wait_for_pipes"), \
         patch("start_studio.write_pid_file"), \
         patch("start_studio.start_server",
               return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
         patch("start_studio.monitor_processes"), \
         patch("start_studio.wait_for_signal"), \
         patch("start_studio.shutdown"), \
         patch("webbrowser.open"):
        start_studio.main(["--config", config_path, "--no-browser"])


# ---------------------------------------------------------------------------
# Property 3: enabled languages control exactly which processes are launched
# ---------------------------------------------------------------------------

class TestEnabledLanguagesControlProcessLaunch(unittest.TestCase):
    """Property 3 — enabled languages control exactly which processes launch."""

    @given(
        enabled=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=50)
    def test_exactly_enabled_languages_are_launched(
        self, enabled: frozenset
    ) -> None:
        """main() launches exactly the Control processes for the enabled set.

        **Property 3: Enabled languages control exactly which processes are launched**
        **Validates: Requirements 1.2, 1.3**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_fake_exes(tmpdir, enabled)
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(_make_config(tmpdir, enabled), fh)

            popen_calls: list[dict] = []
            _run_main_with_mocked_popen(config_path, popen_calls)

        launched_langs = {c["lang"] for c in popen_calls}
        self.assertEqual(
            launched_langs, set(enabled),
            f"Expected exactly {set(enabled)!r} to be launched, got {launched_langs!r}",
        )

    @given(
        enabled=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=50)
    def test_each_process_has_correct_pipe_name_arg(
        self, enabled: frozenset
    ) -> None:
        """Each launched process receives ``-p <pipe_name>`` in its command.

        Validates: Requirements 1.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_fake_exes(tmpdir, enabled)
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(_make_config(tmpdir, enabled), fh)

            popen_calls: list[dict] = []
            _run_main_with_mocked_popen(config_path, popen_calls)

        for call_info in popen_calls:
            lang = call_info["lang"]
            expected_pipe = _pipe_name_for(lang)
            cmd = call_info["cmd"]
            with self.subTest(lang=lang):
                self.assertIn("-p", cmd,
                              f"'{lang}': '-p' not found in cmd {cmd!r}")
                pipe_idx = cmd.index("-p") + 1
                self.assertEqual(
                    cmd[pipe_idx], expected_pipe,
                    f"'{lang}': expected pipe '{expected_pipe}', got '{cmd[pipe_idx]}'",
                )

    @given(
        enabled=st.frozensets(st.sampled_from(["r", "python", "julia"]))
    )
    @settings(max_examples=50)
    def test_each_process_has_rj2xcl_home_in_env(
        self, enabled: frozenset
    ) -> None:
        """Each launched process has RJ2XCL_HOME set in its environment.

        Validates: Requirements 1.4, 7.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_fake_exes(tmpdir, enabled)
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(_make_config(tmpdir, enabled), fh)

            popen_calls: list[dict] = []
            _run_main_with_mocked_popen(config_path, popen_calls)

        for call_info in popen_calls:
            lang = call_info["lang"]
            env = call_info["env"]
            with self.subTest(lang=lang):
                self.assertIsNotNone(env, f"'{lang}': env should not be None")
                self.assertIn("RJ2XCL_HOME", env,
                              f"'{lang}': RJ2XCL_HOME missing from env")
                self.assertEqual(
                    env["RJ2XCL_HOME"], tmpdir,
                    f"'{lang}': RJ2XCL_HOME value mismatch",
                )

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_no_binary_in_control_dir_launches_nothing(self) -> None:
        """When executables are absent, no processes are started."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            # Config says all three enabled, but no binaries created
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(_make_config(tmpdir, frozenset(["r", "python", "julia"])), fh)

            popen_calls: list[dict] = []
            _run_main_with_mocked_popen(config_path, popen_calls)

        self.assertEqual(popen_calls, [],
                         "No processes should launch when binaries are absent")

    def test_non_windows_never_calls_popen(self) -> None:
        """On non-Windows, subprocess.Popen is never called regardless of config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create real executables — irrelevant on non-Windows
            _write_fake_exes(tmpdir, frozenset(["r", "python", "julia"]))
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(_make_config(tmpdir, frozenset(["r", "python", "julia"])), fh)

            with patch("subprocess.Popen") as mock_popen, \
                 patch.object(start_studio, "_IS_WINDOWS", False), \
                 patch("start_studio.wait_for_pipes"), \
                 patch("start_studio.write_pid_file"), \
                 patch("start_studio.start_server",
                       return_value=(threading.Thread(target=lambda: None, daemon=True), 5555)), \
                 patch("start_studio.monitor_processes"), \
                 patch("start_studio.wait_for_signal"), \
                 patch("start_studio.shutdown"), \
                 patch("webbrowser.open"):
                start_studio.main(["--config", config_path, "--no-browser"])

        mock_popen.assert_not_called()

    def test_only_enabled_subsets_are_launched(self) -> None:
        """Only the specified subset launches; others are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only R and Python binaries; Julia deliberately absent
            _write_fake_exes(tmpdir, frozenset(["r", "python"]))
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, "w", encoding="utf-8") as fh:
                json.dump(_make_config(tmpdir, frozenset(["r", "python", "julia"])), fh)

            popen_calls: list[dict] = []
            _run_main_with_mocked_popen(config_path, popen_calls)

        launched = {c["lang"] for c in popen_calls}
        # Julia binary missing → skipped; r and python launched
        self.assertEqual(launched, {"r", "python"})
        self.assertNotIn("julia", launched)


# ---------------------------------------------------------------------------
# Unit-level tests for launch_control() directly
# ---------------------------------------------------------------------------

class TestLaunchControlArguments(unittest.TestCase):
    """Direct unit tests for launch_control() pipe-name and env injection."""

    def _run_launch(self, lang: str, tmpdir: str) -> tuple:
        """Call launch_control for *lang*, return (cmd_args, env)."""
        config = {
            "Standalone": {
                **_STANDALONE_DEFAULTS,
                "controlDir": tmpdir,
            }
        }
        exe_path = os.path.join(tmpdir, EXE_MAP[lang])
        captured: dict = {}

        def mock_popen(cmd, env=None, **kwargs):
            captured["cmd"] = cmd
            captured["env"] = env
            proc = _make_mock_proc()
            proc.args = cmd
            return proc

        with patch("subprocess.Popen", side_effect=mock_popen):
            launch_control(exe_path, lang, config)

        return captured["cmd"], captured["env"]

    def test_r_pipe_name_in_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd, _ = self._run_launch("r", tmpdir)
        self.assertIn(_pipe_name_for("r"), cmd)
        self.assertIn("-p", cmd)

    def test_python_pipe_name_in_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd, _ = self._run_launch("python", tmpdir)
        self.assertIn(_pipe_name_for("python"), cmd)

    def test_julia_pipe_name_in_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd, _ = self._run_launch("julia", tmpdir)
        self.assertIn(_pipe_name_for("julia"), cmd)

    def test_rj2xcl_home_matches_control_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _, env = self._run_launch("r", tmpdir)
        self.assertIn("RJ2XCL_HOME", env)
        self.assertEqual(env["RJ2XCL_HOME"], tmpdir)

    def test_exe_is_first_in_cmd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exe_path = os.path.join(tmpdir, EXE_MAP["r"])
            cmd, _ = self._run_launch("r", tmpdir)
        self.assertEqual(cmd[0], exe_path)

    def test_pipe_flag_precedes_pipe_name(self):
        """``-p`` flag appears immediately before the pipe name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd, _ = self._run_launch("python", tmpdir)
        pipe_idx = cmd.index("-p")
        self.assertEqual(cmd[pipe_idx + 1], _pipe_name_for("python"))


if __name__ == "__main__":
    unittest.main()
