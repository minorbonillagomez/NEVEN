# 03 — Exclusiones Justificadas de la Auditoría

## Resumen

Este documento identifica y justifica todos los archivos y directorios excluidos del análisis de auditoría del proyecto NEVEN. Cada exclusión está categorizada y documentada con su justificación correspondiente.

### Categorías de Exclusión

| Categoría | Descripción | Archivos |
|-----------|-------------|----------|
| **BINARIO** | Archivos binarios compilados no legibles como texto | ~200+ |
| **GENERADO** | Código auto-generado por herramientas (protoc, Doxygen) | ~442 |
| **TERCEROS** | Dependencias de terceros no desarrolladas por el proyecto | ~1,795 |
| **OTRO** | Artefactos de build, caché, logs de compilación | ~2,193 |

**Total estimado de archivos excluidos: ~4,630+**

---

## 1. Directorio Build/ (OTRO)

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Build/` (directorio completo) | OTRO | Directorio de salida de CMake. Contiene 2,193 archivos generados durante la compilación: objetos (.obj), ejecutables (.exe), bibliotecas (.lib/.dll), archivos de solución VS (.sln, .vcxproj), logs de compilación (.tlog), caché de CMake y distribuciones empaquetadas. No es código fuente. |

### Contenido relevante del directorio Build/:

| Subdirectorio | Contenido | Archivos |
|---------------|-----------|----------|
| `Build/_deps/` | Dependencias descargadas por FetchContent (protobuf, googletest, webview2) | ~1,763 |
| `Build/Common/` | Objetos compilados de Common.lib | ~40 |
| `Build/Core/` | Objetos y DLL de NEVEN_Core | ~25 |
| `Build/ControlR/` | Objetos y EXE de ControlR | ~15 |
| `Build/ControlJulia/` | Objetos y EXE de ControlJulia | ~12 |
| `Build/ControlPython/` | Objetos y EXE de ControlPython | ~10 |
| `Build/PB/` | Objetos de Protocol Buffers | ~5 |
| `Build/Dist/` | Distribuciones empaquetadas | ~10 |
| `Build/Dist_STABLE_*/` | Snapshots de distribuciones estables | ~10 |
| `Build/CMakeFiles/` | Archivos internos de CMake | ~50 |
| `Build/*.tlog` | Logs de compilación MSVC | ~100+ |

---

## 2. Archivos Binarios Individuales (BINARIO)

### 2.1 Bibliotecas de importación de R (ControlR/lib/)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `ControlR/lib/R64.exp` | .exp | BINARIO | Archivo de exportación generado por el linker para R 4.4.1 |
| `ControlR/lib/R64.lib` | .lib | BINARIO | Biblioteca de importación para enlazar con R64.dll |
| `ControlR/lib/RGraphApp64.exp` | .exp | BINARIO | Archivo de exportación para RGraphApp64 |
| `ControlR/lib/RGraphApp64.lib` | .lib | BINARIO | Biblioteca de importación para RGraphApp64.dll |

### 2.2 Bibliotecas de importación de Julia (ControlJulia/lib/)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `ControlJulia/lib/libjulia.exp` | .exp | BINARIO | Archivo de exportación generado por el linker para Julia 1.12.6 |
| `ControlJulia/lib/libjulia.lib` | .lib | BINARIO | Biblioteca de importación para enlazar con libjulia.dll |

### 2.3 Artefactos de compilación del Ribbon (Ribbon/x64/)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `Ribbon/x64/Release/Ribbon/dllmain.obj` | .obj | BINARIO | Objeto compilado |
| `Ribbon/x64/Release/Ribbon/ribbon.obj` | .obj | BINARIO | Objeto compilado |
| `Ribbon/x64/Release/Ribbon/ribbon_connect.obj` | .obj | BINARIO | Objeto compilado |
| `Ribbon/x64/Release/Ribbon/stdafx.obj` | .obj | BINARIO | Objeto compilado |
| `Ribbon/x64/Release/Ribbon/RJ2XCLRibbon.pch` | .pch | BINARIO | Precompiled header |
| `Ribbon/x64/Release/Ribbon/RJ2XCLRibbon.res` | .res | BINARIO | Recurso compilado |
| `Ribbon/x64/Release/Ribbon/RJ2XCLRibbon.tlb` | .tlb | BINARIO | Type library generada por MIDL |
| `Ribbon/x64/Release/Ribbon/vc145.pdb` | .pdb | BINARIO | Base de datos de depuración |
| `Ribbon/RJ2XCLRibbon.tlb` | .tlb | BINARIO | Type library COM del Ribbon |

### 2.4 Instaladores (Install/)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `Install/Install-NEVEN.exe` | .exe | BINARIO | Instalador compilado del proyecto |
| `Install/Uninstall-NEVEN.exe` | .exe | BINARIO | Desinstalador compilado del proyecto |

### 2.5 Iconos y fuentes (BINARIO)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `Console/rj2xcl.ico` | .ico | BINARIO | Icono de la aplicación Console |
| `Console/ext/icomoon.woff` | .woff | BINARIO | Fuente de iconos web (formato binario) |
| `Console/ext/cogs/cogs.woff` | .woff | BINARIO | Fuente de iconos web (formato binario) |

### 2.6 Imágenes (BINARIO)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `iconos/Logo_Julia.png` | .png | BINARIO | Logo de Julia para la interfaz |
| `iconos/Logo_NEVEN.png` | .png | BINARIO | Logo del proyecto NEVEN |
| `iconos/Logo_Quarto.png` | .png | BINARIO | Logo de Quarto para la interfaz |
| `iconos/Logo_R.png` | .png | BINARIO | Logo de R para la interfaz |
| `Ribbon/images/console-16.png` | .png | BINARIO | Icono 16px para Ribbon |
| `Ribbon/images/console-32.png` | .png | BINARIO | Icono 32px para Ribbon |
| `Ribbon/images/logo-16.png` | .png | BINARIO | Logo 16px para Ribbon |
| `Ribbon/images/logo-32.png` | .png | BINARIO | Logo 32px para Ribbon |
| `Ribbon/images/logo_julia-16.png` | .png | BINARIO | Icono Julia 16px |
| `Ribbon/images/logo_julia-32.png` | .png | BINARIO | Icono Julia 32px |
| `Ribbon/images/logo_neven-16.png` | .png | BINARIO | Icono NEVEN 16px |
| `Ribbon/images/logo_neven-32.png` | .png | BINARIO | Icono NEVEN 32px |
| `Ribbon/images/logo_quarto-16.png` | .png | BINARIO | Icono Quarto 16px |
| `Ribbon/images/logo_quarto-32.png` | .png | BINARIO | Icono Quarto 32px |
| `Ribbon/images/logo_r-16.png` | .png | BINARIO | Icono R 16px |
| `Ribbon/images/logo_r-32.png` | .png | BINARIO | Icono R 32px |

### 2.7 Documentos PDF (BINARIO)

| Ruta | Extensión | Categoría | Justificación |
|------|-----------|-----------|---------------|
| `docs/Latex/PropuestaV0.pdf` | .pdf | BINARIO | Documento de propuesta de tesis (binario) |
| `docs/Latex/RJ2XCL_Paper.pdf` | .pdf | BINARIO | Paper académico compilado (binario) |
| `docs/Paper/figures/architecture_diagram.pdf` | .pdf | BINARIO | Diagrama de arquitectura (binario) |
| `docs/Paper/figures/dashboard_screenshot.pdf` | .pdf | BINARIO | Captura de pantalla (binario) |
| `docs/Paper/sections/architecture_diagram.pdf` | .pdf | BINARIO | Diagrama de arquitectura (binario) |
| `docs/Paper/main.pdf` | .pdf | BINARIO | Paper principal compilado (binario) |
| `libreria/EJEMPLOS/Excel/BONILLA/INSUMOS/Sharma-CreditScoring.pdf` | .pdf | BINARIO | Material de referencia académico |

---

## 3. Archivos Generados (GENERADO)

### 3.1 Protocol Buffers — Código generado por protoc (PB/)

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `PB/variable.pb.cc` | GENERADO | Código C++ generado automáticamente por `protoc` a partir de `variable.proto`. Se regenera en cada build. |
| `PB/variable.pb.h` | GENERADO | Header C++ generado automáticamente por `protoc` a partir de `variable.proto`. Se regenera en cada build. |

**Nota**: El archivo fuente `PB/variable.proto` y `PB/CMakeLists.txt` SÍ se incluyen en la auditoría ya que son código fuente mantenido manualmente.

### 3.2 Console/generated/ — Código JavaScript generado

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Console/generated/variable_pb.js` | GENERADO | Código JavaScript generado por protoc/protobuf.js a partir de `variable.proto` para uso en el renderer Electron. |

### 3.3 docs/api/html/ — Documentación Doxygen generada

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `docs/api/html/` (438 archivos) | GENERADO | Documentación HTML generada automáticamente por Doxygen a partir de los comentarios del código fuente C++. Incluye archivos .html, .js, .css, .png, .svg. Se regenera ejecutando `doxygen Doxyfile`. |

Archivos representativos:
- `docs/api/html/*.html` — Páginas de documentación de clases, funciones, archivos
- `docs/api/html/*.js` — Scripts de navegación generados
- `docs/api/html/*.png` — Diagramas de herencia de clases
- `docs/api/html/doxygen.svg` — Logo de Doxygen
- `docs/api/html/doxygen.css` — Estilos generados
- `docs/api/html/jquery.js` — Biblioteca jQuery incluida por Doxygen

---

## 4. Dependencias de Terceros (TERCEROS)

### 4.1 Include/ — Mock headers de SDKs externos

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Include/` (30 archivos) | TERCEROS | Headers mock/stub de R, Julia y Excel SDK usados para compilación sin dependencias externas. No son código del proyecto sino interfaces de terceros. |

Contenido:
- `Include/julia.h` — Mock header de Julia C API
- `Include/Rinternals.h`, `Rembedded.h`, `Rinterface.h`, etc. — Mock headers de R C API
- `Include/R_ext/*.h` (15 archivos) — Headers de extensiones R
- `Include/XLCALL.h`, `XLCALL.cpp` — Excel SDK (Microsoft XLL Framework)
- `Include/graphapp.h` — Header de GraphApp (R graphics)
- `Include/AutoLoader.h`, `GCMonitor.h`, `RuntimeLoader.h`, `SandboxVerifier.h`, `ScriptEngine.h` — Interfaces compartidas

### 4.2 OfficeTypes/ — Type libraries COM pre-generadas

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `OfficeTypes/` (8 archivos) | TERCEROS | Type libraries (.tlh, .tli) generadas por `#import` de las bibliotecas COM de Microsoft Office. Son interfaces de terceros pre-generadas, no código del proyecto. |

Archivos:
- `OfficeTypes/excel.tlh`, `excel.tli` — Interfaz COM de Excel
- `OfficeTypes/excel-14.tlh`, `excel-15.tlh` — Versiones específicas de Office
- `OfficeTypes/mso.tlh`, `mso.tli` — Interfaz COM de Microsoft Office
- `OfficeTypes/mso-14.tlh`, `mso-15.tlh` — Versiones específicas de Office

### 4.3 Common/json11/ — Biblioteca JSON de terceros

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Common/json11/json11.cpp` | TERCEROS | Biblioteca JSON ligera de Dropbox (json11). Código de terceros incluido directamente en el proyecto. |
| `Common/json11/json11.hpp` | TERCEROS | Header de json11. Licencia MIT, mantenido por Dropbox. |

### 4.4 Build/_deps/ — Dependencias descargadas por CMake FetchContent

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Build/_deps/protobuf-src/` | TERCEROS | Código fuente de Protocol Buffers v21.12 descargado por FetchContent |
| `Build/_deps/protobuf-build/` | TERCEROS | Compilación de protobuf (incluye libprotobuf.lib) |
| `Build/_deps/protobuf-subbuild/` | TERCEROS | Scripts de descarga de protobuf |
| `Build/_deps/googletest-src/` | TERCEROS | Código fuente de Google Test v1.14.0 descargado por FetchContent |
| `Build/_deps/googletest-build/` | TERCEROS | Compilación de GTest |
| `Build/_deps/googletest-subbuild/` | TERCEROS | Scripts de descarga de GTest |
| `Build/_deps/webview2-src/` | TERCEROS | SDK de WebView2 (Microsoft Edge Chromium) descargado por FetchContent |
| `Build/_deps/webview2-subbuild/` | TERCEROS | Scripts de descarga de WebView2 |

**Total en Build/_deps/: ~1,763 archivos**

---

## 5. Otros Artefactos (OTRO)

### 5.1 Caché de Python

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `startup/__pycache__/` | OTRO | Directorio de bytecode Python compilado. Contiene `startup.cpython-312.pyc`. Generado automáticamente por el intérprete Python. |

### 5.2 Logs de compilación (.tlog)

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Build/**/*.tlog` (100+ archivos) | OTRO | Logs de seguimiento de compilación de MSVC. Registran comandos de compilación, archivos leídos/escritos. No son código fuente. |
| `Ribbon/x64/Release/Ribbon/Ribbon.tlog/*.tlog` | OTRO | Logs de compilación del proyecto Ribbon en Visual Studio |

### 5.3 Artefactos de build del Ribbon (Ribbon/x64/)

| Ruta | Categoría | Justificación |
|------|-----------|---------------|
| `Ribbon/x64/Release/Ribbon/` (directorio) | OTRO | Artefactos de compilación de Visual Studio para NEVENRibbon.dll. Incluye objetos, PCH, recursos compilados, PDB y logs. No es código fuente. |

---

## 6. Resumen por Categoría

### BINARIO (archivos no legibles como texto)

| Extensión | Cantidad | Ubicación principal |
|-----------|----------|---------------------|
| .obj | ~100+ | Build/, Ribbon/x64/ |
| .lib | ~6 | Build/, ControlR/lib/, ControlJulia/lib/ |
| .dll | ~30+ | Build/ |
| .exe | ~10 | Build/, Install/ |
| .exp | ~5 | Build/, ControlR/lib/, ControlJulia/lib/ |
| .pdb | ~2 | Ribbon/x64/ |
| .pch | ~1 | Ribbon/x64/ |
| .res | ~3 | Build/, Ribbon/x64/ |
| .tlb | ~3 | Build/, Ribbon/ |
| .ico | 1 | Console/ |
| .woff | 2 | Console/ext/ |
| .png | ~24 | iconos/, Ribbon/images/, docs/api/html/ |
| .pdf | 7 | docs/Latex/, docs/Paper/, libreria/EJEMPLOS/ |
| .svg | 1 | docs/api/html/ |

### GENERADO (código auto-generado por herramientas)

| Fuente | Archivos | Herramienta |
|--------|----------|-------------|
| PB/variable.pb.cc, .pb.h | 2 | protoc (Protocol Buffers) |
| Console/generated/variable_pb.js | 1 | protobuf.js / protoc |
| docs/api/html/ | 438 | Doxygen |

### TERCEROS (dependencias externas)

| Directorio | Archivos | Origen |
|------------|----------|--------|
| Include/ | 30 | Mock headers R, Julia, Excel SDK |
| OfficeTypes/ | 8 | Type libraries COM de Microsoft Office |
| Common/json11/ | 2 | Biblioteca json11 (Dropbox, MIT) |
| Build/_deps/ | ~1,763 | protobuf v21.12, GTest v1.14.0, WebView2 SDK |

### OTRO (artefactos de build y caché)

| Directorio | Archivos | Tipo |
|------------|----------|------|
| Build/ (sin _deps) | ~430 | Objetos, ejecutables, solución VS, CMake cache |
| Build/**/*.tlog | ~100+ | Logs de compilación MSVC |
| Ribbon/x64/ | ~25 | Artefactos de compilación VS |
| startup/__pycache__/ | 1 | Bytecode Python |

