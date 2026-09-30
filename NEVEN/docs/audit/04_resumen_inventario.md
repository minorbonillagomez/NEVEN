# 04 — Tabla Resumen del Inventario con Cobertura por Módulo

**Proyecto:** NEVEN  
**Fecha:** 2025-01-27  
**Fuentes:** 01_inventario_archivos.md, 02_metricas_loc.md, 03_exclusiones.md

---

## 1. Tabla Resumen por Módulo

| Directorio | Contenido | Lenguajes | Archivos | LOC | Estado |
|---|---|---|---|---:|---|
| Core/ | NEVEN_Core (NEVEN.dll) — motor principal XLL | C++ | 50 | 8,933 | Analizado |
| Common/ | Common.lib — utilidades compartidas (IPC, config, seguridad, viewers) | C++ | 83 | 10,795 | Analizado |
| ControlR/ | ControlR.exe — proceso hijo con R embebido | C++ | 19 | 3,636 | Parcial |
| ControlJulia/ | ControlJulia.exe — proceso hijo con Julia embebida | C++ | 12 | 2,137 | Parcial |
| ControlPython/ | ControlPython.exe — integración Python (DEPRECADO) | C++ | 4 | 1,726 | Analizado |
| Console/ | REPL Electron — aplicación de consola interactiva | TypeScript, JavaScript | 56 | 16,323 | Parcial |
| Ribbon/ | NEVENRibbon.dll — COM Ribbon Add-in para Excel | C++ | 15 | 1,650 | Parcial |
| PB/ | Protocol Buffers — serialización IPC | Protobuf, C++ (generado) | 4 | 17,771 | Parcial |
| tests/ | Suite de tests unitarios y PBT (GTest v1.14.0) | C++ | 26 | 3,943 | Analizado |
| startup/ | Scripts de inicialización para R, Julia y Python | R, Julia, Python | 3 | 1,198 | Analizado |
| libreria/R/ | R4XCL — ~90 funciones estadísticas y de análisis | R | 33 | 5,080 | Analizado |
| libreria/JULIA/ | J4XCL — funciones Julia (ML, matemáticas, optimización) | Julia | 5 | 2,154 | Analizado |
| docs/ | Documentación del proyecto (manual + Doxygen generado) | Markdown, HTML/JS | 2 | 199 | Parcial |
| Addin/ | Empaquetado XLL — configuración de distribución | CMake, XML | 2 | 232 | Analizado |
| .github/ | CI/CD — workflows y templates | YAML, Markdown | 1 | 66 | Analizado |
| **TOTAL** | | | **315** | **75,843** | |

### Leyenda de Estado

| Estado | Significado |
|--------|-------------|
| **Analizado** | Todos los archivos del módulo están incluidos en el análisis de auditoría |
| **Excluido** | Todos los archivos del módulo están excluidos del análisis |
| **Parcial** | Algunos archivos del módulo se analizan y otros se excluyen (binarios, generados, artefactos de build) |

### Detalle de módulos con estado "Parcial"

| Módulo | Archivos Analizados | Archivos Excluidos | Motivo de Exclusión |
|--------|---:|---:|---|
| ControlR/ | 19 | 9 | Bibliotecas de importación binarias (.lib, .exp) en lib/ |
| ControlJulia/ | 12 | 7 | Bibliotecas de importación binarias (.lib, .exp) en lib/ |
| Console/ | 56 | 21 | Iconos (.ico), fuentes (.woff), assets binarios |
| Ribbon/ | 15 | 45 | Imágenes (.png), artefactos de build (x64/Release/), logs (.tlog) |
| PB/ | 4 | 1 | Código C++ generado por protoc incluido en LOC; build.sh excluido |
| docs/ | 2 | 713 | Documentación Doxygen generada (docs/api/html/), PDFs, imágenes |

---

## 2. Cobertura de la Auditoría

### Por archivos

| Métrica | Valor |
|---------|------:|
| Total archivos descubiertos (15 directorios) | 1,121 |
| Archivos analizados (código + config) | 315 |
| Archivos excluidos dentro de los 15 directorios | 806 |
| **Cobertura por archivos** | **28.1%** |
| **Cobertura por archivos de código fuente** | **100%** |

> **Nota:** La cobertura del 28.1% sobre el total se debe a que 715 archivos en docs/ son mayoritariamente documentación Doxygen generada (438 archivos HTML/JS/CSS) y documentación Markdown (no código). La cobertura de archivos de código fuente y configuración es del 100%.

### Por LOC

| Categoría | LOC | % del Total |
|-----------|----:|---:|
| Código C++ nativo (Core+Common+Control*+Ribbon+tests) | 30,972 | 40.8% |
| Código generado (PB) | 17,771 | 23.4% |
| Frontend (Console TS+JS) | 13,196 | 17.4% |
| Scripting (R+Julia+Python) | 8,432 | 11.1% |
| Configuración | 5,599 | 7.4% |
| **Total LOC analizado** | **75,843** | **100%** |

### Por módulo funcional

