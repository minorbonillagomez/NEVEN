# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Python Startup Failures and Blocking Behavior
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bugs exist
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the four root causes
  - **Scoped PBT Approach**: Scope the property to concrete failing cases for each bug:
    - **Bug 1 (No retry)**: Call `PythonInit()` with a startup.py that fails `PyRun_SimpleString()` (rc=-1). Assert that the system retries up to 3 times and sets `g_startup_failed = true` after exhaustion. On unfixed code: no retry occurs, no `g_startup_failed` flag exists — test FAILS.
    - **Bug 3 (Line-by-line IndentationError)**: Use `StringUtilities::Split(startup_code, '\n', 1, lines, true)` on a Python script with multi-line functions containing docstrings and blank-line separators. Filter empty lines (`if (line.length() > 0)`), reassemble with `\n`. Assert the reassembled code equals the original. On unfixed code: empty lines are stripped, assertion FAILS.
    - **Bug 4 (No health check)**: Create a `LanguageService` with `connected_ = true` and `health_status_ = HealthStatus::Unavailable`. Call `MapLanguageFunctions()`. Assert it returns an empty list immediately without calling `Call()`. On unfixed code: `MapLanguageFunctions()` does not check `health_status_` and attempts the pipe call — test FAILS.
  - Test file: `NEVEN/tests/python_reactivation_exploration_pbt.cc`
  - Add test file to `NEVEN/tests/CMakeLists.txt`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bugs exist)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - R and Julia Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (R-only, Julia-only, Python-disabled configs)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - **R initialization preservation**: Verify R `LanguageService` construction with config `{"NEVEN":{"R":{"home":""}}}` produces `configured_ = true`, `language_descriptor_.name_ = "R"`. Verify `Initialize()` sends startup code line-by-line (existing behavior). Generate random R-style startup scripts and verify `Split` + line-by-line sending preserves all non-empty lines correctly.
    - **Julia initialization preservation**: Verify Julia `LanguageService` construction with config `{"NEVEN":{"Julia":{"home":"","enabled":true}}}` produces `configured_ = true`. Verify `Initialize()` sends startup code line-by-line with `wait = false` (JIT mode). Generate random Julia-style scripts and verify line-by-line sending works correctly.
    - **Python-disabled preservation**: Verify that when config has `"Python":{"home":"","enabled":false}`, `LanguageService` sets `configured_ = false` and returns early. Verify that when config has no Python section at all, `configured_ = false`.
    - **Config parsing preservation**: Verify that adding a `"Python"` section to `neven-config.json` does not alter parsing of `"R"` or `"Julia"` sections. Generate random config JSON objects with R/Julia sections and optional Python section; assert R/Julia values are identical with and without Python present.
    - **Health-aware dispatch preservation**: Verify `LanguageManager::CallLanguage()` for R and Julia services with `HealthStatus::Healthy` continues to call `service->Call()` as before. Verify `CallLanguage()` with invalid key still returns `"invalid language key"` error.
  - Test file: `NEVEN/tests/python_reactivation_preservation_pbt.cc`
  - Add test file to `NEVEN/tests/CMakeLists.txt`
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Configuration re-enablement (enable Python build and config entries)

  - [x] 3.1 Add Python section to `Install/neven-config.json`
    - Add `"Python": { "home": "", "enabled": false, "minMajor": 3, "minMinor": 10, "maxMajor": 99 }` under `"NEVEN"`, after the Julia section
    - Python MUST be `"enabled": false` by default — user opts in
    - Follows the existing Julia pattern with `enabled` field
    - _Requirements: 2.6, 3.1_

  - [x] 3.2 Add Python section to `Build/Dist/neven-config.json`
    - Same Python section as 3.1: `"Python": { "home": "", "enabled": false, "minMajor": 3, "minMinor": 10, "maxMajor": 99 }`
    - Keep in sync with Install version
    - _Requirements: 2.6, 3.1_

  - [x] 3.3 Add Python language descriptor to `Install/neven-languages.json`
    - Add entry: `{ "name": "Python", "executable": "ControlPython.exe", "prefix": "Py", "extensions": ["py"], "command_arguments": "", "prepend_path": "$HOME", "priority": 10, "startup_resource": "startup.py" }`
    - Append after the Julia entry in the JSON array
    - _Requirements: 2.6_

  - [x] 3.4 Update `NEVEN/CMakeLists.txt` option description
    - Change `option(NEVEN_ENABLE_PYTHON "Build ControlPython.exe (deprecated)" OFF)` to `option(NEVEN_ENABLE_PYTHON "Build ControlPython.exe (optional, requires Python >= 3.10)" OFF)`
    - Remove the "deprecated" label since Python is being reactivated
    - _Requirements: 2.6_

  - [x] 3.5 Add `/STACK:2097152` linker flag to `ControlPython/CMakeLists.txt`
    - Add `target_link_options(ControlPython PRIVATE /STACK:2097152)` after the `target_link_libraries` block
    - Sets 2MB stack for ControlPython.exe to provide headroom for CPython initialization
    - _Bug_Condition: isBugCondition(input) where ControlPython.exe crashes with STATUS_STACK_BUFFER_OVERRUN during Py_Initialize()_
    - _Requirements: 2.3_

