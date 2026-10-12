# 07 — Análisis de Seguridad Electron (Console/)

**Fecha:** 2025-01-XX  
**Alcance:** `Console/` — Aplicación Electron REPL para RJ2XCL  
**Versión Electron:** 1.8.2 (publicada ~febrero 2018)  
**Hallazgos totales:** 12  

## Tabla Resumen

| ID | Severidad | Archivo | Título |
|----|-----------|---------|--------|
| SEC-ELC-001 | Crítica | Console/package.json | Electron 1.8.2 severamente desactualizado con CVEs conocidos |
| SEC-ELC-002 | Crítica | Console/main.js | nodeIntegration habilitado por defecto sin contextIsolation |
| SEC-ELC-003 | Alta | Console/main.js | Ausencia de Content-Security-Policy (CSP) |
| SEC-ELC-004 | Alta | Console/REPL.ts:45 | XSS via innerHTML con datos de ejecución de código |
| SEC-ELC-005 | Alta | Console/src/ui/alert.ts:115 | XSS via innerHTML en mensajes de alerta |
| SEC-ELC-006 | Alta | Console/src/ui/dialog.ts:123 | XSS via innerHTML en cuerpo de diálogos |
| SEC-ELC-007 | Alta | Console/src/shell/language_interface_r.ts:331 | XSS via innerHTML con descripciones de paquetes R |
| SEC-ELC-008 | Alta | Console/src/editor/editor.ts:688 | XSS via renderizado Markdown sin sanitización |
| SEC-ELC-009 | Alta | Console/src/renderer.ts:22 | Uso irrestricto del módulo `remote` (deprecated) |
| SEC-ELC-010 | Media | Console/main.js:30 | electron-reload activo en producción |
| SEC-ELC-011 | Media | Console/src/shell/terminal_implementation.ts:1164 | shell.openExternal con URIs no validadas |
| SEC-ELC-012 | Media | Console/src/renderer.ts | Acceso directo a `fs` desde proceso renderer |

---

## Hallazgos Detallados

### [SEC-ELC-001] Electron 1.8.2 severamente desactualizado con CVEs conocidos
- **Archivo:** Console/package.json:16
- **Severidad:** Crítica
- **Descripción:** La aplicación utiliza Electron `^1.8.2` (publicada en febrero 2018). Esta versión está basada en Chromium ~59 y Node.js ~8, ambos fuera de soporte desde hace años. Contiene cientos de vulnerabilidades conocidas incluyendo ejecución remota de código (RCE), bypass de sandbox, y vulnerabilidades de V8. No recibe parches de seguridad desde 2018.
- **Código:**
```json
"devDependencies": {
    "electron": "^1.8.2",
}
```
- **Recomendación:** Actualizar a Electron ≥28.x (última LTS estable). Esto requiere migración significativa: reemplazar el módulo `remote` (eliminado en Electron 14+), implementar `contextBridge`, y adaptar la API de IPC. Considerar si la consola Electron sigue siendo necesaria dado que el proyecto ya usa WebView2.

---

### [SEC-ELC-002] nodeIntegration habilitado por defecto sin contextIsolation
- **Archivo:** Console/main.js:79
- **Severidad:** Crítica
- **Descripción:** El `BrowserWindow` se crea sin especificar `webPreferences`. En Electron 1.8.x, los valores por defecto son `nodeIntegration: true` y `contextIsolation: false`. Esto significa que cualquier código JavaScript ejecutado en la ventana (incluyendo scripts de terceros, contenido renderizado, o inyecciones XSS) tiene acceso completo a Node.js: sistema de archivos, procesos hijo, red, etc. Un ataque XSS se convierte automáticamente en ejecución remota de código.
- **Código:**
```javascript
// Create the browser window.
mainWindow = new BrowserWindow(window_state);
// No webPreferences configurado — defaults inseguros en Electron 1.x:
// nodeIntegration: true, contextIsolation: false
```
- **Recomendación:** Configurar explícitamente las opciones de seguridad:
```javascript
mainWindow = new BrowserWindow({
  ...window_state,
  webPreferences: {
    nodeIntegration: false,
    contextIsolation: true,
    enableRemoteModule: false,
    sandbox: true,
    preload: path.join(__dirname, 'preload.js')
  }
});
```
Implementar un `preload.js` con `contextBridge.exposeInMainWorld()` para exponer solo las APIs necesarias.

