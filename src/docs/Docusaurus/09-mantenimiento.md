---
id: mantenimiento
title: Capitulo 9 -- Mantenimiento
sidebar_label: 9. Mantenimiento
sidebar_position: 9
---

# Capitulo 9: Mantenimiento y Desarrollo

## 9.1 Compilacion del proyecto

### Requisitos
- Visual Studio 2022 (con "Desarrollo de escritorio con C++")
- CMake 3.15+ (incluido con VS 2022)
- R 4.4.1+ y Julia 1.12.6+ instalados

### Comandos de build

```powershell
# Build completo limpio (recomendado)
powershell -ExecutionPolicy Bypass -File build.ps1 -Clean -Config Release

# O usando CMake directamente:
cmake -S . -B Build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
cmake --build Build --config Release

# Compilar componentes individuales:
cmake --build Build --config Release --target NEVEN_Core       # XLL
cmake --build Build --config Release --target ControlJulia     # Julia
cmake --build Build --config Release --target ControlR         # R
cmake --build Build --config Release --target ControlPython    # Python
```

### Regenerar libjulia.lib (si Julia se actualiza)

```powershell
cd ControlJulia\lib
.\rebuild-julia-lib.ps1
lib /machine:X64 /def:libjulia.def /out:libjulia.lib
```

> **CRITICO:** Usar el metodo exacto del script `rebuild-julia-lib.ps1`. Otros metodos de parsing producen un `.lib` que compila pero crashea en runtime.

### Despliegue

```powershell
Stop-Process -Name "EXCEL","ControlR","ControlJulia","ControlPython" -Force -ErrorAction SilentlyContinue
taskkill /F /IM msedgewebview2.exe 2>$null
Start-Sleep -Seconds 3

Copy-Item "Build\Core\Release\NEVEN64.dll" "C:\NEVEN\NEVEN64.xll" -Force
Copy-Item "Build\ControlR\Release\ControlR.exe" "C:\NEVEN\ControlR.exe" -Force
Copy-Item "Build\ControlJulia\Release\ControlJulia.exe" "C:\NEVEN\ControlJulia.exe" -Force
Copy-Item "Build\ControlPython\Release\ControlPython.exe" "C:\NEVEN\ControlPython.exe" -Force
Copy-Item "Build\Ribbon\Release\NEVENRibbon.dll" "C:\NEVEN\NEVENRibbon.dll" -Force
regsvr32 /s "C:\NEVEN\NEVENRibbon.dll"
```

## 9.2 Agregar funciones de usuario

### Funcion R

Crear archivo `.R` en `%USERPROFILE%\Documents\NEVEN\functions\`:

```r
MiFuncion <- function(datos, parametro = 0) {
  return(sum(datos) * parametro)
}
attr(MiFuncion, "description") <- list(
  "Mi funcion personalizada",
  datos = "Rango de datos",
  parametro = "Multiplicador"
)
```

### Funcion Julia

Agregar al archivo `functions.jl`:

```julia
function MiCalculo(datos, parametro=0)
    return sum(Float64.(datos)) * parametro
end
```

Recargar con el boton **Actualizar** del Ribbon o `=RJ_UpdateFunctions()`.

### Funcion Python

Crear archivo `.py` en `C:\NEVEN\startup\` o en el directorio de funciones de usuario.

```python
def mi_funcion(datos, parametro=0):
    """Mi funcion personalizada de Python."""
    import numpy as np
    return float(np.sum(datos) * parametro)
```

La funcion queda disponible en Excel como:

```excel
=NEVEN.p("mi_funcion", A1:A10, 2.5)
```

> **Sin reinicio:** Los cambios a funciones Python se aplican al reiniciar ControlPython. Desde NEVEN Studio: *Configuracion → Reiniciar Python*.

## 9.3 Solucion de problemas

| Problema | Solucion |
|:---|:---|
| `#NOMBRE?` en todas las funciones | XLL no cargado --> Archivo --> Opciones --> Complementos |
| Ribbon no aparece | `regsvr32 C:\NEVEN\NEVENRibbon.dll` + limpiar resiliency |
| Excel se congela | `Stop-Process -Name "EXCEL","ControlR","ControlJulia","ControlPython" -Force` |
| Paquete R faltante | `=NEVEN.r("install.packages('nombre')")` |
| Julia exception | Verificar datos del rango (tipos numericos) |
| Pluto no abre | Matar procesos Julia: `Stop-Process -Name "julia" -Force` |
| Python no responde | `Stop-Process -Name "ControlPython" -Force` — se reinicia automaticamente |
| Paquete Python faltante | `=NEVEN.py("import subprocess; subprocess.run(['pip','install','paquete'])")` |
| `ModuleNotFoundError` en Python | Python no encontro el paquete — verificar que `pip install` uso el Python correcto |

## 9.4 Archivos clave del codigo fuente

| Archivo | Responsabilidad |
|:---|:---|
| `RJ2XCL/src/rj2xcl.cc` | Singleton principal, Init, xlAutoOpen |
| `RJ2XCL/src/basic_functions.cc` | ~200 funciones exportadas |
| `RJ2XCL/src/language_service.cc` | Comunicacion con ControlR/Julia/Python |
| `Common/ViewerManager.cc` | WebView2 lifecycle |
| `Common/PlutoManager.cc` | Pluto.jl lifecycle |
| `Common/ConfigService.cc` | Configuracion centralizada |
| `Common/SandboxVerifier.cc` | Validacion de seguridad |
| `Ribbon/ribbon_connect.h` | Ribbon COM callbacks |
| `startup/startup.jl` | Modulo NEVEN Julia |
| `startup/startup.r` | Dispatcher R (carga libreria R4XCL) |
| `startup/neven_http_server.py` | Servidor HTTP Studio (puerto 5555) |
| `startup/rag_engine.py` | Motor RAG con DuckDB VSS |
| `startup/ontology_service.py` | Servicio de ontologias YAML |
| `libreria/JULIA/functions.jl` | Funciones Julia (9 modulos + aliases) |
| `libreria/Python/ai_functions.py` | Funciones IA (ai_call, plantillas) |
| `libreria/Python/quarto_functions.py` | Renderizado Quarto via Python |

