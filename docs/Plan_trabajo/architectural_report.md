# Reporte de Arquitectura: Proyecto NEVEN 🏗️

Como **Ingeniero Senior del Escuadrón BLAST**, he analizado la estructura y el código del proyecto NEVEN tras la migración desde NEVEN. Basado en los principios de la **Arquitectura de 3 Capas** y **Código Determinista**, presento mis hallazgos y propuestas de mejora.

## 1. Análisis del Estado Actual

### 🔍 Hallazgos Principales

*   **Ausencia de SOPs (Capa 1):** No existe documentación estandarizada sobre convenciones de código, manejo de errores uniformes o flujos de trabajo.
*   **Núcleo Monolítico (Capa 2/3):** La clase `NEVEN` (en `NEVEN.cc`) centraliza demasiadas responsabilidades: carga de archivos, gestión de lenguajes, manejo de ventanas de Windows, registro en Excel y callbacks de sistema.
*   **Convenciones de Nomenclatura Mixtas:** Se observa una mezcla de `PascalCase` y `snake_case`, además de archivos con extensiones `.cc` y `.cpp` de forma inconsistente.
*   **Manejo de Errores Fragmentado:** Se utilizan valores de retorno `bool`, enums personalizados (`FileError`) y códigos de retorno `int` de forma no estandarizada.
*   **Residuos de Legacy:** Persisten nombres de clases (`class NEVEN`), claves de registro (`RJ2XCL2.DevOptions`) y nombres de archivos (`RJ2XCL_Main.cpp`) que no reflejan el rebranding final.

---

## 2. Propuestas de Mejora (3 Capas)

### 📄 Capa 1: SOPs y Estándares
**Objetivo:** Crear una base sólida de conocimiento para el equipo.
*   **Acción:** Crear `/docs/sops/` con:
    *   `coding-standards.md`: Definir `snake_case` para funciones y `PascalCase` para clases.
    *   `error-handling.md`: Documentar el nuevo patrón `Result`.

### 🔀 Capa 2: Modularización y Rutas
**Objetivo:** Desacoplar la lógica de negocio del pegamento con Excel.
*   **Acción:** Dividir la clase `NEVEN` (renombrada a `RJ2XCL_Engine`) en servicios específicos:
    *   `ConfigService`: Para el manejo de JSON y registro.
    *   `LanguageManager`: Exclusivo para la orquestación de lenguajes (R, Julia).
    *   `WindowManager`: Para la manipulación de la consola y callbacks de Windows.

### 🛠️ Capa 3: Herramientas Deterministas
**Objetivo:** Código que funcione a la primera y sea testeable.
*   **Acción:**
    *   Implementar un template `Result<T, E>` en `Common/result.h` para unificar el retorno de errores.
    *   Mover utilidades genéricas de `NEVEN.cc` a funciones puras en `Common/string_utilities.h` o similar.
    *   Estandarizar todas las extensiones de archivos a `.cc` para uniformidad en el sistema de build.

---

## 3. Plan de Acción Recomendado

1.  **Fase 1 (Limpieza)**: Renombrar `class NEVEN` a `Engine` y actualizar los archivos `RJ2XCL_*.cpp` restantes.
2.  **Fase 2 (Documentación)**: Implementar los primeros SOPs en `/docs/sops/`.
3.  **Fase 3 (Refactorización)**: Introducir el patrón `Result` en la capa de servicios (`Common`).
4.  **Fase 4 (Desacoplamiento)**: Extraer la lógica de configuración y gestión de archivos de la clase principal.

> [!TIP]
> Priorizar la implementación del patrón `Result` permitirá que las futuras features sean mucho más robustas y fáciles de depurar usando la sub-rutina de Self-Healing.

---
**Reporte preparado por:** Skill A (Arquitecto) - Escuadrón BLAST.
