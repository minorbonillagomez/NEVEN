---
id: webview2-ribbon
title: Capitulo 7 -- WebView2 y Ribbon
sidebar_label: 7. WebView2 y Ribbon
sidebar_position: 7
---

# Capitulo 7: WebView2 y Ribbon

## 7.1 WebView2 -- Visualización embebida

WebView2 (basado en Microsoft Edge Chromium) permite renderizar contenido HTML interactivo en ventanas flotantes asociadas a Excel.

### Dark mode viewer

El viewer WebView2 usa un fondo grafito (#2D2D2D) por defecto, proporcionando un tema oscuro consistente para todas las visualizaciones interactivas (Plotly, D3.js, Leaflet, rpivotTable). Esto reduce la fatiga visual y mejora el contraste de los graficos.

### Modos de uso

| Fórmula | Contenido |
|:---|:---|
| `=NEVEN.v("<html>...</html>")` | HTML directo (inline) |
| `=NEVEN.v("C:/ruta/archivo.html")` | Archivo HTML local |
| `=NEVEN.v(R.GR_PlotlyView(...))` | Gráfico Plotly desde R |
| `=NEVEN.v(R.Pivot(...))` | Tabla pivote interactiva |
| `=NEVEN.v(R.D3(...))` | Visualización D3.js |
| `=NEVEN.v(R.Dashboard(...))` | Dashboard todo-en-uno |
| `=NEVEN.v(R.Map(...))` | Mapa interactivo Leaflet |
| `=NEVEN.editor()` | Editor de presentaciones Impress.js |

### Gráficos embebidos en hoja (Shapes)

A diferencia del viewer flotante, estas funciones insertan el gráfico directamente en la hoja de Excel como una imagen Shape:

| Fórmula | Motor | Descripción |
|:---|:---|:---|
| `=NEVEN.chart.r(rango, tipo, nombre, ancho, alto)` | R | Gráfico R base incrustado |
| `=NEVEN.chart.p(rango, tipo, nombre, ancho, alto)` | Python | Gráfico matplotlib incrustado |
| `=NEVEN.chart.j(rango, tipo, nombre, ancho, alto)` | Julia | Gráfico Julia incrustado |

**Tipos de gráfico:** 1=Líneas, 2=Barras, 3=Scatter, 4=Histograma, 5=Pie, 6=BoxPlot, 7=Heatmap

### Seguridad del viewer

El filtro de navegacion permite solo contenido confiable:

| Permitido | Ejemplo |
|:---|:---|
| `file://` | Archivos HTML locales |
| `about:blank` | Pagina vacia |
| `data:`, `blob:` | Plotly image export, D3.js SVG |
| `CDNs confiables` | jsdelivr, cloudflare, Google Fonts |
| `localhost:port` | Solo en modo Pluto (Advanced Mode) |

Todo lo demás se bloquea con log de advertencia.

### Funciones del viewer

| Formula | Accion |
|:---|:---|
| `=NEVEN.v.list()` | Lista viewers activos (ej: "viewer-1, viewer-2") |
| `=NEVEN.v.close("viewer-1")` | Cierra un viewer específico |
| `=NEVEN.v.send("viewer-1", json)` | Envía datos JSON al JavaScript del viewer |

---

## 7.2 Ribbon COM -- Interfaz nativa

La pestaña **NEVEN** en la cinta de Excel proporciona acceso directo a todas las funcionalidades:

### Grupos y botones

| Grupo | Boton | Icono | Acción |
|:---|:---|:---|:---|
| **Motores** | Activar NEVEN | ServerConnect | Carga NEVEN64.xll bajo demanda |
| | Actualizar | Refresh | Re-registra funciones R/Julia/Python |
| | Estado | ServerConnection | Muestra estado de los motores |
| | R (toggle) | -- | Activa/desactiva motor R al inicio |
| | Julia (toggle) | -- | Activa/desactiva motor Julia al inicio |
| | Python (toggle) | -- | Activa/desactiva motor Python al inicio |
| **Análisis** | NEVEN Studio | BlogHomePage | Abre NEVEN Studio (analisis interactivo) |
| | Texto | ReviewCompareDocuments | Analisis de documentos PDF/TXT |
| | Simulación | ChartInsert | Explorador Monte Carlo |
| **Visor** | Abrir Visor | PictureInsertFromFile | Dialogo de seleccion de archivo HTML |
| | Cerrar Todos | WindowCloseAllDocuments | Cierra todas las ventanas WebView2 |
| **Notebooks** | Pluto.jl | FileDocumentManagement | Arranca servidor Pluto.jl |
| | Biblioteca | ViewsGallery | Lista de notebooks disponibles |
| | Detener | RecordStop | Detiene servidor Pluto |
| **Studio** | NEVEN Studio | ViewCode | Abre el TaskPane interactivo |
| | Iniciar Servidor | ServerConnection | Inicia servidor HTTP puerto 5555 |
| | Detener Servidor | RecordStop | Detiene servidor HTTP puerto 5555 |
| | Presentaciones | SlideshowFromBeginning | Editor Impress.js |
| **Ayuda** | Documentacion | Help | Abre documentacion NEVEN (17 capitulos) |
| | Acerca de | Info | Muestra mensaje breve → ver Tab Ayuda en NEVEN Studio |

### Botón "Iniciar Servidor"

El botón **Iniciar Servidor** en el grupo Studio permite arrancar el servidor HTTP cuando el TaskPane muestra error de conexion:

1. **Si el servidor ya esta corriendo:** Muestra mensaje informativo (puerto 5555 activo)
2. **Si no esta corriendo:** Inicia `start_studio.py`, espera hasta 15 segundos, y confirma el resultado

Este boton es util cuando:
- El TaskPane muestra "ERROR DEL COMPLEMENTO"
- Se cerro el servidor accidentalmente
- Se necesita reiniciar el servidor después de cambios

### Boton "Detener Servidor"

El boton **Detener Servidor** permite apagar el servidor HTTP de forma limpia:

1. **Si el servidor esta corriendo:** Envía solicitud POST a `/api/shutdown`, espera confirmacion
2. **Si no esta corriendo:** Muestra mensaje indicando que no hay nada que detener

Este botón es útil cuando:
- Se va a cerrar Excel y no se necesita el servidor activo
- Se quiere liberar el puerto 5555 para otro uso
- Se necesita reiniciar el servidor (detener + iniciar)

> **Nota:** El servidor HTTP corre como proceso independiente de Excel. Si cierra Excel sin detener el servidor, este seguira corriendo en segundo plano consumiendo recursos.

### Solución de problemas del Ribbon

Si el Ribbon desaparece después de un crash de Excel:

```powershell
# Limpiar la lista de add-ins deshabilitados
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force

# Verificar registro
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```