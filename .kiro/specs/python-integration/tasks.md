# Tasks: Python Integration for RJ2XCL

## Task 1: Configuration Files and Build System Setup
- [x] 1.1 Add Python entry to `RJ2XCL/Install/rj2xcl-languages.json` with name "Python", executable "ControlPython.exe", prefix "P", extensions ["py"], startup_resource "startup.py"
- [x] 1.2 Add Python section to `RJ2XCL/Install/rj2xcl-config.json` under "RJ2XCL" with home "", minMajor 3, minMinor 10, maxMajor 99
- [x] 1.3 Create `RJ2XCL/ControlPython/CMakeLists.txt` following the ControlJulia pattern: find Python via PYTHON_HOME, link python3.lib, include Python.h
- [x] 1.4 Add `ControlPython` subdirectory to root `RJ2XCL/CMakeLists.txt` under the `if(NOT SKIP_LANGUAGE_TARGETS)` guard alongside ControlR and ControlJulia

## Task 2: Python Discovery Service
- [x] 2.1 Add `FindPython()` method to `RJ2XCL/Common/DiscoveryService.h`
- [x] 2.2 Implement `FindPython()` in `RJ2XCL/Common/DiscoveryService.cc` — search registry (`HKLM\SOFTWARE\Python\PythonCore`), env vars (`PYTHON_HOME`, `PYTHONHOME`), filesystem paths (`%LOCALAPPDATA%\Programs\Python\*`, `%PROGRAMFILES%\Python*`)
- [x] 2.3 Add Python case to `GetBestVersion()` in DiscoveryService so it calls `FindPython()` when language_name is "Python"
- [x] 2.4 Add validation in `FindPython()` to verify `python3.dll` or `python3XX.dll` and `include/Python.h` exist in each candidate

## Task 3: ControlPython Process — Main and Pipe Loop
- [x] 3.1 Create `RJ2XCL/ControlPython/include/python_interface.h` with function declarations: `PythonInit`, `PythonShutdown`, `PythonGetVersion`, `PythonExec`, `PythonCall`, `PythonShellExec`, `ListScriptFunctions`, `ReadSourceFile`
- [x] 3.2 Create `RJ2XCL/ControlPython/src/control_python.cc` with `main()` — parse `-p` argument, get Python version, validate version >= 3.10, create management thread, create stdio thread, create callback pipe, create primary pipe (blocking), call `PythonInit()`, enter `pipe_loop()`
- [x] 3.3 Implement `pipe_loop()` in `control_python.cc` — WaitForMultipleObjects on pipe handles, dispatch `kFunctionCall` (SystemCall or PythonCall), `kCode` (PythonExec), `kShellCommand` (PythonShellExec)
- [x] 3.4 Implement `SystemCall()` in `control_python.cc` — handle `get-language` (return "Python::<version>"), `read-source-file`, `install-application-pointer`, `list-functions`, `shutdown`, `console`, `close`
- [x] 3.5 Implement `ManagementThreadFunction()` — listen on `<pipename>-M`, on "break" call `PyErr_SetInterrupt()` with GIL
- [x] 3.6 Implement `StdioThreadFunction()` — capture stdout/stderr pipe redirection, forward to console clients (mirror ControlJulia pattern)

## Task 4: Python Interface — CPython Embedding
- [x] 4.1 Create `RJ2XCL/ControlPython/src/python_interface.cc` with `PythonInit()` — read config from `rj2xcl-config.json`, call `Py_Initialize()`, execute `startup.py` via `PyRun_SimpleString`
- [x] 4.2 Implement `PythonShutdown()` — call `Py_FinalizeEx()`
- [x] 4.3 Implement `PythonGetVersion()` — parse `Py_GetVersion()` string into major, minor, patch integers
- [x] 4.4 Implement `PythonExec()` — execute code via `PyRun_String` with `Py_eval_input` for expressions, fall back to `Py_file_input` for statements; convert result via `PyObjectToVariable`; capture exceptions via `PyErr_Fetch` + traceback
- [x] 4.5 Implement `PythonCall()` — resolve function by name via `PyObject_GetAttrString` on `__main__`, build argument tuple from Protobuf arguments via `VariableToPyObject`, call via `PyObject_CallObject`, convert result
- [x] 4.6 Implement `PythonShellExec()` — use `PyRun_InteractiveOne` or `code.InteractiveConsole` equivalent for multi-line support; return ExecResult (Success/Incomplete/Error)
- [x] 4.7 Implement `ListScriptFunctions()` — call `startup.list_functions()` Python function, convert returned list to Protobuf `CallResponse` with function descriptors
- [x] 4.8 Implement `ReadSourceFile()` — call `startup.read_script_file(path, notify)` Python function

## Task 5: Type Conversion (Protobuf ↔ Python)
- [x] 5.1 Implement `VariableToPyObject()` in `python_interface.cc` — map Protobuf Variable to PyObject: real→PyFloat, integer→PyLong, str→PyUnicode, boolean→PyBool, nil→Py_None
- [x] 5.2 Implement `VariableToPyObject()` for Array types — 1D array → numpy.ndarray (or list fallback), 2D matrix → pandas.DataFrame (or list-of-lists fallback)
- [x] 5.3 Implement `PyObjectToVariable()` in `python_interface.cc` — map PyObject to Protobuf Variable: PyFloat→real, PyLong→integer, PyUnicode→str, PyBool→boolean, Py_None→nil
- [x] 5.4 Implement `PyObjectToVariable()` for container types — pandas.DataFrame → Array with headers as first row, numpy.ndarray → Array (1D or 2D), list → Array, unsupported → str(obj)

