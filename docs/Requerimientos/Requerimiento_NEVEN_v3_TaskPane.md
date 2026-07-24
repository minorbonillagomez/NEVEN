# NEVEN v3.0 — Task Pane + Bridge Bidireccional

## Visión
Convertir el Viewer de NEVEN en un Task Pane embebido dentro de Excel que se comunica bidireccionalmente con las celdas, eliminando la necesidad de fórmulas intermedias. El usuario interactúa con los datos directamente desde el panel lateral.

---

## Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                     EXCEL WINDOW                             │
├────────────────────────────┬────────────────────────────────┤
│                            │     TASK PANE (HTML/JS)        │
│    SPREADSHEET             │  ┌──────────────────────────┐  │
│    (datos del usuario)     │  │  Data Studio / Dashboard  │  │
│                            │  │  Geodata / ML Reports     │  │
│    A    B    C    D        │  │                          │  │
│  1 Lat  Lon  Val  Cat      │  │  ← Office.js API →      │  │
│  2 9.93 -84  450  Norte    │  │     Excel.run()          │  │
│  3 9.94 -84  320  Sur      │  │     range.values         │  │
│  4 ...                     │  │                          │  │
│                            │  │  ← localhost:5555 →      │  │
│                            │  │     fetch() → Python     │  │
│                            │  │     DuckDB queries       │  │
│                            │  └──────────────────────────┘  │
├────────────────────────────┴────────────────────────────────┤
│  NEVEN64.xll (XLL) + NEVENRibbon.dll (COM) ← coexisten     │
│  ControlPython.exe ← API HTTP en localhost:5555             │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes Clave

### 1. manifest.xml (Office Web Add-in)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1" 
           xsi:type="TaskPaneApp">
  <Id>neven-data-studio-{guid}</Id>
  <Version>3.0.0</Version>
  <ProviderName>NEVEN Project</ProviderName>
  <DefaultLocale>es-ES</DefaultLocale>
  <DisplayName DefaultValue="NEVEN Studio"/>
  <Description DefaultValue="Análisis interactivo embebido en Excel"/>
  <Hosts><Host Name="Workbook"/></Hosts>
  <DefaultSettings>
    <SourceLocation DefaultValue="https://localhost:5555/taskpane.html"/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>
  
  <!-- Coexistencia con XLL existente -->
  <EquivalentAddins>
    <EquivalentAddin>
      <FileName>NEVEN64.xll</FileName>
      <Type>XLL</Type>
    </EquivalentAddin>
  </EquivalentAddins>
</OfficeApp>
```

**Nota:** Microsoft permite que un Office Web Add-in coexista con un XLL/COM add-in en la misma máquina. El elemento `EquivalentAddins` controla la prioridad.

### 2. Servidor Local (ControlPython ampliado)
ControlPython.exe se extiende para exponer un endpoint HTTP en localhost:

```python
# Dentro de ControlPython o como microservicio separado
from http.server import HTTPServer, BaseHTTPRequestHandler
import duckdb, json

class NEVENHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        
        if body["action"] == "query":
            result = duckdb_execute(body["sql"])
            self.respond(result)
        
        elif body["action"] == "analyze":
            result = full_analysis(body["data"])
            self.respond(result)
        
        elif body["action"] == "groupby":
            result = groupby_live(body["column"], body["metric"], body["value_col"])
            self.respond(result)
```

### 3. Task Pane HTML (taskpane.html)
```javascript
// Leer datos directamente de las celdas seleccionadas
async function readSelectedData() {
    await Excel.run(async (context) => {
        const range = context.workbook.getSelectedRange();
        range.load("values, address, columnCount, rowCount");
        await context.sync();
        
        // Enviar a Python para análisis
        const response = await fetch("http://localhost:5555/analyze", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                action: "analyze",
                data: range.values,
                address: range.address
            })
        });
        
        const result = await response.json();
        renderDashboard(result); // Actualizar el Task Pane
    });
}

// Escribir resultados de vuelta a Excel
async function writeResults(data, targetAddress) {
    await Excel.run(async (context) => {
        const sheet = context.workbook.worksheets.getActiveWorksheet();
        const range = sheet.getRange(targetAddress);
        range.values = data;
        range.format.autofitColumns();
        await context.sync();
    });
}

