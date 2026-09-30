# 02 — Métricas LOC: Líneas de Código por Lenguaje y por Módulo

**Proyecto:** NEVEN  
**Fecha:** 2025-01-27  
**Método:** Conteo de líneas no vacías (LOC = líneas con al menos un carácter no-whitespace)  
**Alcance:** Archivos fuente en los 15 módulos del proyecto  
**Exclusiones:** `Build/`, `node_modules/`, `docs/api/html/` (Doxygen generado), binarios

---

## 1. LOC por Lenguaje

| Lenguaje       | Extensiones                        |    LOC | Archivos | % LOC  |
|----------------|------------------------------------|-------:|---------:|-------:|
| C++            | `.cc`, `.h`, `.cpp`, `.hpp`, `.c`  | 48,417 |      195 |  63.8% |
| TypeScript     | `.ts`                              |  7,740 |       41 |  10.2% |
| JavaScript     | `.js`                              |  5,655 |        5 |   7.5% |
| Config         | `CMakeLists.txt`, `.json`, `.yml`, `.xml`, `.proto` | 5,599 | 33 | 7.4% |
| R              | `.R`                               |  5,188 |       34 |   6.8% |
| Julia          | `.jl`                              |  2,373 |        6 |   3.1% |
| Python         | `.py`                              |    871 |        1 |   1.1% |
| **TOTAL**      |                                    | **75,843** | **315** | **100%** |

> **Nota:** Se excluyen archivos Markdown, HTML, LaTeX, binarios y otros no clasificados como código fuente o configuración.

---

## 2. LOC por Módulo

| Módulo          | Descripción                          |    LOC | Archivos | % LOC  |
|-----------------|--------------------------------------|-------:|---------:|-------:|
| PB              | Protocol Buffers (generado por protoc) | 17,771 |      4 |  23.4% |
| Console         | REPL Electron (TypeScript/JS)        | 16,323 |       56 |  21.5% |
| Common          | Common.lib — utilidades compartidas  | 10,795 |       83 |  14.2% |
| Core            | NEVEN_Core (NEVEN.dll)               |  8,933 |       50 |  11.8% |
| libreria/R      | Librería R4XCL (~90 funciones)       |  5,080 |       33 |   6.7% |
| tests           | Tests unitarios (GTest)              |  3,943 |       26 |   5.2% |
| ControlR        | ControlR.exe — integración R         |  3,636 |       19 |   4.8% |
| libreria/JULIA  | Librería J4XCL (Julia)               |  2,154 |        5 |   2.8% |
| ControlJulia    | ControlJulia.exe — integración Julia |  2,137 |       12 |   2.8% |
| ControlPython   | ControlPython.exe (deprecado)        |  1,726 |        4 |   2.3% |
| Ribbon          | NEVENRibbon.dll — COM Ribbon         |  1,650 |       15 |   2.2% |
| startup         | Scripts de inicio R/Julia/Python     |  1,198 |        3 |   1.6% |
| Addin           | Empaquetado XLL                      |    232 |        2 |   0.3% |
| docs            | Documentación (solo .js de build)    |    199 |        2 |   0.3% |
| .github         | CI/CD workflows                      |     66 |        1 |   0.1% |
| **TOTAL**       |                                      | **75,843** | **315** | **100%** |

---

## 3. Tabla Cruzada: LOC por Módulo × Lenguaje

| Módulo          |    C++ |     R | Julia | Python |    TS |    JS | Config | **Total** |
|-----------------|-------:|------:|------:|-------:|------:|------:|-------:|----------:|
| Core            |  8,497 |     — |     — |      — |     — |     — |    436 |   **8,933** |
| Common          | 10,738 |     — |     — |      — |     — |     — |     57 |  **10,795** |
| ControlR        |  3,235 |     — |     — |      — |     — |     — |    401 |   **3,636** |
| ControlJulia    |  1,835 |     — |     — |      — |     — |     — |    302 |   **2,137** |
| ControlPython   |  1,648 |     — |     — |      — |     — |     — |     78 |   **1,726** |
| Console         |      — |     — |     — |      — | 7,740 | 5,456 |  3,127 |  **16,323** |
| Ribbon          |  1,127 |     — |     — |      — |     — |     — |    523 |   **1,650** |
| PB              | 17,445 |     — |     — |      — |     — |     — |    326 |  **17,771** |
| tests           |  3,892 |     — |     — |      — |     — |     — |     51 |   **3,943** |
| startup         |      — |   108 |   219 |    871 |     — |     — |      — |   **1,198** |
| libreria/R      |      — | 5,080 |     — |      — |     — |     — |      — |   **5,080** |
| libreria/JULIA  |      — |     — | 2,154 |      — |     — |     — |      — |   **2,154** |
| docs            |      — |     — |     — |      — |     — |   199 |      — |     **199** |
| Addin           |      — |     — |     — |      — |     — |     — |    232 |     **232** |
| .github         |      — |     — |     — |      — |     — |     — |     66 |      **66** |
| **TOTAL**       | **48,417** | **5,188** | **2,373** | **871** | **7,740** | **5,655** | **5,599** | **75,843** |

