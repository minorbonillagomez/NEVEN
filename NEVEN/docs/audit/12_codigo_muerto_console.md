# 12. Detección de Código Muerto — Console (TypeScript/Electron)

## Resumen Ejecutivo

Auditoría de código muerto en el directorio `Console/` del proyecto NEVEN. Se analizaron exports no importados, archivos no alcanzables desde los entry points, dependencias npm sin uso, y assets huérfanos.

## Tabla Resumen

| ID | Título | Severidad | Archivo(s) |
|----|--------|-----------|------------|
| CM-BAJA-001 | Clase `DataCache` exportada pero no importada desde renderer.ts | Baja | src/common/data_cache.ts |
| CM-BAJA-002 | Clase `Pipe2` (management_pipe) no importada desde renderer.ts | Baja | src/io/management_pipe.ts |
| CM-BAJA-003 | Clase `StdIOPipe` no importada desde renderer.ts | Baja | src/io/stdio_pipe.ts |
| CM-BAJA-004 | Clase `Julia07Interface` comentada en renderer.ts | Baja | src/shell/language_interface_julia-0.7.ts |
| CM-BAJA-005 | Exports no utilizados en `pipe.ts` | Baja | src/io/pipe.ts |
| CM-BAJA-006 | Exports no utilizados en `text_formatter.ts` | Baja | src/shell/text_formatter.ts |
| CM-BAJA-007 | Exports no utilizados en `splitter.ts` | Baja | src/ui/splitter.ts |
| CM-BAJA-008 | REPL.ts no alcanzable desde ningún entry point compilado | Baja | REPL.ts |
| CM-BAJA-009 | Archivo `src/json.d.ts` sin referencia | Baja | src/json.d.ts |
| CM-BAJA-010 | Dependencia npm `asar` sin uso en código fuente | Baja | package.json |
| CM-BAJA-011 | Asset `data/themes/test-theme.json` sin referencia | Baja | data/themes/test-theme.json |
| CM-BAJA-012 | Script `script/generate-symbol-table.js` sin referencia | Baja | script/generate-symbol-table.js |
| CM-BAJA-013 | Import `prototype` de `stream` sin uso en renderer.ts | Baja | src/renderer.ts |
| CM-BAJA-014 | Método `InsertJSON` vacío en ConfigManager | Baja | src/common/config_manager.ts |
| CM-BAJA-015 | Método estático `Insert` vacío en UserStylesheet | Baja | src/ui/user_stylesheet.ts |
| CM-BAJA-016 | Clase `ObservedProxy` exportada pero solo usada internamente | Baja | src/common/observed_proxy.ts |

---

## Hallazgos Detallados

### 9.1 — Exports no importados en Console/src/

### [CM-BAJA-001] Clase `DataCache` — export no importado desde entry point principal
- **Archivo(s):** `Console/src/common/data_cache.ts`
- **Severidad:** Baja
- **Descripción:** La clase `DataCache` y su namespace asociado (`CacheStatus`, `CacheResult`, `CacheData`) se exportan pero no se importan desde `renderer.ts`. Sin embargo, sí se usa transitivamente desde `language_interface_r.ts` (que es alcanzable desde renderer.ts).
- **Evidencia:** `renderer.ts` no importa `data_cache.ts` directamente, pero `language_interface_r.ts` sí lo importa: `import { DataCache } from '../common/data_cache'`. Es alcanzable transitivamente.
- **Recomendación:** No es código muerto real. Mantener. Documentar la dependencia transitiva.

### [CM-BAJA-002] Clase `Pipe2` no importada directamente desde renderer.ts
- **Archivo(s):** `Console/src/io/management_pipe.ts`
- **Severidad:** Baja
- **Descripción:** La clase `Pipe2` se exporta pero no se importa desde `renderer.ts`. Se usa transitivamente desde `language_interface_r.ts`, `language_interface_julia.ts` y `language_interface_julia-0.7.ts`.
- **Evidencia:** Búsqueda de imports muestra que solo los archivos de language_interface la importan. Es alcanzable transitivamente.
- **Recomendación:** No es código muerto real. Mantener.

### [CM-BAJA-003] Clase `StdIOPipe` no importada directamente desde renderer.ts
- **Archivo(s):** `Console/src/io/stdio_pipe.ts`
- **Severidad:** Baja
- **Descripción:** La clase `StdIOPipe` se exporta pero no se importa desde `renderer.ts`. Se usa transitivamente desde `language_interface_julia.ts` y `language_interface_julia-0.7.ts`.
- **Evidencia:** Solo los archivos Julia la importan. Es alcanzable transitivamente.
- **Recomendación:** No es código muerto real. Mantener.