// GROUP BY en vivo
async function liveGroupBy(column, metric, valueCol) {
    const response = await fetch("http://localhost:5555/query", {
        method: "POST",
        body: JSON.stringify({
            action: "query",
            sql: `SELECT "${column}", ${metric}("${valueCol}") as resultado 
                  FROM dataset GROUP BY "${column}" ORDER BY resultado DESC`
        })
    });
    const result = await response.json();
    renderGroupByChart(result);
}
```

---

## Flujo de Usuario v3.0

1. **Usuario abre NEVEN Studio** (botón en Ribbon o automático)
2. **Task Pane aparece** al costado derecho de Excel
3. **Selecciona rango** en la hoja → el Task Pane detecta automáticamente:
   - Muestra preview de los datos
   - Sugiere análisis según tipos detectados
4. **Click "Analizar"** → envía datos a Python/DuckDB
5. **Resultados aparecen** en el Task Pane (gráficos, tablas, correlaciones)
6. **GROUP BY interactivo** → dropdown, resultado instantáneo sobre datos COMPLETOS
7. **"Exportar a hoja"** → escribe resultados en una hoja nueva automáticamente
8. **SQL libre** → campo de texto, resultados renderizados en el panel

---

## Coexistencia XLL + Task Pane

Microsoft soporta oficialmente que ambos coexistan:

| Componente | Función | Tecnología |
|---|---|---|
| NEVEN64.xll | Funciones =P.*, =R.*, =J.* | XLL C++ |
| NEVENRibbon.dll | Botones del Ribbon | COM |
| NEVEN Studio (Task Pane) | Panel interactivo | Office.js + HTML |
| ControlPython.exe | Backend DuckDB + ML | Python HTTP |

El XLL sigue manejando las fórmulas de celda. El Task Pane maneja la interactividad visual. No compiten — se complementan.

---

## Ventajas sobre v2.1

| v2.1 (actual) | v3.0 (Task Pane) |
|---|---|
| Viewer en ventana separada | Panel embebido dentro de Excel |
| Requiere fórmula → path → NEVEN.v() | Click en rango → análisis directo |
| GROUP BY pre-calculado | GROUP BY en vivo sobre datos completos |
| No puede escribir de vuelta | Exporta resultados a hojas nuevas |
| SQL requiere celda separada | SQL integrado en el panel |
| Datos salen de Excel | Datos nunca salen del contexto |

---

## Requisitos de Instalación

1. **Excel 2016+ o Microsoft 365** (Office.js requiere mínimo 16.0)
2. **Sideload del manifest.xml** (no requiere publicar en AppSource):
   - Compartir carpeta de red con el manifest
   - O insertar via registro de Windows
   - O catálogo centralizado de la organización
3. **ControlPython con HTTP server** en localhost:5555
4. **CORS habilitado** en el server local

---

## Plan de Implementación

### Fase 1: HTTP Server en ControlPython (2 días)
- Agregar endpoint HTTP en localhost:5555
- Endpoints: /analyze, /query, /groupby, /health
- CORS headers para Office.js

### Fase 2: manifest.xml + taskpane.html (2 días)
- Crear manifest para sideload
- Portar el HTML del Data Studio actual al Task Pane
- Integrar Office.js para leer rangos

### Fase 3: Bridge Bidireccional (3 días)
- Leer selección → enviar a Python → renderizar
- Escribir resultados de vuelta a la hoja
- Event listeners para cambio de selección (reactivo)

### Fase 4: GROUP BY en vivo + SQL (2 días)
- Eliminar pre-cálculo, todo en tiempo real
- Campo SQL con autocompletado de columnas
- Resultados exportables a hoja

### Fase 5: Testing + Deploy (1 día)
- Probar con datasets 1M+ filas
- Documentar sideload para usuarios
- Integrar en instalador

**Estimado total: 10 días**

---

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Office.js no disponible en Excel antiguo | Fallback a Viewer actual (v2.1 sigue funcional) |
| CORS bloqueado por políticas corporativas | Servidor local no requiere internet |
| Rendimiento con 10M filas | DuckDB streaming + paginación |
| Sideload restringido por IT | Documentar alternativas de despliegue |

---

## Conclusión

La v3.0 con Task Pane convierte a NEVEN en una herramienta de BI embebida dentro de Excel, sin servidor externo, sin cloud, 100% local. El usuario selecciona datos → ve análisis → exporta resultados, todo sin salir de la hoja. Con DuckDB como motor, no hay límite de filas.

La coexistencia con el XLL actual está oficialmente soportada por Microsoft, lo que significa que las funciones `=P.*`, `=R.*`, `=J.*` siguen funcionando exactamente igual. El Task Pane es un layer adicional de interactividad.
