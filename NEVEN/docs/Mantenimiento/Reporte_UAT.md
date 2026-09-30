# User Acceptance Testing (UAT) Report — NEVEN 2.0

## Test Environment

| Item | Value |
|------|-------|
| **Date** | _YYYY-MM-DD_ |
| **Tester** | _Name_ |
| **Windows Version** | _e.g. Windows 11 23H2_ |
| **Excel Version** | _e.g. Microsoft 365, 64-bit_ |
| **R Version** | _e.g. R 4.4.0_ |
| **Julia Version** | _e.g. Julia 1.11.2_ |
| **NEVEN Build** | _e.g. Release 2.0.0, Build/Dist/NEVEN64.xll_ |

---

## Pre-conditions

- [ ] R is installed and accessible from PATH or detected by DiscoveryService
- [ ] Julia is installed and accessible from PATH or detected by DiscoveryService
- [ ] Excel is installed (64-bit recommended)
- [ ] NEVEN64.xll has been compiled via `.\build.ps1 -Package`
- [ ] NEVENRibbon2x64.dll has been compiled via `.\scripts\build-ribbon.ps1`
- [ ] Installer has been run OR manual registration has been performed

---

## Test Cases

### T-01: Add-in Loading

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | Open Excel | Excel opens without errors | ☐ | |
| 2 | Go to File --> Options --> Add-ins | NEVEN appears in the list | ☐ | |
| 3 | Verify the Ribbon tab | "NEVEN" tab is visible in the Ribbon | ☐ | |

### T-02: Version Function

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | In any cell, type `=NEVEN.Version()` | Returns version string (e.g., "2.0.0") | ☐ | |
| 2 | Verify no `#NAME?` error | Cell shows text, not an error | ☐ | |

### T-03: R Integration — Basic Function

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | Create file `Docs/NEVEN/functions/test.R` with: `mi_suma <- function(a, b) a + b` | File saved | ☐ | |
| 2 | Restart Excel or click "Reiniciar Entornos" | R engine reloads | ☐ | |
| 3 | In a cell, type `=NEVEN.r.mi_suma(3, 7)` | Returns `10` | ☐ | |

### T-04: Julia Integration — Basic Function

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | Create file `Docs/NEVEN/functions/test.jl` with: `JuliaSuma(a, b) = a + b` | File saved | ☐ | |
| 2 | Restart Excel or click "Reiniciar Entornos" | Julia engine reloads | ☐ | |
| 3 | In a cell, type `=NEVEN.j.JuliaSuma(5, 8)` | Returns `13` | ☐ | |

### T-05: Console REPL (WebView2)

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | Click "Abrir Consola" in the NEVEN Ribbon tab | WebView2 REPL window opens with dark theme | ☐ | |
| 2 | Type `1 + 1` in the R prompt | Returns `[1] 2` | ☐ | |
| 3 | Switch to Julia tab and type `2^10` | Returns `1024` | ☐ | |
| 4 | Type `system("dir")` in R prompt | Blocked by sandbox with error message | ☐ | |

### T-06: R Graphics

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | In the R console, type `plot(1:10)` | A scatter plot appears in the console or as an Excel shape | ☐ | |

### T-07: COM Automation from Julia

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | In the Julia console, type `EXCEL.ActiveSheet.Range("A1").Value = "Hello"` | Cell A1 shows "Hello" | ☐ | |

### T-08: File Hot-Reload

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | With Excel open, modify `test.R` to change `mi_suma` to return `a * b` | File saved | ☐ | |
| 2 | Wait 2-3 seconds (FileWatchService interval) | Function auto-reloads | ☐ | |
| 3 | Recalculate `=NEVEN.r.mi_suma(3, 7)` | Returns `21` (3×7) | ☐ | |

### T-09: Security — Script Integrity

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | Create a `.sha256` sidecar file for `test.R` with the wrong hash | File saved | ☐ | |
| 2 | Restart Excel | Warning logged about integrity mismatch | ☐ | |

### T-10: Uninstaller

| Step | Action | Expected Result | Pass/Fail | Notes |
|------|--------|-----------------|-----------|-------|
| 1 | Go to Control Panel --> Programs --> NEVEN 2.0 --> Uninstall | Uninstaller runs | ☐ | |
| 2 | Reopen Excel | NEVEN tab is gone, no errors | ☐ | |

---

## Summary

| Category | Total | Passed | Failed | Blocked |
|----------|-------|--------|--------|---------|
| Loading & Registration | 3 | | | |
| R Integration | 3 | | | |
| Julia Integration | 3 | | | |
| Console | 3 | | | |
| Graphics | 1 | | | |
| COM Automation | 1 | | | |
| File Watching | 3 | | | |
| Security | 2 | | | |
| Installer/Uninstaller | 2 | | | |
| **TOTAL** | **21** | | | |

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Tester | | | |
| Supervisor | | | |

---
*Template version: 1.0.0 — Generated for NEVEN UAT*