### [CM-BAJA-004] Clase `Julia07Interface` comentada en import de renderer.ts
- **Archivo(s):** `Console/src/shell/language_interface_julia-0.7.ts`
- **Severidad:** Baja
- **Descripción:** El archivo `language_interface_julia-0.7.ts` exporta `Julia07Interface`, pero el import en `renderer.ts` está comentado (`//import { Julia07Interface } from './shell/language_interface_julia-0.7'`). El archivo sigue siendo compilado por TypeScript porque es importado transitivamente por el compilador, pero la clase nunca se instancia.
- **Evidencia:** Línea 27 de renderer.ts: `//import { Julia07Interface } from './shell/language_interface_julia-0.7';`. La clase no aparece en `language_interface_types` array.
- **Recomendación:** Eliminar el archivo o documentar si se planea reactivar para Julia 0.7+.

### [CM-BAJA-005] Exports no utilizados en `pipe.ts`
- **Archivo(s):** `Console/src/io/pipe.ts`
- **Severidad:** Baja
- **Descripción:** La interfaz `HistoryCallbackType` se exporta pero no se importa en ningún otro archivo. Se usa solo internamente en `pipe.ts` para tipar el callback.
- **Evidencia:** Búsqueda de `HistoryCallbackType` en todos los archivos .ts muestra que solo se define y usa en `pipe.ts`.
- **Recomendación:** Cambiar a no-exportado (`interface` sin `export`) o mantener si se prevé uso externo.

### [CM-BAJA-006] Exports no utilizados en `text_formatter.ts`
- **Archivo(s):** `Console/src/shell/text_formatter.ts`
- **Severidad:** Baja
- **Descripción:** Las interfaces `Token`, `TokenizedString`, y `TextFormatter`, así como la constante `VTESC` y la función `KeywordsToRegex` se exportan. Solo `RTextFormatter` y `TextFormatter` (como tipo) se usan externamente.
- **Evidencia:** `VTESC` no se importa en ningún otro archivo. `Token` y `TokenizedString` no se importan externamente. `TextFormatter` se importa en `terminal_implementation.ts`.
- **Recomendación:** Remover `export` de `VTESC`, `Token`, `TokenizedString` si no se necesitan externamente.

### [CM-BAJA-007] Exports no utilizados en `splitter.ts`
- **Archivo(s):** `Console/src/ui/splitter.ts`
- **Severidad:** Baja
- **Descripción:** La interfaz `SplitterStatus` se exporta pero no se importa en ningún otro archivo.
- **Evidencia:** Búsqueda de `SplitterStatus` en imports de otros archivos no produce resultados. Solo se usa internamente como tipo del BehaviorSubject.
- **Recomendación:** Remover `export` de `SplitterStatus`.

### [CM-BAJA-013] Import `prototype` de `stream` sin uso en renderer.ts
- **Archivo(s):** `Console/src/renderer.ts`
- **Severidad:** Baja
- **Descripción:** La línea `import { prototype } from 'stream';` importa `prototype` del módulo `stream` de Node.js pero nunca se utiliza en el archivo.
- **Evidencia:** Línea 37 de renderer.ts: `import { prototype } from 'stream';`. No hay ninguna referencia a `prototype` en el resto del archivo.
- **Recomendación:** Eliminar el import no utilizado.

### [CM-BAJA-014] Método `InsertJSON` vacío en ConfigManager
- **Archivo(s):** `Console/src/common/config_manager.ts`
- **Severidad:** Baja
- **Descripción:** El método `InsertJSON(path:string, json:string)` de la clase `ConfigManager` tiene un cuerpo vacío (solo declara variables locales sin lógica). Nunca se invoca desde ningún otro archivo.
- **Evidencia:** El método solo contiene `let source = this.raw_config_file_; let components = path.split(".");` sin implementación real. No se encuentra ninguna llamada a `InsertJSON` en el codebase.
- **Recomendación:** Eliminar el método stub o implementarlo si es necesario.

### [CM-BAJA-015] Método estático `Insert` vacío en UserStylesheet
- **Archivo(s):** `Console/src/ui/user_stylesheet.ts`
- **Severidad:** Baja
- **Descripción:** El método estático `Insert()` de la clase `UserStylesheet` tiene un cuerpo completamente vacío y no se invoca desde ningún lugar.
- **Evidencia:** El método está definido como `static Insert(){}` sin implementación. No se encuentra ninguna llamada a `UserStylesheet.Insert()` en el codebase.
- **Recomendación:** Eliminar el método vacío.

