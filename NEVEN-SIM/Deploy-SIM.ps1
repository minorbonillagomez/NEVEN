# Deploy-SIM.ps1 — Copia NEVEN-SIM a C:\NEVEN para pruebas
# Uso: .\Deploy-SIM.ps1

$ErrorActionPreference = "Stop"
$dest = "C:\NEVEN"
$buildDir = "$PSScriptRoot\..\Build\NEVEN-SIM\Release"
$simDir = $PSScriptRoot

Write-Host "=== Deploy NEVEN-SIM ===" -ForegroundColor Cyan

# XLL
Write-Host "  Copiando NEVEN-SIM.xll..." -NoNewline
Copy-Item "$buildDir\NEVEN-SIM.xll" "$dest\NEVEN-SIM.xll" -Force
Write-Host " OK" -ForegroundColor Green

# Config
Write-Host "  Copiando neven-sim-config.json..." -NoNewline
Copy-Item "$simDir\neven-sim-config.json" "$dest\neven-sim-config.json" -Force
Write-Host " OK" -ForegroundColor Green

# Workspace HTML
Write-Host "  Copiando workspace..." -NoNewline
New-Item -ItemType Directory -Path "$dest\workspace" -Force | Out-Null
Copy-Item "$simDir\workspace\sim-workspace.html" "$dest\workspace\sim-workspace.html" -Force
Write-Host " OK" -ForegroundColor Green

# R library
Write-Host "  Copiando libreria R..." -NoNewline
Copy-Item "$simDir\libreria\R\neven_sim_fit.R" "$dest\libreria\R\neven_sim_fit.R" -Force
Write-Host " OK" -ForegroundColor Green

# Julia library
Write-Host "  Copiando libreria Julia..." -NoNewline
Copy-Item "$simDir\libreria\JULIA\NEVENSim.jl" "$dest\libreria\JULIA\NEVENSim.jl" -Force
Write-Host " OK" -ForegroundColor Green

Write-Host ""
Write-Host "Deploy completo. Carga NEVEN-SIM.xll en Excel para probar." -ForegroundColor Green
Write-Host "  =SIM.Status()  para verificar" -ForegroundColor Yellow
