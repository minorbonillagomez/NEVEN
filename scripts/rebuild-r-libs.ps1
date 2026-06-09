#=============================================
# RJ2XCL: Rebuild R import libraries for linking ControlR.exe
#
# This script generates R64.lib and RGraphApp64.lib from the
# R.dll and RGraphApp.dll found in your R installation.
#
# Usage:
#   .\scripts\rebuild-r-libs.ps1
#   .\scripts\rebuild-r-libs.ps1 -RHome "C:\Program Files\R\R-4.4.1"
#
# Requirements:
#   - Visual Studio Developer Command Prompt (for dumpbin and lib)
#   - R installed (auto-detected from registry or PATH)
#=============================================

Param(
    [String]$RHome
)

function Find-R {
    # 1. Check parameter
    if ($RHome -and (Test-Path $RHome)) {
        return $RHome
    }

    # 2. Check R_HOME environment variable
    $envHome = $env:R_HOME
    if ($envHome -and (Test-Path $envHome)) {
        return $envHome
    }

    # 3. Check registry (R 4.x)
    $regPaths = @(
        "HKLM:\SOFTWARE\R-core\R64",
        "HKLM:\SOFTWARE\R-core\R",
        "HKLM:\SOFTWARE\WOW6432Node\R-core\R64",
        "HKLM:\SOFTWARE\WOW6432Node\R-core\R"
    )
    foreach ($regPath in $regPaths) {
        if (Test-Path $regPath) {
            $installPath = (Get-ItemProperty $regPath -ErrorAction SilentlyContinue).InstallPath
            if ($installPath -and (Test-Path $installPath)) {
                Write-Host "Found R in registry: $installPath" -ForegroundColor Green
                return $installPath
            }
        }
    }

    # 4. Check common paths
    $commonPaths = @(
        "C:\Program Files\R",
        "$env:ProgramFiles\R"
    )
    foreach ($base in $commonPaths) {
        if (Test-Path $base) {
            $latest = Get-ChildItem $base -Directory | Sort-Object Name -Descending | Select-Object -First 1
            if ($latest) {
                Write-Host "Found R in common path: $($latest.FullName)" -ForegroundColor Green
                return $latest.FullName
            }
        }
    }

    Write-Host "ERROR: Could not find R installation. Use -RHome parameter." -ForegroundColor Red
    exit 1
}

# Find R
$rHome = Find-R
Write-Host "Using R home: $rHome" -ForegroundColor Cyan

# Verify R.dll exists
$rDll = Join-Path $rHome "bin\x64\R.dll"
$rgaDll = Join-Path $rHome "bin\x64\RGraphApp.dll"

if (-not (Test-Path $rDll)) {
    Write-Host "ERROR: R.dll not found at $rDll" -ForegroundColor Red
    exit 1
}

# Output directory
$outDir = Join-Path $PSScriptRoot "..\ControlR\lib"
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

Write-Host ""
Write-Host "Generating 64-bit .def and .lib files..." -ForegroundColor Yellow

# Check for dumpbin and lib
$dumpbin = Get-Command dumpbin -ErrorAction SilentlyContinue
$lib = Get-Command lib -ErrorAction SilentlyContinue

if (-not $dumpbin -or -not $lib) {
    Write-Host "ERROR: dumpbin and lib not found. Run from Visual Studio Developer Command Prompt." -ForegroundColor Red
    Write-Host "  Or run: & 'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat'" -ForegroundColor Yellow
    exit 1
}

# Generate R64.def from R.dll
Write-Host "  Generating R64.def from R.dll..." -ForegroundColor White
$symbols = dumpbin /exports $rDll | Out-String
$symbols = ($symbols -replace "(?s)^.*ordinal.*?\n", "")
$symbols = ($symbols -replace "(?s)\n\s*Summary.*?$", "")
$symbols = ($symbols -replace "(?m)^\s+\S+\s+\S+\s+\S+\s+", "")
$defContent = "LIBRARY R`nEXPORTS`n`n$symbols`n"
$defPath = Join-Path $outDir "R64.def"
$defContent | Out-File -Encoding ASCII $defPath

# Generate R64.lib
Write-Host "  Generating R64.lib..." -ForegroundColor White
$libPath = Join-Path $outDir "R64.lib"
lib /machine:X64 /def:$defPath /out:$libPath 2>&1 | Out-Null

# Generate RGraphApp64.def and .lib (if exists)
if (Test-Path $rgaDll) {
    Write-Host "  Generating RGraphApp64.def from RGraphApp.dll..." -ForegroundColor White
    $symbols = dumpbin /exports $rgaDll | Out-String
    $symbols = ($symbols -replace "(?s)^.*ordinal.*?\n", "")
    $symbols = ($symbols -replace "(?s)\n\s*Summary.*?$", "")
    $symbols = ($symbols -replace "(?m)^\s+\S+\s+\S+\s+\S+\s+", "")
    $symbols = ($symbols -replace "(?m)^\(.*?\n", "")
    $defContent = "LIBRARY RGraphApp`nEXPORTS`n`n$symbols`n"
    $defPath = Join-Path $outDir "RGraphApp64.def"
    $defContent | Out-File -Encoding ASCII $defPath

    $libPath = Join-Path $outDir "RGraphApp64.lib"
    lib /machine:X64 /def:$defPath /out:$libPath 2>&1 | Out-Null
}
else {
    Write-Host "  WARNING: RGraphApp.dll not found at $rgaDll (skipping)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done! Libraries generated in: $outDir" -ForegroundColor Green
Write-Host "  R64.lib" -ForegroundColor White
if (Test-Path $rgaDll) {
    Write-Host "  RGraphApp64.lib" -ForegroundColor White
}
Write-Host ""
Write-Host "Next step: rebuild the project with CMake" -ForegroundColor Cyan
