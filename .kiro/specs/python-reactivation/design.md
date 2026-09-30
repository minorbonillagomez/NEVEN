# Python Reactivation Bugfix Design

## Overview

Python was fully integrated as a third language service in NEVEN but was disabled (`NEVEN_ENABLE_PYTHON=OFF`) because it caused intermittent Excel hangs and crashes. The code is 100% intact — four specific bugs made it unstable. This design addresses each bug with minimal, targeted fixes that preserve the existing architecture and leave R/Julia behavior completely unchanged.

The four bugs are: (1) `PythonInit()` has no retry on `PyRun_SimpleString()` failure, (2) `ControlPython.exe` crashes with `STATUS_STACK_BUFFER_OVERRUN` due to initialization order, (3) `language_service.cc::Initialize()` sends startup code line-by-line which breaks Python's indentation-sensitive syntax, and (4) `UpdateFunctions()` blocks indefinitely when Python is connected but broken.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bugs — Python is enabled as a language service (`"enabled": true` in config, entry present in `neven-languages.json`, `NEVEN_ENABLE_PYTHON=ON` in CMake)
- **Property (P)**: The desired behavior — Python either initializes successfully and registers functions, or fails gracefully and is marked Unavailable without affecting Excel or other languages
- **Preservation**: R and Julia initialization, communication, function registration, and runtime behavior must remain identical to the current (Python-disabled) state
- **`PythonInit()`**: Function in `python_interface.cc` that initializes the CPython interpreter and executes `startup.py`
- **`ControlPython.exe`**: Child process in `ControlPython/src/control_python.cc` that embeds CPython and communicates with the XLL via Named Pipes + Protobuf
- **`LanguageService::Initialize()`**: Method in `Core/src/language_service.cc` that sends startup code to a connected language process
- **`MapLanguageFunctions()`**: Method in `language_service.cc` that calls `list-functions` on a language service to discover Excel-callable functions
- **`HealthStatus`**: Enum (`Healthy`, `Unavailable`, `Unknown`) in `language_service.h` tracking per-language process health
- **`CallTimeoutMs`**: Per-language or global timeout for pipe calls, configured in `neven-config.json`

## Bug Details

### Bug Condition

The bugs manifest when Python is enabled as a language service. Four distinct failure modes occur during the startup sequence: `PythonInit()` fails intermittently without retry, `ControlPython.exe` crashes from stack buffer overrun before connecting, startup code sent line-by-line produces `IndentationError`, and `UpdateFunctions()` blocks indefinitely on a broken Python service.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type LanguageServiceConfig
  OUTPUT: boolean

  RETURN input.language = "Python"
         AND input.enabled = true
         AND input.build_flag = "NEVEN_ENABLE_PYTHON=ON"
         AND input.config_section_exists = true
         AND input.languages_json_entry_exists = true
