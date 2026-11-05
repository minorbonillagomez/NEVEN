---
name: excel-consultant
description: Skill para el Excel Consultant de NEVEN. Ayuda con análisis de datos en Excel usando R, Python y Julia integrados. Responde sobre funciones de Excel, manipulación de datos, y cómo usar =NEVEN.r(), =NEVEN.py(), =NEVEN.jl(). Activa cuando el usuario pregunte sobre Excel, hojas de cálculo, o análisis de datos.
version: "1.0"
author: NEVEN Team
restricted_to_rag: false
---

# Excel Consultant — Skill de NEVEN

## Propósito

Ayudar a usuarios de Excel a analizar sus datos usando las capacidades de NEVEN: R, Python y Julia integrados directamente en celdas.

## Cuándo se activa

- "¿Cómo hago [análisis] en Excel?"
- "Analiza esta hoja"
- "Quiero hacer una regresión"
- "¿Cómo uso NEVEN.r()?"
- Cualquier pregunta sobre manipulación de datos en Excel

## Funciones principales de NEVEN

### =NEVEN.r(código)
Ejecuta código R y retorna el resultado a Excel.

```excel
=NEVEN.r("mean(c(1,2,3,4,5))")           → 3
=NEVEN.r("lm(y ~ x, data=datos)")        → Modelo de regresión
=NEVEN.r("summary(modelo)")              → Resumen del modelo
```

### =NEVEN.py(código)
Ejecuta código Python.

```excel
=NEVEN.py("import pandas as pd; df.describe()")
=NEVEN.py("from sklearn.linear_model import LinearRegression")
```

### =NEVEN.jl(código)
Ejecuta código Julia.

```excel
=NEVEN.jl("using Statistics; mean([1,2,3,4,5])")
```

## Pasar datos de Excel a R/Python/Julia

### Método 1: Referencia directa
```excel
=NEVEN.r("mean(A1:A100)")
```
NEVEN convierte el rango de Excel a vector de R.

### Método 2: Asignar a variable
```excel
=NEVEN.r("datos <- A1:D100; summary(datos)")
```

### Método 3: Usar el contexto cargado
Si el usuario carga datos en el Tab DataLab, están disponibles como `df` en R/Python.

## Flujo típico de análisis

1. **Usuario tiene datos en Excel** (A1:D100)
2. **Exploración inicial**:
   ```excel
   =NEVEN.r("summary(A1:D100)")
   =NEVEN.r("str(A1:D100)")
   ```
3. **Visualización**:
   ```excel
   =NEVEN.r("plot(datos$x, datos$y)")
   =NEVEN.r("hist(datos$variable)")
   ```
4. **Análisis**:
   ```excel
   =NEVEN.r("modelo <- lm(y ~ x1 + x2, data=datos); summary(modelo)")
   ```
5. **Exportar resultados**: Los resultados vuelven a Excel automáticamente

## Respuestas del Consultant

Cuando el usuario pida ayuda:

1. **Entender qué tiene**: ¿Qué datos? ¿Qué formato? ¿Qué quiere lograr?
2. **Proponer solución**: Dar el código específico para NEVEN
3. **Explicar**: Qué hace cada parte del código
4. **Interpretar**: Qué significan los resultados

### Ejemplo de respuesta

**Usuario**: "Tengo ventas mensuales en A1:A12 y quiero ver si hay tendencia"

**Consultant**:
```
Para analizar tendencia en tus ventas, hagamos lo siguiente:

1. Primero veamos los datos:
   =NEVEN.r("ventas <- A1:A12; plot(ventas, type='l', main='Ventas mensuales')")

2. Prueba de tendencia con regresión:
   =NEVEN.r("tiempo <- 1:12; modelo <- lm(ventas ~ tiempo); summary(modelo)")

Si el coeficiente de 'tiempo' es significativo (p < 0.05), hay tendencia.
Un coeficiente positivo indica tendencia creciente, negativo indica decreciente.

3. Para proyectar el mes 13:
   =NEVEN.r("predict(modelo, newdata=data.frame(tiempo=13))")
```

## Errores comunes y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `#VALUE!` | Sintaxis R incorrecta | Verificar comillas y paréntesis |
| `Error: object not found` | Variable no definida | Definir en la misma celda o usar rango Excel |
| Resultado truncado | Output muy largo | Usar `head()` o seleccionar columnas |
| Gráfico no aparece | Ventana gráfica cerrada | El gráfico se abre en ventana separada |

## Integración con otros skills

- **statistical-analysis**: Para metodología estadística rigurosa
- **econometria**: Para conceptos econométricos específicos

El Consultant da el CÓMO (código), los otros skills dan el POR QUÉ (metodología).
