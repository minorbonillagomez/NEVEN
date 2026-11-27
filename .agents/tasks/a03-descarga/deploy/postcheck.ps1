$ErrorActionPreference = 'Continue'
if (Get-Process -Name EXCEL -ErrorAction SilentlyContinue) { "ABORTA: Excel abierto"; return }
$py = if (Test-Path 'C:\NEVEN\python\python.exe') { 'C:\NEVEN\python\python.exe' } else { (Get-Command python).Source }
if (-not (Get-NetTCPConnection -LocalPort 5555 -State Listen -ErrorAction SilentlyContinue)) {
  Start-Process -FilePath $py -ArgumentList @('"C:\NEVEN\taskpane\start_studio.py"','--no-browser') -WindowStyle Hidden | Out-Null
}
$code = '000'
foreach ($i in 1..40) { Start-Sleep -Seconds 1; $code = curl.exe -s -o NUL -w "%{http_code}" --max-time 3 https://localhost:5555/health; if ($code -eq '200') { break } }
"1) https 5555 /health -> $code"
$html = (curl.exe -s --max-time 8 https://localhost:5555/taskpane.html) -join "`n"
$tok = ([regex]::Match($html, 'name="neven-token" content="([^"]+)"')).Groups[1].Value
"   secreto en la pagina: $([bool]$tok)"

# arrancar el servidor de audiolibros como lo hace el boton de la pestana
$st = curl.exe -s -o NUL -w "%{http_code}" --max-time 30 -X POST -H 'Content-Type: application/json' -H 'Origin: https://localhost:5555' -H "X-NEVEN-Token: $tok" -d '{}' https://localhost:5555/api/audiobook/start
"2) POST /api/audiobook/start con secreto -> $st"
$l = $null
foreach ($i in 1..30) { Start-Sleep -Seconds 1; $l = Get-NetTCPConnection -LocalPort 5557 -State Listen -ErrorAction SilentlyContinue; if ($l) { break } }
if ($l) { "3) 5557 escucha en: $(($l | ForEach-Object LocalAddress | Sort-Object -Unique) -join ', ')" } else { "3) 5557 NO escucha" }
"   5556 escucha: $([bool](Get-NetTCPConnection -LocalPort 5556 -State Listen -ErrorAction SilentlyContinue))"

if ($l) {
  "4) audiolibros sin secreto (POST /api/config) -> $(curl.exe -s -o NUL -w '%{http_code}' --max-time 8 -X POST -H 'Content-Type: application/json' -H 'Origin: https://localhost:5555' -d '{}' http://127.0.0.1:5557/api/config)"
  "   audiolibros con Origin ajeno -> $(curl.exe -s -o NUL -w '%{http_code}' --max-time 8 -X POST -H 'Content-Type: application/json' -H 'Origin: http://evil.example' -H "X-NEVEN-Token: $tok" -d '{}' http://127.0.0.1:5557/api/config)"
  "   CORS comodin en respuesta: $([bool]((curl.exe -s -D - -o NUL --max-time 8 -H 'Origin: http://evil.example' http://127.0.0.1:5557/ ) -match 'Access-Control-Allow-Origin: \*'))"
}
"5) servidor principal sin secreto -> $(curl.exe -s -o NUL -w '%{http_code}' --max-time 8 -X POST -H 'Content-Type: application/json' -H 'Origin: https://localhost:5555' -d '{\"code\":\"1+1\"}' https://localhost:5555/api/r)"
"(los servidores quedan en marcha para la prueba del usuario)"
