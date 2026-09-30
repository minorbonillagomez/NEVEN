---
id: introduccion
title: Capitulo 1 -- Introduccion
sidebar_label: 1. Introduccion
sidebar_position: 1
---

# Capitulo 1: Introduccion

## 1.1 El problema

Excel es la herramienta de analisis de datos mas utilizada del mundo. Sin embargo, sus capacidades estadisticas nativas son limitadas: no tiene regresion logistica, no tiene analisis de componentes principales, no tiene modelos ARIMA.

Por otro lado, R y Julia son lenguajes potentes para estadistica y matematica, pero requieren programacion -- una barrera para muchos profesionales.

$
\underbrace{\text{Excel}}_{\text{Universal pero limitado}} + \underbrace{\text{R + Julia}}_{\text{Potentes pero tecnicos}} = \underbrace{\text{NEVEN}}_{\text{Lo mejor de ambos mundos}}
$

## 1.2 La solucion

NEVEN expone funciones de R y Julia como formulas nativas de Excel. El usuario escribe:

```
=J.Algebra(A1:B2, 0, 6)
```

Y obtiene el determinante de la matriz en su celda -- sin escribir una linea de codigo Julia.

## 1.3 Evolucion del proyecto

| Version | Ano | Logro |
|:---|:---|:---|
| R4XCL | 2023 | R en Excel via BERT (tesis original) |
| NEVEN v1.0 | Ene 2026 | Fork de BERT, R 4.4.1 + Julia 1.12.6 |
| **NEVEN v2.0** | **Abr 2026** | WebView2, Pluto.jl, Quarto, Ribbon COM |
| **NEVEN v2.1** | **Jul 2026** | Python integrado, NEVEN-SIM (Monte Carlo), NEVEN Studio Standalone, Data Lab V1, AI Integration |

## 1.4 Ecosistema completo

```
+-----------------------------------------------------------+
|              MODO 1: Microsoft Excel (XLL)                 |
|  R 4.4.1 · Julia 1.12 · Quarto · Pluto.jl                 |
|  WebView2 Viewer (Plotly, HTML) · Ribbon COM               |
+-----------------------------------------------------------+

+-----------------------------------------------------------+
|        MODO 2: NEVEN Studio Standalone (sin Excel)         |
|                                                           |
|  Navegador web (http://localhost:5555)                    |
|  +-----------+ +----------+ +-----------+ +-----------+  |
|  | Data Lab  | |Run Script| |Data Studio| |AI / LLM   |  |
|  |punto-click| |R/Julia/Py| |CSV/Parquet| |LMStudio   |  |
|  +-----------+ +----------+ +-----------+ +-----------+  |
|       |               |                                   |
|  ControlR.exe   ControlPython.exe   ControlJulia.exe      |
+-----------------------------------------------------------+
```

## 1.5 Comparacion con BERT (proyecto base)

| Capacidad | BERT | NEVEN v2.0 |
|:---|:---:|:---:|
| Funciones R en Excel | si | si |
| Funciones Julia en Excel | si | si |
| Graficos interactivos | no | si |
| Notebooks reactivos | no | si |
| Reportes Quarto | no | si |
| Ribbon nativo | no | si |
| Sandbox de seguridad | no | si |
| Tests automatizados | 0 | 357 |
| Score | ~4/10 | **9.5/10** |

## 1.6 NEVEN Studio Standalone

A partir de julio 2026, NEVEN puede usarse **sin Microsoft Excel**. NEVEN Studio Standalone es una interfaz web que corre en el navegador del sistema y da acceso a todas las capacidades analíticas de NEVEN.

### Modos de uso

| | NEVEN para Excel | NEVEN Studio |
|:---|:---:|:---:|
| Requiere Excel | ✅ | ❌ |
| Funciones como fórmulas (`=R.func()`) | ✅ | ❌ |
| Data Lab (punto y clic) | ❌ | ✅ |
| Run Script (R/Julia/Python) | ❌ | ✅ |
| Carga de archivos CSV/Parquet | ❌ | ✅ |
| AI / LLM Integration | Parcial | ✅ |
| Mismos motores R/Julia/Python | ✅ | ✅ |

### Cómo abrir NEVEN Studio

```
Doble clic en "NEVEN Studio.vbs"
  → Abre http://localhost:5555 en el navegador
  → Pestañas: Data Lab | Run Script | Data Studio | AI
```
