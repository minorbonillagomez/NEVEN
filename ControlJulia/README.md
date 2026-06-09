# ControlJulia — Layer 3: Julia Engine Process

A standalone **Windows executable** (`controljulia.exe`) that hosts the Julia interpreter and communicates with the RJ2XCL core via Named Pipes.

## Architecture

```
Excel (RJ2XCL.dll) ──pipe──► ControlJulia.exe ──embed──► libjulia
```

## Key Initialization (`julia_interface.cc`)

Julia startup reads config from `rj2xcl-config.json` → `RJ2XCL.J`:

| Key | Purpose |
|---|---|
| `home` | Override Julia installation path |
| `usePrecompiled` | `"yes"` / `"no"` — controls `jl_options.use_precompiled` |
| `useCompileCache` | `"yes"` / `"no"` |
| `fastMath` | `"on"` / `"off"` / `"default"` |
| `minMajor`, `minMinor`, `maxMajor` | Version gate (same pattern as ControlR H1) |

## Type Mapping

| Julia Type | Protobuf Variable |
|---|---|
| `Float64` | `Variable::kReal` |
| `Int64` | `Variable::kInteger` |
| `String` | `Variable::kStr` |
| `Bool` | `Variable::kBoolean` |
| `Array` | `Variable::kArr` (rows/cols preserved) |
| `Ptr` | `Variable::kComPointer` |

## Dependencies

```
ControlJulia → libjulia, Common (windows_api_functions, result.h, json11)
```
