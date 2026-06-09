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

## 1.4 Ecosistema completo

```
+-----------------------------------------------------------+
|                    Microsoft Excel                         |
|                                                           |
|  +----------+  +----------+  +----------+  +--------+    |
|  | R 4.4.1  |  |Julia 1.12|  | Quarto   |  |Pluto.jl|   |
|  |Estadist. |  |Matemat.  |  |Reportes  |  |Notebook|   |
|  +----+-----+  +----+-----+  +----+-----+  +---+----+   |
|       +--------------+-----------+--------------+         |
|                    WebView2 Viewer                         |
|              (Plotly, HTML, Impress.js)                    |
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
| Tests automatizados | 0 | 205 |
| Score | ~4/10 | **9.2/10** |
