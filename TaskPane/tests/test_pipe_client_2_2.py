"""Tests for task 2.2: send_code, send_function_call, and _read_response.

Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
"""

from __future__ import annotations

import struct
import sys
import os
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
    _frame,
)
import variable_pb2


# ---------------------------------------------------------------------------
# Helpers
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
    """Return a PipeClient whose _read_exact is backed by *raw_bytes*."""
    c = PipeClient(r"\\.\pipe\neven_test", timeout_ms=timeout_ms)
    c._handle = object()  # pretend connected

    buf = [raw_bytes]  # mutable so the lambda can close over it

    def _mock_read_exact(n: int) -> bytes:
        chunk = buf[0][:n]
        buf[0] = buf[0][n:]
        return chunk

    c._read_exact = _mock_read_exact  # type: ignore[method-assign]

    # _write_all is a no-op — we don't need a real pipe
    c._write_all = lambda data: None  # type: ignore[method-assign]

    return c


# ---------------------------------------------------------------------------
# 1. send_code — happy path
# ---------------------------------------------------------------------------

class TestSendCode(unittest.TestCase):
    def test_returns_integer_variable(self):
        """send_code returns the Variable from the server response."""
        var = variable_pb2.Variable()
        var.integer = 42
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_code(["x <- 42", "x"])
        self.assertEqual(result.WhichOneof("value"), "integer")
        self.assertEqual(result.integer, 42)

    def test_returns_real_variable(self):
        var = variable_pb2.Variable()
        var.real = 3.14
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_code(["3.14"])
        self.assertEqual(result.WhichOneof("value"), "real")
        self.assertAlmostEqual(result.real, 3.14)

    def test_returns_str_variable(self):
        var = variable_pb2.Variable()
        var.str = "hello"
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_code(["'hello'"])
        self.assertEqual(result.str, "hello")

    def test_returns_boolean_variable(self):
        var = variable_pb2.Variable()
        var.boolean = True
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_code(["TRUE"])
        self.assertTrue(result.boolean)

    def test_returns_nil_variable(self):
        var = variable_pb2.Variable()
        var.nil = True
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_code(["NULL"])
        self.assertEqual(result.WhichOneof("value"), "nil")

    def test_sends_framed_message_with_lines(self):
        """send_code writes a framed CallResponse containing the code lines."""
        var = variable_pb2.Variable()
        var.integer = 1
        written_chunks: list[bytes] = []

        c = PipeClient(r"\\.\pipe\neven_test", timeout_ms=5_000)
        c._handle = object()
        c._write_all = lambda data: written_chunks.append(data)  # type: ignore[method-assign]
        c._read_exact = _client_with_canned_response(
            _make_framed_result(var)
        )._read_exact  # type: ignore[method-assign]

        c.send_code(["line1", "line2"])

        self.assertEqual(len(written_chunks), 1)
        framed = written_chunks[0]
        # decode the framed bytes to verify lines are present
        (length,) = struct.unpack("<i", framed[:4])
        payload = framed[4 : 4 + length]
        decoded = variable_pb2.CallResponse()
        decoded.ParseFromString(payload)
        self.assertEqual(list(decoded.code.line), ["line1", "line2"])

    def test_raises_pipe_client_error_on_err_response(self):
        """send_code raises PipeClientError when the server replies with err."""
        c = _client_with_canned_response(_make_framed_err("syntax error"))
        with self.assertRaises(PipeClientError) as ctx:
            c.send_code(["bad code {{"])
        self.assertIn("syntax error", str(ctx.exception))

    def test_wait_flag_is_set_in_outgoing_message(self):
        """send_code sets the wait=True field on the outgoing CallResponse by default."""
        var = variable_pb2.Variable()
        var.integer = 0
        written_chunks: list[bytes] = []

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        c._write_all = lambda data: written_chunks.append(data)  # type: ignore[method-assign]
        c._read_exact = _client_with_canned_response(
            _make_framed_result(var)
        )._read_exact  # type: ignore[method-assign]

        c.send_code(["x"], wait=True)
        (length,) = struct.unpack("<i", written_chunks[0][:4])
        payload = written_chunks[0][4 : 4 + length]
        decoded = variable_pb2.CallResponse()
        decoded.ParseFromString(payload)
        self.assertTrue(decoded.wait)