### [CM-BAJA-016] Clase `ObservedProxy` — export innecesario
- **Archivo(s):** `Console/src/common/observed_proxy.ts`
- **Severidad:** Baja
- **Descripción:** La clase `ObservedProxy` se exporta pero solo se importa desde `properties.ts` (mismo directorio). El export es técnicamente innecesario si solo se usa internamente en el módulo `common/`.
- **Evidencia:** Solo `properties.ts` importa `ObservedProxy`. No hay uso externo fuera de `src/common/`.
- **Recomendación:** Mantener el export (es necesario para el sistema de módulos TypeScript entre archivos). No es código muerto.

---

### 9.2 — Archivos TypeScript no alcanzables desde entry points

### [CM-BAJA-008] REPL.ts no alcanzable desde ningún entry point compilado
- **Archivo(s):** `Console/REPL.ts`
- **Severidad:** Baja
- **Descripción:** El archivo `REPL.ts` en la raíz de Console/ importa `'./protobuf_client'` que no existe en el repositorio. No está incluido en `tsconfig.json` (que solo lista `src/renderer.ts`). No es referenciado por `main.js` ni por `index.html`. El archivo `repl.html` es un archivo HTML independiente con JavaScript inline que no importa REPL.ts.
- **Evidencia:** 
  - `tsconfig.json` → `"files": ["src/renderer.ts"]` — REPL.ts no está incluido.
  - `import { MessageClient } from './protobuf_client'` — archivo `protobuf_client.ts` no existe.
  - `repl.html` usa JavaScript inline, no importa REPL.ts.
  - `main.js` carga `index.html`, no `repl.html`.
- **Recomendación:** Este archivo parece ser un prototipo incompleto para la nueva consola REPL WebView2. Documentar su estado o eliminarlo si `repl.html` lo reemplaza.

### [CM-BAJA-009] Archivo `src/json.d.ts` sin referencia
- **Archivo(s):** `Console/src/json.d.ts`
- **Severidad:** Baja
- **Descripción:** El archivo de declaración de tipos `json.d.ts` no es referenciado explícitamente por ningún archivo ni por `tsconfig.json`. Puede ser recogido implícitamente por el compilador TypeScript si está en el directorio de compilación, pero su utilidad es cuestionable dado que `tsconfig.json` usa `"files"` explícito.
- **Evidencia:** No aparece en `tsconfig.json` files array. No hay `/// <reference>` a este archivo. Con `"files"` explícito en tsconfig, los archivos `.d.ts` no listados no se incluyen automáticamente.
- **Recomendación:** Verificar si el compilador TypeScript lo necesita para resolver tipos de módulos JSON. Si no, eliminar.

---

### 9.3 — Dependencias npm sin uso

### [CM-BAJA-010] Dependencia `asar` sin uso en código fuente
- **Archivo(s):** `Console/package.json` (devDependencies)
- **Severidad:** Baja
- **Descripción:** La dependencia `asar` (v0.14.1) está listada en `devDependencies` pero no se importa ni requiere en ningún archivo TypeScript o JavaScript del proyecto. No aparece en ningún script de `package.json`.
- **Evidencia:** 
  - `grep -r "asar" Console/src/` → sin resultados
  - `grep -r "require.*asar" Console/` → sin resultados en archivos .ts/.js
  - No aparece en scripts de package.json
  - Nota: `electron-builder` puede usarlo internamente para empaquetar, pero no es una dependencia directa del código.
- **Recomendación:** Verificar si `electron-builder` lo necesita como peer dependency. Si no, eliminar de devDependencies.

**Nota sobre otras dependencias:** Las siguientes dependencias fueron verificadas y están en uso:
| Dependencia | Uso |
|-------------|-----|
| `@types/node` | Tipos TypeScript para Node.js |
| `electron` | Runtime de la aplicación |
| `electron-builder` | Script `package` en package.json |
| `less-watch-compiler` | Scripts `build` y `watch` |
| `typescript` | Compilación TypeScript |
| `@types/text-encoding` | Tipos para TextDecoder (terminal_implementation.ts) |
| `chokidar` | Importado en file_watcher.ts |
| `electron-reload` | Requerido en main.js |
| `electron-window-state` | Requerido en main.js |
| `google-protobuf` | Usado via generated/variable_pb.js |
| `js-base64` | Importado en utilities.ts, svg_graphics_device.ts, terminal_implementation.ts |
| `less` | Importado en user_stylesheet.ts |
| `markdown-it` | Importado en editor.ts |
| `markdown-it-task-lists` | Importado en editor.ts |
| `monaco-editor` | Usado en editor.ts, index.html |
| `rxjs` | Importado en múltiples archivos |
| `xterm` | Importado en terminal_implementation.ts, custom-fit.ts |

