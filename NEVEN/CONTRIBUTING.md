# Contributing to NEVEN

Thank you for your interest in contributing to **NEVEN** (formerly RJ2XCL)! This project is developed as part of a doctoral research effort to democratize advanced scientific computing for everyday Excel users. Every contribution -- from bug fixes to documentation improvements -- helps achieve that goal.

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Development Environment Setup](#development-environment-setup)
3.  [Building from Source](#building-from-source)
4.  [Running Tests](#running-tests)
5.  [Coding Standards](#coding-standards)
6.  [How to Contribute](#how-to-contribute)
7.  [Good First Issues](#good-first-issues)
8.  [Reporting Bugs](#reporting-bugs)
9.  [Proposing Features](#proposing-features)

------------------------------------------------------------------------

## Project Overview {#project-overview}

NEVEN is a C++17 Excel add-in that bridges Microsoft Excel with the R (4.4.1) and Julia (1.12.6) programming languages. It enables 50+ statistical functions, interactive graphics (Plotly, D3.js, Sankey), and arbitrary code execution from Excel cells with sandbox security.

**Current quality score: 8.5/10** -- 119 unit tests, 30+ security patterns, centralized config.

Architecture follows a 3-layer process-isolated design:

- **XLL (NEVEN64.xll):** Excel integration, function registration, sandbox, type conversion
- **ControlR.exe:** Embedded R 4.4.1 runtime, communicates via Named Pipes + Protobuf
- **ControlJulia.exe:** Embedded Julia 1.12.6 runtime, same IPC protocol

See [Estado de las Cosas](docs/ESTADO_DE_LAS_COSAS.md) for the full project status.

------------------------------------------------------------------------

## Development Environment Setup {#development-environment-setup}

### Prerequisites

| Tool          | Version | Notes                                     |
|---------------|---------|-------------------------------------------|
| Visual Studio | 2022    | C++ Desktop Development workload required |
| CMake         | 3.15+   | Add to PATH                               |
| PowerShell    | 5.1+    | Included in Windows 10/11                 |
| R             | 4.0+    | Runtime only -- not needed to compile     |
| Julia         | 1.6+    | Runtime only -- not needed to compile     |

### Initial Setup

``` powershell
# 1. Clone the repository
git clone https://github.com/mboni/RJ2XCL.git
cd RJ2XCL

# 2. Build + run tests
.\build.ps1 -Test

# 3. (Optional) Build the Ribbon COM DLL separately
.\scripts\build-ribbon.ps1
```

> **No R or Julia installation is needed to compile.** The project uses mock headers in `include/` that declare all required interfaces without implementation. Real R and Julia are only needed at runtime.

------------------------------------------------------------------------

## Building from Source {#building-from-source}

``` powershell
# Standard Release build
.\build.ps1

# Debug build with tests
.\build.ps1 -Config Debug -Test

# Full pipeline: clean -> build -> test -> package
.\build.ps1 -Clean -Test -Package
```

### Build Outputs

| Artifact           | Location                           |
|--------------------|------------------------------------|
| `NEVEN.dll`        | `build_new/RJ2XCL/RJ2XCL/Release/` |
| `NEVEN64.xll`      | `build_new/Dist/`                  |
| `rj2xcl_tests.exe` | `build_new/tests/Release/`         |

------------------------------------------------------------------------

## Running Tests {#running-tests}

``` cmd
:: In Developer Command Prompt for VS 2022
cd build_new
cmake --build . --config Release --target rj2xcl_tests
.\tests\Release\rj2xcl_tests.exe
```

Expected: **119 tests from 18 test suites -- 119 passing, 0 failed**

Or run specific suites:

```cmd
.\tests\Release\rj2xcl_tests.exe --gtest_filter="Sandbox*"
.\tests\Release\rj2xcl_tests.exe --gtest_filter="ConfigGetters*:ConfigJson*:ConfigPath*"
```

### Test Coverage Areas

| Test File | Tests | What it Tests |
|---|---:|---|
| `sandbox_tests.cc` | 63 | Sandbox patterns (R + Julia), bypass prevention, allowed operations |
| `config_service_tests.cc` | 11 | Config getters, defaults, JSON parsing, path validation |
| `security_tests.cc` | 4 | SHA-256 integrity verification of scripts |
| `raii_xloper_tests.cc` | 4 | RAII memory management, move semantics, xlFree |
| `type_conversion_tests.cc` | 3 | XLOPER12 <-> Protobuf, UTF-8, thread safety |
| `basic_functions_tests.cc` | 4 | Version, bounds checking, input validation |
| `callback_dispatcher_tests.cc` | 2 | Callback routing between Excel and engines |
| `discovery_tests.cc` | 4 | R/Julia environment auto-discovery |
| `common_tests.cc` | 12 | Result<T,E>, ConfigService, version checks, logging |
| `com_object_map_tests.cc` | 3 | COM pointer management |
| `language_service_tests.cc` | 2 | File validation, string interpolation |
| `callback_behavior_tests.cc` | 2 | Registration tracking, COM routing |
| `integration_tests.cc` | 1 | Full Named Pipe lifecycle with mock engine |

### Adding a New Test

1.  Create (or edit) a `*_tests.cc` file in `tests/`
2.  Add the file to `tests/CMakeLists.txt`
3.  Use `MockExcelBridge` to simulate the Excel API without opening Excel
4.  Follow the existing test structure using Google Test (`TEST_F`, `EXPECT_*`)
5.  Run `.\tests\Release\rj2xcl_tests.exe` to verify all 119+ tests pass

**Example -- adding a sandbox test:**

```cpp
TEST_F(SandboxTest, R_BlocksMyNewPattern) {
    EXPECT_TRUE(IsBlocked("dangerous_function('arg')"));
}

TEST_F(SandboxTest, R_AllowsMyLegitFunction) {
    EXPECT_TRUE(IsAllowed("safe_function(1, 2, 3)"));
}
```

------------------------------------------------------------------------

## Coding Standards {#coding-standards}

Please read [`docs/sops/coding-standards.md`](docs/sops/coding-standards.md) before submitting code. Key rules:

| Element | Convention | Example |
|----|----|----|
| Classes | `PascalCase` | `class LanguageManager` |
| Functions/variables | `snake_case` | `void register_functions()` |
| Class members | `snake_case_` | `int next_id_` |
| Constants / Macros | `SCREAMING_SNAKE_CASE` | `MAX_BUFFER_SIZE` |
| File extensions | `.cc` for C++, `.h` for headers | `pipe.cc` |

**Error handling:** Use `Result<T, E>` from `Common/result.h` instead of raw booleans or exceptions. See [`docs/sops/error-handling.md`](docs/sops/error-handling.md).

**Memory management:** Always use `std::unique_ptr` / `std::shared_ptr`. Never use raw `new`/`delete`. For Excel types use `RaiiXlOper`.

------------------------------------------------------------------------

## How to Contribute {#how-to-contribute}

1.  **Fork** the repository
2.  **Create a branch** from `main`: `git checkout -b feat/my-feature`
3.  **Make your changes**, ensuring all existing tests still pass
4.  **Add tests** for any new functionality
5.  **Submit a Pull Request** against `main` using the PR template

### PR Checklist

- [ ] Code follows the naming conventions in `coding-standards.md`
- [ ] New code uses `Result<T,E>` for error handling
- [ ] All new public functions have Doxygen comments
- [ ] `.\build.ps1 -Test` passes without errors
- [ ] No raw `new`/`delete` in C++ code
- [ ] GPL v3 copyright header added to any new source files

------------------------------------------------------------------------

## Good First Issues {#good-first-issues}

New to the project? Here are some self-contained tasks to get started:

- **Tests:** Write unit tests for `AutoLoader` or `EnvService` (currently untested)
- **Documentation:** Add `@brief` comments to functions in `ControlJulia/` that lack them
- **Security:** Add new sandbox patterns for R/Julia functions you consider dangerous
- **Examples:** Add a new example `.R` or `.jl` script to `Documents\NEVEN\functions\`
- **Bug fix:** Migrate `std::cout` in `ControlJulia/src/` to `CHILD_LOG` macros (see `child_log.h`)
- **Functions:** Port a new statistical function from R to the R4XCL library

------------------------------------------------------------------------

## Reporting Bugs {#reporting-bugs}

Use the [Bug Report issue template](.github/ISSUE_TEMPLATE/bug_report.md). Please include:
- NEVEN version
- Windows version and Excel version (32-bit or 64-bit)
- R/Julia version (if relevant)
- Steps to reproduce
- Expected vs. actual behavior
- Relevant log output from `neven.log`

------------------------------------------------------------------------

## Proposing Features {#proposing-features}

Open a [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) describing:
- The problem you want to solve
- Your proposed solution
- Alternatives you considered

------------------------------------------------------------------------

## License

By contributing to NEVEN, you agree that your contributions will be licensed under the **GNU General Public License v3.0**. See [LICENSE](Install/license.txt) for details.
