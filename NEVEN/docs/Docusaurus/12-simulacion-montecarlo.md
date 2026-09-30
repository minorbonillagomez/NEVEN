---
id: simulacion-montecarlo
title: Capitulo 12 -- Simulacion Monte Carlo (NEVEN-SIM)
sidebar_label: 12. Simulacion Monte Carlo
sidebar_position: 12
---

# Capitulo 12: Simulacion Monte Carlo (NEVEN-SIM)

## 12.1 Introduccion

NEVEN-SIM es un modulo de simulacion estocastica que extiende NEVEN con capacidades de analisis de riesgo al estilo Crystal Ball / @Risk. Opera como un XLL separado (`NEVEN-SIM.xll`) que se carga junto al add-in base.

**Capacidades:**
- Ajuste automatico de distribuciones a datos historicos (7 distribuciones)
- Simulacion Monte Carlo con hasta 10 millones de iteraciones
- Analisis de sensibilidad (Spearman rank correlation)
- Explorador reactivo de escenarios con sliders interactivos
- Exportacion de resultados a CSV

## 12.2 Instalacion

1. Copiar `NEVEN-SIM.xll` a `C:\NEVEN\`
2. Copiar `workspace\sim-report-template.html` a `C:\NEVEN\workspace\`
3. Copiar `libreria\R\neven_sim_fit.R` a `C:\NEVEN\libreria\R\`
4. Copiar `libreria\JULIA\NEVENSim.jl` a `C:\NEVEN\libreria\JULIA\`
5. En Excel: Archivo → Opciones → Complementos → Examinar → `C:\NEVEN\NEVEN-SIM.xll`
6. Instalar dependencias:
   - `=R.instalar("fitdistrplus jsonlite")`
   - `=J.Instalar("Distributions")`

## 12.3 Uso Rapido

### Verificar estado
```
=SIM.Status()
→ "NEVEN-SIM v1.0 | Base: OK | Estado: Inactivo | Supuestos: 0"
```

### Ajustar distribucion a datos
```
=SIM.Fit(A1:A50)
→ "Mejor: weibull(p1=16.29, p2=8.22) AIC=222 | 2: norm(...) | 3: gamma(...)"
```

### Simulacion completa (sin reporte visual)
```
=SIM.QuickRun(A1:A50, "(x) -> x * 1.1", 100000)
```

### Simulacion con reporte interactivo
```
=SIM.QuickRun(A1:A50, "(x) -> x * 1.1", 100000, 1)
```
Abre un viewer con histograma + sliders reactivos.

### Ver muestras simuladas
```
=SIM.Datos(100)
```
Retorna las primeras 100 muestras como array dinamico.

### Exportar a CSV
```
=SIM.Exportar()
→ "OK: 100000 registros -> C:/NEVEN/data/sim_results_20260716_093012.csv"
```

## 12.4 El Modelo

El parametro `modelo` es una funcion anonima de Julia que se aplica a cada muestra:

| Modelo | Significado |
|:---|:---|
| `(x) -> x` | Sin transformacion (distribucion tal cual) |
| `(x) -> x * 1.1` | Crecimiento del 10% |
| `(x) -> x - 500` | Resta un costo fijo |
| `(x) -> max(x - 100, 0)` | Ganancia si supera umbral (tipo opcion) |
| `(x) -> x * 0.3` | Margen del 30% |

## 12.5 Distribuciones Soportadas

El fitting automatico evalua estas distribuciones por AIC:

| Distribucion | Parametros | Restriccion |
|:---|:---|:---|
| Normal | media, desv.std | Ninguna |
| LogNormal | meanlog, sdlog | Datos > 0 |
| Gamma | shape, rate | Datos > 0 |
| Weibull | shape, scale | Datos > 0 |
| Exponencial | rate | Datos > 0 |
| Uniforme | min, max | Ninguna |
| Beta | alpha, beta | Datos en [0,1] |

## 12.6 Explorador Reactivo

El viewer interactivo permite:
- Cambiar distribucion, parametros, modelo e iteraciones con sliders
- Ver el histograma actualizarse en tiempo real (<100ms)
- Guardar escenarios para comparacion
- Superponer dos escenarios en el mismo grafico
- Copiar parametros de escenarios guardados a Excel

**Nota:** La simulacion reactiva usa JavaScript puro (Box-Muller) para respuesta instantanea. La simulacion "real" via `=SIM.QuickRun` usa R (fitting) + Julia (MC) para resultados de produccion.

## 12.7 Arquitectura Tecnica

```
Excel → SIM.QuickRun → FitService (R/fitdistrplus)
                      → MonteCarloService (Julia/Distributions.jl)
                      → HTML report → NEVEN.v() viewer
```

- **SimBridge**: relay via xlUDF a NEVEN base (lazy detection)
- **FitService**: genera codigo R con `fitdistrplus::fitdist()`
- **MonteCarloService**: genera codigo Julia con `Distributions.jl`
- **SensitivityService**: Spearman rank correlation
- **SimViewerManager**: genera HTML + abre viewer

## 12.8 Limitaciones (Phase 1)

- Una sola variable por simulacion (multi-variable en Phase 2)
- `SIM.Datos(N)` limitado a ~3000 registros por tamano del pipe
- Para datos completos usar `SIM.Exportar()` (CSV a disco)
- Explorador reactivo no conectado bidireccional con Excel
- Copulas y series de tiempo en Phase 2

## 12.9 Troubleshooting

| Problema | Solucion |
|:---|:---|
| `SIM.Status()` dice "Base: NO DISPONIBLE" | Verificar que NEVEN64.xll esta cargado |
| `SIM.Fit()` dice "BLOCKED: library()" | Usar `requireNamespace` (ya corregido en v1.0) |
| `SIM.QuickRun()` dice "Julia call failed" | Verificar `=NEVEN.j("1+1")` retorna 2 |
| Excel se cierra al cargar | Verificar que no hay xlUDF en xlAutoOpen |
| `SIM.Exportar()` dice "BLOCKED: open()" | Crear `C:\NEVEN\data\` manualmente |
