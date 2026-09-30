---
id: webview2-ribbon
title: Capitulo 7 -- WebView2 y Ribbon
sidebar_label: 7. WebView2 y Ribbon
sidebar_position: 7
---

# Capitulo 7: WebView2 y Ribbon

## 7.1 WebView2 -- Visualizacion embebida

WebView2 (basado en Microsoft Edge Chromium) permite renderizar contenido HTML interactivo en ventanas flotantes asociadas a Excel.

### Dark mode viewer

El viewer WebView2 usa un fondo grafito (#2D2D2D) por defecto, proporcionando un tema oscuro consistente para todas las visualizaciones interactivas (Plotly, D3.js, Leaflet, rpivotTable). Esto reduce la fatiga visual y mejora el contraste de los graficos.

### Modos de uso

| Formula | Contenido |
|:---|:---|
| `=NEVEN.v("<html>...</html>")` | HTML directo (inline) |
| `=NEVEN.v("C:/ruta/archivo.html")` | Archivo HTML local |
| `=NEVEN.v(R.GR_PlotlyView(...))` | Grafico Plotly desde R |
| `=NEVEN.v(R.Pivot(...))` | Tabla pivote interactiva |
| `=NEVEN.v(R.D3(...))` | Visualizacion D3.js |
| `=NEVEN.v(R.Dashboard(...))` | Dashboard todo-en-uno |
| `=NEVEN.v(R.Map(...))` | Mapa interactivo Leaflet |
| `=NEVEN.editor()` | Editor de presentaciones Impress.js |

### Seguridad del viewer

El filtro de navegacion permite solo contenido confiable:

| Permitido | Ejemplo |
|:---|:---|
| `file://` | Archivos HTML locales |
| `about:blank` | Pagina vacia |
| `data:`, `blob:` | Plotly image export, D3.js SVG |
| CDNs confiables | jsdelivr, cloudflare, Google Fonts |
| `localhost:port` | Solo en modo Pluto (Advanced Mode) |

Todo lo demas se bloquea con log de advertencia.

### Funciones del viewer

| Formula | Accion |
|:---|:---|
| `=NEVEN.v.list()` | Lista viewers activos (ej: "viewer-1, viewer-2") |
| `=NEVEN.v.close("viewer-1")` | Cierra un viewer especifico |
| `=NEVEN.v.send("viewer-1", json)` | Envia datos JSON al JavaScript del viewer |

---

## 7.2 Ribbon COM -- Interfaz nativa

La pestana **NEVEN** en la cinta de Excel proporciona acceso directo a todas las funcionalidades:

### Grupos y botones

| Grupo | Boton | Icono | Accion |
|:---|:---|:---|:---|
| **Motores** | Activar NEVEN | ServerConnect | Carga NEVEN64.xll bajo demanda |
| | Actualizar | Refresh | Re-registra funciones R/Julia/Python |
| | Estado | ServerConnection | Muestra estado de los motores |
| | R (toggle) | -- | Activa/desactiva motor R al inicio |
| | Julia (toggle) | -- | Activa/desactiva motor Julia al inicio |
| | Python (toggle) | -- | Activa/desactiva motor Python al inicio |
| **Analisis** | NEVEN Studio | BlogHomePage | Abre NEVEN Studio (analisis interactivo) |
| | Texto | ReviewCompareDocuments | Analisis de documentos PDF/TXT |
| | Simulacion | ChartInsert | Explorador Monte Carlo |
| **Visor** | Abrir Visor | PictureInsertFromFile | Dialogo de seleccion de archivo HTML |
| | Cerrar Todos | WindowCloseAllDocuments | Cierra todas las ventanas WebView2 |
| **Notebooks** | Pluto.jl | FileDocumentManagement | Arranca servidor Pluto.jl |
| | Biblioteca | ViewsGallery | Lista de notebooks disponibles |
| | Detener | RecordStop | Detiene servidor Pluto |
| **Studio** | NEVEN Studio | ViewCode | Abre el TaskPane interactivo |
| | Iniciar Servidor | ServerConnection | Inicia servidor HTTP puerto 5555 |
| | Detener Servidor | RecordStop | Detiene servidor HTTP puerto 5555 |
| | Presentaciones | SlideshowFromBeginning | Editor Impress.js |
| **Ayuda** | Documentacion | Help | Abre documentacion NEVEN |
| | Acerca de | Info | Informacion del proyecto |

### Boton "Iniciar Servidor"

El boton **Iniciar Servidor** en el grupo Studio permite arrancar el servidor HTTP cuando el TaskPane muestra error de conexion:

1. **Si el servidor ya esta corriendo:** Muestra mensaje informativo (puerto 5555 activo)
2. **Si no esta corriendo:** Inicia `start_studio.py`, espera hasta 15 segundos, y confirma el resultado

Este boton es util cuando:
- El TaskPane muestra "ERROR DEL COMPLEMENTO"
- Se cerro el servidor accidentalmente
- Se necesita reiniciar el servidor despues de cambios

### Boton "Detener Servidor"

El boton **Detener Servidor** permite apagar el servidor HTTP de forma limpia:

1. **Si el servidor esta corriendo:** Envia solicitud POST a `/api/shutdown`, espera confirmacion
2. **Si no esta corriendo:** Muestra mensaje indicando que no hay nada que detener

Este boton es util cuando:
- Se va a cerrar Excel y no se necesita el servidor activo
- Se quiere liberar el puerto 5555 para otro uso
- Se necesita reiniciar el servidor (detener + iniciar)

> **Nota:** El servidor HTTP corre como proceso independiente de Excel. Si cierra Excel sin detener el servidor, este seguira corriendo en segundo plano consumiendo recursos.

### Solucion de problemas del Ribbon

Si el Ribbon desaparece despues de un crash de Excel:

```powershell
# Limpiar la lista de add-ins deshabilitados
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force

# Verificar registro
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```
