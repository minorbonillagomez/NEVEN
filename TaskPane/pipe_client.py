# Copyright (c) 2026 RJ2XCL Project
#
# This file is part of RJ2XCL / NEVEN Studio Standalone.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Named Pipe client for NEVEN Control processes.

Speaks the 4-byte-framed Protobuf ``CallResponse`` protocol that every
Control*.exe process (ControlR.exe, ControlJulia.exe, ControlPython.exe)
implements via ``MessageUtilities::Frame`` / ``MessageUtilities::Unframe``.

Usage::

    with PipeClient(r"\\\\.\\pipe\\neven_r", timeout_ms=30_000) as client:
        result = client.send_code(["1 + 1"])

Platform note
-------------
On Windows the primary I/O path uses ``pywin32`` (``win32file`` /
``win32api``).  When ``pywin32`` is not installed (e.g. in a CI environment
or on macOS/Linux) a ``ctypes``-based Win32 fallback is attempted.  On
non-Windows the fallback also stubs out to raise ``OSError``, keeping the
module importable for unit testing.
"""

from __future__ import annotations

import struct
import threading
from typing import Any

# ---------------------------------------------------------------------------
# Protobuf import
# ---------------------------------------------------------------------------
try:
    import variable_pb2  # type: ignore[import]
except ModuleNotFoundError:
    # Allow the module to be imported in environments where the generated
    # protobuf stubs are not on PYTHONPATH (e.g. running tests from the
    # workspace root rather than C:\\NEVEN\\taskpane\\).
    import sys
    import os

    _pb_candidates = [
        os.path.join(os.path.dirname(__file__)),          # same dir as this file
        r"C:\NEVEN\taskpane",
    ]
    for _p in _pb_candidates:
        if _p not in sys.path and os.path.isdir(_p):
            sys.path.insert(0, _p)
    import variable_pb2  # type: ignore[import]

# ---------------------------------------------------------------------------
# Win32 backend selection
# ---------------------------------------------------------------------------
try:
    import win32file  # type: ignore[import]
    import win32api   # type: ignore[import]
    import pywintypes  # type: ignore[import]
    _WIN32_BACKEND = "pywin32"
except ImportError:
    win32file = None  # type: ignore[assignment]
    win32api = None   # type: ignore[assignment]
    pywintypes = None  # type: ignore[assignment]
    _WIN32_BACKEND = "ctypes"

if _WIN32_BACKEND == "ctypes":
    import ctypes
    import ctypes.wintypes as _wt
    import sys as _sys

    if _sys.platform == "win32":
        _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        # CreateFileW
        _kernel32.CreateFileW.restype = _wt.HANDLE
        _kernel32.CreateFileW.argtypes = [
            _wt.LPCWSTR,   # lpFileName
            _wt.DWORD,     # dwDesiredAccess
            _wt.DWORD,     # dwShareMode
            ctypes.c_void_p,  # lpSecurityAttributes
            _wt.DWORD,     # dwCreationDisposition
            _wt.DWORD,     # dwFlagsAndAttributes
            _wt.HANDLE,    # hTemplateFile
        ]

        # ReadFile
        _kernel32.ReadFile.restype = _wt.BOOL
        _kernel32.ReadFile.argtypes = [
            _wt.HANDLE,          # hFile
            ctypes.c_void_p,     # lpBuffer
            _wt.DWORD,           # nNumberOfBytesToRead
            ctypes.POINTER(_wt.DWORD),  # lpNumberOfBytesRead
            ctypes.c_void_p,     # lpOverlapped
        ]

        # WriteFile
        _kernel32.WriteFile.restype = _wt.BOOL
        _kernel32.WriteFile.argtypes = [
            _wt.HANDLE,
            ctypes.c_void_p,
            _wt.DWORD,
            ctypes.POINTER(_wt.DWORD),
            ctypes.c_void_p,
        ]

        # CloseHandle
        _kernel32.CloseHandle.restype = _wt.BOOL
        _kernel32.CloseHandle.argtypes = [_wt.HANDLE]

        _INVALID_HANDLE_VALUE: int = ctypes.c_void_p(-1).value  # type: ignore[assignment]
        _GENERIC_READ = 0x80000000
        _GENERIC_WRITE = 0x40000000
        _OPEN_EXISTING = 3
        _FILE_ATTRIBUTE_NORMAL = 0x80
    else:
        # Non-Windows: no kernel32 available; stubs will raise OSError.
        _kernel32 = None  # type: ignore[assignment]
        _INVALID_HANDLE_VALUE = -1


# ---------------------------------------------------------------------------
# Exception hierarchy  (Requirement 2.6, 2.7, 10.5, 10.6)
# ---------------------------------------------------------------------------

class PipeClientError(Exception):
    """Base exception for all Named Pipe client errors."""


class PipeTimeoutError(PipeClientError):
    """Raised when a pipe read does not complete within ``timeout_ms``."""


class PipeProtocolError(PipeClientError):
    """Raised when the framing or Protobuf deserialization is invalid."""


# ---------------------------------------------------------------------------
# Module-level framing helpers  (Requirements 2.2, 2.3, 2.4, 10.1, 10.2)
# ---------------------------------------------------------------------------

def _frame(msg: variable_pb2.CallResponse) -> bytes:
    """Serialize *msg* with a 4-byte little-endian signed int32 length prefix.

    Matches ``MessageUtilities::Frame`` in ``message_utilities.cc`` exactly:
    the prefix is the byte length of the serialized Protobuf payload packed
    as a signed 32-bit integer in little-endian byte order.
    """
    payload: bytes = msg.SerializeToString()
    length_prefix: bytes = struct.pack("<i", len(payload))  # signed 32-bit LE
    return length_prefix + payload


def _unframe(data: bytes) -> variable_pb2.CallResponse:
    """Deserialize a framed byte string produced by ``_frame`` or the C++ equivalent.

    Reads the 4-byte length prefix, enforces the 256 KB hard limit
    (``kMaxDynamicBufferSize``), and parses the Protobuf payload.

    Raises
    ------
    PipeProtocolError
        If *data* is too short, the declared length exceeds 256 KB, or the
        payload cannot be deserialized into a ``CallResponse``.
    """
    if len(data) < 4:
        raise PipeProtocolError(
            f"Response too short: expected at least 4 bytes, got {len(data)}"
        )
    (length,) = struct.unpack("<i", data[:4])
    if length > PipeClient.MAX_RESPONSE_BYTES:
        raise PipeProtocolError(
            f"Response size {length} exceeds {PipeClient.MAX_RESPONSE_BYTES} byte limit"
        )
    if length < 0:
        raise PipeProtocolError(f"Response length prefix is negative: {length}")
    payload = data[4 : 4 + length]
    msg = variable_pb2.CallResponse()
    try:
        ok = msg.ParseFromString(payload)
    except Exception as exc:
        raise PipeProtocolError(
            f"Failed to deserialize CallResponse: {exc}"
        ) from exc
    if not ok:
        raise PipeProtocolError("Failed to deserialize CallResponse")
    return msg


# ---------------------------------------------------------------------------
# PipeClient class  (Requirements 2.1, 2.7, 2.8, 2.9, 9.4)
# ---------------------------------------------------------------------------

class PipeClient:
    """Python client for a Control*.exe Named Pipe endpoint.

    Parameters
    ----------
    pipe_name:
        Full Win32 named pipe path, e.g. ``\\\\\\\\.\\\\pipe\\\\neven_r``.
    timeout_ms:
        Read/write timeout in milliseconds (default: 60,000 ms).
    """

    MAX_RESPONSE_BYTES: int = 256 * 1024  # kMaxDynamicBufferSize

    def __init__(self, pipe_name: str, timeout_ms: int = 60_000) -> None:
        self._pipe_name: str = pipe_name
        self._timeout_ms: int = timeout_ms
        self._handle: Any = None  # HANDLE (pywin32) or ctypes HANDLE or None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "PipeClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Public connection API
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open a ``CreateFile`` handle to the Named Pipe.

        Raises ``OSError`` on failure (e.g. pipe not found, access denied).
        The handle is stored internally and used by all subsequent I/O.
        """
        if _WIN32_BACKEND == "pywin32":
            self._handle = self._connect_pywin32()
        else:
            self._handle = self._connect_ctypes()

    def close(self) -> None:
        """Close the pipe handle.  Idempotent — safe to call multiple times."""
        if self._handle is None:
            return
        try:
            if _WIN32_BACKEND == "pywin32":
                win32api.CloseHandle(self._handle)
            else:
                self._close_ctypes(self._handle)
        finally:
            self._handle = None

    # ------------------------------------------------------------------
    # Internal: connect helpers
    # ------------------------------------------------------------------

    def _connect_pywin32(self) -> Any:
        """Open the pipe using pywin32's ``CreateFile``."""
        try:
            handle = win32file.CreateFile(
                self._pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,           # no sharing
                None,        # default security
                win32file.OPEN_EXISTING,
                0,           # normal attributes (synchronous I/O)
                None,
            )
        except pywintypes.error as exc:
            raise OSError(
                f"Cannot open named pipe {self._pipe_name!r}: {exc}"
            ) from exc
        return handle

    def _connect_ctypes(self) -> Any:
        """Open the pipe using the ctypes Win32 fallback."""
        if _kernel32 is None:
            raise OSError(
                "Named pipes are only available on Windows; "
                f"cannot connect to {self._pipe_name!r}"
            )
        handle = _kernel32.CreateFileW(
            self._pipe_name,
            _GENERIC_READ | _GENERIC_WRITE,
            0,
            None,
            _OPEN_EXISTING,
            _FILE_ATTRIBUTE_NORMAL,
            None,
        )
        if handle == _INVALID_HANDLE_VALUE:
            err = ctypes.get_last_error()
            raise OSError(
                err,
                f"Cannot open named pipe {self._pipe_name!r} "
                f"(Win32 error {err})",
            )
        return handle

    def _close_ctypes(self, handle: Any) -> None:
        """Close a ctypes Win32 handle."""
        if _kernel32 is not None:
            _kernel32.CloseHandle(handle)

    # ------------------------------------------------------------------
    # Internal: low-level I/O
    # ------------------------------------------------------------------

    def _read_exact(self, n: int) -> bytes:
        """Read exactly *n* bytes from the pipe, enforcing ``timeout_ms``.

        A background thread performs the blocking ``ReadFile``/``read`` call;
        the calling thread joins with a ``timeout_ms / 1000`` second deadline.
        If the deadline expires before all bytes are received the pipe is
        closed and ``PipeTimeoutError`` is raised.

        Raises
        ------
        PipeTimeoutError
            If the read does not complete within ``self._timeout_ms``.
        PipeClientError
            If the pipe is closed by the server (0 bytes returned mid-read)
            or an I/O error occurs.
        """
        result: list[bytes] = []
        exc_holder: list[Exception] = []

        def _read_worker() -> None:
            try:
                data = self._read_exactly_sync(n)
                result.append(data)
            except Exception as exc:  # noqa: BLE001
                exc_holder.append(exc)

        worker = threading.Thread(target=_read_worker, daemon=True)
        worker.start()
        worker.join(timeout=self._timeout_ms / 1000.0)

        if worker.is_alive():
            # The read is still blocked — close the handle to unblock it and
            # raise PipeTimeoutError.
            self.close()
            raise PipeTimeoutError(
                f"Pipe read timed out after {self._timeout_ms} ms"
            )

        if exc_holder:
            raise exc_holder[0]

        return result[0]

    def _read_exactly_sync(self, n: int) -> bytes:
        """Blocking read of exactly *n* bytes.  Called from the worker thread."""
        buf = b""
        remaining = n
        while remaining > 0:
            chunk = self._read_chunk(remaining)
            if not chunk:
                raise PipeClientError("Pipe closed by server")
            buf += chunk
            remaining -= len(chunk)
        return buf

    def _read_chunk(self, n: int) -> bytes:
        """Read up to *n* bytes from the underlying handle."""
        if _WIN32_BACKEND == "pywin32":
            _err, data = win32file.ReadFile(self._handle, n)
            return bytes(data)
        else:
            return self._read_chunk_ctypes(n)

    def _read_chunk_ctypes(self, n: int) -> bytes:
        """ctypes ReadFile wrapper."""
        buf = ctypes.create_string_buffer(n)
        bytes_read = _wt.DWORD(0)
        ok = _kernel32.ReadFile(
            self._handle,
            buf,
            _wt.DWORD(n),
            ctypes.byref(bytes_read),
            None,
        )
        if not ok:
            err = ctypes.get_last_error()
            raise PipeClientError(f"ReadFile failed with Win32 error {err}")
        return buf.raw[: bytes_read.value]

    def _write_all(self, data: bytes) -> None:
        """Write *data* to the pipe, flushing completely."""
        if _WIN32_BACKEND == "pywin32":
            win32file.WriteFile(self._handle, data)
        else:
            self._write_all_ctypes(data)

    def _write_all_ctypes(self, data: bytes) -> None:
        """ctypes WriteFile wrapper."""
        buf = ctypes.create_string_buffer(data)
        written = _wt.DWORD(0)
        ok = _kernel32.WriteFile(
            self._handle,
            buf,
            _wt.DWORD(len(data)),
            ctypes.byref(written),
            None,
        )
        if not ok:
            err = ctypes.get_last_error()
            raise PipeClientError(f"WriteFile failed with Win32 error {err}")

    # ------------------------------------------------------------------
    # Public send API  (Requirements 2.2, 2.3, 2.5, 2.6)
    # ------------------------------------------------------------------

    def send_code(
        self,
        lines: list,
        wait: bool = True,
    ) -> "variable_pb2.Variable":
        """Send a code execution request and return the result Variable.

        Builds a ``CallResponse{code=Code{line=lines}}``, frames it, writes
        it to the pipe, reads the response via ``_read_response``, and
        returns the ``result`` Variable.  If the server replies with ``err``
        the string is wrapped in a ``PipeClientError`` and raised.

        Parameters
        ----------
        lines:
            Script lines to execute (each element is one line of code).
        wait:
            Sets the ``wait`` field on the ``CallResponse`` message.
            When ``True`` (default) the server executes synchronously and
            returns a result before the next message is processed.

        Returns
        -------
        variable_pb2.Variable
            The ``result`` Variable from the server response.

        Raises
        ------
        PipeClientError
            If the server returns an ``err`` string in the response.
        PipeTimeoutError
            If the response is not received within ``timeout_ms``.
        PipeProtocolError
            If framing or deserialization fails.
        """
        msg = variable_pb2.CallResponse()
        msg.wait = wait
        msg.code.line.extend(lines)
        self._write_all(_frame(msg))
        return self._read_response()

    def send_function_call(
        self,
        function: str,
        arguments: list,
        target: int = variable_pb2.CallTarget.Value("language"),
    ) -> "variable_pb2.Variable":
        """Send a function call request and return the result Variable.

        Builds a ``CallResponse{function_call=CompositeFunctionCall{...}}``,
        frames it, writes it to the pipe, reads the response, and returns
        the ``result`` Variable.

        Parameters
        ----------
        function:
            Name of the function to call on the language side.
        arguments:
            List of ``variable_pb2.Variable`` instances to pass as arguments.
        target:
            ``CallTarget`` enum value (default: ``language`` = 0).  Use
            ``variable_pb2.CallTarget.Value("system")`` for system calls such
            as ``list-functions``.

        Returns
        -------
        variable_pb2.Variable
            The ``result`` Variable from the server response.

        Raises
        ------
        PipeClientError
            If the server returns an ``err`` string in the response.
        PipeTimeoutError
            If the response is not received within ``timeout_ms``.
        PipeProtocolError
            If framing or deserialization fails.
        """
        msg = variable_pb2.CallResponse()
        msg.function_call.function = function
        msg.function_call.arguments.extend(arguments)
        msg.function_call.target = target
        self._write_all(_frame(msg))
        return self._read_response()

    # ------------------------------------------------------------------
    # Internal: response reader  (Requirements 2.4, 2.6, 10.5, 10.6)
    # ------------------------------------------------------------------

    def _read_response(self) -> "variable_pb2.Variable":
        """Read one framed response from the pipe and return the result Variable.

        Protocol (matches ``MessageUtilities::Unframe``):

        1. Read 4 bytes → signed 32-bit little-endian payload length.
        2. Enforce ``MAX_RESPONSE_BYTES`` (256 KB) hard limit.
        3. Read exactly ``length`` bytes → Protobuf payload.
        4. Deserialize into ``CallResponse``.
        5. Inspect the ``operation`` oneof:
           - ``"result"`` → return the ``Variable``.
           - ``"err"``    → raise ``PipeClientError(response.err)``.
           - anything else (console, function_list, …) → raise
             ``PipeProtocolError`` describing the unexpected variant.

        Returns
        -------
        variable_pb2.Variable
            The ``result`` Variable sent by the server.

        Raises
        ------
        PipeClientError
            If the ``operation`` oneof is ``err``.
        PipeProtocolError
            If the response length exceeds 256 KB, the payload cannot be
            deserialized, or the ``operation`` oneof is an unexpected variant.
        PipeTimeoutError
            (propagated from ``_read_exact``) if the deadline is exceeded.
        """
        # --- Step 1: read 4-byte length prefix ---
        header = self._read_exact(4)
        (length,) = struct.unpack("<i", header)

        # --- Step 2: enforce size limit (Requirement 10.5) ---
        if length < 0:
            raise PipeProtocolError(
                f"Response length prefix is negative: {length}"
            )
        if length > self.MAX_RESPONSE_BYTES:
            raise PipeProtocolError(
                f"Response size {length} exceeds {self.MAX_RESPONSE_BYTES} byte limit"
            )

        # --- Step 3: read payload ---
        payload = self._read_exact(length)

        # --- Step 4: deserialize (Requirement 10.6) ---
        response = variable_pb2.CallResponse()
        try:
            ok = response.ParseFromString(payload)
        except Exception as exc:
            raise PipeProtocolError(
                f"Failed to deserialize CallResponse: {exc}"
            ) from exc
        if not ok:
            raise PipeProtocolError("Failed to deserialize CallResponse")

        # --- Step 5: inspect oneof variant ---
        which = response.WhichOneof("operation")

        if which == "result":
            return response.result

        if which == "err":
            # Requirement 2.6: raise PipeClientError with the error string
            raise PipeClientError(response.err)

        # Unexpected oneof variant (console push, function_list, etc.)
        raise PipeProtocolError(
            f"Unexpected CallResponse.operation variant: {which!r}"
        )