## Task 6: Sandbox Verifier — Python Patterns
- [x] 6.1 Add `python_blocked` pattern vector to `SandboxVerifier::ValidateCodeForExecution()` in `RJ2XCL/Common/SandboxVerifier.cc` with all shell, file, dynamic code, native, network, and environment patterns
- [x] 6.2 Add Python bypass detection to the advanced bypass section — `getattr()` with suspicious modules, string concatenation patterns constructing blocked function names
- [x] 6.3 Add Python pattern checking loop in `ValidateCodeForExecution()` that checks both `lower_code` and `stripped_code` against `python_blocked` patterns (same as R and Julia)

## Task 7: Startup Script
- [x] 7.1 Create `RJ2XCL/startup/startup.py` with `list_functions()` — introspect `__main__` module for user-defined functions, return metadata list with name, arguments (via `inspect.signature`), docstring, category "Python"
- [x] 7.2 Implement `read_script_file(path, notify=False)` in `startup.py` — execute file in `__main__` namespace via `exec(open(path).read(), ...)`
- [x] 7.3 Implement `install_application_pointer(pointer)` in `startup.py` — store COM pointer in module-level variable
- [x] 7.4 Implement graphics helpers in `startup.py` — configure matplotlib Agg backend, `rj2xcl_graphics_device(width, height)` returning PNG path, `rj2xcl_last_plot()` returning last plot path with Windows backslashes, plotly HTML export helper
- [x] 7.5 Add package availability checks at startup — attempt import of numpy, pandas, matplotlib, sklearn; log warnings for missing packages; print "RJ2XCL Python startup complete"

## Task 8: Sandbox Tests for Python Patterns
- [x] 8.1 Add Python shell execution blocked tests to `RJ2XCL/tests/sandbox_tests.cc` — `Python_BlocksOsSystem`, `Python_BlocksOsPopen`, `Python_BlocksSubprocessCall`, `Python_BlocksSubprocessRun`, `Python_BlocksSubprocessPopen`, `Python_BlocksSubprocessCheckOutput`, `Python_BlocksSubprocessCheckCall`
- [x] 8.2 Add Python file manipulation blocked tests — `Python_BlocksOsRemove`, `Python_BlocksOsUnlink`, `Python_BlocksOsRmdir`, `Python_BlocksOsRename`, `Python_BlocksShutilRmtree`, `Python_BlocksShutilMove`, `Python_BlocksShutilCopy`
- [x] 8.3 Add Python dynamic code blocked tests — `Python_BlocksExec`, `Python_BlocksEval`, `Python_BlocksCompile`, `Python_BlocksDunderImport`, `Python_BlocksImportlib`
- [x] 8.4 Add Python native/unsafe blocked tests — `Python_BlocksCtypesCdll`, `Python_BlocksCtypesWindll`, `Python_BlocksCtypesCDLL`, `Python_BlocksCtypesWinDLL`
- [x] 8.5 Add Python network blocked tests — `Python_BlocksUrllib`, `Python_BlocksSocket`, `Python_BlocksHttpClient`
- [x] 8.6 Add Python environment blocked tests — `Python_BlocksOsEnviron`, `Python_BlocksOsPutenv`, `Python_BlocksOsChdir`
- [x] 8.7 Add Python bypass prevention tests — whitespace (`"os . system('dir')"`, `"os.system ('dir')"`), case variation (`"OS.SYSTEM('dir')"`, `"Os.System('dir')"`), getattr bypass (`"getattr(__import__('os'), 'system')('dir')"`), string concatenation
- [x] 8.8 Add Python allowed operations tests — `Python_AllowsImportPandas`, `Python_AllowsDescribe`, `Python_AllowsNpMean`, `Python_AllowsLen`, `Python_AllowsArithmetic`, `Python_AllowsPrint`, `Python_AllowsListComprehension`, `Python_AllowsStringFormat`

## Task 9: Property-Based Sandbox Tests
- [x] 9.1 Create `RJ2XCL/tests/python_sandbox_pbt.cc` with test fixture and random generators for Python code strings
- [x] 9.2 Implement Property 5 test: generate random blocked patterns with whitespace/case variation, verify all rejected with non-empty reason (min 100 iterations)
- [x] 9.3 Implement Property 7 test: generate random safe Python code strings (arithmetic, assignments, safe function calls), verify all accepted (min 100 iterations)
- [x] 9.4 Implement Property 8 test: generate random Python code strings (mix of safe and unsafe), verify idempotent validation — same result on two consecutive calls (min 100 iterations)
- [x] 9.5 Add `python_sandbox_pbt.cc` to `RJ2XCL/tests/CMakeLists.txt` test executable sources

## Task 10: Hot-Reload Support
- [x] 10.1 Add `.py` extension handling to `FileWatchService` so it monitors Python source files alongside `.r` and `.jl` files
- [x] 10.2 Verify that `FileWatchService` sends `read-source-file` command to the Python `LanguageService` when a `.py` file changes (same mechanism as R/Julia)

## Task 11: Documentation and Verification
- [x] 11.1 Build the project with `cmake --build` and verify ControlPython.exe compiles (requires Python SDK on build machine, or use SKIP_LANGUAGE_TARGETS for CI)
- [x] 11.2 Run `rj2xcl_tests` and verify all new sandbox tests pass (Python blocked patterns, allowed operations, bypass prevention, property-based tests)
