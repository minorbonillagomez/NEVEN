# NEVEN v2.0 -- Guia de Solucion de Problemas

**Universidad de Costa Rica -- Tesis de Maestria**

------------------------------------------------------------------------

## 1. Excel se atascó al abrir

**Sintoma:** Excel no responde al iniciar, se queda en pantalla blanca.

**Causa:** Procesos zombie de una sesion anterior bloquean los Named Pipes.

**Solucion:**
```powershell
# Matar todos los procesos
Stop-Process -Name "EXCEL","ControlR","ControlJulia","julia" -Force -ErrorAction SilentlyContinue
taskkill /F /IM msedgewebview2.exe 2>$null

# Esperar 5 segundos y abrir Excel
Start-Sleep -Seconds 5
```

**Prevencion:** Siempre cerrar Excel normalmente (no forzar cierre). Si Excel se congela, usar el Task Manager para matar EXCEL.EXE primero.

------------------------------------------------------------------------

## 2. El Ribbon NEVEN no aparece

**Sintoma:** La pestana NEVEN no se muestra en la cinta de Excel.

**Causa:** Excel deshabilito el COM Add-in despues de un crash.

**Solucion:**
```powershell
# Limpiar la lista de add-ins deshabilitados
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\CrashingAddinList" -Force -ErrorAction SilentlyContinue

# Verificar que el Ribbon esta habilitado
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect" -Name "LoadBehavior" -Value 3 -Type DWord

# Re-registrar si es necesario
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```

------------------------------------------------------------------------

## 3. Funciones retornan #NOMBRE?

**Sintoma:** `=NEVEN.r("1+1")` o `=J.Algebra(...)` retornan #NOMBRE?.

**Causas posibles:**

**3a. El XLL no esta cargado:**
- Verificar en Archivo --> Opciones --> Complementos que NEVEN64.xll esta activo
- Si no aparece, cargar manualmente: Examinar --> `C:\NEVEN\NEVEN64.xll`

**3b. R o Julia no conectaron:**
- Revisar `C:\NEVEN\neven.log` buscando "Connected 0 language service(s)"
- Verificar que ControlR.exe y ControlJulia.exe existen en `C:\NEVEN\`
- Verificar que R 4.4.1+ y Julia 1.12.6+ estan instalados

**3c. Las funciones de usuario no se cargaron:**
- Ejecutar en VBA: `Application.Run "RJ_UpdateFunctions"`
- Verificar que los archivos .R y .jl estan en `Documents\NEVEN\functions\`

------------------------------------------------------------------------

## 4. Julia retorna "read error"

**Sintoma:** `=NEVEN.j("1+1")` retorna "read error" en lugar del resultado.

**Causa:** Julia no termino de procesar el startup script antes de recibir la llamada.

**Solucion:** Esperar 15 segundos despues de abrir Excel (el timer de recarga diferida necesita tiempo). Si persiste:
- Verificar que `C:\NEVEN\neven_julia.dll` (sysimage) existe
- Sin sysimage, Julia tarda minutos en arrancar via JIT

------------------------------------------------------------------------

## 5. Julia funciones J.Algebra etc. no disponibles

**Sintoma:** `=NEVEN.j("1+1")` funciona pero `=J.Algebra(...)` retorna #NOMBRE?.

**Causa:** El archivo `functions.jl` no se cargo correctamente.

**Solucion:**
1. Verificar que `Documents\NEVEN\functions\functions.jl` existe
2. Verificar que el archivo usa `NEVEN.ListFunctions()` (no `RJ2XCL.ListFunctions()`)
3. Esperar 15 segundos y ejecutar `Application.Run "RJ_UpdateFunctions"`

------------------------------------------------------------------------

## 6. Regenerar la sysimage de Julia

**Cuando:** Despues de actualizar Julia, modificar startup.jl, o si la sysimage se corrompe.

```powershell
# Cerrar Excel primero
Stop-Process -Name "EXCEL","ControlR","ControlJulia","julia" -Force -ErrorAction SilentlyContinue

# Generar sysimage (tarda 5-10 minutos)
$env:NEVEN_HOME = "C:\NEVEN\"
julia "scripts\build-julia-sysimage.jl"
```

**Resultado:** `C:\NEVEN\neven_julia.dll` (~415 MB). Julia arrancara en 1-2 segundos.

------------------------------------------------------------------------

## 7. WebView2 no muestra contenido

**Sintoma:** `=NEVEN.v(...)` retorna "WebView2 not available".

**Causa:** El runtime de WebView2 (Edge Chromium) no esta instalado.

**Solucion:** WebView2 viene preinstalado en Windows 10/11. Si falta:
- Descargar de https://developer.microsoft.com/en-us/microsoft-edge/webview2/

------------------------------------------------------------------------

## 8. R.Pivot o R.D3 no generan visualizacion

**Sintoma:** La formula retorna un path pero el viewer no abre.

**Causa:** Falta envolver con `NEVEN.v()`.

**Correcto:** `=NEVEN.v(R.Pivot(A1:E11, 1))`
**Incorrecto:** `=R.Pivot(A1:E11, 1)` (solo retorna el path del HTML)

------------------------------------------------------------------------

## 9. Paquetes R no instalados

**Sintoma:** R.Pivot retorna error sobre rpivotTable no encontrado.

**Solucion:**
```
=NEVEN.r("install.packages('rpivotTable', repos='https://cran.r-project.org', quiet=TRUE)")
```

Paquetes requeridos por las funciones de visualizacion:
- `rpivotTable` -- para R.Pivot y R.Dashboard
- `plotly` -- para R.GR_PlotlyView
- `htmlwidgets` -- para guardar widgets como HTML
- `jsonlite` -- para R.Esquisse, R.D3, R.Map
- `ggplot2` -- para R.GR_QuickPlot tipos 7-9

------------------------------------------------------------------------

## 10. Despliegue a C:\NEVEN\

**Procedimiento completo:**
```powershell
# 1. Matar procesos
Stop-Process -Name "EXCEL","ControlR","ControlJulia","julia" -Force -ErrorAction SilentlyContinue

