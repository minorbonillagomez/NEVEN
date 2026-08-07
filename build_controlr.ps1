# build_controlr.ps1 — Build ControlR.exe (NEVEN v2.4)
#
# This script handles the r_ge_stubs.cc C-linkage build requirement.
# MSBuild with /TP (compile all as C++) can override CompileAs=CompileAsC
# in incremental builds. This script pre-compiles r_ge_stubs.cc as C
# before invoking the full build, ensuring C linkage for GE symbols.
#
# Usage:
#   .\build_controlr.ps1                    # Release build
#   .\build_controlr.ps1 -Config Debug      # Debug build
#   .\build_controlr.ps1 -CleanFirst        # Full rebuild

param(
    [string]$Config = "Release",
    [switch]$CleanFirst
)

$cmake    = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
$msbuild  = "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
$buildDir = "$PSScriptRoot\Build"
$vcxproj  = "$buildDir\ControlR\ControlR.vcxproj"
$stubFile = "$PSScriptRoot\ControlR\src\r_ge_stubs.cc"

Write-Host "=== Building ControlR.exe ($Config) ===" -ForegroundColor Cyan

if ($CleanFirst) {
    Write-Host "Clean build requested..." -ForegroundColor Yellow
    & $cmake --build $buildDir --target ControlR --config $Config --clean-first 2>&1
    $exitCode = $LASTEXITCODE
} else {
    # Step 1: Pre-compile r_ge_stubs.cc as C (touch to force recompile)
    Write-Host "Step 1: Pre-compiling r_ge_stubs.cc as C..." -ForegroundColor Yellow
    (Get-Item $stubFile).LastWriteTime = Get-Date
    & $msbuild $vcxproj /p:Configuration=$Config /p:Platform=x64 `
        /t:ClCompile "/p:SelectedFiles=$stubFile" /v:m 2>&1 | Select-Object -Last 2

    # Step 2: Full build (r_ge_stubs.obj with C linkage is now in cache)
    Write-Host "Step 2: Building ControlR..." -ForegroundColor Yellow
    & $cmake --build $buildDir --target ControlR --config $Config 2>&1
    $exitCode = $LASTEXITCODE
}

if ($exitCode -eq 0) {
    $exePath = "$buildDir\ControlR\$Config\ControlR.exe"
    if (Test-Path $exePath) {
        $item = Get-Item $exePath
        Write-Host "SUCCESS: ControlR.exe ($([Math]::Round($item.Length/1KB)) KB)" -ForegroundColor Green
        Write-Host "Path: $exePath"
        
        # Verify no static R.dll dependency
        $dumpbin = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\HostX64\x64\dumpbin.exe"
        if (Test-Path $dumpbin) {
            $imports = & $dumpbin /IMPORTS $exePath 2>&1 | Where-Object { $_ -match "R\.dll|R64|RGraphApp" }
            if ($imports) {
                Write-Host "WARNING: Static R.dll imports found!" -ForegroundColor Red
            } else {
                Write-Host "Verified: No static R.dll dependencies (dynamic loading OK)" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "BUILD FAILED (exit code $exitCode)" -ForegroundColor Red
}
