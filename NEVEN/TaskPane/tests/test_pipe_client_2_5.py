"""Tests for task 2.5: PipeClient error paths.

All five error paths from Requirements 2.6, 2.7, 2.9, 10.5, 10.6 are verified here.
Several of these are already covered in depth by test_pipe_client_2_1.py and
test_pipe_client_2_2.py; this file provides the explicit traceability grouping
called for by the spec task and adds the dedicated "send-level" test for the
timeout path through send_code / send_function_call (not just _read_exact).

Requirements: 2.6, 2.7, 2.9, 10.5, 10.6
"""

from __future__ import annotations

import struct
import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

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
    _frame,
)
import variable_pb2


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_framed_result(var: variable_pb2.Variable) -> bytes:
    """Build a framed CallResponse{result=var} as the server would send it."""
    resp = variable_pb2.CallResponse()
    resp.result.CopyFrom(var)
    return _frame(resp)


def _make_framed_err(message: str) -> bytes:
    """Build a framed CallResponse{err=message} as the server would send it."""
    resp = variable_pb2.CallResponse()
    resp.err = message
    return _frame(resp)


def _client_with_canned_response(raw_bytes: bytes, timeout_ms: int = 5_000) -> PipeClient:
    """Return a PipeClient whose _read_exact is backed by *raw_bytes*.

    _write_all is a no-op so no real pipe is needed.
    """
    c = PipeClient(r"\\.\pipe\neven_test", timeout_ms=timeout_ms)
    c._handle = object()  # pretend connected

    buf = [raw_bytes]

    def _mock_read_exact(n: int) -> bytes:
        chunk = buf[0][:n]
        buf[0] = buf[0][n:]
        return chunk

    c._read_exact = _mock_read_exact   # type: ignore[method-assign]
    c._write_all = lambda data: None   # type: ignore[method-assign]
    return c


# ---------------------------------------------------------------------------
# Error path 1 — err field in CallResponse raises PipeClientError (Req 2.6)
# ---------------------------------------------------------------------------

class TestErrFieldRaisesPipeClientError(unittest.TestCase):
    """Requirement 2.6: when the server returns err, PipeClientError must be raised."""

    def test_send_code_raises_pipe_client_error_on_err_field(self):
        """send_code raises PipeClientError when the response carries an err string."""
        c = _client_with_canned_response(_make_framed_err("runtime error in R"))
        with self.assertRaises(PipeClientError) as ctx:
            c.send_code(["stop('runtime error in R')"])
        self.assertIn("runtime error in R", str(ctx.exception))

    def test_send_function_call_raises_pipe_client_error_on_err_field(self):
        """send_function_call raises PipeClientError when the response carries an err string."""
        c = _client_with_canned_response(_make_framed_err("unknown function: foo"))
        with self.assertRaises(PipeClientError) as ctx:
            c.send_function_call("foo", [])
        self.assertIn("unknown function: foo", str(ctx.exception))

    def test_read_response_raises_pipe_client_error_on_err_field(self):
        """_read_response raises PipeClientError directly for an err operation."""
        c = _client_with_canned_response(_make_framed_err("execution failed"))
        with self.assertRaises(PipeClientError) as ctx:
            c._read_response()
        self.assertIn("execution failed", str(ctx.exception))

    def test_error_is_not_pipe_protocol_error(self):
        """The exception raised for err field must be PipeClientError, not PipeProtocolError."""
        c = _client_with_canned_response(_make_framed_err("some error"))
        with self.assertRaises(PipeClientError) as ctx:
            c._read_response()
        # Must NOT be the more-specific PipeProtocolError subclass
        self.assertNotIsInstance(ctx.exception, PipeProtocolError)

    def test_empty_err_string_still_raises(self):
        """Even an empty err string must cause PipeClientError to be raised."""
        c = _client_with_canned_response(_make_framed_err(""))
        with self.assertRaises(PipeClientError):
            c._read_response()