- [x] 4. Fix 2 — Stack buffer overrun guard in `ControlPython/src/control_python.cc`

  - [x] 4.1 Move `Py_Initialize()` after argument parsing and pipe setup
    - Currently `Py_Initialize()` is called at line ~320 before pipe instances are created
    - Move it to just before `PythonInit()` call (after `NextPipeInstance` calls and stdio setup)
    - This reduces stack pressure during CPython initialization by ensuring local variables from pipe setup are already deallocated or in a stable state
    - _Bug_Condition: isBugCondition(input) where Py_Initialize() is called with high stack usage from local variables (buffer[MAX_PATH], stringstream, pipe objects)_
    - _Expected_Behavior: Py_Initialize() runs with minimal stack pressure after pipe setup is complete_
    - _Preservation: R and Julia ControlR.exe/ControlJulia.exe are not modified_
    - _Requirements: 2.3_

  - [x] 4.2 Add SEH guard (`__try/__except`) around `Py_Initialize()`
    - Wrap `Py_Initialize()` in `__try { Py_Initialize(); } __except(EXCEPTION_EXECUTE_HANDLER) { ... }`
    - On exception: log the error with `CHILD_LOG_ERR`, call `rj2xcl::ChildProcessLog::Shutdown()`, and `return PROCESS_ERROR_CONFIGURATION_ERROR`
    - Catches `STATUS_STACK_BUFFER_OVERRUN` and other fatal exceptions gracefully instead of silent crash
    - _Bug_Condition: isBugCondition(input) where Py_Initialize() triggers STATUS_STACK_BUFFER_OVERRUN (0xC0000409)_
    - _Expected_Behavior: Exception is caught, logged, and process exits with known error code_
    - _Requirements: 2.3_

  - [x] 4.3 Check `PythonStartupSucceeded()` after `PythonInit()` returns
    - After `PythonInit()` returns, call `PythonStartupSucceeded()`
    - If false: log a warning (`CHILD_LOG_WARN("startup.py failed — Python functions will not be available")`) but continue into `pipe_loop()` — the XLL will detect the failure via health status
    - _Requirements: 2.2, 2.5_

