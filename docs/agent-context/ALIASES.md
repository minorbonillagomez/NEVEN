# Sistema de Aliases — NEVEN

> Los aliases permiten usar nombres cortos para llamar funciones en Excel.
> Ejemplo: `=NEVEN.R("ACP", ...)` en lugar de `=NEVEN.R("AD_ACP.C", ...)`

---

## Aliases disponibles

### Análisis de Datos (AD_)

| Alias | Función Real | Descripción |
|-------|--------------|-------------|
| `ACP`, `PCA` | `AD_ACP.C` | Análisis de Componentes Principales |
| `KMeans`, `KMedias` | `AD_KMedias.C` | Clustering K-Medias |
| `Clustering`, `HClust` | `AD_ClusteringJerarquico.C` | Clustering Jerárquico |
| `Cor`, `Correlacion` | `AD_Correlacion.C` | Matriz de Correlaciones |
| `Arbol`, `DecisionTree`, `CART` | `AD_ArbolDeDecision.C` | Árbol de Decisión |

### Regresión (MR_)

| Alias | Función Real | Descripción |
|-------|--------------|-------------|
| `Lineal`, `LM`, `OLS` | `MR_Lineal` | Regresión Lineal |
| `Logistica`, `Logit`, `Binario` | `MR_Binario.C` | Regresión Logística |
| `Poisson` | `MR_Poisson.C` | Regresión de Poisson |
| `Tobit` | `MR_Tobit.C` | Regresión Tobit |
| `IV`, `2SLS`, `Instrumentales` | `MR_2SLS` | Variables Instrumentales |
| `Panel`, `PanelData` | `MR_PanelData.C` | Datos de Panel |
| `NeweyWest`, `HAC` | `MR_Newey_West` | Errores Robustos Newey-West |
| `FGLS`, `GLS` | `MR_FGLS` | Mínimos Cuadrados Generalizados |
| `Heckit`, `Heckman` | `MR_HECKIT` | Corrección Sesgo de Selección |
| `SVM`, `SupportVector` | `MR_SVM` | Máquinas de Soporte Vectorial |
| `RESET` | `MR_RESET` | Prueba RESET de Ramsey |
| `Davidson`, `MacKinnon` | `MR_Davidson_MacKinnon` | J-Test Davidson-MacKinnon |

### Series de Tiempo (ST_)

| Alias | Función Real | Descripción |
|-------|--------------|-------------|
| `AR`, `AutoRegresivo`, `ARIMA`, `SeriesTiempo` | `ST_AutoRegresivos` | Modelos Autorregresivos |
| `ECM`, `Cointegracion`, `ErrorCorrection` | `ST_ECM` | Modelo de Corrección de Error |
| `VAR`, `VectorAR` | `ST_VAR` | Vector Autorregresivo |

### Text Mining (TM_)

| Alias | Función Real | Descripción |
|-------|--------------|-------------|
| `TextMining`, `NLP`, `Texto` | `TM_TextMining` | Análisis de Texto |

### Gráficos (GR_)

| Alias | Función Real | Descripción |
|-------|--------------|-------------|
| `Histograma`, `Hist` | `GR_Histograma.C` | Histograma |
| `BoxPlot`, `Box` | `GR_BoxPlot.C` | Diagrama de Caja |
| `Scatter`, `Dispersion` | `GR_Scatter.C` | Diagrama de Dispersión |
| `Correlaciones`, `CorrPlot` | `GR_Correlaciones.C` | Gráfico de Correlaciones |

---

## Cómo agregar un nuevo alias

### Paso 1: Modificar el Dispatcher R

**Archivo:** `C:\NEVEN\functions\R4XCL-0-NevenX.R`

Buscar la tabla `.neven_aliases` (aproximadamente línea 205) y agregar:

```r
.neven_aliases <- list(
    # ... aliases existentes ...
    
    "MiNuevoAlias" = "NombreFuncionReal",
    
    # ... más aliases ...
)
```

**Reglas:**
- La **clave** es el alias (nombre corto)
- El **valor** es el nombre EXACTO de la función en R
- Los aliases son **case-insensitive** (`acp`, `ACP`, `Acp` funcionan igual)

### Paso 2: Modificar el Servidor HTTP

**Archivo:** `C:\NEVEN\startup\neven_http_server.py`

Buscar el diccionario `_function_aliases` (aproximadamente línea 1942) y agregar:

```python
_function_aliases = {
    # ... aliases existentes ...
    
    "NombreFuncionReal": ["MiNuevoAlias", "OtroAlias"],
    
    # ... más aliases ...
}
```

**Nota:** Aquí el formato es inverso — la clave es la función, el valor es la lista de aliases.

### Paso 3: Reiniciar servicios

1. **Reiniciar servidor HTTP:**
   ```powershell
   Get-Process python* | Stop-Process -Force
   Start-Process python "C:\NEVEN\TaskPane\start_studio.py" --no-browser
   ```

2. **Reiniciar Excel** para que cargue el dispatcher R actualizado

### Paso 4: Verificar

1. Abrir Tab Ayuda en NEVEN Studio
2. Buscar la función — debe mostrar "→ MiNuevoAlias, OtroAlias"
3. Probar en Excel: `=NEVEN.R("MiNuevoAlias", datos)`

---

## Ejemplo completo

**Agregar alias "Regresion" para MR_Lineal:**

**En R (`R4XCL-0-NevenX.R`):**
```r
.neven_aliases <- list(
    "Lineal"        = "MR_Lineal",
    "LM"            = "MR_Lineal",
    "OLS"           = "MR_Lineal",
    "Regresion"     = "MR_Lineal",   # ← NUEVO
    ...
)
```

**En Python (`neven_http_server.py`):**
```python
_function_aliases = {
    "MR_Lineal": ["Lineal", "LM", "OLS", "Regresion"],  # ← agregar al final
    ...
}
```

---

## Notas importantes

1. **Compatibilidad:** Los nombres completos (`AD_ACP.C`, `MR_Lineal`) siempre funcionan
2. **No hay conflictos:** Si un alias no existe, se usa el nombre tal cual
3. **Un alias = una función:** Cada alias solo puede apuntar a una función
4. **Una función = múltiples aliases:** Una función puede tener varios aliases
