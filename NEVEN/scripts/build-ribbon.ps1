# build-ribbon.ps1 - RJ2XCL Ribbon DLL Builder
# Copyright (c) 2026 RJ2XCL Project - GPLv3
#
# Compiles RJ2XCLRibbon.vcxproj using MSBuild (Visual Studio 2022).
# The Ribbon project is a COM ATL DLL that provides the Excel Ribbon UI.
# It is kept as a separate .vcxproj because ATL projects are not trivially
# migrated to CMake.
#
# USAGE:
#   .\scripts\build-ribbon.ps1                 # Release x64 (default)
#   .\scripts\build-ribbon.ps1 -Config Debug   # Debug build
#
# OUTPUT:
#   Ribbon\x64\Release\RJ2XCLRibbon2x64.dll
#   Build\Dist\RJ2XCLRibbon2x64.dll       (copied automatically)

Param(
    [string]$Config   = "Release",
    [string]$Platform = "x64"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RJ2XCL Ribbon Builder                " -ForegroundColor Cyan
Write-Host "   Config: $Config | Platform: $Platform" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- Locate MSBuild ---
$msbuildPaths = @(
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
)

$msbuild = $null
foreach ($p in $msbuildPaths) {
    if (Test-Path $p) { $msbuild = $p; break }
}

if (-not $msbuild) {
    # Try vswhere as fallback
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild -property installationPath
        $candidate = Join-Path $vsPath "MSBuild\Current\Bin\MSBuild.exe"
        if (Test-Path $candidate) { $msbuild = $candidate }
    }
}

if (-not $msbuild) {
    Write-Host "[ERROR] MSBuild not found. Please install Visual Studio 2022 with C++ workload." -ForegroundColor Red
    Write-Host "        Searched paths:" -ForegroundColor Yellow
    $msbuildPaths | ForEach-Object { Write-Host "          $_" -ForegroundColor DarkGray }
    exit 1
}

Write-Host "MSBuild: $msbuild" -ForegroundColor DarkGray

# --- Project paths ---
$projectRoot = Split-Path $PSScriptRoot -Parent
$ribbonProj  = Join-Path $projectRoot "Ribbon\RJ2XCLRibbon.vcxproj"
$outDll      = Join-Path $projectRoot "Ribbon\x64\$Config\RJ2XCLRibbon2x64.dll"
$distDir     = Join-Path $projectRoot "Build\Dist"

if (-not (Test-Path $ribbonProj)) {
    Write-Host "[ERROR] Ribbon project not found: $ribbonProj" -ForegroundColor Red
    exit 1
}

# --- Build ---
Write-Host ""
Write-Host "Building $ribbonProj..." -ForegroundColor Green
& $msbuild $ribbonProj `
    /p:Configuration=$Config `
    /p:Platform=$Platform `
    /m `
    /nologo `
    /verbosity:minimal

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Ribbon build failed (exit $LASTEXITCODE)." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Ribbon build successful." -ForegroundColor Green

# --- Copy to Dist ---
if (Test-Path $outDll) {
    if (-not (Test-Path $distDir)) { New-Item -Path $distDir -ItemType Directory | Out-Null }
    Copy-Item $outDll $distDir -Force
    $sizKB = [math]::Round((Get-Item $outDll).Length / 1024)
    Write-Host "Copied: $outDll -> $distDir ($sizKB KB)" -ForegroundColor Cyan
} else {
    Write-Host "[WARN] Output DLL not found at expected path:" -ForegroundColor Yellow
    Write-Host "       $outDll" -ForegroundColor DarkGray
    Write-Host "       Check the Ribbon project output directory." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Ribbon build complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
