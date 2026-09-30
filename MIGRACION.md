# MIGRACION.md — NEVEN Project — Guía de Continuación

**Última actualización:** 2026-08-20
**Versión actual:** v2.2 (Excel Consultant + Ontologías Dinámicas)

---

## Estado del Proyecto

| Componente | Estado | Notas |
|---|---|---|
| NEVEN64.xll | ✅ Estable | Add-in principal |
| NEVENRibbon.dll | ✅ Estable | COM Ribbon |
| ControlR.exe | ✅ Estable | Motor R embebido |
| ControlJulia.exe | ✅ Estable | Motor Julia embebido |
| ControlPython.exe | ✅ Estable | Motor Python (Stable ABI) |
| NEVEN-SIM.xll | ✅ Estable | Simulación Monte Carlo |
| Task Pane (Studio) | ✅ v3.0 | DataLab, Chat, Pluto, Run Script |
| **Excel Consultant** | ✅ NUEVO | Auditoría y documentación de hojas |
| **Ontologías Dinámicas** | ✅ NUEVO | Sistema autoevolutivo de conocimiento |
| AgentService | ✅ Estable | neven_ai_service.py |

---

## Estructura del Workspace (Agosto 2026)

```
F:\ANTIGRAVITY\2026\NEVEN\
├── .agents/                  ← Skills de Kiro
│   └── skills/
│       ├── metaheuristic-optimization/
│       └── ontology-book-processor/
├── .kiro/                    ← Configuración Kiro
│   ├── contexto/CHAT.md        Bitácora persistente del proyecto
│   ├── hooks/                  Hooks de automatización
│   ├── skills/                 Links a .agents/skills/
│   └── steering/               Reglas de proyecto
├── .vscode/                  ← Configuración VSCode
├── MIGRACION.md              ← Este archivo
│
├── NEVEN/                    ← REPOSITORIO GIT PRINCIPAL
│   ├── AgentService/           neven_ai_service.py (Excel Consultant prompt)
│   ├── Common/                 Common.lib
│   ├── ControlJulia/           ControlJulia.exe
│   ├── ControlPython/          ControlPython.exe + startup/
│   ├── ControlR/               ControlR.exe
│   ├── Core/                   NEVEN64.xll (NEVEN_Core)
│   ├── docs/                   Documentación técnica
│   ├── libreria/               Funciones R (63), Julia (9), Python
│   ├── NEVEN-SIM/              Módulo Monte Carlo
│   ├── Ribbon/                 NEVENRibbon.dll
│   ├── TaskPane/               taskpane.html/js + neven_http_server.py
│   ├── tests/                  228 tests GTest
│   └── ...
│
└── ONTOLOGIA/                ← SISTEMA DE CONOCIMIENTO
    ├── LIBROS/                 Econometría (Wooldridge, Greene, Hamilton)
    │   └── memory/ontology/
    │       ├── schema.yaml
    │       └── graph.jsonl
    ├── LIBROS EXCEL/           Funciones Excel nativas (113 funciones)
    │   ├── *.pdf               CFI, Curso Práctico, Excel Bible
    │   └── memory/ontology/
    │       ├── schema.yaml
    │       └── graph.jsonl
    └── NEVEN/                  Funciones NEVEN (R/Julia/Python)
        └── memory/ontology/
            ├── schema.yaml     NEVENFunction, RFunction, JuliaFunction
            └── graph.jsonl     40 entidades + relaciones
```

---

## Nueva Funcionalidad: Excel Consultant

El Excel Consultant es un modo del agente AI que actúa como auditor y documentador de hojas de cálculo.

### Capacidades:
1. **Auditoría** — Detectar errores, fórmulas frágiles, hardcoding
2. **Documentación** — Explicar qué hace una hoja, flujo de datos
3. **Optimización** — Sugerir fórmulas mejores (BUSCARV→BUSCARX)
4. **Educación** — Enseñar sobre funciones y best practices
5. **Creación de funciones** — Escribir R/Julia/Python cuando Excel no alcanza
6. **Expansión de conocimiento** — Procesar libros PDF para expandir ontologías

### Activación:
Se activa automáticamente cuando el usuario hace clic en "Analizar Hoja" en el TaskPane.

### Archivos clave:
- `AgentService/neven_ai_service.py` — `_EXCEL_CONSULTANT_PROMPT`
- `TaskPane/taskpane.js` — `captureSheetForAnalysis()`

---

## Nueva Funcionalidad: Ontologías Dinámicas

NEVEN es ahora un **sistema autoevolutivo de conocimiento**. El agente puede:

1. **Crear funciones** → Actualizar `ONTOLOGIA/NEVEN/memory/ontology/graph.jsonl`
2. **Procesar libros** → Expandir cualquier ontología con nuevo conocimiento
3. **Personalizar dominios** → Usuario agrega PDFs, agente extrae conocimiento

### Ontologías disponibles:

| Ontología | Entidades | Propósito |
|-----------|-----------|-----------|
| LIBROS EXCEL | 113 funciones | Excel nativo (SUM, VLOOKUP, etc.) |
| NEVEN | 40 funciones | Funciones R/Julia/Python de NEVEN |
| LIBROS | Conceptos | Econometría teórica |

### Ciclo evolutivo:
```
Usuario pide función → Agente busca en ontología → No existe →
Agente CREA función → Agente ACTUALIZA ontología →
Próxima sesión YA CONOCE la función
```

---

## Cómo Retomar el Proyecto

### Rutas importantes
```
Workspace:    F:\ANTIGRAVITY\2026\NEVEN\
Repo Git:     F:\ANTIGRAVITY\2026\NEVEN\NEVEN\
Producción:   C:\NEVEN\
Ontologías:   F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\
Bitácora:     F:\ANTIGRAVITY\2026\NEVEN\.kiro\contexto\CHAT.md
```

### Build completo
```powershell
cd F:\ANTIGRAVITY\2026\NEVEN\NEVEN
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean
```

### Build incremental
```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

### Deploy a producción
```powershell
# Copiar binarios a C:\NEVEN\
# Copiar TaskPane, libreria, startup, configs
```

---

## Entornos y Dependencias

| Herramienta | Versión | Uso |
|---|---|---|
| Visual Studio | 2022 Community | Build C++ |
| Python | 3.13.x | ControlPython + AgentService |
| R | 4.4.1 | ControlR |
| Julia | 1.12.6 | ControlJulia |
| CMake | 3.15+ | Build system |
| Protobuf | v21.12 | IPC (FetchContent) |
| GTest | v1.14.0 | Tests (FetchContent) |

---

## Commits Recientes (Agosto 2026)

| Hash | Descripción |
|------|-------------|
| `fc93d68` | feat(consultant): add book processing protocol for customizable ontologies |
| `bf69956` | feat(consultant): add dynamic ontology protocol |
| `40ab2c8` | feat(taskpane): contextual chips for Excel Consultant |
| `309ae11` | feat(analyzer): connect sheet_analyzer to graph.jsonl ontology |
| `289eb30` | feat(translations): add excel_translations.py with 482 mappings |

---

## Próximos Pasos

1. **Deploy a producción** — Copiar cambios a `C:\NEVEN\`
2. **Probar ciclo completo** — Crear función → actualizar ontología → verificar persistencia
3. **Documentar en Docusaurus** — Nueva sección "Sistema de Conocimiento"
4. **Expandir ontología NEVEN** — Documentar las ~90 funciones R restantes

---

*Generado: 2026-08-20 — NEVEN v2.2*
