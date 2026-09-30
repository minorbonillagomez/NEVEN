---
name: RJ2XCL Documentation
description: Generates human-readable documentation for the RJ2XCL project including maintenance guides, troubleshooting, and architecture references.
---

# RJ2XCL Documentation Skill

## Context
RJ2XCL is an Excel add-in that integrates R and Julia as scripting engines. It evolved from BERT Toolkit and is part of a Master's thesis in Applied Mathematics (Universidad de Costa Rica).

## Key Project Files
- `docs/ESTADO_DE_LAS_COSAS.md` — Current project status, changes log, and pending items
- `docs/ESTADO_DEL_ARTE.md` — Complete context: thesis, R4XCL library, migration plan
- `docs/SESION_2026-04-13.md` — Technical session notes with build commands and fixes

## Architecture Overview
- **RJ2XCL64.xll** — Excel add-in DLL loaded by Excel, registers functions via XLL API
- **ControlR.exe** — Separate process embedding R 4.4.1, communicates via Named Pipes + Protobuf
- **ControlJulia.exe** — Separate process embedding Julia (pending fix)
- **startup.r** — R initialization script with `BERT.graphics.device()` compatibility and `RJ2XCL$list.functions()`
- **rj2xcl-config.json** — Main configuration (R/Julia paths, options)
- **rj2xcl-languages.json** — Language service definitions (executables, arguments, extensions)

## Documentation Standards
When generating documentation for this project:

1. **Language**: Write in Spanish (the project team works in Spanish)
2. **Audience**: Assume the reader is a developer familiar with C++ and R but NOT with the XLL SDK or Named Pipes
3. **Structure**: Use clear sections with numbered steps for procedures
4. **Troubleshooting**: Always include common errors, their causes, and solutions
5. **Build commands**: Include exact commands for the Developer Command Prompt for VS 2022
6. **File paths**: Use Windows paths with backslashes
7. **Cross-references**: Link to other docs in the `docs/` folder when relevant

## Key Technical Details
- Build system: CMake 3.15+ with MSVC (VS 2022)
- R headers: Real R 4.4.1 headers with custom `Complex.h` for MSVC compatibility
- Excel API: `MdCallBack12` with corrected parameter order `(xlfn, count, opers[], operRes)`
- Pipe communication: Named Pipes with Protobuf serialization
- Function registration: `xlfRegister` with module path fallback via `GetModuleFileNameW`
- Graphics: PNG fallback via `BERT.graphics.device()` compatibility layer
