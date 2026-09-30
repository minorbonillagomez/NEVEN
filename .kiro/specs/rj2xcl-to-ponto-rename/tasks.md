# Implementation Plan: Rename RJ2XCL to NEVEN

## Overview

This plan implements the rename in two phases: Phase 1 updates all documentation (.md files), Phase 2 updates code files grouped by component. After both phases, we verify the build compiles and all 205 tests pass. Internal C++ names (RJ_ prefix) and short aliases (R., J.) do not change.

## Tasks

- [x] 1. Phase 1: Documentation updates
  - [x] 1.1 Update docs/*.md files
    - Replace all textual references to "RJ2XCL" with "NEVEN" in docs/ Markdown files
    - Update formula examples to new names (e.g., `=NEVEN.v(...)` instead of `=RJ2XCL.VIEW(...)`)
    - Update paths from `C:\RJ2XCL\` to `C:\NEVEN\`
    - Update config file references from `rj2xcl-config.json` to `neven-config.json`
    - Update binary names (NEVEN64.xll, NEVENRibbon.dll)
    - Avoid special characters that corrupt in UTF-8
    - _Requirements: 8.1, 8.2, 8.5, 8.6, 8.7, 8.8_

  - [x] 1.2 Update docs/docusaurus/*.md files (11 chapters)
    - Replace all references to "RJ2XCL" with "NEVEN" across all Docusaurus chapters
    - Update formula examples to new Nombre_Excel_Visible
    - Update architecture diagrams with new binary names
    - Update paths and config file references
    - Avoid special characters that corrupt in UTF-8
    - _Requirements: 8.3, 8.2, 8.5, 8.6, 8.7, 8.8_

  - [x] 1.3 Update Examples/EJEMPLOS_USUARIO.md
    - Replace all formula examples with new NEVEN prefixed names
    - Update any paths or config references
    - Add migration section listing old-to-new name mapping
    - _Requirements: 8.4, 11.2_

  - [x] 1.4 Update CHANGELOG.md and other root .md files
    - Update CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md if they reference RJ2XCL
    - Document the rename in CHANGELOG
    - _Requirements: 8.1_

- [x] 2. Checkpoint - Review documentation changes
  - Ensure all .md files are updated consistently, ask the user if questions arise.

- [x] 3. Phase 2: Code changes - XLL core (basic_functions)
  - [x] 3.1 Update basic_functions.h - funcTemplates array
    - Change column 3 (Nombre_Excel_Visible) for all rows: `RJ2XCL.VIEW` → `NEVEN.v`, `RJ2XCL.PLUTO.*` → `NEVEN.pluto.*`, etc. (full mapping in design)
    - Change column 6 (category) from `"RJ2XCL"` to `"NEVEN"` for all rows
    - Update help descriptions in columns 9+ that reference RJ2XCL
    - Do NOT change column 1 (internal C++ names like `RJ_View`)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 12.1_

  - [x] 3.2 Update basic_functions.h - callTemplates array
    - Change `RJ2XCL.Call` → `NEVEN.Call`, `RJ2XCL.Exec` → `NEVEN.Exec`
    - Change `RJ2XCL.R` → `NEVEN.r`, `RJ2XCL.J` → `NEVEN.j`
    - Update category from `"RJ2XCL"` to `"NEVEN"`
    - _Requirements: 1.7, 12.1_

  - [x] 3.3 Update basic_functions.cc - output strings
    - `RJ_About()`: Change `"RJ2XCL v2.0"` to `"NEVEN v2.0"`
    - `RJ_Help()`: Update all formula examples from `RJ2XCL.*` to `NEVEN.*`
    - `RJ_Version()`: Change `"RJ2XCL 2.0.0"` to `"NEVEN 2.0.0"`
    - `RJ_PlutoData()`: Change Julia code string `"RJ2XCL.set_data"` to `"NEVEN.set_data"`
    - _Requirements: 1.6, 2.3_

- [x] 4. Phase 2: Code changes - Ribbon COM Add-in
  - [x] 4.1 Update ribbon_ui.xml
    - Change `<tab id="TabRJ2XCL" label="RJ2XCL">` to `<tab id="TabNEVEN" label="NEVEN">`
    - Update supertip "Acerca de" from `"RJ2XCL v2.0..."` to `"NEVEN v2.0..."`
    - Update supertip "Config JSON" to reference `neven-config.json`
    - Update all other supertips referencing "RJ2XCL"
    - _Requirements: 2.1, 2.3, 2.7_

  - [x] 4.2 Update ribbon_connect.h
    - `GetLabel`: return `"NEVEN Console"` instead of `"RJ2XCL\u00a0Console"`
    - `RunXllFunction` calls: update to new names (e.g., `L"NEVEN.cmd.pluto.start"`)
    - `SetPointers()`: change module search from `"RJ2XCL"` to `"NEVEN"`
    - `OnOpenConfig`: path to `"C:\\NEVEN\\neven-config.json"`
    - `OnOpenScriptsDir`: path to `"C:\\NEVEN\\"`
    - `OnAbout`: call `NEVEN.about.dialog`
    - `DECLARE_REGISTRY_RESOURCEID`: change to `IDR_NEVENRIBBON`
    - MessageBox titles: `"RJ2XCL - ..."` to `"NEVEN - ..."`
    - `_Run2` calls: `L"RJ2XCL.R"` → `L"NEVEN.r"`, `L"RJ2XCL.J"` → `L"NEVEN.j"`
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 5.4_

  - [x] 4.3 Update Ribbon .rgs file
    - Change ProgID from `RJ2XCLRibbon.Connect` to `NEVENRibbon.Connect`
    - Update description references
    - _Requirements: 5.1, 5.2_

  - [x] 4.4 Update Ribbon resource.h
    - Change `IDR_RJ2XCLRIBBON` to `IDR_NEVENRIBBON`
    - _Requirements: 5.3_

  - [x] 4.5 Update Ribbon CMakeLists.txt
    - Change `project(RJ2XCLRibbon)` to `project(NEVENRibbon)`
    - Change target name from `RJ2XCLRibbon` to `NEVENRibbon`
    - Update IDL/TLB references: `RJ2XCLRibbon.idl/tlb` to `NEVENRibbon.idl/tlb`
    - Change `OUTPUT_NAME "RJ2XCLRibbon"` to `OUTPUT_NAME "NEVENRibbon"`
    - Update post-build copy: `RJ2XCLRibbon.dll` to `NEVENRibbon.dll`
    - _Requirements: 4.2, 4.3_

- [x] 5. Phase 2: Code changes - Services
  - [x] 5.1 Update ConfigService.cc
    - Change registry key `"RJ2XCL.DevOptions"` to `"NEVEN.DevOptions"`
    - Change env var `"RJ2XCL_HOME"` to `"NEVEN_HOME"`
    - Change config filename `"rj2xcl-config.json"` to `"neven-config.json"`
    - Change log warnings `"RJ2XCL home directory"` to `"NEVEN home directory"`
    - Change JSON root key `config_["RJ2XCL"]` to `config_["NEVEN"]`
    - _Requirements: 3.1, 3.3, 3.4_

  - [x] 5.2 Update rj2xcl.cc (singleton main)
    - Change log path from `"rj2xcl.log"` to `"neven.log"`
    - Change `xlAddInManagerInfo12` Pascal string `L"\006RJ2XCL"` to `L"\005NEVEN"`
    - Change log messages `"RJ2XCL: Engine::Init"` to `"NEVEN: Engine::Init"`
    - Change command line check `"/x:RJ2XCL"` to `"/x:NEVEN"`
    - Change MessageBox title `"RJ2XCL"` to `"NEVEN"`
    - Change language config filename if applicable: `"rj2xcl-languages.json"` to `"neven-languages.json"`
    - _Requirements: 6.1, 6.2, 3.2_

  - [x] 5.3 Update rj2xcl.def
    - Update `LIBRARY` directive if it references RJ2XCL
    - Update comments from `"RJ2XCL Project"` to `"NEVEN Project"`
    - Do NOT change any exported symbols (RJ_* names stay)
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 6. Phase 2: Code changes - Scripts
  - [x] 6.1 Update startup.r
    - Change `RJ2XCL <- new.env(...)` to `NEVEN <- new.env(...)`
    - Change all `RJ2XCL$` references to `NEVEN$`
    - Change `"rj2xcl_plot_"` to `"neven_plot_"`
    - Change `".rj2xcl.last.plot"` to `".neven.last.plot"`
    - Change `"RJ2XCL.last.plot"` to `"NEVEN.last.plot"`
    - Change `"RJ2XCL R startup complete"` to `"NEVEN R startup complete"`
    - Change graphics directory reference from `"RJ2XCL"` to `"NEVEN"`
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 6.2 Update startup.jl
    - Change `module RJ2XCL` to `module NEVEN`
    - Change `end # module RJ2XCL` to `end # module NEVEN`
    - Change `const RJ = RJ2XCL` to `const RJ = NEVEN` (keep alias RJ)
    - Change `"RJ2XCL_HOME"` to `"NEVEN_HOME"` in `set_data()`
    - Change `"C:\\RJ2XCL"` to `"C:\\NEVEN"` (fallback path)
    - Change docstrings `RJ2XCL.get_data` to `NEVEN.get_data`
    - Change `struct RJ2XCLDisplay` to `struct NEVENDisplay`
    - Change `RJ2XCLDisplay()` to `NEVENDisplay()`
    - _Requirements: 7.4, 7.5, 7.6_

- [x] 7. Phase 2: Code changes - Build system
  - [x] 7.1 Update root CMakeLists.txt
    - Change `project(RJ2XCL ...)` to `project(NEVEN ...)`
    - Change `option(RJ2XCL_ENABLE_PYTHON ...)` to `option(NEVEN_ENABLE_PYTHON ...)`
    - _Requirements: 4.3_

  - [x] 7.2 Update RJ2XCL/CMakeLists.txt (XLL subdirectory)
    - Change target name `RJ2XCL_Core` to `NEVEN_Core`
    - Change `OUTPUT_NAME "RJ2XCL64"` to `OUTPUT_NAME "NEVEN64"`
    - Update post-build copy: `RJ2XCL64.xll` to `NEVEN64.xll`
    - _Requirements: 4.1, 4.3_

- [x] 8. Checkpoint - Verify code changes compile
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Phase 2: Code changes - Tests
  - [x] 9.1 Update test files with new string references
    - Update all string assertions referencing "RJ2XCL" to "NEVEN"
    - Update paths `"C:\\RJ2XCL\\"` to `"C:\\NEVEN\\"`
    - Update function name references to new Nombre_Excel_Visible
    - Update config file references in tests
    - _Requirements: 9.2, 9.3, 9.4_

- [x] 10. Build verification
  - Run `cmake --build build_new --config Release --parallel`
  - Verify compilation succeeds with zero errors
  - Verify output binaries are named NEVEN64.xll and NEVENRibbon.dll
  - _Requirements: 4.1, 4.2, 9.1_

- [x] 11. Test verification
  - Run `build_new\tests\Release\rj2xcl_tests.exe`
  - Verify all 205 tests pass
  - If any test fails, fix the failing string references and re-run
  - _Requirements: 9.1_

- [x] 12. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Internal C++ names (RJ_ prefix) do NOT change — this preserves ABI compatibility
- Short aliases R. and J. do NOT change
- Repository directory names (RJ2XCL/) are NOT renamed in this phase
- The user always kills Excel/ControlR/ControlJulia processes before deploying
- Avoid Unicode special characters in documentation to prevent UTF-8 corruption
- Deploy target is C:\NEVEN\ (was C:\RJ2XCL\)
