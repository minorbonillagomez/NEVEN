param([switch]$DryRun,[string]$Manifest="$PSScriptRoot\manifest.json",[string]$ApprovalMessage='')
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
function Test-Approval([string]$t){
  if([string]::IsNullOrWhiteSpace($t)){ return $false }
  $t=$t.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD) -replace '\p{M}',''
  if($t -match '\b(no\s+(apruebo|aprobado|confirmo|confirmado|autorizo|lances|despliegues|ejecutes)|rechaz\w*|cancel\w*|deny|denied|reject\w*|not\s+approved|do\s+not|don''t|detente|esperar?|wait|stop|negativo|abort\w*)\b'){ return $false }
  return ($t -match '\b(aprobad[oa]s?|apruebo|aprobar|confirmad[oa]s?|confirmo|autoriz\w+|adelante|procede\w*|lanza\w*|dale|approved?|confirmed?|proceed|go\s+ahead|ok|si|yes)\b')
}
$m=Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
$root=$m.prodRoot.TrimEnd('\'); $bk=$m.backupDir
if($DryRun){Write-Host '== DRY RUN: no se modifica nada ==' -ForegroundColor Yellow}
# 0. Aprobacion (mensaje reenviado por el orquestador, lenguaje natural)
$ok=Test-Approval $ApprovalMessage
if(-not $DryRun -and -not $ok){ Fail 'Falta aprobacion afirmativa: pase el mensaje del usuario en -ApprovalMessage.' }
Write-Host "[aprobacion] mensaje='$ApprovalMessage' -> $(if($ok){'afirmativo'}else{'NO afirmativo (en real se negaria)'})"
# 1. Excel
if(Get-Process -Name EXCEL -ErrorAction SilentlyContinue){ if($DryRun){Write-Host 'AVISO: Excel esta abierto (en real se negaria).' -ForegroundColor Yellow}else{Fail 'Excel esta abierto. Cierrelo.'} }
# 2. Precondiciones
if(-not $DryRun -and (Test-Path -LiteralPath $bk)){ Fail "La carpeta de backup ya existe: $bk" }
if($DryRun -and (Test-Path -LiteralPath $bk)){ Write-Host "AVISO: la carpeta de backup ya existe (en real se negaria): $bk" -ForegroundColor Yellow }
foreach($f in $m.files){
  if(-not (Test-Path -LiteralPath $f.source)){ Fail "Falta origen $($f.source)" }
  if((Sha $f.source) -ne $f.sourceSha256){ Fail "Hash de origen distinto al manifiesto: $($f.source)" }
  if($f.source -match '\.py$'){ $b=[IO.File]::ReadAllBytes($f.source); if($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF){ Fail "El .py de origen tiene BOM UTF-8: $($f.source)" } }
  $ex2=Test-Path -LiteralPath $f.destination
  if($ex2 -and $null -eq $f.destSha256Current){ Fail "Destino existe pero el manifiesto dice que no: $($f.destination)" }
  if(-not $ex2 -and $null -ne $f.destSha256Current){ Fail "Destino no existe pero el manifiesto dice que si: $($f.destination)" }
  if($ex2 -and (Sha $f.destination) -ne $f.destSha256Current){ Fail "Destino cambio desde el manifiesto (regenerar): $($f.destination)" }
  if(-not $f.destination.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){ Fail "Destino fuera de $root : $($f.destination)" }
  if($f.destination -ieq "$root\neven-config.json"){ Fail 'neven-config.json no se puede desplegar.' }
}
# 3. Detener servidor NEVEN Studio
Stop-Studio ([bool]$DryRun)
# 4. Backup nuevo verificado por hash
foreach($f in $m.files){
  $rel=$f.destination.Substring($root.Length+1); $bp=Join-Path $bk $rel
  if($null -eq $f.destSha256Current){ Write-Host "[backup] (nuevo, sin copia) $rel"; continue }
  Write-Host "[backup] $($f.destination) -> $bp"
  if($DryRun){continue}
  [IO.Directory]::CreateDirectory((Split-Path $bp -Parent)) | Out-Null
  [IO.File]::Copy($f.destination,$bp,$false)
  if((Sha $bp) -ne $f.destSha256Current){ Fail "Backup infiel: $bp. No se ha copiado nada a produccion." }
}
if(-not $DryRun){ Write-Host "Backup verificado en $bk" -ForegroundColor Green }
# 5. Copia
foreach($f in $m.files){
  Write-Host "[copy] $($f.source) -> $($f.destination)"
  if($DryRun){continue}
  try{ [IO.File]::Copy($f.source,$f.destination,$true) }catch{ Fail "Copia fallida $($f.destination): $($_.Exception.Message). Ejecute Rollback-NEVEN.ps1." }
  if((Sha $f.destination) -ne $f.sourceSha256){ Fail "Hash de destino distinto tras copiar: $($f.destination). Ejecute Rollback-NEVEN.ps1." }
}
# 6. __pycache__
foreach($p in $m.cleanPycache){ Write-Host "[pycache] $p"; if(-not $DryRun -and (Test-Path -LiteralPath $p)){ Remove-Item -LiteralPath $p -Recurse -Force } }
if($DryRun){Write-Host 'DRY RUN completado: sin errores.' -ForegroundColor Yellow}else{Write-Host 'Despliegue completado y verificado por hash. Reinicie servidor (start_studio.py) y Excel; el servidor de audiolibros lo arranca el boton de la pestana (puerto 5557); para deshacer: Rollback-NEVEN.ps1.' -ForegroundColor Green}