# Estado del Proyecto NEVEN — Agosto 2026

**Fecha:** 19 de agosto de 2026  
**Version:** NEVEN v2.4  
**Autor:** Minor Bonilla Gomez + Kiro (Claude Sonnet 4.6)

---

## Resumen Ejecutivo

NEVEN v2.4 esta **funcional y estable**. Todos los motores (R, Python, Julia) funcionan. NEVEN Studio (Task Pane) esta completo con visualizaciones D3 y fallback Office.js para Run Script.

---

## Estado por Componente

### Nucleo XLL (NEVEN64.xll)

| Componente | Estado | Notas |
|------------|--------|-------|
| NEVEN.dll (XLL) | OK | Carga en Excel sin errores |
| ControlR.exe | OK | Embebe R 4.4.1 via C API |
| ControlPython.exe | OK | Python Stable ABI (python3.dll) |
| ControlJulia.exe | OK | Julia 1.12.6 con sysimage |
| Named Pipes IPC | OK | Protobuf v21.12 |
| NEVENRibbon.dll | OK | Pestana NEVEN en Ribbon |

### Funciones Excel

| Funcion | Estado | Descripcion |
|---------|--------|-------------|
| `=NEVEN.r("code")` | OK | Ejecuta codigo R |
| `=NEVEN.p("code")` | OK | Ejecuta codigo Python |
| `=NEVEN.j("code")` | OK | Ejecuta codigo Julia |
| `=NEVEN.v("path")` | OK | Abre viewer HTML |
| UDFs personalizadas | OK | ~90 funciones R, ~30 Julia |

### NEVEN Studio (Task Pane)

| Tab | Estado | Funcionalidades |
|-----|--------|-----------------|
| Data Studio | OK | Cargar CSV/JSON, Leer Excel, DuckDB, Quick Chart, Group By |
| SQL | OK | Queries DuckDB con paginacion |
| Run Script | OK | R/Python/Julia con fallback Office.js |
| Data Lab | OK | Modulos de analisis con R |
| Presentaciones | OK | Crear slides desde graficos |
| IA | OK | Chat con LLM |
| Ayuda | OK | Documentacion interactiva |

### Quick Chart (Grafico Rapido)

| Tipo | Motor | Estado |
|------|-------|--------|
| Barras, Lineas, Dispersion | Plotly | OK |
| Area, Pastel | Plotly | OK |
| Histograma, Box Plot | Plotly | OK |
| Heatmap | Plotly | OK |
| Mapa (Lat/Lon) | Leaflet | OK |
| Bubble, Funnel | Plotly | OK |
| Radar | Plotly | OK (scatterpolar) |
| **Treemap** | D3 v7 | OK (nuevo) |
| **Sankey** | D3 + d3-sankey | OK (nuevo) |
| **Sunburst** | D3 v7 | OK (nuevo) |

---

## Cambios Recientes (Agosto 2026)

### Sesion 19 de agosto 2026

**Commits:**
- `548172b` — Run Script fallback + D3 visualizations + UI improvements
- `93479c0` — fix: remove emojis from taskpane (encoding issues)
- `4a22c00` — fix: remove Wikipedia emoji mojibake
- `8cfb775` — fix(a11y): add for attributes to labels for accessibility

**Funcionalidades nuevas:**
1. **Run Script Fallback Office.js** — Cuando el servidor HTTP no puede conectar al pipe de R (error 503), el Task Pane ejecuta el codigo via `=NEVEN.r()` directamente en Excel.
2. **Serializacion capture.output()** — Resultados complejos de R se serializan a texto plano para evitar errores de desbordamiento.
3. **D3 Visualizations** — Treemap, Sankey, Sunburst implementados con D3 v7 en Quick Chart.
4. **Tab VIEWERS eliminado** — Redundante con Quick Chart y Run Script.
5. **Modales showConfirm/showAlert** — Compatibles con Office Add-ins (no usan window.confirm).

**Fixes:**
- Mojibake de emojis corregido (regla: emojis PROHIBIDOS)
- Labels de accesibilidad agregados
- Scroll en OUTPUT area

---

## Arquitectura Actual

```
Excel 64-bit
    |
    +-- NEVEN64.xll (C++17, MSVC)
    |       |
    |       +-- Named Pipe --> ControlR.exe --> R 4.4.1
    |       |
    |       +-- Named Pipe --> ControlPython.exe --> Python 3.x (Stable ABI)
    |       |
    |       +-- Named Pipe --> ControlJulia.exe --> Julia 1.12.6
    |
    +-- NEVENRibbon.dll (COM Add-in)
    |
    +-- Task Pane (Office.js + neven_http_server.py)
            |
            +-- DuckDB (in-memory)
            +-- Plotly.js
            +-- D3.js v7
            +-- Leaflet.js
```

---

## Limitaciones Conocidas

| Limitacion | Causa | Workaround |
|------------|-------|------------|
| Run Script lento (~2-4s) | Fallback Office.js tiene overhead IPC | Recompilar ControlR con 3ra instancia pipe (diferido) |
| Julia cold start | Sin sysimage toma ~30s | Usar sysimage `neven_julia.dll` |
| 1 pipe instance para HTTP | ControlR crea solo 2 instancias | Codigo modificado pero no compilado |

---

## Directorio de Produccion

```
C:\NEVEN\
    +-- NEVEN64.xll
    +-- ControlR.exe
    +-- ControlPython.exe
    +-- ControlJulia.exe
    +-- neven_julia.dll (sysimage, ~415MB)
    +-- startup\
    |       +-- startup.r
    |       +-- startup.jl
    |       +-- neven_http_server.py
    |       +-- pipe_client.py
    |       +-- variable_pb2.py
    +-- taskpane\
    |       +-- taskpane.html
    |       +-- datalab.js
    |       +-- taskpane.css
    +-- libreria\
            +-- R\ (~32 archivos .R)
            +-- JULIA\ (functions.jl + modulos)
```

---

## Repositorio

**GitHub:** https://github.com/minorbonillagomez/NEVEN  
**Branch:** main  
**Ultimo commit:** `8cfb775` (19 agosto 2026)

---

## Pendientes

| Prioridad | Tarea | Detalle |
|-----------|-------|---------|
| BAJA | Recompilar ControlR | 3ra instancia pipe para Run Script mas rapido |
| BAJA | Botones Expandir/Slide para D3 | Paridad con graficos Plotly |
| BAJA | Buscar mojibake residual | Grep exhaustivo del proyecto |

---

## Metricas del Proyecto

| Metrica | Valor |
|---------|-------|
| Lineas de codigo C++ | ~15,000 |
| Lineas de codigo R | ~5,000 |
| Lineas de codigo Julia | ~1,500 |
| Lineas de codigo Python | ~2,000 |
| Lineas de codigo JS/HTML | ~4,500 |
| Tests unitarios | 228 (GTest) |
| Funciones UDF exportadas | ~120 |

---

*Documento generado: 19 de agosto de 2026*
