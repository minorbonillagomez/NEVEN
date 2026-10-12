# NEVEN v3.2: Manual de Primeros Pasos

**BukloLAB — Tesis de Maestría, Universidad de Costa Rica**

---

## 1. Requisitos

| Componente | Versión | Descarga |
|:---|:---|:---|
| Windows | 10/11 (64 bits) | — |
| Microsoft Excel | 2016+ o Microsoft 365 (64-bit) | — |
| R | 4.4.1+ | https://cran.r-project.org |
| Python | 3.10+ | https://python.org |
| Julia | 1.12.6+ (opcional) | https://julialang.org |
| Quarto | 1.9.18+ (opcional) | https://quarto.org |

> **Nota:** Python es requerido para NEVEN Studio. Julia y Quarto son opcionales.

---

## 2. Instalación

### Opción A: Instalador automatizado (recomendado)

1. Descarga y extrae `NEVEN-v3.2-Setup.zip`
2. Abre PowerShell como Administrador
3. Ejecuta:

```powershell
cd C:\ruta\donde\extrajiste
.\Install-NEVEN.ps1
```

El instalador:
- Copia archivos a `C:\NEVEN\`
- Instala dependencias Python (DuckDB, FastEmbed, MarkItDown, etc.)
- Registra el Ribbon COM (`NEVENRibbon.dll`)
- Configura el XLL en Excel

### Opción B: Instalación manual

1. Copiar los archivos de NEVEN a `C:\NEVEN\`
2. Crear junction para Quarto: `mklink /J C:\Quarto "C:\Program Files\Quarto"`
3. Registrar el Ribbon: `regsvr32 C:\NEVEN\NEVENRibbon.dll`
4. Abrir Excel → Archivo → Opciones → Complementos → Examinar → `C:\NEVEN\NEVEN64.xll`

---

## 3. Verificación Rápida

Al abrir Excel debería aparecer la pestaña **NEVEN** en la cinta de opciones.

### Prueba en celdas

```
=NEVEN.R("1+1")        → 2
=NEVEN.J("sqrt(144)")  → 12 (si Julia está instalada)
=NEVEN.P("1+1")        → 2
=NEVEN.about()         → Información del proyecto
```

Si retorna `#NOMBRE?`, el XLL no se cargó. Ver sección 10 (Solución de Problemas).

### Abre NEVEN Studio

Haz clic en **NEVEN Studio** en el Ribbon (o `Ctrl+Shift+N`). Se abre un panel con 7 tabs:

| Tab | Función |
|-----|---------|
| **SQL** | Consultas DuckDB sobre datos de Excel |
| **Data Studio** | Análisis exploratorio con gráficos |
| **Run Script** | REPL para R, Python y Julia |
| **Data Lab** | Notebooks interactivos |
| **Presentaciones** | Slides con Quarto/Impress.js |
| **IA** | Chat con RAG (300+ entidades) |
| **Ayuda** | Documentación (16 capítulos) |

---

## 4. Funciones Básicas

### R — Estadística

```
=NEVEN.r("mean(c(10,20,30))")     → 20
=NEVEN.r("sd(c(10,20,30))")       → 10
=R.MR_Lineal(Y, X, 1)             → Coeficientes de regresión
```

### Julia — Matemática

```
=NEVEN.j("pi")                    → 3.14159...
=NEVEN.j("factorial(10)")         → 3628800
=J.Algebra(A1:C3, 0, 6)           → Determinante de matriz
```

### Python — Propósito General

```
=NEVEN.P("1+1")                   → 2
=NEVEN.P("sum([10,20,30])")       → 60
=NEVEN.P("round(3.14159, 2)")     → 3.14
=P.MiFuncion(A1, B1)              → Función de usuario Python
```

### Funciones con rangos de Excel

Con una matriz 2x2 en A1:B2 (ej: 1,2,3,4):

```
=J.Algebra(A1:B2,0,0)              → Lista de 12 procedimientos
=J.Algebra(A1:B2,0,6)              → Determinante (-2)
=J.Algebra(A1:B2,0,4)              → Valores propios
```