# ---------------------------------------------------------------------------
# 2. send_function_call — happy path
# ---------------------------------------------------------------------------

class TestSendFunctionCall(unittest.TestCase):
    def test_returns_result_variable(self):
        """send_function_call returns the Variable from the server response."""
        var = variable_pb2.Variable()
        var.real = 2.718
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_function_call("exp", [], variable_pb2.CallTarget.Value("language"))
        self.assertAlmostEqual(result.real, 2.718)

    def test_sends_correct_function_name(self):
        """send_function_call encodes the function name in the outgoing message."""
        var = variable_pb2.Variable()
        var.nil = True
        written_chunks: list[bytes] = []

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        c._write_all = lambda data: written_chunks.append(data)  # type: ignore[method-assign]
        c._read_exact = _client_with_canned_response(
            _make_framed_result(var)
        )._read_exact  # type: ignore[method-assign]

        c.send_function_call("list-functions", [], variable_pb2.CallTarget.Value("system"))

        (length,) = struct.unpack("<i", written_chunks[0][:4])
        payload = written_chunks[0][4 : 4 + length]
        decoded = variable_pb2.CallResponse()
        decoded.ParseFromString(payload)
        self.assertEqual(decoded.function_call.function, "list-functions")
        self.assertEqual(decoded.function_call.target, variable_pb2.CallTarget.Value("system"))

    def test_sends_arguments(self):
        """send_function_call encodes the Variable arguments in the outgoing message."""
        var = variable_pb2.Variable()
        var.integer = 99
        written_chunks: list[bytes] = []

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        c._write_all = lambda data: written_chunks.append(data)  # type: ignore[method-assign]
        c._read_exact = _client_with_canned_response(
            _make_framed_result(var)
        )._read_exact  # type: ignore[method-assign]

        arg1 = variable_pb2.Variable()
        arg1.integer = 7
        arg2 = variable_pb2.Variable()
        arg2.str = "hello"
        c.send_function_call("my_func", [arg1, arg2])

        (length,) = struct.unpack("<i", written_chunks[0][:4])
        payload = written_chunks[0][4 : 4 + length]
        decoded = variable_pb2.CallResponse()
        decoded.ParseFromString(payload)
        self.assertEqual(len(decoded.function_call.arguments), 2)
        self.assertEqual(decoded.function_call.arguments[0].integer, 7)
        self.assertEqual(decoded.function_call.arguments[1].str, "hello")

    def test_default_target_is_language(self):
        """send_function_call defaults to CallTarget.language (0)."""
        var = variable_pb2.Variable()
        var.nil = True
        written_chunks: list[bytes] = []

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        c._write_all = lambda data: written_chunks.append(data)  # type: ignore[method-assign]
        c._read_exact = _client_with_canned_response(
            _make_framed_result(var)
        )._read_exact  # type: ignore[method-assign]

        c.send_function_call("my_func", [])

        (length,) = struct.unpack("<i", written_chunks[0][:4])
        payload = written_chunks[0][4 : 4 + length]
        decoded = variable_pb2.CallResponse()
        decoded.ParseFromString(payload)
        self.assertEqual(decoded.function_call.target, variable_pb2.CallTarget.Value("language"))

    def test_raises_pipe_client_error_on_err_response(self):
        """send_function_call raises PipeClientError on an err response."""
        c = _client_with_canned_response(_make_framed_err("unknown function"))
        with self.assertRaises(PipeClientError) as ctx:
            c.send_function_call("nonexistent", [])
        self.assertIn("unknown function", str(ctx.exception))


# ---------------------------------------------------------------------------
# 3. _read_response — error paths
# ---------------------------------------------------------------------------

