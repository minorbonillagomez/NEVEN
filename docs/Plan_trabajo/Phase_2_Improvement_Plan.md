# Plan de Trabajo: Modernización NEVEN - FASE 2 🚀

Este plan detalla las historias de usuario y tareas para la **Fase 2** de la modernización de NEVEN, enfocada en la testabilidad, extensibilidad y desacoplamiento total del host.

---

## 🏗️ Epics de la Fase 2

### 1. Abstracción del Puente Excel (Capa 3)
**Objetivo**: Aislar el motor de las dependencias directas del SDK de Excel para permitir pruebas unitarias sin el host.

### 2. Dispatcher de Callbacks (Capa 2)
**Objetivo**: Refactorizar el manejo centralizado de callbacks usando un sistema basado en eventos o registro de manejadores.

### 3. Propagación Determinista (Result Pattern)
**Objetivo**: Extender el uso de `Result<T, E>` a toda la lógica de orquestación y comunicación.

### 4. Sincronización de Metadatos y Licencias
**Objetivo**: Limpiar residuos de "NEVEN" en archivos de proyecto y actualizar encabezados legales.

---

## 📋 Historias de Usuario (INVEST)

### User Story 1: Servicio de Puente Excel
**Como** desarrollador  
**I want** un servicio `ExcelBridgeService` que abstraiga `XLCALL.h`  
**So that** pueda simular el comportamiento de Excel en entornos de prueba.

#### Acceptance Criteria
- [x] Interfaz `IExcelBridge` definida con métodos para `Excel12` y `Excel12v`.
- [x] Implementación `WinExcelBridge` que use el SDK real.
- [x] Implementación `MockExcelBridge` para tests automáticos.
- [x] No hay llamadas directas a `Excel12` fuera del servicio.

**Story Points**: 8 | **Priority**: Must Have

---

### User Story 2: Sistema de Despacho de Eventos
**Como** arquitecto  
**I want** un sistema donde los handlers de gráficos y COM se registren independientemente  
**So that** `HandleCallbackOnThread` no sea una función monolítica.

#### Acceptance Criteria
- [x] Clase `CallbackDispatcher` implementada.
- [x] `GraphicsHandler` extraído y registrado en el dispatcher.
- [x] `COMHandler` extraído y registrado en el dispatcher.
- [x] Reducción de la complejidad ciclomática de `NEVEN.cc`.

**Story Points**: 13 | **Priority**: Should Have

---

## 🗓️ Planificación de Sprints

### Sprint 6: Abstracción Core (2 semanas)
- [x] **Task 6.1**: Implementar `ExcelBridgeService` e integrarlo en `RJ2XCL_Engine` (6h)
- [x] **Task 6.2**: Migrar conversores de tipos para usar el nuevo puente (4h)
- [x] **Task 6.3**: Crear tests unitarios usando `MockExcelBridge` (6h)

### Sprint 7: Modularización de Callbacks (2 semanas)
- [x] **Task 7.1**: Implementar el framework de `CallbackDispatcher` (4h)
- [x] **Task 7.2**: Refactorizar lógica de Gráficos a un handler independiente (6h)
- [x] **Task 7.3**: Refactorizar lógica de COM a un handler independiente (6h)

### Sprint 8: Pulido y Metadatos (1 semana)
- [x] **Task 8.1**: Propagar `Result` en los nuevos handlers (4h)
- [x] **Task 8.2**: Sincronizar archivos `.vcxproj` y encabezados de licencia (2h)
- [x] **Task 8.3**: Verificación final de integración (4h)

---

## 🚦 Definición de Hecho (DoD)
- [x] Código compilado sin warnings.
- [x] Cobertura de tests unitarios > 70% en nuevas clases.
- [x] Documentación técnica actualizada en `/docs`.
- [x] PR aprobado por el Arquitecto Senior.

---
**Plan elaborado siguiendo las guías de Task Planning para FASE 2.**
