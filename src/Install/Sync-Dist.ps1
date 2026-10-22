<#
.SYNOPSIS
    Sincroniza los componentes de produccion (C:\NEVEN) al directorio Dist para empaquetado.

.DESCRIPTION
    Copia todos los archivos necesarios para el instalador desde la instalacion de
    desarrollo en C:\NEVEN al directorio Dist\. Excluye la sysimage de Julia y
    archivos de log/temporales.

.PARAMETER SourceDir
    Directorio de produccion. Default: C:\NEVEN

.PARAMETER DistDir
    Directorio de distribucion. Default: .\Dist

.PARAMETER Force
    Sobrescribe archivos existentes sin preguntar.

.EXAMPLE
    .\Sync-Dist.ps1
    .\Sync-Dist.ps1 -Force
#>
param(
    [string]$SourceDir = 'C:\NEVEN',
    [string]$DistDir = (Join-Path $PSScriptRoot 'Dist'),
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# ============================================================
#  Configuracion de componentes
# ============================================================

# Archivos individuales a copiar
$Files = @(
    'NEVEN64.xll',
    'NEVENRibbon.dll',
    'ControlR.exe',
    'ControlJulia.exe',
    'ControlPython.exe',
    'neven-config.json',
    'neven-languages.json',
    'manifest.xml',
    'packages-manifest.json',
    'NEVEN Studio.vbs',
    'NEVEN_studio.ico'
)

# Directorios a copiar (completos)
$Directories = @(
    'functions',
    'startup',
    'TaskPane',
    'examples',
    'docs',
    'ontology',
    'prompts',
    'libreria'
    # 'data' excluido - contiene archivos temporales y DBs de desarrollo
    # 'notebooks' excluido - vacio, usuarios crean los propios
)

# Patrones a excluir
$ExcludePatterns = @(
    '*.log',
    '*.tmp',
    '*.bak',
    '*.bak_*',
    '__pycache__',
    '.pytest_cache',
    '.hypothesis',
    'neven_julia.dll',
    'neven_julia.version',
    'webview2-data',
    'crashes',
    'temp',
    'workspace',
    'certs',
    '*.pid'
)

# ============================================================
#  Funciones
# ============================================================

function Write-Status {
    param([string]$Message, [string]$Type = 'INFO')
    switch ($Type) {
        'OK'    { $symbol = '[OK]'; $color = 'Green' }
        'WARN'  { $symbol = '[!]'; $color = 'Yellow' }
        'ERROR' { $symbol = '[X]'; $color = 'Red' }
        default { $symbol = '-->'; $color = 'Cyan' }
    }
    Write-Host "  $symbol $Message" -ForegroundColor $color
}

function Copy-FileIfNewer {
    param([string]$Source, [string]$Dest)
    
    if (-not (Test-Path $Source)) {
        Write-Status "$([System.IO.Path]::GetFileName($Source)) - NO EXISTE en origen" 'WARN'
        return $false
    }
    
    $srcInfo = Get-Item $Source
    $needsCopy = $true
    
    if ((Test-Path $Dest) -and -not $Force) {
        $dstInfo = Get-Item $Dest
        if ($srcInfo.LastWriteTime -le $dstInfo.LastWriteTime) {
            $needsCopy = $false
        }
    }
    
    if ($needsCopy) {
        [System.IO.File]::Copy($Source, $Dest, $true)
        $sizeMB = [math]::Round($srcInfo.Length / 1MB, 2)
        Write-Status "$([System.IO.Path]::GetFileName($Source)) ($sizeMB MB)" 'OK'
        return $true
    } else {
        Write-Status "$([System.IO.Path]::GetFileName($Source)) (sin cambios)" 'INFO'
        return $false
    }
}

function Copy-DirectoryFiltered {
    param([string]$Source, [string]$Dest, [string[]]$Exclude)
    
    if (-not (Test-Path $Source)) {
        Write-Status "$([System.IO.Path]::GetFileName($Source))/ - NO EXISTE en origen" 'WARN'
        return
    }
    
    # Limpiar destino si existe
    if (Test-Path $Dest) {
        Remove-Item $Dest -Recurse -Force
    }
    
    # Crear directorio destino
    New-Item -ItemType Directory -Path $Dest -Force | Out-Null
    
    # Copiar archivos excluyendo patrones
    $files = Get-ChildItem $Source -Recurse -File | Where-Object {
        $relativePath = $_.FullName.Substring($Source.Length + 1)
        $excluded = $false
        foreach ($pattern in $Exclude) {
            if ($relativePath -like $pattern -or $_.Name -like $pattern -or $_.Directory.Name -like $pattern) {
                $excluded = $true
                break
            }
        }
        -not $excluded
    }
    
    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($Source.Length + 1)
        $destFile = Join-Path $Dest $relativePath
        $destDir = [System.IO.Path]::GetDirectoryName($destFile)
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        [System.IO.File]::Copy($file.FullName, $destFile, $true)
    }
    
    $count = (Get-ChildItem $Dest -Recurse -File -ErrorAction SilentlyContinue).Count
    $size = [math]::Round((Get-ChildItem $Dest -Recurse -File -ErrorAction SilentlyContinue | 
             Measure-Object -Property Length -Sum).Sum / 1MB, 2)
    Write-Status "$([System.IO.Path]::GetFileName($Source))/ ($count archivos, $size MB)" 'OK'
}

# ============================================================
#  Main
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         NEVEN - Sincronizacion a Dist                      " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Origen:  $SourceDir"
Write-Host "  Destino: $DistDir"
Write-Host ""

# Verificar origen
if (-not (Test-Path $SourceDir)) {
    Write-Host "  ERROR: Directorio origen no existe: $SourceDir" -ForegroundColor Red
    exit 1
}

# Crear Dist si no existe
if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
    Write-Status "Creado directorio Dist" 'OK'
}

# Copiar archivos individuales
Write-Host ""
Write-Host "  === ARCHIVOS ===" -ForegroundColor Yellow
foreach ($file in $Files) {
    $src = Join-Path $SourceDir $file
    $dst = Join-Path $DistDir $file
    Copy-FileIfNewer -Source $src -Dest $dst | Out-Null
}

# Copiar directorios
Write-Host ""
Write-Host "  === DIRECTORIOS ===" -ForegroundColor Yellow
foreach ($dir in $Directories) {
    $src = Join-Path $SourceDir $dir
    $dst = Join-Path $DistDir $dir
    Copy-DirectoryFiltered -Source $src -Dest $dst -Exclude $ExcludePatterns
}

# Resumen
Write-Host ""
Write-Host "  === RESUMEN ===" -ForegroundColor Yellow
$totalFiles = (Get-ChildItem $DistDir -Recurse -File).Count
$totalSize = [math]::Round((Get-ChildItem $DistDir -Recurse -File | 
             Measure-Object -Property Length -Sum).Sum / 1MB, 2)
Write-Host ""
Write-Status "Total: $totalFiles archivos, $totalSize MB" 'OK'
Write-Host ""
Write-Host "  Dist listo para empaquetado." -ForegroundColor Green
Write-Host ""
