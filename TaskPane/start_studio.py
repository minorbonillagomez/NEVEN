# Copyright (c) 2026 RJ2XCL Project
#
# This file is part of RJ2XCL / NEVEN Studio Standalone.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""NEVEN Studio Standalone — Launcher.

Entry point::

    python start_studio.py [--config PATH] [--port INT] [--languages LIST] [--no-browser]

This module covers tasks 4.1, 4.2, and 4.3:
  - 4.1: CLI argument parsing, config loading, language resolution, executable discovery.
  - 4.2: Process launch, pipe readiness polling, and PID file management.
  - 4.3: HTTP server wiring, URL print, browser open, process monitoring, and signal handling.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10,
              8.5, 8.6, 9.1, 9.2, 9.3, 9.6
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Platform detection — pipe polling is Windows-only (Requirement 1.5, 4.7)
# ---------------------------------------------------------------------------
_IS_WINDOWS = sys.platform == "win32"

# Win32 backend for pipe probing (mirrors pipe_client.py approach)
if _IS_WINDOWS:
    try:
        import win32file   # type: ignore[import]
        import win32api    # type: ignore[import]
        import pywintypes  # type: ignore[import]
        _WIN32_BACKEND = "pywin32"
    except ImportError:
        win32file = None   # type: ignore[assignment]
        win32api = None    # type: ignore[assignment]
        pywintypes = None  # type: ignore[assignment]
        import ctypes
        import ctypes.wintypes as _wt
        _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _kernel32.CreateFileW.restype = _wt.HANDLE
        _kernel32.CreateFileW.argtypes = [
            _wt.LPCWSTR, _wt.DWORD, _wt.DWORD,
            ctypes.c_void_p, _wt.DWORD, _wt.DWORD, _wt.HANDLE,
        ]
        _kernel32.CloseHandle.restype = _wt.BOOL
        _kernel32.CloseHandle.argtypes = [_wt.HANDLE]
        _INVALID_HANDLE_VALUE: int = ctypes.c_void_p(-1).value  # type: ignore[assignment]
        _GENERIC_READ  = 0x80000000
        _GENERIC_WRITE = 0x40000000
        _OPEN_EXISTING = 3
        _FILE_FLAG_NORMAL = 0x80
        _WIN32_BACKEND = "ctypes"
else:
    _WIN32_BACKEND = "none"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default path to the config file  (Requirement 1.1)
DEFAULT_CONFIG_PATH: str = r"C:\NEVEN\neven-config.json"

#: Valid scripting language identifiers
VALID_LANGUAGES: frozenset[str] = frozenset({"r", "python", "julia"})

#: Mapping from language id → Control*.exe binary name
EXE_MAP: dict[str, str] = {
    "r":      "ControlR.exe",
    "python": "ControlPython.exe",
    "julia":  "ControlJulia.exe",
}

#: Default values for the Standalone config section  (Requirement 9.1)
_STANDALONE_DEFAULTS: dict[str, object] = {
    "controlDir":   r"C:\NEVEN\\",
    "startupDir":   r"C:\NEVEN\startup\\",
    "staticDir":    r"C:\NEVEN\taskpane\\",
    "functionsDir": r"C:\NEVEN\functions\\",
    "port":         5555,
}

#: Log prefix used for all launcher messages
_LOG_PREFIX = "[NEVEN Launcher]"


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _warn(msg: str) -> None:
    """Write a WARNING message to stderr."""
    print(f"{_LOG_PREFIX} WARNING: {msg}", file=sys.stderr)


def _info(msg: str) -> None:
    """Write an INFO message to stderr."""
    print(f"{_LOG_PREFIX} INFO: {msg}", file=sys.stderr)


