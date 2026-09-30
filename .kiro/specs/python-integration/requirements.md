# Requirements Document: Python Integration for RJ2XCL

## Introduction

This document specifies the requirements for integrating Python as a third language in the RJ2XCL platform. RJ2XCL is a C++17 Excel add-in (XLL) that currently integrates R and Julia with Microsoft Excel via process isolation (Named Pipes + Protobuf). The Python integration follows the established architecture: a new child process (`ControlPython.exe`) embedding CPython via the C API, communicating with the XLL through the same IPC protocol. Users will invoke Python functions from Excel cells using the `P.` prefix (e.g., `=P.MyFunction(A1:A10)`) and inline code via `=RJ2XCL.P("expression")`, consistent with the existing convention (`RJ2XCL.R`, `RJ2XCL.J`, `RJ2XCL.P`). This provides access to pandas, scikit-learn, matplotlib, and the broader Python ecosystem.

## Glossary

- **XLL**: Excel add-in dynamic library (RJ2XCL64.xll) that registers worksheet functions and manages language services
- **ControlPython**: Child process executable (`ControlPython.exe`) that embeds the CPython interpreter and communicates with the XLL via Named Pipes
- **LanguageManager**: Component in the XLL that discovers, launches, and manages connections to language service processes (ControlR, ControlJulia, ControlPython)
- **DiscoveryService**: Component that locates language runtime installations on the user's system (registry, filesystem, environment variables)
- **SandboxVerifier**: Security component that validates code strings against blocked patterns before execution, preventing shell access, file manipulation, and network operations
- **ConfigService**: Singleton that manages application configuration from `rj2xcl-config.json`, providing validated settings to all components
- **LanguageDescriptor**: Data structure describing a language service (name, executable, prefix, extensions, startup script, home path)
- **Protobuf**: Google Protocol Buffers — binary serialization format used for IPC between the XLL and child processes
- **Named_Pipe**: Windows IPC mechanism used for bidirectional communication between the XLL and language service processes
- **Startup_Script**: Language-specific initialization script (`startup.py`) loaded at process start, providing function listing, script loading, and Excel integration utilities
- **FileWatchService**: Component that monitors source files for changes and triggers hot-reload in the corresponding language service
- **CPython_C_API**: The C-level embedding API (`Python.h`, `Py_Initialize`, `PyRun_String`, etc.) used to embed the Python interpreter in ControlPython.exe
- **Function_Registry**: The mechanism by which user-defined Python functions are discovered, listed, and registered as Excel worksheet functions with the `P.` prefix
- **Graphics_Pipeline**: The subsystem that captures graphical output (matplotlib figures, plotly charts) and delivers them as image files or HTML for display from Excel

## Requirements

### Requirement 1: Python Installation Discovery

**User Story:** As a user, I want RJ2XCL to automatically find my Python installation, so that I do not need to manually configure paths.

#### Acceptance Criteria

1. WHEN RJ2XCL starts, THE DiscoveryService SHALL search for Python installations in the following locations in priority order: (a) the `home` override in `rj2xcl-config.json` Python section, (b) the `PYTHON_HOME` or `PYTHONHOME` environment variable, (c) the Windows Registry under `HKLM\SOFTWARE\Python\PythonCore`, (d) common filesystem paths (`%LOCALAPPDATA%\Programs\Python\*`, `%PROGRAMFILES%\Python*`)
2. THE DiscoveryService SHALL select the highest-version Python installation that satisfies the minimum version constraint (major >= 3, minor >= 10)
3. IF no Python installation meeting the minimum version is found, THEN THE LanguageManager SHALL log a warning and skip Python language registration without affecting R or Julia services
4. THE DiscoveryService SHALL verify that the selected Python installation contains `python3.dll` (stable ABI) or `python3XX.dll` and the `include/Python.h` header before accepting the installation as valid
5. WHEN a valid Python installation is found, THE DiscoveryService SHALL return a `LanguageInstallation` struct with name, version, home path, and 64-bit flag consistent with the existing R and Julia discovery pattern

### Requirement 2: Language Configuration Registration

**User Story:** As a developer, I want Python to be registered in the language configuration system, so that the LanguageManager can launch and manage ControlPython.exe like the existing language services.

#### Acceptance Criteria