# 2. Copiar binarios
Copy-Item "Build\Dist\NEVEN64.xll" "C:\NEVEN\NEVEN64.xll" -Force
Copy-Item "Build\Dist\NEVENRibbon.dll" "C:\NEVEN\NEVENRibbon.dll" -Force
Copy-Item "Build\Dist\ControlR.exe" "C:\NEVEN\ControlR.exe" -Force
Copy-Item "Build\Dist\ControlJulia.exe" "C:\NEVEN\ControlJulia.exe" -Force

# 3. Copiar startup scripts
Copy-Item "startup\startup.r" "C:\NEVEN\startup\startup.r" -Force
Copy-Item "startup\startup.jl" "C:\NEVEN\startup\startup.jl" -Force

# 4. Registrar Ribbon
regsvr32 "C:\NEVEN\NEVENRibbon.dll"

# 5. Abrir Excel
```

------------------------------------------------------------------------

## 11. Archivos de log

| Archivo | Ubicacion | Contenido |
|:---|:---|:---|
| neven.log | C:\NEVEN\ | Log principal del XLL |
| controlcontrolr.log | %TEMP%\ | Log de ControlR.exe |
| controlcontroljulia.log | %TEMP%\ | Log de ControlJulia.exe |

Para ver el log en tiempo real:
```powershell
Get-Content "C:\NEVEN\neven.log" -Wait -Tail 20
```

------------------------------------------------------------------------

*NEVEN v2.0 -- Universidad de Costa Rica -- Tesis de Maestria*


------------------------------------------------------------------------

## NUEVOS (Mayo 2026)

------------------------------------------------------------------------

## N1. Excel se atasca al cargar el XLL (Office WebView2 PreWarm)

**Síntoma:** Excel se congela al cargar NEVEN64.xll. El log muestra que R conecta pero el proceso no avanza.

**Causa:** El Windows Update KB5087051 (13/05/2026) introdujo procesos `msedgewebview2.exe` de Office ("PreWarm Empty Addin", "Storage Service", "Network Service") que consumen CPU y bloquean la inicialización.

**Solución:**
```powershell
# Deshabilitar Office WebView2 PreWarm
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\Common" -Name "StartupBoost" -Value 0 -Type DWord
New-Item -Path "HKCU:\Software\Microsoft\Office\16.0\Wef" -Force
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\Wef" -Name "EnablePreWarm" -Value 0 -Type DWord

# Matar procesos existentes
taskkill /F /IM msedgewebview2.exe
```

------------------------------------------------------------------------

## N2. Julia: funciones J.* muestran error #¡NOMBRE!

**Síntoma:** `=J.JM_Algebra(...)` retorna error de NOMBRE, pero `=NEVEN.j("1+1")` funciona.

**Causa:** Julia usa carga bajo demanda (lazyLoad). Las funciones J.* no se registran hasta que el usuario las activa.

**Solución:**
1. Haga clic en el botón **"Actualizar"** en la pestaña NEVEN del Ribbon (grupo Motores)
2. Espere ~30-60 segundos mientras Julia compila las funciones
3. Las funciones `=J.*` quedarán disponibles

------------------------------------------------------------------------

## N3. R.MR_Binario.C retorna PARSE ERROR con datos categóricos

**Síntoma:** Al usar datos con variables de texto (ej: German Credit), la función retorna PARSE ERROR.

**Causa:** Versiones anteriores requerían `Categorica=1` para datos con texto. La auto-detección resuelve esto automáticamente.

**Solución:**
- Use `Categorica=0` (default) — NEVEN detecta automáticamente las variables categóricas
- Si tiene variables numéricas que representan categorías (ej: 1=Soltero, 2=Casado), use `Categorica=1` para activar el diálogo de selección manual

------------------------------------------------------------------------

## N4. Excel ignora el XLL al cargarlo manualmente

**Síntoma:** Al seleccionar NEVEN64.xll desde Complementos, Excel no lo carga (no aparece error ni funciones).

**Causa:** Excel cachea información del add-in y rechaza silenciosamente un XLL que cambió de tamaño/hash.

**Solución:**
1. Copie el XLL con un nombre diferente: `NEVEN64_v2.xll`
2. Cargue la copia desde Complementos → Examinar
3. O limpie el registro:
```powershell
Remove-Item -Path "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency" -Recurse -Force
```

------------------------------------------------------------------------

## N5. Procesos zombie impiden reiniciar Excel

**Síntoma:** Al cerrar y reabrir Excel, se atasca porque procesos de la sesión anterior siguen activos.

**Solución:**
```powershell
taskkill /F /IM EXCEL.EXE
taskkill /F /IM ControlR.exe
taskkill /F /IM ControlJulia.exe
taskkill /F /IM ControlPython.exe
taskkill /F /IM msedgewebview2.exe
Remove-Item -Path "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency" -Recurse -ErrorAction SilentlyContinue
```
Espere 3 segundos y abra Excel.
