# Plan de Trabajo: Modernización Arquitectónica NEVEN 🚀 [COMPLETADO]

Este plan detalla las historias de usuario y tareas necesarias para implementar las mejoras propuestas en el [Reporte de Arquitectura](file:///C:/Users/mboni/.gemini/antigravity/brain/47495aeb-b40b-4128-91f6-0b4058ed62f2/architectural_report.md).

---

## 🏗️ Epic: Proyecto NEVEN - Fase de Refactorización

### User Story 1: Estandarización de SOPs (Capa 1)
**Como** desarrollador del proyecto  
**Quiero** tener reglas claras y procedimientos estándar  
**Para que** el código sea consistente y fácil de mantener entre colaboradores.

#### Acceptance Criteria
- [x] Documento `coding-standards.md` creado con reglas de nomenclatura.
- [x] Documento `error-handling.md` creado definiendo el uso de `Result`.
- [x] Los documentos están accesibles en `/docs/sops/`.

**Status**: ✅ COMPLETADO

---

### User Story 2: Limpieza de Identidad (Legacy NEVEN)
**Como** usuario final e ingeniero  
**Quiero** que el proyecto use exclusivamente el nombre NEVEN  
**Para evitar** confusiones con la versión anterior (NEVEN).

#### Acceptance Criteria
- [x] Clase `NEVEN` renombrada a `Engine` o `RJ2XCL_Engine`.
- [x] Archivos físicos `RJ2XCL_*.cpp` renombrados.
- [x] Claves de registro y recursos internos actualizados.

**Status**: ✅ COMPLETADO

---

### User Story 3: Implementación de Código Determinista (Patrón Result)
**Como** desarrollador  
**Quiero** un sistema de manejo de errores unificado  
**Para que** las funciones sean predecibles y fáciles de depurar.

#### Acceptance Criteria
- [x] Template `Result<T, E>` implementado en `Common/result.h`.
- [x] Refactorización de utilidades en `Common` para usar `Result`.

**Status**: ✅ COMPLETADO

---

### User Story 4: Desacoplamiento del Núcleo (Modularización)
**Como** arquitecto  
**Quiero** separar las responsabilidades de la clase principal  
**Para** reducir la complejidad ciclomática y mejorar la testabilidad.

#### Acceptance Criteria
- [x] Creación de `ConfigService` (JSON/Registry).
- [x] Extracción de `LanguageManager`.
- [x] Extracción de `WindowManager`.
- [x] Test unitarios para los nuevos servicios.

**Status**: ✅ COMPLETADO

---

## 📋 Backlog de Tareas por Sprint

### Sprint 1: Cimientos y Limpieza (2 semanas)
**Meta**: Eliminar rastro de NEVEN y establecer estándares.
- [x] **Task 1.1**: Crear estructura de directorios `/docs/sops/` (1h)
- [x] **Task 1.2**: Escribir `coding-standards.md` (2h)
- [x] **Task 1.3**: Refactorizar nombres de archivos `RJ2XCL_*.cpp` a `RJ_*.cc` (4h)
- [x] **Task 1.4**: Renombrar clase `NEVEN` y sus instancias en el código (6h)
- [x] **Task 1.5**: Actualizar claves de registro literales (2h)

### Sprint 2: Robustez (2 semanas)
**Meta**: Implementar el patrón de manejo de errores.
- [x] **Task 2.1**: Desarrollar `Common/result.h` (4h)
- [x] **Task 2.2**: Refactorizar `FileContents` y `ReadConfigFile` para usar `Result` (4h)
- [x] **Task 2.3**: Escribir `error-handling.md` con ejemplos prácticos (2h)

### Sprint 3: Desacoplamiento (2 semanas)
- [x] **Task 3.1**: Crear `ConfigService` y migrar lógica de lectura de JSON/Registro
- [x] **Task 3.2**: Crear `LanguageManager` y migrar servicios de lenguaje
- [x] **Task 3.3**: Documentar nueva arquitectura modular

### Sprint 4: Calidad y CI/CD (2 semanas)
- [x] **Task 4.1**: Configurar GoogleTest en CMake
- [x] **Task 4.2**: Implementar suite de pruebas para `Common`
- [x] **Task 4.3**: Automatizar ejecución de tests en el flujo de trabajo (build.ps1)

### Sprint 5: Pulido de Identidad y WindowManager (2 semanas)
- [x] **Task 5.1**: Reemplazar `config["NEVEN"]` por `config["NEVEN"]`
- [x] **Task 5.2**: Renombrar namespace `RJ2XCLGraphics` a `RJ2XCLGraphics`
- [x] **Task 5.3**: Extraer `WindowManager` de `RJ2XCL_Engine`
- [x] **Task 5.4**: Actualizar nombres de proyectos en CMakeLists y archivos `.rc`

---
**Plan COMPLETADO siguiendo las guías de Task Planning.**
