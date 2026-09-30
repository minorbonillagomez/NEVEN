# generate-docs.ps1 - RJ2XCL API Documentation Generator
# Copyright (c) 2026 RJ2XCL Project - GPLv3
#
# Generates HTML API documentation using Doxygen.
#
# USAGE:
#   .\scripts\generate-docs.ps1           # Generate docs
#   .\scripts\generate-docs.ps1 -Open     # Generate and open in browser

Param(
    [switch]$Open = $false
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RJ2XCL Documentation Generator       " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check for Doxygen
$doxygen = Get-Command doxygen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $doxygen) {
    # Fallback for common Windows install paths if PATH hasn't refreshed
    $commonPaths = @(
        "C:\Program Files\doxygen\bin\doxygen.exe",
        "C:\Program Files (x86)\doxygen\bin\doxygen.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) { $doxygen = $p; break }
    }
}

if (-not $doxygen) {
    Write-Host "[ERROR] Doxygen not found in PATH or default locations." -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Doxygen:" -ForegroundColor Yellow
    Write-Host "  1. Download from https://www.doxygen.nl/download.html"
    Write-Host "  2. Or via winget:  winget install doxygen"
    Write-Host "  3. Or via choco:   choco install doxygen.install"
    Write-Host ""
    exit 1
}

# Run Doxygen
Write-Host "Running Doxygen..." -ForegroundColor Green
Push-Location $projectRoot
try {
    & $doxygen Doxyfile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Doxygen failed (exit $LASTEXITCODE)." -ForegroundColor Red
        exit $LASTEXITCODE
    }
} finally {
    Pop-Location
}

$outputDir = Join-Path $projectRoot "docs\api\html"
$indexFile = Join-Path $outputDir "index.html"

if (Test-Path $indexFile) {
    Write-Host "Documentation generated: $outputDir" -ForegroundColor Green
    
    if ($Open) {
        Write-Host "Opening in browser..." -ForegroundColor Cyan
        Start-Process $indexFile
    } else {
        Write-Host "Run with -Open to open in browser." -ForegroundColor DarkGray
    }
} else {
    Write-Host "[WARN] index.html not found at $indexFile" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Documentation generation complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
