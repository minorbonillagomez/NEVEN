---
id: office-addin
title: "Capitulo 21 - Office Add-in (TaskPane Integrado)"
sidebar_label: 21. Office Add-in
sidebar_position: 21
---

# Capitulo 21: Office Add-in (TaskPane Integrado)

**Disponible desde:** Agosto 2026

NEVEN puede ejecutarse como un **Office Web Add-in**, integrando el TaskPane directamente dentro de Excel como un panel lateral nativo. Esta modalidad ofrece mejor integración con Excel que el modo Standalone.

---

## 21.1 Modos de operación de NEVEN Studio

NEVEN Studio puede ejecutarse de dos formas:

| Modo | Descripción | Ventajas |
|:---|:---|:---|
| **Standalone** | Navegador externo (localhost:5555) | No requiere Excel, independiente |
| **Office Add-in** | Panel lateral dentro de Excel | Integración nativa, acceso directo a datos |

---

## 21.2 Diferencias entre modos

| Característica | Standalone | Office Add-in |
|:---|:---|:---|
| Ubicación | Navegador externo | Panel lateral de Excel |
| Acceso a celdas | Via Bridge (indirecto) | Via Office.js (directo) |
| Fórmulas | No puede insertar | Puede insertar fórmulas |
| Selección Excel | Requiere "Enviar a Studio" | Lectura automática |
| Persistencia | Se cierra con el navegador | Se mantiene con Excel |
| Requisitos | Solo Python | Excel + Python |

---

## 21.3 Habilitar el Office Add-in

### Paso 1: Verificar archivos

El instalador de NEVEN crea estos archivos:

```
C:\NEVEN\
├── manifest.xml           ← Manifiesto del Add-in
├── catalog\
│   └── manifest.xml       ← Copia para el catálogo
└── TaskPane\
    └── taskpane.html      ← Interfaz del Add-in
```

### Paso 2: Configurar catálogo de confianza

Excel debe confiar en el directorio del catálogo:

```
1. Excel → Archivo → Opciones
2. Centro de confianza → Configuración del Centro de confianza
3. Catálogos de complementos de confianza
4. Agregar: \\localhost\C$\NEVEN\catalog
5. Marcar "Mostrar en menú"
6. Aceptar y reiniciar Excel
```

**Nota:** El path usa `\\localhost\C$\...` (UNC path) porque Excel requiere este formato para catálogos locales.

### Paso 3: Insertar el Add-in

```
1. Excel → Insertar → Mis complementos
2. Carpeta compartida → NEVEN Studio
3. Clic "Agregar"
4. El TaskPane aparece como panel lateral
```

---

## 21.4 Estructura del manifest.xml

El manifiesto define la configuración del Add-in:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:type="TaskPaneApp">
  
  <!-- Identificación -->
  <Id>neven-studio-addin</Id>
  <Version>2.3.0</Version>
  <ProviderName>NEVEN Project</ProviderName>
  <DefaultLocale>es-CR</DefaultLocale>
  
  <!-- Nombre y descripción -->
  <DisplayName DefaultValue="NEVEN Studio"/>
  <Description DefaultValue="Análisis estadístico con R, Julia y Python"/>
  
  <!-- Hosts soportados -->
  <Hosts>
    <Host Name="Workbook"/>
  </Hosts>
  
  <!-- Permisos -->
  <Permissions>ReadWriteDocument</Permissions>
  
  <!-- URL del TaskPane -->
  <DefaultSettings>
    <SourceLocation DefaultValue="http://localhost:5555/taskpane.html"/>
  </DefaultSettings>
  
</OfficeApp>
```

---

## 21.5 Permisos del Add-in

El Add-in solicita permisos para:

| Permiso | Descripción | Uso |
|:---|:---|:---|
| **ReadDocument** | Leer celdas y rangos | Obtener datos para análisis |
| **WriteDocument** | Escribir en celdas | Insertar resultados |
| **ReadWriteDocument** | Ambos | Flujo completo de análisis |

---

## 21.6 API Office.js

El Office Add-in usa la API Office.js para interactuar con Excel:

### Leer selección actual

```javascript
async function readSelection() {
  return Excel.run(async (context) => {
    const selection = context.workbook.getSelectedRange();
    selection.load(['values', 'address', 'rowCount', 'columnCount']);
    await context.sync();
    
    return {
      values: selection.values,
      address: selection.address,
      rows: selection.rowCount,
      cols: selection.columnCount
    };
  });
}
```

### Escribir en celda

```javascript
async function writeToCell(address, value) {
  return Excel.run(async (context) => {
    const range = context.workbook.worksheets
      .getActiveWorksheet()
      .getRange(address);
    range.values = [[value]];
    await context.sync();
  });
}
```

### Insertar fórmula NEVEN

```javascript
async function insertNevenFormula(address, formula) {
  return Excel.run(async (context) => {
    const range = context.workbook.worksheets
      .getActiveWorksheet()
      .getRange(address);
    // Ejemplo: =NEVEN.R("AD_ACP.C", A1:D20)
    range.formulas = [[formula]];
    await context.sync();
  });
}
```

---

## 21.7 Flujo de datos Office Add-in vs Standalone

### Standalone (via Bridge)

```
Excel                    NEVEN Studio (Browser)
  │                            │
  │  [Usuario selecciona]      │
  │                            │
  │  ──── "Enviar a Studio" ──►│
  │       (HTTP POST)          │
  │                            │
  │                      [Procesar datos]
  │                            │
  │  ◄─── Resultados ─────────│
  │       (mostrar en browser) │
