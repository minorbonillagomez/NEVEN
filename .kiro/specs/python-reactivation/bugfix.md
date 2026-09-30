# Bugfix Requirements Document

## Introduction

Python was fully integrated as a third language service in NEVEN (alongside R and Julia) with 165 passing tests, 30+ sandbox patterns, and complete type conversion support. It was frozen on April 18, 2026 because it caused intermittent hangs and crashes in Excel. The code is 100% intact but disabled (`NEVEN_ENABLE_PYTHON=OFF`, Python entry removed from `neven-languages.json`, no Python section in `neven-config.json`). This bugfix addresses the four root causes that made Python unstable and re-enables it as an optional, resilient language service.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN Python is enabled and `startup.py` is executed via `PyRun_SimpleString()` in `PythonInit()` THEN the system intermittently fails with `rc=-1`, leaving the interpreter without `list_functions()` and `read_script_file()`, and no retry or recovery is attempted

1.2 WHEN `startup.py` fails (rc=-1) and `UpdateFunctions()` subsequently calls `list-functions` on the "connected" Python service THEN the system blocks indefinitely because `list_functions()` is not defined in `__main__` and the call never returns a usable response

1.3 WHEN `ControlPython.exe` starts THEN the system intermittently crashes with `STATUS_STACK_BUFFER_OVERRUN` (0xC0000409) during CPython initialization or pipe setup, killing the process before it can connect to the XLL

1.4 WHEN `startup.py` fails via `PyRun_SimpleString()` and the XLL sends the startup code line-by-line via pipe as a fallback THEN the system produces `IndentationError` on multi-line Python functions with docstrings, leaving the interpreter in an unusable state

1.5 WHEN `ControlPython.exe` crashes or becomes unresponsive THEN the system has no timeout, health check, or graceful degradation — `UpdateFunctions()` blocks the Excel UI thread waiting for a response from a dead or broken Python process

1.6 WHEN Python is enabled as a language service THEN the system is unstable — Excel hangs on startup, crashes intermittently, or blocks indefinitely during function registration, so Python was disabled entirely (`NEVEN_ENABLE_PYTHON=OFF`)

### Expected Behavior (Correct)

2.1 WHEN `startup.py` execution via `PyRun_SimpleString()` fails (rc=-1) THEN the system SHALL retry execution up to a configurable number of times (e.g., 3 retries) with a brief delay, and log each attempt, before declaring startup failed

2.2 WHEN `startup.py` fails after all retries THEN the system SHALL mark the Python language service as unavailable (health status = Unavailable) and `UpdateFunctions()` SHALL skip Python without blocking, allowing R and Julia to continue normally

2.3 WHEN `ControlPython.exe` starts THEN the system SHALL guard against stack buffer overrun by ensuring CPython initialization occurs after pipe argument parsing and with proper error handling, and SHALL use structured exception handling (SEH) around `Py_Initialize()` to catch fatal crashes gracefully

2.4 WHEN the XLL needs to send startup code to Python as a fallback THEN the system SHALL send the entire `startup.py` content as a single code block (not line-by-line) to preserve multi-line function definitions and docstrings

2.5 WHEN `ControlPython.exe` crashes or becomes unresponsive THEN the system SHALL detect the failure via the existing per-language call timeout (`callTimeoutMs` or per-language override), mark Python as Unavailable, and continue operating with R and Julia without blocking the Excel UI thread

2.6 WHEN Python is re-enabled (`NEVEN_ENABLE_PYTHON=ON`, Python entry in `neven-languages.json`, Python section in `neven-config.json` with `"enabled": true`) THEN the system SHALL build `ControlPython.exe`, discover the Python installation, launch the process, and register Python functions in Excel — all without hanging or crashing Excel

### Unchanged Behavior (Regression Prevention)

3.1 WHEN Python is disabled (no Python section in `neven-config.json` or `"enabled": false`) THEN the system SHALL CONTINUE TO start cleanly with only R and optionally Julia, with no performance impact from Python-related code paths

3.2 WHEN R or Julia language services are configured and connected THEN the system SHALL CONTINUE TO launch, connect, send startup scripts, and register functions exactly as before, with no changes to their initialization or communication paths

3.3 WHEN `UpdateFunctions()` is called and only R and Julia are connected THEN the system SHALL CONTINUE TO call `list-functions` on each connected language and register all discovered functions in Excel without any new delays or timeouts affecting R/Julia

3.4 WHEN user-defined function files are loaded from `Documents/NEVEN/functions/` THEN the system SHALL CONTINUE TO dispatch `.r` files to R, `.jl` files to Julia, and `.py` files to Python (if connected), with hot-reload via FileWatchService working for all languages

3.5 WHEN `=NEVEN.r("1+1")` or `=NEVEN.j("1+1")` is called THEN the system SHALL CONTINUE TO return the correct result (2) with the same latency and reliability as before

3.6 WHEN the existing 165 Python tests are run (sandbox tests, PBT tests, unit tests) THEN the system SHALL CONTINUE TO pass all tests without modification to test logic

---

## Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type LanguageServiceConfig
  OUTPUT: boolean
  
  // Returns true when Python is enabled as a language service
  RETURN X.language = "Python" AND X.enabled = true
END FUNCTION
```

## Fix Checking Property

```pascal
// Property: Fix Checking — Python Resilient Initialization
FOR ALL X WHERE isBugCondition(X) DO
  result ← InitializeLanguageService'(X)
  ASSERT (result.status = Connected AND result.startup_ok = true)
      OR (result.status = Unavailable AND result.excel_stable = true AND result.r_julia_unaffected = true)
END FOR
```

This property states: for every configuration where Python is enabled, the fixed system either successfully connects Python, or gracefully marks it as unavailable — but in both cases Excel remains stable and R/Julia are unaffected.

## Preservation Checking Property

```pascal
// Property: Preservation Checking — R and Julia Unaffected
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

This property states: for all non-Python language configurations (R, Julia, or Python disabled), the fixed code behaves identically to the original code. No changes to R/Julia initialization, communication, function registration, or runtime behavior.