Con datos en A1:C10 (3 columnas numéricas):

```
=J.Estadistica(A1:C10,0,0)         → Lista de 8 procedimientos
=J.Estadistica(A1:C10,0,1)         → Descriptiva (N, Media, Std, Min, Q1, Med, Q3, Max)
=J.Estadistica(A1:C10,0,2)         → Matriz de correlación
```

**Patrón TipoOutput:** Todas las funciones usan el último argumento como selector:
- `0` = ver lista de procedimientos disponibles
- `1, 2, 3...` = ejecutar el procedimiento correspondiente

---

## 5. Gráficos Interactivos

### Plotly desde rango de Excel

Con datos en A1:C4 (encabezados + 3 filas):

```
=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Mi Gráfico",5))
```

### QuickPlot (9 tipos)

```
=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",1))   → Barras
=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",7))   → ggplot2 interactivo
```

### Dashboard y más

| Fórmula | Resultado |
|:---|:---|
| `=NEVEN.v(R.Dashboard(A1:E11, 1))` | Dashboard 6 pestañas |
| `=NEVEN.v(R.Pivot(A1:E11, 1))` | Tabla pivote interactiva |
| `=NEVEN.v(R.Esquisse(A1:E11, 1))` | Explorador de datos Plotly |
| `=NEVEN.v(R.D3(A1:E11, 1))` | Treemap D3.js |
| `=NEVEN.v(R.D3(A1:E11, 2))` | Diagrama Sankey |
| `=NEVEN.v(R.Map(A1:D11, 1))` | Mapa con marcadores (requiere lat/lon) |

---

## 6. NEVEN Studio — SQL

Ejecuta consultas SQL sobre datos de Excel usando DuckDB.

### Cargar datos

1. Selecciona un rango en Excel
2. En el tab SQL, haz clic en **Cargar selección**
3. Los datos se cargan como tabla `data`

### Consultas

```sql
SELECT * FROM data WHERE columna > 100 ORDER BY otra

SELECT categoria, AVG(ventas) as promedio
FROM data
GROUP BY categoria
HAVING AVG(ventas) > 1000
```

---

## 7. NEVEN Studio — Chat IA con RAG

El tab **IA** incluye un chat con acceso a 300+ entidades de conocimiento.

### Cómo funciona

1. Escribe tu pregunta en lenguaje natural
2. El sistema busca contexto relevante (RAG)
3. La IA responde usando ese contexto

### Indexar documentos

**Formatos soportados:** PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD

1. Haz clic en **...** para seleccionar archivo
2. Asigna un dominio (econometría, estadística, excel, etc.)
3. Haz clic en **Indexar**

---

## 8. Pluto.jl y Quarto

### Enviar datos a Pluto

```
=NEVEN.pluto.data(A1:D20, "datos")    → Envía rango a Julia
=NEVEN.pluto.start()                   → Inicia servidor
=NEVEN.notebook.open("excel_data")     → Abre dashboard con datos
```

### Renderizar documento Quarto

```
=NEVEN.q("C:/NEVEN/quarto/analisis_ventas.qmd")
```

---

## 9. Ribbon — Botones Disponibles

| Grupo | Botón | Acción |
|:---|:---|:---|
| **Studio** | NEVEN Studio | Abre el TaskPane (7 tabs) |
| Motores | Consola R | Abre Rgui.exe |
| Motores | Consola Julia | Abre terminal Julia |
| Motores | Consola Python | Abre terminal Python |
| Motores | Actualizar | Re-registra funciones |
| Visualización | Abrir HTML | Seleccionar archivo HTML |
| Visualización | Presentaciones | Editor Impress.js |
| Visualización | Cerrar Visores | Cierra ventanas WebView2 |
| Pluto.jl | Iniciar Pluto | Arranca servidor |
| Pluto.jl | Notebooks | Lista de notebooks |
| Pluto.jl | Detener Pluto | Detiene servidor |
| Quarto | Renderizar QMD | Seleccionar .qmd |
| Configuración | Carpeta Scripts | Abre C:\NEVEN |
| Configuración | Config JSON | Abre configuración |
| Configuración | Acerca de | Info del proyecto |

