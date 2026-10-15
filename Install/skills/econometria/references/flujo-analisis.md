# Flujo de Análisis Econométrico en NEVEN

## Flujo Estándar de Regresión

```
1. EXPLORACIÓN
   └── Estadísticas descriptivas (Tab Datos en Studio)
   └── Correlaciones (GR_Correlaciones)
   └── Gráficos exploratorios (GR_Scatter, GR_Histograma)

2. ESTIMACIÓN INICIAL
   └── =NevenX.R("MR_Lineal", Y, X, 1) → Tabla OLS

3. DIAGNÓSTICOS
   └── TipoOutput=5 → VIF (multicolinealidad)
   └── TipoOutput=6 → Breusch-Pagan (heterocedasticidad)
   └── TipoOutput=8 → Observaciones influyentes
   └── RG_RESET → Especificación funcional

4. CORRECCIONES
   └── Si heterocedasticidad → TipoOutput=7 (errores robustos)
   └── Si endogeneidad → MR_2SLS (variables instrumentales)
   └── Si datos panel → MR_PanelData.C

5. REPORTE FINAL
   └── TipoOutput=13 → Métricas estructuradas
   └── Exportar tabla stargazer
```

---

## Flujo de Series de Tiempo

```
1. VISUALIZACIÓN
   └── GR_SeriesTiempo → Gráfico de la serie
   └── Identificar tendencia, estacionalidad

2. TEST DE ESTACIONARIEDAD
   └── Test ADF → ¿Es I(0) o I(1)?
   └── Si I(1) → Diferenciar

3. SELECCIÓN DE MODELO
   └── Si univariada → ARIMA
   └── Si multivariada estacionaria → VAR
   └── Si multivariada cointegrada → ECM

4. ESTIMACIÓN
   └── ST_VAR con criterio AIC/BIC
   └── TipoOutput=1 → Resumen del modelo

5. ANÁLISIS DINÁMICO
   └── TipoOutput=2 → IRF (impulso-respuesta)
   └── TipoOutput=3 → Causalidad de Granger

6. PRONÓSTICO
   └── TipoOutput=4 → Predicción fuera de muestra
```

---

## Comandos Rápidos en Excel

### Regresión básica
```excel
=NevenX.R("MR_Lineal", A2:A100, B2:D100, 1)
```
Rango A2:A100 = Y (con header en A1)
Rango B2:D100 = X1, X2, X3 (con headers en B1:D1)
TipoOutput=1 → Tabla OLS

### Ver ayuda de una función
```excel
=NevenX.R("MR_Lineal",,, 0)
```
TipoOutput=0 siempre retorna la documentación de parámetros.

### Regresión con filtro
```excel
=NevenX.R("MR_Lineal", Y, X,, Escala, Filtro,, TipoOutput)
```
Filtro = columna donde 1=excluir, 0=incluir

### VAR multivariado
```excel
=NevenX.R("ST_VAR", A2:C100,,,,,,,, 2, 1)
```
Rango A2:C100 = 3 series
a9=2 → 2 rezagos
TipoOutput=1 → Resumen

---

## DataLab (NEVEN Studio)

### Ventajas sobre fórmulas Excel
- Interfaz visual para selección de variables
- Resultados interactivos (tablas, gráficos Plotly)
- Historial de ejecuciones
- Exportación directa

### Acceso
1. Click en botón "Studio" en el Ribbon de NEVEN
2. Tab "Data Lab"
3. Seleccionar función del catálogo
4. Asignar columnas a roles (Y, X, etc.)
5. Configurar parámetros
6. Click "Ejecutar"

---

## Interpretación de Resultados

### Tabla OLS (TipoOutput=1)

```
=========================================
                    Dependent variable:   
                    ---------------------
                            Y             
-----------------------------------------
X1                       0.523***        
                         (0.087)         
                                         
X2                       -0.189**        
                         (0.056)         
                                         
Constant                  2.341***       
                         (0.412)         
-----------------------------------------
Observations               100           
R2                        0.672          
Adjusted R2               0.665          
F Statistic        99.4*** (df = 2; 97)  
=========================================
Note:          *p<0.1; **p<0.05; ***p<0.01
```

**Leer**:
- Coeficiente X1 = 0.523: Un aumento de 1 unidad en X1 aumenta Y en 0.523 unidades
- Error estándar en paréntesis
- Asteriscos indican significancia estadística
- R² = 0.672: El modelo explica 67.2% de la variación en Y

### Métricas estructuradas (TipoOutput=13)

Retorna tabla con columnas:
- Seccion: "Coeficientes", "Ajuste", "Diagnosticos"
- Parametro: nombre del parámetro
- Metrica: tipo de métrica (Estimado, SE, p-value, etc.)
- Valor: valor numérico

Útil para post-procesar en Excel (BUSCARV, filtros, etc.)

---

## Errores Comunes y Soluciones

| Error | Causa probable | Solución |
|-------|----------------|----------|
| #VALOR! | Rango sin header | Incluir fila de encabezados |
| R4XCL_Error: singular matrix | Multicolinealidad perfecta | Eliminar variable redundante |
| Coeficientes NA | Columna constante o colineal | Revisar datos, eliminar columna |
| R² muy alto (>0.99) | Posible regresión espuria | Verificar estacionariedad |
| F primera etapa < 10 | Instrumentos débiles | Buscar mejores instrumentos |

---

## Checklist Pre-Análisis

- [ ] Datos en formato columnar (una variable por columna)
- [ ] Primera fila = headers (nombres de variables)
- [ ] Sin celdas vacías en medio del rango
- [ ] Variables numéricas sin texto
- [ ] Suficientes observaciones (regla: n > 10×k)
- [ ] Variables en unidades comparables (considerar logaritmos)