1. THE language configuration file (`rj2xcl-languages.json`) SHALL include a Python entry with: name `"Python"`, executable `"ControlPython.exe"`, prefix `"P"`, extensions `["py"]`, and startup resource `"startup.py"`
2. THE configuration file (`rj2xcl-config.json`) SHALL include a `"Python"` section with fields: `home` (string, default empty), `minMajor` (integer, default 3), `minMinor` (integer, default 10), `maxMajor` (integer, default 99)
3. WHEN the LanguageManager reads the language configuration, THE LanguageManager SHALL construct a `LanguageDescriptor` for Python and launch `ControlPython.exe` using the same process isolation pattern as ControlR.exe and ControlJulia.exe
4. THE Python language entry SHALL use the prefix `"P"` so that registered Python functions appear in Excel as `=P.FunctionName(args)`, consistent with the convention `R.` for R and `J.` for Julia

### Requirement 3: ControlPython.exe Process Architecture

**User Story:** As a developer, I want ControlPython.exe to follow the same architecture as ControlR.exe and ControlJulia.exe, so that the codebase remains consistent and maintainable.

#### Acceptance Criteria

1. THE ControlPython process SHALL embed the CPython interpreter using the C API (`Py_Initialize`, `Py_Finalize`, `PyRun_SimpleString`, `PyObject_CallObject`)
2. THE ControlPython process SHALL accept a pipe name via the `-p` command-line argument and establish Named Pipe communication with the XLL using the existing `Pipe` class from `Common/pipe.h`
3. THE ControlPython process SHALL implement the same pipe loop pattern as ControlJulia: waiting on multiple pipe handles, processing `kFunctionCall`, `kCode`, and `kShellCommand` Protobuf messages
4. THE ControlPython process SHALL support the following system commands via `SystemCall`: `get-language`, `read-source-file`, `install-application-pointer`, `list-functions`, `shutdown`, `console`, and `close`
5. THE ControlPython process SHALL report its language tag as `"Python::<major>.<minor>.<patch>"` in response to the `get-language` system command
6. THE ControlPython process SHALL create a management pipe (`<pipename>-M`) on a separate thread for receiving break/interrupt signals, following the ControlJulia pattern
7. THE ControlPython process SHALL capture Python stdout and stderr via pipe redirection and forward them to console clients, following the ControlJulia stdio thread pattern

### Requirement 4: Python Startup Script

**User Story:** As a developer, I want a startup script that initializes the Python environment inside ControlPython, so that function discovery, script loading, and Excel integration work consistently with R and Julia.

#### Acceptance Criteria

1. THE Startup_Script (`startup/startup.py`) SHALL define a `list_functions()` function that introspects all user-defined functions in the `__main__` module and returns their metadata (name, docstring, category, argument names, default values) in the same format expected by the XLL's `CreateFunctionList`
2. THE Startup_Script SHALL define a `read_script_file(path, notify=False)` function that executes a Python source file in the `__main__` namespace using `exec(open(path).read(), __main__.__dict__)`
3. THE Startup_Script SHALL define an `install_application_pointer(pointer)` function that stores the Excel COM application pointer for optional COM automation
4. THE Startup_Script SHALL set the `category` field to `"Python"` for all discovered functions, consistent with R using `"Exported R Functions"` and Julia using `"Julia"`
5. WHEN the Startup_Script completes initialization, THE Startup_Script SHALL print `"RJ2XCL Python startup complete"` to stdout

### Requirement 5: Excel Function Registration with P. Prefix

**User Story:** As a user, I want to call my Python functions from Excel cells using the `P.` prefix, so that I can distinguish Python functions from R and Julia functions consistently (`R.`, `J.`, `P.`).

#### Acceptance Criteria

1. WHEN ControlPython returns the function list via the `list-functions` system command, THE XLL SHALL register each function as an Excel worksheet function with the `P.` prefix (e.g., a Python function `my_regression` becomes `=P.my_regression(...)`)
2. THE Function_Registry SHALL extract argument names and default values from Python function signatures using `inspect.signature` so that Excel's Function Wizard displays meaningful parameter names
3. THE Function_Registry SHALL extract the function's docstring and use it as the Excel function description in the Function Wizard
4. IF a Python function name conflicts with an existing R or Julia function name, THEN THE LanguageManager SHALL resolve the conflict via the prefix (`P.func` vs `R.func` vs `J.func`) without error

### Requirement 6: Type Conversion (Excel ↔ Protobuf ↔ Python)

**User Story:** As a user, I want Excel data to be correctly converted to Python types and vice versa, so that I can use pandas DataFrames, numpy arrays, and standard Python types seamlessly.

#### Acceptance Criteria