---

## 4. Tabla Cruzada: Archivos por Módulo × Lenguaje

| Módulo          | C++ |  R | Julia | Python | TS | JS | Config | **Total** |
|-----------------|----:|---:|------:|-------:|---:|---:|-------:|----------:|
| Core            |  47 |  — |     — |      — |  — |  — |      3 |    **50** |
| Common          |  82 |  — |     — |      — |  — |  — |      1 |    **83** |
| ControlR        |  16 |  — |     — |      — |  — |  — |      3 |    **19** |
| ControlJulia    |   9 |  — |     — |      — |  — |  — |      3 |    **12** |
| ControlPython   |   3 |  — |     — |      — |  — |  — |      1 |     **4** |
| Console         |   — |  — |     — |      — | 41 |  3 |     12 |    **56** |
| Ribbon          |  11 |  — |     — |      — |  — |  — |      4 |    **15** |
| PB              |   2 |  — |     — |      — |  — |  — |      2 |     **4** |
| tests           |  25 |  — |     — |      — |  — |  — |      1 |    **26** |
| startup         |   — |  1 |     1 |      1 |  — |  — |      — |     **3** |
| libreria/R      |   — | 33 |     — |      — |  — |  — |      — |    **33** |
| libreria/JULIA  |   — |  — |     5 |      — |  — |  — |      — |     **5** |
| docs            |   — |  — |     — |      — |  — |  2 |      — |     **2** |
| Addin           |   — |  — |     — |      — |  — |  — |      2 |     **2** |
| .github         |   — |  — |     — |      — |  — |  — |      1 |     **1** |
| **TOTAL**       | **195** | **34** | **6** | **1** | **41** | **5** | **33** | **315** |

---

## 5. Métricas Derivadas

| Métrica                                    |   Valor |
|--------------------------------------------|--------:|
| LOC total (código fuente + config)         |  75,843 |
| Total archivos analizados                  |     315 |
| LOC promedio por archivo                   |     241 |
| LOC código C++ nativo (sin PB generado)    |  30,972 |
| LOC código aplicativo (sin PB generado)    |  58,072 |
| LOC código generado (PB)                   |  17,771 |
| Ratio código nativo C++ / total            |   40.8% |
| Ratio código scripting (R+Julia+Python)    |   11.1% |
| Ratio código frontend (TS+JS)              |   17.7% |

### Distribución por Categoría Funcional

| Categoría                          |    LOC | Archivos | % LOC  |
|------------------------------------|-------:|---------:|-------:|
| **Código C++ nativo** (Core+Common+Control*+Ribbon+tests) | 30,972 | 193 | 40.8% |
| **Código generado** (PB)          | 17,771 |        4 |  23.4% |
| **Frontend** (Console TS+JS)      | 13,196 |       44 |  17.4% |
| **Configuración** (todos)         |  5,599 |       33 |   7.4% |
| **Scripting** (R+Julia+Python)    |  8,432 |       41 |  11.1% |
| **Otros** (docs JS, Addin config) |    — |      — |      — |

---

## 6. Observaciones

1. **PB domina en LOC bruto** (23.4%) pero es código auto-generado por `protoc` — no requiere mantenimiento manual.
2. **Console** es el segundo módulo más grande (21.5%) combinando TypeScript y JavaScript.
3. **Common** (14.2%) y **Core** (11.8%) son los módulos C++ escritos a mano más grandes.
4. **Python** tiene presencia mínima (871 LOC, 1 archivo) — consistente con su estado deprecado.
5. **libreria/R** (5,080 LOC en 33 archivos) es significativamente más grande que **libreria/JULIA** (2,154 LOC en 5 archivos).
6. **LOC promedio por archivo C++**: ~248 líneas — indica archivos de tamaño manejable.
7. **Startup scripts** son compactos (1,198 LOC total) — scripts de inicialización concisos.

---

## Notas Metodológicas

1. **LOC** = líneas no vacías (se excluyen líneas que contienen solo whitespace).
2. **Exclusiones aplicadas**:
   - `Build/` — artefactos de compilación
   - `node_modules/` — dependencias npm
   - `docs/api/html/` — documentación Doxygen auto-generada
   - Archivos binarios (`.dll`, `.exe`, `.obj`, `.lib`, `.pdb`, `.ico`, `.woff`, `.png`, `.pdf`)
3. **Clasificación de lenguaje**: basada en extensión de archivo; `CMakeLists.txt` se clasifica como Config independientemente de su extensión.
4. **R case-insensitive**: archivos `.r` y `.R` se cuentan ambos como lenguaje R.
5. **Herramienta**: PowerShell con `StreamReader` para conteo línea por línea.
