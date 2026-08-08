# Guía de Actualización de Motores — NEVEN

> **Versión:** 2026-08-07
> **Aplica a:** NEVEN v2.3.2+
> **Audiencia:** Usuario final, investigador, administrador de NEVEN

---

## Resumen rápido

NEVEN integra tres motores de lenguaje (R, Julia, Python). Cada uno puede actualizarse de forma **independiente** sin necesidad de recompilar el sistema, con los matices indicados en este documento.

| Motor | Gestor recomendado | Comando de actualización | Requiere acción post-actualización |
|:---|:---|:---|:---|
| R | winget | `winget upgrade --id RProject.R` | Ninguna — automático |
| Julia | juliaup | `juliaup update` | Reconstruir sysimage (opcional) |
| Python | winget | `winget upgrade --id Python.Python.3.13` | Ninguna — automático |

---

## 1. Actualizar R

### Procedimiento

```powershell
winget upgrade --id RProject.R
```

### Cómo verificar en Excel

```excel
=NEVEN.R("R.version.string")
```
Retorna algo como: `"R version 4.6.1 (2025-09-12)"`

### Notas técnicas

- NEVEN detecta automáticamente la versión de R instalada mediante el registro de Windows.
- ControlR.exe utiliza carga dinámica de `R.dll` — funciona con cualquier versión R 3.5+.
- No se requiere recompilar ni cambiar ningún archivo de configuración.
- Si `R.home` en `neven-config.json` está en blanco (`""`), NEVEN usa la versión más reciente detectada.

### Configuración manual (opcional)

Si se tienen varias versiones de R instaladas y se quiere forzar una específica, editar `C:\NEVEN\neven-config.json`:

```json
"R": {
  "home": "C:\\Program Files\\R\\R-4.6.1",
  ...
}
```

Dejar `"home": ""` para detección automática.

---

## 2. Actualizar Julia

### Procedimiento

```powershell
# Con juliaup (recomendado):
juliaup update

# Sin juliaup — instalador manual desde:
# https://julialang.org/downloads/
```

### Cómo verificar en Excel

```excel
=NEVEN.J("string(VERSION)")
```
Retorna algo como: `"1.12.6"`

### Notas técnicas

- Después de actualizar Julia, NEVEN detecta automáticamente que la sysimage (`neven_julia.dll`) fue compilada con una versión anterior y usa **init estándar** (JIT). No ocurre ningún crash.
- El **primer cálculo Julia** por sesión tardará 1-5 minutos mientras el JIT compila las funciones. Los cálculos siguientes son instantáneos.
- Para eliminar ese retraso, reconstruir la sysimage (ver sección 2.1).

### 2.1 Reconstruir la sysimage después de actualizar Julia

La sysimage precalcula el JIT y elimina el retraso del primer uso. Es **opcional** pero recomendada.

**Opción A — Botón del Ribbon (más fácil):**
1. Ribbon NEVEN → grupo **Notebooks** → botón **Sysimage**
2. Confirmar el diálogo → esperar 5-10 minutos → reiniciar Excel

**Opción B — Línea de comandos:**
```powershell
$env:NEVEN_HOME = "C:\NEVEN\"
julia "C:\NEVEN\startup\build-julia-sysimage.jl"
# Al terminar, reiniciar Excel
```

La sysimage nueva quedará en `C:\NEVEN\neven_julia.dll` y se activará automáticamente la próxima vez que abra Excel.

---

## 3. Actualizar Python

### Procedimiento

```powershell
winget upgrade --id Python.Python.3.13
```

### Cómo verificar en Excel

```excel
=NEVEN.P("sys.version")
```
Retorna algo como: `"3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, ...) [MSC ...]"`

### Notas técnicas

- NEVEN usa la **Stable ABI** de Python (`python3.dll`) — compatible con cualquier versión Python 3.10+.
- ControlPython.exe no requiere recompilación al actualizar Python.
- Si Python está en una ruta no estándar, configurar en `neven-config.json`:

```json
"Python": {
  "home": "C:\\Users\\Usuario\\AppData\\Local\\Programs\\Python\\Python313",
  ...
}
```

Dejar `"home": ""` para detección automática.

---

## 4. Instalar paquetes R

Para instalar paquetes R adicionales que sus funciones requieran:

```excel
=NEVEN.R("install.packages('nombre_paquete')")
```

O desde la consola R del Ribbon: **Motores → Consola → tab R**.

Los paquetes que NEVEN usa internamente (plm, AER, sandwich, vars, etc.) están preinstalados en la librería de NEVEN.

---

## 5. Instalar paquetes Julia

```excel
=NEVEN.J("import Pkg; Pkg.add(\"NombrePaquete\")")
```

O en la consola Julia del Ribbon.

**Nota:** Si instala paquetes nuevos, la sysimage quedará desactualizada. Reconstruirla con el botón **Sysimage** del Ribbon para que los nuevos paquetes tengan startup rápido.

---

## 6. Instalar paquetes Python

```excel
=NEVEN.P("import subprocess; subprocess.run(['pip', 'install', 'nombre_paquete'])")
```

O desde la consola del sistema:

```powershell
pip install nombre_paquete
```

---

## 7. Verificar estado de todos los motores

```excel
=NEVEN.status()
```

Retorna un resumen de conexión, versión y funciones registradas de los 3 motores.

---

## 8. Solución de problemas comunes

### Excel se congela al cargar NEVEN

1. Cerrar Excel completamente
2. En PowerShell:
   ```powershell
   taskkill /F /IM ControlR.exe /T
   taskkill /F /IM ControlJulia.exe /T
   taskkill /F /IM ControlPython.exe /T
   ```
3. Limpiar el registro de add-ins problemáticos:
   ```powershell
   Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\StartupItems" -Force -ErrorAction SilentlyContinue
   ```
4. Abrir Excel de nuevo

### Julia muy lenta en el primer cálculo

Normal — es el JIT compilando. Solución: reconstruir sysimage con el botón **Sysimage** del Ribbon.

### Julia crashea al cargar

La sysimage es incompatible con la versión de Julia instalada. NEVEN lo detecta y usa init estándar automáticamente. Si el crash persiste:

```powershell
# Desactivar la sysimage manualmente:
Rename-Item "C:\NEVEN\neven_julia.dll" "C:\NEVEN\neven_julia.dll.bak"
```

Luego reconstruirla con el botón del Ribbon.

### Error "motor no disponible" en Excel

El proceso hijo (ControlR/Julia/Python) no inició correctamente. Verificar:

```powershell
# Ver logs:
Get-Content "$env:TEMP\controlcontrolr.log" -Tail 20
Get-Content "$env:TEMP\controlcontroljulia.log" -Tail 20
```

---

## 9. Respaldar la instalación antes de actualizar

Si prefiere tener un punto de retorno antes de actualizar:

```powershell
# Respaldar los ejecutables actuales
Copy-Item "C:\NEVEN\ControlR.exe" "C:\NEVEN\ControlR.exe.bak"
Copy-Item "C:\NEVEN\ControlJulia.exe" "C:\NEVEN\ControlJulia.exe.bak"
Copy-Item "C:\NEVEN\NEVEN64.xll" "C:\NEVEN\NEVEN64.xll.bak"
```

Para restaurar, simplemente revertir los nombres.

---

*NEVEN — Universidad de Costa Rica · Maestría en Matemática Aplicada · Minor Bonilla Gómez*
