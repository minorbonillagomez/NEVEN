# Registro de Decisiones de Implementación: Refactorización de Identidad 📝

## Decisión: Renombrado de Clase Principal

**Fecha**: 2026-03-16  
**Tarea**: Sprint 1 - Task 1.4

### Contexto
La clase principal del proyecto se llamaba `NEVEN`, heredada del proyecto original. Esto causaba confusión en el código y no reflejaba el nuevo branding `NEVEN`.

### Cambio Realizado
- **Anterior**: `class NEVEN`
- **Nuevo**: `class RJ2XCL_Engine`

### Justificación
Se eligió `RJ2XCL_Engine` para:
1.  Reflejar claramente el nombre del proyecto.
2.  Indicar su propósito como el motor central de orquestación.
3.  Facilitar la transición hacia la modularización (Capa 2) donde este "motor" se dividirá en servicios menores.

### Impacto
Este cambio requiere la actualización de:
- `include/NEVEN.h`
- `src/NEVEN.cc`
- Todo el código que utiliza el singleton `NEVEN::Instance()`.

---
**Firmado**: Developer (BMAD Suite)