---

## 7. Criterios de Decisión

### ¿Por qué se excluyen?

1. **Archivos binarios**: No son legibles como texto, no contienen patrones de código analizables. El análisis de seguridad se realiza sobre el código fuente que los genera.

2. **Código generado**: Es producido automáticamente por herramientas (protoc, Doxygen). Los problemas deben corregirse en la fuente (`.proto`, código fuente C++), no en la salida generada.

3. **Dependencias de terceros**: No son responsabilidad del proyecto NEVEN. Se auditan indirectamente verificando versiones y CVEs conocidos (ver análisis de seguridad de configuración).

4. **Artefactos de build**: Son efímeros, se regeneran en cada compilación. No representan el estado del código fuente.

### ¿Qué SÍ se audita de estos directorios?

| Directorio excluido | Archivos que SÍ se auditan |
|---------------------|---------------------------|
| PB/ | `variable.proto`, `CMakeLists.txt`, `build.sh` |
| Include/ | Se audita el *uso* de estos headers desde el código fuente |
| OfficeTypes/ | Se audita el *uso* de estas interfaces desde el código fuente |
| Common/json11/ | Se audita el *uso* de json11 desde el código del proyecto |
| Build/_deps/ | Se auditan las versiones declaradas en CMakeLists.txt |
| Console/ | Se audita `package.json` para dependencias npm |

---

## 8. Verificación de Completitud (Property 11)

Para cumplir con la invariante de contabilidad de archivos:

```
Archivos_Descubiertos = Archivos_Analizados + Archivos_Excluidos
```

Los archivos excluidos documentados en este archivo, sumados a los archivos analizados en el inventario (01_inventario.md), deben igualar el total de archivos descubiertos en el proyecto.
