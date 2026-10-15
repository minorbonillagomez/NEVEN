# Funciones de NEVEN en Excel

## Funciones Principales

### =NEVEN.r(código)
Ejecuta código R y retorna el resultado.

```excel
=NEVEN.r("1 + 1")                        → 2
=NEVEN.r("mean(c(1,2,3,4,5))")           → 3
=NEVEN.r("summary(datos)")               → Resumen estadístico
```

### =NEVEN.py(código)
Ejecuta código Python.

```excel
=NEVEN.py("1 + 1")
=NEVEN.py("import math; math.sqrt(16)")  → 4
```

### =NEVEN.jl(código)
Ejecuta código Julia.

```excel
=NEVEN.jl("sum(1:100)")                  → 5050
```

---

## Dispatcher NevenX

### =NevenX.R(proceso, Y, X, TipoOutput, ...)

Función universal para análisis econométricos.

```excel
=NevenX.R("MR_Lineal", A2:A100, B2:D100, 1)
```

**Parámetros posicionales**:
| Pos | Slot | Nombre | Descripción |
|-----|------|--------|-------------|
| 1 | - | proceso | Nombre de la función |
| 2 | a0 | SetDatosY | Variable dependiente |
| 3 | a1 | SetDatosX | Variables independientes |
| 4 | a2 | TipoOutput | Tipo de resultado (0=ayuda) |
| 5 | a3 | Escala | Estandarizar (0/1) |
| 6 | a4 | Filtro | Excluir observaciones |
| 7 | a5 | Constante | Incluir intercepto (0/1) |
| 8 | a6 | Libre_1 | Varía según función |
| 9 | a7 | Libre_2 | Varía según función |

### Ver ayuda de una función

```excel
=NevenX.R("MR_Lineal",,, 0)
```
TipoOutput=0 SIEMPRE retorna documentación.

---

## Funciones por Categoría

### Regresión (RG)
| Función | Descripción |
|---------|-------------|
| MR_Lineal | MCO |
| MR_Binario.C | Logit |
| MR_Poisson.C | Conteos |
| MR_Tobit.C | Censurada |
| MR_PanelData.C | Efectos fijos/aleatorios |
| MR_2SLS | Variables instrumentales |

### Series de Tiempo (ST)
| Función | Descripción |
|---------|-------------|
| ST_VAR | Vectores autorregresivos |
| ST_ECM | Corrección de errores |
| ST_ADF | Test raíz unitaria |
| ST_Arima | ARIMA |

### Análisis de Datos (AD)
| Función | Descripción |
|---------|-------------|
| AD_ACP.C | Componentes principales |
| AD_KMedias.C | Clustering K-means |
| AD_Pivot | Tabla dinámica |

### Gráficos (GR)
| Función | Descripción |
|---------|-------------|
| GR_Lineas | Serie temporal |
| GR_Barras | Comparación |
| GR_Scatter | Dispersión |
| GR_BoxPlot | Distribución |
| GR_Histograma | Frecuencias |
| GR_Correlaciones | Matriz de correlación |

---

## Pasar Datos de Excel

### Rango como argumento

```excel
=NEVEN.r("mean(A1:A100)")
```
NEVEN convierte A1:A100 a vector de R.

### Asignar a variable

```excel
=NEVEN.r("datos <- B2:E100; colnames(datos) <- c('x','y','z','w'); summary(datos)")
```

### Múltiples operaciones

```excel
=NEVEN.r("x <- A2:A100; y <- B2:B100; cor(x, y)")
```

---

## Retorno de Resultados

### Escalar → Celda única
```excel
=NEVEN.r("mean(A1:A100)")  → 45.3
```

### Vector → Columna
```excel
=NEVEN.r("1:10")  → Array vertical 1-10
```

### Matriz/DataFrame → Tabla
```excel
=NEVEN.r("cor(A1:D100)")  → Matriz de correlación 4x4
```

### Gráfico → Ventana separada
Los gráficos se abren en una ventana WebView2.

---

## NEVEN Studio (Task Pane)

### Acceso
Click en botón "Studio" del Ribbon NEVEN.

### Tabs disponibles
1. **Data Lab** — Análisis con interfaz gráfica
2. **Run Script** — Ejecutar scripts R/Python/Julia
3. **IA** — Chat con asistente AI
4. **Datos** — Cargar y explorar datasets
5. **Ayuda** — Documentación

### Cargar datos en Data Lab
1. Seleccionar rango en Excel
2. Click "Cargar Selección" en tab Datos
3. Los datos quedan como tabla `dataset` en DuckDB

---

## Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| #VALUE! | Sintaxis incorrecta | Verificar código R |
| #NOMBRE? | Función no cargada | Verificar XLL activo |
| object not found | Variable no existe | Definir en misma celda |
| cannot coerce | Tipo incorrecto | Verificar formato datos |

---

## Atajos de Productividad

### Fórmulas frecuentes

```excel
# Estadísticas descriptivas
=NEVEN.r("summary(A1:D100)")

# Correlación
=NEVEN.r("cor(A1:D100)")

# Regresión rápida
=NevenX.R("MR_Lineal", Y, X, 1)

# Gráfico de dispersión
=NEVEN.r("plot(A1:A100, B1:B100)")
```

### Combinar con funciones Excel

```excel
=SI(NEVEN.r("cor.test(A1:A100, B1:B100)$p.value") < 0.05, "Significativo", "No significativo")
```
