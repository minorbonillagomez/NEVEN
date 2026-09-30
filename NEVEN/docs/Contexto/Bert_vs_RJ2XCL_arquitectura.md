# Analisis Comparativo: BERT Toolkit vs NEVEN v2.0

**Fecha**: 27 de abril de 2026
**Universidad de Costa Rica — Tesis de Maestria**

------------------------------------------------------------------------

## 1. Vision General

| Aspecto | BERT Toolkit (Original) | NEVEN v2.0 |
|:---|:---|:---|
| **Concepto** | Conector basico Excel-R-Julia | Plataforma analitica integral |
| **Lenguajes** | R 3.4.x, Julia 0.6.2 (obsoletos) | R 4.4.1, Julia 1.12.6 (actuales) |
| **Visualizacion** | PNG estatico en hoja | WebView2 embebido (Plotly, D3.js, HTML interactivo) |
| **Notebooks** | No soportado | Pluto.jl reactivo con pipeline de datos |
| **Reportes** | No soportado | Quarto (.qmd --> HTML --> WebView2) |
| **Interfaz** | Boton basico en Add-ins | Ribbon COM nativo con iconos custom |
| **Seguridad** | Sin sandbox | 30+ patrones bloqueados por lenguaje |
| **Tests** | 0 | 205 (unit + property-based) |
| **Score** | ~4/10 (estimado) | 9.2/10 (evaluado) |

------------------------------------------------------------------------

## 2. Arquitectura

### BERT Original
```
Excel <----> XLL <----> ControlR.exe (R 3.4)
                  ControlJulia.exe (Julia 0.6)
```
- Monolitico: clase principal con 15+ responsabilidades
- Sin servicios modulares
- Configuracion hardcoded
- Sin health monitoring

### NEVEN v2.0
```
Excel <----> XLL <----> ControlR.exe (R 4.4.1)
           │      ControlJulia.exe (Julia 1.12.6)
           │
           ├──--> WebView2 (STA thread) --> Plotly, HTML, Impress.js
           ├──--> Pluto.jl (proceso separado) --> Notebooks reactivos
           ├──--> Quarto CLI (CreateProcess) --> Reportes HTML
           └──--> NEVENRibbon.dll (COM) --> Pestana nativa en Excel
```
- 4 capas: Interface, Servicios, Subsistemas, Herramientas
- 25+ servicios especializados (ConfigService, ViewerManager, PlutoManager, etc.)
- Configuracion centralizada con validacion
- Health monitoring per-language con retry limits

------------------------------------------------------------------------

## 3. Comparacion Funcional Detallada

| Funcionalidad | BERT | NEVEN v2.0 | Ventaja |
|:---|:---:|:---:|:---|
| `=R.Func(rango)` | ✅ | ✅ | Paridad |
| `=J.Func(rango)` | ✅ | ✅ | Paridad |
| Funciones R registradas | ~20 | **~90** | NEVEN: 9 modulos estadisticos |
| Funciones Julia registradas | ~5 | **~75** | NEVEN: 11 modulos + aliases cortos |
| Graficos PNG en hoja | ✅ | ✅ | Paridad |
| **Graficos interactivos** | ❌ | ✅ | NEVEN: Plotly, ggplot2, D3.js en WebView2 |
| **Notebooks reactivos** | ❌ | ✅ | NEVEN: Pluto.jl con pipeline Excel-->Julia |
| **Reportes profesionales** | ❌ | ✅ | NEVEN: Quarto .qmd --> HTML |
| **Editor presentaciones** | ❌ | ✅ | NEVEN: Impress.js drag-and-drop |
| **Ribbon nativo** | ❌ | ✅ | NEVEN: COM Add-in con iconos R/Julia/Quarto |
| **Sandbox seguridad** | ❌ | ✅ | NEVEN: 30+ patrones bloqueados |
| **Tests automatizados** | ❌ | ✅ | NEVEN: 205 tests (unit + PBT) |
| **Mensajes de error** | `#VALOR!` | ✅ | NEVEN: mensaje real de R/Julia en celda |
| **Pipeline datos Excel-->ML** | ❌ | ✅ | NEVEN: PLUTO.DATA --> PCA, clustering |
| **Config centralizado** | ❌ | ✅ | NEVEN: JSON validado con getters tipados |
| **Health monitoring** | ❌ | ✅ | NEVEN: HealthStatus enum, per-language timeout |
| **Callback thread** | ✅ | ✅ | Paridad (reactivado en NEVEN) |
| Hot-reload scripts | ✅ | ✅ | Paridad |
| Consola REPL | ✅ Electron | ✅ Rgui/Julia terminal | Diferente enfoque |
| Version R soportada | 3.4-3.5 | **4.4.1+** | NEVEN: 6 versiones mas reciente |
| Version Julia soportada | 0.6.2 | **1.12.6** | NEVEN: 12 versiones mas reciente |

------------------------------------------------------------------------

## 4. Innovaciones Exclusivas de NEVEN