```

### Office Add-in (via Office.js)

```
Excel + TaskPane (mismo proceso)
  │
  │  [Usuario selecciona rango]
  │           │
  │           ▼
  │  [TaskPane lee via Office.js]
  │           │
  │           ▼
  │  [Procesar datos]
  │           │
  │           ▼
  │  [Insertar resultados via Office.js]
  │
```

---

## 21.8 Ventajas del modo Office Add-in

### 1. Lectura automática de selección

No es necesario hacer clic en "Enviar a Studio". Quick Plots y Chart Gallery pueden leer la selección directamente:

```javascript
// En Office Add-in, esto funciona directamente
const data = await readExcelSelection();
```

### 2. Inserción de fórmulas

El Add-in puede insertar fórmulas NEVEN en celdas:

```javascript
// Insertar fórmula de regresión
await insertNevenFormula('E1', '=NEVEN.R("RG_Lineal.C", A1:D20)');
```

### 3. Persistencia

El TaskPane permanece abierto mientras Excel esté abierto, incluso al cambiar de libro.

### 4. Experiencia nativa

El panel lateral se comporta como cualquier otro panel de Excel (se puede anclar, redimensionar, minimizar).

---

## 21.9 Limitaciones del modo Office Add-in

| Limitación | Explicación |
|:---|:---|
| Requiere servidor HTTP | El TaskPane carga desde localhost:5555 |
| Un solo Add-in NEVEN | No puede haber múltiples instancias |
| Tamaño del panel | Limitado al ancho del panel lateral |
| Sin acceso a VBA | Office.js no puede ejecutar macros VBA |

---

## 21.10 Ribbon del Office Add-in

El Add-in puede agregar botones al Ribbon de Excel:

```xml
<!-- En manifest.xml -->
<ExtensionPoint xsi:type="PrimaryCommandSurface">
  <CustomTab id="NEVEN.Tab">
    <Label resid="TabLabel"/>
    <Group id="NEVEN.Group">
      <Label resid="GroupLabel"/>
      <Control xsi:type="Button" id="ShowTaskpane">
        <Label resid="ButtonLabel"/>
        <Icon>
          <bt:Image size="16" resid="Icon16"/>
          <bt:Image size="32" resid="Icon32"/>
        </Icon>
        <Action xsi:type="ShowTaskpane">
          <TaskpaneId>NEVEN.Taskpane</TaskpaneId>
        </Action>
      </Control>
    </Group>
  </CustomTab>
</ExtensionPoint>
```

### Coexistencia con COM Ribbon

NEVEN tiene dos Ribbons:

| Ribbon | Tipo | Contenido |
|:---|:---|:---|
| **COM Add-in** | C++ nativo | Activar, Servidor, Pluto, Simulación |
| **Office Add-in** | manifest.xml | Botón NEVEN Studio |

Ambos aparecen en Excel pero con propósitos diferentes.

---

## 21.11 Troubleshooting

**El Add-in no aparece en "Mis complementos":**
- Verificar que el catálogo esté configurado correctamente
- Usar ruta UNC: `\\localhost\C$\NEVEN\catalog`
- Reiniciar Excel después de agregar el catálogo

**El TaskPane muestra error de conexión:**
- Verificar que el servidor HTTP esté corriendo (puerto 5555)
- Ejecutar: `C:\NEVEN\TaskPane\NEVEN Studio.vbs` o iniciar desde Ribbon

**Office.js no funciona:**
- Verificar que `Office.initialize` se ejecute
- Revisar la consola del navegador (F12 en el TaskPane)
- Verificar permisos en manifest.xml

**El Add-in se carga muy lento:**
- Primera carga puede tardar (Office descarga Office.js)
- Las siguientes cargas son más rápidas (cache)

---

## 21.12 Desarrollo y depuración

### Abrir DevTools en el TaskPane

```
1. Clic derecho en el TaskPane
2. "Inspeccionar" o "Inspect Element"
3. Se abre la consola de depuración
```

### Recargar el TaskPane

```
1. Clic derecho en el TaskPane
2. "Recargar" o presionar F5
```

### Logs de Office.js

```javascript
// Habilitar logging
Office.onReady((info) => {
  console.log('Office.js ready');
  console.log('Host:', info.host);
  console.log('Platform:', info.platform);
});
```

---

## 21.13 Actualizar el Add-in

Cuando se actualiza NEVEN:

1. **Actualizar manifest.xml** si hay cambios de configuración
2. **Limpiar cache de Office:**
   ```
   %LOCALAPPDATA%\Microsoft\Office\16.0\Wef\
   ```
3. **Reiniciar Excel**
4. El Add-in carga la nueva versión desde localhost

---

## 21.14 Seguridad

### HTTPS en producción

Para entornos de producción, se recomienda usar HTTPS:

```xml
<SourceLocation DefaultValue="https://localhost:5555/taskpane.html"/>
```

Requiere configurar certificado SSL en el servidor Python.

### Permisos mínimos

Si solo se necesita lectura:

```xml
<Permissions>ReadDocument</Permissions>
```

---

*Documentación actualizada: Agosto 2026*

*Office Add-in — Agosto 2026*
*Universidad de Costa Rica — Tesis de Maestría*

