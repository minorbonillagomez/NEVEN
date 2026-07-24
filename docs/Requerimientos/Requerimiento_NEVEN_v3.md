# NEVEN v3.0 — Requerimientos Técnicos

**Proyecto:** NEVEN (Next-Generation Econometric & Numerical Engine)
**Módulo:** Interactive Reactive Dashboard + AI Prescriptiva
**Versión:** 3.0.0
**Estado:** Planificado
**Prerequisito:** NEVEN v2.1 estable y distribuida
**Fecha:** Julio 2026

---

## 1. Visión

NEVEN v3.0 transforma el Viewer de un "visor de resultados" en un **panel de control bidireccional reactivo** conectado a Excel, los motores de cómputo (R/Julia/Python) y un LLM local (LM Studio). El usuario interactúa con controles visuales que modifican datos en Excel en tiempo real, disparan recálculos y reciben interpretación automática por IA.

---

## 2. Componentes Principales

### 2.1 Bridge Bidireccional (WebView2 ↔ Excel)
El corazón de v3.0. Permite comunicación en ambas direcciones:
- **Excel → Viewer**: Eventos de selección, cambio de celdas, resultados de UDF
- **Viewer → Excel**: Escritura de valores, disparo de recálculo, inyección de texto

### 2.2 Reactive Dashboard
Panel visual con controles (sliders, inputs, dropdowns) vinculados directamente a celdas de Excel. Cambios en el Viewer = cambios en Excel = recálculo automático.

### 2.3 AI Prescriptiva (LM Studio)
Integración profunda con LM Studio para interpretación automática de modelos econométricos, con payload JSON estandarizado y system prompts especializados.

### 2.4 Dual-Return UDF
Las funciones de NEVEN retornan un ID ligero a la celda + el objeto visual completo al Viewer simultáneamente.

---

## 3. Requerimientos Funcionales

### RF-01: Bridge Bidireccional

| ID | Requerimiento | Prioridad |
|:---|:---|:---:|
| RF-01.1 | Excel→Viewer: captura de selección de rango activo en tiempo real | ALTA |
| RF-01.2 | Viewer→Excel: escribir valores en celdas desde controles JS | ALTA |
| RF-01.3 | Lock Range: fijar rango objetivo para evitar cambios accidentales | MEDIA |
| RF-01.4 | Bulk Write: escritura vectorizada de arrays completos | MEDIA |
| RF-01.5 | Event queue: cola de mensajes thread-safe entre WebView2 STA y Excel main thread | ALTA |

**Implementación técnica:**
- Usar el mecanismo de callbacks existente (mismo que R/Julia) para marshalling entre threads
- Exponer COM object al JS via `ICoreWebView2::AddHostObjectToScript` o usar PostMessage + event queue
- Garantizar que NUNCA se bloquee el hilo principal de Excel

### RF-02: Reactive Dashboard

| ID | Requerimiento | Prioridad |
|:---|:---|:---:|
| RF-02.1 | Sliders vinculados a celdas (cambio slider = cambio celda = recálculo) | ALTA |
| RF-02.2 | Latencia total percibida < 50ms para sliders | ALTA |
| RF-02.3 | Throttle/Debounce durante arrastre (pausar ScreenUpdating de Excel) | MEDIA |
| RF-02.4 | Range Picker visual: seleccionar rango desde el Viewer | MEDIA |
| RF-02.5 | Multi-binding: un viewer con múltiples controles vinculados a diferentes celdas | ALTA |

### RF-03: Motor de Renderizado Avanzado

| ID | Requerimiento | Prioridad |
|:---|:---|:---:|
| RF-03.1 | Soporte Plotly.js (ya existe) | ✅ |
| RF-03.2 | Soporte D3.js para visualizaciones custom | BAJA |
| RF-03.3 | Dual-Return UDF: celda muestra ID, viewer muestra gráfico completo | ALTA |
| RF-03.4 | Recursos JS bundleados localmente (offline, sin CDN) | MEDIA |
| RF-03.5 | Canvas/WebGL para datasets > 100K puntos | BAJA |

### RF-04: AI Prescriptiva (LM Studio)

| ID | Requerimiento | Prioridad |
|:---|:---|:---:|
| RF-04.1 | Payload JSON estandarizado para modelos econométricos | ALTA |
| RF-04.2 | Comunicación async con LM Studio localhost:1234 (ya existe) | ✅ |
| RF-04.3 | Panel dedicado para interpretación con Markdown rendering (ya existe) | ✅ |
| RF-04.4 | Un clic para exportar interpretación a Excel (bloque de texto formateado) | ALTA |
| RF-04.5 | System prompts especializados por tipo de modelo (OLS, ARIMA, VAR, etc.) | MEDIA |
| RF-04.6 | Carga de documentos para resumen/análisis con IA (ya existe) | ✅ |
| RF-04.7 | Historial de conversación con contexto (ya existe) | ✅ |

---

## 4. Requerimientos No Funcionales

| ID | Requerimiento | Target |
|:---|:---|:---|
| RNF-01 | Latencia mensaje JS→Host < 5ms | Crítico |
| RNF-02 | Refresh gráfico 30-60 FPS durante slider | Crítico |
| RNF-03 | No bloquear hilo principal de Excel NUNCA | Crítico |
| RNF-04 | Caída de LM Studio no afecta al Viewer ni Excel | Alto |
| RNF-05 | 100% localhost (sin llamadas externas) | Crítico |
| RNF-06 | Recursos JS locales (funciona sin internet) | Alto |
| RNF-07 | Crash del Viewer no afecta a Excel | Crítico |
| RNF-08 | Compatibilidad con NEVEN v2.1 (backward compatible) | Alto |