---

### [SEC-ELC-003] Ausencia de Content-Security-Policy (CSP)
- **Archivo:** Console/index.html
- **Severidad:** Alta
- **Descripción:** El archivo `index.html` no define ninguna meta tag `Content-Security-Policy` ni se configura CSP via headers en el proceso principal. Sin CSP, no hay restricciones sobre qué scripts pueden ejecutarse, qué recursos pueden cargarse, ni qué conexiones de red pueden establecerse. Esto facilita la explotación de vulnerabilidades XSS.
- **Código:**
```html
<html>
  <head>
    <meta charset="UTF-8">
    <title>RJ2XCL Console</title>
    <!-- No hay meta CSP -->
```
- **Recomendación:** Agregar una política CSP restrictiva:
```html
<meta http-equiv="Content-Security-Policy" 
  content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;">
```
O mejor aún, configurar CSP via `session.defaultSession.webRequest.onHeadersReceived` en el proceso principal.

---

### [SEC-ELC-004] XSS via innerHTML con datos de ejecución de código
- **Archivo:** Console/REPL.ts:45
- **Severidad:** Alta
- **Descripción:** El método `promptUser()` inserta directamente el resultado de la ejecución de código R/Julia en el DOM usando `innerHTML` sin sanitización. Si la salida de R o Julia contiene HTML malicioso (por ejemplo, `cat("<img src=x onerror=require('child_process').exec('calc')>")`), se ejecutará con privilegios completos de Node.js debido a `nodeIntegration: true`.
- **Código:**
```typescript
private promptUser(msg: string) {
    const terminal = document.getElementById('terminal-output');
    if (terminal) {
        terminal.innerHTML += `<div>${msg}</div>`;
        terminal.scrollTop = terminal.scrollHeight;
    }
}
```
- **Recomendación:** Usar `textContent` o crear nodos DOM de forma segura:
```typescript
private promptUser(msg: string) {
    const terminal = document.getElementById('terminal-output');
    if (terminal) {
        const div = document.createElement('div');
        div.textContent = msg;
        terminal.appendChild(div);
        terminal.scrollTop = terminal.scrollHeight;
    }
}
```

---

### [SEC-ELC-005] XSS via innerHTML en mensajes de alerta
- **Archivo:** Console/src/ui/alert.ts:115
- **Severidad:** Alta
- **Descripción:** El componente `AlertManager.Show()` inserta el campo `spec.message` directamente como HTML en el DOM. Si el mensaje proviene de datos externos (respuestas de pipe, errores del backend, datos de actualización), un atacante podría inyectar HTML/JS arbitrario. Los botones también se construyen con interpolación de strings sin escapar.
- **Código:**
```typescript
AlertManager.container_node_.querySelector(".alert_message>div.content").innerHTML = spec.message || "";

let button_text = `<button>${Constants.dialogs.buttons.ok}</button>`;
if(spec.buttons && spec.buttons.length){
  button_text = spec.buttons.map(label => `<button>${label}</button>`).join("\n");
}
AlertManager.container_node_.querySelector(".alert_buttons>div.content").innerHTML = button_text || "";
```
- **Recomendación:** Usar `textContent` para mensajes de texto plano. Si se requiere HTML en mensajes, implementar una función de sanitización (DOMPurify) o construir nodos DOM programáticamente.

---

