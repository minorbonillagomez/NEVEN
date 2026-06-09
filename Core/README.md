# RJ2XCL Core — Layer 2: Excel Engine

The main XLL (Excel Add-In) engine. Loaded by Excel as a DLL; implements the `xlAutoOpen`/`xlAutoClose` entrypoints.

## Responsibilities

- **Function Registration**: `excel_api_functions.cc` registers all `RJ2XCL.*` functions with Excel via `xlfRegister`.
- **IPC Orchestration**: `LanguageService` opens Named Pipes to ControlR and ControlJulia child processes.
- **Type Bridge**: `type_conversions.h` maps between Excel's `XLOPER12` and Protobuf `Variable` messages.
- **Callback Dispatch**: `CallbackDispatcher` shuttles Excel COM callbacks back from R/Julia threads.
- **Graphics**: `GraphicsHandler` handles `RJ2XCLGraphics` shape updates from R/Julia.
- **Ribbon**: `ribbon_connect.h` implements the COM ribbon integration.

## Key Files

| File | Purpose |
|---|---|
| `src/rj2xcl.cc` | `xlAutoOpen` / `xlAutoClose` — add-in lifecycle |
| `src/language_service.cc` | Named Pipe I/O and child process comms (`buffer_` is now a dynamic `vector<char>`) |
| `include/basic_functions.h` | `funcTemplates[]` — Excel function metadata |
| `include/type_conversions.h` | Thread-safe `WideStringToUtf8`, `XLOPERToVariable` |
| `include/language_service.h` | `LanguageService` base class |

## Buffer Design (H5)

`LanguageService::buffer_` starts at **8KB** and doubles on `ERROR_MORE_DATA` up to **256KB**. This allows DataFrames and large R objects to be transferred without truncation.

## Dependencies

```
RJ2XCL Core → Common (ConfigService, WindowManager, DiscoveryService, SecurityService)
```