END FUNCTION
```

### Examples

- **Bug 1 — Intermittent startup.py failure**: `PythonInit()` calls `PyRun_SimpleString(startup_code)` which returns `rc=-1`. No retry is attempted. `list_functions()` and `read_script_file()` are never defined in `__main__`. Subsequent `list-functions` call from XLL gets `NameError` or hangs. Expected: retry up to 3 times, then mark Unavailable.
- **Bug 2 — Stack buffer overrun crash**: `ControlPython.exe` calls `Py_Initialize()` in `main()` before parsing pipe arguments. If CPython initialization triggers a stack-heavy operation (e.g., importing `site.py`) while the stack is already partially consumed by local variables, `STATUS_STACK_BUFFER_OVERRUN` (0xC0000409) kills the process. Expected: parse arguments first, guard `Py_Initialize()` with SEH.
- **Bug 3 — IndentationError from line-by-line sending**: `LanguageService::Initialize()` splits `startup.py` by `\n`, skips empty lines (`if (line.length() > 0)`), and adds each as a separate `code->add_line()`. On the ControlPython side, `PythonExec()` reassembles with `\n` — but the empty lines that separate Python function definitions are lost, causing `IndentationError`. Expected: send entire file as a single code block for Python.
- **Bug 4 — Indefinite blocking**: When `startup.py` fails (Bug 1) and Python is "connected" (pipe is open), `MapLanguageFunctions()` calls `list-functions` via `Call()`. The call reaches ControlPython, which tries `list_functions()` in `__main__` — but it doesn't exist. `ListScriptFunctions()` returns an empty list, but if the pipe is in a bad state or the process crashed (Bug 2), `Call()` blocks on `WaitForSingleObject()` until the global timeout (10 minutes). Expected: check health status before calling, use per-language timeout.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- R language service initialization, pipe communication, startup script execution, and function registration must work exactly as before
- Julia language service initialization, JIT compilation, pipe communication, and function registration must work exactly as before
- Mouse/keyboard interaction with Excel, COM automation callbacks, and the Ribbon UI must remain unchanged
- `=NEVEN.r("1+1")` and `=NEVEN.j("1+1")` must return correct results with the same latency
- Hot-reload via `FileWatchService` must continue to work for `.r`, `.jl`, and `.py` files
- The 165 existing Python tests (sandbox, PBT, unit) must continue to pass without modification
- When Python is disabled (`"enabled": false` or no config section), the system must start cleanly with only R and optionally Julia

**Scope:**
All inputs that do NOT involve Python being enabled as a language service should be completely unaffected by this fix. This includes:
- R-only and Julia-only configurations
- Configurations where Python section exists but `"enabled": false`
- All Excel formula calls to R and Julia functions
- Console/REPL interactions with R and Julia
- WebView2 viewer operations
- Pluto notebook operations

## Hypothesized Root Cause

Based on code analysis of the actual source files, the root causes are:

1. **No Retry in `PythonInit()`** (`python_interface.cc:107-126`): `PyRun_SimpleString()` is called exactly once. If it returns `rc=-1` (which can happen due to CPython GIL timing, import path issues, or transient file locks), the error is logged but execution continues. `PythonInit()` returns normally, `pipe_loop()` starts, and the XLL believes Python is ready — but `list_functions()` and `read_script_file()` were never defined.

2. **Initialization Order in `main()`** (`control_python.cc:310-330`): `Py_Initialize()` is called at line ~320, after only basic argument parsing. The function allocates significant stack space for CPython's internal initialization (importing `site.py`, `builtins`, etc.). Combined with the existing local variables (`buffer[MAX_PATH]`, `std::stringstream`, pipe objects), this can exceed the default 1MB stack on some systems, triggering `STATUS_STACK_BUFFER_OVERRUN`. Additionally, there is no SEH guard around `Py_Initialize()`.

3. **Line-by-Line Startup Code Sending** (`language_service.cc:152-167`): The `Initialize()` method uses `StringUtilities::Split(startup_code, '\n', 1, lines, true)` to split the startup script into lines, then iterates with `if (line.length() > 0) code->add_line(line)`. This skips empty lines. For R, this is harmless because R's parser doesn't rely on blank lines. For Python, blank lines between function definitions and after docstrings are syntactically significant — removing them causes `IndentationError` when `PythonExec()` reassembles the code with `\n`.

4. **No Health Check Before `MapLanguageFunctions()`** (`language_service.cc:695-707`): `MapLanguageFunctions()` checks `if (!connected_) return {}` but does not check `health_status_`. If the process crashed (Bug 2) after the pipe was connected, `connected_` is still `true` but the pipe is broken. The `Call()` method will block on `WaitForSingleObject()` until the global timeout (default 600,000ms = 10 minutes). `MapFunctions()` in `rj2xcl.cc:592` iterates all services without checking health status either.

## Correctness Properties

Property 1: Bug Condition - Python Resilient Initialization

_For any_ configuration where Python is enabled (isBugCondition returns true), the fixed system SHALL either (a) successfully initialize Python, execute `startup.py`, connect via pipe, and register Python functions in Excel, or (b) mark Python as `HealthStatus::Unavailable` and allow `UpdateFunctions()` to complete without blocking — in both cases Excel remains responsive and R/Julia are unaffected.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property 2: Preservation - R and Julia Behavior Unchanged

_For any_ configuration where Python is NOT enabled (isBugCondition returns false), the fixed code SHALL produce exactly the same behavior as the original code — R and Julia initialization, pipe communication, function registration, runtime calls, and hot-reload all work identically.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File 1**: `ControlPython/src/python_interface.cc`

**Function**: `PythonInit()`

**Specific Changes**:
1. **Add retry loop around `PyRun_SimpleString()`**: Wrap the startup.py execution in a retry loop (max 3 attempts). On failure, clear the Python error state with `PyErr_Clear()`, log the attempt number, and `Sleep(100)` before retrying. After all retries exhausted, log a fatal error and set a global flag `g_startup_failed = true`.
2. **Add startup success query function**: Add a new exported function `bool PythonStartupSucceeded()` that returns `!g_startup_failed`. This allows `control_python.cc` to check startup status and report it to the XLL.

**File 2**: `ControlPython/src/control_python.cc`

**Function**: `main()`

**Specific Changes**:
1. **Reorder initialization**: Move `Py_Initialize()` call to after all argument parsing and pipe setup is complete. Currently it's at line ~320; move it to just before `PythonInit()` (after pipe instances are created). This reduces stack pressure during CPython initialization.
2. **Add SEH guard around `Py_Initialize()`**: Wrap `Py_Initialize()` in a `__try/__except` block to catch `STATUS_STACK_BUFFER_OVERRUN` and other fatal exceptions. On catch, log the error and exit with `PROCESS_ERROR_CONFIGURATION_ERROR` instead of crashing silently.
3. **Check startup success after `PythonInit()`**: After `PythonInit()` returns, check `PythonStartupSucceeded()`. If false, log a warning but continue into `pipe_loop()` — the XLL will detect the failure via health status when it tries to call `list-functions`.
4. **Increase default stack size**: Add `/STACK:2097152` (2MB) to the linker flags in `ControlPython/CMakeLists.txt` to provide more headroom for CPython's initialization.

**File 3**: `Core/src/language_service.cc`

**Function**: `LanguageService::Initialize()`

**Specific Changes**:
1. **Send startup code as single block for Python**: Add a check for `language_descriptor_.name_ == "Python"`. For Python, instead of splitting into lines and skipping empty ones, add the entire startup code as a single `code->add_line(startup_code)` entry. This preserves blank lines, indentation, and docstrings. For R and Julia, keep the existing line-by-line behavior unchanged.

**Function**: `LanguageService::MapLanguageFunctions()`

**Specific Changes**:
2. **Add health status check**: Before calling `Call()`, check `if (health_status_ == HealthStatus::Unavailable) return {};`. This prevents blocking on a dead or broken process.

**File 4**: `Install/neven-config.json`

**Specific Changes**:
1. **Add Python section**: Add a `"Python"` section under `"NEVEN"` with `"enabled": false` by default, matching the Julia pattern:
   ```json
   "Python": {
     "home": "",
     "enabled": false,
     "minMajor": 3,
     "minMinor": 10,
     "maxMajor": 99
   }
   ```

**File 5**: `Install/neven-languages.json`

**Specific Changes**:
1. **Add Python entry back**: Add the Python language descriptor:
   ```json
   {
     "name": "Python",
     "executable": "ControlPython.exe",
     "prefix": "Py",
     "extensions": ["py"],
     "command_arguments": "",
     "prepend_path": "$HOME",
     "priority": 10,
     "startup_resource": "startup.py"
   }
   ```

**File 6**: `NEVEN/CMakeLists.txt`

**Specific Changes**:
1. **Update option description**: Change `option(NEVEN_ENABLE_PYTHON "Build ControlPython.exe (deprecated)" OFF)` to `option(NEVEN_ENABLE_PYTHON "Build ControlPython.exe (optional, requires Python >= 3.10)" OFF)`. Remove the "deprecated" label since Python is being reactivated.

**File 7**: `ControlPython/CMakeLists.txt`

**Specific Changes**:
1. **Add stack size linker flag**: Add `target_link_options(ControlPython PRIVATE /STACK:2097152)` to set a 2MB stack for the ControlPython process.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate each failure mode using the existing mock infrastructure (`MockExcelBridge`, mock pipes). Run these tests on the UNFIXED code to observe failures and confirm root causes.

**Test Cases**:
1. **Startup Retry Test**: Call `PythonInit()` with a corrupted `startup.py` path or content that causes `PyRun_SimpleString()` to fail. Verify that on unfixed code, no retry is attempted and `list_functions()` is undefined (will fail on unfixed code).
2. **Line-by-Line IndentationError Test**: Use `StringUtilities::Split()` on a Python script with multi-line functions and docstrings, filter empty lines, reassemble with `\n`, and verify the result produces `IndentationError` when parsed by Python (will fail on unfixed code).
3. **Health Status Bypass Test**: Create a `LanguageService` with `connected_ = true` but `health_status_ = Unavailable`, call `MapLanguageFunctions()`, and verify it still attempts the pipe call and blocks (will fail on unfixed code).
4. **Startup Code Preservation Test**: Split `startup.py` using the current `Split` + empty-line-filter logic, reassemble, and compare to original. Verify they differ (empty lines removed) — confirming the root cause of Bug 3.

**Expected Counterexamples**:
- `PythonInit()` fails once and never retries — `list_functions()` is not defined
- Reassembled startup code differs from original (missing blank lines between functions)
- `MapLanguageFunctions()` attempts pipe call on Unavailable service
- Possible causes: no retry logic, line-by-line splitting removes empty lines, no health check in `MapLanguageFunctions()`

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed functions produce the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := InitializeLanguageService'(input)
  ASSERT (result.status = Connected AND result.startup_ok = true)
      OR (result.status = Unavailable AND result.excel_stable = true AND result.r_julia_unaffected = true)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed code produces the same result as the original code.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT InitializeLanguageService(input) = InitializeLanguageService'(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (different config combinations, language selections, timeout values)
- It catches edge cases that manual unit tests might miss (e.g., config with Python section but `enabled: false`, config with no Python section at all)
- It provides strong guarantees that behavior is unchanged for all non-Python configurations

**Test Plan**: Observe behavior on UNFIXED code first for R and Julia operations, then write property-based tests capturing that behavior.

**Test Cases**:
1. **R Initialization Preservation**: Verify R language service initialization, startup script execution, and function registration work identically before and after the fix
2. **Julia Initialization Preservation**: Verify Julia language service initialization, JIT handling, and function registration work identically before and after the fix
3. **Config Parsing Preservation**: Verify that `neven-config.json` parsing for R and Julia sections produces identical `LanguageService` configuration before and after adding the Python section
4. **Timeout Behavior Preservation**: Verify that `GetCallTimeoutMs()` and `GetLanguageCallTimeoutMs()` return identical values for R and Julia before and after the fix

### Unit Tests

- Test `PythonInit()` retry logic: verify 3 retries on `PyRun_SimpleString()` failure, verify success on second attempt, verify `g_startup_failed` flag after all retries exhausted
- Test `LanguageService::Initialize()` sends single code block for Python vs line-by-line for R/Julia
- Test `MapLanguageFunctions()` returns empty list when `health_status_ == Unavailable`
- Test `neven-config.json` parsing with Python section present (`enabled: true`, `enabled: false`, missing `enabled` key)
- Test `neven-languages.json` parsing with Python entry present
- Test `CMakeLists.txt` builds ControlPython when `NEVEN_ENABLE_PYTHON=ON`

### Property-Based Tests

- Generate random `LanguageServiceConfig` inputs (varying language name, enabled flag, config presence) and verify that for Python-enabled configs the system either succeeds or marks Unavailable, and for non-Python configs behavior is identical to unfixed code
- Generate random startup script content (with varying indentation, blank lines, docstrings) and verify that the single-block sending preserves the original content exactly
- Generate random timeout values and verify that per-language timeout configuration works correctly for Python without affecting R/Julia timeouts

### Integration Tests

- Test full Python initialization flow: config parsing → discovery → process launch → pipe connect → startup.py execution → function registration
- Test Python failure recovery: simulate `startup.py` failure → verify retry → verify Unavailable marking → verify `UpdateFunctions()` completes without blocking
- Test mixed-language startup: R + Julia + Python (enabled) → verify all three initialize independently and a Python failure doesn't affect R/Julia
- Test Python disabled: R + Julia + Python (`enabled: false`) → verify Python is skipped entirely and R/Julia work normally
