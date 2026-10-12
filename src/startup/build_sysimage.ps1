# Usar ruta 8.3 (sin espacios) para evitar problemas con PackageCompiler
$julia = (Get-Item "C:\Users\Minor Bonilla G\AppData\Local\Programs\Julia-1.12.6\bin\julia.exe").FullName
$julia83 = (cmd /c "for %I in (`"$julia`") do @echo %~sI").Trim()
$script = "C:\NEVEN\startup\run-sysimage.jl"
$log    = "C:\NEVEN\sysimage_build5.log"

Write-Host "Julia: $julia83"
& $julia83 $script 2>&1 | Tee-Object -FilePath $log
if ($LASTEXITCODE -eq 0) {
    Add-Content $log "BUILD_OK"
} else {
    Add-Content $log "BUILD_FAILED exit=$LASTEXITCODE"
}