# ---------------------------------------------------------------------------
# Error path 2 — mock pipe that never responds raises PipeTimeoutError (Req 2.7)
# ---------------------------------------------------------------------------

class TestTimeoutRaisesPipeTimeoutError(unittest.TestCase):
    """Requirement 2.7: a read that doesn't complete within timeout_ms raises
    PipeTimeoutError and closes the connection."""

    def _make_blocking_client(self, timeout_ms: int = 100) -> PipeClient:
        """Return a PipeClient whose _read_exactly_sync sleeps forever."""
        c = PipeClient(r"\\.\pipe\neven_test", timeout_ms=timeout_ms)
        c._handle = object()

        def _never_responds(n: int) -> bytes:
            time.sleep(60)  # far longer than any test timeout
            return b"\x00" * n  # unreachable

        c._read_exactly_sync = _never_responds  # type: ignore[method-assign]
        return c

    def test_read_exact_raises_pipe_timeout_error(self):
        """_read_exact raises PipeTimeoutError when the read thread exceeds timeout_ms."""
        c = self._make_blocking_client(timeout_ms=100)
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            with self.assertRaises(PipeTimeoutError):
                c._read_exact(4)

    def test_timeout_closes_the_connection(self):
        """_read_exact closes the pipe handle when it times out."""
        c = self._make_blocking_client(timeout_ms=100)
        self.assertIsNotNone(c._handle)

        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            with self.assertRaises(PipeTimeoutError):
                c._read_exact(4)

        self.assertIsNone(c._handle)

    def test_send_code_propagates_pipe_timeout_error(self):
        """send_code propagates PipeTimeoutError from the blocked read."""
        c = self._make_blocking_client(timeout_ms=100)
        c._write_all = lambda data: None  # type: ignore[method-assign]

        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            with self.assertRaises(PipeTimeoutError):
                c.send_code(["Sys.sleep(60)"])

    def test_timeout_error_is_subclass_of_pipe_client_error(self):
        """PipeTimeoutError must be a subclass of PipeClientError (Req 2.7)."""
        self.assertTrue(issubclass(PipeTimeoutError, PipeClientError))

    def test_timeout_error_message_mentions_ms(self):
        """PipeTimeoutError message should reference the timeout duration."""
        c = self._make_blocking_client(timeout_ms=100)
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            with self.assertRaises(PipeTimeoutError) as ctx:
                c._read_exact(4)
        self.assertIn("100", str(ctx.exception))


# ---------------------------------------------------------------------------
# Error path 3 — response length > 256 KB raises PipeProtocolError (Req 10.5)
# ---------------------------------------------------------------------------

