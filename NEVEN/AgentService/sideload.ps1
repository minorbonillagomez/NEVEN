# =============================================================================
# NEVEN AI Agent — Sideloading para desarrollo local
# =============================================================================
#
# Registra el add-in del Agente IA en Excel Desktop (Windows) para pruebas
# locales sin necesidad de publicar en el Marketplace ni en el Admin Center.
#
# USO:
#   PowerShell -ExecutionPolicy Bypass -File sideload.ps1
#   PowerShell -ExecutionPolicy Bypass -File sideload.ps1 -Remove
#   PowerShell -ExecutionPolicy Bypass -File sideload.ps1 -Manifest manifest.dev.xml
#
# REQUISITOS:
#   - Excel Desktop instalado (Microsoft 365 o Excel 2019+)
#   - El servicio IA corriendo: python neven_ai_service.py --port 5556
#   - PowerShell 5.1 o superior
#
# MECANISMO:
#   Office Desktop busca manifests en las "Carpetas de catálogo compartido"
#   registradas en HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs.
#   Este script:
#     1. Crea la carpeta del catálogo si no existe
#     2. Copia el manifest en esa carpeta
#     3. Registra la carpeta como catálogo confiable en el registro
#     4. (Opcional) Inicia el servicio IA automáticamente
#
# PARA DESINSTALAR:
#   Ejecutar con -Remove, o en Excel: Insertar > Mis complementos > ... > Quitar
# =============================================================================

param(
    [switch]$Remove,
    [string]$Manifest = "manifest.dev.xml",
    [int]$ServicePort = 5556,
    [switch]$StartService
)

$ErrorActionPreference = "Stop"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$CatalogDir = "$env:LOCALAPPDATA\NEVEN\AddInCatalog"
$RegPath    = "HKCU:\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs"
$CatalogId  = "{NEVEN-AI-AGENT-DEV-CATALOG}"

# ── Colores de output ──────────────────────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "  → $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "  ✗ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "NEVEN AI Agent — Sideloading" -ForegroundColor White
Write-Host "─────────────────────────────" -ForegroundColor DarkGray

# ── Modo: eliminar ──────────────────────────────────────────────────────────────
if ($Remove) {
    Write-Step "Eliminando registro del catálogo..."

    if (Test-Path "$RegPath\$CatalogId") {
        Remove-Item "$RegPath\$CatalogId" -Recurse -Force
        Write-Ok "Registro eliminado"
    } else {
        Write-Warn "El catálogo no estaba registrado"
    }

    if (Test-Path $CatalogDir) {
        Remove-Item $CatalogDir -Recurse -Force
        Write-Ok "Carpeta del catálogo eliminada: $CatalogDir"
    }

    Write-Host ""
    Write-Host "Add-in removido. Reinicia Excel para aplicar los cambios." -ForegroundColor Yellow
    exit 0
}

# ── Verificar que el manifest existe ────────────────────────────────────────────
$ManifestPath = Join-Path $ScriptDir $Manifest
if (-not (Test-Path $ManifestPath)) {
    Write-Err "Manifest no encontrado: $ManifestPath"
    Write-Host "  Asegúrate de estar en el directorio AgentService/" -ForegroundColor DarkGray
    exit 1
}
Write-Ok "Manifest encontrado: $Manifest"

# ── Crear carpeta del catálogo ───────────────────────────────────────────────────
if (-not (Test-Path $CatalogDir)) {
    New-Item -ItemType Directory -Path $CatalogDir -Force | Out-Null
    Write-Ok "Carpeta del catálogo creada: $CatalogDir"
} else {
    Write-Step "Carpeta del catálogo ya existe: $CatalogDir"
}

# ── Copiar manifest al catálogo ──────────────────────────────────────────────────
$DestManifest = Join-Path $CatalogDir "neven-ai-agent.xml"
[System.IO.File]::Copy($ManifestPath, $DestManifest, $true)
Write-Ok "Manifest copiado a: $DestManifest"

# ── Registrar la carpeta como catálogo confiable en el registro ─────────────────
if (-not (Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}

$CatalogRegPath = "$RegPath\$CatalogId"
if (-not (Test-Path $CatalogRegPath)) {
    New-Item -Path $CatalogRegPath -Force | Out-Null
}

# Valores del catálogo confiable
Set-ItemProperty -Path $CatalogRegPath -Name "Id"          -Value $CatalogId           -Type String
Set-ItemProperty -Path $CatalogRegPath -Name "Url"         -Value $CatalogDir           -Type String
Set-ItemProperty -Path $CatalogRegPath -Name "Flags"       -Value 1                     -Type DWord
Set-ItemProperty -Path $CatalogRegPath -Name "Type"        -Value 1                     -Type DWord

Write-Ok "Catálogo registrado en el registro de Windows"

# ── (Opcional) Iniciar el servicio IA ───────────────────────────────────────────
if ($StartService) {
    Write-Step "Iniciando servicio IA en puerto $ServicePort..."

    $PythonExe = $null
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $PythonExe = $cmd.Source }
    if (-not $PythonExe) {
        $cmd3 = Get-Command python3 -ErrorAction SilentlyContinue
        if ($cmd3) { $PythonExe = $cmd3.Source }
    }

    if ($PythonExe) {
        $ServiceScript = Join-Path $ScriptDir "neven_ai_service.py"
        if (Test-Path $ServiceScript) {
            Start-Process -FilePath $PythonExe `
                -ArgumentList "$ServiceScript --port $ServicePort" `
                -WindowStyle Normal
            Start-Sleep -Seconds 2
            Write-Ok "Servicio IA iniciado en http://localhost:$ServicePort"
        } else {
            Write-Warn "neven_ai_service.py no encontrado en $ScriptDir"
        }
    } else {
        Write-Warn "Python no encontrado en el PATH. Inicia el servicio manualmente:"
        Write-Host "  python neven_ai_service.py --port $ServicePort" -ForegroundColor DarkGray
    }
}

# ── Verificar que el servicio responde ──────────────────────────────────────────
Write-Step "Verificando servicio en http://localhost:$ServicePort..."
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:$ServicePort/health" `
                              -TimeoutSec 3 -ErrorAction Stop
    Write-Ok "Servicio activo — versión: $($resp.version)"
} catch {
    Write-Warn "El servicio no responde en puerto $ServicePort"
    Write-Host "  Inicia el servicio con:" -ForegroundColor DarkGray
    Write-Host "    python neven_ai_service.py --port $ServicePort" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  O ejecuta este script con -StartService:" -ForegroundColor DarkGray
    Write-Host "    PowerShell -ExecutionPolicy Bypass -File sideload.ps1 -StartService" -ForegroundColor DarkGray
}

# ── Instrucciones finales ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Add-in registrado. Para activarlo en Excel:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Abre o reinicia Excel" -ForegroundColor DarkGray
Write-Host "  2. Insertar → Mis complementos → CARPETA COMPARTIDA" -ForegroundColor DarkGray
Write-Host "  3. Selecciona 'NEVEN AI [DEV]' y pulsa Agregar" -ForegroundColor DarkGray
Write-Host "  4. El panel aparecerá en el lado derecho de la hoja" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  URL del add-in: http://localhost:$ServicePort/" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Para desinstalar:" -ForegroundColor DarkGray
Write-Host "    PowerShell -ExecutionPolicy Bypass -File sideload.ps1 -Remove" -ForegroundColor DarkGray
Write-Host ""
