<#
.SYNOPSIS
    Deploys user-facing documentation to Documents\NEVEN\docs\

.DESCRIPTION
    Copies the 10 selected documentation files to the user's NEVEN docs folder.
    Called by Install-NEVEN.ps1 during Phase 5 (User Setup) or can be run standalone.

.EXAMPLE
    .\Deploy-UserDocs.ps1
    .\Deploy-UserDocs.ps1 -SourceDir ".\docs"
#>
param(
    [string]$SourceDir = (Join-Path $PSScriptRoot '..\docs'),
    [string]$TargetDir = (Join-Path $env:USERPROFILE 'Documents\NEVEN\docs')
)

# Create target directory
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Host "  Created: $TargetDir" -ForegroundColor Green
}

# List of documents to deploy (source path relative to docs/)
$documents = @(
    @{ Source = "ANTES_DE_INICIAR.md";                    Desc = "Guia de primer uso" },
    @{ Source = "NAMING-ESP.md";                          Desc = "Nomenclatura del proyecto" },
    @{ Source = "Mantenimiento\TROUBLESHOOTING.md";       Desc = "Solucion de problemas" },
    @{ Source = "Estado\Estado_del_arte.md";              Desc = "Catalogo y comparacion" },
    @{ Source = "Evaluaciones\Evaluacion_objetiva.md";    Desc = "Evaluacion tecnica" },
    @{ Source = "Evaluaciones\Evaluacion_comercial.md";   Desc = "Evaluacion comercial" },
    @{ Source = "Evaluaciones\Evaluacion_doctoral.md";    Desc = "Evaluacion academica" },
    @{ Source = "Evaluaciones\Evaluacion_OWASP.md";       Desc = "Evaluacion de seguridad" },
    @{ Source = "neven-docs.html";                        Desc = "Documentacion completa (12 capitulos)" }
)

# Also check for DICCIONARIO_FUNCIONES.md in multiple possible locations
$diccionario = @("DICCIONARIO_FUNCIONES.md", "Estado\DICCIONARIO_FUNCIONES.md", "Contexto\DICCIONARIO_FUNCIONES.md")
foreach ($d in $diccionario) {
    if (Test-Path (Join-Path $SourceDir $d)) {
        $documents += @{ Source = $d; Desc = "Diccionario de funciones (95 funciones)" }
        break
    }
}

# Copy each document
$copied = 0
foreach ($doc in $documents) {
    $src = Join-Path $SourceDir $doc.Source
    if (Test-Path $src) {
        $destName = Split-Path $doc.Source -Leaf
        $dest = Join-Path $TargetDir $destName
        Copy-Item $src $dest -Force
        Write-Host "  [OK] $destName - $($doc.Desc)" -ForegroundColor White
        $copied++
    } else {
        Write-Host "  [!!] $($doc.Source) - no encontrado" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "  $copied documentos desplegados en: $TargetDir" -ForegroundColor Green
Write-Host ""
