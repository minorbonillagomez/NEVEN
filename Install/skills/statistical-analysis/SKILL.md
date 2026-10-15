---
name: statistical-analysis
description: Metodología estadística para análisis en NEVEN. Guía la selección de tests, verificación de supuestos, cálculo de effect sizes y reporte en formato APA. Usa las funciones de R disponibles en NEVEN. Activa cuando el usuario pida análisis estadístico, comparar grupos, o reportar resultados.
version: "1.0"
author: NEVEN Team (adaptado de Research Agent Skills)
restricted_to_rag: false
---

# Statistical Analysis — Skill para NEVEN

## Propósito

Guiar análisis estadísticos rigurosos usando las funciones de R disponibles en NEVEN. El objetivo es producir análisis que un revisor no pueda criticar: test correcto, supuestos verificados, effect sizes honestos, reporte completo.

## Cuándo se activa

- "Hazme un t-test"
- "¿Qué test debo usar?"
- "Compara estos grupos"
- "¿Es significativo?"
- "Calcula el poder estadístico"

## Workflow de análisis

### 1. Enmarcar la pregunta ANTES de tocar datos
- ¿Cuál es la hipótesis?
- ¿Cuáles son las variables (outcome, predictores)?
- ¿Diseño independiente o pareado?
- Comprometerse con un test ANTES de ver resultados

### 2. Inspeccionar los datos
Para cada grupo reportar: n, media, SD, mediana, valores faltantes.
Graficar histogramas o boxplots ANTES de cualquier test.

```r
# En NEVEN
=NEVEN.r("summary(datos)")
=NEVEN.r("hist(datos$variable)")
```

### 3. Seleccionar el test

**Comparar 2 grupos:**
| Condición | Test |
|-----------|------|
| Independiente, normal | t-test independiente |
| Independiente, no normal | Mann-Whitney U |
| Pareado, normal | t-test pareado |
| Pareado, no normal | Wilcoxon signed-rank |

**Comparar 3+ grupos:**
| Condición | Test |
|-----------|------|
| Independiente, normal | ANOVA |
| Independiente, no normal | Kruskal-Wallis |
| Pareado, normal | ANOVA de medidas repetidas |

**Relaciones:**
| Tipo | Test |
|------|------|
| Dos continuas, normal | Pearson |
| Dos continuas, no normal | Spearman |
| Outcome continuo | Regresión lineal |
| Outcome binario | Regresión logística |

### 4. Verificar supuestos

```r
# Normalidad
=NEVEN.r("shapiro.test(datos$variable)")

# Homocedasticidad
=NEVEN.r("leveneTest(variable ~ grupo, data=datos)")

# Para regresión
=NEVEN.r("plot(modelo)")  # 4 gráficos diagnósticos
```

**Si fallan los supuestos:**
- Normalidad leve + n>30 → proceder (robusto)
- Normalidad severa → test no paramétrico
- Varianzas desiguales → Welch's t-test o ANOVA

### 5. Ejecutar el test con effect size

```r
# t-test con effect size
=NEVEN.r("t.test(grupo1, grupo2)")
=NEVEN.r("cohen.d(grupo1, grupo2)")  # requiere effsize

# ANOVA
=NEVEN.r("aov(variable ~ grupo, data=datos)")
=NEVEN.r("etaSquared(modelo)")  # requiere lsr
```

### 6. Reportar en formato APA

**t-test:**
```
El Grupo A (n = 48, M = 75.2, SD = 8.5) puntuó significativamente 
más alto que el Grupo B (n = 52, M = 68.3, SD = 9.2), 
t(98) = 3.82, p < .001, d = 0.77, 95% CI [0.36, 1.18].
```

**ANOVA:**
```
Se encontró un efecto principal significativo del tratamiento,
F(2, 147) = 8.45, p < .001, η²p = .10.
```

## Effect sizes de referencia

| Test | Pequeño | Mediano | Grande |
|------|---------|---------|--------|
| d (t-test) | 0.20 | 0.50 | 0.80 |
| η²p (ANOVA) | 0.01 | 0.06 | 0.14 |
| r (correlación) | 0.10 | 0.30 | 0.50 |
| R² (regresión) | 0.02 | 0.13 | 0.26 |

## Reglas de integridad

1. **Distinguir confirmatorio de exploratorio** — si descubriste algo post-hoc, etiquétalo así
2. **No buscar significancia** — si el test planeado no es significativo, ese es el resultado
3. **Corregir comparaciones múltiples** — Tukey para ANOVA, Holm/Bonferroni para otros
4. **No significativo ≠ sin efecto** — puede ser falta de poder
5. **Significativo ≠ importante** — con n grande, efectos triviales dan p < .001

## Funciones R disponibles en NEVEN

La librería R4XCL incluye:
- `t.test()`, `wilcox.test()`, `chisq.test()`
- `aov()`, `TukeyHSD()`, `kruskal.test()`
- `cor.test()`, `lm()`, `glm()`
- `shapiro.test()`, `ks.test()`

Para effect sizes, instalar: `effsize`, `lsr`, `pwr`
