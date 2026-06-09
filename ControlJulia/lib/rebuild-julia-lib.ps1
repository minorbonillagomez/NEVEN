$dumpFile = Join-Path $PSScriptRoot "libjulia.def.txt"
$defFile = Join-Path $PSScriptRoot "libjulia.def"
$libFile = Join-Path $PSScriptRoot "libjulia.lib"

$dump = Get-Content $dumpFile -Raw
$dump = ($dump -replace "(?s)^.*ordinal.*?\n", "")
$dump = ($dump -replace "(?s)\n\s*Summary.*?$", "")
$dump = ($dump -replace "(?m)^\s+\S+\s+\S+\s+\S+\s+", "")

$content = "LIBRARY libjulia`nEXPORTS`n`n$dump`n"
$content | Out-File -Encoding ASCII $defFile

Write-Host "Generated: $defFile"
Write-Host "Now run: lib /machine:X64 /def:libjulia.def /out:libjulia.lib"
