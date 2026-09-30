# Ribbon — COM/Ribbon Integration

Implements the Excel Ribbon integration as a COM in-process server. Provides the custom toolbar buttons for the RJ2XCL add-in.

## Files

| File | Responsibility |
|---|---|
| `ribbon_connect.h` | Main COM interface implementing `IRibbonExtensibility` |
| `RJ2XCLRibbon_utf8.rc` | Ribbon XML resource (defines tabs, groups, buttons) |

## Ribbon → Engine Calls

Ribbon buttons invoke functions on the `RJ2XCL_Engine` singleton using the `RJ2XCL.` prefix:

```cpp
// e.g. for the Console button
Excel12(xlcRun, 0, 1, &RJ2XCL_TempStr12(L"RJ2XCL.Console"));
```

> **Note**: The prefix must be `RJ2XCL.` — this was corrected from an earlier `RJ.` bug (Sprint 1, H6).

## COM Threading

The Ribbon object is created on the apartment thread (STA). All callbacks from the Ribbon run on the Excel main thread. Do not call `LanguageService::Call()` directly from Ribbon handlers; use `xlcRun` to dispatch to the registered XLL functions instead.

## Dependencies

```
Ribbon → RJ2XCL Core (RJ2XCL_Engine singleton), COM (ATL-free manual vtable)
```
