# NEVEN — Guia de Inicio Rapido

**Version:** 2.0 | **Plataforma:** Windows 10+ (64-bit) | **Excel:** 2013, 2016, 2019 o Microsoft 365

---

## 1. Instalacion

### Requisitos previos

| Componente | Requerido | Descarga |
|:---|:---|:---|
| Microsoft Excel | Si (64-bit) | Ya instalado en tu equipo |
| R 4.4.1+ | Si | https://cran.r-project.org/bin/windows/base/ |
| Julia 1.12.6+ | Opcional | https://julialang.org/downloads/ |

> Julia es opcional. Si no la necesitas, puedes desactivarla en la configuracion (ver seccion 6).

### Pasos de instalacion

**Paso 1:** Instala R desde https://cran.r-project.org. Usa las opciones por defecto.

**Paso 2:** Copia los archivos de NEVEN a `C:\NEVEN\`:

```
C:\NEVEN\
  NEVEN64.xll          <- Add-in de Excel
  ControlR.exe          <- Motor de R
  ControlJulia.exe      <- Motor de Julia (opcional)
  neven-config.json     <- Configuracion
  neven-languages.json  <- Definicion de lenguajes
  startup\startup.r     <- Script de inicio de R
  startup\startup.jl    <- Script de inicio de Julia
```

**Paso 3:** Abre Excel y carga el add-in:
1. Ve a **Archivo → Opciones → Complementos**
2. En "Administrar", selecciona **Complementos de Excel** y haz clic en **Ir...**
3. Haz clic en **Examinar** y selecciona `C:\NEVEN\NEVEN64.xll`
4. Marca la casilla y haz clic en **Aceptar**

**Paso 4:** Verifica que funciona. En cualquier celda escribe:

```
=NEVEN.R("1+1")
```

Si retorna **2**, NEVEN esta funcionando. Prueba tambien Julia y Python:

```
=NEVEN.J("sqrt(144)")     → 12
=NEVEN.P("1+1")           → 2
```

---

## 2. Tu Primera Formula R

NEVEN expone funciones de R como formulas de Excel. No necesitas saber R para usarlas.

### Ejemplo: Regresion lineal

Supongamos que tienes datos en Excel:
- Columna A (filas 2-11): Variable dependiente (Y)
- Columna B (filas 2-11): Variable independiente (X)

En una celda escribe:

```
=R.MR_Lineal(A2:A11, B2:B11, 1)
```

Esto ejecuta una regresion lineal y retorna los coeficientes. El tercer parametro (`TipoOutput`) controla que resultado obtener:

| TipoOutput | Resultado |
|:---:|:---|
| 0 | Lista de procedimientos disponibles |
| 1 | Coeficientes del modelo |
| 2 | Resumen completo (R², p-values) |
| 3 | Tabla ANOVA |
| 4 | Residuos |

> **Tip:** Usa `TipoOutput = 0` en cualquier funcion para ver que opciones tiene.

---

## 3. Tu Primer Grafico Interactivo

NEVEN puede generar graficos interactivos con zoom, hover y tooltips usando Plotly, D3.js y Leaflet.

### Ejemplo: Dashboard interactivo

Con datos en el rango A1:E11 (con encabezados), escribe:

```
=NEVEN.v(R.Dashboard(A1:E11, 1))
```

Esto abre una ventana con un dashboard de 6 pestanas:
- Tabla pivote (drag-and-drop)
- Graficos Plotly (scatter, barras, lineas)
- Visualizaciones D3 (treemap, sankey)

### Otros graficos disponibles

| Formula | Resultado |
|:---|:---|
| `=NEVEN.v(R.Pivot(A1:E11, 1))` | Tabla pivote interactiva |
| `=NEVEN.v(R.Esquisse(A1:E11, 1))` | Explorador de datos Plotly |
| `=NEVEN.v(R.D3(A1:E11, 1))` | Treemap D3.js |
| `=NEVEN.v(R.D3(A1:E11, 2))` | Diagrama Sankey |
| `=NEVEN.v(R.Map(A1:D11, 1))` | Mapa con marcadores (requiere lat/lon) |

> **Nota:** La primera vez que uses graficos interactivos, R necesita instalar paquetes. Ejecuta:
> `=NEVEN.r("install.packages(c('plotly','htmlwidgets','rpivotTable','jsonlite'), repos='https://cran.r-project.org')")`

---

## 4. Funciones Julia (Opcional)

Si tienes Julia instalada, puedes usar funciones matematicas avanzadas:

```
=NEVEN.j("sqrt(144)")                    → 12
=J.Algebra(A1:C3, 0, 6)                  → Determinante de matriz
=J.Estadistica(A1:A20, 0, 1)             → Estadistica descriptiva
=J.Regresion(X, Y, 0, 1)                 → Coeficientes de regresion
```

### Funciones Julia disponibles

| Funcion | Que hace |
|:---|:---|
| `J.Algebra` | Algebra lineal: LU, QR, SVD, eigenvalores, determinante |
| `J.Calculo` | Derivadas, integrales, biseccion, interpolacion |
| `J.Estadistica` | Descriptiva, correlacion, t-test, normalizar |
| `J.KNN` | Clasificacion K-Nearest Neighbors |
| `J.Regresion` | Regresion lineal con intervalos de confianza |
| `J.Clustering` | K-Medias con WCSS y metodo del codo |
| `J.Optimizar` | Gradiente, Newton, simplex, programacion cuadratica |

> **Nota:** Julia tarda ~15 segundos en estar lista despues de abrir Excel (carga de sysimage). Si una funcion Julia retorna "read error", espera unos segundos y presiona F9 para recalcular.

---

## 5. Funciones Python (Opcional)

Si tienes Python 3.10+ instalado, puedes ejecutar codigo Python desde Excel:

```
=NEVEN.P("1+1")                          → 2
=NEVEN.P("sum([10,20,30])")              → 60
=NEVEN.P("round(3.14159, 2)")            → 3.14
=NEVEN.P("len('hola mundo')")            → 10
```

Las funciones de usuario Python se registran con prefijo `P.`:

```
=P.MiFuncion(A1, B1)
```

> **Nota:** Si Python no esta instalado, NEVEN arranca limpiamente solo con R y Julia. Para deshabilitar Python manualmente, cambia `"enabled": false` en la seccion Python de `neven-config.json`.

---

## 6. Funciones del Sistema

| Formula | Que hace |
|:---|:---|
| `=NEVEN.R("codigo R")` | Ejecuta codigo R arbitrario |
| `=NEVEN.J("codigo Julia")` | Ejecuta codigo Julia arbitrario |
| `=NEVEN.P("codigo Python")` | Ejecuta codigo Python arbitrario |
| `=NEVEN.V(html_o_ruta)` | Abre contenido HTML en el visor WebView2 |
| `=NEVEN.Q("archivo.qmd")` | Renderiza un documento Quarto |
| `=NEVEN.pluto.start()` | Inicia el servidor Pluto.jl (notebooks) |
| `=NEVEN.pluto.data(rango, "nombre")` | Envia datos de Excel a Pluto |

---

## 6. Configuracion

El archivo `C:\NEVEN\neven-config.json` controla el comportamiento de NEVEN.

### Desactivar Julia (si no la necesitas)

Cambia `"enabled": true` a `"enabled": false` en la seccion Julia:

```json
"Julia": {
  "home": "",
  "enabled": false,
  "minMajor": 1,
  "minMinor": 6,
  "maxMajor": 99
}
```

Esto evita que NEVEN intente buscar y conectar Julia al abrir Excel. Las funciones `J.*` no estaran disponibles, pero R funcionara sin problemas.

### Parametros principales

| Parametro | Default | Que hace |
|:---|:---|:---|
| `sandboxEnabled` | true | Bloquea comandos peligrosos en `=NEVEN.r()` |
| `callTimeoutMs` | 600000 (10 min) | Tiempo maximo de espera para una llamada |
| `maxRetries` | 2 | Reintentos al reconectar un pipe roto |
| `WebView2.maxViewers` | 8 | Maximo de ventanas de visualizacion |
| `Pluto.port` | 1234 | Puerto del servidor Pluto.jl |

---

## 7. Crear Tus Propias Funciones

Crea un archivo `.R` en `Documentos\NEVEN\functions\`:

```r
# MiSuma.R
MiSuma <- function(a, b) a + b