### [SEC-ELC-006] XSS via innerHTML en cuerpo de diálogos
- **Archivo:** Console/src/ui/dialog.ts:123
- **Severidad:** Alta
- **Descripción:** El setter `body` del `DialogManager` acepta strings y las inserta directamente como HTML. El setter `status` hace lo mismo. Cualquier dato no confiable pasado como cuerpo de diálogo se interpreta como HTML con acceso a Node.js.
- **Código:**
```typescript
set body(body:string|HTMLElement) { 
  let container = (DialogManager.node_map_.dialog_body as HTMLElement);
  container.innerHTML = "";
  if(body){
    if( typeof body === "string" ) container.innerHTML = body; 
    else container.appendChild(body);
  }
}

set status(text:string){
  let container = (DialogManager.node_map_.dialog_status as HTMLElement);
  container.innerHTML = text||"";
}
```
- **Recomendación:** Separar la API: usar `textContent` para texto plano y requerir `HTMLElement` para contenido rico. Sanitizar cualquier string HTML con DOMPurify antes de insertarla.

---

### [SEC-ELC-007] XSS via innerHTML con descripciones de paquetes R
- **Archivo:** Console/src/shell/language_interface_r.ts:331
- **Severidad:** Alta
- **Descripción:** Las descripciones de paquetes R se insertan directamente como HTML. Estas descripciones provienen del backend R y podrían contener HTML malicioso si un paquete tiene una descripción manipulada o si los datos se corrompen en tránsito por el pipe.
- **Código:**
```typescript
node.package_name.innerText = data.name;
node.package_description.innerHTML = data.description;
```
- **Recomendación:** Usar `textContent` o `innerText` en lugar de `innerHTML`:
```typescript
node.package_description.textContent = data.description;
```

---

### [SEC-ELC-008] XSS via renderizado Markdown sin sanitización
- **Archivo:** Console/src/editor/editor.ts:688-689, 1138-1139
- **Severidad:** Alta
- **Descripción:** El editor renderiza archivos Markdown usando `markdown-it` y el resultado se inserta directamente via `innerHTML`. La librería `markdown-it` por defecto permite HTML inline en Markdown, lo que significa que un archivo `.md` malicioso puede contener `<script>` tags o event handlers que se ejecutarán con privilegios de Node.js.
- **Código:**
```typescript
document.rendered_content_node_.innerHTML = MD.render(document.rendered_content_);
```
- **Recomendación:** Configurar markdown-it para deshabilitar HTML inline:
```typescript
const MD = new MarkdownIt({ html: false }).use(MarkdownItTasks);
```
O sanitizar la salida con DOMPurify antes de insertarla en el DOM.

---

### [SEC-ELC-009] Uso irrestricto del módulo `remote` (deprecated)
- **Archivo:** Console/src/renderer.ts:22, Console/src/editor/editor.ts:31, Console/src/ui/menu_utilities.ts:20, Console/src/shell/terminal_implementation.ts:51, Console/src/shell/multiplexed_terminal.ts:26
- **Severidad:** Alta
- **Descripción:** Múltiples archivos del proceso renderer importan y usan el módulo `remote` de Electron, que fue deprecado en Electron 12 y eliminado en Electron 14 por razones de seguridad. El módulo `remote` permite al renderer invocar cualquier API del proceso principal de forma síncrona, incluyendo `BrowserWindow`, `Menu`, `dialog`, y `getCurrentWindow()`. Esto expone toda la superficie de ataque del proceso principal al renderer.
- **Código:**
```typescript
// renderer.ts
import {clipboard, remote, dialog, shell as electron_shell} from 'electron';
const {Menu, MenuItem} = remote;

// editor.ts
import { remote, clipboard, shell as electron_shell } from 'electron';
const { Menu, MenuItem, dialog } = remote;

// terminal_implementation.ts
import { remote } from 'electron';
// Usado para: remote.dialog.showSaveDialog(), remote.getCurrentWindow()
```
- **Recomendación:** Reemplazar `remote` con comunicación IPC explícita:
1. Definir handlers en el proceso principal via `ipcMain.handle()`
2. Exponer invocadores seguros via `contextBridge` en el preload
3. Llamar desde el renderer via `ipcRenderer.invoke()`

