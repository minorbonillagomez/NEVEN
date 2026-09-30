# validate-before-run.ps1
# Hook PreToolUse: valida comandos de alto riesgo usando la ontologia de NEVEN.
# Ontologia: F:\ANTIGRAVITY\2026\NEVEN\NEVEN\docs\ontologia\neven-core\neven-ontology-p1.yaml
# Recibe JSON por stdin. Retorna decision "ask" con analisis tecnico especifico.

param()

$inputJson = $input | Out-String
try { $ctx = $inputJson | ConvertFrom-Json } catch { exit 0 }

$command = ""
$toolName = $ctx.toolName
if ($toolName -eq "execute_pwsh") { $command = $ctx.toolInput.command }
elseif ($toolName -eq "control_pwsh_process") {
    $command = $ctx.toolInput.command
    if (-not $command) { exit 0 }
}
if (-not $command) { exit 0 }

# --- Deteccion de tipo de operacion ---
$analysis = @()
$isHighRisk = $false

# REGLA-01: Compilacion del Ribbon
if ($command -match "NEVENRibbon\.vcxproj|MSBuild.*Ribbon") {
    $isHighRisk = $true
    $analysis += "REGLA-01 — Compilacion Ribbon:"
    # Verificar balance de llaves en ribbon_connect.h
    $hFile = "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Ribbon\ribbon_connect.h"
    if (Test-Path $hFile) {
        $content = Get-Content $hFile -Raw
        $open  = ([regex]::Matches($content, '\{')).Count
        $close = ([regex]::Matches($content, '\}')).Count
        if ($open -ne $close) {
            $analysis += "  ERROR: ribbon_connect.h tiene llaves desbalanceadas ({ = $open, } = $close)"
        } else {
            $analysis += "  OK: ribbon_connect.h llaves balanceadas ({ = $open })"
        }
    }
    # Verificar que XML es valido
    $xmlFile = "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Ribbon\ribbon_ui.xml"
    if (Test-Path $xmlFile) {
        try {
            [xml](Get-Content $xmlFile) | Out-Null
            $analysis += "  OK: ribbon_ui.xml es XML valido"
            # Extraer callbacks del XML y verificar vs GetIDsOfNames
            $xmlContent = Get-Content $xmlFile -Raw
            $callbacks = [regex]::Matches($xmlContent, '(?:onAction|getPressed|getLabel)="([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
            $hContent = Get-Content $hFile -Raw
            $missing = @()
            foreach ($cb in $callbacks) {
                if ($hContent -notmatch [regex]::Escape($cb)) {
                    $missing += $cb
                }
            }
            if ($missing.Count -gt 0) {
                $analysis += "  ERROR INV-RIBBON-01: Callbacks en XML no registrados en GetIDsOfNames: $($missing -join ', ')"
            } else {
                $analysis += "  OK INV-RIBBON-01: Todos los callbacks del XML estan en GetIDsOfNames ($($callbacks.Count) verificados)"
            }
        } catch {
            $analysis += "  ERROR: ribbon_ui.xml no es XML valido: $_"
        }
    }
}

# REGLA-02: Deploy de archivo .R
if ($command -match "C:\\\\NEVEN\\\\.*\.R\b|C:/NEVEN/.*\.R\b") {
    $isHighRisk = $true
    $analysis += "REGLA-02 — Deploy de archivo .R:"
    # Extraer ruta del archivo fuente del comando
    $srcMatch = [regex]::Match($command, '"?([A-Z]:[^"]+\.R)"?')
    if ($srcMatch.Success) {
        $srcFile = $srcMatch.Groups[1].Value
        if (Test-Path $srcFile) {
            $bytes = [System.IO.File]::ReadAllBytes($srcFile)
            # BOM check
            if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
                $analysis += "  ERROR INV-SR-05: Archivo tiene BOM (EF BB BF) - usara UTF8Encoding($false)"
            } else {
                $analysis += "  OK INV-SR-01/05: Sin BOM"
            }
            # ASCII check
            $nonAscii = ($bytes | Where-Object { $_ -gt 127 }).Count
            if ($nonAscii -gt 0) {
                $analysis += "  WARN INV-SR-01: $nonAscii caracteres no-ASCII (pueden ser comentarios)"
            } else {
                $analysis += "  OK INV-SR-01: ASCII puro"
            }
            # library() check para startup.r
            if ($srcFile -match "startup\.r$") {
                $lines = Get-Content $srcFile
                $libLines = $lines | Where-Object { $_ -match "^library\(" }
                if ($libLines) {
                    $analysis += "  ERROR INV-SR-02: library() en nivel top-level encontrado — usar requireNamespace()"
                } else {
                    $analysis += "  OK INV-SR-02: Sin library() en nivel top-level"
                }
            }
        }
    }
}

