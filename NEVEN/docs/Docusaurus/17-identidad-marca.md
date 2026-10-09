---
id: identidad-marca
title: Capítulo 17 — Identidad y Marca NEVEN
sidebar_label: 17. Identidad
sidebar_position: 17
---

# NEVEN: Evolución e Identidad de Marca

**Versión:** NEVEN v3.2  
**Última actualización:** 2026-08-19

## De R4XCL/RJ2XCL a NEVEN

La transición del nombre del proyecto representa una evolución hacia una identidad de software profesional:

| Versión | Nombre | Significado |
|---------|--------|-------------|
| v1.x | R4XCL | R for Excel |
| v2.x | RJ2XCL | R+Julia to Excel |
| v3.x | **NEVEN** | Nombre de marca |

---

## El Concepto del Autor: La Firma Oculta ⟨v⟩

Un elemento fundamental en la arquitectura visual de **NEVEN** es la inclusión de la firma del autor, **Minor Bonilla Gómez**.

- **La Firma ⟨v⟩:** La letra "v" minúscula encerrada entre paréntesis angulares `⟨v⟩` como marca personal.
- **De Minor a Major:** Dentro del juego de simetría del logo, la marca del autor cobra una nueva dimensión. Es el punto donde el esfuerzo individual de **Minor** se proyecta hacia una solución de impacto **Major** (mayor).

---

## Razones Artísticas y Filosóficas

### Resiliencia e Inmortalidad

- **Esperanto:** *Neven* se construye de *ne* (no) y la raíz de *venki* (vencer). Evoca lo **invicto**, una infraestructura que no se rinde ante la complejidad de los datos.
- **Simbolismo Botánico:** En idiomas eslavos, *Neven* es la caléndula, "la flor que no se marchita", simbolizando reportes y análisis que permanecen vigentes.

### Acrónimo Técnico Oculto

**NEVEN** también puede interpretarse como:
- **N**umerical
- **E**xcel
- **V**isualization
- **E**ngine for
- **N**etworks

Este acrónimo refleja la esencia: un motor de visualización numérica para Excel que conecta múltiples lenguajes en una red integrada.

---

## Arte del Logo y Simetría Absoluta

### El Ambigrama Especular

La característica más distintiva de **NEVEN** es su **simetría total**:

- **N-E-V-Ǝ-И:** Al invertir horizontalmente las letras finales (E→Ǝ y N→И), el logo se lee igual en ambas direcciones.
- **La V como Vértice:** La **V** central actúa como el eje de simetría y el vértice de convergencia para los tres motores.

```
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║      N   E   V   Ǝ   И                ║
    ║              ▲                        ║
    ║              │                        ║
    ║         Eje de simetría               ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
```

:::tip Significado visual
La simetría comunica que el software es equilibrado, lógico y confiable — cualidades esenciales para herramientas de análisis de datos.
:::

---

## NEVEN v3.2: El Estado Actual

### Arquitectura de 4 Capas

```
┌─────────────────────────────────────────────────────────────┐
│                 Microsoft Excel (Host)                       │
├─────────────────────────────────────────────────────────────┤
│  NEVEN64.xll        │  NEVENRibbon.dll  │  NEVEN Studio     │
│  (C++17, MSVC)      │  (COM Add-in)     │  (Office Add-in)  │
├─────────────────────┴───────────────────┴───────────────────┤
│                  RJ2XCL_Engine (Singleton)                  │
├─────────────────────────────────────────────────────────────┤
│   ┌─────────┐   ┌────────────┐   ┌─────────────┐            │
│   │ControlR │   │ControlJulia│   │ControlPython│            │
│   │ (R 4.4) │   │ (Jl 1.12.6)│   │ (Py 3.12)   │            │
│   └─────────┘   └────────────┘   └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Principales

| Motor | Versión | Especialidad |
|-------|---------|--------------|
| **R** | 4.4.1 | Estadística, econometría, visualización |
| **Julia** | 1.12.6 | Cálculo numérico, optimización, ML |
| **Python** | 3.12 | AI/LLM, automatización, conectividad |

### NEVEN Studio

Modo standalone con 7 tabs especializados:

| Tab | Función |
|-----|---------|
| **SQL** | Consultas SQL sobre datos de Excel (DuckDB) |
| **Data Studio** | Transformación visual de datos |
| **Run Script** | Editor de código R/Julia/Python |
| **Data Lab** | Descubrimiento de datos + lenguaje natural |
| **Presentaciones** | Generador reveal.js |
| **IA** | Asistente AI contextual |
| **Ayuda** | Búsqueda semántica + RAG |

### Métricas de Calidad

| Métrica | Valor |
|---------|-------|
| Tests automatizados | 342 (100% passing) |
| Funciones UDF | 200+ |
| Latencia IPC | <1ms |
| Calificación doctoral | **9.71/10** |

---

## Estrategia de Mercadeo

- **Simplicidad:** Nombre bisílabo fácil de recordar (vs. acrónimos técnicos).
- **Diferenciación:** Marca de software de alta gama con identidad corporativa.
- **Equilibrio:** Simetría visual = software equilibrado y confiable.
- **Universalidad:** Funciona en múltiples idiomas sin traducción.

---

## El Legado del Código

Aunque la marca externa es **NEVEN**, el código interno mantiene los prefijos históricos por compatibilidad ABI:

| Contexto | Prefijo | Ejemplo |
|----------|---------|---------|
| Interno C++ | `RJ_`, `RJ2XCL_` | `RJ2XCL_Engine` |
| Usuario Excel | `NEVEN.` | `=NEVEN.r("...")` |
| Config | `neven-` | `neven-config.json` |
| Funciones | `R.`, `J.`, `P.` | `=R.MR_Lineal(...)` |

---

## Conclusión

**NEVEN** es el punto de encuentro donde la ciencia de datos y la agilidad de los negocios convergen. Con v3.2, ha evolucionado de un simple add-in de Excel a una plataforma completa de análisis que integra:

- Tres motores de scripting (R, Julia, Python)
- Interfaz standalone (NEVEN Studio)
- Inteligencia artificial (RAG + asistente contextual)
- Visualizaciones interactivas (WebView2, Plotly, reveal.js)

El nombre **NEVEN** —invicto, inmarchitable— refleja la resiliencia del proyecto y su capacidad de adaptarse sin perder su esencia: democratizar el análisis estadístico avanzado para usuarios de Excel.

---

*NEVEN v3.2 — Add-in XLL políglota para Microsoft Excel*  
*BukloLAB — Tesis de Maestría, Universidad de Costa Rica*  
*Autor: Minor Bonilla Gómez ⟨v⟩*