---

### [SEC-ELC-010] electron-reload activo en producción
- **Archivo:** Console/main.js:30
- **Severidad:** Media
- **Descripción:** El módulo `electron-reload` está configurado incondicionalmente (no depende de `dev_flags`). Esto significa que en producción, la aplicación monitorea cambios en el directorio `build/` y recarga automáticamente. Un atacante con acceso de escritura al directorio podría inyectar código que se ejecutaría automáticamente al ser detectado por el watcher.
- **Código:**
```javascript
require('electron-reload')(path.join(__dirname,"build"));

let dev_flags = 0;  // Se parsea después, pero electron-reload ya está activo
```
- **Recomendación:** Condicionar `electron-reload` a modo desarrollo:
```javascript
if (process.env.NODE_ENV === 'development' || dev_flags) {
  require('electron-reload')(path.join(__dirname, "build"));
}
```
O mejor, mover `electron-reload` a `devDependencies` y no incluirlo en el build de producción.

---

### [SEC-ELC-011] shell.openExternal con URIs no validadas
- **Archivo:** Console/src/shell/terminal_implementation.ts:1164, Console/src/editor/editor.ts:262
- **Severidad:** Media
- **Descripción:** `shell.openExternal()` se invoca con URIs provenientes de contenido renderizado (links en terminal, links en editor, links en Markdown) sin validación de protocolo. Un enlace malicioso con protocolo `file://`, `javascript:`, o un esquema personalizado podría ejecutar acciones no deseadas en el sistema operativo.
- **Código:**
```typescript
// terminal_implementation.ts — URIs de links detectados en terminal
(this.xterm_ as any).webLinksInit((event: MouseEvent, uri: string) => {
  shell.openExternal(uri);
});

// editor.ts — cualquier href en contenido renderizado
electron_shell.openExternal(e.srcElement['href']);
```
- **Recomendación:** Validar que la URI use un protocolo permitido antes de abrirla:
```typescript
function safeOpenExternal(uri: string) {
  try {
    const parsed = new URL(uri);
    if (['http:', 'https:'].includes(parsed.protocol)) {
      shell.openExternal(uri);
    }
  } catch (e) {
    console.warn('URI inválida:', uri);
  }
}
```

---

### [SEC-ELC-012] Acceso directo a `fs` desde proceso renderer
- **Archivo:** Console/src/editor/editor.ts:23, Console/src/shell/terminal_implementation.ts:53, Console/src/ui/user_stylesheet.ts:22, Console/src/ui/menu_utilities.ts:25, Console/src/shell/svg_graphics_device.ts:25, Console/src/common/config_manager.ts:28
- **Severidad:** Media
- **Descripción:** Seis archivos del proceso renderer importan directamente el módulo `fs` de Node.js para leer/escribir archivos. Combinado con `nodeIntegration: true` y la ausencia de `contextIsolation`, cualquier vulnerabilidad XSS permite acceso completo al sistema de archivos del usuario. El renderer no debería tener acceso directo a `fs`.
- **Código:**
```typescript
// editor.ts
import * as fs from 'fs';
// Usado para: fs.readFile, fs.writeFile, fs.readdir, fs.existsSync

// terminal_implementation.ts
import * as fs from 'fs';
// Usado para: fs.writeFile (guardar imágenes)

// config_manager.ts
import * as fs from 'fs';
// Usado para: fs.readFile, fs.writeFile (configuración)
```
- **Recomendación:** Mover todas las operaciones de filesystem al proceso principal y exponerlas via IPC con validación de rutas:
```typescript
// main process
ipcMain.handle('fs:readFile', (event, filePath) => {
  // Validar que filePath está dentro de directorios permitidos
  if (!isAllowedPath(filePath)) throw new Error('Acceso denegado');
  return fs.promises.readFile(filePath, 'utf8');
});
```