class TestOversizedResponseRaisesPipeProtocolError(unittest.TestCase):
    """Requirement 10.5: a length prefix declaring > 256 KB must raise PipeProtocolError."""

    def _client_with_oversized_header(self, declared_length: int) -> PipeClient:
        """Return a PipeClient whose first _read_exact call returns a header
        declaring *declared_length* bytes, no payload is needed."""
        raw = struct.pack("<i", declared_length)
        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        buf = [raw]

        def _read_exact(n: int) -> bytes:
            chunk = buf[0][:n]
            buf[0] = buf[0][n:]
            return chunk

        c._read_exact = _read_exact   # type: ignore[method-assign]
        c._write_all = lambda data: None  # type: ignore[method-assign]
        return c

    def test_exactly_at_limit_does_not_raise(self):
        """A length header of exactly MAX_RESPONSE_BYTES must pass the size guard.

        The implementation uses `length > MAX_RESPONSE_BYTES` (strict greater-than),
        so a payload declared as exactly 256 KB must not be rejected by the guard.
        We verify this by confirming the size-guard code path is not taken — the
        test expects either a successful parse or a PipeProtocolError from the
        deserialization step (not the size-guard step).
        """
        limit = PipeClient.MAX_RESPONSE_BYTES

        # Build a real, small valid payload and use it as the actual content.
        # We declare the length as `limit` in the header but only supply the
        # real payload bytes — _read_exact is mocked so the "remaining" bytes
        # for the second call simply return the real payload regardless of `n`.
        var = variable_pb2.Variable()
        var.nil = True
        resp = variable_pb2.CallResponse()
        resp.result.CopyFrom(var)
        real_payload = resp.SerializeToString()

        header = struct.pack("<i", limit)
        call_count = [0]

        def _read_exact(n: int) -> bytes:
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: the 4-byte header
                return header
            else:
                # Second call: return the real (small) payload regardless of n.
                # This simulates receiving exactly the real_payload bytes.
                return real_payload

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        c._read_exact = _read_exact   # type: ignore[method-assign]

        # The size guard (length > MAX_RESPONSE_BYTES) must NOT fire here.
        # Any exception that follows is from deserialization or unexpected oneof,
        # NOT from the size check — so we assert it's not a size-limit message.
        try:
            c._read_response()
        except PipeProtocolError as exc:
            self.assertNotIn("exceeds", str(exc),
                             "Size guard must not fire for length == MAX_RESPONSE_BYTES")

    def test_one_byte_over_limit_raises(self):
        """A length of MAX_RESPONSE_BYTES + 1 must raise PipeProtocolError."""
        c = self._client_with_oversized_header(PipeClient.MAX_RESPONSE_BYTES + 1)
        with self.assertRaises(PipeProtocolError) as ctx:
            c._read_response()
        msg = str(ctx.exception)
        self.assertIn("exceeds", msg)

    def test_far_over_limit_raises(self):
        """A declared length of 10 MB must raise PipeProtocolError (not allocate buffer)."""
        ten_mb = 10 * 1024 * 1024
        c = self._client_with_oversized_header(ten_mb)
        with self.assertRaises(PipeProtocolError):
            c._read_response()

    def test_error_message_contains_size(self):
        """PipeProtocolError message should contain the declared size."""
        bad_size = PipeClient.MAX_RESPONSE_BYTES + 100
        c = self._client_with_oversized_header(bad_size)
        with self.assertRaises(PipeProtocolError) as ctx:
            c._read_response()
        self.assertIn(str(bad_size), str(ctx.exception))

    def test_unframe_also_enforces_limit(self):
        """_unframe module-level helper must also raise for oversized declared length."""
        from pipe_client import _unframe
        oversized = struct.pack("<i", PipeClient.MAX_RESPONSE_BYTES + 1)
        with self.assertRaises(PipeProtocolError):
            _unframe(oversized)


# ---------------------------------------------------------------------------
# Error path 4 — unparseable payload raises PipeProtocolError (Req 10.6)
# ---------------------------------------------------------------------------

