"""Tests for task 2.1: PipeClient class — connect, close, _read_exact, context manager.

Requirements: 2.1, 2.7, 2.8, 2.9, 9.4
"""

from __future__ import annotations

import sys
import os
import io
import threading
import time
import unittest
from unittest.mock import MagicMock, patch, call

# Ensure variable_pb2 can be found from production path
sys.path.insert(0, r"C:\NEVEN\taskpane")

# Add TaskPane to path so pipe_client is importable
_TASKPANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _TASKPANE)

from pipe_client import (  # noqa: E402
    PipeClient,
    PipeClientError,
    PipeTimeoutError,
    PipeProtocolError,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal PipeClient in "disconnected" state for unit testing
# without a real pipe
# ---------------------------------------------------------------------------

def make_client(pipe_name: str = r"\\.\pipe\neven_test", timeout_ms: int = 5_000) -> PipeClient:
    return PipeClient(pipe_name, timeout_ms=timeout_ms)


# ---------------------------------------------------------------------------
# 1. Constructor
# ---------------------------------------------------------------------------

class TestPipeClientConstructor(unittest.TestCase):
    def test_default_timeout(self):
        c = PipeClient(r"\\.\pipe\neven_r")
        self.assertEqual(c._timeout_ms, 60_000)

    def test_custom_timeout(self):
        c = PipeClient(r"\\.\pipe\neven_r", timeout_ms=5_000)
        self.assertEqual(c._timeout_ms, 5_000)

    def test_pipe_name_stored(self):
        name = r"\\.\pipe\neven_julia"
        c = PipeClient(name)
        self.assertEqual(c._pipe_name, name)

    def test_handle_initially_none(self):
        c = PipeClient(r"\\.\pipe\neven_r")
        self.assertIsNone(c._handle)

    def test_max_response_bytes_class_constant(self):
        self.assertEqual(PipeClient.MAX_RESPONSE_BYTES, 256 * 1024)


# ---------------------------------------------------------------------------
# 2. connect() — Requirement 2.1, 9.4
# ---------------------------------------------------------------------------

class TestConnect(unittest.TestCase):
    """connect() must call the Win32 CreateFile and store the handle."""

    def test_connect_pywin32_success(self):
        """connect() stores a non-None handle when CreateFile succeeds."""
        fake_handle = object()
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32file") as mock_wf, \
             patch("pipe_client.win32api"), \
             patch("pipe_client.pywintypes"):
            mock_wf.GENERIC_READ = 0x80000000
            mock_wf.GENERIC_WRITE = 0x40000000
            mock_wf.OPEN_EXISTING = 3
            mock_wf.CreateFile.return_value = fake_handle

            c = make_client()
            c.connect()

            self.assertIs(c._handle, fake_handle)
            mock_wf.CreateFile.assert_called_once()

    def test_connect_pywin32_raises_oserror_on_failure(self):
        """connect() raises OSError when CreateFile fails."""
        import types
        fake_pywintypes = types.SimpleNamespace(error=OSError)

        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32file") as mock_wf, \
             patch("pipe_client.pywintypes", fake_pywintypes):
            mock_wf.GENERIC_READ = 0x80000000
            mock_wf.GENERIC_WRITE = 0x40000000
            mock_wf.OPEN_EXISTING = 3
            mock_wf.CreateFile.side_effect = OSError("pipe not found")

            c = make_client()
            with self.assertRaises(OSError):
                c.connect()

        self.assertIsNone(c._handle)

    def test_connect_accepts_custom_pipe_name(self):
        """connect() passes the pipe_name given in the constructor to CreateFile."""
        custom_name = r"\\.\pipe\neven_custom_test"
        fake_handle = object()
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32file") as mock_wf, \
             patch("pipe_client.win32api"), \
             patch("pipe_client.pywintypes"):
            mock_wf.GENERIC_READ = 0x80000000
            mock_wf.GENERIC_WRITE = 0x40000000
            mock_wf.OPEN_EXISTING = 3
            mock_wf.CreateFile.return_value = fake_handle

            c = PipeClient(custom_name)
            c.connect()

            args, _ = mock_wf.CreateFile.call_args
            self.assertEqual(args[0], custom_name)


# ---------------------------------------------------------------------------
# 3. close() — Requirement 2.8, 2.9
# ---------------------------------------------------------------------------

class TestClose(unittest.TestCase):
    def test_close_calls_closehandle(self):
        """close() calls CloseHandle on the stored handle."""
        fake_handle = object()
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api") as mock_wa:
            c = make_client()
            c._handle = fake_handle
            c.close()
            mock_wa.CloseHandle.assert_called_once_with(fake_handle)

    def test_close_sets_handle_none(self):
        """close() sets _handle to None after closing."""
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            c = make_client()
            c._handle = object()
            c.close()
            self.assertIsNone(c._handle)

    def test_close_idempotent_when_already_none(self):
        """close() on an already-closed client must not raise."""
        c = make_client()
        self.assertIsNone(c._handle)
        c.close()  # should not raise
        c.close()  # should not raise

    def test_close_idempotent_when_called_twice(self):
        """Calling close() twice after connect() should not raise."""
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api") as mock_wa:
            c = make_client()
            c._handle = object()
            c.close()
            c.close()  # second call — handle is already None
            mock_wa.CloseHandle.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Context manager — Requirement 2.9
# ---------------------------------------------------------------------------

class TestContextManager(unittest.TestCase):
    def test_enter_returns_self(self):
        """__enter__ must return the PipeClient instance itself."""
        c = make_client()
        result = c.__enter__()
        self.assertIs(result, c)

    def test_exit_calls_close(self):
        """__exit__ must call close() regardless of exception state."""
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api") as mock_wa:
            c = make_client()
            c._handle = object()
            c.__exit__(None, None, None)
            mock_wa.CloseHandle.assert_called_once()

    def test_with_statement_closes_on_normal_exit(self):
        """Using 'with PipeClient(...) as c:' closes the connection on block exit."""
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api") as mock_wa:
            c = make_client()
            c._handle = sentinel = object()
            with c:
                self.assertIs(c._handle, sentinel)
            # After exiting the with block, handle should be None
            self.assertIsNone(c._handle)
            mock_wa.CloseHandle.assert_called_once_with(sentinel)

    def test_with_statement_closes_on_exception(self):
        """__exit__ closes the connection even when an exception is raised inside the block."""
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api") as mock_wa:
            c = make_client()
            c._handle = object()
            try:
                with c:
                    raise ValueError("test error")
            except ValueError:
                pass
            self.assertIsNone(c._handle)
            mock_wa.CloseHandle.assert_called_once()


# ---------------------------------------------------------------------------
# 5. _read_exact() — Requirement 2.7 (timeout enforcement)
# ---------------------------------------------------------------------------

class TestReadExact(unittest.TestCase):
    """Tests for _read_exact: success path, timeout, and pipe-closed error."""

    def _make_client_with_mock_read(self, data: bytes, delay: float = 0.0) -> PipeClient:
        """Return a PipeClient whose _read_exactly_sync returns *data* after *delay* seconds."""
        c = make_client(timeout_ms=500)
        c._handle = object()

        def _mock_read_sync(n: int) -> bytes:
            if delay > 0:
                time.sleep(delay)
            return data

        c._read_exactly_sync = _mock_read_sync  # type: ignore[assignment]
        return c

    def test_read_exact_returns_correct_bytes(self):
        """_read_exact returns the bytes produced by the underlying read."""
        expected = b"\x01\x02\x03\x04"
        c = self._make_client_with_mock_read(expected)
        result = c._read_exact(4)
        self.assertEqual(result, expected)

    def test_read_exact_raises_timeout_error(self):
        """_read_exact raises PipeTimeoutError when the read thread exceeds timeout_ms."""
        # delay >> timeout_ms so the thread is definitely still running when join expires
        c = self._make_client_with_mock_read(b"\x00" * 4, delay=2.0)
        c._timeout_ms = 100  # very short

        # Patch win32api so close() doesn't reject the plain-object sentinel handle
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            with self.assertRaises(PipeTimeoutError):
                c._read_exact(4)

    def test_read_exact_closes_handle_on_timeout(self):
        """_read_exact closes the pipe handle when a timeout occurs."""
        closed = []

        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            c = make_client(timeout_ms=100)
            c._handle = object()

            def _slow_read_sync(n: int) -> bytes:
                time.sleep(2.0)
                return b"\x00" * n

            c._read_exactly_sync = _slow_read_sync  # type: ignore[assignment]

            original_close = c.close
            def _tracking_close():
                closed.append(True)
                original_close()

            c.close = _tracking_close  # type: ignore[method-assign]

            with self.assertRaises(PipeTimeoutError):
                c._read_exact(4)

        self.assertTrue(closed, "close() should have been called on timeout")

    def test_read_exact_propagates_pipe_client_error(self):
        """_read_exact propagates PipeClientError raised inside the worker thread."""
        c = make_client(timeout_ms=1_000)
        c._handle = object()

        def _failing_read_sync(n: int) -> bytes:
            raise PipeClientError("Pipe closed by server")

        c._read_exactly_sync = _failing_read_sync  # type: ignore[assignment]

        with self.assertRaises(PipeClientError, msg="Pipe closed by server"):
            c._read_exact(4)


# ---------------------------------------------------------------------------
# 6. _read_exactly_sync() — accumulates multiple chunks
# ---------------------------------------------------------------------------

class TestReadExactlySync(unittest.TestCase):
    def test_accumulates_partial_chunks(self):
        """_read_exactly_sync loops until exactly n bytes are accumulated."""
        # Simulate a _read_chunk that returns 2 bytes at a time
        chunks = [b"AB", b"CD", b"EF"]
        idx = [0]

        c = make_client()
        c._handle = object()

        def _chunked_read(n: int) -> bytes:
            if idx[0] >= len(chunks):
                return b""
            chunk = chunks[idx[0]]
            idx[0] += 1
            return chunk

        c._read_chunk = _chunked_read  # type: ignore[assignment]
        result = c._read_exactly_sync(6)
        self.assertEqual(result, b"ABCDEF")

    def test_raises_pipe_client_error_on_empty_chunk(self):
        """_read_exactly_sync raises PipeClientError when the pipe returns 0 bytes."""
        c = make_client()
        c._handle = object()
        c._read_chunk = lambda n: b""  # type: ignore[assignment]

        with self.assertRaises(PipeClientError):
            c._read_exactly_sync(4)


# ---------------------------------------------------------------------------
# 7. Exception hierarchy
# ---------------------------------------------------------------------------

class TestExceptionHierarchy(unittest.TestCase):
    def test_pipe_timeout_error_is_pipe_client_error(self):
        self.assertTrue(issubclass(PipeTimeoutError, PipeClientError))

    def test_pipe_protocol_error_is_pipe_client_error(self):
        self.assertTrue(issubclass(PipeProtocolError, PipeClientError))

    def test_pipe_client_error_is_exception(self):
        self.assertTrue(issubclass(PipeClientError, Exception))


if __name__ == "__main__":
    unittest.main()
