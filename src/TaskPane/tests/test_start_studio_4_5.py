"""Property test for task 4.5: SIGINT/SIGTERM terminates all launched processes.

**Property 4: SIGINT/SIGTERM terminates all launched processes**
**Validates: Requirements 1.9**

Uses the ``stop_event`` mechanism from ``wait_for_signal`` — when the event is
set (as it would be on SIGINT/SIGTERM) the caller proceeds to ``shutdown()``.
We test that ``shutdown()`` calls ``terminate()`` on every mock process.
"""

from __future__ import annotations

import os
import subprocess
import sys
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

from start_studio import shutdown  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_proc(pid: int = 9999) -> MagicMock:
    """Return a mock Popen-like object whose wait() returns immediately."""
    proc = MagicMock(spec=subprocess.Popen)
    proc.pid = pid
    proc.args = [r"C:\NEVEN\ControlR.exe"]
    proc.wait.return_value = 0
    return proc


# ---------------------------------------------------------------------------
# Property 4: shutdown() calls terminate() on every process
# ---------------------------------------------------------------------------

class TestShutdownTerminatesAllProcesses(unittest.TestCase):
    """Property 4 — SIGINT/SIGTERM terminates all launched processes (Req 1.9)."""

    @given(
        enabled=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=50)
    def test_terminate_called_on_every_process(self, enabled: frozenset) -> None:
        """shutdown() must call terminate() on every process in the dict.

        **Property 4: SIGINT/SIGTERM terminates all launched processes**
        **Validates: Requirements 1.9**
        """
        # Build a dict of mock processes for each enabled language
        processes = {lang: _make_mock_proc(pid=i + 1000)
                     for i, lang in enumerate(sorted(enabled))}

        # shutdown() mirrors what the signal handler triggers
        shutdown(processes)

        # Every mock process must have had terminate() called
        for lang, proc in processes.items():
            with self.subTest(lang=lang):
                proc.terminate.assert_called_once()

    @given(
        enabled=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=50)
    def test_wait_called_after_terminate(self, enabled: frozenset) -> None:
        """shutdown() must call wait() on every process after terminate().

        **Validates: Requirements 1.9**
        """
        processes = {lang: _make_mock_proc(pid=i + 2000)
                     for i, lang in enumerate(sorted(enabled))}

        shutdown(processes)

        for lang, proc in processes.items():
            with self.subTest(lang=lang):
                proc.wait.assert_called()

    @given(
        enabled=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=30)
    def test_all_processes_terminated_even_if_one_raises(
        self, enabled: frozenset
    ) -> None:
        """Even if one terminate() raises OSError, the others are still called.

        **Validates: Requirements 1.9**
        """
        langs = sorted(enabled)
        processes: dict = {}
        for i, lang in enumerate(langs):
            proc = _make_mock_proc(pid=i + 3000)
            # First language raises on terminate; the rest succeed
            if i == 0:
                proc.terminate.side_effect = OSError("already dead")
            processes[lang] = proc

        # Should not raise
        try:
            shutdown(processes)
        except Exception as exc:
            self.fail(f"shutdown() raised unexpectedly: {exc}")

        # Remaining processes (non-first) must still have terminate called
        for i, lang in enumerate(langs[1:], 1):
            with self.subTest(lang=lang):
                processes[lang].terminate.assert_called()

    @given(
        enabled=st.frozensets(
            st.sampled_from(["r", "python", "julia"]),
            min_size=1,
        )
    )
    @settings(max_examples=30)
    def test_kill_called_when_wait_times_out(self, enabled: frozenset) -> None:
        """When proc.wait() raises TimeoutExpired, proc.kill() must be called.

        **Validates: Requirements 1.9**
        """
        processes: dict = {}
        for i, lang in enumerate(sorted(enabled)):
            proc = _make_mock_proc(pid=i + 4000)
            proc.wait.side_effect = subprocess.TimeoutExpired(cmd="ctrl", timeout=5)
            proc.kill.return_value = None
            # second wait (after kill) succeeds
            proc.wait.side_effect = [
                subprocess.TimeoutExpired(cmd="ctrl", timeout=5),
                None,
            ]
            processes[lang] = proc

        shutdown(processes)

        for lang, proc in processes.items():
            with self.subTest(lang=lang):
                proc.kill.assert_called_once()


if __name__ == "__main__":
    unittest.main()