---

## 10. Solución de Problemas

### Las fórmulas retornan #NOMBRE?

1. Verificar que el XLL está cargado: Archivo → Opciones → Complementos
2. Si no aparece, Examinar → `C:\NEVEN\NEVEN64.xll`

### El Ribbon no aparece

```powershell
# En PowerShell como administrador:
regsvr32 "C:\NEVEN\NEVENRibbon.dll"

# Si Excel lo deshabilitó por un crash:
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force
```

### Excel se congela al abrir

```powershell
Stop-Process -Name "EXCEL","ControlR","ControlJulia","ControlPython" -Force
```

### NEVEN Studio no abre

Verificar que el servidor HTTP está corriendo:
```
http://localhost:5555/health
```

Si no responde, reiniciar Excel o ejecutar manualmente:
```powershell
cd C:\NEVEN\startup
python neven_http_server.py
```

### Paquetes R faltantes

```
=NEVEN.r("install.packages('plotly', repos='https://cran.r-project.org')")
```

### Chat IA no responde

Verificar configuración de API en `C:\NEVEN\neven-config.json`:
```json
"AI": {
  "provider": "bedrock",
  "model": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

---

## 11. Crear Funciones Propias

### Función R

Crear archivo en `C:\Users\<usuario>\Documents\NEVEN\functions\mi_funcion.R`:

```r
CalcularMargen <- function(ingresos, costos) {
  return((ingresos - costos) / ingresos * 100)
}
attr(CalcularMargen, "description") <- list(
  "Calcula margen de beneficio en porcentaje",
  ingresos = "Ingresos totales",
  costos = "Costos totales"
)
```

Usar en Excel: `=R.CalcularMargen(A1, B1)`

### Función Julia

Agregar al archivo `functions.jl`:

```julia
function MiCalculo(datos, parametro=0)
    return sum(Float64.(datos)) * parametro
end
```

Usar en Excel: `=J.MiCalculo(A1:A10, 5)`

### Función Python

Crear archivo en `C:\Users\<usuario>\Documents\NEVEN\functions\mi_funcion.py`:

```python
def CalcularIVA(monto, tasa=13.0):
    """Calcula el IVA de un monto.

    Args:
        monto: Monto base
        tasa: Porcentaje de IVA (default: 13%)
    """
    return monto * (tasa / 100)
```

Usar en Excel: `=P.CalcularIVA(A1, 13)`

---

## 12. Configuración

El archivo `C:\NEVEN\neven-config.json` controla NEVEN.

### Secciones principales

```json
{
  "R": { "enabled": true, "home": "" },
  "Julia": { "enabled": true, "home": "" },
  "Python": { "enabled": true },
  "RAG": {
    "enabled": true,
    "minScore": 0.50,
    "topK": 3,
    "indexPath": "C:\\NEVEN\\data\\rag_index.duckdb"
  },
  "WebView2": { "maxViewers": 8 },
  "Pluto": { "port": 1234 }
}
```

### Desactivar un lenguaje

Cambiar `"enabled": true` a `"enabled": false` en la sección correspondiente.

---

## 13. Más Ejemplos

Ver la carpeta `Ejemplos/` del proyecto con subcarpetas organizadas por lenguaje:
- `R/` — 40+ ejemplos de funciones R
- `Julia/` — Álgebra, cálculo, optimización
- `Python/` — Integración y funciones de usuario
- `Quarto/` — Documentos y presentaciones

---

## 14. Recursos

| Recurso | Ubicación |
|:---|:---|
| Todas las funciones | Tab **Ayuda** en NEVEN Studio |
| Documentación (16 capítulos) | `C:\NEVEN\docs\neven-docs.html` |
| Diccionario de 200+ funciones | `docs/Diccionario_Funciones.md` |
| Arquitectura del sistema | `docs/arquitectura.md` |
| RAG y formatos | `docs/RAG_GUIDE.md` |
| Troubleshooting detallado | `docs/TROUBLESHOOTING.md` |

---

*NEVEN v3.2 — BukloLAB*
*"La caléndula que no se marchita"*
