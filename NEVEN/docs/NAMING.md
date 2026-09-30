# NEVEN Naming & Identity Guide

This document explains the relationship between the three names used throughout the project: **NEVEN**, **RJ2XCL**, and **BERT**. Understanding this history is essential for navigating the codebase without confusion.

## Historical Context

The project has gone through three naming phases:

1. **BERT** (Basic Excel R Toolkit) — the original project name when it only supported R integration with Excel. This name appears in legacy environment variables and some early documentation.

2. **RJ2XCL** (R Julia 2 Excel) — the internal C++ namespace and prefix adopted when Julia support was added. This became the canonical identifier in the compiled codebase: namespaces, class prefixes, DLL exports, and ABI symbols all use this prefix.

3. **NEVEN** — the current public-facing name used in all user-visible surfaces. This is the name users see in the Excel ribbon, documentation, configuration files, and function calls.

## When to Use Each Name

### NEVEN — User-Facing Contexts

Use **NEVEN** in anything a user sees or interacts with:

- Excel ribbon tab and UI elements
- User documentation and help text
- Configuration file names (`neven-config.json`)
- Excel worksheet functions (`=NEVEN.r()`, `=NEVEN.j()`)
- Installation directory (`C:\NEVEN\`)
- New environment variables (use `NEVEN_` prefix)
- Error messages shown to users
- README, CHANGELOG, and public-facing docs

### RJ2XCL — Internal C++ Code

Use **RJ2XCL** in the compiled C++ layer for ABI compatibility:

- C++ namespaces (`namespace rj2xcl { }`)
- Class name prefixes where historically established
- DLL export symbols (changing these would break binary compatibility)
- Protocol Buffers package name (`RJ2XCLBuffers`)
- Internal header guards and macros
- Build target names in CMake (e.g., `rj2xcl_tests`)
- Singleton instances (`RJ2XCL_Engine`)

> **Why not rename?** Renaming C++ symbols would break ABI compatibility with existing compiled add-ins, require coordinated updates across all DLL boundaries, and invalidate any external tools that reference exported symbols by name.

### BERT — Legacy Environment Variables Only

Use **BERT** only when maintaining backward compatibility with existing deployments:

- Legacy environment variables (`BERT_HOME`, `BERT_FUNCTIONS_DIRECTORY`, etc.)
- These are read as a last-resort fallback by `GetNevenEnvVar()`
- **Do not create new variables with the BERT_ prefix**

## Environment Variable Convention

New environment variables **must** use the `NEVEN_` prefix. The `GetNevenEnvVar()` function (declared in `Common/EnvService.h`) implements a priority-based fallback:

```
Priority: NEVEN_{name}  >  RJ2XCL_{name}  >  BERT_{name}  >  (empty string)
```

For example, calling `GetNevenEnvVar("HOME")` checks in order:
1. `NEVEN_HOME` — returns value if set
2. `RJ2XCL_HOME` — returns value if set
3. `BERT_HOME` — returns value if set
4. Returns empty string

This ensures new installations use the modern prefix while existing deployments continue to work without reconfiguration.

## Quick Reference Table

| Context | Name to Use | Example |
|---------|-------------|---------|
| Excel functions | NEVEN | `=NEVEN.r("summary(x)")` |
| Config files | NEVEN | `neven-config.json` |
| UI / Ribbon | NEVEN | "NEVEN" tab in Excel |
| Documentation | NEVEN | This file |
| C++ namespaces | rj2xcl | `namespace rj2xcl { }` |
| DLL exports | RJ2XCL | `RJ2XCL_Engine` singleton |
| Protobuf package | RJ2XCL | `RJ2XCLBuffers::Variable` |
| Test targets | rj2xcl | `rj2xcl_tests` |
| New env vars | NEVEN_ | `NEVEN_HOME` |
| Legacy env vars | BERT_ / RJ2XCL_ | `BERT_HOME` (read-only fallback) |