---

## 5. Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MICROSOFT EXCEL                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ NEVEN64.xll v3.0                                                ││
│  │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐  ││
│  │  │ RJ2XCL_Engine│  │BridgeService  │  │ LanguageManager     │  ││
│  │  │ (existente)  │  │(NUEVO v3.0)   │  │ (R/Julia/Python)    │  ││
│  │  └──────────────┘  └───────┬───────┘  └─────────────────────┘  ││
│  │                             │ Event Queue (thread-safe)          ││
│  └─────────────────────────────┼───────────────────────────────────┘│
│                                │                                     │
│  ┌─────────────────────────────┼───────────────────────────────────┐│
│  │ ViewerManager + ViewerWindow (WebView2 STA thread)              ││
│  │  ┌─────────────────────────┐│                                   ││
│  │  │ HostObject (COM/IDispatch)│ ← AddHostObjectToScript         ││
│  │  │  .writeCell(sheet,cell,v)│                                   ││
│  │  │  .readRange(range)      ││                                   ││
│  │  │  .getSelection()        ││                                   ││
│  │  │  .callKernel(lang,code) ││                                   ││
│  │  └─────────────────────────┘│                                   ││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│ Viewer HTML/JS  │          │ LM Studio           │
│ (Reactive UI)   │          │ (localhost:1234)     │
│ window.nevenHost│          │ Chat/Completions API │
└─────────────────┘          └─────────────────────┘
```

---

## 6. Plan de Implementación por Fases

### Fase A: Lectura (Excel → Viewer) — Riesgo BAJO
- Capturar evento `SheetSelectionChange` en el XLL
- Enviar rango seleccionado al Viewer via PostMessage
- JS muestra "Active Range: Sheet1!B2:E50"
- **Criterio de éxito:** Seleccionar rango en Excel → label se actualiza en Viewer

### Fase B: Escritura Simple (Viewer → Excel) — Riesgo MEDIO
- Implementar event queue en BridgeService
- JS llama `window.nevenHost.writeCell("Sheet1", "A1", 42)`
- El BridgeService encola la operación
- El hilo principal de Excel la ejecuta en el próximo callback safe-point
- **Criterio de éxito:** Slider en Viewer → celda se actualiza → fórmula se recalcula

### Fase C: Dual-Return UDF — Riesgo MEDIO
- La UDF retorna ID a la celda ("NEVEN.Chart#8492")
- Simultaneamente envía el payload completo al Viewer
- El Viewer renderiza el gráfico/resultado en su panel
- **Criterio de éxito:** `=R.RegresionLineal(...)` muestra resumen en celda + gráfico en Viewer

### Fase D: AI Prescriptiva Integrada — Riesgo BAJO
- Botón "Interpretar" en el Viewer toma los datos del modelo activo
- Construye payload JSON estandarizado
- Envía a LM Studio con system prompt especializado
- Muestra resultado en panel Markdown
- Botón "Exportar a Excel" escribe la interpretación (requiere Fase B)
- **Criterio de éxito:** Output de regresión → un clic → interpretación IA en panel → un clic → en Excel

---

## 7. Dependencias y Prerequisitos

| Prerequisito | Estado |
|:---|:---|
| NEVEN v2.1 estable y distribuida | Pendiente (cerrar hoy) |
| ViewerManager con PostMessage funcional | ✅ (JS→C++ funciona con write-cell a archivo) |
| LM Studio integration | ✅ (AI Assistant funciona) |
| Plotly rendering en WebView2 | ✅ |
| Named Pipes + Protobuf IPC | ✅ |
| Callback mechanism (thread marshalling) | ✅ (usado por R/Julia) |
| Excel COM pointer marshalled | ✅ (stream_pointer_ en RJ2XCL_Engine) |

---

## 8. Riesgos Identificados

| Riesgo | Impacto | Mitigación |
|:---|:---|:---|
| Crash de Excel por escritura desde thread incorrecto | ALTO | Usar event queue + callback mechanism existente |
| COM threading violation (STA) | ALTO | Marshal via IStream (patrón ya usado) |
| Regresión en funcionalidad v2.1 | MEDIO | Feature flag, test suite completa |
| Sandbox security (JS accede a Excel) | MEDIO | Whitelist de operaciones permitidas |
| Rendimiento degradado con muchos bindings | BAJO | Throttle + batch updates |

---

## 9. Métricas de Éxito

| Métrica | Target |
|:---|:---|
| Latencia slider→celda actualizada | < 50ms |
| Crash rate durante uso normal | 0% |
| Tests pasando después de implementación | 100% (228 + 69 existentes) |
| Viewer↔Excel roundtrip | < 10ms |
| LM Studio response renderizada | < 5 segundos |

---

## 10. Cronograma Estimado

| Fase | Duración | Dependencia |
|:---|:---|:---|
| Fase A (Lectura) | 1-2 días | Ninguna |
| Fase B (Escritura) | 2-3 días | Fase A |
| Fase C (Dual-Return) | 2-3 días | Fase B |
| Fase D (AI Prescriptiva) | 1-2 días | Fase B + LM Studio (✅) |
| Testing + Estabilización | 2-3 días | Todas |
| **Total estimado** | **8-13 días** | |

---

*NEVEN v3.0 — Requerimiento Técnico*
*Autor: Minor Bonilla Gómez*
*Fecha: Julio 2026*