def _error(msg: str) -> None:
    """Write an ERROR message to stderr."""
    print(f"{_LOG_PREFIX} ERROR: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI argument parsing  (Requirements 1.1, 9.2, 9.6)
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the launcher.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with ``--config``, ``--port``, ``--languages``,
        and ``--no-browser`` arguments.
    """
    parser = argparse.ArgumentParser(
        prog="start_studio.py",
        description="NEVEN Studio Standalone launcher",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=DEFAULT_CONFIG_PATH,
        help=(
            f"Path to neven-config.json "
            f"(default: {DEFAULT_CONFIG_PATH})"
        ),
    )
    parser.add_argument(
        "--port",
        metavar="INT",
        type=int,
        default=None,
        help="HTTP server port (overrides config, default: 5555)",
    )
    parser.add_argument(
        "--languages",
        metavar="LIST",
        default=None,
        help=(
            "Comma-separated list of language engines to start "
            "(e.g. r,python).  Overrides the config file. "
            "Valid values: r, python, julia."
        ),
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=False,
        help="Do not open the Studio URL in the default browser on startup.",
    )
    return parser


# ---------------------------------------------------------------------------
# Config loading  (Requirements 1.1, 9.1)
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    """Load ``neven-config.json`` and return a merged config dict.

    The returned dict always contains a ``"Standalone"`` key whose sub-keys
    include at minimum: ``controlDir``, ``startupDir``, ``staticDir``,
    ``functionsDir``, and ``port``.  Any key absent from the file falls back
    to the value in ``_STANDALONE_DEFAULTS``.

    Parameters
    ----------
    path:
        Filesystem path to ``neven-config.json``.

    Returns
    -------
    dict
        Full parsed config with defaults applied to the ``Standalone`` section.
        If the file is missing or unreadable the entire config is the defaults.

    Notes
    -----
    * Logs a WARNING to stderr when the file is not found (Requirement 1.1).
    * Does NOT raise on missing file — callers receive defaults.
    """
    raw: dict = {}

    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        _warn(f"Config file not found: {path!r} — using defaults")
    except (json.JSONDecodeError, OSError) as exc:
        _warn(f"Cannot read config file {path!r}: {exc} — using defaults")

    # Extract (or create) the Standalone section
    standalone_raw: dict = raw.get("Standalone", {})

    # Merge with defaults: file values win over defaults
    standalone: dict = {**_STANDALONE_DEFAULTS, **standalone_raw}

    # Normalise the port field: if present in the file as int, honour it;
    # otherwise the default (5555) already comes from _STANDALONE_DEFAULTS.
    if "port" in standalone_raw:
        try:
            standalone["port"] = int(standalone_raw["port"])
        except (TypeError, ValueError):
            _warn(
                f"Invalid port value {standalone_raw['port']!r} in config — "
                "using default 5555"
            )
            standalone["port"] = 5555

    # Persist the merged section back into the full config dict
    raw["Standalone"] = standalone
    return raw


# ---------------------------------------------------------------------------
# Language resolution  (Requirements 1.2, 9.6)
# ---------------------------------------------------------------------------

def resolve_languages(config: dict, arg: Optional[str]) -> set[str]:
    """Return the set of enabled language identifiers.

    Resolution order:

    1. If *arg* is not ``None`` (i.e. ``--languages`` was supplied on the CLI),
       parse the comma-separated list and use it — ignoring the config file.
    2. Otherwise, read the ``languages`` list from the ``Standalone`` section
       of *config*.
    3. If neither source is available, default to all three languages.

    Each resolved identifier is validated against ``VALID_LANGUAGES``
    (``{"r", "python", "julia"}``).  Invalid entries are silently dropped
    after logging a warning.

    Parameters
    ----------
    config:
        Full config dict as returned by :func:`load_config`.
    arg:
        Raw value of the ``--languages`` CLI argument (e.g. ``"r,python"``)
        or ``None`` if the argument was not supplied.

    Returns
    -------
    set[str]
        Non-empty subset of ``{"r", "python", "julia"}``.  If after
        validation no valid languages remain, returns all three as a fallback.
    """
    candidates: list[str]

    if arg is not None:
        # CLI override: comma-separated, strip whitespace, lower-case
        candidates = [tok.strip().lower() for tok in arg.split(",") if tok.strip()]
    else:
        # Config file: expect Standalone.languages as a list of strings
        standalone = config.get("Standalone", {})
        raw_langs = standalone.get("languages")
        if isinstance(raw_langs, list) and raw_langs:
            candidates = [str(x).strip().lower() for x in raw_langs if str(x).strip()]
        else:
            # No languages section — enable all three
            return set(VALID_LANGUAGES)

    # Validate
    valid: set[str] = set()
    for lang in candidates:
        if lang in VALID_LANGUAGES:
            valid.add(lang)
        else:
            _warn(
                f"Unknown language {lang!r} — valid values are "
                f"{sorted(VALID_LANGUAGES)}; skipping"
            )

    if not valid:
        _warn("No valid languages remained after validation — enabling all languages")
        return set(VALID_LANGUAGES)

    return valid


# ---------------------------------------------------------------------------
# Executable discovery  (Requirements 9.3)
# ---------------------------------------------------------------------------

def find_exe(config: dict, lang: str) -> Optional[str]:
    """Construct and validate the path to a Control*.exe binary.

    Looks up the binary name for *lang* in ``EXE_MAP``, prepends
    ``config["Standalone"]["controlDir"]``, and checks that the resulting
    path points to an existing file.

    Parameters
    ----------
    config:
        Full config dict as returned by :func:`load_config`.
    lang:
        Language identifier — one of ``"r"``, ``"python"``, ``"julia"``.

    Returns
    -------
    str or None
        Absolute path to the binary when it exists, or ``None`` when the
        binary is not found (a WARNING is logged in that case).

    Notes
    -----
    Log format: ``[NEVEN Launcher] WARNING: <exe> not found — skipping <lang>``
    """
    exe_name = EXE_MAP.get(lang)
    if exe_name is None:
        _warn(f"No executable mapping for language {lang!r} — skipping {lang}")
        return None

    control_dir: str = str(
        config.get("Standalone", {}).get("controlDir", _STANDALONE_DEFAULTS["controlDir"])
    )
    exe_path = os.path.join(control_dir, exe_name)

    if not os.path.isfile(exe_path):
        _warn(f"{exe_name} not found — skipping {lang}")
        return None

    return exe_path


# ---------------------------------------------------------------------------
# Pipe name helper
# ---------------------------------------------------------------------------

def _pipe_name_for(lang: str) -> str:
    r"""Return the Named Pipe path for *lang*.

    Pattern: ``\\.\pipe\neven_{lang}``
    """
    return r"\\.\pipe\neven_" + lang


def _pipe_arg_for(lang: str) -> str:
    r"""Return the short pipe name passed as ``-p`` argument to Control*.exe.

    The C++ ``Pipe::Start`` prepends ``\\.\pipe\`` automatically, so we pass
    only the short name (e.g. ``neven_python``) as the ``-p`` argument.
    The full Win32 path then becomes ``\\.\pipe\neven_python``.
    """
    return "neven_" + lang


# ---------------------------------------------------------------------------
# Pipe probe helper — used by both wait_for_pipes and the HTTP server
# ---------------------------------------------------------------------------

def _probe_pipe_once(pipe_name: str) -> bool:
    """Try to open *pipe_name* with CreateFile; return True on success.

    Closes the handle immediately — this is only a readiness check.
    On non-Windows always returns False.
    """
    if not _IS_WINDOWS:
        return False

    if _WIN32_BACKEND == "pywin32":
        try:
            h = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None,
            )
            win32api.CloseHandle(h)
            return True
        except pywintypes.error:
            return False
    else:  # ctypes fallback
        h = _kernel32.CreateFileW(
            pipe_name,
            _GENERIC_READ | _GENERIC_WRITE,
            0,
            None,
            _OPEN_EXISTING,
            _FILE_FLAG_NORMAL,
            None,
        )
        if h == _INVALID_HANDLE_VALUE:
            return False
        _kernel32.CloseHandle(h)
        return True


# ---------------------------------------------------------------------------
# Task 4.2 — Process launch  (Requirements 1.3, 1.4)
# ---------------------------------------------------------------------------

def _acquire_instance_lock() -> object:
    """Acquire a Windows named mutex that prevents multiple launcher instances.

    Returns the mutex handle or None on non-Windows.
    Raises SystemExit(1) if another launcher is actively running.
    If the previous launcher died, the abandoned mutex is reclaimed.
    """
    if not _IS_WINDOWS:
        return None

    import ctypes
    import ctypes.wintypes as wt

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _k32.CreateMutexW.restype         = wt.HANDLE
    _k32.CreateMutexW.argtypes        = [ctypes.c_void_p, wt.BOOL, wt.LPCWSTR]
    _k32.WaitForSingleObject.restype  = wt.DWORD
    _k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]

    MUTEX_NAME     = "Global\\NEVEN_Studio_Launcher"
    WAIT_OBJECT_0  = 0x00000000
    WAIT_ABANDONED = 0x00000080
    WAIT_TIMEOUT   = 0x00000102

    handle = _k32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        _warn("Could not create instance mutex — continuing without single-instance guard")
        return None

    result = _k32.WaitForSingleObject(handle, 0)

    if result == WAIT_OBJECT_0:
        return handle
    if result == WAIT_ABANDONED:
        _warn("Previous launcher exited uncleanly — taking over")
        return handle
    if result == WAIT_TIMEOUT:
        _error(
            "NEVEN Studio is already running. "
            "Stop the existing instance (Ctrl+C in its terminal) before starting a new one."
        )
        sys.exit(1)

    _warn(f"Unexpected mutex result {result:#x} — continuing without single-instance guard")
    return handle

def _r_home(config: dict, install_dir: str) -> str:
    """Return the R installation directory as a short (8.3) path.

    Resolution order:
    1. ``neven-config.json`` → ``NEVEN.R.home`` (if non-empty)
    2. Windows registry: ``HKLM\\SOFTWARE\\R-core\\R\\InstallPath``
    3. Default: ``C:\\Program Files\\R\\R-4.4.1``
    """
    r_home_cfg: str = str(config.get("NEVEN", {}).get("R", {}).get("home", "")).strip()
    if r_home_cfg:
        return _short_path(r_home_cfg)

    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for sub in (r"SOFTWARE\R-core\R", r"SOFTWARE\WOW6432Node\R-core\R"):
                try:
                    with winreg.OpenKey(hive, sub) as k:
                        val, _ = winreg.QueryValueEx(k, "InstallPath")
                        if val:
                            return _short_path(str(val))
                except OSError:
                    pass
    except ImportError:
        pass

    return _short_path(r"C:\Program Files\R\R-4.4.1")


def _julia_home(config: dict, install_dir: str) -> str:
    """Return the Julia installation directory.

    Resolution order:
    1. ``neven-config.json`` → ``NEVEN.Julia.home`` (if non-empty)
    2. Known installation paths (LocalAppData\\Programs\\Julia*)
    3. ``julia`` on PATH (skipping WindowsApps stubs)
    4. Default ``C:\\Julia``
    """
    julia_home_cfg: str = str(config.get("NEVEN", {}).get("Julia", {}).get("home", "")).strip()
    if julia_home_cfg:
        return _short_path(julia_home_cfg)

    # Search common install location first (avoids WindowsApps stub)
    import glob
    local_programs = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")
    candidates = sorted(
        glob.glob(os.path.join(local_programs, "Julia*")),
        reverse=True,  # newest first
    )
    for candidate in candidates:
        julia_exe = os.path.join(candidate, "bin", "julia.exe")
        if os.path.isfile(julia_exe):
            return _short_path(candidate)

    # Also check Program Files
    for pf in (r"C:\Program Files", r"C:\Program Files (x86)"):
        for candidate in sorted(glob.glob(os.path.join(pf, "Julia*")), reverse=True):
            julia_exe = os.path.join(candidate, "bin", "julia.exe")
            if os.path.isfile(julia_exe):
                return _short_path(candidate)

    # PATH fallback — skip WindowsApps stubs
    import shutil
    julia_exe_path = shutil.which("julia")
    if julia_exe_path and "WindowsApps" not in julia_exe_path:
        return _short_path(os.path.dirname(os.path.dirname(julia_exe_path)))

    return _short_path(r"C:\Julia")


def _short_path(long_path: str) -> str:
    """Convert a long Windows path to its 8.3 short form.

    This avoids spaces in paths passed as CLI arguments to Control*.exe
    which uses argv[] splitting that doesn't handle quoted paths.
    """
    if " " not in long_path:
        return long_path  # no spaces — no need to convert
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        ret = ctypes.windll.kernel32.GetShortPathNameW(long_path, buf, 260)
        if ret > 0:
            return buf.value
    except Exception:
        pass
    return long_path  # fallback — return as-is


def _extra_args_for(lang: str, config: dict, install_dir: str) -> list:
    """Return extra CLI arguments for the Control*.exe beyond ``-p pipe``."""
    if lang == "r":
        home = _r_home(config, install_dir)
        _info(f"R home: {home}")
        return ["-r", home]
    elif lang == "julia":
        # ControlJulia uses JULIA_BINDIR env var, set by prepend_path in XLL.
        # In standalone mode Julia is found via PATH or julia_home config.
        home = _julia_home(config, install_dir)
        # ControlJulia doesn't take -j; it reads JULIA_BINDIR from env.
        # We set it via env in launch_control, not as a CLI arg.
        return []
    else:
        return []


def launch_control(
    exe: str,
    lang: str,
    config: dict,
) -> subprocess.Popen:
    """Launch a Control*.exe process for *lang*.

    Calls::

        subprocess.Popen([exe, '-p', pipe_name],
                         env={**os.environ, 'RJ2XCL_HOME': install_dir})

    Parameters
    ----------
    exe:
        Absolute path to the Control*.exe binary.
    lang:
        Language identifier (``"r"``, ``"python"``, or ``"julia"``).
    config:
        Full config dict as returned by :func:`load_config`.

    Returns
    -------
    subprocess.Popen
        The launched process object.

    Notes
    -----
    * The pipe name follows the pattern ``\\\\.\\pipe\\neven_{lang}``
      (Requirement 1.3).
    * ``RJ2XCL_HOME`` is set from ``config["Standalone"]["controlDir"]``
      (Requirement 1.4).
    """
    pipe_name = _pipe_arg_for(lang)   # short name — Pipe::Start adds \\.\pipe\ prefix
    install_dir: str = str(
        config.get("Standalone", {}).get(
            "controlDir", _STANDALONE_DEFAULTS["controlDir"]
        )
    )
    env = {**os.environ, "RJ2XCL_HOME": install_dir}

    # Build extra arguments from neven-languages.json
    # R requires: -r "<R_HOME>"   (from neven-config.json NEVEN.R.home or registry)
    # Julia/Python: no extra args needed
    extra_args: list[str] = _extra_args_for(lang, config, install_dir)

    # Prepend language runtime to PATH so DLLs are found (mirrors XLL's PrependPath)
    if lang == "r":
        r_home = _r_home(config, install_dir)
        r_bin = os.path.join(r_home, "bin", "x64")
        env["PATH"] = r_bin + os.pathsep + env.get("PATH", "")
        _info(f"R PATH prepend: {r_bin}")

    # Julia needs JULIA_BINDIR so it can find libjulia.dll
    if lang == "julia":
        julia_home = _julia_home(config, install_dir)
        julia_bindir = os.path.join(julia_home, "bin")
        env["JULIA_BINDIR"] = julia_bindir
        # Also prepend Julia bin to PATH so DLL loading works
        env["PATH"] = julia_bindir + os.pathsep + env.get("PATH", "")
        _info(f"Julia home: {julia_home}")

    cmd = [exe, "-p", pipe_name] + extra_args
    _info(f"Launching: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, env=env)
    _info(f"Launched {os.path.basename(exe)} (PID {proc.pid})")
    return proc


# ---------------------------------------------------------------------------
# Task 4.2 — Pipe readiness polling  (Requirement 1.5)
# ---------------------------------------------------------------------------

def wait_for_pipes(
    processes: Dict[str, subprocess.Popen],
    timeout: float = 10.0,
) -> None:
    """Poll each language's Named Pipe until it is ready or the timeout expires.

    On Windows, polls ``\\\\.\\pipe\\neven_{lang}`` via ``CreateFile`` every
    100 ms up to *timeout* seconds.  Languages whose pipes do not become
    ready within the timeout are logged as warnings and removed from
    *processes* (the caller's dict is mutated in-place).

    On non-Windows the function returns immediately after logging an INFO
    message — no pipe polling is performed and no processes are started
    (Requirement 4.7).

    Parameters
    ----------
    processes:
        ``{lang: Popen}`` mapping built by the startup sequence.  Modified
        in-place: timed-out languages are removed.
    timeout:
        Maximum seconds to wait per language (default: 10 s).
    """
    if not _IS_WINDOWS:
        _info("Non-Windows platform — scripting engines not started")
        return

    _POLL_INTERVAL = 0.1  # 100 ms

    langs_to_check = list(processes.keys())
    deadline = time.monotonic() + timeout

    # Track which langs are still waiting
    pending: set[str] = set(langs_to_check)

    while pending and time.monotonic() < deadline:
        newly_ready: set[str] = set()
        for lang in list(pending):
            pipe_name = _pipe_name_for(lang)
            if _probe_pipe_once(pipe_name):
                _info(f"{lang} pipe ready: {pipe_name}")
                newly_ready.add(lang)
        pending -= newly_ready
        if pending:
            time.sleep(_POLL_INTERVAL)

    # Any langs still pending have timed out
    for lang in pending:
        _warn(f"{lang} pipe timeout — skipping")
        processes.pop(lang, None)


# ---------------------------------------------------------------------------
# Task 4.2 — PID file  (Requirements 8.5, 8.6)
# ---------------------------------------------------------------------------

def _pid_file_path(config: dict) -> str:
    """Return the path to the PID file: ``<NEVEN_HOME>/studio.pid``."""
    control_dir: str = str(
        config.get("Standalone", {}).get(
            "controlDir", _STANDALONE_DEFAULTS["controlDir"]
        )
    )
    return os.path.join(control_dir, "studio.pid")


def remove_pid_file(config: dict) -> None:
    """Remove the PID file if it exists.  Registered with :mod:`atexit`.

    Parameters
    ----------
    config:
        Full config dict as returned by :func:`load_config`.
    """
    path = _pid_file_path(config)
    try:
        os.remove(path)
        _info(f"Removed PID file: {path}")
    except FileNotFoundError:
        pass  # Already gone — not an error
    except OSError as exc:
        _warn(f"Could not remove PID file {path!r}: {exc}")


def write_pid_file(
    config: dict,
    processes: Dict[str, subprocess.Popen],
    launcher_pid: int,
) -> None:
    """Write a JSON PID file and register cleanup via :mod:`atexit`.

    The file contains the launcher PID plus one entry per started language::

        { "launcher": 12345, "r": 12346, "python": 12347 }

    Languages not in *processes* are omitted.  The file is written
    atomically (overwrite) to ``<NEVEN_HOME>/studio.pid``.

    Parameters
    ----------
    config:
        Full config dict as returned by :func:`load_config`.
    processes:
        ``{lang: Popen}`` mapping of started Control processes.
    launcher_pid:
        PID of the launcher process itself (typically ``os.getpid()``).

    Notes
    -----
    * Registers :func:`remove_pid_file` with :func:`atexit.register` so the
      file is removed on clean exit (Requirement 8.6).
    * If present at startup the file is silently overwritten; no locking is
      required because only one launcher runs per installation.
    """
    pid_data: dict = {"launcher": launcher_pid}
    for lang, proc in processes.items():
        pid_data[lang] = proc.pid

    path = _pid_file_path(config)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(pid_data, fh, indent=None)
        _info(f"PID file written: {path}")
    except OSError as exc:
        _warn(f"Could not write PID file {path!r}: {exc}")

    # Register cleanup — atexit calls this when the launcher exits cleanly
    atexit.register(remove_pid_file, config)


# ---------------------------------------------------------------------------
# Task 4.3 — HTTP server wiring  (Requirement 1.6, 9.5)
# ---------------------------------------------------------------------------

def start_server(
    config: dict,
    pipe_clients: Dict[str, object],
) -> Tuple[threading.Thread, int]:
    """Start the HTTP server with injected PipeClient factories.

    Builds a ``pipe_client_factory`` dict from *pipe_clients* — a mapping of
    ``{lang: PipeClient}`` — by wrapping each client in a zero-argument lambda
    so the server can call the factory to get a client instance.  This satisfies
    the ``pipe_client_factory: dict[str, Callable[[], PipeClient]]`` contract
    expected by ``neven_http_server.start_server`` (Requirement 9.5).

    Parameters
    ----------
    config:
        Full config dict as returned by :func:`load_config`.  The ``Standalone``
        section supplies port, staticDir, etc.
    pipe_clients:
        ``{lang: PipeClient}`` mapping of already-connected clients.  May be
        empty on non-Windows (no Control processes started).

    Returns
    -------
    (thread, port)
        The daemon ``threading.Thread`` running the server and the bound port.

    Raises
    ------
    SystemExit
        If the server cannot bind to any port (mirrors the HTTP server's own
        fatal behaviour — Requirement 1.6).
    """
    # Import here to avoid a hard dependency at module load time.
    # Search for neven_http_server.py in candidate directories, in order:
    #   1. Production:  C:\NEVEN\startup\               (installed)
    #   2. Repo source: <this_file>/../ControlPython/startup/  (dev)
    #   3. Same dir as this file                        (fallback)
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    _http_candidates = [
        os.path.join(_this_dir, "..", "startup"),                   # C:\NEVEN\startup
        os.path.join(_this_dir, "..", "ControlPython", "startup"),  # repo dev
        _this_dir,                                                   # same dir
    ]
    for _candidate in _http_candidates:
        _candidate = os.path.normpath(_candidate)
        if os.path.isfile(os.path.join(_candidate, "neven_http_server.py")):
            if _candidate not in sys.path:
                sys.path.insert(0, _candidate)
            break
    else:
        _error("Cannot find neven_http_server.py — checked: " +
               ", ".join(os.path.normpath(p) for p in _http_candidates))
        sys.exit(1)

    import neven_http_server  # type: ignore[import]

    # pipe_clients is the shared factory dict — passed by reference so the
    # background engine-connector thread can add entries live after server start.
    # If callers pass a {lang: PipeClient} dict (old style), wrap each client
    # in a zero-arg lambda; if they pass a {lang: callable} dict (new style),
    # use it directly.
    factory: dict[str, object] = {}
    for lang, val in pipe_clients.items():
        if callable(val) and not hasattr(val, 'connect'):
            # already a factory callable
            factory[lang] = val
        else:
            # PipeClient instance — wrap it
            factory[lang] = (lambda c: lambda: c)(val)

    # IMPORTANT: we replace the contents of pipe_clients with factory entries
    # so that the background thread updating pipe_clients also updates factory.
    # Instead, point server_config at the *same object* as pipe_clients.
    pipe_clients.clear()
    pipe_clients.update(factory)

    standalone = config.get("Standalone", {})
    server_config = {
        "enabled": True,
        "port": standalone.get("port", 5555),
        "fallbackPort": standalone.get("fallbackPort", 5556),
        "certPath": standalone.get("certPath", ""),
        "keyPath":  standalone.get("keyPath", ""),
        "staticDir":   standalone.get("staticDir",   r"C:\NEVEN\taskpane"),
        "viewersDir":  standalone.get("viewersDir",  r"C:\NEVEN\workspace"),
        "queryTimeoutSec": standalone.get("queryTimeoutSec", 30),
        "maxPayloadMB":    standalone.get("maxPayloadMB", 50),
        "pipe_client_factory": pipe_clients,  # same object — live updates visible
    }

    result = neven_http_server.start_server(server_config)
    if result is None:
        _error("HTTP server failed to start — cannot bind on any port")
        sys.exit(1)

    thread, port = result
    return thread, port


# ---------------------------------------------------------------------------
# Task 4.3 — Process monitoring  (Requirement 1.10)
# ---------------------------------------------------------------------------

def monitor_processes(processes: Dict[str, subprocess.Popen]) -> None:
    """Start a background thread that logs unexpected Control process exits.

    Each Control process is polled once per second.  When ``proc.poll()``
    returns a non-``None`` value (i.e. the process has exited) the exit code
    is logged to stderr in the format::

        [NEVEN Launcher] ERROR: <name> exited with code <N>

    where ``<name>`` is the base name of the executable (e.g. ``ControlR.exe``).

    The monitor thread is a daemon thread so it does not prevent clean exit.

    Parameters
    ----------
    processes:
        ``{lang: Popen}`` mapping.  A snapshot is taken at call time; later
        mutations to the dict are **not** observed by the monitor.
    """
    if not processes:
        return

    # Take a snapshot so the monitor is not affected by later dict mutations.
    snapshot: dict[str, subprocess.Popen] = dict(processes)

    def _monitor():
        still_running: dict[str, subprocess.Popen] = dict(snapshot)
        while still_running:
            time.sleep(1)
            exited: list[str] = []
            for lang, proc in still_running.items():
                rc = proc.poll()
                if rc is not None:
                    # Determine a readable process name
                    try:
                        name = os.path.basename(proc.args[0])  # type: ignore[index]
                    except (AttributeError, IndexError, TypeError):
                        name = f"Control-{lang}"
                    _error(f"{name} exited with code {rc}")
                    exited.append(lang)
            for lang in exited:
                del still_running[lang]

    t = threading.Thread(target=_monitor, daemon=True, name="neven-monitor")
    t.start()


# ---------------------------------------------------------------------------
# Task 4.3 — Signal handling  (Requirement 1.9)
# ---------------------------------------------------------------------------

def wait_for_signal() -> None:
    """Block until SIGINT or SIGTERM is received.

    Uses a ``threading.Event`` so the function works correctly on Windows,
    where SIGTERM may not interrupt a blocking ``signal.pause()`` call.

    When the event is set (by either signal handler) the function returns,
    allowing the caller to proceed with :func:`shutdown`.
    """
    stop_event = threading.Event()

    def _handler(signum, frame):  # noqa: ANN001
        stop_event.set()

    signal.signal(signal.SIGINT, _handler)
    # SIGTERM is supported on Windows only as of Python 3.8+ via the CRT;
    # wrap in try/except to stay portable regardless.
    try:
        signal.signal(signal.SIGTERM, _handler)
    except (OSError, ValueError):
        # On some platforms SIGTERM cannot be caught; SIGINT still works.
        pass

    _info("Studio is running. Press Ctrl+C to stop.")
    stop_event.wait()


# ---------------------------------------------------------------------------
# Task 4.3 — Shutdown  (Requirement 1.9)
# ---------------------------------------------------------------------------

def shutdown(processes: Dict[str, subprocess.Popen]) -> None:
    """Terminate all Control subprocesses gracefully.

    For each process:

    1. Calls ``proc.terminate()`` (SIGTERM on POSIX, ``TerminateProcess`` on
       Windows with a gentle signal).
    2. Waits up to 5 seconds for the process to exit via ``proc.wait(timeout=5)``.
    3. If the process is still alive after the timeout, calls ``proc.kill()``
       (SIGKILL / ``TerminateProcess`` forcefully).

    Parameters
    ----------
    processes:
        ``{lang: Popen}`` mapping of running Control processes.
    """
    for lang, proc in processes.items():
        try:
            name = os.path.basename(proc.args[0])  # type: ignore[index]
        except (AttributeError, IndexError, TypeError):
            name = f"Control-{lang}"

        try:
            proc.terminate()
            _info(f"Sent terminate to {name} (PID {proc.pid})")
        except OSError as exc:
            _warn(f"Could not terminate {name}: {exc}")
            continue

        try:
            proc.wait(timeout=5)
            _info(f"{name} exited cleanly")
        except subprocess.TimeoutExpired:
            _warn(f"{name} did not exit after 5 s — killing")
            try:
                proc.kill()
                proc.wait()
                _info(f"{name} killed")
            except OSError as exc:
                _warn(f"Could not kill {name}: {exc}")


# ---------------------------------------------------------------------------
# Main entry point — fully wired (tasks 4.1 + 4.2 + 4.3)
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> None:
    """Full NEVEN Studio Standalone startup sequence.

    Parses arguments, loads config, resolves languages, launches Control
    processes, starts the HTTP server, opens the browser, monitors processes,
    waits for a signal, then shuts everything down.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # --- Config loading (Req 1.1, 9.1) ---
    config = load_config(args.config)

    # --- Port override (Req 9.2) ---
    if args.port is not None:
        config["Standalone"]["port"] = args.port

    # --- Language resolution (Req 1.2, 9.6) ---
    enabled_langs = resolve_languages(config, args.languages)

    # --- Single-instance guard (prevents ghost factory servers) ---
    _instance_lock = _acquire_instance_lock()  # noqa: F841 — kept alive intentionally

    # --- Executable discovery (Req 9.3) ---
    executables: dict[str, str] = {}
    for lang in sorted(enabled_langs):
        exe = find_exe(config, lang)
        if exe is not None:
            executables[lang] = exe

    # --- Process launch (Req 1.3, 1.4) ---
    processes: Dict[str, subprocess.Popen] = {}
    if _IS_WINDOWS:
        for lang, exe in executables.items():
            try:
                proc = launch_control(exe, lang, config)
                processes[lang] = proc
            except OSError as exc:
                _warn(f"Failed to launch {lang} engine: {exc} — skipping")
    else:
        # Non-Windows: log and skip all Control processes (Req 4.7)
        _info("Non-Windows platform — scripting engines not started")

    # --- HTTP server starts immediately (Req 1.6) ---
    # PipeClients connect in a background thread.  The shared pipe_factory dict
    # is updated live as each engine becomes ready — no blocking the server.
    pipe_factory: Dict[str, object] = {}

    # --- PID file (Req 8.5, 8.6) ---
    write_pid_file(config, processes, os.getpid())

    # --- HTTP server start with shared factory (Req 1.6) ---
    _thread, port = start_server(config, pipe_factory)


    # --- Background: connect PipeClients and hot-register into factory ---
    def _connect_engines():
        if not _IS_WINDOWS or not processes:
            return
        _pc_dir = os.path.dirname(os.path.abspath(__file__))
        if _pc_dir not in sys.path:
            sys.path.insert(0, _pc_dir)
        try:
            import pipe_client as _pc_mod  # type: ignore[import]
        except ImportError:
            _warn("pipe_client.py not found -- script endpoints will return 503")
            return
        CONNECT_TIMEOUT = 300.0  # 5 min — Julia cold start without sysimage
        POLL_INTERVAL   = 0.5
        for lang in sorted(processes.keys()):
            pipe_name = _pipe_name_for(lang)
            _info(f"Waiting for {lang} pipe: {pipe_name}")
            deadline = time.monotonic() + CONNECT_TIMEOUT
            while time.monotonic() < deadline:
                try:
                    client = _pc_mod.PipeClient(pipe_name, timeout_ms=120_000)
                    client.connect()
                    pipe_factory[lang] = (lambda c: lambda: c)(client)
                    _info(f"Engine ready: {lang} — /api/{lang} now active")
                    break
                except OSError:
                    time.sleep(POLL_INTERVAL)
            else:
                _warn(f"{lang}: pipe never appeared after {CONNECT_TIMEOUT}s")

    threading.Thread(
        target=_connect_engines, daemon=True, name="neven-engine-connector"
    ).start()

    # --- Print Studio URL (Req 1.7) ---
    url = f"http://localhost:{port}/taskpane.html"
    print(url, flush=True)

    # --- Open browser (Req 1.8) ---
    if not args.no_browser:
        webbrowser.open(url)

    # --- Monitor Control processes (Req 1.10) ---
    monitor_processes(processes)

    # --- Block until Ctrl+C / SIGTERM (Req 1.9) ---
    wait_for_signal()

    # --- Graceful shutdown (Req 1.9) ---
    _info("Shutting down…")
    shutdown(processes)
    _info("Done.")


if __name__ == "__main__":
    main()
