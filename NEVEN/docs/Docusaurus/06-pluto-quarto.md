---
id: pluto-quarto
title: Capitulo 6 -- Pluto.jl y Quarto
sidebar_label: 6. Pluto y Quarto
sidebar_position: 6
---

# Capitulo 6: Pluto.jl y Quarto

## 6.1 Pluto.jl -- Notebooks reactivos

Pluto.jl permite trabajar con notebooks Julia interactivos directamente desde Excel. Los notebooks son **reactivos**: al cambiar una celda, todas las celdas dependientes se recalculan automaticamente.

### Flujo basico

```
=NEVEN.pluto.start()                           --> Inicia servidor
=NEVEN.notebook.open("linalg_decomposition")   --> Abre notebook
=NEVEN.pluto.stop()                            --> Detiene servidor
```

### Pipeline de datos Excel --> Pluto

$
\text{Excel} \xrightarrow{\texttt{PLUTO.DATA}} \text{Julia (pipe)} \xrightarrow{\text{TSV}} \text{Pluto.jl}
$

```
=NEVEN.pluto.data(A1:D20, "datos")             --> Envia rango a Julia
=NEVEN.notebook.open("excel_data")             --> Abre dashboard
```

El notebook `excel_data` muestra automaticamente:
- Vista previa de datos (primeras 20 filas)
- Estadisticas descriptivas ($N$, $\bar{x}$, $s$, min, max)
- Seccion editable para analisis personalizado

### PCA desde Excel

En una celda del notebook Pluto:

```julia
using MultivariateStats, LinearAlgebra
num_cols = [j for j in 1:length(headers) if raw_data[1,j] isa Number]
X = Float64[raw_data[i,j] for i in 1:size(raw_data,1), j in num_cols]
model = fit(PCA, X'; maxoutdim=2)
println("Varianza explicada: ",
    round.(principalvars(model) ./ tvar(model) * 100, digits=2), "%")
```

### Grafico en Pluto

```julia
using Plots
labels = [string(raw_data[i,1]) for i in 2:size(raw_data,1)]
vals = [Float64(raw_data[i,2]) for i in 2:size(raw_data,1)]
bar(labels, vals, title="Datos desde Excel", ylabel="Valor")
```

### Notebooks disponibles (15)

| # | Notebook | Categoria |
|:---|:---|:---|
| 1-7 | stats_regression, lme4_mixed_models, survival_analysis, forecast_arima, psych_factor_analysis, plm_panel_econometrics, rstanarm_bayes | R via RCall |
| 8-12 | jump_optimization, diffeq_simulation, turing_hierarchical, montecarlo_risk, linalg_decomposition | Julia nativo |
| 13 | multilang_pipeline | Mixto R+Julia |
| 14 | excel_dashboard | Demo ventas |
| 15 | excel_data | **Generico NxP** |

---

## 6.2 Quarto -- Reportes profesionales

Quarto renderiza documentos `.qmd` a HTML y los muestra en WebView2:

$
\texttt{.qmd} \xrightarrow{\text{Quarto CLI}} \texttt{.html} \xrightarrow{\text{WebView2}} \text{Excel}
$

```
=NEVEN.q("C:/NEVEN/quarto/analisis_ventas.qmd")
```

### Documentos de ejemplo

| Documento | Contenido |
|:---|:---|
| `test_report.qmd` | Reporte basico del sistema |
| `data_report.qmd` | Reporte de datos |
| `analisis_ventas.qmd` | Analisis de negocio |
| `julia_stats.qmd` | Capacidades de Julia |

### Crear un documento Quarto propio

Crear archivo `mi_reporte.qmd` en `C:\NEVEN\quarto\`:

```yaml
---
title: "Mi Reporte"
format:
  html:
    self-contained: true
    theme: none
    minimal: true
---

## Resultados

| Metrica | Valor |
|---------|-------|
| Media   | 42    |
| Std     | 7.3   |
```

Renderizar desde Excel:
```
=NEVEN.q("C:/NEVEN/quarto/mi_reporte.qmd")
```
