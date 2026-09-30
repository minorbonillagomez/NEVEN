#=============================================
# RJ2XCL: Complete Build Script
#
# This script builds the entire RJ2XCL project:
#   1. Regenerates R import libraries (if R is installed)
#   2. Configures CMake
#   3. Builds all targets in Release mode
#   4. Packages artifacts to Dist/
#
# Usage:
#   .\scripts\build-all.ps1
#   .\scripts\build-all.ps1 -RHome "C:\Program Files\R\R-4.4.1"
#   .\scripts\build-all.ps1 -SkipLibs   # Skip R lib regeneration
#
# Requirements:
#   - Visual Studio 2019+ (with C++ desktop development)
#   - CMake 3.15+ (usually comes with VS)
#   - R installed (for ControlR.exe)
#   - Julia installed (for ControlJulia.exe, optional)
#=============================================

Param(
    [String]$RHome,
    [switch]$SkipLibs,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$buildDir = Join-Path $rootDir "Build"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RJ2XCL Build System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 0: Find CMake
$cmake = Get-Command cmake -ErrorAction SilentlyContinue
if (-not $cmake) {
    # Try VS paths
    $vsPaths = @(
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "C:\Program Files\CMake\bin\cmake.exe"
    )
    foreach ($p in $vsPaths) {
        if (Test-Path $p) {
            $cmake = @{ Source = $p }
            Write-Host "Found CMake at: $p" -ForegroundColor Green
            break
        }
    }
    if (-not $cmake) {
        Write-Host "ERROR: CMake not found. Install CMake or run from VS Developer Command Prompt." -ForegroundColor Red
        exit 1
    }
}
$cmakePath = if ($cmake.Source) { $cmake.Source } else { "cmake" }

# Step 1: Regenerate R libs (optional)
if (-not $SkipLibs) {
    Write-Host "[Step 1/4] Regenerating R import libraries..." -ForegroundColor Yellow
    $rebuildScript = Join-Path $scriptDir "rebuild-r-libs.ps1"
    if (Test-Path $rebuildScript) {
        $rebuildArgs = @()
        if ($RHome) { $rebuildArgs += "-RHome", $RHome }
        & $rebuildScript @rebuildArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARNING: R lib regeneration failed. ControlR.exe may not link." -ForegroundColor Yellow
            Write-Host "  You can skip this with -SkipLibs and use existing libs." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  rebuild-r-libs.ps1 not found, skipping" -ForegroundColor Yellow
    }
} else {
    Write-Host "[Step 1/4] Skipping R lib regeneration (-SkipLibs)" -ForegroundColor Gray
}

# Step 2: Clean if requested
if ($Clean -and (Test-Path $buildDir)) {
    Write-Host "[Step 2/4] Cleaning build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $buildDir
}

# Step 3: Configure CMake
Write-Host "[Step 3/4] Configuring CMake..." -ForegroundColor Yellow
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
}

$cmakeArgs = @("..", "-A", "x64")
if ($RHome) {
    $cmakeArgs += "-DR_HOME=$RHome"
}

Push-Location $buildDir
try {
    & $cmakePath @cmakeArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: CMake configuration failed." -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# Step 4: Build
Write-Host "[Step 4/4] Building Release..." -ForegroundColor Yellow
& $cmakePath --build $buildDir --config Release
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Build had errors. Check output above." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Build Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}

# Summary
$distDir = Join-Path $buildDir "Dist"
Write-Host ""
Write-Host "Output directory: $distDir" -ForegroundColor Cyan
if (Test-Path $distDir) {
    Get-ChildItem $distDir -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($distDir.Length + 1)
        $size = "{0:N0} KB" -f ($_.Length / 1024)
        Write-Host "  $rel ($size)" -ForegroundColor White
    }
}
Write-Host ""
