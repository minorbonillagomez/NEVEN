<#
.SYNOPSIS
    Compila NEVEN-Setup.nsi contra un Dist/ de relleno para comprobar su sintaxis.

.DESCRIPTION
    makensis aborta en la pagina de bienvenida de NEVEN-Setup.nsi cuando Dist/
    no esta poblado ("Error while loading icon from Dist\NEVEN_studio.ico"), asi
    que nunca llega a parsear las secciones del final: el bloque de deteccion de
    motores y los dos bloques de permisos de la instalacion no se pueden comprobar
    sin un empaquetado completo.

    Este script copia el .nsi real a un directorio temporal, genera ahi un Dist/
    de relleno (un icono y dos BMP validos, mas un fichero por cada ruta que el
    .nsi incluye) y compila. No toca el repositorio ni produce un instalador
    utilizable: el .exe resultante queda en el temporal y se borra.

.PARAMETER KeepWorkDir
    No borrar el directorio temporal, para inspeccionar la salida.

.EXAMPLE
    powershell -NoProfile -File src\Install\Check-NSISSyntax.ps1
#>
[CmdletBinding()]
param(
    [switch]$KeepWorkDir
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$nsi       = Join-Path $scriptDir 'NEVEN-Setup.nsi'

$makensis = $null
foreach ($candidate in @(
    'C:\Program Files (x86)\NSIS\makensis.exe',
    'C:\Program Files\NSIS\makensis.exe'
)) {
    if (Test-Path $candidate) { $makensis = $candidate; break }
}
if (-not $makensis) {
    $cmd = Get-Command makensis.exe -ErrorAction SilentlyContinue
    if ($cmd) { $makensis = $cmd.Source }
}
if (-not $makensis) {
    Write-Host 'SKIP: makensis.exe no esta en este equipo (instale NSIS para comprobar el .nsi).'
    exit 0
}

$workDir = Join-Path $env:TEMP ("neven-nsis-check-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
$dist    = Join-Path $workDir 'Dist'

# Ficheros que el .nsi incluye uno a uno, y directorios que incluye con File /r.
$distFiles = @(
    'NEVEN64.xll', 'NEVENRibbon.dll', 'ControlR.exe', 'ControlJulia.exe',
    'ControlPython.exe', 'neven-config.json', 'neven-languages.json',
    'packages-manifest.json', 'NEVEN Studio.vbs'
)
$distDirs = @('functions', 'startup', 'TaskPane', 'docs', 'examples', 'ontology', 'prompts', 'libreria')

try {
    New-Item -ItemType Directory -Path $dist -Force | Out-Null
    Copy-Item $nsi $workDir
    Copy-Item (Join-Path $scriptDir 'Install-NEVEN.ps1') $workDir
    Copy-Item (Join-Path $scriptDir 'Set-InstallPermissions.ps1') $workDir
    Copy-Item (Join-Path $scriptDir 'license.rtf') $workDir

    foreach ($f in $distFiles) { Set-Content -Path (Join-Path $dist $f) -Value 'placeholder' }
    foreach ($d in $distDirs) {
        $sub = Join-Path $dist $d
        New-Item -ItemType Directory -Path $sub -Force | Out-Null
        Set-Content -Path (Join-Path $sub 'placeholder.txt') -Value 'placeholder'
    }
    Set-Content -Path (Join-Path $dist 'TaskPane\manifest.xml') -Value '<placeholder/>'

    # Un icono y dos BMP reales: makensis valida el formato al compilar.
    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 32, 32
    foreach ($bmpName in @('header.bmp', 'wizard.bmp')) {
        $bmp.Save((Join-Path $dist $bmpName), [System.Drawing.Imaging.ImageFormat]::Bmp)
    }
    $hIcon = $bmp.GetHicon()
    $icon  = [System.Drawing.Icon]::FromHandle($hIcon)
    $fs    = [System.IO.File]::Create((Join-Path $dist 'NEVEN_studio.ico'))
    try { $icon.Save($fs) } finally { $fs.Dispose() }
    $icon.Dispose()
    $bmp.Dispose()

    Push-Location $workDir
    try {
        $output = & $makensis /V2 'NEVEN-Setup.nsi' 2>&1 | Out-String
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    if ($code -eq 0) {
        Write-Host "OK: makensis compilo NEVEN-Setup.nsi completo (codigo 0) en $workDir"
        if ($output.Trim()) { Write-Host $output.Trim() }
    } else {
        Write-Host "FAIL: makensis devolvio $code" -ForegroundColor Red
        Write-Host $output
    }
    exit $code
} finally {
    if ($KeepWorkDir) {
        Write-Host "Directorio de trabajo conservado: $workDir"
    } elseif (Test-Path $workDir) {
        Remove-Item $workDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
