# 08 — Análisis de Seguridad de Configuración

**Proyecto:** NEVEN  
**Fecha:** 2026-01-XX  
**Auditor:** Kiro (Auditoría Automatizada)  
**Alcance:** CMakeLists.txt, archivos JSON, GitHub Actions, .gitignore

---

## Resumen Ejecutivo

| Severidad | Hallazgos | Descripción |
|-----------|-----------|-------------|
| Crítica   | 2         | Campo apiKey en config versionado, .gitignore insuficiente |
| Alta      | 3         | Ausencia total de flags de seguridad MSVC, _CRT_SECURE_NO_WARNINGS |
| Media     | 3         | Actions sin SHA pinning, dependencias Electron desactualizadas, permisos workflow |
| Baja      | 1         | Puerto Pluto hardcodeado |
| **Total** | **9**     | |

**Hallazgos positivos:** 4

---

## Hallazgos de Seguridad

---

### 5.1 — Análisis de CMakeLists.txt (Flags de Seguridad MSVC)

### [SEC-CFG-001] Ausencia total de flags de seguridad MSVC en el proyecto
- **Archivo:** CMakeLists.txt (raíz y todos los subdirectorios)
- **Severidad:** Alta
- **Descripción:** Ninguno de los 8 archivos CMakeLists.txt del proyecto define flags de seguridad de compilación MSVC. No se encontraron `/GS` (buffer security check), `/DYNAMICBASE` (ASLR), `/NXCOMPAT` (DEP), `/guard:cf` (Control Flow Guard), `/SAFESEH` ni `/SDL`. Aunque MSVC habilita algunos por defecto (como `/GS` y `/DYNAMICBASE` en Release), no declararlos explícitamente significa que: (1) no hay garantía en todas las configuraciones, (2) no se activan protecciones avanzadas como CFG, y (3) no hay documentación de la postura de seguridad.
- **Código:**
```cmake
# CMakeLists.txt raíz — solo define supresión de warnings, sin flags de seguridad
if(MSVC)
    add_compile_definitions(_SILENCE_CXX17_OLD_ALLOCATOR_MEMBERS_DEPRECATION_WARNING ...)
endif()
```
- **Recomendación:** Agregar un bloque de seguridad en el CMakeLists.txt raíz:
```cmake
if(MSVC)
    # Security hardening flags
    add_compile_options(/GS /sdl)
    add_link_options(/DYNAMICBASE /NXCOMPAT /CETCOMPAT)
    
    # Control Flow Guard (Release only — impacto en rendimiento)
    if(NOT CMAKE_BUILD_TYPE STREQUAL "Debug")
        add_compile_options(/guard:cf)
        add_link_options(/guard:cf)
    endif()
endif()
```

---

### [SEC-CFG-002] Definición de _CRT_SECURE_NO_WARNINGS en múltiples targets
- **Archivo:** ControlR/CMakeLists.txt:88, ControlJulia/CMakeLists.txt:66, ControlPython/CMakeLists.txt:72
- **Severidad:** Alta
- **Descripción:** Los tres procesos hijo (ControlR, ControlJulia, ControlPython) definen `_CRT_SECURE_NO_WARNINGS`, lo que suprime advertencias del compilador sobre funciones inseguras de la CRT (como `strcpy`, `sprintf`, `scanf`). Estos ejecutables manejan datos provenientes de Named Pipes y podrían ser vulnerables a buffer overflows si usan funciones inseguras sin validación.
- **Código:**
```cmake
# ControlR/CMakeLists.txt
target_compile_definitions(ControlR PRIVATE
    WIN32
    _WINDOWS
    UNICODE
    _UNICODE
    _CRT_SECURE_NO_WARNINGS   # ← Suprime advertencias de seguridad CRT
)
```
- **Recomendación:** Eliminar `_CRT_SECURE_NO_WARNINGS` y migrar a las variantes seguras (`_s`) de las funciones CRT. Si la migración es gradual, limitar la supresión a archivos específicos con `#pragma warning(disable:4996)` documentando la razón.

---

### [SEC-CFG-003] Ausencia de /guard:cf en DLLs cargadas por Excel
- **Archivo:** Core/CMakeLists.txt, Ribbon/CMakeLists.txt
- **Severidad:** Alta
- **Descripción:** NEVEN_Core (NEVEN64.xll) y NEVENRibbon.dll son DLLs cargadas en el proceso de Excel. Sin Control Flow Guard (`/guard:cf`), un atacante que logre corromper memoria podría redirigir el flujo de ejecución. Dado que Excel es un objetivo frecuente de ataques, estas DLLs deberían tener las máximas protecciones.
- **Código:**
```cmake
# Core/CMakeLists.txt — sin opciones de compilación de seguridad
target_link_libraries(NEVEN_Core PRIVATE Common PB libprotobuf ...)
# No hay target_compile_options ni target_link_options de seguridad
```
- **Recomendación:** Agregar específicamente a los targets de DLL:
```cmake
if(MSVC)
    target_compile_options(NEVEN_Core PRIVATE /guard:cf /GS /sdl)
    target_link_options(NEVEN_Core PRIVATE /guard:cf /DYNAMICBASE /NXCOMPAT /CETCOMPAT)
    target_compile_options(NEVENRibbon PRIVATE /guard:cf /GS /sdl)
    target_link_options(NEVENRibbon PRIVATE /guard:cf /DYNAMICBASE /NXCOMPAT /CETCOMPAT)
endif()
```