---

## Análisis de Dependencias npm

| Dependencia | Versión | Estado | Riesgo |
|-------------|---------|--------|--------|
| electron | ^1.8.2 | EOL desde 2018, cientos de CVEs | Crítico |
| typescript | ^2.7.2 | Muy desactualizado (actual: 5.x) | Bajo (dev) |
| @types/node | ^8.9.1 | Desactualizado | Bajo (dev) |
| electron-builder | ^19.56.0 | Desactualizado | Bajo (dev) |
| xterm | ^3.2.0 | Desactualizado (actual: 5.x), posibles XSS | Media |
| markdown-it | ^8.4.0 | Desactualizado (actual: 14.x) | Media |
| monaco-editor | ^0.10.1 | Muy desactualizado (actual: 0.45+) | Media |
| google-protobuf | ^3.5.0 | Desactualizado (actual: 3.21+) | Baja |
| rxjs | ^5.5.6 | EOL (actual: 7.x) | Baja |
| chokidar | ^2.0.1 | Desactualizado (actual: 3.x) | Baja |
| electron-reload | ^1.2.2 | No debería estar en producción | Media |

**Nota:** No se puede ejecutar `npm audit` sin `node_modules` instalado, pero la antigüedad de Electron 1.8.2 (basado en Chromium ~59/Node ~8) implica exposición a CVEs críticos incluyendo:
- CVE-2018-1000136 (Electron nodeIntegration bypass)
- Múltiples CVEs de Chromium V8 (RCE)
- CVEs de Node.js 8.x (buffer overflows, HTTP smuggling)

---

## Hallazgos Positivos

1. **Comunicación IPC via Named Pipes con Protobuf:** La comunicación entre la consola y los procesos backend (ControlR, ControlJulia) usa Protocol Buffers sobre Named Pipes de Windows, lo cual proporciona serialización tipada y evita inyección de comandos en el canal de comunicación.

2. **No se detectó uso de `eval()` o `Function()`:** El código no utiliza evaluación dinámica de JavaScript, lo cual reduce la superficie de ataque para inyección de código.

3. **Carga local de contenido:** La aplicación carga `index.html` desde el filesystem local (`file://` protocol) en lugar de URLs remotas, eliminando ataques man-in-the-middle sobre el contenido principal.

4. **Uso de `textContent`/`innerText` en algunos casos:** El título de alertas (`alert.ts:115`) y nombres de paquetes (`language_interface_r.ts:330`) usan correctamente `textContent`/`innerText`, mostrando que el patrón seguro se conoce pero no se aplica consistentemente.

5. **Arquitectura de procesos separados:** La separación entre la consola Electron y los procesos de lenguaje (ControlR, ControlJulia) limita el impacto de una compromisión del renderer a la sesión de la consola, sin afectar directamente a Excel.

---

## Recomendación General

La consola Electron presenta un perfil de riesgo **Crítico** debido a la combinación de:
- Electron 1.8.2 sin parches de seguridad desde 2018
- `nodeIntegration: true` por defecto (cualquier XSS = RCE)
- Múltiples vectores XSS via `innerHTML`
- Sin Content-Security-Policy

**Opciones de remediación (en orden de preferencia):**

1. **Migrar a WebView2** — El proyecto ya usa WebView2 para visualizaciones. Consolidar la consola REPL en WebView2 eliminaría la dependencia de Electron y sus problemas de seguridad heredados.

2. **Actualizar a Electron ≥28** — Requiere refactorización significativa (eliminar `remote`, implementar `contextBridge`, migrar IPC) pero mantiene la arquitectura actual.

3. **Hardening mínimo** — Si la migración no es viable a corto plazo: agregar CSP, reemplazar `innerHTML` con `textContent`, condicionar `electron-reload` a desarrollo. Esto mitiga los vectores XSS pero no resuelve las vulnerabilidades del runtime.
