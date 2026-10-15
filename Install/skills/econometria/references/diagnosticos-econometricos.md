# Diagnósticos Econométricos en NEVEN

## Tests de Heterocedasticidad

### Breusch-Pagan (TipoOutput=6 en MR_Lineal)

**Hipótesis**:
- H0: Var(u|X) = σ² (homocedasticidad)
- H1: Var(u|X) = σ²·h(Xγ) (heterocedasticidad)

**Procedimiento**:
1. Estimar MCO, obtener residuos û
2. Regresar û² sobre X
3. LM = n·R² de la regresión auxiliar
4. LM ~ χ²(k) bajo H0

**Interpretación**:
- p-value < 0.05 → Rechazar H0 → Hay heterocedasticidad
- Solución: Usar errores estándar robustos (HC)

---

## Errores Estándar Robustos

### HC (Heteroskedasticity-Consistent)

NEVEN implementa HC via TipoOutput=7 en MR_Lineal.

**Variantes**:
| Tipo | Descripción | Cuándo usar |
|------|-------------|-------------|
| HC0 | White (1980) | Muestras grandes |
| HC1 | HC0 × n/(n-k) | Corrección grados de libertad |
| HC2 | HC0 con leverage | Muestras pequeñas |
| HC3 | Jackknife | Más conservador, muestras pequeñas |

**En NEVEN**: Por defecto usa HC1.

### Newey-West (HAC)

Corrige heterocedasticidad Y autocorrelación. Para series de tiempo.

**Uso**: RG_Newey_West

**Bandwidth**: Automático vía regla de Newey-West (basado en n).

---

## Multicolinealidad

### VIF — Factor de Inflación de Varianza (TipoOutput=5)

$$VIF_j = \frac{1}{1 - R^2_j}$$

Donde R²ⱼ es el R² de regresar Xⱼ sobre las demás X.

**Interpretación**:
| VIF | Diagnóstico |
|-----|-------------|
| < 5 | Aceptable |
| 5-10 | Moderada (revisar) |
| > 10 | Alta (problema) |

**Soluciones**:
- Eliminar variable redundante
- Combinar variables (índice, PCA)
- Obtener más datos

---

## Tests de Especificación

### RESET de Ramsey (RG_RESET)

**Propósito**: Detecta especificación funcional incorrecta (omisión de no linealidades).

**Procedimiento**:
1. Estimar modelo original, obtener Ŷ
2. Agregar Ŷ², Ŷ³ como regresores
3. Test F de significancia conjunta

**Hipótesis**:
- H0: Modelo correctamente especificado
- H1: Faltan términos no lineales

**Interpretación**:
- p-value < 0.05 → Modelo mal especificado → Considerar transformaciones, interacciones

---

## Diagnósticos de Variables Instrumentales

### F de Primera Etapa (TipoOutput=4 en MR_2SLS)

**Propósito**: Evaluar fortaleza de los instrumentos.

**Regla de oro**: F > 10 para instrumentos fuertes.

| F | Diagnóstico |
|---|-------------|
| < 10 | Instrumentos débiles → sesgo hacia OLS |
| 10-20 | Aceptable |
| > 20 | Instrumentos fuertes |

### Test Wu-Hausman (TipoOutput=3)

**Propósito**: Confirmar que 2SLS es necesario.

**Hipótesis**:
- H0: Variable X es exógena (OLS consistente)
- H1: Variable X es endógena (necesita IV)

**Interpretación**:
- p-value < 0.05 → Rechazar H0 → Usar 2SLS
- p-value ≥ 0.05 → No hay evidencia de endogeneidad → OLS suficiente

### Test Sargan/Hansen (TipoOutput=5)

**Propósito**: Validar restricciones de sobreidentificación (cuando hay más instrumentos que endógenas).

**Hipótesis**:
- H0: Instrumentos válidos (no correlacionados con u)
- H1: Al menos un instrumento inválido

**Interpretación**:
- p-value < 0.05 → Rechazar H0 → Algún instrumento correlacionado con error
- Solo funciona si modelo está sobreidentificado

---

## Observaciones Influyentes (TipoOutput=8)

### Distancia de Cook

$$D_i = \frac{e_i^2}{k \cdot MSE} \cdot \frac{h_i}{(1-h_i)^2}$$

**Regla**: Dᵢ > 4/n indica observación influyente.

### Leverage (hᵢᵢ)

Mide qué tan lejos está la observación i del centro de X.

**Regla**: hᵢᵢ > 2(k+1)/n indica alto leverage.

### DFBETAS

Cambio en cada βⱼ al omitir observación i.

**Regla**: |DFBETAS| > 2/√n indica influencia en ese coeficiente.

---

## Autocorrelación

### Durbin-Watson

$$DW = \frac{\sum_{t=2}^{n}(e_t - e_{t-1})^2}{\sum_{t=1}^{n}e_t^2}$$

**Interpretación**:
| DW | Diagnóstico |
|----|-------------|
| ≈ 2 | No autocorrelación |
| < 2 | Autocorrelación positiva |
| > 2 | Autocorrelación negativa |

**Valores críticos**: Dependen de n y k. Ver tablas de Savin-White.

### Breusch-Godfrey (LM)

Más general que DW. Permite testear autocorrelación de orden superior.

---

## Normalidad de Residuos

### Jarque-Bera

$$JB = \frac{n}{6}\left(S^2 + \frac{(K-3)^2}{4}\right)$$

Donde S = skewness, K = kurtosis.

**Hipótesis**:
- H0: Residuos normales
- H1: No normalidad

**Nota**: Con muestras grandes, inferencia es válida aún sin normalidad (Teorema Central del Límite). El test es más relevante para muestras pequeñas.

---

## Resumen: Cuándo Aplicar Cada Test

| Sospecha | Test | Output NEVEN |
|----------|------|--------------|
| Heterocedasticidad | Breusch-Pagan | MR_Lineal, TipoOutput=6 |
| Multicolinealidad | VIF | MR_Lineal, TipoOutput=5 |
| Forma funcional | RESET | RG_RESET |
| Endogeneidad | Wu-Hausman | MR_2SLS, TipoOutput=3 |
| Instrumentos débiles | F primera etapa | MR_2SLS, TipoOutput=4 |
| Instrumentos inválidos | Sargan | MR_2SLS, TipoOutput=5 |
| Outliers | Cook, leverage | MR_Lineal, TipoOutput=8 |