### 4.1 WebView2 Embebido
BERT solo podia generar PNG estaticos. NEVEN renderiza contenido HTML interactivo dentro de Excel:
- Plotly con zoom, pan, hover, tooltips
- ggplot2 convertido a Plotly interactivo
- HTML personalizado, archivos locales, CDNs
- Filtro de navegacion con whitelist de seguridad

### 4.2 Pipeline Excel --> Julia --> Pluto
Flujo inexistente en BERT:
```
=NEVEN.pluto.data(A1:D100, "datos")  --> Julia recibe matriz
=NEVEN.notebook.open("excel_data")   --> Pluto muestra dashboard
```
El usuario ejecuta PCA, clustering, regresion directamente sobre datos de Excel en un notebook reactivo.

### 4.3 Quarto como Proceso Externo
BERT no tenia capacidad de reportes. NEVEN renderiza documentos Quarto:
```
=NEVEN.q("reporte.qmd")  --> HTML profesional en WebView2
```

### 4.4 Ribbon COM con Iconos Custom
BERT tenia un boton basico. NEVEN tiene una pestana completa:
- 13 botones en 5 grupos
- Iconos oficiales PNG de R, Julia, Quarto
- Consolas R y Julia accesibles con un clic

### 4.5 Funciones Julia con Aliases
BERT tenia funciones Julia basicas. NEVEN tiene 11 modulos:

| Funcion | Procedimientos | Ejemplo |
|:---|:---:|:---|
| `J.Algebra` | 12 | Determinante, eigenvalores, LU, QR, SVD |
| `J.Calculo` | 7 | Derivada, integrales, interpolacion |
| `J.EDO` | 4 | Euler, Runge-Kutta |
| `J.Estadistica` | 8 | Descriptiva, correlacion, t-test, outliers |
| `J.KNN` | 5 | Clasificacion, precision/recall, confusion |
| `J.Regresion` | 5 | Coeficientes, R2, residuos, intervalos |
| `J.Clustering` | 6 | K-Medias, codo, descriptivas |
| `J.Optimizar` | 7 | Gradiente, Newton, simplex, QP |
| `J.Transformar` | 6 | Transponer, ordenar, filtrar, frecuencias |
| `J.Utilidades` | 5 | Secuencias, aleatorios, fecha |

### 4.6 Seguridad
BERT ejecutaba cualquier codigo sin restriccion. NEVEN bloquea:
- `system()`, `shell()`, `file.remove()` en R
- `ccall()`, `run()`, `unsafe_*` en Julia
- Path traversal y command injection en configuracion
- Bypass detection (whitespace stripping, string concatenation)

------------------------------------------------------------------------

## 5. Calidad de Codigo

| Metrica | BERT | NEVEN v2.0 |
|:---|:---|:---|
| TODOs/FIXMEs | 20+ | **0** |
| Debug artifacts (std::cout) | Multiples | **0** en XLL (7 en procesos hijo, aceptable) |
| Memory leaks conocidos | Si (Pipe, XLOPER) | **Corregidos** (RAII, thread_local) |
| Race conditions | Si (callbacks) | **Corregidas** (mutex) |
| Hardcoded paths | Si | **0** (ConfigService) |
| Tests | 0 | **205** |
| Documentacion inline | Minima | **Doxygen en 8+ clases** |

------------------------------------------------------------------------

## 6. Rendimiento

| Aspecto | BERT | NEVEN v2.0 |
|:---|:---|:---|
| Arranque R | ~2s | ~2s (paridad) |
| Arranque Julia | ~5 min (JIT) | **~2s** (sysimage precompilada) |
| Timeout configurable | No | Si (per-language) |
| Reconnect automatico | goto retry (infinito) | Max 2 reintentos (configurable) |
| Recalculo paralelo | Unsafe (static vars) | **Safe** (thread_local XLOPER12) |

------------------------------------------------------------------------

## 7. Conclusion

BERT fue una prueba de concepto innovadora que demostro la viabilidad de integrar R y Julia en Excel. NEVEN v2.0 toma esa base y la transforma en un producto de calidad profesional:

| Dimension | BERT --> NEVEN | Mejora |
|:---|:---|:---|
| Funcionalidad | Basica --> Completa | WebView2, Pluto, Quarto, Ribbon, 200 funciones |
| Seguridad | Inexistente --> Robusta | Sandbox, config validation, navigation filter |
| Calidad | Prototipo --> Produccion | 0 TODOs, RAII, 205 tests |
| Documentacion | Minima --> Exhaustiva | 10 documentos, 80+ ejemplos |
| UX | Boton basico --> Ribbon nativo | Iconos custom, 13 botones, tooltips |

**NEVEN no es un parche de BERT — es una reinvencion completa que supera al original en todas las dimensiones medibles.**

------------------------------------------------------------------------

*Universidad de Costa Rica — Tesis de Maestria*
*De 4.3 a 9.2 — Team Vikingos ⚔️ — SKÅL!*
