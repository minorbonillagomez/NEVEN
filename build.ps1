# build.ps1 - RJ2XCL Build, Test and Package Automation
# Copyright (c) 2026 RJ2XCL Project - GPLv3
#
# USAGE:
#   .\build.ps1                        # Configure + Build (Release)
#   .\build.ps1 -Config Debug          # Debug build
#   .\build.ps1 -Test                  # Build + run unit tests
#   .\build.ps1 -Package               # Build + test + package XLL + configs
#   .\build.ps1 -Clean                 # Delete build dir first
#   .\build.ps1 -Clean -Test -Package  # Full clean rebuild

Param(
    [switch]$Clean   = $false,
    [switch]$Test    = $false,
    [switch]$Package = $false,
    [string]$BuildDir = "Build",
    [string]$Config   = "Release"
)

$ErrorActionPreference = "Stop"

# --- Helpers ---
function Write-Step { param([string]$msg, [string]$color = "Green")
    Write-Host ""
    Write-Host "$msg" -ForegroundColor $color }

function Fail { param([string]$msg)
    Write-Host ""
    Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

# Add CMake to path for this session
$cmakePath = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
if (-not (Test-Path "$cmakePath\cmake.exe")) {
    # Fallback to standalone CMake
    $cmakePath = "C:\Program Files\CMake\bin"
}
$env:Path = "$cmakePath;" + $env:Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RJ2XCL Build Automation v2.0.0       " -ForegroundColor Cyan
Write-Host "   Config: $Config  |  BuildDir: $BuildDir" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Clean
if ($Clean -and (Test-Path $BuildDir)) {
    Write-Step "[1/5] Cleaning '$BuildDir'..." "Yellow"
    Remove-Item -Path $BuildDir -Recurse -Force
}

# 2. Create build dir
if (-not (Test-Path $BuildDir)) {
    Write-Step "[2/5] Creating build directory..."
    New-Item -Path $BuildDir -ItemType Directory | Out-Null
}

# 3. Configure CMake
Write-Step "[3/5] Configuring CMake (x64)..."
cmake -S . -B $BuildDir -A x64 "-DCMAKE_BUILD_TYPE=$Config"
if ($LASTEXITCODE -ne 0) { Fail "CMake configuration failed (exit $LASTEXITCODE)." }

# 4. Build
Write-Step "[4/5] Building project ($Config)..."
cmake --build $BuildDir --config $Config --parallel
if ($LASTEXITCODE -ne 0) { Fail "Build failed (exit $LASTEXITCODE)." }

# 5. Tests (optional flag)
if ($Test) {
    Write-Step "[5/5] Running unit tests..." "Cyan"
    Push-Location $BuildDir
    try {
        ctest --output-on-failure -C $Config --test-dir .
        if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "Unit tests failed (exit $LASTEXITCODE)." }
        Write-Host "All tests passed." -ForegroundColor Green
    } finally {
        Pop-Location
    }
} else {
    Write-Step "[5/5] Tests skipped (use -Test to run)." "DarkGray"
}

# 6. Package (optional flag)
if ($Package) {
    Write-Step "Packaging distribution..." "Cyan"
    $distDir = Join-Path $BuildDir "Dist"
    if (-not (Test-Path $distDir)) { Fail "Dist/ not found - did the build succeed?" }

    # Verify the XLL was generated
    $xllPath = Join-Path $distDir "NEVEN64.xll"
    if (-not (Test-Path $xllPath)) { Fail "NEVEN64.xll not found in $distDir." }
    $xllSize = (Get-Item $xllPath).Length / 1024
    $roundedXllSize = [math]::Round($xllSize)
    Write-Host "  NEVEN64.xll:    $roundedXllSize KB" -ForegroundColor Green

    # Copy additional files into Dist
    Copy-Item "Install\rj2xcl_logo.png" $distDir -Force -ErrorAction SilentlyContinue
    Copy-Item "Install\*.json"          $distDir -Force -ErrorAction SilentlyContinue
    Copy-Item "Examples\*"              (Join-Path $distDir "examples") -Force -Recurse -ErrorAction SilentlyContinue
    
    # Copy Engine Backends
    Copy-Item "$BuildDir\ControlR\${Config}\ControlR.exe" $distDir -Force -ErrorAction SilentlyContinue
    Copy-Item "$BuildDir\ControlJulia\${Config}\ControlJulia.exe" $distDir -Force -ErrorAction SilentlyContinue

    # Create versioned zip
    $version  = "2.0.0"
    $zipName  = "RJ2XCL_${version}_${Config}.zip"
    # Ensure root Dist folder exists for the zip artifact
    if (-not (Test-Path "Dist")) { New-Item -ItemType Directory -Path "Dist" -Force | Out-Null }
    $zipDest  = Join-Path "Dist" $zipName
    if (Test-Path $zipDest) { Remove-Item $zipDest -Force }
    Compress-Archive -Path $distDir\* -DestinationPath $zipDest
    $zipSize = (Get-Item $zipDest).Length / 1024
    $roundedZipSize = [math]::Round($zipSize)
    Write-Host "  Package created: $zipDest ($roundedZipSize KB)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Build complete! " -NoNewline
Write-Host "RJ2XCL $Config" -ForegroundColor Yellow -NoNewline
Write-Host " ready." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