class TestUnparseablePayloadRaisesPipeProtocolError(unittest.TestCase):
    """Requirement 10.6: a payload that can't be deserialized into CallResponse
    must raise PipeProtocolError, not return a partial object."""

    def _client_with_garbage_payload(self, garbage: bytes) -> PipeClient:
        header = struct.pack("<i", len(garbage))
        raw = header + garbage
        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        buf = [raw]

        def _read_exact(n: int) -> bytes:
            chunk = buf[0][:n]
            buf[0] = buf[0][n:]
            return chunk

        c._read_exact = _read_exact   # type: ignore[method-assign]
        c._write_all = lambda data: None  # type: ignore[method-assign]
        return c

    def test_random_garbage_raises(self):
        """Random bytes that aren't valid protobuf must raise PipeProtocolError."""
        garbage = b"\xff\xfe\xfd\xfc\xfb\xfa" * 8
        c = self._client_with_garbage_payload(garbage)
        with self.assertRaises(PipeProtocolError) as ctx:
            c._read_response()
        self.assertIn("deserialize", str(ctx.exception))

    def test_all_0xff_bytes_raises(self):
        """A payload of all 0xFF bytes must raise PipeProtocolError."""
        c = self._client_with_garbage_payload(b"\xff" * 20)
        with self.assertRaises(PipeProtocolError):
            c._read_response()

    def test_truncated_valid_payload_raises(self):
        """A payload that is a truncated (incomplete) valid protobuf must raise PipeProtocolError."""
        # Build a real message and strip the last byte to corrupt it
        resp = variable_pb2.CallResponse()
        resp.err = "some error"
        real_payload = resp.SerializeToString()
        truncated = real_payload[:-1]

        c = self._client_with_garbage_payload(truncated)
        with self.assertRaises(PipeProtocolError):
            c._read_response()

    def test_empty_payload_returns_default_message(self):
        """An empty payload (length=0) should parse as an empty CallResponse
        without raising — the oneof is unset, so an unexpected-variant error fires."""
        c = self._client_with_garbage_payload(b"")
        # Empty protobuf is technically valid (no fields set), but _read_response
        # then hits the unexpected oneof case; either PipeProtocolError is acceptable.
        with self.assertRaises(PipeProtocolError):
            c._read_response()

    def test_unframe_raises_for_bad_payload(self):
        """_unframe module-level helper must also raise PipeProtocolError for garbage."""
        from pipe_client import _unframe
        garbage = b"\xff\xfe" * 10
        raw = struct.pack("<i", len(garbage)) + garbage
        with self.assertRaises(PipeProtocolError):
            _unframe(raw)


# ---------------------------------------------------------------------------
# Error path 5 — context manager calls close() on exit (Req 2.9)
# ---------------------------------------------------------------------------

class TestContextManagerCallsClose(unittest.TestCase):
    """Requirement 2.9: 'with PipeClient(...) as c:' must call close() on exit."""

    def test_close_called_on_normal_exit(self):
        """close() is invoked after the with block exits normally."""
        close_calls = []

        c = PipeClient(r"\\.\pipe\neven_test")
        # Use patch.object so the real Win32 CloseHandle is never reached
        with patch.object(c, "close", side_effect=lambda: close_calls.append(True)):
            with c:
                pass

        self.assertEqual(len(close_calls), 1,
                         "close() must be called exactly once on normal exit")

    def test_close_called_on_exception_exit(self):
        """close() is invoked even when an exception propagates out of the with block."""
        close_calls = []

        c = PipeClient(r"\\.\pipe\neven_test")
        with patch.object(c, "close", side_effect=lambda: close_calls.append(True)):
            try:
                with c:
                    raise RuntimeError("intentional error")
            except RuntimeError:
                pass

        self.assertEqual(len(close_calls), 1,
                         "close() must be called exactly once even when an exception occurs")

    def test_with_statement_sets_handle_none_on_exit(self):
        """After the with block, _handle must be None (connection is closed)."""
        with patch("pipe_client._WIN32_BACKEND", "pywin32"), \
             patch("pipe_client.win32api"):
            c = PipeClient(r"\\.\pipe\neven_test")
            sentinel = object()
            c._handle = sentinel

            with c:
                self.assertIs(c._handle, sentinel,
                              "_handle must be set during block execution")

            self.assertIsNone(c._handle,
                              "_handle must be None after the with block exits")

    def test_enter_returns_same_client_instance(self):
        """__enter__ must return the PipeClient instance (enables 'as c:' binding)."""
        c = PipeClient(r"\\.\pipe\neven_test")
        result = c.__enter__()
        self.assertIs(result, c)
        # Clean up (no real handle to close)
        c._handle = None

    def test_patch_object_approach(self):
        """Verify context manager via patch.object on close (alternative approach)."""
        c = PipeClient(r"\\.\pipe\neven_test")
        with patch.object(c, "close") as mock_close:
            with c:
                mock_close.assert_not_called()
            mock_close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