## 9.5 Fixes criticos (no revertir)

| Fix | Archivo | Impacto si se revierte |
|:---|:---|:---|
| Firma MdCallBack12 | `xlcall_stubs.cc` | Todas las llamadas a Excel API fallan |
| Complex.h para MSVC | `ControlR/include/R_ext/Complex.h` | ControlR.exe crashea |
| thread_local XLOPER12 | `basic_functions.cc` | Corrupcion en recalculo paralelo |
| Startup wait=true | `language_service.cc` | Pipe se desincroniza |
| CharacterMode=LinkDLL | `rinterface_win.cc` | ControlR crashea sin consola |

## 9.6 NEVEN Studio — despliegue de cambios

Los archivos del Studio son Python/HTML — no requieren recompilar C++. Basta con:

```powershell
# 1. Detener ControlPython
Get-Process | Where-Object { $_.Name -match "ControlPython" } | Stop-Process -Force

# 2. Copiar archivos actualizados
$src = "f:\ANTIGRAVITY\2026\NEVEN\NEVEN"
Copy-Item "$src\ControlPython\startup\neven_http_server.py" "C:\NEVEN\startup\" -Force
Copy-Item "$src\ControlPython\startup\datalab_handler.py"  "C:\NEVEN\startup\" -Force
Copy-Item "$src\TaskPane\taskpane.html"                     "C:\NEVEN\taskpane\" -Force
Copy-Item "$src\TaskPane\datalab.js"                        "C:\NEVEN\taskpane\" -Force

# 3. Reiniciar: doble clic en "NEVEN Studio.vbs"
```

## 9.7 Data Lab — agregar función al catálogo

Para agregar una función al catálogo Data Lab se necesitan dos archivos:

**1. Wrapper R** (en `NEVEN/libreria/R/` y luego copiar a `C:\NEVEN\functions\`):

```r
MiFuncion.Studio <- function(data_X, K = 3L) {
  resultado <- list(tabla = mi_analisis(data_X))
  tier_map  <- c(tabla = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
```

**1b. Wrapper Python** (alternativa — en `NEVEN/libreria/Python/` y copiar a `C:\NEVEN\startup\`):

```python
def MiFuncion_Studio(data_X, K=3):
    """Wrapper Python para Data Lab."""
    import numpy as np
    resultado = mi_analisis(data_X, K)
    return [
        {"name": "tabla", "label": "Resultado", "type": "table",
         "value": resultado, "tier": 1}
    ]
```

Para usar Python en el sidecar, cambiar `"languages": ["r"]` → `"languages": ["python"]` y ajustar `"file"` y `"function_name"`.

**2. Sidecar JSON** (en `NEVEN/Install/functions/` y copiar a `C:\NEVEN\functions\`):

```r
MiFuncion.Studio <- function(data_X, K = 3L) {
  resultado <- list(tabla = mi_analisis(data_X))
  tier_map  <- c(tabla = 1L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
```

**2. Sidecar JSON** (en `NEVEN/Install/functions/` y copiar a `C:\NEVEN\functions\`):

```json
{
  "id": "MiFuncion", "family": "UC", "family_label": "Mis Funciones",
  "name": "Mi Función", "description": "Descripción breve.",
  "languages": ["r"], "function_name": "MiFuncion.Studio", "file": "MiFuncion.Studio.R",
  "variable_roles": { "X": { "label": "Variables", "types": ["numeric"], "multiple": true, "required": true } },
  "parameters": [ { "name": "K", "label": "K clusters", "type": "integer", "default": 3, "tier": 1 } ]
}
```

Reiniciar NEVEN Studio — el catálogo se actualiza automáticamente al llamar `GET /api/datalab/catalog`.

> **Nota:** Cambios a `r_object_to_slots.R` requieren reiniciar `ControlR.exe` para tener efecto.

## 9.8 Solución de problemas — Studio y Data Lab

| Problema | Solución |
|:---|:---|
| Studio no abre | `tasklist \| findstr ControlPython` — verificar que el proceso existe |
| Data Lab muestra "no disponible" (503) | `datalab_handler.py` no encontrado en `C:\NEVEN\startup\` |
| Catálogo vacío | Verificar JSONs en `C:\NEVEN\functions\` y revisar `warnings` en la respuesta del catálogo |
| Función retorna slots vacíos | `r_object_to_slots.R` no cargado — verificar `startup.r` |
| Error 400 en filtro WHERE | SQL inválido — el mensaje de error DuckDB aparece en Results Panel |
| Resumen IA ausente | LMStudio apagado o `AI.enabled=false` en `neven-config.json` |
| Puerto 5555 ocupado | Cambiar puerto en `start_studio.py` |
| Wrapper Python no encontrado | Verificar que el `.py` esta en `C:\NEVEN\startup\` y que el sidecar usa `"languages": ["python"]` |
| `ImportError` en wrapper Python | Instalar el paquete faltante: `pip install nombre_paquete` en el Python de NEVEN |
| RAG no indexa EPUB | Verificar `pip install ebooklib` en el entorno Python de NEVEN |
