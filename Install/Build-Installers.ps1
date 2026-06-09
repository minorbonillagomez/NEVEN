<#
.SYNOPSIS
    Genera Install-NEVEN.exe y Uninstall-NEVEN.exe a partir de los scripts .ps1

.DESCRIPTION
    Usa ps2exe para convertir los scripts PowerShell en ejecutables standalone.
    Ejecutar cada vez que se modifique Install-NEVEN.ps1 o Uninstall-NEVEN.ps1.

.EXAMPLE
    .\Build-Installers.ps1
#>

# Verificar ps2exe
$module = Get-Module -ListAvailable -Name ps2exe
if (-not $module) {
    Write-Host "Instalando ps2exe..." -ForegroundColor Yellow
    Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser | Out-Null
    Install-Module -Name ps2exe -Scope CurrentUser -Force -SkipPublisherCheck
}
Import-Module ps2exe

$scriptDir = $PSScriptRoot

# Generar Install-NEVEN.exe
Write-Host "Generando Install-NEVEN.exe..." -ForegroundColor Cyan
Invoke-ps2exe -inputFile (Join-Path $scriptDir "Install-NEVEN.ps1") `
              -outputFile (Join-Path $scriptDir "Install-NEVEN.exe") `
              -title "NEVEN Installer" `
              -description "NEVEN - R, Julia and Python to Excel" `
              -company "Universidad de Costa Rica" `
              -product "NEVEN" `
              -version "2.0.0.0" `
              -copyright "2026 Minor Bonilla Gomez - GPL v3" `
              -requireAdmin `
              -noConsole:$false

# Generar Uninstall-NEVEN.exe
Write-Host "Generando Uninstall-NEVEN.exe..." -ForegroundColor Cyan
Invoke-ps2exe -inputFile (Join-Path $scriptDir "Uninstall-NEVEN.ps1") `
              -outputFile (Join-Path $scriptDir "Uninstall-NEVEN.exe") `
              -title "NEVEN Uninstaller" `
              -description "NEVEN Uninstaller" `
              -company "Universidad de Costa Rica" `
              -product "NEVEN" `
              -version "2.0.0.0" `
              -copyright "2026 Minor Bonilla Gomez - GPL v3" `
              -noConsole:$false

Write-Host ""
Write-Host "Listo. Archivos generados:" -ForegroundColor Green
Get-ChildItem (Join-Path $scriptDir "*.exe") | ForEach-Object {
    Write-Host "  $($_.Name) ($([math]::Round($_.Length/1KB)) KB)" -ForegroundColor White
}
