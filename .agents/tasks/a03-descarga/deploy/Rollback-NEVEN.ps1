param([switch]$DryRun,[string]$Manifest="$PSScriptRoot\manifest.json")
$ErrorActionPreference='Stop'
function Fail($m){ Write-Host "ERROR: $m" -ForegroundColor Red; exit 1 }
function Sha($p){ (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }
function Get-StudioProcs {
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ($_.Name -match '^pythonw?(\d+(\.\d+)*)?\.exe$' -and $_.CommandLine -match 'C:\\NEVEN\\taskpane\\start_studio\.py') -or
    ($_.Name -match '^pythonw?(\d+(\.\d+)*)?\.exe$' -and $_.CommandLine -match 'neven_audiobook_server\.py') -or
    ($_.Name -match '^Control(R|Julia|Python)\.exe$' -and $_.ExecutablePath -like 'C:\NEVEN\*')
  }
}
function Stop-Studio([bool]$dry){
  $procs=@(Get-StudioProcs)
  $c=Get-NetTCPConnection -LocalPort 5555 -State Listen -ErrorAction SilentlyContinue
  if($c){ foreach($id in ($c.OwningProcess|Select-Object -Unique)){ if(-not ($procs|Where-Object ProcessId -eq $id)){ Fail "El puerto 5555 lo usa el PID $id, que no es el servidor NEVEN Studio (start_studio.py). No se toca." } } }
  if(-not $procs){ Write-Host '[server] ningun proceso de NEVEN Studio ni del servidor de audiolibros activo' ; return }
  foreach($p in $procs){ Write-Host "[server] detener PID $($p.ProcessId) $($p.Name): $($p.CommandLine)"; if(-not $dry){ Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } }
  if(-not $dry){
    $i=0; while(((@(Get-StudioProcs).Count -gt 0) -or (Get-NetTCPConnection -LocalPort 5555 -State Listen -ErrorAction SilentlyContinue)) -and $i -lt 20){ Start-Sleep -Milliseconds 500; $i++ }
    if(@(Get-StudioProcs).Count -gt 0 -or (Get-NetTCPConnection -LocalPort 5555 -State Listen -ErrorAction SilentlyContinue)){ Fail 'El servidor no se detuvo.' }
    Write-Host '[server] detenidos, puerto 5555 libre' -ForegroundColor Green
  }
}
$m=Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$root=$m.prodRoot.TrimEnd('\'); $bk=$m.backupDir
if($DryRun){Write-Host '== DRY RUN: no se modifica nada ==' -ForegroundColor Yellow}
if(-not (Test-Path -LiteralPath $bk)){ if($DryRun){Write-Host "AVISO: backup aun no existe (se crea en el despliegue real): $bk" -ForegroundColor Yellow}else{Fail "No existe el backup $bk"} }
if(Get-Process -Name EXCEL -ErrorAction SilentlyContinue){ if($DryRun){Write-Host 'AVISO: Excel esta abierto (en real se negaria).' -ForegroundColor Yellow}else{Fail 'Excel esta abierto. Cierrelo.'} }
foreach($f in $m.files){   # comprobar antes de tocar nada
  if(-not $f.destination.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase) -or $f.destination -ieq "$root\neven-config.json"){ Fail "Destino no permitido: $($f.destination)" }
  $rel=$f.destination.Substring($root.Length+1); $bp=Join-Path $bk $rel
  if($null -ne $f.destSha256Current -and -not $DryRun){
    if(-not (Test-Path -LiteralPath $bp)){ Fail "Falta copia: $bp" }
    if((Sha $bp) -ne $f.destSha256Current){ Fail "Copia corrupta: $bp" }
  }
}
Stop-Studio ([bool]$DryRun)
foreach($f in $m.files){
  $rel=$f.destination.Substring($root.Length+1); $bp=Join-Path $bk $rel
  if($null -eq $f.destSha256Current){
    Write-Host "[delete] $($f.destination) (no existia antes)"
    if(-not $DryRun){ if(Test-Path -LiteralPath $f.destination){ Remove-Item -LiteralPath $f.destination -Force }; if(Test-Path -LiteralPath $f.destination){ Fail "No se pudo borrar $($f.destination)" } }
  } else {
    Write-Host "[restore] $bp -> $($f.destination)"
    if(-not $DryRun){
      [IO.File]::Copy($bp,$f.destination,$true)
      if((Sha $f.destination) -ne $f.destSha256Current){ Fail "Hash tras restaurar distinto: $($f.destination)" }
    }
  }
}
foreach($p in $m.cleanPycache){ Write-Host "[pycache] $p"; if(-not $DryRun -and (Test-Path -LiteralPath $p)){ Remove-Item -LiteralPath $p -Recurse -Force } }
if($DryRun){Write-Host 'DRY RUN completado.' -ForegroundColor Yellow}else{Write-Host 'Rollback completado y verificado por hash.' -ForegroundColor Green}