<#
.SYNOPSIS
    Sincroniza archivos del repositorio a Dist/ y genera NEVEN-v3.2-Setup.zip.

.DESCRIPTION
    Este script es la fuente de verdad para construir el ZIP del instalador.
    Debe ejecutarse cada vez que se modifiquen archivos en:
      - NEVEN/TaskPane/        (servidor HTTP, RAG engine, taskpane HTML/JS)
      - NEVEN/docs/            (documentacion, RAG_GUIDE.md, neven-docs.html)
      - NEVEN/docs/Docusaurus/ (capitulos .md fuente)
      - NEVEN/libreria/        (funciones R, Julia, Python)
      - NEVEN/startup/         (scripts de inicio)

    La carpeta Dist/ esta en .gitignore. Este script la mantiene sincronizada
    con los archivos trackeados en git antes de empacar el ZIP.

.EXAMPLE
    .\Build-Setup.ps1

.NOTES
    IMPORTANTE: Usar [System.IO.File]::Copy() en vez de Copy-Item para
    preservar la codificacion UTF-8 sin BOM en archivos R y Python.
#>

param(
    [string]$ZipName  = 'NEVEN-v3.2-Setup.zip',
    [switch]$SkipSync = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir  = $PSScriptRoot
$distDir    = Join-Path $scriptDir 'Dist'
$repoRoot   = Split-Path $scriptDir -Parent  # NEVEN/
$zipPath    = Join-Path $scriptDir $ZipName

# ────────────────────────────────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────────────────────────────────

function Sync-File {
    param([string]$Src, [string]$Dst)
    if (-not (Test-Path $Src)) {
        Write-Host "  WARN: not found: $Src" -ForegroundColor Yellow
        return
    }
    $dstDir = Split-Path $Dst -Parent
    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }
    [System.IO.File]::Copy($Src, $Dst, $true)
    $rel = $Src.Replace($repoRoot + '\', '')
    Write-Host "  synced: $rel" -ForegroundColor Gray
}

function Sync-Dir {
    param([string]$Src, [string]$Dst, [string]$Filter = '*')
    if (-not (Test-Path $Src)) {
        Write-Host "  WARN: dir not found: $Src" -ForegroundColor Yellow
        return
    }
    if (-not (Test-Path $Dst)) {
        New-Item -ItemType Directory -Path $Dst -Force | Out-Null
    }
    Get-ChildItem $Src -Filter $Filter -Recurse -File | ForEach-Object {
        $rel     = $_.FullName.Substring($Src.Length).TrimStart('\')
        $dstFile = Join-Path $Dst $rel
        $dstFileDir = Split-Path $dstFile -Parent
        if (-not (Test-Path $dstFileDir)) {
            New-Item -ItemType Directory -Path $dstFileDir -Force | Out-Null
        }
        [System.IO.File]::Copy($_.FullName, $dstFile, $true)
    }
    $count = @(Get-ChildItem $Src -Filter $Filter -Recurse -File).Count
    Write-Host "  synced dir: $(Split-Path $Src -Leaf)/ ($count files)" -ForegroundColor Gray
}

# ────────────────────────────────────────────────────────────────────────────
#  1. Sincronizar archivos del repo a Dist/
# ────────────────────────────────────────────────────────────────────────────

if (-not $SkipSync) {
    Write-Host "`nSincronizando archivos del repo a Dist/..." -ForegroundColor Cyan

    # -- startup (servidor HTTP, RAG engine, ontology service) --
    Sync-Dir (Join-Path $repoRoot 'TaskPane')  (Join-Path $distDir 'startup') '*.py'
    Sync-Dir (Join-Path $repoRoot 'TaskPane')  (Join-Path $distDir 'startup') '*.txt'

    # -- taskpane (HTML, JS, CSS) --
    Sync-File (Join-Path $repoRoot 'TaskPane\taskpane.html')        (Join-Path $distDir 'taskpane\taskpane.html')
    Sync-Dir  (Join-Path $repoRoot 'TaskPane')                      (Join-Path $distDir 'taskpane') '*.js'
    Sync-Dir  (Join-Path $repoRoot 'TaskPane')                      (Join-Path $distDir 'taskpane') '*.css'

    # -- docs (documentacion trackeada en git) --
    Sync-File (Join-Path $repoRoot 'docs\RAG_GUIDE.md')             (Join-Path $distDir 'docs\RAG_GUIDE.md')
    Sync-File (Join-Path $repoRoot 'docs\neven-docs.html')          (Join-Path $distDir 'docs\neven-docs.html')

    # -- Docusaurus markdown sources (para regenerar HTML si se desea) --
    Sync-Dir  (Join-Path $repoRoot 'docs\Docusaurus')               (Join-Path $distDir 'docs\Docusaurus') '*.md'

    # -- ontologias (docs/ontologia/) --
    Sync-Dir  (Join-Path $repoRoot 'docs\ontologia')                (Join-Path $distDir 'docs\ontologia')

    # -- funciones R / sidecars JSON --
    Sync-Dir  (Join-Path $repoRoot 'Install\functions')             (Join-Path $distDir 'functions')

    # -- libreria R, Julia, Python (solo scripts, no ejemplos) --
    Sync-Dir  (Join-Path $repoRoot 'libreria\R')                    (Join-Path $distDir 'libreria\R')
    Sync-Dir  (Join-Path $repoRoot 'libreria\JULIA')                (Join-Path $distDir 'libreria\JULIA')
    Sync-Dir  (Join-Path $repoRoot 'libreria\Python')               (Join-Path $distDir 'libreria\Python')

    Write-Host "Sincronizacion completada." -ForegroundColor Green
} else {
    Write-Host "`n[SkipSync] Usando Dist/ tal como esta." -ForegroundColor Yellow
}

# ────────────────────────────────────────────────────────────────────────────
#  2. Generar ZIP
# ────────────────────────────────────────────────────────────────────────────

Write-Host "`nGenerando $ZipName..." -ForegroundColor Cyan

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$distDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

$zip    = Get-Item $zipPath
$sizeMB = [math]::Round($zip.Length / 1MB, 2)

# Contar archivos en el ZIP
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive   = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$fileCount = $archive.Entries.Count
$archive.Dispose()

Write-Host ""
Write-Host "ZIP generado exitosamente:" -ForegroundColor Green
Write-Host "  Archivo : $($zip.Name)"           -ForegroundColor White
Write-Host "  Tamano  : $sizeMB MB"              -ForegroundColor White
Write-Host "  Archivos: $fileCount"              -ForegroundColor White
Write-Host "  Fecha   : $($zip.LastWriteTime)"   -ForegroundColor White
Write-Host ""
Write-Host "Proximo paso: hacer commit del ZIP y push." -ForegroundColor DarkGray
