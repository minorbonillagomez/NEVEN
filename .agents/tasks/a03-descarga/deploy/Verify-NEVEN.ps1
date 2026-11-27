$ErrorActionPreference='Continue'
$m=Get-Content -LiteralPath "$PSScriptRoot\manifest.json" -Raw | ConvertFrom-Json
foreach($f in $m.files){ $h=(Get-FileHash -LiteralPath $f.destination -Algorithm SHA256).Hash; "HASH $(if($h -eq $f.sourceSha256){'OK '}else{'BAD'}) $($f.destination)" }
$py = if(Test-Path 'C:\NEVEN\python\python.exe'){'C:\NEVEN\python\python.exe'}else{'python'}
"python=$py"
$p = Start-Process -FilePath $py -ArgumentList '"C:\NEVEN\taskpane\start_studio.py"','--no-browser' -WindowStyle Hidden -PassThru
"launcher pid $($p.Id)"
function Req($method,$url,$hdr,$body){
  $a=@('-k','-s','-o','NUL','-w','%{http_code}','-X',$method)
  foreach($k in $hdr.Keys){ $a+=@('-H',"${k}: $($hdr[$k])") }
  if($body){ $a+=@('-H','Content-Type: application/json','-d',$body) }
  $a+=$url; (& curl.exe @a)
}
$ok=$false
for($i=0;$i -lt 60;$i++){ Start-Sleep 1; $c=Req 'GET' 'https://localhost:5555/health' @{} $null; if($c -eq '200'){$ok=$true;break} }
"health: $c (tras $i s)"
if($ok){
  $html = (& curl.exe -k -s https://localhost:5555/taskpane.html) -join "`n"
  $mm=[regex]::Match($html,'<meta[^>]*name="neven-token"[^>]*content="([^"]*)"|<meta[^>]*content="([^"]*)"[^>]*name="neven-token"')
  $tok=if($mm.Groups[1].Success){$mm.Groups[1].Value}else{$mm.Groups[2].Value}
  "taskpane.html meta neven-token: $($mm.Success) (len $($tok.Length))"
  "taskpane.html script neven-auth.js: $($html -match '<script[^>]*src="[^"]*neven-auth\.js')"
  "neven-auth.js: $(Req 'GET' 'https://localhost:5555/neven-auth.js' @{} $null)"
  $body='{"code":"1+1"}'
  "api/r con token+origin ok: $(Req 'POST' 'https://localhost:5555/api/r' @{'X-NEVEN-Token'=$tok;'Origin'='https://localhost:5555'} $body)"
  "api/r sin token: $(Req 'POST' 'https://localhost:5555/api/r' @{'Origin'='https://localhost:5555'} $body)"
  "api/r origin 5556: $(Req 'POST' 'https://localhost:5555/api/r' @{'X-NEVEN-Token'=$tok;'Origin'='http://localhost:5556'} $body)"
}
# parar arbol
$ids=@($p.Id)
$pp=Get-NetTCPConnection -LocalPort 5555 -State Listen -ErrorAction SilentlyContinue | % OwningProcess
if($pp){$ids+=$pp}
foreach($i in ($ids|Select -Unique)){ & taskkill /F /T /PID $i 2>&1 | Out-Null }
Get-Process -Name ControlR,ControlJulia,ControlPython -ErrorAction SilentlyContinue | % { & taskkill /F /T /PID $_.Id 2>&1 | Out-Null }
Start-Sleep 2
"puerto 5555 libre: $(-not (Get-NetTCPConnection -LocalPort 5555 -ErrorAction SilentlyContinue))"
"procesos restantes: $((Get-Process -Name python,pythonw,ControlR,ControlJulia,ControlPython -ErrorAction SilentlyContinue | % { "$($_.Name)/$($_.Id)" }) -join ',')"
