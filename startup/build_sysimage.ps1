$julia = "C:\Users\Minor Bonilla G\AppData\Local\Programs\Julia-1.12.6\bin\julia.exe"
$script = "C:\NEVEN\startup\run-sysimage.jl"
$log = "C:\NEVEN\sysimage_build5.log"

& $julia $script 2>&1 | Tee-Object -FilePath $log
if ($LASTEXITCODE -eq 0) {
    Add-Content $log "BUILD_OK"
} else {
    Add-Content $log "BUILD_FAILED exit=$LASTEXITCODE"
}
