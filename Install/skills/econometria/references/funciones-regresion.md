# Funciones de Regresión en NEVEN

## Regresión Lineal (MR_Lineal / RG_Lineal)

**Propósito**: Estima la relación lineal Y = Xβ + u usando MCO (Mínimos Cuadrados Ordinarios).

**Uso en Excel**:
```
=NevenX.R("MR_Lineal", SetDatosY, SetDatosX, TipoOutput)
```

**Uso en DataLab**: Seleccionar RG_Lineal en el catálogo de Regresión.

### Parámetros
| Slot | Nombre | Descripción |
|------|--------|-------------|
| a0 | SetDatosY | Variable dependiente (rango con header) |
| a1 | SetDatosX | Variables independientes (rango con header) |
| a3 | Escala | Estandarizar X (0=No, 1=Sí) |
| a4 | Filtro | Excluir observaciones donde Filtro=1 |
| a5 | Constante | Incluir intercepto (0=No, 1=Sí, default=1) |
| a6 | SetDatosPredecir | Rango para predicción fuera de muestra |

### TipoOutputs
| ID | Descripción |
|----|-------------|
| 0 | Ayuda (parámetros y outputs) |
| 1 | Tabla OLS con stargazer (IC 95%) |
| 2 | Predicción dentro de muestra (Ŷ) |
| 3 | Predicción fuera de muestra |
| 4 | Efectos marginales |
| 5 | VIF (Factor de Inflación de Varianza) |
| 6 | Test Breusch-Pagan (heterocedasticidad) |
| 7 | OLS con errores estándar robustos (HC) |
| 8 | Observaciones de influencia (Cook, leverage) |
| 12 | Vector de residuos |
| 13 | Métricas estructuradas |

### Métricas reportadas
- Coeficientes (β) con errores estándar, t-statistics, p-values
- R², R² ajustado
- F-statistic y p-value del modelo
- AIC, BIC

### Supuestos que verifica
- Homocedasticidad (via Breusch-Pagan, TipoOutput=6)
- Multicolinealidad (via VIF, TipoOutput=5)

---

## 2SLS — Variables Instrumentales (MR_2SLS / RG_2SLS)

**Propósito**: Corrige endogeneidad usando variables instrumentales Z. Estima en dos etapas.

**Cuándo usar**: Cuando E(u|X) ≠ 0 (variable omitida correlacionada con X, error de medición, simultaneidad).

**Uso en Excel**:
```
=NevenX.R("MR_2SLS", SetDatosY, SetDatosX,,, Filtro,, SetInstrumentos, SetDatosExo,, TipoOutput)
```

### Parámetros especiales
| Slot | Nombre | Descripción |
|------|--------|-------------|
| a6 | SetInstrumentos | Variables instrumentales Z (REQUERIDO) |
| a7 | SetDatosExo | Variables exógenas de control (opcional) |

### TipoOutputs
| ID | Descripción |
|----|-------------|
| 1 | Tabla 2SLS con stargazer |
| 3 | Test Wu-Hausman (endogeneidad) |
| 4 | Test F primera etapa (instrumentos débiles: F < 10 = problema) |
| 5 | Test Sargan (sobreidentificación) |

### Diagnósticos automáticos
- **F primera etapa < 10**: Instrumentos débiles, sesgo hacia OLS
- **Wu-Hausman significativo**: Confirma endogeneidad, 2SLS justificado
- **Sargan significativo**: Instrumentos correlacionados con error (problema)

Referencia: Wooldridge, Capítulo 15.

---

## Regresión Logística (MR_Binario.C / RG_Logistica)

**Propósito**: Modela P(Y=1|X) cuando Y es binaria (0/1).

**Modelo**: logit(p) = ln(p/(1-p)) = Xβ

### TipoOutputs
| ID | Descripción |
|----|-------------|
| 1 | Tabla logit con stargazer |
| 2 | Probabilidades predichas |
| 4 | Efectos marginales (∂P/∂X) |
| 5 | Matriz de confusión |

### Interpretación
- Los coeficientes son log-odds ratios
- exp(β) = odds ratio
- Efectos marginales dependen del punto de evaluación

---

## Regresión Poisson (MR_Poisson.C / RG_Poisson)

**Propósito**: Modela conteos Y ∈ {0, 1, 2, ...}

**Modelo**: E(Y|X) = exp(Xβ)

### Supuestos
- Equidispersión: Var(Y|X) = E(Y|X)
- Si Var > E: usar binomial negativa

---

## Regresión Tobit (MR_Tobit.C / RG_Tobit)

**Propósito**: Variable dependiente censurada (ej: truncada en 0).

**Modelo**: Y* = Xβ + u; Y = max(0, Y*)

Referencia: Wooldridge, Capítulo 17.

---

## Datos de Panel (MR_PanelData.C / RG_DatosPanel)

**Propósito**: Datos con dimensión i (individuos) y t (tiempo).

**Modelos disponibles**:
- Efectos fijos (within estimator)
- Efectos aleatorios (GLS)
- Pooled OLS

### Parámetros especiales
| Slot | Nombre | Descripción |
|------|--------|-------------|
| a6 | Variable_i | Identificador de individuo |
| a7 | Variable_t | Identificador de tiempo |

### Test Hausman
- H0: Efectos aleatorios consistentes
- H1: Efectos fijos necesarios

Referencia: Wooldridge, Capítulo 13-14.

---

## Errores Robustos

### Newey-West (RG_Newey_West)
Corrige heterocedasticidad Y autocorrelación. Para series de tiempo.

### FGLS (RG_FGLS)
Mínimos Cuadrados Generalizados Factibles. Para estructuras de error conocidas.

---

## Tests de Especificación

### RESET (RG_RESET)
Test de especificación funcional de Ramsey. H0: modelo correctamente especificado.

### Davidson-MacKinnon (RG_Davidson_MacKinnon)
Test J para modelos no anidados.

---

## HECKIT (RG_HECKIT)
Corrección de sesgo de selección (modelo de Heckman en dos etapas).

**Cuándo usar**: Cuando Y solo se observa para una submuestra no aleatoria.

Referencia: Wooldridge, Capítulo 17.
