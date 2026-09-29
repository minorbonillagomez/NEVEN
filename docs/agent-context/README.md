# Contexto para Agentes de IA — NEVEN

> **INSTRUCCIÓN OBLIGATORIA:** Antes de realizar CUALQUIER cambio en el código de NEVEN, 
> lee los documentos en esta carpeta en el orden indicado.

---

## Orden de lectura obligatorio

| # | Documento | Propósito |
|---|-----------|-----------|
| 1 | `CHECKLIST_PRE_CAMBIOS.md` | Verificaciones antes de modificar cualquier archivo |
| 2 | `INVARIANTES.md` | Reglas técnicas que NUNCA deben violarse |
| 3 | `COMO_AGREGAR_FUNCIONES.md` | Proceso para agregar nueva funcionalidad |
| 4 | `ALIASES.md` | Sistema de nombres cortos y cómo extenderlo |

---

## ¿Qué es NEVEN?

NEVEN es un add-in para Microsoft Excel que integra R, Julia y Python como motores de scripting. 
Permite ejecutar funciones estadísticas, modelos de ML y visualizaciones desde celdas de Excel.

**Componentes principales:**
- `NEVEN64.xll` — Add-in XLL cargado por Excel
- `ControlR.exe` — Proceso que ejecuta código R
- `ControlJulia.exe` — Proceso que ejecuta código Julia
- `ControlPython.exe` — Proceso que ejecuta código Python
- `NEVEN Studio` — TaskPane con UI para análisis interactivo

---

## Ubicaciones importantes

| Qué | Ruta |
|-----|------|
| Funciones R/Julia | `C:\NEVEN\functions\` |
| Sidecars JSON | `C:\NEVEN\functions\*.json` |
| Servidor HTTP | `C:\NEVEN\startup\neven_http_server.py` |
| TaskPane UI | `C:\NEVEN\TaskPane\` |
| Configuración | `C:\NEVEN\neven-config.json` |

---

## Regla de oro

**Si no estás seguro de cómo hacer algo, lee los documentos en esta carpeta PRIMERO.**

Los errores más comunes ocurren por:
1. No verificar invariantes (ej: BOM en archivos R)
2. No usar el nombre exacto de función (`function_name_xll`)
3. Modificar solo uno de los dos archivos cuando se requieren ambos (aliases)

---

## Contacto

Este proyecto es la tesis de maestría de Minor Bonilla Gómez, Universidad de Costa Rica.