- [x] 5. Fix 1 — Retry `startup.py` execution in `ControlPython/src/python_interface.cc`

  - [x] 5.1 Add retry loop around `PyRun_SimpleString()` in `PythonInit()`
    - Wrap the `PyRun_SimpleString(startup_result.value().c_str())` call in a retry loop (max 3 attempts)
    - On failure (rc != 0): call `PyErr_Clear()`, log the attempt number (`CHILD_LOG_WARN("startup.py attempt %d/%d failed (rc=%d)", attempt, max_retries, rc)`), and `Sleep(100)` before retrying
    - On success: break out of loop and log success
    - After all retries exhausted: log fatal error and set `g_startup_failed = true`
    - _Bug_Condition: isBugCondition(input) where PyRun_SimpleString() returns rc=-1 and no retry is attempted_
    - _Expected_Behavior: System retries up to 3 times with PyErr_Clear() + Sleep(100) between attempts_
    - _Preservation: PythonInit() still reads config and startup.py the same way; only the execution has retry logic_
    - _Requirements: 2.1_

  - [x] 5.2 Add global flag `g_startup_failed` and exported function `PythonStartupSucceeded()`
    - Add `static bool g_startup_failed = false;` at file scope
    - Add `bool PythonStartupSucceeded() { return !g_startup_failed; }` as an exported function
    - Declare `bool PythonStartupSucceeded();` in `python_interface.h`
    - This allows `control_python.cc` to check startup status and report it to the XLL
    - _Requirements: 2.1, 2.2_

- [x] 6. Fix 3 — Send startup code as single block for Python in `Core/src/language_service.cc`

  - [x] 6.1 Modify `LanguageService::Initialize()` to send single code block for Python
    - In the startup code sending section, add a check: `if (language_descriptor_.name_ == "Python")`
    - For Python: instead of splitting into lines and filtering empty ones, add the entire startup code as a single `code->add_line(startup_code)` entry
    - For R and Julia: keep the existing line-by-line behavior completely unchanged (the `Split` + `for` loop + `if (line.length() > 0)` pattern)
    - This preserves blank lines, indentation, and docstrings in Python's `startup.py`
    - _Bug_Condition: isBugCondition(input) where startup.py is split line-by-line, empty lines are stripped, and reassembly produces IndentationError_
    - _Expected_Behavior: Python startup code is sent as a single block preserving all whitespace and blank lines_
    - _Preservation: R startup code continues to be sent line-by-line with wait=true; Julia startup code continues to be sent line-by-line with wait=false_
    - _Requirements: 2.4, 3.2_

- [x] 7. Fix 4 — Health check before calling in `Core/src/language_service.cc`

  - [x] 7.1 Add health status check in `MapLanguageFunctions()`
    - Add `if (health_status_ == HealthStatus::Unavailable) return {};` immediately after the existing `if (!connected_) return {};` check
    - This prevents blocking on a dead or broken Python process when `connected_` is still `true` but the process has crashed
    - _Bug_Condition: isBugCondition(input) where connected_=true but health_status_=Unavailable, and Call() blocks on WaitForSingleObject() for up to 10 minutes_
    - _Expected_Behavior: MapLanguageFunctions() returns empty list immediately for Unavailable services_
    - _Preservation: R and Julia services with HealthStatus::Healthy or HealthStatus::Unknown are unaffected — the new check only short-circuits for Unavailable_
    - _Requirements: 2.5, 3.3_

- [x] 8. Verify fixes with exploration and preservation tests

  - [x] 8.1 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Python Resilient Initialization
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior for all four bugs
    - When this test passes, it confirms:
      - `PythonInit()` retries on failure and sets `g_startup_failed` after exhaustion
      - Startup code sent as single block preserves original content (no IndentationError)
      - `MapLanguageFunctions()` returns empty list for Unavailable services without blocking
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bugs are fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 8.2 Verify preservation tests still pass
    - **Property 2: Preservation** - R and Julia Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after fix (no regressions to R/Julia behavior)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 9. Checkpoint — Ensure all tests pass
  - Run the full test suite: `ctest --test-dir build --output-on-failure`
  - Verify all 228 existing tests continue to pass
  - Verify the new exploration test (task 1) now passes
  - Verify the new preservation tests (task 2) still pass
  - If any test fails, investigate and fix before proceeding
  - Ensure all tests pass, ask the user if questions arise
