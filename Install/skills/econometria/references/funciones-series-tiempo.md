# Funciones de Series de Tiempo en NEVEN

## VAR — Vectores Autorregresivos (ST_VAR)

**Propósito**: Modela la dinámica conjunta de 2+ series de tiempo estacionarias.

**Uso en Excel**:
```
=NevenX.R("ST_VAR", data_Series,,,,,,,, Rezagos, TipoOutput)
```

**Uso en DataLab**: Seleccionar ST_VAR en el catálogo de Series de Tiempo.

### Parámetros
| Slot | Nombre | Descripción |
|------|--------|-------------|
| a0 | data_Series | Mínimo 2 columnas numéricas (rango con header) |
| a9 | Rezagos | Número de rezagos del modelo (default=2) |

### Parámetros en DataLab
| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| MaxRezagos | Máximo de rezagos a evaluar | 8 |
| CriterioSel | Criterio de selección: AIC, BIC, HQ, FPE | AIC |
| TipoConst | Constante, Tendencia, o ambas | Constante |
| HorizontePron | Períodos a pronosticar | 4 |

### TipoOutputs
| ID | Descripción |
|----|-------------|
| 0 | Ayuda |
| 1 | Resumen del modelo VAR estimado |
| 2 | Función de Impulso-Respuesta (IRF) |
| 3 | Test de Causalidad de Granger |
| 4 | Predicción fuera de muestra |
| 5 | Métricas estructuradas |

### Interpretación

**Función de Impulso-Respuesta (IRF)**:
- Muestra cómo un shock en una variable afecta a otra a lo largo del tiempo
- Útil para entender transmisión de shocks

**Causalidad de Granger**:
- H0: X no causa-Granger a Y (rezagos de X no predicen Y)
- Rechazo → X tiene poder predictivo sobre Y
- NO implica causalidad verdadera, solo precedencia temporal

Referencia: Hamilton, Capítulo 11; Wooldridge, Capítulo 18.

---

## ECM — Modelo de Corrección de Errores (ST_ECM)

**Propósito**: Modela series cointegradas — con equilibrio de largo plazo y ajuste de corto plazo.

**Uso en Excel**:
```
=NevenX.R("ST_ECM", data_Series,,,,,,,, Rezagos, TipoOutput)
```

### Cuándo usar
- Series I(1) que comparten una tendencia estocástica común
- Relación de largo plazo estable entre las variables

### Estructura del modelo

$$\Delta Y_t = \alpha (Y_{t-1} - \beta X_{t-1}) + \text{rezagos de } \Delta Y, \Delta X + u_t$$

Donde:
- $(Y_{t-1} - \beta X_{t-1})$ = término de corrección de error
- $\alpha$ = velocidad de ajuste (debe ser negativo para estabilidad)
- $\beta$ = relación de largo plazo

### Interpretación
- **α negativo y significativo**: Sistema corrige hacia el equilibrio
- **|α| grande**: Ajuste rápido
- **β**: Elasticidad de largo plazo

Referencia: Hamilton, Capítulos 19-20.

---

## Tests de Raíz Unitaria

### ADF — Dickey-Fuller Aumentado

**Propósito**: Determina si una serie es estacionaria.

- H0: Serie tiene raíz unitaria (no estacionaria, I(1))
- H1: Serie es estacionaria (I(0))

**Valores críticos** (MacKinnon):
| Significancia | Sin tendencia | Con tendencia |
|--------------|---------------|---------------|
| 1% | -3.43 | -3.96 |
| 5% | -2.86 | -3.41 |
| 10% | -2.57 | -3.13 |

**Interpretación**:
- t-stat < valor crítico → Rechazar H0 → Serie estacionaria
- Si no se rechaza → Diferenciar y volver a testear

---

## ARIMA (ST_Arima)

**Propósito**: Modela una serie univariada como función de sus propios rezagos y errores pasados.

**Modelo**: ARIMA(p, d, q)
- p = orden autorregresivo (AR)
- d = orden de diferenciación
- q = orden de media móvil (MA)

### Selección de orden
1. Determinar d con test ADF (diferenciar hasta estacionariedad)
2. Examinar ACF y PACF de la serie diferenciada
3. Seleccionar p, q con AIC/BIC

### Reglas ACF/PACF
| Patrón | ACF | PACF | Modelo sugerido |
|--------|-----|------|-----------------|
| Decae exponencialmente | Corta en p | - | AR(p) |
| Corta en q | Decae exponencialmente | - | MA(q) |
| Decae | Decae | - | ARMA(p,q) |

Referencia: Hamilton, Capítulos 3-4.

---

## Estacionariedad

### Definición (débil/covarianza)
Una serie {Yₜ} es estacionaria si:
1. E(Yₜ) = μ (constante en t)
2. Var(Yₜ) = σ² (constante en t)
3. Cov(Yₜ, Yₜ₋ₖ) = γₖ (solo depende del rezago k)

### Por qué importa
- Series no estacionarias → regresiones espurias
- R² alto pero relación falsa
- t-statistics no válidos

### Soluciones
- **Tendencia determinista**: Incluir t en la regresión
- **Raíz unitaria**: Diferenciar la serie
- **Cointegración**: Usar ECM si existe relación de largo plazo

---

## Criterios de Selección de Modelos

| Criterio | Fórmula | Uso |
|----------|---------|-----|
| AIC | ln(SSR/n) + 2k/n | Balance fit vs. parsimonia |
| BIC/SC | ln(SSR/n) + k·ln(n)/n | Penaliza más parámetros (más conservador) |
| HQ | ln(SSR/n) + 2k·ln(ln(n))/n | Intermedio |
| FPE | SSR/n · (n+k)/(n-k) | Error de predicción final |

Donde: n = observaciones, k = parámetros, SSR = suma de residuos al cuadrado.

**Regla**: Elegir el modelo que MINIMIZA el criterio.