# ---------------------------------------------------------------------------
# Variable → Python type conversion helper  (Requirements 2.5, 3.5, 3.6, 3.7)
# ---------------------------------------------------------------------------

def variable_to_python(var: "variable_pb2.Variable") -> Any:
    """Convert a Protobuf ``Variable`` message to a native Python value.

    Dispatches on the ``value`` oneof field of *var* and returns the
    appropriate Python type.

    Mapping
    -------
    * ``integer``      → ``int``
    * ``real``         → ``float``
    * ``str``          → ``str``
    * ``boolean``      → ``bool``
    * ``nil``          → ``None``
    * ``missing``      → ``None``
    * ``arr``          → ``dict`` with keys ``"columns"`` (list[str]) and
                         ``"rows"`` (list[list[any]])
    * ``html_content`` → ``dict`` with keys ``"html"`` (str) and
                         ``"title"`` (str)
    * ``err``          → raises ``PipeClientError(var.err.message)``

    Parameters
    ----------
    var:
        A ``variable_pb2.Variable`` protobuf message.

    Returns
    -------
    any
        The Python-native equivalent of the variable's value.

    Raises
    ------
    PipeClientError
        When the ``err`` oneof is set in *var*.
    """
    which = var.WhichOneof("value")

    if which == "integer":
        return int(var.integer)

    if which == "real":
        return float(var.real)

    if which == "str":
        return str(var.str)

    if which == "boolean":
        return bool(var.boolean)

    if which in ("nil", "missing"):
        return None

    if which == "err":
        raise PipeClientError(var.err.message)

    if which == "arr":
        arr = var.arr
        columns: list[str] = list(arr.colnames)
        num_rows: int = arr.rows
        num_cols: int = arr.cols

        # arr.data is a flat row-major list of Variables with length rows*cols.
        # Reconstruct as a list-of-lists using variable_to_python recursively.
        flat = [variable_to_python(cell) for cell in arr.data]
        if num_cols > 0 and num_rows > 0:
            rows: list[list[Any]] = [
                flat[r * num_cols : (r + 1) * num_cols]
                for r in range(num_rows)
            ]
        else:
            rows = []

        return {"columns": columns, "rows": rows}

    if which == "html_content":
        hc = var.html_content
        return {"html": hc.html, "title": hc.title}

    # Unrecognised or unset oneof — return None (treat as nil/missing)
    return None