| Capa Arquitectónica | Módulos | LOC | Archivos |
|---|---|---:|---:|
| Core (XLL) | Core/ | 8,933 | 50 |
| Infraestructura compartida | Common/ | 10,795 | 83 |
| Procesos hijo (IPC) | ControlR/, ControlJulia/, ControlPython/ | 7,499 | 35 |
| Serialización | PB/ | 17,771 | 4 |
| Frontend | Console/ | 16,323 | 56 |
| Ribbon | Ribbon/ | 1,650 | 15 |
| Librerías de scripting | libreria/R/, libreria/JULIA/, startup/ | 8,432 | 41 |
| Testing | tests/ | 3,943 | 26 |
| Configuración/CI | Addin/, .github/ | 298 | 3 |
| Documentación (código) | docs/ | 199 | 2 |

---

## 3. Verificación de Property 11: Invariante de Contabilidad de Archivos

### Enunciado

> *For any completed audit execution, the union of files reported as "analyzed" and files reported as "excluded" SHALL equal the total set of files discovered during the inventory phase. No file SHALL appear in both sets or be absent from both.*

### Verificación

```
Total Descubierto = Archivos Analizados + Archivos Excluidos (dentro del alcance)
```

#### Desglose por módulo

| Módulo | Descubiertos | Analizados | Excluidos | Verificación |
|--------|---:|---:|---:|---|
| Core/ | 53 | 50 | 3 | ✓ (50 + 3 = 53) |
| Common/ | 84 | 83 | 1 | ✓ (83 + 1 = 84) |
| ControlR/ | 28 | 19 | 9 | ✓ (19 + 9 = 28) |
| ControlJulia/ | 19 | 12 | 7 | ✓ (12 + 7 = 19) |
| ControlPython/ | 4 | 4 | 0 | ✓ (4 + 0 = 4) |
| Console/ | 77 | 56 | 21 | ✓ (56 + 21 = 77) |
| Ribbon/ | 60 | 15 | 45 | ✓ (15 + 45 = 60) |
| PB/ | 5 | 4 | 1 | ✓ (4 + 1 = 5) |
| tests/ | 26 | 26 | 0 | ✓ (26 + 0 = 26) |
| startup/ | 6 | 3 | 3 | ✓ (3 + 3 = 6) |
| libreria/R/ | 33 | 33 | 0 | ✓ (33 + 0 = 33) |
| libreria/JULIA/ | 5 | 5 | 0 | ✓ (5 + 0 = 5) |
| docs/ | 715 | 2 | 713 | ✓ (2 + 713 = 715) |
| Addin/ | 2 | 2 | 0 | ✓ (2 + 0 = 2) |
| .github/ | 4 | 1 | 3 | ✓ (1 + 3 = 4) |
| **TOTAL** | **1,121** | **315** | **806** | **✓ (315 + 806 = 1,121)** |

### Detalle de archivos excluidos por módulo

| Módulo | Excluidos | Categorías de Exclusión |
|--------|---:|---|
| Core/ | 3 | OTRO: README.md, .rc, .def (no son código analizable para LOC) |
| Common/ | 1 | OTRO: README.md |
| ControlR/ | 9 | BINARIO: .lib, .exp (4); OTRO: .gitignore, README.md, .def, .ps1 (5) |
| ControlJulia/ | 7 | BINARIO: .lib, .exp (2); OTRO: .gitignore, README.md, .def, .txt, .ps1 (5) |
| Console/ | 21 | BINARIO: .ico, .woff (3); OTRO: .html, .css, .less, .lock, .gitignore, .md (18) |
| Ribbon/ | 45 | BINARIO: .png, .obj, .pch, .pdb, .res, .tlb (24); OTRO: .tlog, .idl, .rgs, .rc, .def, .gitignore, .md (21) |
| PB/ | 1 | OTRO: build.sh (script de build auxiliar) |
| startup/ | 3 | BINARIO: .pyc (1); OTRO: .sha256 (2) |
| docs/ | 713 | GENERADO: Doxygen HTML/JS/CSS (438); BINARIO: .png, .pdf, .svg (30+); OTRO: Markdown, LaTeX, etc. (~245) |
| .github/ | 3 | OTRO: Markdown templates (3) |

### Resultado

**✓ PROPERTY 11 VERIFICADA**: La unión de archivos analizados (315) y archivos excluidos (806) es exactamente igual al total de archivos descubiertos (1,121). Ningún archivo aparece en ambos conjuntos ni está ausente de ambos.

---

## 4. Directorios Fuera del Alcance de los 15 Módulos

Además de los 1,121 archivos descubiertos en los 15 directorios del alcance, existen directorios adicionales que están completamente fuera del alcance de la auditoría:

| Directorio | Archivos (est.) | Categoría | Justificación |
|---|---:|---|---|
| Build/ | ~2,193 | OTRO | Artefactos de compilación CMake/MSVC |
| Build/_deps/ | ~1,763 | TERCEROS | Dependencias descargadas (protobuf, GTest, WebView2) |
| Include/ | 30 | TERCEROS | Mock headers de R, Julia, Excel SDK |
| OfficeTypes/ | 8 | TERCEROS | Type libraries COM pre-generadas |
| Install/ | 2 | BINARIO | Instaladores compilados |
| iconos/ | 4 | BINARIO | Logos PNG del proyecto |

