# Plan de Trabajo: Modernización NEVEN - FASE 3 🚀

Este plan ha sido elaborado siguiendo los principios del **Escuadrón BLAST** y el skill de **Task Planning**, basándose en el [Análisis Arquitectónico v3.0](file:///C:/Users/mboni/.gemini/antigravity/brain/47495aeb-b40b-4128-91f6-0b4058ed62f2/architectural_status_v3.md).

---

## 🏗️ Epics de la Fase 3

### Epic 1: Robustez y Seguridad de Memoria (RAII)
**Objetivo**: Eliminar riesgos de fugas de memoria y punteros colgantes en la interacción con el SDK de Excel mediante la implementación de envoltorios RAII deterministas.

### Epic 2: QA & CI/CD Hub
**Objetivo**: Establecer una infraestructura de pruebas automatizadas que valide la integridad de la orquestación y los servicios del motor en cada fase de build.

### Epic 3: Extensibilidad y Blindaje (Security)
**Objetivo**: Mejorar el descubrimiento de entornos de ejecución y añadir capas de validación de seguridad para scripts externos.

---

## 📋 Historias de Usuario (INVEST)

### User Story 1: Gestión de Tipos Excel Segura
**Como** desarrollador de sistemas  
**I want** usar un wrapper `RaiiXlOper` para tipos `XLOPER12`  
**So that** la memoria de Excel sea liberada automáticamente al salir del scope.

#### Acceptance Criteria
- [ ] Dado un `XLOPER12` complejo Cuando se instancia `RaiiXlOper` Entonces se gestiona el `xlbitXLFree`.
- [ ] Dado el fin de un scope de función Cuando el objeto `RaiiXlOper` se destruye Entonces la memoria se libera sin fugas.
- [ ] Dado el registro de una función Cuando se usan tipos RAII Entonces el código es legible y libre de `new`/`delete` manuales.

**Story Points**: 8 | **Priority**: Must Have

---

### User Story 2: Validación de Integridad en el Build
**Como** ingeniero de QA  
**I want** que los tests críticos se ejecuten en cada build de CMake/GTest  
**So that** los errores de orquestación no lleguen a producción.

#### Acceptance Criteria
- [ ] Dado un cambio en el core Cuando se ejecuta `build.ps1` Entonces se reportan los resultados de GTest.
- [ ] Dado el `MockExcelBridge` Cuando se ejecutan tests de orquestación Entonces se valida el flujo sin abrir Excel.
- [ ] Dado `common_tests.cc` Cuando se compila el proyecto Entonces no hay errores de linting o linkado.

**Story Points**: 5 | **Priority**: Must Have

---

### User Story 3: Descubrimiento Proactivo de Entornos
**Como** usuario final  
**I want** que NEVEN detecte mis instalaciones de R y Julia automáticamente  
**So that** no tenga que configurar manualmente las rutas de sistema.

#### Acceptance Criteria
- [ ] Dado una instalación estándar de R Cuando se inicia NEVEN Entonces el `DiscoveryService` localiza el home.
- [ ] Dado múltiples versiones de Julia Cuando se abre la configuración Entonces el usuario puede seleccionar el entorno activo.

**Story Points**: 8 | **Priority**: Should Have

---

## 🗓️ Planificación de Sprints

### Sprint 9: Estabilidad y RAII (1 semana)
- **Meta**: 100% seguridad de memoria en el bridge de Excel.
- **Tareas**:
  - [ ] Implementar framework `RaiiXlOper` y `XlOperGuard` (4h)
  - [ ] Refactorizar `RegisterFunctions` y `UnregisterFunctions` (6h)
  - [ ] Migrar conversores en `type_conversions.cc` a RAII (6h)

### Sprint 10: QA e Infraestructura (1 semana)
- **Meta**: Suite de tests estabilizada y automatizada.
- **Tareas**:
  - [ ] Configurar GTest en CMake para el entorno local (4h)
  - [ ] Arreglar lints y dependencias en `common_tests.cc` (4h)
  - [ ] Implementar tests para `CallbackDispatcher` y Handlers (6h)

### Sprint 11: Seguridad y Despliegue (1 semana)
- **Meta**: Blindaje de ejecución y telemetría estructurada.
- **Tareas**:
  - [ ] Implementar `DiscoveryService` (Registry/Paths scan) (6h)
  - [ ] Implementar `LogService` (Estructurado a archivo/consola) (4h)
  - [ ] Validación de hash en carga de scripts de usuario (6h)

---

## 🚦 Definición de Hecho (DoD)
- [ ] Código compilado sin warnings en x64/Release.
- [ ] Suite de tests unitarios al 100% de éxito.
- [ ] Cero fugas de memoria detectadas en tests de stress.
- [ ] Documentación técnica actualizada en `DocsDelProyecto`.

---
**Plan aprobado por el Escuadrón BLAST bajo estándares INVEST.**
