<#
.SYNOPSIS
    NEVEN Uninstaller — Standalone template for removing all NEVEN components.

.DESCRIPTION
    This is the standalone uninstaller template. During installation, Install-NEVEN.ps1
    generates a customized copy of this script inside the NEVEN_Home directory with the
    correct Excel versions embedded.

    This template can also be run directly — it will auto-detect Excel versions.

    Removes:
    - COM registration (regsvr32 /u)
    - XLL registry entries for all Excel versions
    - Ribbon COM registry key
    - User scripts (optional, with prompt)
    - Quarto junction (if present)
    - Desktop shortcut
    - NEVEN_Home directory

.PARAMETER Silent
    Run without interactive prompts. Deletes everything except user scripts.

.EXAMPLE
    .\Uninstall-NEVEN.ps1
    .\Uninstall-NEVEN.ps1 -Silent
#>
param([switch]$Silent)

$ErrorActionPreference = 'Continue'
$NEVENHome = $PSScriptRoot

# Auto-detect Excel versions if not embedded by installer
$ExcelVersions = @()
foreach ($ver in @('15.0','16.0')) {
    $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
    if (Test-Path $regPath) { $ExcelVersions += $ver }
}

Write-Host ''
Write-Host '  ============================================' -ForegroundColor Cyan
Write-Host '   NEVEN Uninstaller' -ForegroundColor Cyan
Write-Host '  ============================================' -ForegroundColor Cyan
Write-Host ''
Write-Host "  This will remove NEVEN from: $NEVENHome" -ForegroundColor White
Write-Host ''

# Confirmation
if (-not $Silent) {
    $confirm = Read-Host '  Are you sure you want to uninstall NEVEN? (y/n)'
    if ($confirm -ne 'y') {
        Write-Host '  Uninstallation cancelled.' -ForegroundColor Yellow
        exit 0
    }
}

# Check if Excel is running
$excelProcs = Get-Process -Name 'EXCEL' -ErrorAction SilentlyContinue
if ($excelProcs) {
    Write-Host '  Excel is currently running. Please close Excel before uninstalling.' -ForegroundColor Red
    if (-not $Silent) {
        $wait = Read-Host '  Press Enter after closing Excel, or type "skip" to continue anyway'
        if ($wait -ne 'skip') {
            $excelProcs = Get-Process -Name 'EXCEL' -ErrorAction SilentlyContinue
            if ($excelProcs) {
                Write-Host '  Excel is still running. Some operations may fail.' -ForegroundColor Yellow
            }
        }
    }
}

$removed = @()

# 1. Unregister COM via regsvr32
$ribbonDll = Join-Path $NEVENHome 'NEVENRibbon.dll'
if (Test-Path $ribbonDll) {
    try {
        $proc = Start-Process -FilePath 'regsvr32' -ArgumentList "/u /s `"$ribbonDll`"" -Wait -PassThru -NoNewWindow -ErrorAction SilentlyContinue
        $removed += 'COM registration (regsvr32 /u)'
    } catch {
        Write-Host "  Warning: Failed to unregister COM: $_" -ForegroundColor Yellow
    }
}

# 2. Remove XLL registry entries
foreach ($ver in $ExcelVersions) {
    $regPath = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
    if (-not (Test-Path $regPath)) { continue }
    $props = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
    $openKeys = $props.PSObject.Properties | Where-Object { $_.Name -match '^OPEN\d*$' -and $_.Value -match 'NEVEN' }
    foreach ($key in $openKeys) {
        Remove-ItemProperty -Path $regPath -Name $key.Name -ErrorAction SilentlyContinue
        $removed += "XLL entry $($key.Name) (Excel $ver)"
    }
}

# 3. Remove Ribbon registry key
$ribbonKey = 'HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect'
if (Test-Path $ribbonKey) {
    Remove-Item -Path $ribbonKey -Recurse -Force -ErrorAction SilentlyContinue
    $removed += 'Ribbon registry key'
}

# 4. User scripts — prompt before deleting
$userNevenDir = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'NEVEN'
if (Test-Path $userNevenDir) {
    $deleteUser = 'n'
    if (-not $Silent) {
        Write-Host ''
        Write-Host "  User scripts found at: $userNevenDir" -ForegroundColor White
        $deleteUser = Read-Host '  Delete user scripts and graphics? This cannot be undone. (y/n) [n]'
    }
    if ($deleteUser -eq 'y') {
        Remove-Item -Path $userNevenDir -Recurse -Force -ErrorAction SilentlyContinue
        $removed += "User scripts directory ($userNevenDir)"
    } else {
        Write-Host "  Preserved user scripts at $userNevenDir" -ForegroundColor Green
    }
}

# 5. Quarto junction
if (Test-Path 'C:\Quarto') {
    $item = Get-Item 'C:\Quarto' -Force -ErrorAction SilentlyContinue
    if ($item -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        try {
            cmd /c rmdir 'C:\Quarto' 2>$null
            $removed += 'Quarto junction (C:\Quarto)'
        } catch {
            Write-Host "  Warning: Could not remove Quarto junction: $_" -ForegroundColor Yellow
        }
    }
}

# 6. Desktop shortcut
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'NEVEN.lnk'
if (Test-Path $shortcutPath) {
    Remove-Item -Path $shortcutPath -Force -ErrorAction SilentlyContinue
    $removed += 'Desktop shortcut'
}

# 7. Remove NEVEN_Home directory
# Since this script runs from inside NEVEN_Home, we spawn a cleanup process
$tempScript = Join-Path $env:TEMP 'neven-cleanup.ps1'
$cleanupCode = @"
Start-Sleep -Seconds 2
if (Test-Path '$NEVENHome') {
    Remove-Item -Path '$NEVENHome' -Recurse -Force -ErrorAction SilentlyContinue
}
Remove-Item -Path '$tempScript' -Force -ErrorAction SilentlyContinue
"@
Set-Content -Path $tempScript -Value $cleanupCode -Encoding UTF8

# Summary
Write-Host ''
Write-Host '  ============================================' -ForegroundColor Green
Write-Host '   NEVEN Uninstallation Summary' -ForegroundColor Green
Write-Host '  ============================================' -ForegroundColor Green
foreach ($item in $removed) {
    Write-Host "   [OK] Removed: $item" -ForegroundColor Green
}
Write-Host "   [OK] NEVEN directory will be removed: $NEVENHome" -ForegroundColor Green
Write-Host ''
Write-Host '  NEVEN has been uninstalled.' -ForegroundColor White
Write-Host ''

# Launch deferred cleanup and exit
Start-Process -FilePath 'powershell.exe' -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$tempScript`"" -WindowStyle Hidden
exit 0