Estos directorios no forman parte del inventario de los 15 módulos definidos en el alcance de la auditoría (Requerimiento 11.3).

---

## 5. Observaciones Clave

1. **El código C++ nativo es el núcleo del proyecto** — 30,972 LOC en 193 archivos representan la lógica de negocio principal.
2. **PB es el módulo con más LOC pero es generado** — 17,771 LOC auto-generados por protoc no requieren auditoría de calidad de código.
3. **Console es el segundo módulo más grande** — 16,323 LOC de frontend TypeScript/JavaScript.
4. **La librería R es 2.4× más grande que la de Julia** — refleja la madurez relativa de cada integración.
5. **ControlPython es mínimo** (1,726 LOC, 4 archivos) — consistente con su estado deprecado.
6. **docs/ domina en cantidad de archivos** (715 de 1,121) pero la mayoría es Doxygen generado.
7. **La cobertura de código fuente es del 100%** — todos los archivos de código y configuración están incluidos en el análisis.

---

*Resumen generado como parte de la Fase 1 (Inventario y Alcance) de la auditoría integral del proyecto NEVEN.*

---

## ACTUALIZACIÓN — Agosto 2026 (NEVEN v2.2)

### Cambios estructurales desde el inventario original (2025-01-27)

| Cambio | Impacto en inventario |
|:---|:---|
| **Console/ eliminado** | El módulo Electron (16,323 LOC, 56 archivos) fue removido completamente. Reemplazado por WebView2 REPL (~200 LOC en Common). Reducción real: ~15,000 LOC netos |
| **ControlPython activo** | Ya NO está deprecado. Activo con 357 tests y funciones AI/LLM |
| **TaskPane/ nuevo** | NEVEN Studio Standalone: `taskpane.html`, `datalab.js`, `start_studio.py`, `pipe_client.py`, `neven_http_server.py` — aprox. 8,000+ LOC JavaScript/Python |
| **CreadorPresentaciones/ nuevo** | Editor de presentaciones integrado: `script.js` (~1,100 LOC JS), `index.html`, `styles.css` |
| **startup/ expandido** | Agregado `r_object_to_slots.R` (serializador Data Lab) |
| **Install/functions/ nuevo** | 28+ sidecars JSON del catálogo Data Lab (~2,000 líneas JSON) |
| **libreria/R/ expandido** | 28 funciones `.Studio.R` para Data Lab agregadas al catálogo R4XCL |
| **NEVEN-SIM/ nuevo** | Módulo de simulación Monte Carlo (XLL separado, `BUILD_NEVEN_SIM=ON`) |

### Tabla resumen actualizada (estimado v2.2)

| Directorio | LOC aprox. | Estado v2.2 |
|---|---:|---|
| Core/ | ~9,000 | Sin cambios estructurales |
| Common/ | ~11,500 | +REPLManager, +REPLBridge eliminando Console |
| ControlR/ | ~3,700 | Sin cambios |
| ControlJulia/ | ~2,200 | Sin cambios |
| ControlPython/ | ~2,500 | **Activo y expandido** (Python 3.13 estable, AI functions) |
| Console/ | 0 | **ELIMINADO** — reemplazado por WebView2 REPL |
| TaskPane/ | ~8,000+ | **NUEVO** — NEVEN Studio Standalone |
| CreadorPresentaciones/ | ~2,000 | **NUEVO** — Editor de presentaciones |
| Ribbon/ | ~1,700 | Sin cambios |
| PB/ | ~17,800 | Sin cambios |
| tests/ | ~5,500 | +357 tests (vs 228) |
| startup/ | ~1,800 | +r_object_to_slots.R |
| libreria/R/ | ~7,000 | +28 funciones .Studio.R |
| libreria/JULIA/ | ~2,200 | Sin cambios |
| Install/functions/ | ~2,000 | **NUEVO** — 28+ sidecars JSON |
| NEVEN-SIM/ | ~1,500 | **NUEVO** — Monte Carlo XLL |
| docs/ | ~80,000+ | +NEVEN-BOOK.md, +Evaluaciones actualizadas |

### Tests: de 228 a 357

| Período | Tests | Cambio |
|:---|:---:|:---|
| Mayo 2026 (último inventario) | 228 | — |
| Julio 2026 (Studio + Data Lab) | 357 | +129 nuevos tests |
| **Agosto 2026 (v2.2)** | **357** | Sin nuevos tests (cambios UI) |

### Nuevos módulos fuera del alcance original

Los siguientes componentes **no existían** en el inventario original y deben ser incluidos en una auditoría actualizada:

- `TaskPane/` — NEVEN Studio (servidor HTTP Python + UI JS)
- `CreadorPresentaciones/` — Editor Impress.js
- `Install/functions/` — Catálogo Data Lab (sidecar JSONs)
- `NEVEN-SIM/` — Módulo Monte Carlo
- `startup/r_object_to_slots.R` — Serializador Data Lab

*Inventario actualizado: agosto 2026*