---

### 5.2 — Verificación de Archivos JSON (Valores Sensibles)

### [SEC-CFG-004] Campo apiKey presente en neven-config.json versionado
- **Archivo:** Install/neven-config.json:43
- **Severidad:** Crítica
- **Descripción:** El archivo `Install/neven-config.json` contiene un campo `"apiKey": ""` en la sección AI. Aunque actualmente está vacío, este patrón es peligroso porque: (1) invita a los usuarios a colocar su API key directamente en el archivo, (2) el archivo está versionado en Git, y (3) las copias en `Build/Dist*/` también contienen el campo. Si algún desarrollador o usuario coloca una key real y hace commit, quedará expuesta en el historial de Git permanentemente.
- **Código:**
```json
"AI": {
    "enabled": true,
    "provider": "lmstudio",
    "apiKey": "",
    "model": "nvidia/nemotron-3-nano-4b",
    "endpoint": "http://localhost:1234/v1/chat/completions",
    "maxTokens": 1000,
    "temperature": 0.3
}
```
- **Recomendación:** 
  1. Eliminar el campo `apiKey` del archivo de configuración template.
  2. Documentar que la API key debe configurarse via variable de entorno (`NEVEN_AI_API_KEY`).
  3. Modificar `ConfigService` para leer la key desde el entorno:
  ```cpp
  std::string api_key = EnvService::get("NEVEN_AI_API_KEY", "");
  ```
  4. Agregar un archivo `.env.example` con las variables esperadas (sin valores reales).

---

### [SEC-CFG-005] Puerto Pluto hardcodeado sin validación
- **Archivo:** Install/neven-config.json:38
- **Severidad:** Baja
- **Descripción:** El puerto de Pluto está fijado en `1234`, un puerto conocido y predecible. Si otro proceso ocupa ese puerto, podría interceptar comunicaciones. No es un hallazgo crítico dado que es configurable, pero el valor por defecto debería ser menos predecible o dinámico.
- **Código:**
```json
"Pluto": {
    "port": 1234
}
```
- **Recomendación:** Considerar usar puerto 0 (asignación dinámica por el OS) o un rango alto aleatorio (49152-65535). Documentar que el puerto es configurable.

---

### 5.3 — Análisis de GitHub Actions Workflow

### [SEC-CFG-006] Actions referenciadas por tag mutable en lugar de SHA
- **Archivo:** .github/workflows/build-and-test.yml:18,21,38,41,44,52
- **Severidad:** Media
- **Descripción:** Todas las GitHub Actions están referenciadas por tags mutables (`@v4`, `@v2`) en lugar de SHA de commit. Un atacante que comprometa el repositorio de una action podría mover el tag a código malicioso (ataque de supply chain). Esto afecta a: `actions/checkout@v4`, `microsoft/setup-msbuild@v2`, `r-lib/actions/setup-r@v2`, `actions/upload-artifact@v4`.
- **Código:**
```yaml
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup MSVC
      uses: microsoft/setup-msbuild@v2

    - name: Install R
      uses: r-lib/actions/setup-r@v2
```
- **Recomendación:** Fijar cada action a un SHA específico con comentario del tag:
```yaml
    - name: Checkout
      uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

    - name: Setup MSVC
      uses: microsoft/setup-msbuild@6fb02220983dee41ce7ae257b6f4d8f9bf5ed4ce # v2.0.0
```

---

### [SEC-CFG-007] Workflow sin declaración explícita de permisos mínimos
- **Archivo:** .github/workflows/build-and-test.yml:1-10
- **Severidad:** Media
- **Descripción:** El workflow no declara `permissions` a nivel global ni por job. Por defecto, GitHub otorga `write` en todos los scopes para workflows en `push` events. Esto viola el principio de mínimo privilegio — los jobs de test solo necesitan `contents: read` y el de upload necesita `actions: write`.
- **Código:**
```yaml
name: NEVEN Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  BUILD_DIR: build
# ← No hay declaración de 'permissions'
```
- **Recomendación:** Agregar permisos mínimos:
```yaml
permissions:
  contents: read

jobs:
  unit-tests:
    permissions:
      contents: read
    # ...
  full-build:
    permissions:
      contents: read
      actions: write  # para upload-artifact
```

