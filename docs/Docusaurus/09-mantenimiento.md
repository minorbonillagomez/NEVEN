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

## 9.3 Solucion de problemas

| Problema | Solucion |
|:---|:---|
| `#NOMBRE?` en todas las funciones | XLL no cargado --> Archivo --> Opciones --> Complementos |
| Ribbon no aparece | `regsvr32 C:\NEVEN\NEVENRibbon.dll` + limpiar resiliency |
| Excel se congela | `Stop-Process -Name "EXCEL","ControlR","ControlJulia" -Force` |
| Paquete R faltante | `=NEVEN.r("install.packages('nombre')")` |
| Julia exception | Verificar datos del rango (tipos numericos) |
| Pluto no abre | Matar procesos Julia: `Stop-Process -Name "julia" -Force` |

## 9.4 Archivos clave del codigo fuente

| Archivo | Responsabilidad |
|:---|:---|
| `RJ2XCL/src/rj2xcl.cc` | Singleton principal, Init, xlAutoOpen |
| `RJ2XCL/src/basic_functions.cc` | ~200 funciones exportadas |
| `RJ2XCL/src/language_service.cc` | Comunicacion con ControlR/Julia |
| `Common/ViewerManager.cc` | WebView2 lifecycle |
| `Common/PlutoManager.cc` | Pluto.jl lifecycle |
| `Common/ConfigService.cc` | Configuracion centralizada |
| `Common/SandboxVerifier.cc` | Validacion de seguridad |
| `Ribbon/ribbon_connect.h` | Ribbon COM callbacks |
| `startup/startup.jl` | Modulo NEVEN Julia |
| `libreria/JULIA/functions.jl` | Funciones Julia (9 modulos + aliases) |

## 9.5 Fixes criticos (no revertir)

| Fix | Archivo | Impacto si se revierte |
|:---|:---|:---|
| Firma MdCallBack12 | `xlcall_stubs.cc` | Todas las llamadas a Excel API fallan |
| Complex.h para MSVC | `ControlR/include/R_ext/Complex.h` | ControlR.exe crashea |
| thread_local XLOPER12 | `basic_functions.cc` | Corrupcion en recalculo paralelo |
| Startup wait=true | `language_service.cc` | Pipe se desincroniza |
| CharacterMode=LinkDLL | `rinterface_win.cc` | ControlR crashea sin consola |
