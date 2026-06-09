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