---

### [SEC-CFG-008] Dependencias Electron extremadamente desactualizadas en package.json
- **Archivo:** Console/package.json:16-20
- **Severidad:** Media
- **Descripción:** El package.json de Console usa `electron@^1.8.2` (2018), `electron-builder@^19.56.0`, y `typescript@^2.7.2`. Electron 1.x tiene cientos de vulnerabilidades conocidas (CVEs) incluyendo ejecución remota de código. Aunque la Console está marcada como "pendiente", si se construye o ejecuta en desarrollo, expone la máquina a riesgos significativos.
- **Código:**
```json
"devDependencies": {
    "@types/node": "^8.9.1",
    "asar": "^0.14.1",
    "electron": "^1.8.2",
    "electron-builder": "^19.56.0",
    "less-watch-compiler": "^1.11.0",
    "typescript": "^2.7.2"
}
```
- **Recomendación:** Si la Console está activa, actualizar a Electron 28+ con `contextIsolation: true` y `nodeIntegration: false`. Si está deprecada, agregar un aviso en el README y considerar eliminar el package.json o marcarlo con `"private": true, "deprecated": true`.

---

### 5.4 — Verificación de .gitignore

### [SEC-CFG-009] .gitignore raíz extremadamente insuficiente — no excluye archivos sensibles
- **Archivo:** .gitignore (raíz del proyecto)
- **Severidad:** Crítica
- **Descripción:** El `.gitignore` raíz solo excluye `BERTModule_*.gz`, `notes.md` y `yarn-error.log`. No excluye: directorio `Build/` (que contiene binarios compilados y copias de config), archivos `.env`, claves privadas (`.pem`, `.key`), archivos de depuración (`.pdb`), `node_modules/`, ni archivos de IDE. El directorio `Build/` con sus subdirectorios `Dist_STABLE_*` está actualmente en el repositorio, conteniendo ejecutables compilados y copias de `neven-config.json`.
- **Código:**
```gitignore
# folders have local .gitignore files for the various relevant types.
# this top-level folder is just for R module build artifacts

BERTModule_*.gz
notes.md

yarn-error.log
```
- **Recomendación:** Reemplazar con un `.gitignore` comprehensivo:
```gitignore
# Build artifacts
Build/
Dist/
*.xll
*.dll
*.exe
*.obj
*.pdb
*.ilk
*.lib
*.exp

# Sensitive files
.env
.env.*
*.pem
*.key
*.pfx
*.p12
neven-config.local.json

# Dependencies
node_modules/

# IDE
.vs/
*.suo
*.user

# OS
Thumbs.db
Desktop.ini

# Logs
*.log
```
Nota: El `.gitignore` de Console sí excluye `node_modules` y `build` localmente, pero la protección debe ser global.

---

## Hallazgos Positivos

| # | Aspecto | Descripción |
|---|---------|-------------|
| ✅ 1 | **Runtime estático (/MT)** | El proyecto usa `CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded"`, eliminando dependencia de MSVC redistributables y reduciendo superficie de ataque por DLL hijacking. |
| ✅ 2 | **Sandbox habilitado por defecto** | `neven-config.json` tiene `"sandboxEnabled": true`, indicando que existe un mecanismo de sandboxing para los procesos hijo. |
| ✅ 3 | **FetchContent con versiones fijas** | Las dependencias externas (Protobuf v21.12, GTest v1.14.0, WebView2 1.0.2903.40) usan versiones específicas, no ramas `main` o `latest`. |
| ✅ 4 | **No hay secretos hardcodeados en JSON** | Los archivos `constants.json`, `default_config.json`, `tsconfig.json` y `package.json` no contienen tokens, passwords ni API keys con valores reales. El campo `apiKey` está vacío (aunque su presencia es un riesgo documentado arriba). |

---

## Resumen de Acciones Requeridas

| Prioridad | Acción | Esfuerzo |
|-----------|--------|----------|
| 🔴 P0 | Actualizar `.gitignore` y verificar que `Build/` no esté trackeado | 1 hora |
| 🔴 P0 | Eliminar campo `apiKey` de config template, usar env vars | 2 horas |
| 🟠 P1 | Agregar flags de seguridad MSVC (`/GS`, `/guard:cf`, `/DYNAMICBASE`) | 1 hora |
| 🟠 P1 | Eliminar `_CRT_SECURE_NO_WARNINGS` y migrar a funciones `_s` | 4-8 horas |
| 🟡 P2 | Fijar GitHub Actions a SHA commits | 30 min |
| 🟡 P2 | Agregar `permissions` mínimos al workflow | 15 min |
| 🟡 P2 | Evaluar actualización o deprecación formal de Console/Electron | 2 horas |

---

*Fin del análisis de seguridad de configuración.*
