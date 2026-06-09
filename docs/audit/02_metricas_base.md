# 02 — Métricas Base: LOC y Archivos por Lenguaje y Módulo

**Proyecto:** NEVEN  
**Fecha:** 2025-01-27  
**Método:** Conteo de líneas no vacías (LOC excluye líneas en blanco)  
**Alcance:** Directorios de código fuente y documentación (excluye build artifacts, binarios, node_modules)

---

## 1. LOC por Lenguaje

| Lenguaje     | LOC    | % del Total |
|--------------|-------:|------------:|
| C++          | 53,427 |      32.4%  |
| R            |  5,188 |       3.1%  |
| Julia        |  2,373 |       1.4%  |
| Python       |    871 |       0.5%  |
| TypeScript   |  7,740 |       4.7%  |
| JavaScript   | 11,807 |       7.2%  |
| Config       |  8,995 |       5.5%  |
| Markdown     | 12,765 |       7.7%  |
| Other        | 61,560 |      37.4%  |
| **TOTAL**    | **164,726** | **100%** |

> **Nota sobre "Other":** Incluye HTML generado por Doxygen (docs/api), archivos .tex (LaTeX), .html de la consola Electron, y scripts auxiliares (.ps1, .bat, .sh). La mayoría (≈62K LOC) corresponde a documentación API auto-generada.

---

## 2. LOC por Módulo

| Módulo          | LOC    | % del Total | Descripción                          |
|-----------------|-------:|------------:|--------------------------------------|
| Core            | 11,147 |       6.8%  | NEVEN_Core (NEVEN.dll)               |
| Common          | 10,813 |       6.6%  | Common.lib — utilidades compartidas  |
| ControlR        |  6,134 |       3.7%  | ControlR.exe — integración R         |
| ControlJulia    |  3,833 |       2.3%  | ControlJulia.exe — integración Julia |
| ControlPython   |  1,726 |       1.0%  | ControlPython (deprecado)            |
| Console         | 20,865 |      12.7%  | REPL Electron (TypeScript/JS)        |
| Ribbon          |  2,026 |       1.2%  | NEVENRibbon.dll — COM Ribbon         |
| PB              | 17,775 |      10.8%  | Protocol Buffers (generado)          |
| tests           |  3,943 |       2.4%  | Tests unitarios (GTest)              |
| startup         |  1,659 |       1.0%  | Scripts de inicio R/Julia            |
| libreria/R      |  5,080 |       3.1%  | Librería R4XCL (~90 funciones)       |
| libreria/JULIA  |  2,154 |       1.3%  | Librería J4XCL (Julia)               |
| docs            | 77,204 |      46.9%  | Documentación (ver desglose abajo)   |
| Addin           |    232 |       0.1%  | Empaquetado XLL                      |
| .github         |    135 |       0.1%  | CI/CD workflows                      |
| **TOTAL**       | **164,726** | **100%** |                                 |

### Desglose del módulo `docs`

| Subcategoría         | LOC    | Archivos | Nota                              |
|----------------------|-------:|---------:|-----------------------------------|
| docs/api (generado)  | 62,460 |      581 | Doxygen HTML/JS/CSS auto-generado |
| docs (authored)      | 15,210 |       85 | Documentación escrita manualmente |
| **Total docs**       | **77,204** | **662** |                              |

---

## 3. Archivos por Lenguaje

| Lenguaje     | Archivos | % del Total |
|--------------|--------:|------------:|
| C++          |     205 |      20.0%  |
| R            |      34 |       3.3%  |
| Julia        |       6 |       0.6%  |
| Python       |       1 |       0.1%  |
| TypeScript   |      41 |       4.0%  |
| JavaScript   |     277 |      27.1%  |
| Config       |      54 |       5.3%  |
| Markdown     |      69 |       6.7%  |
| Other        |     337 |      32.9%  |
| **TOTAL**    | **1,024** | **100%** |

---

## 4. Archivos por Módulo

| Módulo          | Archivos | % del Total |
|-----------------|--------:|------------:|
| Core            |      53 |       5.2%  |
| Common          |      84 |       8.2%  |
| ControlR        |      26 |       2.5%  |
| ControlJulia    |      18 |       1.8%  |
| ControlPython   |       4 |       0.4%  |
| Console         |      74 |       7.2%  |
| Ribbon          |      22 |       2.1%  |
| PB              |       5 |       0.5%  |
| tests           |      26 |       2.5%  |
| startup         |       6 |       0.6%  |
| libreria/R      |      33 |       3.2%  |
| libreria/JULIA  |       5 |       0.5%  |
| docs            |     662 |      64.6%  |
| Addin           |       2 |       0.2%  |
| .github         |       4 |       0.4%  |
| **TOTAL**       | **1,024** | **100%** |

---

## 5. Totales Generales

| Métrica                        | Valor       |
|--------------------------------|------------:|
| Total LOC (todas las fuentes)  |     164,726 |
| Total archivos                 |       1,024 |
| LOC código fuente (sin docs)   |      87,522 |
| LOC código C++ (Core+Common+Control*+Ribbon+PB+tests) |  53,427 |
| LOC código aplicativo (sin generado ni docs) | ~65,000 |
| Archivos código fuente (sin docs) |       362 |

### Resumen Ejecutivo

| Categoría              | LOC    | Archivos |
|------------------------|-------:|---------:|
| **Código C++ nativo**  | 53,427 |      205 |
| **Código scripting (R+Julia+Python)** | 8,432 | 41 |
| **Código frontend (TS+JS)** | 19,547 | 318 |
| **Configuración**      |  8,995 |       54 |
| **Documentación (authored)** | 15,210 | 85 |
| **Documentación (generada)** | 62,460 | 581 |
| **Otros (HTML, LaTeX, scripts)** | ~(balance) | ~(balance) |

---

## Notas Metodológicas

1. **LOC** = líneas no vacías (se excluyen líneas que solo contienen whitespace)
2. **Exclusiones**: archivos binarios (.png, .ico, .woff, .pdf, .exe, .dll, .obj, .lib, .pdb, .pch, .res, .tlb, .gz), directorios de build (x64/, Release/, Debug/), node_modules
3. **Clasificación de lenguaje**: basada en extensión de archivo (.cc/.cpp/.h/.hpp → C++, .r/.rmd → R, .jl → Julia, .py → Python, .ts → TypeScript, .js → JavaScript, .json/.yml/.xml/.proto/.less/.css/.cmake → Config, .md → Markdown)
4. **"Other"** incluye: HTML (Doxygen + Electron), LaTeX (.tex), scripts shell (.ps1, .bat, .sh), archivos .txt no-CMake
5. **PB (17,775 LOC)**: mayormente código generado por protoc (Protocol Buffers)
6. **Console JS (277 archivos)**: incluye dependencias vendored en ext/cogs/ (CodeMirror, etc.)
