---
id: bert-vs-neven
title: BERT vs NEVEN
sidebar_label: BERT vs NEVEN
sidebar_position: 21
---

# Análisis Comparativo: BERT Toolkit vs NEVEN v3.2

Este documento compara el BERT Toolkit original (2017) con NEVEN v3.2 (2026), mostrando la evolución de un conector básico a una plataforma analítica completa.

---

## 1. Visión General

| Aspecto | BERT Toolkit | NEVEN v3.2 |
|:---|:---|:---|
| **Concepto** | Conector básico Excel-R-Julia | Plataforma analítica con IA |
| **Lenguajes** | R 3.4.x, Julia 0.6.2 | R 4.4.1, Julia 1.12.6, Python 3.13 |
| **Visualización** | PNG estático | WebView2 (Plotly, D3.js) |
| **Notebooks** | No soportado | Pluto.jl reactivo |
| **SQL** | No soportado | DuckDB integrado |
| **IA** | No soportado | Chat con RAG (300+ entidades) |
| **Tests** | 0 | 342 |
| **Score** | ~4/10 | 9.71/10 |

---

## 2. Arquitectura

### BERT Original

```
Excel ←──→ XLL ←──→ ControlR.exe (R 3.4)
                    ControlJulia.exe (Julia 0.6)
```

- Monolítico: clase principal con 15+ responsabilidades
- Sin servicios modulares
- Configuración hardcoded

### NEVEN v3.2

```
Excel ←──→ XLL ←──→ ControlR.exe (R 4.4.1)
          │         ControlJulia.exe (Julia 1.12.6)
          │         ControlPython.exe (Python 3.13)
          │
          ├───→ WebView2 ───→ Plotly, D3.js, HTML
          ├───→ Pluto.jl ───→ Notebooks reactivos
          ├───→ Quarto ───→ Reportes HTML
          ├───→ NEVENRibbon.dll ───→ Pestaña nativa
          │
          └───→ HTTP Server (5555) ───→ NEVEN Studio
                    │
                    ├───→ DuckDB (SQL)
                    ├───→ RAG Engine
                    └───→ AI Chat (Bedrock)
```

- 4 capas: Interface, Servicios, Subsistemas, Herramientas
- 25+ servicios especializados
- Configuración centralizada con validación

---

## 3. Comparación Funcional

| Funcionalidad | BERT | NEVEN v3.2 |
|:---|:---:|:---:|
| Funciones R | ~20 | **~120** |
| Funciones Julia | ~5 | **~75** |
| Funciones Python | ❌ | **variable** |
| Gráficos interactivos | ❌ | ✅ |
| Notebooks reactivos | ❌ | ✅ |
| SQL sobre Excel | ❌ | ✅ |
| Chat IA con RAG | ❌ | ✅ |
| TaskPane (Studio) | ❌ | ✅ (7 tabs) |
| Sandbox seguridad | ❌ | ✅ |
| Tests automatizados | 0 | **342** |

---

## 4. Innovaciones de NEVEN v3.2

### NEVEN Studio

Panel lateral con 7 tabs:
- SQL (DuckDB)
- Data Studio (gráficos)
- Run Script (REPL)
- Data Lab (notebooks)
- Presentaciones
- IA (Chat + RAG)
- Ayuda (16 capítulos)

### RAG Engine

- 300+ entidades de conocimiento
- Traducción multilingüe (EN/ES/PT/FR)
- 12+ formatos de documentos

### Python Integrado

```excel
=NEVEN.P("sum([10,20,30])")     → 60
=P.MiFuncion(A1, B1)            → Función de usuario
```

---

## 5. Calidad de Código

| Métrica | BERT | NEVEN v3.2 |
|:---|:---|:---|
| TODOs/FIXMEs | 20+ | **0** |
| Memory leaks | Sí | **Corregidos** |
| Race conditions | Sí | **Corregidas** |
| Tests | 0 | **342** |

---

## 6. Rendimiento

| Aspecto | BERT | NEVEN v3.2 |
|:---|:---|:---|
| Arranque Julia | ~5 min | **<5s** (sysimage) |
| Arranque Python | N/A | **<1s** |
| Recálculo paralelo | Unsafe | **Safe** |

---

## 7. Conclusión

| Dimensión | BERT → NEVEN v3.2 |
|:---|:---|
| Funcionalidad | Básica → Completa |
| Lenguajes | 2 obsoletos → 3 actuales |
| IA | Inexistente → Integrada |
| Tests | 0 → 342 |
| Score | ~4/10 → **9.71/10** |

:::tip Mejora total
NEVEN no es un parche de BERT — es una reinvención completa que supera al original en +5.7 puntos.
:::

---

*BukloLAB — Tesis de Maestría, Universidad de Costa Rica*