class TestReadResponse(unittest.TestCase):
    def test_raises_pipe_protocol_error_on_oversized_response(self):
        """_read_response raises PipeProtocolError when length > MAX_RESPONSE_BYTES."""
        # Build a header that declares a length just above the 256 KB limit
        oversized_length = PipeClient.MAX_RESPONSE_BYTES + 1
        raw = struct.pack("<i", oversized_length)  # only the 4-byte header

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()

        buf = [raw]

        def _mock_read_exact(n: int) -> bytes:
            chunk = buf[0][:n]
            buf[0] = buf[0][n:]
            return chunk

        c._read_exact = _mock_read_exact  # type: ignore[method-assign]
        c._write_all = lambda data: None  # type: ignore[method-assign]

        with self.assertRaises(PipeProtocolError) as ctx:
            c._read_response()
        self.assertIn("exceeds", str(ctx.exception))

    def test_raises_pipe_protocol_error_on_negative_length(self):
        """_read_response raises PipeProtocolError when length is negative."""
        raw = struct.pack("<i", -1)

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        buf = [raw]
        c._read_exact = lambda n: (buf.__setitem__(0, buf[0][n:]) or buf[0][:n]) if False else (lambda n2: (buf[0][:n2], buf.__setitem__(0, buf[0][n2:]))[0])(n)  # noqa: E501
        # simpler inline version:
        data_holder = [raw]

        def _read_exact_neg(n: int) -> bytes:
            chunk = data_holder[0][:n]
            data_holder[0] = data_holder[0][n:]
            return chunk

        c._read_exact = _read_exact_neg  # type: ignore[method-assign]

        with self.assertRaises(PipeProtocolError):
            c._read_response()

    def test_raises_pipe_protocol_error_on_bad_protobuf(self):
        """_read_response raises PipeProtocolError if payload can't be deserialized."""
        garbage = b"\xff\xfe\xfd\xfc" * 10  # not valid protobuf
        header = struct.pack("<i", len(garbage))
        raw = header + garbage

        c = PipeClient(r"\\.\pipe\neven_test")
        c._handle = object()
        buf = [raw]

        def _read_exact_garbage(n: int) -> bytes:
            chunk = buf[0][:n]
            buf[0] = buf[0][n:]
            return chunk

        c._read_exact = _read_exact_garbage  # type: ignore[method-assign]
        c._write_all = lambda data: None  # type: ignore[method-assign]

        with self.assertRaises(PipeProtocolError) as ctx:
            c._read_response()
        self.assertIn("deserialize", str(ctx.exception))

    def test_raises_pipe_client_error_on_err_operation(self):
        """_read_response raises PipeClientError when operation is err."""
        c = _client_with_canned_response(_make_framed_err("execution failed"))
        with self.assertRaises(PipeClientError) as ctx:
            c._read_response()
        self.assertIn("execution failed", str(ctx.exception))

    def test_returns_result_variable(self):
        """_read_response returns the Variable when operation is result."""
        var = variable_pb2.Variable()
        var.str = "done"
        c = _client_with_canned_response(_make_framed_result(var))
        result = c._read_response()
        self.assertEqual(result.str, "done")

    def test_raises_pipe_protocol_error_on_unexpected_operation(self):
        """_read_response raises PipeProtocolError for unexpected oneof variants."""
        # Build a response with operation=console (an unexpected push message)
        resp = variable_pb2.CallResponse()
        resp.console.text = "hello from console"
        raw = _frame(resp)

        c = _client_with_canned_response(raw)
        with self.assertRaises(PipeProtocolError) as ctx:
            c._read_response()
        self.assertIn("console", str(ctx.exception))


# ---------------------------------------------------------------------------
# 4. Smoke test — callable signatures
# ---------------------------------------------------------------------------

class TestSmokeCallable(unittest.TestCase):
    """Confirm the three methods exist and are callable with expected signatures."""

    def test_send_code_is_callable(self):
        c = PipeClient(r"\\.\pipe\neven_test")
        self.assertTrue(callable(c.send_code))

    def test_send_function_call_is_callable(self):
        c = PipeClient(r"\\.\pipe\neven_test")
        self.assertTrue(callable(c.send_function_call))

    def test_read_response_is_callable(self):
        c = PipeClient(r"\\.\pipe\neven_test")
        self.assertTrue(callable(c._read_response))

    def test_send_code_returns_variable(self):
        """End-to-end smoke: send_code returns a Variable with the expected field."""
        var = variable_pb2.Variable()
        var.integer = 7
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_code(["7"])
        self.assertIsInstance(result, variable_pb2.Variable)
        self.assertEqual(result.integer, 7)

    def test_send_function_call_returns_variable(self):
        """End-to-end smoke: send_function_call returns a Variable."""
        var = variable_pb2.Variable()
        var.boolean = False
        c = _client_with_canned_response(_make_framed_result(var))
        result = c.send_function_call("some_fn", [])
        self.assertIsInstance(result, variable_pb2.Variable)
        self.assertFalse(result.boolean)


if __name__ == "__main__":
    unittest.main()
