# add-license-headers.ps1 — GPL v3 Header Injection Tool
# Copyright (c) 2026 RJ2XCL Project — GPLv3
#
# Scans all C++ source files and adds the GPL v3 copyright header
# to any file that doesn't already have one.
#
# USAGE:
#   .\scripts\add-license-headers.ps1             # Dry run (preview)
#   .\scripts\add-license-headers.ps1 -Apply      # Actually modify files

Param(
    [switch]$Apply = $false
)

$projectRoot = Split-Path $PSScriptRoot -Parent

$header = @"
/**
 * Copyright (c) 2026 RJ2XCL Project
 *
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

"@

$scanDirs = @(
    "RJ2XCL\include",
    "RJ2XCL\src",
    "Common",
    "ControlR",
    "ControlJulia",
    "PB",
    "tests"
)

$extensions = @("*.cc", "*.cpp", "*.h")
$excludePatterns = @("*json11*", "*Build*", "*_deps*", "*.pb.h", "*.pb.cc")

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   GPL v3 License Header Tool           " -ForegroundColor Cyan
Write-Host "   Mode: $(if ($Apply) { 'APPLY' } else { 'DRY RUN' })" -ForegroundColor $(if ($Apply) { "Yellow" } else { "Green" })
Write-Host "========================================" -ForegroundColor Cyan

$needsHeader = @()
$alreadyHas = 0

foreach ($dir in $scanDirs) {
    $fullDir = Join-Path $projectRoot $dir
    if (-not (Test-Path $fullDir)) { continue }
    
    foreach ($ext in $extensions) {
        $files = Get-ChildItem -Path $fullDir -Filter $ext -Recurse -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            # Check exclude patterns
            $skip = $false
            foreach ($pattern in $excludePatterns) {
                if ($file.FullName -like $pattern) { $skip = $true; break }
            }
            if ($skip) { continue }

            $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
            if (-not $content) { continue }

            if ($content -match "GNU General Public License" -or $content -match "Copyright.*RJ2XCL") {
                $alreadyHas++
            } else {
                $needsHeader += $file
            }
        }
    }
}

Write-Host ""
Write-Host "Files with header:    $alreadyHas" -ForegroundColor Green
Write-Host "Files missing header: $($needsHeader.Count)" -ForegroundColor $(if ($needsHeader.Count -gt 0) { "Yellow" } else { "Green" })

if ($needsHeader.Count -eq 0) {
    Write-Host "`nAll files have the GPL v3 header!" -ForegroundColor Green
    exit 0
}

Write-Host ""
foreach ($file in $needsHeader) {
    $relativePath = $file.FullName.Replace($projectRoot + "\", "")
    if ($Apply) {
        $content = Get-Content $file.FullName -Raw
        $newContent = $header + $content
        Set-Content -Path $file.FullName -Value $newContent -NoNewline
        Write-Host "  [ADDED] $relativePath" -ForegroundColor Green
    } else {
        Write-Host "  [NEEDS] $relativePath" -ForegroundColor Yellow
    }
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry run complete. Run with -Apply to modify files." -ForegroundColor Cyan
}
