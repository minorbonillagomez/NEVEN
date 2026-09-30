# ControlR — Layer 3: R Engine Process

A standalone **Windows executable** (`controlr.exe`) that hosts the R interpreter and communicates with the RJ2XCL core via Named Pipes.

## Architecture

```
Excel (RJ2XCL.dll) ──pipe──► ControlR.exe ──embed──► R.dll (libR)
                                │
                        ManagementThread (break, shutdown)
```

## Key Design: `RControllerState` (H4)

All process-level state is encapsulated in the `RControllerState` struct (created in `main()`):

| Field | Type | Thread | Notes |
|---|---|---|---|
| `pipes` / `handles` | `vector<Pipe*>` / `vector<HANDLE>` | R main | Only accessed from `InputStreamRead` |
| `console_buffer` | `vector<string>` | R main | Queued messages when console not yet connected |
| `active_pipe` | `stack<int>` | R main | Tracks call depth for callbacks |
| `console_client` | `int` | R main | Index of connected console pipe |
| `user_break_flag` | `std::atomic<bool>` | **Cross-thread** | Set by `ManagementThread`, read by R callbacks |
| `language_tag` | `string` | Read-only | Set in `main()` before threads start |

## Version Compatibility (H1)

The version gate reads `minMajor`/`minMinor`/`maxMajor` from `rj2xcl-config.json`. Default: `R >= 3.5`. **R 4.x is fully supported**.

## Pipe Indices

| Index | Pipe | Purpose |
|---|---|---|
| `CALLBACK_INDEX` | `<name>-CB` | Synchronous callbacks from R → Excel |
| `PRIMARY_CLIENT_INDEX` | `<name>` | Main function calls Excel → R |

## Dependencies

```
ControlR → libR, Common (windows_api_functions, result.h, json11)
```
