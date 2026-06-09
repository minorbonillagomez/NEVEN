# Install Directory — RJ2XCL

This directory contains everything needed to build and distribute the RJ2XCL installer.

## Contents

| File/Directory | Description |
|---------------|-------------|
| `InstaladorRJ2XCL.cs` | C# WinForms installer source (single-file, self-contained) |
| `Desinstalador.cs` | C# uninstaller source |
| `RJ2XCL_Setup.exe` | Compiled installer executable |
| `RJ2XCL_Payload.zip` | Packaged payload (DLLs, configs, docs, examples) |
| `build-installer.ps1` | Script to compile the C# installer with CSC |
| `crear_instalador.ps1` | Script to create the full payload + installer package |
| `install-script.nsi` | NSIS installer script (alternative to C# installer) |
| `rj2xcl-config.json` | Default configuration template |
| `rj2xcl-languages.json` | Default language paths template |
| `rj2xcl.ico` | Application icon |
| `rj2xcl_logo.png` | Application logo |
| `license.txt` | GPL v3 full text |
| `_staging/` | Staging directory used during payload creation |
| `test_payload/` | Test payload for installer validation |
| `verify_payload/` | Payload verification scripts |

## How to Build the Installer

### Prerequisites
- .NET Framework SDK (csc.exe) — included with Visual Studio
- The main project must be compiled first: `.\build.ps1 -Package`
- (Optional) The Ribbon DLL: `.\scripts\build-ribbon.ps1`

### Step 1: Build the project
```powershell
# From the repository root
.\build.ps1 -Clean -Test -Package
.\scripts\build-ribbon.ps1
```

### Step 2: Create the payload
```powershell
# This creates RJ2XCL_Payload.zip with all necessary files
.\Install\crear_instalador.ps1
```

### Step 3: Compile the installer
```powershell
.\Install\build-installer.ps1
```

The output is `Install/RJ2XCL_Setup.exe`.

## What the Payload Contains

The `RJ2XCL_Payload.zip` is a self-contained archive with:
- `RJ2XCL.dll` — Core engine
- `RJ2XCL64.xll` — Excel add-in entry point
- `RJ2XCLRibbon2x64.dll` — Excel Ribbon COM component
- `rj2xcl-config.json` — Default configuration
- `rj2xcl-languages.json` — Language paths configuration
- `rj2xcl_logo.png` — Application logo
- `docs/` — User documentation
- `examples/` — Sample R and Julia scripts
- `console/` — Electron-based interactive console
- `Desinstalar.exe` — Uninstaller

## Publishing a Release

1. Ensure all tests pass: `.\build.ps1 -Clean -Test`
2. Update version number in:
   - `CMakeLists.txt` (project VERSION)
   - `RJ2XCL/include/rj2xcl_version.h`
   - `Install/InstaladorRJ2XCL.cs` (VERSION constant)
3. Build the installer: `.\Install\crear_instalador.ps1`
4. Test the installer on a clean Windows machine
5. Create a GitHub Release with the `RJ2XCL_Setup.exe`
6. Tag the commit: `git tag v2.0.0`

---
*Directory documentation v1.0.0*
