# Tests Estadísticos Disponibles en NEVEN

## Tests de Comparación de Grupos

### t-test (dos grupos)

```r
# En NEVEN
=NEVEN.r("t.test(grupo1, grupo2)")                    # Independiente, Welch
=NEVEN.r("t.test(grupo1, grupo2, var.equal=TRUE)")   # Independiente, varianzas iguales
=NEVEN.r("t.test(antes, despues, paired=TRUE)")       # Pareado
```

**Interpretación output**:
- `t` = estadístico t
- `df` = grados de libertad
- `p-value` = probabilidad bajo H0
- `95 percent confidence interval` = IC para diferencia de medias

### Wilcoxon / Mann-Whitney (no paramétrico)

```r
=NEVEN.r("wilcox.test(grupo1, grupo2)")            # Mann-Whitney U
=NEVEN.r("wilcox.test(antes, despues, paired=TRUE)")  # Wilcoxon signed-rank
```

### ANOVA (3+ grupos)

```r
=NEVEN.r("modelo <- aov(outcome ~ grupo, data=datos); summary(modelo)")
=NEVEN.r("TukeyHSD(modelo)")  # Comparaciones post-hoc
```

### Kruskal-Wallis (no paramétrico, 3+ grupos)

```r
=NEVEN.r("kruskal.test(outcome ~ grupo, data=datos)")
```

---

## Tests de Asociación

### Chi-cuadrado (categóricas)

```r
=NEVEN.r("tabla <- table(var1, var2); chisq.test(tabla)")
```

### Correlación

```r
=NEVEN.r("cor.test(x, y)")                    # Pearson (default)
=NEVEN.r("cor.test(x, y, method='spearman')")  # Spearman (no paramétrico)
=NEVEN.r("cor.test(x, y, method='kendall')")   # Kendall tau
```

---

## Tests de Normalidad

### Shapiro-Wilk (n < 5000)

```r
=NEVEN.r("shapiro.test(datos$variable)")
```

**Interpretación**: p < 0.05 → Rechazar normalidad

### Kolmogorov-Smirnov

```r
=NEVEN.r("ks.test(datos$variable, 'pnorm', mean=mu, sd=sigma)")
```

---

## Tests de Homocedasticidad

### Levene (para ANOVA)

```r
=NEVEN.r("library(car); leveneTest(outcome ~ grupo, data=datos)")
```

### Bartlett

```r
=NEVEN.r("bartlett.test(outcome ~ grupo, data=datos)")
```

---

## Funciones de Regresión NEVEN

| Función | Descripción | Uso |
|---------|-------------|-----|
| MR_Lineal | MCO básico | `=NevenX.R("MR_Lineal", Y, X, 1)` |
| MR_Binario.C | Logit/Probit | `=NevenX.R("MR_Binario.C", Y, X, 1)` |
| RG_2SLS | Variables instrumentales | `=NevenX.R("MR_2SLS", Y, X,,,, Z, Exo,, 1)` |
| MR_PanelData.C | Datos panel | `=NevenX.R("MR_PanelData.C", Y, X,,,, i, t,, 1)` |

---

## Effect Sizes

### Cohen's d (requiere paquete effsize)

```r
=NEVEN.r("library(effsize); cohen.d(grupo1, grupo2)")
```

### Eta-squared para ANOVA

```r
=NEVEN.r("library(lsr); etaSquared(modelo_aov)")
```

### r de correlación

Ya lo provee `cor.test()`.

---

## Análisis de Poder

### Paquete pwr

```r
# Poder para t-test
=NEVEN.r("library(pwr); pwr.t.test(d=0.5, sig.level=0.05, power=0.8)")

# Poder para correlación
=NEVEN.r("pwr.r.test(r=0.3, sig.level=0.05, power=0.8)")

# Poder para ANOVA
=NEVEN.r("pwr.anova.test(k=3, f=0.25, sig.level=0.05, power=0.8)")
```

**Interpretación output**: `n` = tamaño de muestra necesario por grupo.

---

## Diagnósticos de Regresión

### Via NEVEN TipoOutputs

| TipoOutput | Test |
|------------|------|
| 5 | VIF (multicolinealidad) |
| 6 | Breusch-Pagan (heterocedasticidad) |
| 8 | Cook's distance, leverage |
| 12 | Residuos |

### Via R directo

```r
=NEVEN.r("plot(modelo)")           # 4 gráficos diagnósticos
=NEVEN.r("car::vif(modelo)")       # VIF
=NEVEN.r("lmtest::bptest(modelo)") # Breusch-Pagan
=NEVEN.r("lmtest::dwtest(modelo)") # Durbin-Watson
```

---

## Checklist de Análisis Estadístico

1. **[ ] Hipótesis pre-especificada** antes de ver datos
2. **[ ] Descriptivos reportados** (n, M, SD por grupo)
3. **[ ] Supuestos verificados** (normalidad, homocedasticidad)
4. **[ ] Test apropiado seleccionado** según diseño y supuestos
5. **[ ] Effect size calculado** (no solo p-value)
6. **[ ] IC reportado** junto con estimación puntual
7. **[ ] Corrección múltiple** si aplica
8. **[ ] Reporte en formato APA**
