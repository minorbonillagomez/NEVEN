# NEVEN: Quality Assurance & Testing Report

## Resumen Ejecutivo

Este documento certifica la robustez, estabilidad y seguridad de **NEVEN** v2.0 a nivel de producción. El proyecto ha superado una auditoría de seguridad exhaustiva (36 hallazgos, todos remediados) y mantiene una batería de 357 pruebas automatizadas con 100% de aprobación.

**Resultado Actual:** `100% tests passed, 0 tests failed out of 357`

---

## Estrategia de Pruebas (Testing Strategy)

El proyecto utiliza un enfoque moderno de validación apoyado en **Google Test v1.14.0**, **Google Mock**, **rapidcheck** (property-based testing) y coordinado mediante **CTest** a través de `CMake`.

### Categorías de Tests

| Categoría | Tests | Descripción |
|-----------|-------|-------------|
| Sandbox (R + Julia + Python) | 154 | Verificación de patrones bloqueados, bypass prevention, idempotencia |
| Property-Based Tests (PBT) | 24 | Propiedades formales validadas con rapidcheck (100+ iteraciones) |
| Input Sanitization | 21 | Allowlist de caracteres, idempotencia, BuildSafeCommandLine |
| IPC / Protobuf | 6 | Frame/Unframe round-trip, rechazo de datos inválidos |
| Pipe Lifecycle (RAII) | 8 | SafePipeHandle: creación, move, cleanup, atomic ops |
| Repository Hygiene | 14 | .gitignore, CI permissions, dead code absence |
| Build Verification | 4 | MSVC security flags presentes en CMakeLists.txt |
| Type Conversion & RAII | 34 | XLOPER12 lifecycle, serialización |
| Integration / E2E | 12 | Named Pipe lifecycle, Console independence |
| Otros (Config, Discovery, etc.) | 80 | ConfigService, LanguageService, COM, callbacks |
| **Total** | **357** | |

### 1. Property-Based Testing (PBT)

Se formalizaron 9 propiedades de correctitud validadas con rapidcheck:

| # | Propiedad | Archivo |
|---|-----------|---------|
| 1 | InputSanitizer allowlist correctness | `tests/input_sanitizer_pbt.cc` |
| 2 | InputSanitizer idempotence | `tests/input_sanitizer_pbt.cc` |
| 3 | Sandbox execution path equivalence | `tests/sandbox_path_pbt.cc` |
| 4 | Sandbox blocklist enforcement | `tests/sandbox_blocklist_pbt.cc` |
| 5 | Sandbox error message specificity | `tests/sandbox_blocklist_pbt.cc` |
| 6 | Sandbox verification idempotence | `tests/sandbox_path_pbt.cc` |
| 7 | Protobuf Frame/Unframe round-trip | `tests/protobuf_ipc_pbt.cc` |
| 8 | Protobuf Unframe rejects invalid data | `tests/protobuf_ipc_pbt.cc` |
| 9 | Environment variable lookup priority | `tests/env_lookup_pbt.cc` |

### 2. Manejo Determinista de Memoria (RAII)

- `RaiiXlOper`: Destrucción determinista de estructuras XLOPER12
- `SafePipeHandle`: RAII para handles de Named Pipes con CRITICAL_SECTION
- `UniqueHandle`: Wrapper genérico para handles de Windows

### 3. Capa de Aislamiento y Mocks

Los módulos principales usan interfaces virtuales para inyección de dependencias:
- `MockExcelBridge`: Simula la API de Excel para tests sin Excel instalado
- `mock_engine_backend.exe`: Simula un motor de lenguaje para tests IPC

### 4. Seguridad

La suite de seguridad valida:
- **InputSanitizer**: Allowlist de caracteres para rutas y argumentos
- **SandboxVerifier**: 30+ patrones bloqueados por lenguaje, 5 mecanismos anti-bypass
- **MessageValidator**: Validación de frames Protobuf antes de deserialización
- **SafePipeHandle**: Operaciones atómicas que previenen TOCTOU
- **MSVC flags**: /GS, /guard:cf, /sdl, /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT

---

## Auditoría de Seguridad

Se realizó una auditoría estática completa del código fuente (ver `docs/INFORME_AUDITORIA.md`):

| Severidad | Hallazgos | Remediados |
|-----------|-----------|------------|
| Crítica | 8 | 8 ✅ |
| Alta | 7 | 7 ✅ |
| Media | 5 | 5 ✅ |
| Baja | 14 | 14 ✅ |
| Informativa | 2 | 2 ✅ |
| **Total** | **36** | **36 ✅** |

### Acciones principales:
1. InputSanitizer centralizado para todas las llamadas a CreateProcess
2. SandboxVerifier extendido y aplicado a REPL + AutoLoader
3. MessageValidator para validación de frames IPC
4. SafePipeHandle RAII con operaciones atómicas
5. Flags de seguridad MSVC aplicados globalmente
6. Console/Electron eliminado (50+ CVEs, reemplazado por WebView2 REPL)
7. ControlPython reactivado (4 bugs de estabilidad resueltos: retry, SEH, single-block, health check)
8. Código muerto eliminado, funciones duplicadas consolidadas

---

## Módulos Eliminados

| Módulo | Razón | Reemplazo |
|--------|-------|-----------|
| Console/ (Electron 1.8.2) | 50+ CVEs, 5 XSS, nodeIntegration sin sandbox | WebView2 REPL (REPLManager + REPLBridge) |
| ControlPython/ | Deprecado, causaba hangs | Ninguno (Python OFF permanente) |
| libreria/PYTHON/ | Scripts huérfanos sin runtime | Ninguno |

---

