# Implementation Plan: NEVEN Installer

## Overview

Build a single PowerShell script `Install-NEVEN.ps1` (~400-500 lines) that automates the full deployment of the NEVEN Excel add-in on Windows 10+ (64-bit). The script executes six sequential phases: pre-flight checks, user choices, file deployment, registration, user setup, and verification. A companion `Uninstall-NEVEN.ps1` is generated during installation.

All functions use PowerShell 5.1-compatible syntax only. No external module dependencies.

## Tasks

- [x] 1. Create script skeleton with parameters, logging, and execution flow
  - [x] 1.1 Create `NEVEN/Install/Install-NEVEN.ps1` with the script header, `param()` block (`$InstallDir`, `$DistDir`, `$Silent`), `$ErrorActionPreference = 'Continue'`, and `$script:LogFile` variable
    - Define the `Write-Log` function with `$Message` and `$Level` parameters (INFO/WARN/ERROR)
    - Write-Log appends `[timestamp] LEVEL Message` to `$script:LogFile` and writes to host with color coding (White/Yellow/Red)
    - Add the log file header block (banner with start time)
    - Add placeholder comments for each of the six phases in the main execution flow
    - _Requirements: 14.1, 14.2, 15.5_

- [x] 2. Implement Phase 1 — Pre-flight check functions
  - [x] 2.1 Implement `Test-WindowsVersion` and `Test-PowerShellVersion`
    - `Test-WindowsVersion` returns `$true` if Windows 10+ (build >= 10240) and 64-bit via `[Environment]::Is64BitOperatingSystem` and `[Environment]::OSVersion.Version.Build`
    - `Test-PowerShellVersion` returns `$true` if `$PSVersionTable.PSVersion >= 5.1`
    - Both log their result via Write-Log
    - Wire into main flow: if either returns `$false`, display error and `exit 1`
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 2.2 Implement `Find-R`, `Find-Julia`, and `Find-Python`
    - `Find-R`: search registry (`HKLM:\SOFTWARE\R-core\R`), PATH (`Rscript.exe`), filesystem (`C:\Program Files\R\R-*`); extract version via `Rscript.exe --version`; return `[PSCustomObject]@{ Found; Path; Version; Adequate }` where Adequate = version >= 4.4.1
    - `Find-Julia`: search PATH (`julia.exe`), filesystem (`$env:LOCALAPPDATA\Programs\Julia-*`); extract version via `julia.exe --version`; return same shape; Adequate = version >= 1.12.6
    - `Find-Python`: search PATH (`python.exe`), registry (`HKLM:\SOFTWARE\Python\PythonCore`), filesystem (`$env:LOCALAPPDATA\Programs\Python\Python3*`); extract version via `python.exe --version`; Adequate = version >= 3.10
    - Log each detection result
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11_

  - [x] 2.3 Implement `Find-ExcelVersions` and `Find-ExistingInstall`
    - `Find-ExcelVersions`: scan `HKCU:\Software\Microsoft\Office\{15.0,16.0}\Excel\Options`; return array of version strings found
    - `Find-ExistingInstall`: check if `$TargetPath` exists and contains `NEVEN64.xll`; return `[PSCustomObject]@{ Found; Path; HasConfig }`
    - _Requirements: 4.3, 12.1_

  - [x] 2.4 Implement `Show-PreflightSummary`
    - Display formatted summary table with color-coded status: ✓ Green (found and adequate), ⚠ Yellow (found but old, or optional and missing), ✗ Red (required and missing)
    - Show download URLs for missing runtimes (R: `https://cran.r-project.org/bin/windows/base/`, Julia: `https://julialang.org/downloads/`, Python: `https://www.python.org/downloads/`)
    - _Requirements: 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 2.1, 2.3, 2.4_

  - [ ]* 2.5 Write property test for language detection (Property 1)
    - **Property 1: Language detection finds runtimes present on the system**
    - Generate 100+ random combinations of registry entries, PATH entries, and filesystem paths; verify `Find-R`, `Find-Julia`, `Find-Python` return `Found=$true` when runtime is present and `Found=$false` when absent
    - Test file: `NEVEN/Install/Tests/Find-Language.Tests.ps1`
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [ ]* 2.6 Write property test for version parsing (Property 2)
    - **Property 2: Round trip consistency of version string parsing**
    - Generate 100+ random valid version output strings in R/Julia/Python formats; verify extracted `[major, minor, patch]` tuple matches embedded numbers and `Adequate` flag is correct relative to minimum versions
    - Test file: `NEVEN/Install/Tests/Parse-Version.Tests.ps1`
    - **Validates: Requirements 1.4, 1.5, 1.6, 1.8, 1.10**

