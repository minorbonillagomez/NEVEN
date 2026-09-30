# Changelog

All notable changes to NEVEN (formerly RJ2XCL) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **Console/ (Electron REPL) eliminated** — The Electron 1.8.2 REPL application has been
  completely removed from the repository. It carried 50+ CVEs, 5 XSS vulnerabilities,
  and was fully replaced by the WebView2-based REPL (REPLManager + REPLBridge) which
  runs in-process without a separate Electron child process. This closes audit findings
  SEC-CRI-007, SEC-CRI-008, SEC-ALT-001 through SEC-ALT-003, SEC-ALT-006, SEC-MED-004,
  SEC-MED-005, and SEC-INF-002.

### Added
- **Security remediation** — Comprehensive security hardening addressing 36 audit findings:
  - InputSanitizer: character allowlist validation for all CreateProcess paths
  - SandboxVerifier: extended R/Julia blocklists, REPL + AutoLoader enforcement
  - MessageValidator: Protobuf frame validation before deserialization
  - SafePipeHandle: RAII wrapper with atomic read/write (TOCTOU prevention)
  - MSVC security flags: /GS, /guard:cf, /sdl, /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT
  - GitHub Actions: permissions restricted to contents: read
  - .gitignore: comprehensive exclusion patterns for sensitive files
  - GetNevenEnvVar: NEVEN_ > RJ2XCL_ > BERT_ priority lookup
  - eval(parse()) eliminated from all R library files
  - Dead code removed (julia-0.7.ts, __pycache__, duplicate .neven_webview_dir)
  - Common/ reorganized into Security/ and IPC/ subdirectories
  - Doxygen documentation added to all public headers
  - docs/NAMING.md documenting NEVEN/RJ2XCL/BERT relationship

### Changed
- **Project renamed from RJ2XCL to NEVEN** -- All user-visible names, binaries, config files,
  environment variables, and documentation now use the NEVEN identity.
  Internal C++ symbols (RJ_ prefix) remain unchanged for ABI compatibility.
  - Excel functions: `RJ2XCL.VIEW(...)` -> `NEVEN.v(...)`, `RJ2XCL.R(...)` -> `NEVEN.r(...)`, etc.
  - Binaries: `RJ2XCL64.xll` -> `NEVEN64.xll`, `RJ2XCLRibbon.dll` -> `NEVENRibbon.dll`
  - Config: `rj2xcl-config.json` -> `neven-config.json`, `rj2xcl-languages.json` -> `neven-languages.json`
  - Log: `rj2xcl.log` -> `neven.log`
  - Environment variable: `RJ2XCL_HOME` -> `NEVEN_HOME`
  - Registry key: `RJ2XCL.DevOptions` -> `NEVEN.DevOptions`
  - COM ProgID: `RJ2XCLRibbon.Connect` -> `NEVENRibbon.Connect`
  - Deploy directory: `C:\RJ2XCL\` -> `C:\NEVEN\`
  - Ribbon tab label: "RJ2XCL" -> "NEVEN"
  - R startup environment: `RJ2XCL` -> `NEVEN`
  - Julia module: `module RJ2XCL` -> `module NEVEN` (alias `RJ` kept)
  - Function category in Excel Function Wizard: "RJ2XCL" -> "NEVEN"

### Added
- `CONTRIBUTING.md` -- Contributor guide for open-source collaboration
- `CODE_OF_CONDUCT.md` -- Contributor Covenant v2.1
- `CHANGELOG.md` -- This file
- GitHub Actions CI/CD pipeline (build + test on every push)
- Issue and Pull Request templates
- `Doxyfile` -- API documentation generation via Doxygen
- `docs/sops/architecture-overview.md` -- Consolidated English architecture reference
- `docs/sops/testing-guide.md` -- How to write and run tests
- `docs/UAT_Report.md` -- User Acceptance Testing protocol and results template
- `scripts/build-ribbon.ps1` -- Standalone MSBuild script for Ribbon COM DLL
- `scripts/generate-docs.ps1` -- Doxygen documentation generator
- `scripts/add-license-headers.ps1` -- GPL v3 header injection tool
- `Addin/CMakeLists.txt` -- XLL packaging integrated into CMake build

### Changed
- **GoogleTest pinned** to v1.14.0 (was `heads/main` -- non-reproducible)
- **`build.ps1`** -- Added `-Test` and `-Package` flags, improved error reporting
- **`README.md`** -- Bilingual (EN/ES), removed dead wiki links, added project status
- **`UserGuide.md`** -- Expanded from 47 to ~300 lines with full installation guide
- **`error-handling.md`** -- Status changed from "Propuesto" to "Vigente"
- **`Install/README.md`** -- Documented the installer pipeline and payload contents
- **`rj2xcl.h`** -- Removed legacy commented-out code blocks
- Standardized file extensions: `.cpp` -> `.cc` in `Common/` module

### Fixed
- Dead links in README.md pointing to non-existent wiki pages
- Inconsistent naming conventions between documented standards and actual code

---

## [2.0.0] -- 2026-03

### Added
- **Julia integration** -- Full support for Julia 1.x as a second scripting engine
- **RAII memory management** -- `RaiiXlOper` class for deterministic XLOPER12 lifecycle
- **Result\<T,E\> pattern** -- Deterministic error handling replacing exceptions
- **CMake build system** -- Migrated from MSBuild/VS solutions to CMake 3.15+
- **Protocol Buffers v21.12** -- Upgraded from v3.5.0, auto-fetched via FetchContent
- **Mock headers** -- R, Julia, and Excel SDK mocks for compilation without runtime deps
- **ConfigService** -- JSON-based configuration with graceful fallback
- **DiscoveryService** -- Automatic detection of R/Julia installations via Registry
- **SecurityService** -- SHA-256 script integrity verification
- **LogService** -- Structured logging to file and console
- **LanguageManager** -- Dynamic registry for R/Julia engine services
- **CallbackDispatcher** -- Centralized Command Dispatcher for cross-language callbacks
- **RibbonService** -- COM-based Excel Ribbon management
- **FileWatchService** -- Hot-reload of user scripts on file change
- **AutoLoader** -- Automatic sourcing of `.R` and `.jl` scripts from user directory
- **GCMonitor** -- Coordinated garbage collection across R/Julia/COM
- **SandboxVerifier** -- Malicious script pattern detection
- **Google Test suite** -- 7 test files covering RAII, security, discovery, callbacks
- **One-click installer** -- C# WinForms installer with optional R/Julia download
- **Excel Ribbon** -- Custom tab with Console, Reload, Install, Settings buttons

### Changed
- Renamed from "BERT Toolkit" to "RJ2XCL" (later renamed to "NEVEN")
- R support updated from 3.4.x to 4.x+
- C++ standard updated from C++11 to C++17
- Function prefixes changed to `NEVEN.r.*` and `NEVEN.j.*`
- COM type libraries pre-generated and embedded (`OfficeTypes/`)

---

## [1.0.0] -- 2018

### Added
- Original BERT Toolkit by Structured Data, LLC
- R integration for Excel via XLL add-in
- Basic Julia support (Julia 0.6.2)
- Console REPL (Electron-based)
- COM automation from R
- MSBuild-based build system

---

[Unreleased]: https://github.com/mboni/RJ2XCL/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/mboni/RJ2XCL/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/mboni/RJ2XCL/releases/tag/v1.0.0