## Ejecución de Tests

```powershell
# Build + test completo
.\build.ps1 -Test

# Solo tests (si ya compiló)
cd Build
ctest --output-on-failure -C Release --timeout 120

# Tests de seguridad específicos
ctest --output-on-failure -C Release -R "InputSanitizer|Sandbox|Protobuf|PipeLifecycle"

# Tests de property-based testing
ctest --output-on-failure -C Release -R "PBT|pbt"
```

---

## Estructura de Archivos de Test

```
tests/
├── input_sanitizer_pbt.cc      — PBT: allowlist + idempotencia
├── input_sanitizer_tests.cc    — Unit: metacaracteres, edge cases
├── sandbox_path_pbt.cc         — PBT: path equivalence + idempotencia
├── sandbox_blocklist_pbt.cc    — PBT: blocklist enforcement + specificity
├── sandbox_tests.cc            — Unit: 154 tests de patrones bloqueados
├── python_sandbox_pbt.cc       — PBT: patrones Python
├── protobuf_ipc_pbt.cc         — PBT: round-trip + invalid data rejection
├── pipe_lifecycle_tests.cc     — Unit: SafePipeHandle RAII
├── env_lookup_pbt.cc           — PBT: prioridad NEVEN_ > RJ2XCL_ > BERT_
├── build_verification_tests.cc — Unit: MSVC flags en CMakeLists.txt
├── repo_hygiene_tests.cc       — Unit: .gitignore, CI, dead code
├── r_library_tests.cc          — Unit: ausencia de eval(parse())
├── integration_tests.cc        — E2E: IPC lifecycle, Console independence
├── security_tests.cc           — Unit: SecurityService SHA-256
├── config_service_tests.cc     — Unit: ConfigService
├── common_tests.cc             — Unit: utilidades comunes
├── mock_engine_backend.cc      — Ejecutable mock para tests IPC
└── CMakeLists.txt              — Build configuration
```

---

*Última actualización: Mayo 2026 — Post auditoría de seguridad y remediación completa.*


---

## NEVEN-SIM: Simulación Monte Carlo (Julio 2026)

### Tests Automatizados

NEVEN-SIM incluye 69 tests unitarios organizados en 6 suites:

| Suite | Tests | Cobertura |
|:---|:---|:---|
| SimBridge | 5 | Detección de NEVEN base, CallR/CallJulia |
| SimEngine | 13 | State machine, pipeline, callbacks |
| FitService | 11 | JSON/text parsing, code generation, AIC ranking |
| MonteCarloService | 15 | Distribution mapping, Julia code gen |
| SensitivityService | 11 | Spearman parsing, formatting |
| Integration | 14 | Pipeline end-to-end, Excel helpers |

### Build y Ejecución de Tests

```bash
# Configurar con NEVEN-SIM habilitado
cmake -DBUILD_NEVEN_SIM=ON -DSKIP_LANGUAGE_TARGETS=ON -G "Visual Studio 17 2022" -A x64 ..

# Compilar tests
cmake --build . --target NEVEN_SIM_Tests --config Release

# Ejecutar
.\Build\NEVEN-SIM\tests\Release\NEVEN_SIM_Tests.exe --gtest_brief=1
```

### Archivos del Módulo

```
NEVEN-SIM/
├── CMakeLists.txt               # Build del XLL
├── NEVEN-SIM.rc                 # Recursos (version info)
├── neven-sim-config.json        # Configuración
├── include/                     # 7 headers
│   ├── sim_engine.h
│   ├── sim_bridge.h
│   ├── fit_service.h
│   ├── montecarlo_service.h
│   ├── sensitivity_service.h
│   ├── sim_viewer.h
│   ├── sim_exports.h
│   ├── sim_excel_helpers.h
│   └── bridge_poller.h
├── src/                         # 9 implementaciones
│   ├── sim_main.cc              # xlAutoOpen, funciones Excel
│   ├── sim_bridge.cc            # Relay a NEVEN base
│   ├── sim_engine.cc            # Orquestador pipeline
│   ├── fit_service.cc           # Fitting via R
│   ├── montecarlo_service.cc    # MC via Julia
│   ├── sensitivity_service.cc   # Spearman
│   ├── sim_viewer.cc            # WebView2 workspace
│   ├── sim_excel_helpers.cc     # Range extraction
│   ├── bridge_poller.cc         # JS→Excel polling
│   └── neven_sim.def            # Exports
├── workspace/                   # HTML viewers
│   ├── sim-report-template.html # Explorador reactivo
│   ├── demo-reactive.html       # Demo standalone
│   └── demo-bridge.html         # Demo PostMessage
├── libreria/
│   ├── R/neven_sim_fit.R        # Funciones R
│   └── JULIA/NEVENSim.jl       # Módulo Julia
└── tests/                       # 6 archivos de test
```

### Troubleshooting NEVEN-SIM

| Síntoma | Causa | Solución |
|:---|:---|:---|
| Excel crash al cargar XLL | xlUDF llamado durante xlAutoOpen | Verificar que Initialize() NO llama DetectNevenBase() |
| "BLOCKED: library()" | Security system de NEVEN | Usar `requireNamespace()` + prefijo `fitdistrplus::` |
| "BLOCKED: open()" | Security system | Usar `write(path, content)` en vez de `open()` |
| "Julia call failed" | `Main.` bloqueado | Usar `global` en vez de `Main._var` |
| SIM.Datos retorna menos filas | Límite del pipe (~32KB) | Usar SIM.Exportar() para dataset completo |
| Viewer no abre | NEVEN64.xll viejo | Recompilar NEVEN_Core con PostMessageBridge actualizado |