1. THE ControlPython type converter SHALL map Protobuf types to Python types as follows: `double` → `float`, `integer` → `int`, `string` → `str`, `boolean` → `bool`, `nil/missing` → `None`
2. THE ControlPython type converter SHALL map a Protobuf matrix (2D array of values) to a `pandas.DataFrame` when pandas is available, or to a list of lists as fallback
3. THE ControlPython type converter SHALL map a Protobuf array (1D) to a `numpy.ndarray` when numpy is available, or to a Python `list` as fallback
4. WHEN a Python function returns a `pandas.DataFrame`, THE ControlPython type converter SHALL serialize the DataFrame to a Protobuf matrix including column headers as the first row
5. WHEN a Python function returns a `numpy.ndarray`, THE ControlPython type converter SHALL serialize the array to a Protobuf array (1D) or matrix (2D) depending on the array's dimensionality
6. WHEN a Python function returns a scalar (`int`, `float`, `str`, `bool`, `None`), THE ControlPython type converter SHALL serialize the value to the corresponding Protobuf type
7. IF a Python function returns an unsupported type, THEN THE ControlPython type converter SHALL call `str()` on the object and return the string representation

### Requirement 7: Sandbox Security Patterns for Python

**User Story:** As a user, I want the sandbox to block dangerous Python code entered in Excel cells, so that malicious workbooks cannot execute arbitrary system commands.

#### Acceptance Criteria

1. THE SandboxVerifier SHALL block the following Python shell execution patterns: `os.system(`, `os.popen(`, `subprocess.call(`, `subprocess.run(`, `subprocess.Popen(`, `subprocess.check_output(`, `subprocess.check_call(`
2. THE SandboxVerifier SHALL block the following Python file manipulation patterns: `os.remove(`, `os.unlink(`, `os.rmdir(`, `os.rename(`, `shutil.rmtree(`, `shutil.move(`, `shutil.copy(`
3. THE SandboxVerifier SHALL block the following Python dynamic code execution patterns: `exec(`, `eval(`, `compile(`, `__import__(`, `importlib.import_module(`
4. THE SandboxVerifier SHALL block the following Python native/unsafe patterns: `ctypes.cdll`, `ctypes.windll`, `ctypes.CDLL(`, `ctypes.WinDLL(`
5. THE SandboxVerifier SHALL block the following Python network patterns: `urllib.request.urlopen(`, `socket.socket(`, `http.client.HTTPConnection(`
6. THE SandboxVerifier SHALL block the following Python environment manipulation patterns: `os.environ[`, `os.putenv(`, `os.chdir(`
7. THE SandboxVerifier SHALL apply the same whitespace-stripping and case-insensitive matching to Python patterns as currently applied to R and Julia patterns
8. THE SandboxVerifier SHALL detect Python string concatenation bypass attempts where `"os" + ".system"` or `getattr(os, "system")` patterns are used to construct blocked function names
9. WHEN a Python code string passes all pattern checks, THE SandboxVerifier SHALL return `true` with an empty rejection reason

### Requirement 8: Hot-Reload of Python Source Files

**User Story:** As a user, I want my Python source files to be automatically reloaded when I save changes, so that updated functions are immediately available in Excel without restarting.

#### Acceptance Criteria

1. THE FileWatchService SHALL monitor `.py` files in the configured functions directory for modifications, following the same pattern used for `.r` and `.jl` files
2. WHEN a `.py` file is modified, THE FileWatchService SHALL send a `read-source-file` command to ControlPython with the file path
3. WHEN ControlPython receives a `read-source-file` command, THE ControlPython process SHALL re-execute the file in the `__main__` namespace, replacing previously defined functions with their updated versions
4. AFTER re-executing a source file, THE ControlPython process SHALL re-run function discovery and send the updated function list to the XLL for re-registration

### Requirement 9: Graphics Support

**User Story:** As a user, I want to generate matplotlib plots and plotly charts from Excel and view the results, so that I can create data visualizations using Python's ecosystem.

#### Acceptance Criteria

1. THE Startup_Script SHALL configure matplotlib to use the `Agg` (non-interactive) backend by default to prevent GUI window creation from the child process
2. WHEN a Python function calls `matplotlib.pyplot.savefig()` or the RJ2XCL graphics device wrapper, THE Graphics_Pipeline SHALL save the figure as a PNG file in the configured graphics directory (`%USERPROFILE%\Documents\RJ2XCL\graphics`)
3. THE Startup_Script SHALL provide a `rj2xcl_graphics_device(width=800, height=600)` helper function that creates a matplotlib figure with the specified dimensions and returns the output file path, following the pattern of R's `BERT.graphics.device`
4. WHEN a Python function generates a plotly figure, THE Graphics_Pipeline SHALL export the figure as an HTML file in the graphics directory using `plotly.io.write_html()`
5. THE Graphics_Pipeline SHALL generate unique filenames using a timestamp and random suffix pattern (`rj2xcl_plot_YYYYMMDD_HHMMSS_NNNN.png`) to prevent file collisions, consistent with the R graphics naming convention

### Requirement 10: Python Package Availability

