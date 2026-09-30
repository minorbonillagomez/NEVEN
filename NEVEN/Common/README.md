# Common — Layer 1: Shared Services

Services shared across all components. All classes follow the **Singleton** or **pure-utility** pattern.

## Directory Structure

```
Common/
├── Security/          — Security & sandbox components
│   ├── InputSanitizer.cc/h
│   ├── SandboxVerifier.cc  (header in Include/)
│   └── SecurityService.cc/h
├── IPC/               — Inter-process communication
│   ├── pipe.cc/h
│   ├── message_utilities.cc/h
│   ├── REPLBridge.cc/h
│   ├── MessageValidator.cc/h
│   └── SafePipeHandle.cc/h
├── json11/            — JSON parsing library
├── (root)             — Config, Viewers, Startup, Diagnostics, Utilities
└── CMakeLists.txt
```

## Components

| Module | File | Responsibility |
|---|---|---|
| Security | `InputSanitizer` | Validates file paths and arguments against character allowlist |
| Security | `SandboxVerifier` | Blocks dangerous code patterns before execution |
| Security | `SecurityService` | SHA-256 integrity verification for user scripts |
| IPC | `pipe` | Named Pipe wrapper for bidirectional IPC with child processes |
| IPC | `message_utilities` | Protobuf frame/unframe utilities |
| IPC | `REPLBridge` | REPL-specific PostMessage bridge for WebView2 console |
| IPC | `MessageValidator` | Validates Protobuf frames before deserialization |
| IPC | `SafePipeHandle` | RAII wrapper for Windows HANDLE with atomic operations |
| Config | `ConfigService` | Reads and owns `neven-config.json`. Single source of truth. |
| Config | `EnvService` | Environment variable lookup with NEVEN_ > RJ2XCL_ > BERT_ priority |
| Viewers | `ViewerManager` | Manages WebView2 viewer instances |
| Viewers | `ViewerWindow` | Individual WebView2 window management |
| Startup | `NevenInitOrchestrator` | Coordinates startup sequence |
| Diagnostics | `DiagnosticRouter` | Routes diagnostic messages to console |
| Diagnostics | `LogService` | Structured logging via OutputDebugString and optional file sink |
| Discovery | `DiscoveryService` | Scans registry/filesystem for R/Julia installations |

## Key Contracts

- `ConfigService::Initialize()` must be called before any other service that reads config.
- `ConfigService::ReadJsonFile()` returns `Result<Json, FileError::ParseError>` on malformed JSON — callers must handle `Failure`.
- All IPC files are in `Common/IPC/` — include via `"pipe.h"`, `"message_utilities.h"`, etc.
- All security files are in `Common/Security/` — include via `"SecurityService.h"`, `"InputSanitizer.h"`, etc.

## Dependencies (Inward only)

```
Common → (none; standalone)
```