---

### 9.4 — Assets huérfanos en Console/

### [CM-BAJA-011] Asset `data/themes/test-theme.json` sin referencia
- **Archivo(s):** `Console/data/themes/test-theme.json`
- **Severidad:** Baja
- **Descripción:** El archivo `test-theme.json` en el directorio de temas no es referenciado por ningún archivo TypeScript, JavaScript, HTML o LESS del proyecto. El código de carga de temas en `editor.ts` está comentado (función `LoadThemes` completa está en un bloque de comentario).
- **Evidencia:** 
  - Búsqueda de "test-theme" en todo Console/ → sin resultados.
  - La función `LoadThemes()` en editor.ts está completamente comentada.
  - El directorio `data/themes/` no es referenciado dinámicamente en ningún código activo.
- **Recomendación:** Eliminar el archivo o reactivar la funcionalidad de temas si se planea usar.

### [CM-BAJA-012] Script `script/generate-symbol-table.js` sin referencia
- **Archivo(s):** `Console/script/generate-symbol-table.js`
- **Severidad:** Baja
- **Descripción:** El script de generación de tabla de símbolos no es referenciado por ningún script en `package.json` ni por ningún otro archivo del proyecto. Es un script utilitario que probablemente se ejecuta manualmente para regenerar `data/symbol_table.json`.
- **Evidencia:** 
  - No aparece en scripts de package.json.
  - Búsqueda de "generate-symbol-table" en todo Console/ → sin resultados.
  - `data/symbol_table.json` sí se usa (en terminal_implementation.ts).
- **Recomendación:** Documentar el script como herramienta de mantenimiento o agregar un script npm para su ejecución. No es código muerto per se, sino una herramienta de build no documentada.

**Nota sobre otros assets verificados:** Los siguientes assets están en uso:
| Asset | Referencia |
|-------|-----------|
| `ext/icomoon.css` | index.html `<link>` |
| `ext/icomoon.woff` | Referenciado por icomoon.css |
| `ext/cogs/cogs.css` | index.html `<link>` |
| `ext/cogs/cogs.woff` | Referenciado por cogs.css |
| `data/constants.json` | Múltiples archivos .ts via `require()` |
| `data/default_config.json` | config_manager.ts |
| `data/symbol_table.json` | terminal_implementation.ts |
| `data/menus/application_menu.json` | renderer.ts, language_interface_r.ts |
| `data/menus/editor_tab_context_menu.json` | editor.ts |
| `data/menus/terminal_context_menu.json` | multiplexed_terminal.ts |
| `data/schemas/config.schema.json` | config_manager.ts |
| `data/schemas/schema.schema.json` | editor.ts |
| `generated/variable_pb.js` | pipe.ts, management_pipe.ts, message_utilities.ts, graphics devices |
| `rj2xcl.ico` | package.json build config |
| `style/*.less` | Todos importados por style.less o entre sí |

---

## Resumen de Impacto

| Categoría | Hallazgos | Código muerto real |
|-----------|-----------|-------------------|
| 9.1 Exports no importados | 8 | 3 (CM-BAJA-005, 006, 007 — exports innecesarios) |
| 9.2 Archivos no alcanzables | 2 | 1 (CM-BAJA-008 — REPL.ts con import roto) |
| 9.3 Dependencias npm sin uso | 1 | 1 (CM-BAJA-010 — asar) |
| 9.4 Assets huérfanos | 2 | 1 (CM-BAJA-011 — test-theme.json) |
| Código muerto inline | 3 | 3 (CM-BAJA-013, 014, 015) |
| **Total** | **16** | **9** |

## Notas Adicionales

1. **tsconfig.json usa `"files"` explícito**: Solo `src/renderer.ts` está listado. El compilador TypeScript resuelve transitivamente todos los imports desde ese punto de entrada. Archivos no importados transitivamente (como REPL.ts) no se compilan.

2. **REPL.ts vs repl.html**: Existe una dualidad entre el archivo TypeScript `REPL.ts` (que importa un módulo inexistente `protobuf_client`) y el archivo `repl.html` (que contiene toda su lógica en JavaScript inline). Parece que `repl.html` es la implementación activa para WebView2 y `REPL.ts` es un prototipo abandonado.

3. **Código comentado significativo**: 
   - `LoadThemes()` en editor.ts (función completa comentada)
   - Import de `Julia07Interface` en renderer.ts
   - Función `Pause` al final de renderer.ts (en bloque de comentario)
   
4. **Severidad general Baja**: Todo el código muerto encontrado es de bajo impacto. No afecta funcionalidad ni seguridad. La limpieza es recomendable para mantenibilidad.