# REGLA-03: Sysimage Julia / PackageCompiler
if ($command -match "PackageCompiler|create_sysimage|build-julia-sysimage|run-sysimage") {
    $isHighRisk = $true
    $analysis += "REGLA-03 — Sysimage Julia:"
    # Verificar que el precompile script existe y corre
    $precompileFile = "C:\NEVEN\startup\precompile_julia_simple.jl"
    if (Test-Path $precompileFile) {
        $analysis += "  OK: Precompile script existe: $precompileFile"
        $analysis += "  PENDIENTE: Verificar que el script corre: julia '$precompileFile'"
        $analysis += "  NOTA: PackageCompiler ejecuta el precompile en sub-proceso Julia con su propio entorno"
        $analysis += "  VALIDAR ANTES: julia '$precompileFile' debe retornar exit code 0"
    } else {
        $analysis += "  ERROR: Precompile script no encontrado: $precompileFile"
    }
}

# REGLA-04: Deploy DLL + regsvr32
if ($command -match "regsvr32|NEVENRibbon\.dll") {
    $isHighRisk = $true
    $analysis += "REGLA-04 — Deploy NEVENRibbon.dll:"
    # Verificar Excel cerrado
    $excel = Get-Process EXCEL -ErrorAction SilentlyContinue
    if ($excel) {
        $analysis += "  ERROR: Excel esta abierto (PID: $($excel.Id)) — cerrar antes de desplegar"
    } else {
        $analysis += "  OK: Excel cerrado"
    }
    # Verificar DLL reciente
    $dllDist = "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Build\Dist\NEVENRibbon.dll"
    if (Test-Path $dllDist) {
        $age = (Get-Date) - (Get-Item $dllDist).LastWriteTime
        if ($age.TotalHours -gt 1) {
            $analysis += "  WARN: DLL tiene $([int]$age.TotalMinutes) minutos — verificar que es el build correcto"
        } else {
            $analysis += "  OK: DLL reciente ($([int]$age.TotalMinutes) minutos)"
        }
    }
}

# REGLA-05: Modificacion de rj2xcl.cc / basic_functions.cc
if ($command -match "rj2xcl\.cc|basic_functions\.cc|rj2xcl\.def") {
    $isHighRisk = $true
    $analysis += "REGLA-05 — Modificacion del Core XLL:"
    $analysis += "  VERIFICAR: RegisterFunctions() no se llama fuera de Init() (INV-CORE-01)"
    $analysis += "  VERIFICAR: Si se agrego funcion nueva, esta en rj2xcl.def"
}

# Patrones generales de alto riesgo no cubiertos arriba
if (-not $isHighRisk) {
    $generalPatterns = @(
        "Remove-Item.*-Recurse.*-Force",
        "git push.*--force|git reset.*--hard",
        "taskkill.*EXCEL",
        "RegDeleteValue|Remove-ItemProperty.*OPEN"
    )
    foreach ($p in $generalPatterns) {
        if ($command -match $p) {
            $isHighRisk = $true
            $analysis += "Operacion potencialmente destructiva: $p"
            break
        }
    }
}

if (-not $isHighRisk) { exit 0 }

# Construir razon de confirmacion
$reasonLines = @("Validacion NEVEN — revisa antes de proceder:", "")
$reasonLines += $analysis
$reasonLines += ""
$reasonLines += "Comando: $($command.Substring(0, [Math]::Min(300, $command.Length)))$(if ($command.Length -gt 300) { '...' })"
$reason = $reasonLines -join "`n"

$decision = @{
    hookSpecificOutput = @{
        permissionDecision = "ask"
        permissionDecisionReason = $reason
    }
} | ConvertTo-Json -Compress

Write-Output $decision
exit 0