- [x] 3. Implement Phase 2 — User choices function
  - [x] 3.1 Implement `Get-UserChoices`
    - Prompt for installation directory (default `C:\NEVEN\`) via `Read-Host`
    - If R not found: prompt to continue without R (y/n)
    - If R found: prompt to install R packages (y/n, default y)
    - Prompt for desktop shortcut (y/n, default y)
    - If existing install found: prompt to update/reinstall (y/n)
    - Return `[PSCustomObject]@{ InstallDir; ContinueWithoutR; InstallRPackages; CreateShortcut; IsUpdate }`
    - If `$Silent` switch is set, use defaults without prompting
    - _Requirements: 2.2, 2.5, 3.1, 9.1, 10.1, 12.1_

- [x] 4. Checkpoint — Verify pre-flight and user choices
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Phase 3 — File deployment function
  - [x] 5.1 Implement `Install-NEVENFiles`
    - Create `$InstallDir` if not exists
    - If `$IsUpdate` and `neven-config.json` exists, back up to `neven-config.json.bak` (byte-identical copy)
    - Copy critical files from `$DistDir`: `NEVEN64.xll`, `ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe`, `NEVENRibbon.dll`, `neven-config.json`, `neven-languages.json`
    - Create `startup/` subdirectory, copy `startup.r`, `startup.jl`, `startup.py`
    - Create `examples/` subdirectory, copy all files from `Dist/examples/`
    - Log each file copy; on individual failure log ERROR and set `$script:HasWarnings`, continue with remaining files
    - Return `$true` if critical file `NEVEN64.xll` was copied successfully
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 12.2_

  - [ ]* 5.2 Write property test for config backup preservation (Property 6)
    - **Property 6: Config backup preserves original content on update**
    - Generate 100+ random JSON config contents; run backup logic; verify `.bak` file is byte-identical to original
    - Test file: `NEVEN/Install/Tests/ConfigBackup.Tests.ps1`
    - **Validates: Requirements 12.2**

  - [ ]* 5.3 Write property test for error resilience (Property 5)
    - **Property 5: Non-critical failures do not halt installation**
    - Inject random failures into file copy sequences (100+ combinations); verify installer logs each failure and attempts all remaining operations
    - Test file: `NEVEN/Install/Tests/ErrorResilience.Tests.ps1`
    - **Validates: Requirements 3.7, 9.5**

- [x] 6. Implement Phase 4 — Registration functions
  - [x] 6.1 Implement `Register-XLL` and `Unregister-XLL`
    - `Register-XLL`: for each Excel version, open `HKCU:\Software\Microsoft\Office\$ver\Excel\Options`; scan existing `OPEN`/`OPEN1`/`OPEN2`... values; if existing NEVEN entry found, update path; if no entry, find next available `OPENn` key and set value to `/R "$XllPath"`; return `$true` if at least one version registered
    - `Unregister-XLL`: remove NEVEN XLL entries from all Excel version registry keys
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 12.4_

  - [x] 6.2 Implement `Register-RibbonCOM` and `Unregister-RibbonCOM`
    - `Register-RibbonCOM`: run `regsvr32 /s "$DllPath"` via `Start-Process -Wait -PassThru`; if exit code != 0, offer elevation via `Start-Process -Verb RunAs`; on success create Ribbon registry key (`FriendlyName=NEVEN`, `Description=NEVEN Ribbon Menu`, `LoadBehavior=3`); return `$true` if succeeded
    - `Unregister-RibbonCOM`: run `regsvr32 /u /s "$DllPath"` and remove Ribbon registry key
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 12.5, 13.2_

  - [x] 6.3 Implement `New-QuartoJunction`
    - Check if `C:\Program Files\Quarto\` exists; if not, skip and log
    - If `C:\Quarto` already exists, verify target and log "already configured"
    - Otherwise run `cmd /c mklink /J C:\Quarto "C:\Program Files\Quarto"`
    - If fails (access denied), offer elevation via `Start-Process -Verb RunAs`; if declined, log warning with manual command
    - Return `$true` if junction exists and is correct after operation
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 13.3_

  - [ ]* 6.4 Write property test for XLL registration idempotency (Property 3)
    - **Property 3: XLL registration is idempotent — no duplicate entries**
    - Generate 100+ random initial OPEN key states (0-10 existing entries, with/without prior NEVEN entry); run `Register-XLL` twice; verify exactly one NEVEN entry exists after each run
    - Test file: `NEVEN/Install/Tests/Register-XLL.Tests.ps1`
    - **Validates: Requirements 4.1, 4.2, 12.4**

- [x] 7. Implement Phase 5 — User setup functions
  - [x] 7.1 Implement `Initialize-UserDirectories` and `Copy-ExampleFiles`
    - `Initialize-UserDirectories`: create `$env:USERPROFILE\Documents\NEVEN\functions\` and `$env:USERPROFILE\Documents\NEVEN\graphics\`; if already exist, log "already present" and preserve contents
    - `Copy-ExampleFiles`: copy `.r`, `.jl`, `.py` files from `$SourceExamplesDir` to `$TargetFunctionsDir`; if file already exists in target, skip and log "preserved existing"
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4_

  - [x] 7.2 Implement `Install-RPackages`
    - Invoke `Rscript.exe` to install packages in two batches:
      - Batch 1 (base): `stargazer`, `svDialogs`, `lmtest`, `sandwich`, `margins`, `plm`, `rpart`, `rpart.plot`, `PerformanceAnalytics`, `tseries`, `mFilter`, `e1071`, `wooldridge`, `lme4`, `survival`, `psych`, `car`, `Hmisc`, `forecast`
      - Batch 2 (visualization): `plotly`, `htmlwidgets`, `ggplot2`, `corrplot`
    - Display progress for each batch; log failures per-package and continue
    - Return `$true` if `Rscript.exe` executed without fatal error
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 7.3 Implement `New-DesktopShortcut`
    - Create `.lnk` file on Desktop using `WScript.Shell` COM object; target = Excel.exe (from registry or default); arguments = `/r "$XllPath"`; icon = NEVEN icon if available, else Excel default
    - If shortcut already exists, update target path
    - _Requirements: 10.2, 10.3, 10.4_

  - [ ]* 7.4 Write property test for user file preservation (Property 4)
    - **Property 4: User files are preserved across installation and update**
    - Generate 100+ random sets of pre-existing files with random content in user directories; run installer logic; verify no files were deleted, modified, or overwritten
    - Test file: `NEVEN/Install/Tests/UserFiles.Tests.ps1`
    - **Validates: Requirements 6.3, 6.4, 7.4, 12.3**

- [x] 8. Checkpoint — Verify phases 3-5
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement Phase 6 — Verification and uninstaller
  - [x] 9.1 Implement `Test-Installation` and `Show-InstallationResult`
    - `Test-Installation`: verify NEVEN64.xll exists, ControlR.exe exists, neven-config.json exists, XLL registered in Excel registry (at least one version), User_Functions_Dir exists; return `[PSCustomObject]@{ AllPassed; Results[] }`
    - `Show-InstallationResult`: if all passed, display green success message with test instruction `=NEVEN.R("1+1")`; if some failed, display yellow warning listing failed checks and point to install.log
    - _Requirements: 14.3, 14.4, 14.5_

  - [ ]* 9.2 Write property test for verification reporting (Property 7)
    - **Property 7: Verification reports all failures**
    - Generate 100+ random pass/fail combinations for the 5 verification checks; verify warning message lists every failed check and count matches actual failures
    - Test file: `NEVEN/Install/Tests/Verification.Tests.ps1`
    - **Validates: Requirements 14.3, 14.5**

  - [x] 9.3 Implement `New-Uninstaller` function and generate `Uninstall-NEVEN.ps1`
    - `New-Uninstaller` writes `Uninstall-NEVEN.ps1` to `$InstallDir` containing:
      - Confirmation prompt
      - Excel running check (prompt to close)
      - `regsvr32 /u /s` for NEVENRibbon.dll
      - XLL registry removal for all detected Excel versions (inline `Unregister-XLL` logic)
      - Ribbon registry key removal
      - Prompt to delete user scripts (`Documents\NEVEN\`)
      - Quarto junction removal if created by installer
      - NEVEN_Home directory removal
      - Desktop shortcut removal
      - Summary of removed components
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 11.12, 11.13_

- [x] 10. Wire main execution flow and add log footer
  - [x] 10.1 Wire all phases together in the script entry point
    - Connect Phase 1 calls: `Test-WindowsVersion`, `Test-PowerShellVersion` (exit on fail), `Find-R`, `Find-Julia`, `Find-Python`, `Find-ExcelVersions`, `Find-ExistingInstall`, `Show-PreflightSummary`
    - Connect Phase 2: `Get-UserChoices`
    - Set `$script:LogFile` after install dir is confirmed; write log header
    - Connect Phase 3: `Install-NEVENFiles`; exit if critical file failed
    - Patch `neven-config.json` with detected R/Julia/Python paths
    - Connect Phase 4: `Register-XLL`, `Register-RibbonCOM`, `New-QuartoJunction`
    - Connect Phase 5: `Initialize-UserDirectories`, `Copy-ExampleFiles`, conditionally `Install-RPackages`, conditionally `New-DesktopShortcut`
    - Connect Phase 6: `Test-Installation`, `Show-InstallationResult`, `New-Uninstaller`
    - Write log footer (end time, duration)
    - Exit with code 0 (success) or 1 (critical failure)
    - _Requirements: 13.1, 13.4, 14.1, 14.2, 15.5_

- [x] 11. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The script targets PowerShell 5.1 — no PS 7+ features allowed
- All user interaction uses `Read-Host` and `Write-Host` (no GUI)
- The `Uninstall-NEVEN.ps1` is a standalone generated script (not dependent on `Install-NEVEN.ps1` at runtime)