attr(MiSuma, "description") <- list(
  "Suma dos valores",
  a = "Primer valor",
  b = "Segundo valor"
)
attr(MiSuma, "category") <- "Mis Funciones"
```

Guarda el archivo. NEVEN lo detecta automaticamente (hot-reload). Usa en Excel:

```
=R.MiSuma(A1, B1)
```

La funcion aparece en el **Asistente de Funciones** (Shift+F3) bajo la categoria "Mis Funciones" con la descripcion que definiste.

---

## 8. Solucion de Problemas Rapida

| Problema | Solucion |
|:---|:---|
| `#NOMBRE?` en las formulas | Verificar que el XLL esta cargado (Archivo → Opciones → Complementos) |
| `=NEVEN.r("1+1")` retorna `#VALOR!` | Cerrar Excel, matar ControlR.exe en Task Manager, reabrir |
| Julia retorna "read error" | Esperar 15 segundos y presionar F9 |
| Paquete R no encontrado | `=NEVEN.r("install.packages('nombre', repos='https://cran.r-project.org')")` |
| Grafico no se abre | Envolver con `NEVEN.v()`: `=NEVEN.v(R.Pivot(rango, 1))` |
| Excel se congela al abrir | Matar procesos: `taskkill /f /im excel.exe & taskkill /f /im ControlR.exe` |

Para problemas mas complejos, consulta `docs/TROUBLESHOOTING.md`.

---

## 9. Donde Encontrar Mas Informacion

| Recurso | Ubicacion |
|:---|:---|
| Todas las funciones R | Shift+F3 en Excel (Asistente de Funciones) |
| Ejemplos en Excel | Carpeta `Ejemplos/` del proyecto |
| Documentacion completa | Carpeta `docs/` del proyecto |
| Troubleshooting detallado | `docs/TROUBLESHOOTING.md` |
| Arquitectura del sistema | `docs/arquitectura.md` |

---

*NEVEN v2.0 — Universidad de Costa Rica*
*"La calendula que no se marchita"*