**User Story:** As a user, I want to use pandas, numpy, scikit-learn, and matplotlib from Excel, so that I can leverage Python's data science ecosystem.

#### Acceptance Criteria

1. THE Startup_Script SHALL attempt to import `numpy`, `pandas`, `matplotlib`, and `sklearn` at initialization and log a warning for each package that is not available, without failing startup
2. THE documentation SHALL specify that users are responsible for installing Python packages in their Python environment using `pip install` or `conda install` before using them from Excel
3. IF a Python function references a package that is not installed, THEN THE ControlPython process SHALL return the Python `ModuleNotFoundError` message as the Excel cell error value

### Requirement 11: Code Execution via Excel Cells

**User Story:** As a user, I want to execute inline Python code from Excel cells using `=RJ2XCL.P("code")`, so that I can run quick Python expressions without defining a function file, consistent with `=RJ2XCL.R()` and `=RJ2XCL.J()`.

#### Acceptance Criteria

1. WHEN the XLL receives a `=RJ2XCL.P("expression")` call, THE XLL SHALL validate the code string against the SandboxVerifier before sending it to ControlPython
2. WHEN ControlPython receives a `kCode` message, THE ControlPython process SHALL execute the code string in the `__main__` namespace using `PyRun_String` with `Py_eval_input` for expressions and `Py_file_input` for statements
3. WHEN the Python code execution produces a result, THE ControlPython process SHALL convert the result to a Protobuf response using the type conversion rules from Requirement 6
4. IF the Python code raises an exception, THEN THE ControlPython process SHALL capture the traceback using `traceback.format_exc()` and return the error message as the Protobuf error field

### Requirement 12: Console Support

**User Story:** As a user, I want an interactive Python console within RJ2XCL, so that I can test Python code interactively like I can with R and Julia.

#### Acceptance Criteria

1. WHEN a console client connects via the `console` system command, THE ControlPython process SHALL set the console client pipe index and flush any buffered console output, following the ControlJulia pattern
2. THE ControlPython process SHALL display the Python prompt `">>> "` for normal input and `"... "` for continuation lines when processing `kShellCommand` messages
3. WHEN the ControlPython process receives a shell command, THE ControlPython process SHALL execute the command using `code.InteractiveConsole` or equivalent, supporting multi-line statements
4. WHEN the user triggers a break signal via the management pipe, THE ControlPython process SHALL raise a `KeyboardInterrupt` in the Python interpreter to cancel the current operation

### Requirement 13: Testing Requirements

**User Story:** As a developer, I want comprehensive tests for the Python integration, so that I can verify correctness and prevent regressions.

#### Acceptance Criteria

1. THE test suite SHALL include sandbox tests for all Python blocked patterns listed in Requirement 7, following the same GTest structure as the existing `sandbox_tests.cc`
2. THE test suite SHALL include sandbox tests verifying that legitimate Python code is not blocked (e.g., `"import pandas as pd"`, `"df.describe()"`, `"np.mean([1,2,3])"`, `"len([1,2,3])"`), preventing false positives
3. THE test suite SHALL include sandbox tests for Python-specific bypass attempts: whitespace insertion (`"os . system('dir')"`) , case variation (`"OS.SYSTEM('dir')"`) , and string concatenation (`"getattr(__import__('os'), 'system')('dir')"`)
4. FOR ALL valid Python code strings that contain no blocked patterns, parsing the code through the SandboxVerifier then re-checking SHALL produce the same result (idempotence property)
5. FOR ALL blocked Python patterns, the SandboxVerifier SHALL return a non-empty rejection reason string that identifies the specific blocked operation

### Requirement 14: Error Handling and Process Lifecycle

**User Story:** As a user, I want ControlPython to handle errors gracefully and recover from failures, so that a Python error does not crash Excel.

#### Acceptance Criteria

1. IF ControlPython.exe fails to initialize the Python interpreter (`Py_Initialize` fails), THEN THE ControlPython process SHALL log the error and exit with the `PROCESS_ERROR_CONFIGURATION_ERROR` exit code
2. IF the Named Pipe connection between the XLL and ControlPython breaks, THEN THE LanguageManager SHALL attempt reconnection up to `maxRetries` times (from ConfigService) before marking the Python service as unavailable
3. IF a Python function execution exceeds the configured `callTimeoutMs`, THEN THE XLL SHALL cancel the pending call and return a timeout error to the Excel cell
4. WHEN the XLL sends a `shutdown` system command, THE ControlPython process SHALL call `Py_Finalize()` and exit cleanly with exit code 0
5. IF a Python function raises an unhandled exception, THEN THE ControlPython process SHALL catch the exception at the call boundary, return the error via Protobuf, and continue processing subsequent requests without terminating
