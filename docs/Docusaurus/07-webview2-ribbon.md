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
| **Motores** | Consola R | Logo R | Abre Rgui.exe |
| | Consola Julia | Logo Julia | Abre terminal Julia |
| | Instalar Paquete R | Logo R | Dialogo para instalar paquete desde CRAN |
| | Instalar Paquete Julia | Logo Julia | Dialogo para instalar paquete Julia |
| | Paquetes R | Logo R | Lista paquetes R instalados |
| | Paquetes Julia | Logo Julia | Lista paquetes Julia instalados |
| | Actualizar | (refresh) | Re-registra funciones |
| **Visualizacion** | Abrir HTML | (chart) | Dialogo de seleccion de archivo |
| | Presentaciones | (slides) | Editor Impress.js |
| | Listar Visores | (list) | Muestra viewers activos |
| | Cerrar Visores | (close) | Cierra todas las ventanas WebView2 |
| **Pluto.jl** | Iniciar Pluto | (web) | Arranca servidor Pluto.jl |
| | Notebooks | (folder) | Lista de notebooks disponibles |
| | Detener Pluto | (stop) | Detiene servidor |
| **Quarto** | Renderizar QMD | Logo Quarto | Seleccionar y renderizar .qmd |
| **Configuracion** | Carpeta Scripts | (folder) | Abre `C:\NEVEN\` en explorador |
| | Config JSON | (gear) | Abre `neven-config.json` |
| | Acerca de | Logo NEVEN | Informacion del proyecto |

### Solucion de problemas del Ribbon

Si el Ribbon desaparece despues de un crash de Excel:

```powershell
# Limpiar la lista de add-ins deshabilitados
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force

# Verificar registro
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
```
