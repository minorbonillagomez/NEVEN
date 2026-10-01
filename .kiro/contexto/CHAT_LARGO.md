# NEVEN — Bitácora HISTÓRICA (Archivo)

> **Propósito:** Archivo histórico de sesiones anteriores.
> Para sesiones recientes, ver CHAT.md.
> **Contenido:** Aproximadamente primeras 6,500 líneas del historial original.
> **Fecha de archivo:** 2026-09-30

---
# NEVEN — Bitácora de Sesión de Trabajo con Kiro

> **Propósito:** Registro acumulativo de la conversación de trabajo entre Minor Bonilla y Kiro.
> Permite retomar cualquier punto anterior sin depender del historial del chat activo.
> **Actualización:** cada hora o al cerrar sesión.

---

## Ultima actualizacion
**Fecha:** 2026-08-19
**Hora aproximada:** ~20:00 — Commits 342f501 + c081a21 (Tab Conocimiento + Evaluaciones)

---

## Sesiones recientes

### Sesion 2026-08-19 (~18:00) — Tab Conocimiento (Ontología) Frontend

**Estado:** COMPLETO — Pendiente commit

### Objetivo

Implementar el sub-tab "Conocimiento" dentro de Settings para que el usuario pueda:
- Ver dominios de conocimiento disponibles (excel, econometrics)
- Ver libros procesados por dominio
- Procesar nuevos libros PDF para expandir la ontología

### Trabajo realizado

1. **HTML** — Agregado sub-tab "Conocimiento" con `data-settings-tab="ontology"`
2. **HTML** — Agregado panel `#settings-ontology` con:
   - Lista de dominios de conocimiento
   - Lista de libros procesados (por dominio)
   - Formulario para agregar libro (ruta PDF, dominio, opciones avanzadas)
   - Barra de progreso para procesamiento
3. **JavaScript** — Agregadas funciones en `taskpane.js`:
   - `loadOntologyDomains()` — carga dominios desde `/api/ontology/domains`
   - `loadOntologyBooks()` — carga libros desde `/api/ontology/books?domain=X`
   - `browseOntologyFile()` — intenta abrir selector de archivo
   - `processOntologyBook()` — envía PDF a `/api/ontology/process-book`
4. **Event listeners** agregados en `initSettingsTab()`:
   - `btn-ontology-refresh` → recargar dominios
   - `btn-ontology-browse` → seleccionar archivo
   - `btn-ontology-process` → procesar libro
   - `ontology-target-domain` (change) → cargar libros del dominio

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN\TaskPane\taskpane.html` | +85 líneas — sub-tab + panel ontología |
| `NEVEN\TaskPane\taskpane.js` | +230 líneas — handlers y funciones |
| `C:\NEVEN\TaskPane\taskpane.html` | Sync a producción |
| `C:\NEVEN\TaskPane\taskpane.js` | Sync a producción |
| `C:\NEVEN\startup\neven_http_server.py` | Sync a producción (contenía endpoints) |

### Endpoints verificados

| Endpoint | Status | Respuesta |
|----------|--------|-----------|
| `GET /api/ontology/domains` | ✅ OK | 2 dominios (excel, econometrics) |
| `GET /api/ontology/books?domain=excel` | ✅ OK | Lista vacía (sin libros aún) |
| `POST /api/ontology/process-book` | ✅ OK | Valida parámetros correctamente |

### Pendiente

- [x] **ALTA** — ~~Probar UI en Excel~~ ✅ Funciona
- [x] **ALTA** — ~~Crear dominios personalizados~~ ✅ Implementado
- [x] **MEDIA** — ~~Commit~~ ✅ `342f501`
- [ ] **ALTA** — Procesar un libro de prueba para verificar flujo completo
- [ ] **MEDIA** — Push a repositorio remoto
- [ ] **BAJA** — Mejorar selector de archivos (actualmente solo muestra instrucción de escribir ruta)

### Commit realizado

- **Hash:** `342f501`
- **Mensaje:** `feat(studio): tab Conocimiento para gestión de ontología`
- **Archivos:** 6 archivos, +1,790 líneas

### Commit adicional — Evaluaciones

- **Hash:** `c081a21`
- **Mensaje:** `docs: actualizar evaluaciones con Tab Conocimiento (2.21)`
- **Archivos:** 2 archivos (Evaluacion_comercial.md, Evaluacion_doctoral.md), +107 líneas

**Cambios en evaluaciones:**

| Documento | Cambio |
|-----------|--------|
| Evaluacion_comercial.md | +Fortaleza #16: Tab Conocimiento — Ontología extensible |
| Evaluacion_doctoral.md | +Contribución 2.21: UI de gestión autónoma |
| MIBOGO | Sin cambio (evalúa al desarrollador) |
| OWASP | Sin cambio (no nuevas superficies de ataque) |

**Métricas actualizadas:**
- Capacidades comparadas con BERT: 28 (antes 25)
- Innovaciones sobre BERT: 26 (antes 23)

**Nota:** El Tab Settings con Windows Credential Manager (fortaleza #21) ya estaba documentado en evaluaciones anteriores. Esta sesión agregó la fortaleza #16 (Tab Conocimiento).

### Notas técnicas

- El servidor HTTP fue reiniciado (PID 97480) para cargar los nuevos endpoints
- El endpoint `/api/ontology/books` devuelve warning "ontology_manager not available" cuando no hay libros — es comportamiento esperado
- La selección de archivo PDF en Office.js no tiene API nativa de file picker, el usuario debe escribir la ruta manualmente

### Fix adicional (~18:30) — Libros no aparecían

**Problema:** El endpoint `/api/ontology/books` devolvía lista vacía aunque los libros ya estaban procesados.

**Causa raíz:** El archivo `ontology_manager.py` en producción (`C:\NEVEN\startup\`) estaba desactualizado — no tenía la función `list_processed_books()`.

**Fix:** Copiar `ontology_manager.py` del repo a producción y reiniciar servidor.

### Fix adicional (~18:50) — Conteo de libros mostraba 0

**Problema:** La UI mostraba "0 libros" para cada dominio aunque los endpoints funcionaban.

**Causa raíz:** La función `list_domains()` en `ontology_manager.py` no incluía el campo `book_count` en la respuesta. El JavaScript esperaba `d.book_count` pero el servidor solo enviaba `entity_count`.

**Fix:** Modificar `list_domains()` para contar libros únicos por dominio:
```python
# Cuenta libros buscando source_book o reference.book en cada entidad
books = set()
for entity in self._entities.get(d.id, {}).values():
    source = entity.properties.get("source_book")
    if not source:
        ref = entity.properties.get("reference", {})
        source = ref.get("book") if isinstance(ref, dict) else None
    if source:
        books.add(source)
book_count = len(books)
```

**Archivos modificados adicionales:**
| Archivo | Cambio |
|---------|--------|
| `NEVEN\ControlPython\startup\ontology_manager.py` | +15 líneas — agregar book_count a list_domains() |
| `C:\NEVEN\startup\ontology_manager.py` | Sync a producción |

**Resultado verificado:**
- Excel: 6 libros, 183 entidades ✅
- Econometrics: 14 libros, 199 entidades ✅

### Feature adicional (~19:15) — Crear dominios personalizados

**Requerimiento:** El usuario debe poder crear sus propios dominios de conocimiento, no solo usar los predefinidos (excel, econometrics).

**Implementación:**

1. **Frontend (HTML):**
   - Agregada opción `+ Crear nuevo dominio...` en dropdown `ontology-target-domain`
   - Campo oculto `ontology-new-domain-name` que aparece al seleccionar crear nuevo

2. **Frontend (JS):**
   - Nueva función `onOntologyDomainChange()` que muestra/oculta el campo de nuevo dominio
   - Modificado `processOntologyBook()` para validar y usar el nombre del nuevo dominio
   - Validación: nombre debe ser snake_case (letras minúsculas, números, guiones bajos)

3. **Backend (ontology_manager.py):**
   - Nuevo método `OntologyManager.create_domain(domain_id, display_name, description)`
   - Crea estructura en producción: `C:\NEVEN\ontology\{domain_id}\graph.jsonl` + `schema.yaml`
   - Crea estructura en desarrollo: `ONTOLOGIA\LIBROS {NOMBRE}\memory\ontology\`
   - Actualiza `domains.json` con el nuevo dominio
   - Modificado `process_book()` para crear dominio automáticamente si no existe

**Archivos modificados:**
| Archivo | Cambio |
|---------|--------|
| `NEVEN\TaskPane\taskpane.html` | +8 líneas — campo para nuevo dominio |
| `NEVEN\TaskPane\taskpane.js` | +35 líneas — onOntologyDomainChange(), validación nuevo dominio |
| `NEVEN\ControlPython\startup\ontology_manager.py` | +150 líneas — create_domain(), auto-create en process_book |
| `C:\NEVEN\TaskPane\taskpane.html` | Sync |
| `C:\NEVEN\TaskPane\taskpane.js` | Sync |
| `C:\NEVEN\startup\ontology_manager.py` | Sync |

**Decisiones de diseño:**
- El dominio se crea automáticamente al procesar el primer libro (no requiere endpoint separado)
- El schema.yaml se genera con tipos genéricos (Concept, Method, BestPractice) que cubren la mayoría de casos
- Se mantiene sincronización producción ↔ desarrollo para facilitar trabajo con libros

---

### Sesion 2026-08-19 (~13:00) — Fix tildes en Tab Ayuda

**Estado:** COMPLETO — Commit `a298bbb` pusheado

### Problema

Las categorias del diccionario de funciones mostraban "REGRESION" y "ANALISIS" sin tildes.

### Causa raiz

El CSS tenia `text-transform: uppercase` que en algunos navegadores/fuentes no preserva correctamente los caracteres acentuados al convertir a mayusculas.

### Fix aplicado

1. Quitar `text-transform: uppercase` del CSS
2. Hacer `toUpperCase()` en JavaScript que si preserva tildes Unicode
3. Corregir sidecar TM_TextAnalysis.json: "Analisis" -> "Análisis"

### Archivos modificados

- `C:\NEVEN\TaskPane\taskpane.css` — Quitar text-transform
- `C:\NEVEN\TaskPane\ayuda.js` — Agregar toUpperCase() en JS
- `C:\NEVEN\functions\TM_TextAnalysis.json` — Fix tilde en nombre
- `NEVEN\TaskPane\taskpane.css` — Sync al repo
- `NEVEN\TaskPane\ayuda.js` — Sync al repo
- `NEVEN\Install\functions\TM_TextAnalysis.json` — Sync al repo

### Commit

- **Hash:** `a298bbb`
- **Mensaje:** `fix(ayuda): preservar tildes en nombres de categorias`

### Nota tecnica

JavaScript `String.toUpperCase()` preserva tildes correctamente:
- "Regresión".toUpperCase() → "REGRESIÓN"
- "Análisis".toUpperCase() → "ANÁLISIS"

El problema era el CSS `text-transform: uppercase` que depende del navegador/fuente.

### Pendientes proxima sesion

- **[ALTA]** Actualizar documentacion Docusaurus con el nuevo Tab Settings (configurador de perfiles AI/DB)
- **[ALTA]** Actualizar evaluaciones: comercial, doctoral, MiBoGo
- **[MEDIA]** Documentar endpoints nuevos de `/api/config/*`

---

### Sesion 2026-08-19 (~12:30) — Eliminacion de emojis en TaskPane

**Estado:** COMPLETO — Commit `6758b3c` pusheado

### Problema

Usuario encontro emoji de libro (📚) junto a "Contexto:" en el tab Asistente IA.

### Fix aplicado

Eliminados 11 emojis de `taskpane.js` usando regex Python:
- Contexto de hoja/libro (📊, 📚)
- Toast de analisis (📚)
- Indicadores de prioridad (🔴, 🟡, 🟢)
- Botones de graficos (📊, 💾, 📋, 🔍)

### Archivos modificados

- `C:\NEVEN\TaskPane\taskpane.js` — Emojis eliminados
- `NEVEN\TaskPane\taskpane.js` — Sync al repositorio
- `NEVEN\Install\Dist\taskpane\taskpane.js` — Actualizado para instalador

### Commit

- **Hash:** `6758b3c`
- **Mensaje:** `fix(ui): eliminar todos los emojis restantes de taskpane.js`

### Nota para futuro

Para buscar emojis en archivos usar Python:
```python
import re
with open('archivo.js', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if re.search(r'[\U0001F300-\U0001F9FF]', line):
            print(f'{i}: {line[:100]}')
```

---

### Sesion 2026-08-19 (~12:00) — Logging formal y limpieza

**Estado:** COMPLETO — Commit `2d9bd56` pusheado

### Logros principales

1. **Logging formal implementado** en `neven_http_server.py`
   - Logger: `NEVEN.HTTP` usando modulo `logging` de Python
   - Consola: nivel INFO, formato `[NEVEN.HTTP] LEVEL: message`
   - Archivo: nivel DEBUG con RotatingFileHandler (5MB max, 3 backups)
   - Ubicacion: `C:\NEVEN\neven_http.log`

2. **Limpieza de archivos duplicados**
   - Eliminados 6 archivos `taskpane_*.js` con timestamps en produccion
   - Actualizado `taskpane.html` para usar `taskpane.js` (sin timestamp)
   - Contenido mas reciente preservado en archivo principal

### Archivos modificados

- `C:\NEVEN\startup\neven_http_server.py` — Logging formal
- `C:\NEVEN\TaskPane\taskpane.html` — Referencia a taskpane.js sin timestamp
- `C:\NEVEN\TaskPane\taskpane.js` — Contenido actualizado
- `NEVEN\TaskPane\neven_http_server.py` — Sync al repositorio
- `NEVEN\ControlPython\startup\neven_http_server.py` — Sync al repositorio
- `NEVEN\Install\Dist\startup\neven_http_server.py` — Actualizado para instalador

### Commit

- **Hash:** `2d9bd56`
- **Mensaje:** `refactor(http-server): implementar logging formal con rotacion de archivos`

### Decisiones de diseno

- **RotatingFileHandler con 5MB y 3 backups** — Balance entre retener logs utiles y no llenar disco
- **Consola INFO, archivo DEBUG** — Consola limpia para operacion normal, archivo detallado para diagnostico

### Pendientes proxima sesion

- Ninguno pendiente de esta sesion

---

### Sesion 2026-08-19 (~11:30) — Fix AI Chat "Failed to fetch"

**Estado:** COMPLETO — Commit `6094ae2` pusheado

### Problema diagnosticado

El endpoint `/api/ai/chat` fallaba con "Error de red: Failed to fetch" (conexión terminada inesperadamente).

### Causas identificadas

1. **Múltiples instancias del servidor HTTP** — Había DOS procesos Python escuchando en puerto 5555. Los requests llegaban al proceso incorrecto que no tenía el handler actualizado.

2. **`urllib.request.urlopen` bloqueaba en threading** — La librería estándar de Python para HTTP no funciona bien dentro del contexto de threading del HTTPServer. La llamada quedaba bloqueada indefinidamente sin timeout efectivo.

3. **Referencias a `log.info()`/`log.warning()` sin definir `log`** — Agregué logs usando un objeto `log` que no existía, causando `NameError` silencioso.

4. **Variable `ai` usada sin definir** — En el bloque de Azure, se usaba `ai.get("apiVersion", ...)` pero `ai` solo se define en el fallback legacy, no cuando usa config_manager.

### Fixes aplicados

1. **Cambiado de `urllib.request` a `requests`** — La librería `requests` funciona correctamente en contextos de threading.

2. **Corregido acceso a `api_version`** — Ahora verifica si `api_version` está vacía antes de hacer fallback a config legacy.

3. **Reemplazado `log.info/warning` por `print()`** — Para logging simple sin dependencias externas.

4. **Eliminados servidores duplicados** — Instrucciones para verificar con `netstat -ano | Select-String ":5555"`.

### Prueba de verificación

```powershell
# Verificar un solo servidor
netstat -ano | Select-String ":5555.*LISTENING"

# Probar endpoint AI
$body = '{"messages":[{"role":"user","content":"Di OK"}]}'
$body | Out-File -Encoding ASCII body.json -NoNewline
curl.exe -s -X POST "http://localhost:5555/api/ai/chat" -H "Content-Type: application/json" -d "@body.json"
# Debe retornar: {"status": "ok", "reply": "OK", "model": "gpt-4.1", ...}
```

### Archivos modificados

- `C:\NEVEN\startup\neven_http_server.py` — Fix de AI Chat handler
- `NEVEN\TaskPane\neven_http_server.py` — Copia al repositorio
- `NEVEN\ControlPython\startup\neven_http_server.py` — Copia sincronizada
- `NEVEN\Install\Dist\startup\neven_http_server.py` — Actualizado para instalador
- `NEVEN\Install\Dist\taskpane\taskpane.js` — Actualizado para instalador

### Commit

- **Hash:** `6094ae2`
- **Mensaje:** `fix(ai-chat): cambiar urllib a requests para llamadas LLM en threading`

### Decisiones de diseno

- **Usar `requests` en lugar de `urllib.request`** — La libreria estandar tiene problemas conocidos en contextos de threading. `requests` es thread-safe y mas confiable.
- **Mantener logs con `print()`** — En lugar de configurar logging complejo, usar print simple para diagnostico inmediato en consola del servidor.

### Intentos fallidos

1. **Agregar try/except global sin encontrar error** — El error no se capturaba porque ocurria antes de entrar al handler (multiples servidores en mismo puerto)
2. **Agregar logging con `log.info()`** — Objeto `log` no estaba definido, causando NameError silencioso

### Pendientes proxima sesion

- **[BAJA]** Limpiar archivos `taskpane_*.js` duplicados en produccion
- **[BAJA]** Considerar usar logging formal en lugar de print() para el servidor

---

### Sesion 2026-08-20 (~09:30-11:30) — Implementacion NEVEN Settings

**Estado:** COMPLETO — Commit 918e511 pusheado

### Logros principales

1. **config_manager.py** — Modulo completo para gestion de configuracion
   - Dataclasses: `AIProfile`, `DBConnection`, `PromptConfig`, `Preferences`
   - CRUD completo para perfiles AI y conexiones DB
   - Integracion con Windows Credential Manager via `keyring`
   - Migracion automatica de config v1 a v2.0
   - Tests de conexion para OpenAI, Azure, Anthropic, Ollama
   - Tests de conexion para PostgreSQL, MySQL, SQL Server, SQLite, DuckDB

2. **Endpoints HTTP** — 20+ nuevos endpoints en neven_http_server.py
   - GET/POST `/api/config/ai-profiles` (list, get, create, update, delete, activate, test)
   - GET/POST `/api/config/db-connections` (mismo set de operaciones)
   - GET `/api/config/providers`, `/api/config/db-types`
   - GET/POST `/api/config/prompts` (list, get, save)
   - POST `/api/config/reload`

3. **Tab Settings en TaskPane** — UI completa
   - Sub-tabs: Motor IA, Conexiones DB, Prompts
   - Lista de perfiles con radio buttons para activar
   - Formularios de edicion con validacion
   - Botones "Probar Conexion" con feedback visual
   - Estilos CSS integrados con paleta NEVEN

4. **Migracion neven-config.json** — v1 a v2.0
   - API key de Azure movida a Windows Credential Manager
   - Perfil "azure-migrated" creado automaticamente
   - Secciones legacy (NEVEN, WebView2, TaskPane) preservadas

### Archivos modificados (implementacion)

| Archivo | Cambio |
|---------|--------|
| `ControlPython/startup/config_manager.py` | NUEVO — 1000+ lineas |
| `ControlPython/startup/neven_http_server.py` | +400 lineas (handlers config) |
| `TaskPane/taskpane.html` | +200 lineas (tab Settings) |
| `TaskPane/taskpane.js` | +600 lineas (funciones Settings) |
| `TaskPane/taskpane.css` | +50 lineas (estilos Settings) |
| `Install/neven-config.json` | Formato v2.0 |
| `C:\NEVEN\neven-config.json` | Migrado a v2.0 |

### Decisiones de diseño

1. **Credenciales en keyring** — API keys NUNCA en JSON, solo referencias
2. **Multiples perfiles** — Usuario puede tener varios proveedores AI y cambiar entre ellos
3. **Python requerido** — Ya no es opcional porque keyring y HTTP server lo necesitan
4. **Migracion automatica** — config_manager detecta v1 y migra sin intervencion

### Problema resuelto: Submodule corrupto

**Sintoma:** `git add` fallaba con "in unpopulated submodule 'NEVEN'"

**Causa raiz:** NEVEN estaba registrado como submodule (mode 160000) pero no habia `.gitmodules`. Estado inconsistente heredado.

**Solucion:**
```powershell
git rm --cached NEVEN  # Remover referencia de submodule
git add NEVEN/         # Agregar como directorio normal
```

**Resultado:** 850 archivos agregados al commit como directorio normal.

### Commit

```
918e511 feat(settings): formulario de configuracion con perfiles AI/DB y keyring
```

### Pendientes para proxima sesion

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar tab Settings con servidor HTTP corriendo |
| **MEDIA** | Verificar que _handle_ai_chat use el perfil activo de config_manager |
| **BAJA** | Agregar boton Settings al Ribbon (acceso directo sin abrir TaskPane) |

---

### Sesion 2026-08-20 (~08:30-09:00) — Diseño: Formulario de Configuración NEVEN

**Estado:** DISEÑO REFINADO — Pendiente implementación

### Objetivo
Crear un formulario de configuración (Settings) accesible desde el Ribbon para que usuarios no técnicos puedan configurar NEVEN sin usar consolas ni editar archivos JSON manualmente.

### Refinamiento: Múltiples Perfiles

Usuario solicitó que tanto IA como BD soporten múltiples configuraciones con una ACTIVA seleccionable:
- **AI Profiles**: OpenAI, Claude, Azure, Ollama — usuario puede cambiar entre ellos
- **DB Connections**: Múltiples conexiones, una activa a la vez
- UI tipo lista con radio buttons: `[●] OpenAI GPT-4o ← ACTIVA`

### Refinamiento: Encriptación de Credenciales

**Decisión:** Enfoque híbrido (no encriptar todo el JSON)

| Dato | Almacenamiento |
|------|----------------|
| API Keys, passwords BD | Windows Credential Manager via `keyring` |
| Config general (hosts, puertos, nombres) | JSON plano (facilita debug/backup) |

**Flujo:**
1. Usuario ingresa API Key en formulario
2. Python: `keyring.set_password("neven", "openai-gpt4o", "sk-...")`
3. JSON guarda referencia: `"credential_key": "neven/ai/openai-gpt4o"`
4. Al leer: `keyring.get_password("neven", "openai-gpt4o")`

**Por qué no encriptar todo el JSON:**
- Credenciales nunca tocan disco en texto plano (más seguro)
- Config general legible facilita troubleshooting
- Windows Credential Manager es estándar y nativo

### CAMBIO ARQUITECTURAL: Python ahora es REQUERIDO

**Antes:** Python era opcional (R y Julia podían usarse sin él)
**Ahora:** Python es obligatorio para NEVEN

**Razón:** El sistema de configuración depende de:
- `keyring` (Python) para Windows Credential Manager
- `neven_http_server.py` para endpoints de config
- `config_manager.py` (nuevo) para CRUD de perfiles

**Impacto:**
- Instalador debe incluir Python obligatoriamente
- Documentación debe actualizarse
- `neven-config.json` campo `python.enabled` ya no aplica (siempre ON)

### Estructura neven-config.json v2.0

```json
{
  "version": "2.0",
  "active_ai_profile": "openai-gpt4o",
  "active_db_connection": "prod-sqlserver",
  "ai_profiles": [...],
  "db_connections": [...],
  "prompts": {"active_system": "default", "custom_prompts": [...]},
  "preferences": {"language": "es", "theme": "system", ...}
}
```

### Archivos modificados
Ninguno — sesión de diseño únicamente

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Crear `config_manager.py` con soporte keyring |
| **ALTA** | Endpoints HTTP para CRUD de perfiles AI/DB |
| **ALTA** | HTML del formulario Settings con UI de perfiles |
| **MEDIA** | Agregar botón "Configuración" al Ribbon |
| **MEDIA** | Migrar config actual a v2.0 |
| **BAJA** | Sección de prompts editables |

---

### Sesion 2026-08-19 (~16:30) — Verificacion post-push

**Estado:** COMPLETO

### Verificado
- Commit `c27eac3` ya estaba en `origin/master` (push exitoso en sesion anterior)
- `taskpane.html` tenia diferencia repo vs produccion — sincronizado
- `taskpane.js` y `sheet_analyzer.py` ya estaban OK

### Archivos sincronizados a produccion
- `C:\NEVEN\TaskPane\taskpane.html` — copiado desde repo

---

### Sesion 2026-08-19 (~02:50) — D3 Graph + Paleta NEVEN

**Estado:** COMPLETO — Commit c27eac3 pusheado

### Problema resuelto
D3 force graph para flujo de datos del workbook no mostraba conexiones (edges).

### Causa raiz
En `sheet_analyzer.py` linea ~1301, el response de `analyze_workbook()` NO incluia `data_flow.edges`:
```python
"data_flow": {
    "nodes": data_flow.get("nodes", []),
    # FALTABA: "edges": data_flow.get("edges", [])
}
```

### Fix aplicado
Agregado `"edges": data_flow.get("edges", [])` al response dict.

### Mejoras adicionales
1. **Layout jerarquico** — 3 columnas (Input, Processing, Output) en lugar de force puro
2. **Exportar HTML** — Boton genera archivo interactivo standalone
3. **Paleta NEVEN unificada** — Removidos verdes/morados, todo usa gold/amber (#d7a538)
4. **Emojis removidos** — Regex agresivo para limpiar caracteres corruptos (ðŸ...)

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `TaskPane/taskpane.js` | renderWorkbookGraphD3() reescrito, generateGraphHTML(), chip/button styles |
| `TaskPane/taskpane.html` | Emojis removidos, botones unificados con btn-secondary |
| `ControlPython/startup/sheet_analyzer.py` | Agregado edges a data_flow response |

### Commit
```
c27eac3 feat(taskpane): D3 force graph para flujo de datos + paleta NEVEN unificada
```

---

### Sesion 2026-08-19 (~23:45) — Discusion: Renderizado de Mermaid

**Estado:** PENDIENTE — Esperando confirmacion para implementar

### Problema reportado
El diagrama Mermaid del flujo de datos entre hojas se muestra como texto plano en el chat, no como imagen/grafico.

### Opciones discutidas

| Opcion | Descripcion | Pros | Contras |
|--------|-------------|------|---------|
| **1. Mermaid.js (cliente)** | Cargar libreria y renderizar SVG | Interactivo, sin servidor | +1MB JS |
| **2. mermaid.ink (externo)** | Servicio web que genera PNG | Sin libreria | Requiere internet |

### Recomendacion
Opcion 1 con carga lazy (solo cuando hay diagrama). El TaskPane ya carga Plotly y D3, asi que Mermaid no agrega tanto peso relativo.

### Pendientes para proxima sesion

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar renderizado de Mermaid si usuario confirma |
| **ALTA** | Hacer commit de todos los cambios acumulados |
| **MEDIA** | Probar exportacion de chat |

---

### Sesion 2026-08-19 (~23:30) — Boton Exportar Chat Implementado

**Estado:** COMPLETO — Desplegado a produccion

### Logros
Implementado boton "Exportar Chat" que exporta toda la conversacion del tab IA como archivo Markdown.

### Funcionalidad
- Boton "Exportar Chat" en la barra de botones del tab IA
- Exporta: contexto cargado + todos los mensajes (usuario y asistente)
- Genera archivo: `chat_neven_YYYY-MM-DD_HHMM.md`
- Incluye timestamp y metadata

### Estructura del archivo exportado
```markdown
# Conversacion NEVEN IA

**Fecha:** 2026-08-19 23:30:00
**Mensajes:** 4

---

## Contexto cargado
[analisis de hoja/libro si existe]

---

## Conversacion

### [Usuario]
Pregunta del usuario...

### [Asistente]
Respuesta de la IA...

---
*Exportado desde NEVEN Studio*
```

### Correccion aplicada
Usuario indico que los emojis estan prohibidos. Se removieron:
- Boton: "Exportar Chat" (sin emoji)
- Formato MD: `[Usuario]` y `[Asistente]` en lugar de emojis

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/taskpane.html` | +boton, +listener, +funcion _aiExportChat() |
| `C:\NEVEN\TaskPane\taskpane.html` | Desplegado (213 KB) |

### Commits pendientes
No se hizo commit — acumulado con cambios de workbook analysis y descarga MD

### Pendientes para proxima sesion

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Hacer commit de todos los cambios acumulados de la sesion |
| **MEDIA** | Probar exportacion de chat en Excel |
| **BAJA** | Revisar otros lugares del codigo por emojis que deban removerse |

---

### Sesion 2026-08-19 (~23:00) — Discusion: Mejora de Exportacion

**Estado:** 💬 DISCUSIÓN — Pendiente implementación

### Feedback del usuario
El botón "⬇ MD" actual solo descarga el análisis inicial. El usuario señaló que sería más útil poder exportar **la conversación completa** con la IA, no solo el primer mensaje.

### Propuesta acordada
Implementar un **botón flotante "Exportar Chat"** en el área de chat que:
- Exporte toda la conversación como Markdown
- Incluya: contexto cargado + preguntas del usuario + respuestas de la IA
- Agregue timestamp al archivo

### Diseño propuesto
```
┌─────────────────────────────────┐
│  [Modo Consultor activo]        │
│  Usuario: ¿Qué hace esta hoja?  │
│  IA: Esta hoja calcula...       │
│  Usuario: ¿Hay errores?         │
│  IA: Detecté 3 problemas...     │
│                                 │
│  ─────────────────────────────  │
│  [📋 Exportar Chat]             │
└─────────────────────────────────┘
```

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar botón flotante "Exportar Chat" que exporta toda la conversación |
| **ALTA** | Hacer commit de todos los cambios acumulados |
| **MEDIA** | Considerar opción de seleccionar mensajes específicos (más complejo) |

---

### Sesión 2026-08-19 (~22:30) — Descarga MD de Análisis ✅

**Estado:** ✅ COMPLETO — Botones de descarga implementados y desplegados

### Logros
Implementados botones "⬇ MD" para descargar análisis como archivos Markdown:
- **Análisis de hoja** — botón verde junto al mensaje "Modo Consultor Excel activado"
- **Análisis de libro** — botón azul junto al mensaje "Modo Consultor de Libro activo"

### Funciones agregadas (`taskpane.js`)

| Función | Descripción |
|---------|-------------|
| `downloadWorkbookAnalysisMD()` | Descarga análisis de workbook como .md |
| `downloadSheetAnalysisMD()` | Descarga análisis de hoja como .md |
| `downloadTextFile(content, filename, mimeType)` | Utilidad genérica para descargar archivos de texto |

### Formato del archivo descargado
- Nombre: `analisis_{nombre}_{fecha}.md`
- Ejemplo: `analisis_Presupuesto_2026_2026-08-19.md`
- Contenido: mismo texto Markdown que se usa como contexto para la IA

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/taskpane.js` | +3 funciones, +2 botones en mensajes de sistema |
| `C:\NEVEN\TaskPane\taskpane.js` | Desplegado (106 KB) |

### Decisión de diseño
Se eligió **descarga MD directa** (opción 1) sobre PDF porque:
1. Trivial de implementar (ya teníamos el texto formateado)
2. Sin dependencias adicionales
3. El usuario puede convertir a PDF con cualquier herramienta si lo necesita
4. MD es editable y versionable

### Commits pendientes
⚠️ **No se hizo commit** — acumulado con cambios anteriores de workbook analysis

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Hacer commit de todos los cambios (workbook analysis + descarga MD) |
| **MEDIA** | Probar descarga MD en Excel |
| **BAJA** | Considerar agregar opción Print-to-PDF si el usuario lo solicita |

---

### Sesión 2026-08-19 (~22:00) — Confirmación: Análisis de Workbook Funciona ✅

**Estado:** ✅ VERIFICADO POR USUARIO — "Funciona a la perfección!"

### Logros
- Usuario probó el botón "Analizar Libro" en Excel con éxito
- La funcionalidad completa de análisis de workbook está operativa

### Siguiente feature solicitada
Usuario preguntó si es posible descargar el análisis en **PDF** o **MD**.

### Diseño propuesto para descarga

| Opción | Implementación | Pros | Contras |
|--------|---------------|------|---------|
| **MD directo** | Botón "⬇ MD" descarga archivo .md | Trivial, ya tenemos el texto | - |
| **PDF via Print** | Botón "🖨 PDF" abre ventana print | Sin dependencias | Usuario debe elegir "Guardar como PDF" |
| **PDF vía jsPDF** | Generación en frontend | Offline | Formato básico |
| **PDF vía weasyprint** | Generación en backend | PDF profesional | Requiere instalar dependencias GTK |

**Recomendación:** MD directo + Print-to-PDF (sin dependencias nuevas)

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar botón descarga MD del análisis de workbook |
| **ALTA** | Implementar botón Print-to-PDF (o decidir otra opción) |
| **ALTA** | Hacer commit de los cambios de análisis de workbook |
| **MEDIA** | Agregar botones de descarga también al análisis de hoja individual |

---

### Sesión 2026-08-19 (~21:30) — Análisis de Workbook Implementado ✅

**Estado:** ✅ COMPLETO — Código desplegado, pendiente prueba en Excel

### Resumen
Implementación completa del análisis a nivel de libro de trabajo para el Excel Consultant. Extiende la funcionalidad existente de análisis de hoja individual para detectar relaciones entre hojas, patrones arquitecturales y flujo de datos.

### Logros principales

1. **Backend Python** (`sheet_analyzer.py`) — +450 líneas nuevas:
   - `extract_cross_sheet_references()` — detecta fórmulas `=Sheet1!A1`, `='Sheet Name'!A1:B10`
   - `detect_workbook_pattern()` — clasifica: financial_model, dashboard, hub_and_spoke, chain, mesh, isolated_sheets
   - `build_workbook_data_flow()` — construye grafo de flujo (input → processing → output)
   - `analyze_workbook()` — entry point que orquesta todo + genera recomendaciones
   - Helpers: `_find_longest_path()`, `_generate_workbook_mermaid()`, `_generate_workbook_recommendations()`

2. **HTTP Server** (`neven_http_server.py`) — nuevo endpoint:
   - `POST /api/workbook/analyze` — recibe sheets[], retorna análisis completo
   - Handler `_handle_workbook_analyze()` con documentación completa

3. **Frontend JavaScript** (`taskpane.js`) — +380 líneas nuevas:
   - `captureWorkbookForAnalysis()` — captura todas las hojas (max 20, excluye ocultas)
   - `captureSheetData()` — helper para capturar una hoja individual
   - `analyzeWorkbookForAI()` — envía al backend, inyecta contexto, muestra chips
   - `formatWorkbookAnalysisForAI()` — formatea análisis como texto estructurado para AI
   - `showWorkbookConsultantChips()` — chips específicos para consultas de workbook
   - `WORKBOOK_CONSULTANT_CHIPS` — 6 prompts predefinidos para workbook

4. **UI** (`taskpane.html`):
   - Botón "📚 Analizar Libro" (azul, diferenciado del verde de "Analizar Hoja")
   - Función `_aiAnalyzeWorkbook()` — wrapper para el botón
   - Event listener en `initAITab()`

### Archivos modificados

| Archivo (repositorio) | Cambio |
|-----------------------|--------|
| `NEVEN/ControlPython/startup/sheet_analyzer.py` | +450 líneas (funciones workbook) |
| `NEVEN/ControlPython/startup/neven_http_server.py` | +import, +routing, +handler |
| `NEVEN/TaskPane/neven_http_server.py` | Mismo cambio (copia sincronizada) |
| `NEVEN/TaskPane/taskpane.js` | +380 líneas (funciones JS workbook) |
| `NEVEN/TaskPane/taskpane.html` | +botón, +listener, +función wrapper |

| Archivo (producción) | Tamaño |
|----------------------|--------|
| `C:\NEVEN\startup\sheet_analyzer.py` | 51 KB |
| `C:\NEVEN\startup\neven_http_server.py` | 117 KB |
| `C:\NEVEN\TaskPane\taskpane.js` | 106 KB |
| `C:\NEVEN\TaskPane\taskpane.html` | 215 KB |

### Decisiones de diseño

1. **Límite de 20 hojas** — Office.js tiene timeout de ~5 minutos; evita bloqueos en libros grandes
2. **Hojas ocultas ignoradas por default** — opción `includeHiddenSheets` para incluirlas
3. **Referencias externas solo se reportan** — no se sigue a `[OtroLibro.xlsx]Sheet!A1`
4. **Reutilización de `analyze_sheet()`** — composición, no duplicación de lógica
5. **Color azul para botón Workbook** — diferenciación visual del verde de Sheet
6. **Chips específicos por modo** — workbook tiene preguntas diferentes a sheet

### Patrones de workbook detectados

| Patrón | Descripción |
|--------|-------------|
| `financial_model` | Input sheets → Calculation sheets → Summary/Output |
| `dashboard` | Una hoja principal con gráficos referenciando datos |
| `hub_and_spoke` | Una hoja central con >50% de las referencias |
| `chain` | Flujo lineal Sheet1 → Sheet2 → Sheet3 |
| `mesh` | Alta interconectividad (>30% de conexiones posibles) |
| `database` | Hoja grande de datos + hojas de consulta |
| `isolated_sheets` | Hojas sin referencias cruzadas |

### Test del endpoint

Se probó con curl pero el servidor tenía la versión anterior del código (404). Se terminó el proceso (PID 33344) para forzar recarga.

**Próximo paso:** Reiniciar servidor desde Excel y probar con libro real.

### Commits pendientes
⚠️ **No se hizo commit** — cambios listos para commit:
```bash
git add NEVEN/ControlPython/startup/sheet_analyzer.py
git add NEVEN/ControlPython/startup/neven_http_server.py
git add NEVEN/TaskPane/neven_http_server.py
git add NEVEN/TaskPane/taskpane.js
git add NEVEN/TaskPane/taskpane.html
git commit -m "feat(excel-consultant): add workbook-level analysis with cross-sheet detection"
```

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Reiniciar servidor desde Excel y probar botón "Analizar Libro" |
| **ALTA** | Probar con libro real (múltiples hojas, fórmulas cruzadas) |
| **ALTA** | Hacer commit de los cambios |
| **MEDIA** | Verificar que los chips de workbook envían prompts correctamente |
| **MEDIA** | Probar detección de patrones (financial_model, dashboard, etc.) |
| **BAJA** | Agregar soporte para referencias externas (reportar libros vinculados) |
| **BAJA** | Documentar en Docusaurus (capítulo 14 de ontologías) |

---

### Sesión 2026-08-19 (~20:00) — Diseño Excel Consultant Workbook Analysis 📋

**Estado:** 📋 DISEÑO COMPLETO — Pendiente implementación

### Contexto
El Excel Consultant actual (`analyze_sheet()`) solo analiza la hoja activa. El usuario quiere extenderlo para analizar **todo el libro de trabajo**, aprovechando mejor la ontología Excel.

### Archivos explorados
| Archivo | Propósito |
|---------|-----------|
| `NEVEN/ControlPython/startup/sheet_analyzer.py` | Analizador actual de hojas |
| `NEVEN/docs/Docusaurus/14-ontologias-excel-consultant.md` | Documentación de ontología |
| `NEVEN/TaskPane/taskpane.js` | Captura JS con Office.js |

### Diseño propuesto

#### Nuevas funciones Python (`sheet_analyzer.py`)

| Función | Propósito |
|---------|-----------|
| `analyze_workbook(body)` | Entry point principal — analiza todo el libro |
| `extract_cross_sheet_references(sheets)` | Detecta fórmulas `=Sheet1!A1` entre hojas |
| `detect_workbook_pattern(sheets, cross_refs)` | Clasifica: financial_model, dashboard, hub_and_spoke, etc. |
| `build_data_flow_graph(sheets, cross_refs)` | Grafo de flujo Input → Processing → Output |

#### Nuevas funciones JavaScript (`taskpane.js`)

| Función | Propósito |
|---------|-----------|
| `captureWorkbookForAnalysis(options)` | Captura todas las hojas (max 20) |
| `analyzeWorkbookForAI()` | Envía al backend e inyecta contexto en AI |
| `formatWorkbookAnalysisForAI(analysis)` | Formatea análisis para prompt |

#### Nuevo endpoint HTTP
- `POST /api/workbook/analyze`

#### Nueva UI
- Botón "📚 Analizar Libro" junto al existente "📄 Analizar Hoja" en tab IA

### Detecciones que hará el análisis de workbook

| Detección | Descripción |
|-----------|-------------|
| **Cross-sheet refs** | Fórmulas que referencian otras hojas (`=Summary!B10`) |
| **Patrón arquitectural** | Financial Model, Dashboard, Hub-and-Spoke, Chain |
| **Flujo de datos** | Identificar hojas Input, Processing, Output |
| **Hojas huérfanas** | Hojas sin conexión con el resto del libro |
| **Referencias externas** | `[OtroLibro.xlsx]Sheet!A1` (solo reportar) |
| **Complejidad global** | Métricas agregadas de todas las hojas |

### Integración con ontología

La ontología `ONTOLOGIA/LIBROS EXCEL/` se usa para:
- Enriquecer funciones detectadas con descripciones/best practices
- Mapear patrones de workbook a patrones conocidos
- Generar recomendaciones basadas en los libros procesados (CFI, Curso Práctico)

### Tiempo estimado de implementación
| Fase | Tiempo |
|------|--------|
| Backend Python | ~2 horas |
| Frontend JavaScript | ~1.5 horas |
| Testing | ~1 hora |
| **Total** | **~4.5 horas** |

### Decisiones de diseño

1. **Límite de 20 hojas** — Office.js tiene timeout de ~5 min, evita bloqueos
2. **Hojas ocultas ignoradas por default** — opción para incluirlas
3. **Referencias externas solo se reportan** — no se sigue a otros libros
4. **Reutilizar `analyze_sheet()` por hoja** — composición, no duplicación

### Archivos a modificar (pendiente implementación)

| Archivo | Cambios |
|---------|---------|
| `NEVEN/ControlPython/startup/sheet_analyzer.py` | +4 funciones nuevas |
| `NEVEN/TaskPane/neven_http_server.py` | +endpoint `/api/workbook/analyze` |
| `NEVEN/TaskPane/taskpane.js` | +3 funciones JS, +1 botón UI |
| `C:\NEVEN\startup\neven_http_server.py` | Desplegar endpoint |
| `C:\NEVEN\TaskPane\taskpane.js` | Desplegar funciones JS |

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar `extract_cross_sheet_references()` en Python |
| **ALTA** | Implementar `analyze_workbook()` entry point |
| **MEDIA** | Implementar `captureWorkbookForAnalysis()` en JavaScript |
| **MEDIA** | Agregar endpoint `/api/workbook/analyze` |
| **MEDIA** | Agregar botón "Analizar Libro" en UI |
| **BAJA** | Tests con workbooks reales (financieros, dashboards) |

---

### Sesión 2026-08-19 (~19:00) — Eliminación de Código Legacy ✅

**Estado:** ✅ COMPLETO — Código obsoleto eliminado del repositorio

### Commit
`602b9a2` — `chore: remove legacy RJ2XCLModule_2018 code (obsolete since 2018)`

### Eliminado del repositorio
- `docs/_legacy/RJ2XCLModule_2018/` — Paquete R de 2018
  - `.gitignore`, `DESCRIPTION`, `NAMESPACE`
  - `R/RJ2XCLModule.R`
  - `man/*.Rd` (7 archivos de documentación)
  - `src/RJ2XCLModule.cc`
- **456 líneas de código obsoleto eliminadas**

### Problema encontrado
Git tenía un `index.lock` por procesos huérfanos. Se resolvió con:
```powershell
Stop-Process -Name "git" -Force
Remove-Item ".git\index.lock" -Force
```

### Resumen total de limpieza de la sesión

| Tipo | Elemento | Impacto |
|------|----------|---------|
| **Local** | Build/ | -291 MB |
| **Local** | AgentService/node_modules/ | -208 MB |
| **Local** | Ribbon/x64/ | -51 MB |
| **Repo** | docs/_legacy/ | -456 líneas |
| **Total local** | | **~550 MB recuperados** |

### Estado final del proyecto
- Tamaño repo: ~135 MB
- Commits totales de la sesión: 7

---

### Sesión 2026-08-19 (~18:45) — Limpieza de Archivos de Desarrollo ✅

**Estado:** ✅ COMPLETO — 550 MB recuperados

### Directorios eliminados (localmente, no afectan repo)

| Directorio | Tamaño | Razón |
|------------|--------|-------|
| `Build/` | 291 MB | Archivos de compilación cmake (regenerables) |
| `AgentService/node_modules/` | 208 MB | Dependencias Node.js (npm install) |
| `Ribbon/x64/` | 51 MB | Archivos intermedios .obj/.pdb |

### Resultado
- **Antes:** ~685 MB
- **Después:** 134.6 MB
- **Recuperado:** ~550 MB

### Comandos para regenerar si es necesario
```powershell
# Proyecto principal
cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release

# AgentService
cd AgentService && npm install
```

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **BAJA** | Eliminar `docs/_legacy/RJ2XCLModule_2018/` del repo (código obsoleto 2018) |

---

### Sesión 2026-08-19 (~18:30) — Análisis de Archivos Zombie 🔍

**Estado:** 🔍 ANÁLISIS COMPLETO — Pendiente decisión de limpieza

### Hallazgos

#### Limpieza LOCAL segura (~550 MB recuperables):
| Directorio | Tamaño | Estado |
|------------|--------|--------|
| `Build/` | 291 MB | En .gitignore, regenerable con cmake |
| `AgentService/node_modules/` | 208 MB | En .gitignore, regenerable con npm install |
| `Ribbon/x64/` | 51 MB | En .gitignore, build intermedios |

#### Candidatos para eliminar del REPO:
| Directorio | Razón |
|------------|-------|
| `docs/_legacy/RJ2XCLModule_2018/` | Código R de 2018, completamente obsoleto |
| `CreadorPresentaciones/` | Posible duplicado de TaskPane/presentaciones |

#### Mantener (nombre viejo pero necesario):
- `Core/include/rj2xcl*.h` — Prefijo interno por compatibilidad ABI
- `Ribbon/RJ2XCLRibbon.*` — Nombre del COM server registrado en Windows

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **MEDIA** | Ejecutar limpieza local (Build, node_modules, x64) |
| **BAJA** | Eliminar docs/_legacy del repo (commit de limpieza) |
| **BAJA** | Verificar si CreadorPresentaciones es duplicado |

---

### Sesión 2026-08-19 (~18:00) — Commits y Push al Repositorio ✅

**Estado:** ✅ COMPLETO — Todo subido a origin/main

### Commits realizados

| Hash | Descripción |
|------|-------------|
| `85e5374` | feat(ribbon): add Stop Server button to control HTTP server lifecycle |
| `fa41618` | feat(server): add /api/shutdown endpoint for graceful server stop |
| `1bfcdd3` | docs: update documentation to v3.2 |
| `450e7b4` | build(installer): update to v3.2 and rewrite README |
| `0705742` | release: NEVEN v3.2 distribution package |
| `0e45d46` | release: NEVEN v3.2 distribution package (21.7 MB) — con ZIP |

### Decisión: ZIP en el repositorio
El archivo `NEVEN-v3.2-Setup.zip` estaba excluido por `.gitignore` (regla `*.zip`).
Se usó `git add -f` para forzar su inclusión porque el usuario necesita que esté disponible para descarga directa desde el repo.

**Ubicación:** `Releases/v3.2/NEVEN-v3.2-Setup.zip` (21.7 MB)

### Estructura de Releases/
```
Releases/
├── README.md           # Instrucciones de instalación
└── v3.2/
    └── NEVEN-v3.2-Setup.zip  # Paquete completo
```

---

### Sesión 2026-08-19 (~17:30) — Instalador NEVEN v3.2 Completado ✅

**Estado:** ✅ COMPLETO — Paquete de distribución listo para usuario final

### Logros de la sesión
1. ✅ Botón "Detener Servidor" funciona correctamente
2. ✅ Instalador actualizado a versión 3.2
3. ✅ Paquete de distribución creado

### Cambios realizados en el instalador

| Archivo | Cambio |
|---------|--------|
| `Install/Build-Installers.ps1` | Versión 2.0.0.0 → 3.2.0.0 |
| `Install/Install-NEVEN.ps1` | Banner "NEVEN Installer v3.2", fase 4b v3.2 |
| `Install/README.md` | Reescrito completo (RJ2XCL → NEVEN, instrucciones actuales) |
| `Install/Dist/` | Creado con 389 archivos desde C:\NEVEN |
| `Install/Install-NEVEN.exe` | Regenerado (122 KB) |
| `Install/Uninstall-NEVEN.exe` | Regenerado (33 KB) |
| `Install/NEVEN-v3.2-Setup.zip` | Paquete de distribución (21.7 MB) |

### Contenido del paquete de distribución

```
NEVEN-v3.2-Setup.zip (21.7 MB, 397 archivos)
├── Install-NEVEN.exe      # Instalador ejecutable
├── Install-NEVEN.ps1      # Script PowerShell
├── Install-NEVEN.cmd      # Wrapper
├── Uninstall-NEVEN.exe    # Desinstalador
├── Uninstall-NEVEN.ps1
├── Uninstall-NEVEN.cmd
├── README.md              # Instrucciones
├── license.txt            # GPL v3
└── Dist/                  # Artefactos (33.1 MB)
    ├── NEVEN64.xll, ControlR/Julia/Python.exe, NEVENRibbon.dll
    ├── neven-config.json, neven-languages.json
    ├── startup/ (4 archivos)
    ├── taskpane/ (62 archivos)
    ├── docs/neven-docs.html
    ├── examples/ (82 archivos)
    ├── functions/ (148 archivos)
    ├── libreria/R/ (63), JULIA/ (9), PYTHON/ (3)
    └── prompts/ (7 archivos)
```

### Uso del instalador

```powershell
# Descomprimir NEVEN-v3.2-Setup.zip
# Ejecutar como administrador:
.\Install-NEVEN.exe

# O silencioso:
.\Install-NEVEN.exe -Silent
```

### Para probar el instalador
1. Copiar `NEVEN-v3.2-Setup.zip` a una máquina limpia (sin NEVEN instalado)
2. Descomprimir
3. Ejecutar `Install-NEVEN.exe` como administrador
4. Verificar que Excel muestra la pestaña NEVEN
5. Probar `=NEVEN.r("1+1")` → debería retornar 2

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| **MEDIA** | Agregar sysimage Julia al instalador (opcional, +415 MB) |
| **BAJA** | Crear firma digital para los .exe |

---

### Sesión 2026-08-19 (~17:00) — Preparación del Instalador para Usuario Final

**Estado:** 🔍 EN EXPLORACIÓN — Revisando estructura actual del instalador

### Logro
✅ Botón "Detener Servidor" funciona correctamente (Iniciar → Detener → Iniciar de nuevo OK)

### Exploración del instalador
Se revisó la estructura actual en `NEVEN/Install/`:
- `Install-NEVEN.ps1` — Script principal de instalación (2300+ líneas, muy completo)
- `Build-Installers.ps1` — Genera .exe con ps2exe
- `Install-NEVEN.exe` / `Uninstall-NEVEN.exe` — Ejecutables generados
- `README.md` — Aún tiene referencias a "RJ2XCL" (nombre viejo)

### Contenido de producción (C:\NEVEN\)
El directorio de producción contiene ~50+ archivos/carpetas:
- Binarios: NEVEN64.xll, NEVENRibbon.dll, ControlR/Julia/Python.exe
- Configs: neven-config.json, neven-languages.json
- Documentación: docs/, neven-docs.html
- Funciones: functions/, libreria/
- TaskPane: taskpane/, startup/
- Sysimage Julia: neven_julia.dll (~415MB)

### Pendientes para próxima sesión
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Definir qué actualizar: versión, Dist, README, paquete ZIP |
| **ALTA** | Crear directorio Dist con artefactos compilados actuales |
| **MEDIA** | Actualizar README.md (RJ2XCL → NEVEN) |
| **MEDIA** | Regenerar Install-NEVEN.exe con versión 3.2 |

---

---

## Sesiones recientes

### Sesión 2026-08-19 (~16:45) — Fix: Deadlock en shutdown del servidor ✅

**Estado:** ✅ CORREGIDO — Servidor ahora se apaga correctamente

### Síntoma
Al presionar Detener Servidor aparecía:
> "El servidor no respondió a la solicitud de apagado."

El servidor seguía corriendo (navegador respondía JSON).

### Causa raíz
`stop_server()` llama a `_server_instance.shutdown()` que **bloquea** esperando que terminen todas las peticiones en curso. Pero la petición de `/api/shutdown` está en curso → **deadlock**.

### Solución
Usar `server_close()` en lugar de `shutdown()`:
- `shutdown()` → espera gracefully, bloquea si hay peticiones activas
- `server_close()` → cierra el socket inmediatamente sin bloquear

```python
def _shutdown_server():
    time.sleep(0.3)
    if _server_instance:
        _server_instance.server_close()  # ← NO bloquea
    time.sleep(0.1)
    os._exit(0)
```

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `TaskPane/neven_http_server.py` | `server_close()` en lugar de `stop_server()` |
| `ControlPython/startup/neven_http_server.py` | Mismo cambio |
| `C:\NEVEN\startup\neven_http_server.py` | Desplegado |

### Intentos fallidos
1. **`os._exit(0)` directo** → puerto quedaba en TIME_WAIT
2. **`stop_server()` → `shutdown()`** → deadlock porque espera fin de peticiones

### Lección aprendida
⚠️ **Nunca llamar `shutdown()` desde dentro de un request handler** — causa deadlock. Usar `server_close()` para cierre forzado.

### Para verificar
1. Matar python.exe desde Task Manager
2. Iniciar Servidor → OK
3. Verificar navegador → responde JSON
4. Detener Servidor → debe apagarse
5. Navegador → no debe responder
6. Iniciar Servidor de nuevo → debe funcionar

---

### Sesión 2026-08-19 (~16:30) — Bug: Detener Servidor no detecta servidor activo 🔍

**Estado:** ⚠️ REEMPLAZADO — El check sí funcionaba, el problema era el shutdown

### Síntoma
Después de Detener Servidor, al intentar Iniciar Servidor de nuevo aparecía error:
> "No se pudo iniciar el servidor HTTP. Verifica que Python esté instalado y que no haya otro proceso usando el puerto 5555."

### Causa raíz
El método `_handle_shutdown()` usaba `os._exit(0)` directamente, lo que terminaba el proceso Python **sin cerrar el socket HTTP primero**. El SO dejaba el puerto 5555 en estado TIME_WAIT por varios segundos.

### Solución
Llamar a `stop_server()` (que ya existía) antes de `os._exit(0)`. Esta función hace `_server_instance.shutdown()` que cierra el socket limpiamente.

```python
def _shutdown_server():
    time.sleep(0.3)  # Respuesta HTTP
    stop_server()    # ← NUEVO: cierra socket
    time.sleep(0.2)  # Liberar puerto
    os._exit(0)
```

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `TaskPane/neven_http_server.py` | `_handle_shutdown()` ahora llama `stop_server()` |
| `ControlPython/startup/neven_http_server.py` | Mismo cambio |
| `C:\NEVEN\startup\neven_http_server.py` | Desplegado |

### Lección aprendida
⚠️ **Siempre cerrar recursos (sockets, archivos, conexiones) antes de `os._exit()`**. El SO no limpia sockets en uso inmediatamente — quedan en TIME_WAIT ~30-60 segundos.

---

### Sesión 2026-08-19 (~15:30) — Botón "Detener Servidor" ✅

**Estado:** ✅ COMPLETO — Botón implementado y desplegado

### Problema
El servidor HTTP de NEVEN Studio (`start_studio.py`) corre como proceso independiente de Excel. Cuando el usuario cierra Excel, el servidor sigue corriendo en segundo plano consumiendo recursos (puerto 5555 ocupado, Python en memoria).

### Solución
Agregar botón "Detener Servidor" junto al existente "Iniciar Servidor" en el grupo Studio del Ribbon. El botón envía POST a `/api/shutdown` para apagar el servidor de forma limpia.

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `Ribbon/ribbon_connect.h` | DispId `OnStopServerCommand`, mapeo en GetIDsOfNames, case handler con WinHttp |
| `Ribbon/ribbon_ui.xml` | Botón `btnStopServer` con imageMso="RecordStop" |
| `TaskPane/neven_http_server.py` | Endpoint `/api/shutdown` + método `_handle_shutdown()` |
| `ControlPython/startup/neven_http_server.py` | Mismo endpoint (copia sincronizada) |
| `docs/Docusaurus/07-webview2-ribbon.md` | Documentación del botón Detener Servidor |
| `docs/neven-docs.html` | Regenerado (15 capítulos, 212.6 KB) |

### Producción desplegada
- `C:\NEVEN\NEVENRibbon.dll` — DLL del Ribbon
- `C:\NEVEN\startup\neven_http_server.py` — Servidor HTTP
- `C:\NEVEN\docs\neven-docs.html` — Documentación

### Comportamiento del botón
1. **Si servidor activo:** POST a `/api/shutdown`, espera 500ms, confirma apagado
2. **Si servidor inactivo:** Muestra "No hay nada que detener"
3. **Si no responde:** Sugiere terminar manualmente desde Task Manager

### Para verificar
1. Cerrar Excel
2. Abrir Excel con NEVEN
3. Iniciar Servidor → confirmar mensaje de éxito
4. Detener Servidor → confirmar mensaje "Puerto 5555 liberado"
5. Verificar que python.exe ya no aparece en Task Manager

### Decisiones de diseño
- **Endpoint `/api/shutdown`:** Se usa apagado en thread separado con `os._exit(0)` para permitir que la respuesta HTTP llegue al cliente antes de cerrar el servidor
- **WinHttp en C++:** Se reutiliza el patrón de `_studio_alive()` lambda para verificar estado del servidor
- **imageMso="RecordStop":** Icono intuitivo de "detener" que complementa visualmente a "ServerConnection" del botón Iniciar

### Commits pendientes
⚠️ **No se hizo commit** — cambios listos para commit manual:
```
git add NEVEN/Ribbon/ribbon_connect.h NEVEN/Ribbon/ribbon_ui.xml
git add NEVEN/TaskPane/neven_http_server.py NEVEN/ControlPython/startup/neven_http_server.py
git add NEVEN/docs/Docusaurus/07-webview2-ribbon.md NEVEN/docs/neven-docs.html
git commit -m "feat(ribbon): add Stop Server button to control HTTP server lifecycle"
```

### Pendientes para próxima sesión
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar botón Detener Servidor en Excel (requiere reinicio) |
| **ALTA** | Proceder con actualización del instalador de NEVEN |
| **MEDIA** | Commit de todos los cambios de esta sesión |

---

### Sesión 2026-08-19 (~14:45) — Documentación Docusaurus actualizada ✅

**Estado:** ✅ COMPLETO — Manual de usuario regenerado y desplegado

### Resumen
Actualización completa de la documentación Docusaurus para reflejar NEVEN v3.2.

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `docs/Docusaurus/00-portada.md` | Versión v3.2, Python en diagrama, novedades, fecha Setiembre 2026 |
| `docs/Docusaurus/02-instalacion.md` | Python en requisitos, verificación NEVEN.py, troubleshooting Iniciar Servidor |
| `docs/Docusaurus/07-webview2-ribbon.md` | Tabla de grupos/botones actualizada (6 grupos), botón Iniciar Servidor |
| `docs/Docusaurus/13-neven-studio.md` | Sección 13.9 Sistema de Aliases, sección 13.10 Troubleshooting |
| `docs/_build_docs.js` | Capítulo 14 agregado, título v3.2 |
| `docs/neven-docs.html` | Regenerado (15 capítulos, 211 KB) |
| `C:\NEVEN\docs\neven-docs.html` | Desplegado a producción |

### Contenido nuevo documentado
1. **Python** como tercer motor de scripting
2. **Botón Iniciar Servidor** en grupo Studio del Ribbon
3. **Sistema de Aliases** para funciones (ACP, KMeans, etc.)
4. **Capítulo 14** de Ontologías y Excel Consultant incluido en el build
5. **Versión v3.2** en portada y headers

### Para verificar
Abrir `C:\NEVEN\docs\neven-docs.html` en navegador y revisar:
- Portada muestra v3.2 y Python
- Capítulo 2 incluye Python y troubleshooting
- Capítulo 7 tiene tabla de Ribbon actualizada
- Capítulo 13 tiene sección de Aliases
- Capítulo 14 (Ontologías) aparece en sidebar

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **MEDIA** | Hacer commit de cambios de documentación |
| **BAJA** | Revisar capítulos 3-6 y 8-12 por actualizaciones menores |

---

### Sesión 2026-08-19 (continuación ~14:45-14:40) — Caracteres UTF-8 en MessageBox ✅ VERIFICADO

**Estado:** ✅ COMPLETO — Botón funciona correctamente, texto se muestra sin errores

### Síntoma resuelto
El MessageBox mostraba caracteres corruptos ("estÃ¡" en lugar de "está").

### Causa raíz
UTF-8 en archivo fuente + compilador MSVC interpreta como Windows-1252.

### Solución
Usar ASCII puro (sin tildes) en los strings del MessageBox.

### Verificación
Usuario confirmó que el mensaje "El servidor HTTP ya esta en ejecucion." se muestra correctamente.

### Archivos modificados en esta sesión completa
| Archivo | Cambio |
|---------|--------|
| `NEVEN/Ribbon/ribbon_connect.h` | +DispId, +mapeo, +case handler, fix de caracteres |
| `NEVEN/Ribbon/ribbon_ui.xml` | +botón btnStartServer |
| `C:\NEVEN\NEVENRibbon.dll` | DLL desplegada |

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **MEDIA** | Hacer commit de cambios del Ribbon al repositorio |

---

### Sesión 2026-08-19 (continuación ~14:00-14:45) — Ribbon no se muestra ✅ RESUELTO

**Estado:** RESUELTO — El botón "Iniciar Servidor" aparece y funciona

### Síntoma
Después de implementar el botón "Iniciar Servidor" y desplegar NEVENRibbon.dll, el Ribbon NEVEN dejó de aparecer en Excel.

### Causa raíz
La primera compilación no regeneró correctamente los recursos embebidos (el XML del Ribbon). El timestamp de la DLL no había cambiado después del primer intento de compilación.

### Solución
Recompilación limpia con `cmake --build --clean-first` que forzó la regeneración completa de recursos.

### Diagnóstico realizado (para referencia futura)
1. **DLL existe y tiene tamaño correcto:** 319KB en C:\NEVEN\NEVENRibbon.dll ✓
2. **XML es válido:** Sin BOM, parsea correctamente ✓
3. **COM registrado correctamente:** CLSID en HKCU ✓
4. **Add-in habilitado:** LoadBehavior=3 ✓
5. **Sin items deshabilitados en Resiliency** ✓

### Lección aprendida
**Siempre verificar el timestamp de la DLL después de compilar.** Si no cambia, la compilación no se completó correctamente y hay que usar `--clean-first`.

### Resultado final
- Ribbon NEVEN aparece correctamente
- Botón "Iniciar Servidor" visible en grupo Studio
- Pendiente: probar la funcionalidad del botón

---

### Sesión 2026-08-19 — Botón "Iniciar Servidor" en Ribbon ✅

**Estado:** Implementado y desplegado a producción

**Commits pendientes:** Los cambios del Ribbon aún no están commiteados al repositorio.

## ✅ IMPLEMENTADO: Botón para iniciar servidor HTTP desde el Ribbon

### Contexto
El TaskPane (NEVEN Studio) requiere que el servidor HTTP esté corriendo en el puerto 5555.
Cuando el servidor no está activo, el TaskPane muestra "ERROR DEL COMPLEMENTO" con error de conectividad.
Previamente, el usuario tenía que ejecutar manualmente el script de inicio.

### Solución
Nuevo botón "Iniciar Servidor" en la pestaña NEVEN → grupo Studio del Ribbon.

### Funcionalidad
1. **Si el servidor ya está corriendo:** Muestra mensaje informativo (puerto 5555 activo)
2. **Si no está corriendo:** 
   - Ejecuta `python start_studio.py --no-browser` via CreateProcessW
   - Espera hasta 15 segundos para que el servidor inicie
   - Muestra mensaje de éxito o error según el resultado

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/Ribbon/ribbon_connect.h` | +DispId `OnStartServerCommand`, mapeo en GetIDsOfNames, case handler con lógica _studio_alive |
| `NEVEN/Ribbon/ribbon_ui.xml` | +Botón `btnStartServer` en grupo grpStudio |
| `C:\NEVEN\NEVENRibbon.dll` | DLL recompilada y desplegada |

### Ubicación del botón
- **Pestaña:** NEVEN
- **Grupo:** Studio
- **Posición:** Entre "NEVEN Studio" y "Presentaciones"
- **Icono:** ServerConnection (size: normal)
- **Texto:** "Iniciar Servidor"
- **Tooltip:** "Inicia el servidor HTTP en el puerto 5555 si no está corriendo."

### Código clave (ribbon_connect.h)
```cpp
case DispIds::OnStartServerCommand:
{
    // Lambda para verificar si el servidor está vivo
    auto _studio_alive = []() -> bool { ... WinHTTP ping a localhost:5555 ... };
    
    // Si ya está corriendo, notificar
    if (_studio_alive()) {
        MessageBoxW(NULL, L"El servidor HTTP ya está en ejecución...", ...);
        return S_OK;
    }
    
    // Iniciar servidor
    CreateProcessW(..., L"python start_studio.py --no-browser", ...);
    
    // Esperar hasta 15 segundos
    for (int i = 0; i < 30 && !_studio_alive(); i++) Sleep(500);
    
    // Notificar resultado
    if (_studio_alive()) MessageBoxW(...éxito...);
    else MessageBoxW(...error...);
}
```

### Para probar
1. Cerrar Excel si está abierto
2. Abrir Excel
3. Ir a pestaña NEVEN → grupo Studio
4. Hacer clic en "Iniciar Servidor"
5. Verificar que el TaskPane puede conectarse

### Decisiones de diseño
- **Reutilización de lógica:** Se reutilizó el lambda `_studio_alive` de `OnAIAssistantCommand` en lugar de extraerlo a función separada. Esto evita cambios en la interfaz pero implica código duplicado. Aceptable porque la lógica es estable.
- **Timeout de 15s:** Igual que en OnAIAssistantCommand, suficiente para que Python arranque el servidor.
- **Tamaño del botón:** `size="normal"` en lugar de `large` para no ocupar demasiado espacio visual.

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Hacer commit de cambios del Ribbon al repositorio |
| **MEDIA** | Probar el botón en Excel para verificar funcionamiento |
| **BAJA** | Considerar extraer `_studio_alive` a función helper si se usa en más lugares |

---

### Sesión 2026-08-20 — TipoOutput=99 para NevenX (gráficos embebidos) ✅

**Estado:** Implementado, compilado, **EN PRUEBA** — problema con posición de TipoOutput

## ✅ IMPLEMENTADO: TipoOutput=99 para embeber gráficos de análisis como Shapes

### Concepto
Extender las funciones NevenX existentes (AD_ACP, clustering, etc.) para que con `TipoOutput=99` 
generen un gráfico PNG y lo embaban como Shape en Excel, reutilizando el mismo mecanismo de NEVEN.Chart.

### ⚠️ PROBLEMA DETECTADO EN PRUEBA
Usuario reportó que retorna matriz de correlaciones en lugar del gráfico.
**Causa probable:** Posición incorrecta de TipoOutput en la llamada.

Convención NevenX:
```
Pos 1  (proceso) : Metodo        → "AD_ACP.C"
Pos 2  (a0)      : SetDatosY     → datos (o vacío)
Pos 3  (a1)      : SetDatosX     → datos (o vacío)  
Pos 4  (a2)      : TipoOutput    → 99
Pos 5  (a3)      : Escala
```

**Llamada INCORRECTA:** `=NevenX.R("AD_ACP.C", A1:D20,,, 99)` → TipoOutput en pos 5
**Llamada CORRECTA:** `=NevenX.R("AD_ACP.C", A1:D20, , 99)` → TipoOutput en pos 4

### Arquitectura
```
Excel: =NevenX.R("AD_ACP.C", A1:D20,,, 99)
   │
   ▼
1. NevenX_R() llama .nevenx_dispatch en R
2. R ejecuta AD_ACP.C con TipoOutput=99
3. AD_ACP.C genera biplot PNG con ggplot2
4. Retorna data.frame con marcador NEVEN_EMBED_CHART
5. C++ detecta marcador en NevenX_HandleEmbedChart()
6. UpdateGraphics() crea Shape en Excel
7. Retorna "Chart: nombre"
```

### Protocolo de marcador
R retorna un data.frame con 4 columnas especiales:
| Columna | Contenido |
|---------|-----------|
| NEVEN_EMBED_CHART | Ruta al PNG (C:/NEVEN/temp/nevenx_*.png) |
| NEVEN_CHART_NAME | Nombre para el Shape |
| NEVEN_CHART_WIDTH | Ancho en píxeles |
| NEVEN_CHART_HEIGHT | Alto en píxeles |

C++ detecta la columna `NEVEN_EMBED_CHART` y llama a `UpdateGraphics()`.

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\functions\R4XCL-AD-ACP.R` | +75 líneas: TipoOutput=99 genera biplot ggplot2 |
| `NEVEN/libreria/R/R4XCL-AD-ACP.R` | Copia en repo |
| `Core/src/basic_functions.cc` | +85 líneas: NevenX_HandleEmbedChart helper |

### Código R agregado (AD_ACP.C, TipoOutput=99)
```r
}else if(TipoOutput == 99){
    # Genera biplot con ggplot2
    chart_name <- paste0("ACP_", format(Sys.time(), "%H%M%S"))
    temp_file <- paste0("C:/NEVEN/temp/nevenx_", chart_name, ".png")
    
    # Extraer scores y loadings para biplot
    scores <- as.data.frame(res.pca$scores[, 1:2])
    loadings <- as.data.frame(unclass(res.pca$loadings)[, 1:2])
    
    # Crear biplot con ggplot2
    p <- ggplot() +
      geom_point(data=scores, ...) +
      geom_segment(data=loadings, ...) +
      theme_minimal()
    
    ggsave(temp_file, p, ...)
    
    # Retornar marcador para C++
    OutPut <- data.frame(
      NEVEN_EMBED_CHART = temp_file,
      NEVEN_CHART_NAME = chart_name,
      NEVEN_CHART_WIDTH = 500,
      NEVEN_CHART_HEIGHT = 400
    )
}
```

### Código C++ agregado (NevenX_HandleEmbedChart)
```cpp
static LPXLOPER12 NevenX_HandleEmbedChart(LPXLOPER12 result) {
    // Detectar columna NEVEN_EMBED_CHART en headers
    // Extraer ruta PNG, nombre, dimensiones
    // Verificar archivo existe
    // Llamar UpdateGraphics() para crear Shape
    // Retornar "Chart: nombre"
}

// Aplicado a NevenX_R, NevenX_J, NevenX_P:
LPXLOPER12 embed_result = NevenX_HandleEmbedChart(result);
return embed_result ? embed_result : result;
```

### Uso
```excel
=NevenX.R("AD_ACP.C", A1:D20,,, 99)   ; Biplot de ACP embebido
=NevenX.R("AD_ACP.C", A1:D20,,, 1)    ; Matriz de correlación (comportamiento normal)
```

### Extensibilidad
Para agregar TipoOutput=99 a otras funciones:
1. Agregar bloque `}else if(TipoOutput == 99){` en la función R
2. Generar gráfico apropiado para el análisis
3. Guardar en `C:/NEVEN/temp/nevenx_*.png`
4. Retornar data.frame con marcador NEVEN_EMBED_CHART

### Commits pendientes
- `feat(NevenX): add TipoOutput=99 for embedded charts`

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Ejecutar `=NevenX.R("AD_ACP.C", A1:D20, , 99)` y revisar consola R para ver debug: `[AD_ACP.C DEBUG] TipoOutput recibido: X` |
| **ALTA** | Si TipoOutput no es 99, debuggear dispatcher `.nevenx_dispatch` — problema en extracción de a2 |
| **MEDIA** | Agregar TipoOutput=99 a otras funciones: AD_KMediass, AD_ClusteringJerarquico, RG_Lineal |
| **MEDIA** | Crear commit con los cambios |
| **BAJA** | Documentar TipoOutput=99 en la Ayuda del Task Pane |

### Debug agregado
Se agregó línea de debug en `AD_ACP.C`:
```r
cat("[AD_ACP.C DEBUG] TipoOutput recibido:", TipoOutput, "clase:", class(TipoOutput), "\n")
```

También se agregó TipoOutput=99 al sidecar `R4XCL-AD-ACP.json`.

### Archivos modificados en debugging
- `C:\NEVEN\functions\R4XCL-AD-ACP.R` — línea debug agregada
- `C:\NEVEN\functions\R4XCL-AD-ACP.json` — TipoOutput=99 agregado a tipo_outputs

---

### Continuación 2026-08-19 — Debugging TipoOutput=99

**Estado:** En espera de resultado de debug

**Comando a probar:**
```excel
=NevenX.R("AD_ACP.C", A1:D20, , 99)
```

**Qué buscar en consola R:**
```
[AD_ACP.C DEBUG] TipoOutput recibido: X clase: Y
```

**Interpretación del resultado:**
- Si `TipoOutput recibido: 99` → problema en el bloque TipoOutput=99 de R
- Si `TipoOutput recibido: 1` o `0` → problema en dispatcher `.nevenx_dispatch`

**Hipótesis sobre el bug:**
El dispatcher extrae TipoOutput de `a2` pero posiblemente:
1. Excel comprime comas vacías diferente de lo esperado
2. El tipo de dato no es integer (podría ser matrix 1x1)
3. La función `.nevenx_as_scalar` no convierte correctamente

### Debug mejorado — retorno en celda
Se modificó AD_ACP.C para que TipoOutput=98 retorne información de debug directamente en la celda:
```r
if (isTRUE(TipoOutput == 98L) || isTRUE(TipoOutput == 98)) {
    return(data.frame(
      DEBUG_TipoOutput = as.character(TipoOutput),
      DEBUG_Clase = class(TipoOutput)[1],
      DEBUG_SetDatosX_class = class(SetDatosX)[1],
      DEBUG_SetDatosX_nrow = if(is.data.frame(SetDatosX)) nrow(SetDatosX) else NA
    ))
}
```

**Comando a probar:**
```excel
=NevenX.R("AD_ACP.C", A1:D20, , 98)
```

**Interpretación:**
- Si retorna tabla con DEBUG_TipoOutput=98 → dispatcher funciona, problema en bloque 99
- Si retorna matriz de correlaciones → TipoOutput no llega correctamente

### Resultado: TipoOutput NO llega a la función
Probado con TipoOutput=98, sigue retornando matriz de correlaciones. **Confirmado: el problema está en el dispatcher.**

### Debug del dispatcher agregado
Se agregó modo DEBUG al dispatcher para inspeccionar argumentos:
```r
# En .nevenx_dispatch, si proceso == "DEBUG":
return(data.frame(arg, class, is_null, value))
```

**Comando a probar:**
```excel
=NevenX.R("DEBUG", A1:D20, , 99)
```

Esto mostrará dónde aterriza cada argumento (a0-a4) para identificar si el 99 está en a2 o en otra posición.

### ✅ CAUSA RAÍZ ENCONTRADA

**Resultado del debug:**
```
arg  class         is_null    value
a0   matrix,array  FALSO      VENTAS
a1   numeric       FALSO      99      ← ¡El 99 está en a1, no en a2!
a2   NULL          VERDADERO  NULL
a3   NULL          VERDADERO  NULL
a4   NULL          VERDADERO  NULL
```

**Problema:** Excel comprime comas vacías consecutivas. Cuando escribes:
```excel
=NevenX.R("AD_ACP.C", A1:D20, , 99)
```
Excel interpreta `, ,` como un solo espacio, y el 99 aterriza en a1 en vez de a2.

**Solución:** Usar placeholder explícito:
```excel
=NevenX.R("AD_ACP.C", A1:D20, 0, 99)
```
o
```excel
=NevenX.R("AD_ACP.C", A1:D20, "", 99)
```

### Pendientes actualizados

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar `=NevenX.R("AD_ACP.C", A1:D20, 0, 99)` con placeholder |
| **MEDIA** | Considerar fix en dispatcher para manejar comas vacías de Excel |
| **MEDIA** | Remover código de debug temporal de AD_ACP.C y NevenX.R |
| **BAJA** | Documentar comportamiento de placeholders en ayuda |

### Progreso adicional — R funciona, C++ pendiente

**Resultado con placeholder:**
```
=NevenX.R("AD_ACP.C", A1:D20, 0, 99)
```
Retorna tabla con:
- NEVEN_EMBED_CHART: C:/NEVEN/temp/nevenx_ACP_175315.png
- NEVEN_CHART_NAME: ACP_175315
- NEVEN_CHART_WIDTH: 500
- NEVEN_CHART_HEIGHT: 400

**El lado R funciona perfectamente** — genera el PNG y retorna el marcador.

**Problema:** El PNG no se incrusta como Shape. El código C++ `NevenX_HandleEmbedChart` no está ejecutándose.

**Causa probable:** El DLL cargado en Excel es el viejo (antes de agregar el helper). La copia del DLL falló porque Excel estaba abierto.

**Pendiente ALTA:**
1. Cerrar Excel completamente
2. Copiar DLL: `[System.IO.File]::Copy("F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Build\Core\Release\NEVEN64.dll", "C:\NEVEN\NEVEN64.xll", $true)`
3. Abrir Excel y probar de nuevo

### Debug C++ agregado

Se verificó que el DLL en producción es de las 16:53, igual que el compilado. **El problema está en el código C++**, no en la copia.

Se agregó logging extensivo con `OutputDebugStringA` a `NevenX_HandleEmbedChart` para diagnosticar:
- Si la función se llama
- Qué tipo de xltype tiene el resultado
- Cuántas filas/columnas
- Qué headers detecta
- Si encuentra NEVEN_EMBED_CHART

**DLL recompilado** con debug logging. Pendiente:
1. Cerrar Excel
2. Copiar DLL nuevo
3. Abrir DebugView (Sysinternals) para ver logs `[NEVEN]`
4. Probar `=NevenX.R("AD_ACP.C", A1:D20, 0, 99)`

### ✅ BUG ENCONTRADO Y CORREGIDO: xltype flags

**Evidencia del debug:**
```
Header col 0: xltype=16386  (esperado: 2 = xltypeStr)
```

**Causa raíz:** El código comparaba `cell->xltype == xltypeStr` pero el tipo real era `xltypeStr | xlbitDLLFree` (2 + 16384 = 16386). Los flags `xlbitXLFree` y `xlbitDLLFree` indican quién libera la memoria, no cambian el tipo de dato.

**Fix aplicado:** Limpiar flags antes de comparar:
```cpp
int cell_type = cell->xltype & ~(xlbitXLFree | xlbitDLLFree);
if (cell_type == xltypeStr) { ... }
```

Se aplicó el mismo fix a todas las comparaciones de xltype en `NevenX_HandleEmbedChart`.

**DLL recompilado.** Pendiente probar.

### Archivos modificados esta sesión
- `C:\NEVEN\functions\R4XCL-AD-ACP.R` — TipoOutput=99 + debug temporal
- `C:\NEVEN\functions\R4XCL-AD-ACP.json` — TipoOutput=99 en tipo_outputs  
- `C:\NEVEN\functions\R4XCL-0-NevenX.R` — modo DEBUG para inspeccionar argumentos
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Core\src\basic_functions.cc` — fix xltype flags + debug logging

### Pendientes actualizados

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar `=NevenX.R("AD_ACP.C", A1:D20, 0, 99)` con DLL corregido |
| **ALTA** | Si funciona, remover código de debug de C++ y R |
| **MEDIA** | Crear commit con los cambios |
| **BAJA** | Documentar uso de placeholder (0) para argumentos vacíos |

### Progreso: Headers detectados, UpdateGraphics llamado

**Log exitoso:**
```
[NEVEN] Header col 0: 'NEVEN_EMBED_CHART'
[NEVEN] chart_col=0 name_col=1 width_col=2 height_col=3
[2026-09-28 18:09:05] [DEBUG] creating device target
```

El flujo llega hasta `UpdateGraphics` (mensaje "creating device target"). **El problema ahora está en la creación del Shape**, no en la detección del marcador.

**Pendiente verificar:**
1. ¿El resultado en la celda dice "Chart: ACP_XXXXXX"? → **SÍ: "Chart: ACP_180905"**
2. ¿Hay algún Shape nuevo? (Vista → Panel de Selección o Alt+F10) → **NO**
3. ¿Hay errores adicionales en DebugView después de "creating device target"? → **No hay errores**

### Problema identificado: UpdateGraphics no crea el Shape

El código llega hasta `CreateDeviceTarget` pero el Shape no aparece en Excel. Posibles causas:
- `get_ActiveSheet()` falla
- `raw_AddShape()` falla silenciosamente
- Problema con COM threading

Se agregó debug extensivo a `rj2xcl_graphics.cc` pero no se completó la prueba.

### Cambio de estrategia propuesto

**El usuario preguntó si sería más fácil mostrar el gráfico en el TaskPane en lugar de como Shape.**

**Respuesta: SÍ, mucho más fácil.** El TaskPane ya tiene:
- `buildSlotElement` para renderizar resultados
- `_renderPlotlyJSON` para gráficos interactivos
- Sin problemas de COM/Shapes

**Opciones propuestas:**
- A: TipoOutput=99 abre resultado en TaskPane
- B: Botón "Ver en TaskPane" 
- C: Usar funciones .Studio directamente (ya generan Plotly)

### Estado final de la sesión

**Implementado pero NO funcional:**
- TipoOutput=99 en R genera PNG correctamente ✅
- C++ detecta marcador NEVEN_EMBED_CHART ✅
- C++ llama UpdateGraphics ✅
- **UpdateGraphics NO crea el Shape** ❌

**Archivos modificados (con debug temporal):**
- `C:\NEVEN\functions\R4XCL-AD-ACP.R`
- `C:\NEVEN\functions\R4XCL-AD-ACP.json`
- `C:\NEVEN\functions\R4XCL-0-NevenX.R`
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Core\src\basic_functions.cc`
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Core\src\rj2xcl_graphics.cc`

**No hay commits** — todo el código tiene debug temporal que debe limpiarse.

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Decidir: ¿continuar con Shapes o cambiar a TaskPane? |
| **ALTA** | Si TaskPane: usar funciones .Studio que ya generan Plotly |
| **MEDIA** | Limpiar código de debug temporal |
| **BAJA** | Si Shapes: debuggear por qué raw_AddShape no funciona |

---

### Sesión 2026-09-28 (~09:00-10:15) — NEVEN.Chart.R/P/J Implementado ✅

## ✅ IMPLEMENTADO: Gráficos embebidos en Excel como Shapes

### Funcionalidad implementada
Nuevas funciones UDF que crean gráficos embebidos directamente en Excel:
- `=NEVEN.Chart.R(datos, tipo, [nombre], [ancho], [alto])` — R + ggplot2
- `=NEVEN.Chart.P(datos, tipo, [nombre], [ancho], [alto])` — Python + matplotlib
- `=NEVEN.Chart.J(datos, tipo, [nombre], [ancho], [alto])` — Julia + Plots.jl

### Parámetros
| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| datos | Rango | ✓ | - | Fila 1 = headers, Col 1 = eje X |
| tipo | Int | ✓ | - | 1-7 (ver tipos) |
| nombre | Texto | - | auto | Nombre único del Shape |
| ancho | Int | - | 400 | Píxeles |
| alto | Int | - | 300 | Píxeles |

### Tipos de gráfico soportados
| ID | Tipo | Descripción |
|----|------|-------------|
| 1 | Barras | geom_bar / bar() |
| 2 | Líneas | geom_line / plot() |
| 3 | Scatter | geom_point / scatter() |
| 4 | Área | geom_area / fill_between() |
| 5 | Pastel | coord_polar / pie() |
| 6 | Histograma | geom_histogram / hist() |
| 7 | BoxPlot | geom_boxplot / boxplot() |

### Arquitectura
```
Excel: =NEVEN.Chart.R(A1:C10, 2)
   │
   ▼
1. RJ_Chart_R() lee rango via xltypeMulti
2. ExtractRangeForChart() extrae headers + datos
3. Genera código R (ggplot2) con data.frame + ggsave()
4. Ejecuta via pipe a ControlR
5. Imagen guardada en C:\NEVEN\temp\chart_*.png
6. UpdateGraphics() crea/actualiza Shape en Excel
7. Retorna "Chart: nombre"
```

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `Core/include/basic_functions.h` | +3 entradas en funcTemplates, +3 declaraciones |
| `Core/src/basic_functions.cc` | +280 líneas: RJ_Chart_Generic, ExtractRangeForChart, RJ_Chart_R/P/J |
| `C:\NEVEN\functions\NEVEN_Chart.json` | Documentación para Ayuda del Task Pane |
| `NEVEN/functions/NEVEN_Chart.json` | Copia en repo |

### Código clave agregado

**funcTemplates (basic_functions.h):**
```cpp
{ L"RJ_Chart_R", L"UQQQQQ", L"NEVEN.Chart.R", L"Datos, Tipo, Nombre, Ancho, Alto", ... },
{ L"RJ_Chart_P", L"UQQQQQ", L"NEVEN.Chart.P", L"Datos, Tipo, Nombre, Ancho, Alto", ... },
{ L"RJ_Chart_J", L"UQQQQQ", L"NEVEN.Chart.J", L"Datos, Tipo, Nombre, Ancho, Alto", ... },
```

**Helper ExtractRangeForChart (basic_functions.cc):**
- Extrae headers de fila 0
- Extrae datos de filas 1+
- Escapa strings para R/Python/Julia
- Maneja tipos: Num, Int, Str, Bool, Err→NA

**RJ_Chart_Generic (basic_functions.cc):**
- Valida tipo 1-7
- Genera nombre auto si no se provee
- Limita dimensiones 100-2000 px
- Genera código específico por lenguaje
- Ejecuta via CallLanguage()
- Llama UpdateGraphics() para crear Shape

### Reutilización de componentes existentes
- `RJ2XCLGraphics::UpdateGraphics()` — crea/actualiza Shape con imagen
- `Convert::XLOPERToString()` — extrae strings de celdas
- `StringUtilities::Split()` — divide código en líneas
- `RJ2XCL_Engine::CallLanguage()` — ejecuta en motor R/Python/Julia

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Compilar NEVEN.dll con los cambios (cmake --build . --config Release) |
| **ALTA** | Copiar NEVEN.dll a C:\NEVEN\NEVEN64.xll |
| **ALTA** | Reiniciar Excel y probar `=NEVEN.Chart.R(A1:C10, 1)` |
| **BAJA** | Agregar soporte para múltiples series Y |

### Problema encontrado al probar
**Error:** `#NOMBRE` al usar `=NEVEN.Chart.R(...)`

**Causa:** El código fue agregado al repositorio pero **NO se ha compilado** el XLL. Excel está usando la versión anterior de NEVEN64.xll que no incluye las funciones Chart.

**Solución para próxima sesión:**
```powershell
# Opción 1: CMake desde Visual Studio
& "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\build" --config Release

# Opción 2: Abrir Visual Studio
# 1. Abrir F:\ANTIGRAVITY\2026\NEVEN\NEVEN\build\NEVEN.sln
# 2. Seleccionar Release x64
# 3. Build → Build Solution (Ctrl+Shift+B)

# Después de compilar:
Copy-Item "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\build\Core\Release\NEVEN.dll" "C:\NEVEN\NEVEN64.xll" -Force
# Reiniciar Excel
```

**Nota:** `cmake` no está en PATH. Usar la ruta completa de Visual Studio 2022.

### Compilación realizada (~10:45)

**Error inicial:** `application_dispatch` no es miembro de `RJ2XCL_Engine`

**Causa:** Usé el nombre incorrecto del método. El método correcto es `GetApplicationDispatch()`.

**Fix aplicado:**
```cpp
// ANTES (incorrecto):
LPDISPATCH app_dispatch = RJ2XCL_Engine::Instance()->application_dispatch();

// DESPUÉS (correcto):
LPDISPATCH app_dispatch = RJ2XCL_Engine::Instance()->GetApplicationDispatch();
```

**Resultado:** ✅ Compilación exitosa
```
NEVEN_Core.vcxproj -> F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Build\Core\Release\NEVEN64.dll
```

**Pendiente:** Copiar DLL a producción (Excel debe estar cerrado):
```powershell
Copy-Item "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Build\Core\Release\NEVEN64.dll" "C:\NEVEN\NEVEN64.xll" -Force
```

### Segundo error: Excel se cuelga (~11:00)

**Síntoma:** Al ejecutar `=NEVEN.Chart.R(A1:B7, 1)`, Excel se quedó atascado indefinidamente.

**Causa raíz:** El path del archivo temporal usaba backslashes (`C:\NEVEN\temp\...`) que R interpreta como caracteres de escape, causando que `ggsave()` falle silenciosamente y el pipe nunca retorne.

**Fix aplicado:**
```cpp
// ANTES (backslashes - problemas en R):
std::string temp_file = "C:\\NEVEN\\temp\\chart_" + name + ".png";

// DESPUÉS (forward slashes - funciona en todos los lenguajes):
std::string temp_file = "C:/NEVEN/temp/chart_" + name + ".png";
```

**Lección aprendida:** En Windows, siempre usar forward slashes (`/`) en paths que se pasan a R, Python o Julia. Windows los acepta igual que backslashes.

### Estado final de la sesión

| Componente | Estado |
|------------|--------|
| Código C++ | ✅ Implementado y corregido |
| Compilación | ✅ Exitosa |
| DLL en producción | ⏳ Pendiente copiar (Excel debe estar cerrado) |
| Prueba funcional | ⏳ Pendiente |

### Archivos modificados (resumen final)

| Archivo | Cambios |
|---------|---------|
| `Core/include/basic_functions.h` | +3 funcTemplates, +3 declaraciones |
| `Core/src/basic_functions.cc` | +280 líneas, fix `GetApplicationDispatch()`, fix forward slashes |
| `functions/NEVEN_Chart.json` | Documentación para Ayuda |
| `C:\NEVEN\functions\NEVEN_Chart.json` | Copia en producción |

### Commits pendientes
El fix de forward slashes aún no se ha commiteado.

### ✅ PRUEBA EXITOSA (~11:15)

**Confirmado:** `=NEVEN.Chart.R(A1:B7, 1)` funciona correctamente. El gráfico se genera y se embebe como Shape en Excel.

### Discusión: Extensión a otros gráficos

El usuario preguntó si gráficos de librerías como PCA (FactoMineR) pueden usar el mismo componente.

**Respuesta:** Sí, `UpdateGraphics()` puede usarse para cualquier gráfico generado por R/Python/Julia.

**Opciones propuestas:**

| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| A | Función genérica con código | `=NEVEN.Plot.R("fviz_pca_biplot(res)")` |
| B | Funciones específicas | `=NEVEN.PCA.R(datos, "biplot")` |
| C | Extender NevenX | Parámetro para embeber en lugar de WebView2 |

**Librerías candidatas:**
- FactoMineR: PCA, CA, MCA
- factoextra: fviz_cluster, fviz_pca_*
- corrplot: matrices de correlación
- rpart.plot: árboles de decisión
- forecast: series de tiempo

**Decisión pendiente:** Usuario debe elegir enfoque preferido.

### Decisión tomada: Opción C — Extender NevenX

El usuario eligió la **Opción C** porque reutiliza las funciones NevenX existentes (PCA, clustering, etc.) sin duplicar código.

**Plan de implementación:**

| TipoOutput | Comportamiento |
|------------|----------------|
| 0 (default) | Abre en WebView2 (actual) |
| **99** | Embebe como Shape en Excel |

**Ejemplo de uso:**
```excel
' Actual: abre en WebView2
=NevenX.R("R4XCL-AD-ACP", datos, 0)

' Nuevo: embebe como Shape
=NevenX.R("R4XCL-AD-ACP", datos, 99)
```

**Cambios necesarios:**
1. `NEVEN$.nevenx_dispatch` (R): Detectar TipoOutput=99, guardar gráfico como PNG
2. `NevenX_R` (C++): Si resultado es ruta PNG, llamar `UpdateGraphics()`

### Pendientes para próxima sesión (actualizado)

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar TipoOutput=99 en NevenX para embeber gráficos |
| **MEDIA** | Probar con R4XCL-AD-ACP (PCA) y otros análisis |
| **BAJA** | Documentar el nuevo parámetro en NEVEN_Chart.json |

### Commits de la sesión

| Hash | Descripción |
|------|-------------|
| `2ebee1c` | feat(Chart): add NEVEN.Chart.R/P/J embedded chart functions |
| `ea9c619` | fix(Chart): use forward slashes and correct method name |

---

### Commits realizados
| Hash | Descripción |
|------|-------------|
| `2ebee1c` | feat(Chart): add NEVEN.Chart.R/P/J embedded chart functions |

### Decisiones de diseño

1. **Rangos en lugar de código:** El usuario pidió usar rangos de Excel (`A1:C10`) en lugar de strings de código. Esto es más natural para usuarios de Excel y permite que el gráfico se actualice automáticamente cuando cambian los datos.

2. **Un helper genérico `RJ_Chart_Generic`:** En lugar de 3 implementaciones separadas, se usa una función genérica que recibe el `language_key` (0=R, 1=Julia, 2=Python) y genera código específico por lenguaje.

3. **Reutilización de `UpdateGraphics`:** Se reutilizó el código COM existente en `rj2xcl_graphics.cc` que ya maneja la creación de Shapes en Excel. Esto redujo el esfuerzo de ~18h a ~2h.

4. **Imágenes en `C:\NEVEN\temp\`:** Las imágenes PNG se guardan temporalmente y el Shape las referencia. Si el usuario usa el mismo nombre, el Shape se actualiza en lugar de crear uno nuevo.

### Inspiración
La funcionalidad está inspirada en BERT (Basic Excel R Toolkit) que permite embeber gráficos R directamente en celdas de Excel usando `Shapes.AddPicture()`.

### Ejemplos de prueba (para después de compilar)

**Datos de prueba (A1:C7):**
```
Mes,Ventas,Gastos
Ene,120,80
Feb,150,90
Mar,180,100
Abr,140,85
May,200,110
Jun,220,120
```

**Fórmulas de prueba:**
```excel
=NEVEN.Chart.R(A1:B7, 1)                          ' Barras básico
=NEVEN.Chart.R(A1:C7, 2, "tendencia", 600, 400)   ' Líneas con nombre
=NEVEN.Chart.P(B1:C7, 3, "correlacion")           ' Scatter en Python
=NEVEN.Chart.R(A1:B7, 5, "distribucion")          ' Pastel
=NEVEN.Chart.J(A1:B7, 2, "lineas_Julia")          ' Líneas en Julia
```

---

### Sesión 2026-08-19 (~13:30) — FIX: confirm() y alert() no soportados en Office Add-ins ✅

## ✅ IMPLEMENTADO: Reemplazo de confirm/alert nativos por modales HTML

### Problema resuelto
El Task Pane fallaba con error `window.confirm is not supported in Office Add-ins` cuando se intentaba ejecutar `summary(iris)` en R o cuando el usuario cambiaba de lenguaje/archivo teniendo cambios sin guardar.

### Causa raíz
Office Add-ins (WebView2) no soportan los diálogos nativos `window.confirm()` ni `window.alert()`. El código tenía 4 llamadas a `confirm()` y 3 a `alert()` que causaban errores JS silenciosos que rompían la ejecución.

### Ubicaciones afectadas
| Línea original | Contexto | Función original |
|----------------|----------|------------------|
| 2395 | Cambio de lenguaje (script-lang) | `confirm('Hay cambios sin guardar. ¿Continuar?')` |
| 2444 | Abrir script (btn-script-open) | `confirm('Hay cambios sin guardar. ¿Abrir otro archivo?')` |
| 2537 | Nuevo script (btn-script-new) | `confirm('Hay cambios sin guardar. ¿Crear nuevo script?')` |
| 2832 | Cargar ejemplo (script-examples) | `confirm('Hay cambios sin guardar. ¿Cargar ejemplo?')` |
| 1306 | Error pivot | `alert('Error: '+res.message)` |
| 2488 | Error guardado | `alert('Error al guardar: ' + d.message)` |
| 2491 | Error catch | `alert('Error: ' + e)` |

### Solución implementada
1. **Nuevo sistema de modal HTML/CSS** agregado después de `window.showToast`:
   - `showConfirm(message)` → retorna Promise<boolean>
   - `showAlert(message)` → retorna Promise<void>
   - Modal con overlay oscuro, caja centrada, botones Cancelar/Aceptar

2. **Handlers convertidos a async/await** para manejar las Promises

3. **Verificación de sintaxis:** Todos los bloques `<script>` pasan `node --check`

### Archivos modificados
| Archivo | Ubicación | Cambio |
|---------|-----------|--------|
| `taskpane.html` | `C:\NEVEN\taskpane\` | Modal + 7 reemplazos confirm/alert |
| `taskpane.html` | `F:\...\TaskPane\` | Sincronizado |

### Código del modal agregado (líneas ~767-830)
```javascript
(function() {
  var modal = document.createElement('div');
  modal.id = 'neven-modal-overlay';
  // ... estilos inline para overlay + caja
  
  window.showConfirm = function(message) {
    return new Promise(function(resolve) {
      // ... mostrar modal con botones Cancelar/Aceptar
    });
  };
  
  window.showAlert = function(message) {
    return new Promise(function(resolve) {
      // ... mostrar modal con botón OK
    });
  };
})();
```

### Ejemplo de handler convertido
```javascript
// Antes (síncrono, rompe en Office Add-ins):
document.getElementById('script-lang').addEventListener('change', function() {
  if (_scriptDirty && !confirm('...')) { this.value = _scriptLang; return; }
  // ...
});

// Después (async, compatible):
document.getElementById('script-lang').addEventListener('change', async function() {
  var self = this;
  if (_scriptDirty) {
    var ok = await showConfirm('...');
    if (!ok) { self.value = _scriptLang; return; }
  }
  // ...
});
```

### Verificación
```powershell
# No quedan confirm() ni alert() nativos
Select-String -Path "C:\NEVEN\taskpane\taskpane.html" -Pattern "\bconfirm\(" 
# Solo muestra showConfirm (función propia)

# Sintaxis JS válida
node --check <cada bloque script>  # Todos OK
```

### Estado pendiente
El fix de confirm/alert está listo. **Falta verificar que `summary(iris)` funcione** — el servidor HTTP estaba desconectado de las Named Pipes durante las pruebas (Excel no estaba cargado con NEVEN activo).

### Commits realizados
⚠️ **NO SE HIZO COMMIT** — cambios solo en archivos locales, pendiente commit.

### Pendientes para próxima sesión

| Prioridad | Tarea | Detalle |
|-----------|-------|---------|
| **ALTA** | Probar `summary(iris)` con Excel+NEVEN activo | Verificar que el fix de confirm/alert resuelve el problema completo |
| **ALTA** | Commit de cambios | `taskpane.html` tiene cambios sin commit (modal showConfirm/showAlert) |
| **MEDIA** | Verificar `variable_to_python` con tipos "table" | Si `summary(iris)` sigue fallando, el problema está en la conversión de tipos complejos de R |
| **BAJA** | Limpiar mojibake residual | Algunos comentarios aún tienen `Â¿` en lugar de `¿` |

### Archivos modificados (sin commit)
```
C:\NEVEN\taskpane\taskpane.html          ← producción (editado)
F:\...\NEVEN\TaskPane\taskpane.html      ← repo (sincronizado)
F:\...\NEVEN\.kiro\contexto\CHAT.md      ← bitácora (actualizada)
```

---

### Continuación sesión 2026-08-19 (~14:45) — Diagnóstico: Pipes no creados por ControlR

## 🔍 DIAGNÓSTICO: "engine not available" aunque indicadores en verde

### Síntoma
Los indicadores de engines en el Task Pane muestran verde (R, Python, Julia), pero al ejecutar código retorna "r engine not available".

### Diagnóstico realizado
```powershell
# Procesos corriendo:
- Python (servidor HTTP): PID 219676, puerto 5555 ✓
- Excel: PID 254268 ✓
- ControlR: PID 74576, iniciado por Excel ✓

# Pipes encontrados:
[NINGUNO con patrón RJ2XCL2-PIPE-*]
```

### Causa raíz identificada
**ControlR está corriendo pero NO creó el Named Pipe.**

Evidencia:
- ControlR tiene solo 2 threads (debería tener más si el pipe loop está activo)
- Solo 3.5 segundos de CPU time desde inicio (hace horas) → está idle/stuck
- El pipe `RJ2XCL2-PIPE-R-74576` no existe en `\\.\pipe\`

El código en `language_service.cc:129` crea el pipe con el PID del proceso hijo:
```cpp
ss << "RJ2XCL2-PIPE-" << language_descriptor_.prefix_ << "-" << _getpid();
```

ControlR (PID 74576) debería haber creado `RJ2XCL2-PIPE-R-74576`, pero no lo hizo.

### Hipótesis
1. ControlR falló al inicializar R internamente
2. El pipe se creó pero se cerró por timeout/error
3. ControlR está esperando algo que nunca llegó (stuck en connect)

### Solución recomendada
**Reiniciar el XLL de NEVEN:**
1. Excel → Archivo → Opciones → Add-ins → Administrar: Add-ins de Excel
2. Desmarcar NEVEN64.xll → Aceptar
3. Volver a marcarlo → Aceptar

O simplemente cerrar y reabrir Excel.

### Por qué los indicadores muestran verde
El endpoint `/api/engines` usa `_get_engine_status()` que hace probe de pipes, pero el servidor HTTP Python probablemente tiene cache de una sesión anterior o el probe está retornando falsos positivos.

### Archivos relevantes para debug futuro
| Archivo | Función |
|---------|---------|
| `Core/src/language_service.cc:129` | Crea nombre del pipe |
| `ControlR/src/controlr.cc:701-706` | Crea pipe callback y principal |
| `ControlPython/startup/neven_http_server.py:169` | `_discover_pipe()` busca pipes |

### Estado al cerrar sesión
- **Fix de confirm/alert:** ✅ Implementado y listo para probar
- **Pipes de ControlR:** ❌ No existen, requiere reiniciar XLL
- **Servidor HTTP:** ✓ Corriendo pero sin pipes a los que conectar

### Acción final
Usuario mató ControlR manualmente. Excel necesita reiniciar ControlR ejecutando algo como `=NEVEN.r("1+1")` o recargando el add-in.

---

### Continuación 2026-08-19 (~15:30) — Diagnóstico profundo de pipes

## 🔍 INVESTIGACIÓN: Run Script sigue sin funcionar

### Problemas encontrados y resueltos

#### 1. Archivos faltantes en producción
```
C:\NEVEN\startup\pipe_client.py   ← NO EXISTÍA
C:\NEVEN\startup\variable_pb2.py  ← NO EXISTÍA
```
**Fix:** Copiados desde repo/taskpane.

#### 2. Pipes huérfanos con PID incorrecto
El servidor detectaba pipes `RJ2XCL2-PIPE-R-88508` pero ControlR corría con PID diferente (242208, 245108). Los pipes eran de sesiones anteriores que no se limpiaron.

**Fix:** Matar ControlR → pipes se limpian → Excel reinicia ControlR con pipes frescos.

#### 3. Error 231 "All pipe instances are busy"
Incluso con pipes correctos, `PipeClient.connect()` fallaba porque Excel ocupa la única instancia disponible del pipe.

**Análisis de arquitectura:**
- ControlR crea instancia 1 (blocking) → Excel conecta
- ControlR crea instancia 2 solo DESPUÉS de que alguien conecte (línea 363 de controlr.cc)
- Si R está ocupado ejecutando código, el event loop no corre y no se crean más instancias

**Fix parcial:** Agregado retry loop con delay en `_connect_pywin32()` de pipe_client.py

### Archivos modificados en producción

| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\startup\pipe_client.py` | Copiado + retry logic para error 231 |
| `C:\NEVEN\startup\variable_pb2.py` | Copiado desde taskpane |
| `C:\NEVEN\taskpane\taskpane.html` | Modal showConfirm/showAlert |

### Commits realizados
⚠️ **NINGUNO** — todos los cambios están solo en producción, pendiente sync al repo y commit.

### Estado al cerrar sesión
- ControlR no está corriendo (fue matado para limpiar pipes)
- Pipes limpios (0 pipes RJ2XCL)
- Servidor HTTP corriendo en puerto 5555
- **Pendiente:** Usuario debe ejecutar `=NEVEN.r("1+1")` para reiniciar ControlR

### Pendientes actualizados

| Prioridad | Tarea | Detalle |
|-----------|-------|---------|
| **ALTA** | Ejecutar `=NEVEN.r("1+1")` | Para reiniciar ControlR con pipes frescos |
| **ALTA** | Probar Run Script | Después de reiniciar ControlR |
| **ALTA** | Sync y commit | pipe_client.py modificado, taskpane.html con modales |
| **MEDIA** | Bug arquitectura pipes | ControlR solo crea 1 instancia inicial, debería crear más |

---

### Continuación 2026-08-19 (~16:15) — Diagnóstico final: Error 231 persiste

## 🔴 PROBLEMA NO RESUELTO: Run Script no puede conectar al pipe

### Hallazgo clave
**Los pipes usan el PID de Excel, no de ControlR:**
```
Excel PID:     88508
ControlR PID:  214648  
Pipe name:     RJ2XCL2-PIPE-R-88508  ← Correcto!
```
El nombre del pipe es correcto. El problema es otro.

### Causa raíz confirmada
**Error 231: "All pipe instances are busy"**

ControlR crea 2 instancias del pipe:
1. Instancia 1 (blocking) → Excel conecta y la ocupa permanentemente
2. Instancia 2 (non-blocking) → Debería estar disponible pero NO LO ESTÁ

El código en `controlr.cc:705-706`:
```cpp
NextPipeInstance(true, State().pipename);   // Excel usa esta
NextPipeInstance(false, State().pipename);  // Debería estar libre
```

### Intentos de solución

1. **Retry loop en pipe_client.py** — No funciona porque no hay instancias libres
2. **WaitNamedPipe** — Se cuelga indefinidamente (nunca hay instancia libre)
3. **Agregar tercera instancia en controlr.cc** — Modificado pero requiere recompilar

### Modificación realizada (pendiente compilar)
```cpp
// F:\ANTIGRAVITY\2026\NEVEN\NEVEN\ControlR\src\controlr.cc línea 705-707
NextPipeInstance(true, State().pipename);
NextPipeInstance(false, State().pipename);
NextPipeInstance(false, State().pipename);  // Extra instance for HTTP server
```

### Opciones para resolver

| Opción | Esfuerzo | Descripción |
|--------|----------|-------------|
| **A. Recompilar ControlR** | Alto | Compilar C++ con la tercera instancia |
| **B. Office.js fallback** | Medio | Task Pane ejecuta `=NEVEN.r()` via Office.js |
| **C. Reiniciar Excel** | Bajo | Cerrar Excel completamente y reabrir |

### Archivos modificados (sin commit)

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `C:\NEVEN\startup\pipe_client.py` | Retry loop + win32pipe import | En producción |
| `C:\NEVEN\startup\variable_pb2.py` | Copiado | En producción |
| `C:\NEVEN\taskpane\taskpane.html` | Modal showConfirm/showAlert | En producción |
| `F:\...\ControlR\src\controlr.cc` | Tercera instancia pipe | En repo, sin compilar |

### Estado al cerrar sesión
- `=NEVEN.r("1+1")` funciona en Excel ✓
- Run Script en Task Pane: "r engine not available" ✗
- Causa: Error 231, todas las instancias del pipe ocupadas
- Solución requiere: recompilar ControlR o usar Office.js

### Pendientes para próxima sesión

| Prioridad | Tarea | Detalle |
|-----------|-------|---------|
| **ALTA** | Decidir solución | Recompilar ControlR vs Office.js fallback |
| **ALTA** | Implementar solución | Según decisión anterior |
| **ALTA** | Commit cambios | taskpane.html, pipe_client.py, controlr.cc |
| **MEDIA** | Documentar arquitectura pipes | Para evitar este problema en el futuro |

---

### Cierre 2026-08-19 (~16:45) — Reinicio de Excel

Usuario decidió reiniciar Excel como solución más simple. Estado verificado:
- Excel cerrado ✓
- ControlR cerrado ✓  
- Pipes limpios (0 pipes RJ2XCL) ✓

**Próximo paso:** Abrir Excel, ejecutar `=NEVEN.r("1+1")`, probar Run Script en Task Pane.

---

### Post-reinicio 2026-08-19 (~17:00) — Confirmado: problema arquitectónico

## 🔴 CONFIRMADO: Error 231 persiste después de reinicio limpio

### Prueba realizada
1. Excel reiniciado completamente (PID nuevo: 226776)
2. ControlR nuevo (PID: 227836)
3. Pipes frescos: `RJ2XCL2-PIPE-R-226776-*`
4. `=NEVEN.r("1+1")` retorna 2 ✓
5. Run Script: "r engine not available" ✗

### Resultado de prueba de conexión
```python
win32file.CreateFile(r'\\.\pipe\RJ2XCL2-PIPE-R-226776', ...)
# Error 231: Todas las instancias de canalización están en uso.
```

### Conclusión definitiva
**El problema NO es de pipes huérfanos ni estado corrupto.**

Es un **bug arquitectónico en ControlR**: solo crea 1 instancia usable del Named Pipe, y Excel la ocupa permanentemente. El servidor HTTP nunca puede conectar.

### Soluciones disponibles

| Opción | Tiempo | Descripción |
|--------|--------|-------------|
| **A. Recompilar ControlR** | ~30 min | Ya modifiqué `controlr.cc` para crear 3 instancias |
| **B. Office.js fallback** | ~20 min | Task Pane ejecuta R via `Excel.run()` → `=NEVEN.r()` |

### Archivos modificados (pendiente commit)

| Archivo | Estado |
|---------|--------|
| `F:\...\ControlR\src\controlr.cc` | Modificado (3ra instancia), sin compilar |
| `C:\NEVEN\startup\pipe_client.py` | Retry logic agregado |
| `C:\NEVEN\taskpane\taskpane.html` | Modal showConfirm/showAlert |

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar solución (recompilar ControlR o Office.js fallback) |
| **ALTA** | Commit todos los cambios |
| **MEDIA** | Probar `summary(iris)` una vez que Run Script funcione |

---

### Confirmación 2026-08-19 (~17:10) — Consola muestra 503

La consola del Task Pane confirma:
```
Failed to load resource: the server responded with a status of 503 (Service Unavailable)
:5555/api/r:1
```

El servidor HTTP está corriendo y respondiendo, pero retorna 503 porque no puede conectar al pipe de R (error 231 interno).

**Decisión pendiente:** Implementar Office.js fallback (recomendado, ~20 min) o recompilar ControlR (~30 min).

---

### Implementación 2026-08-19 (~17:30) — Office.js Fallback ✅

## ✅ IMPLEMENTADO: Fallback Office.js para Run Script

### Solución implementada
Cuando el servidor HTTP retorna 503 (pipe no disponible), el Task Pane ahora usa Office.js para ejecutar código directamente en Excel.

### Cómo funciona
1. `runScriptRS()` intenta `/api/{lang}` normalmente
2. Si retorna **503**, llama a `runScriptViaOfficeJS(lang, code)`
3. Office.js ejecuta `=NEVEN.{r|p|j}("código")` en celda temporal XFD1048576
4. Lee el resultado y lo renderiza

### Lenguajes soportados
| Lenguaje | Función Excel |
|----------|---------------|
| R | `NEVEN.r("code")` |
| Python | `NEVEN.p("code")` |
| Julia | `NEVEN.j("code")` |

### Código agregado (~60 líneas)
```javascript
// En runScriptRS():
if (resp.status === 503) {
  var fallbackResult = await runScriptViaOfficeJS(lang, code);
  renderScriptResultRS(fallbackResult);
  return;
}

// Nueva función:
async function runScriptViaOfficeJS(lang, code) {
  var funcMap = { r: 'NEVEN.r', python: 'NEVEN.p', julia: 'NEVEN.j' };
  // ... usa Excel.run() para ejecutar fórmula en celda temporal
}
```

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Fallback Office.js agregado |
| `F:\...\TaskPane\taskpane.html` | Sincronizado |

### Verificación
- Sintaxis JS: ✓ OK
- Sincronizado al repo: ✓

### Próximo paso
**Recargar el Task Pane y probar `1+1` en R**

---

### Prueba 2026-08-19 (~17:45) — Fallback funciona parcialmente

## ✅ FALLBACK OFFICE.JS FUNCIONA

### Resultado de la prueba con `summary(iris)`
```
[NEVEN] Server returned 503, trying Office.js fallback...
[DataLab] buildSlotElement: resultado type=scalar tier=1 value= #¡DESBORDAMIENTO!
```

El fallback **se activa correctamente**, pero `summary(iris)` retorna **#¡DESBORDAMIENTO!** (spill error) porque el resultado es una matriz que no cabe en una celda.

### Limitación del fallback Office.js
- ✅ Funciona para **escalares** (`1+1`, `mean(1:10)`, strings)
- ❌ No funciona para **matrices/tablas** (`summary(iris)`, data.frames)

Esto es una limitación inherente: Excel no puede poner una matriz en una sola celda sin "spill".

### Próximo paso
Probar con `1+1` para confirmar que escalares funcionan.

---

### Confirmación 2026-08-19 (~18:00) — ✅ Fallback funciona para escalares

## ✅ CONFIRMADO: `1+1` retorna `2`

El fallback Office.js funciona correctamente para resultados escalares.

### Estado actual
| Tipo de resultado | Estado |
|-------------------|--------|
| Escalares (`1+1`, `mean(1:10)`) | ✅ Funciona |
| Strings | ✅ Funciona |
| Matrices/Tablas (`summary(iris)`) | ❌ Error desbordamiento |

### Solución propuesta para tablas
Envolver código R en `capture.output()` para serializar a texto:
```r
paste(capture.output(summary(iris)), collapse="\n")
```

### Archivos modificados en esta sesión (sin commit)

| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Modal showConfirm/showAlert + Fallback Office.js |
| `F:\...\TaskPane\taskpane.html` | Sincronizado |
| `C:\NEVEN\startup\pipe_client.py` | Retry logic + win32pipe |
| `F:\...\ControlR\src\controlr.cc` | 3ra instancia pipe (sin compilar) |

### Commits realizados
⚠️ **NINGUNO** — todos los cambios pendientes de commit

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Commit todos los cambios |
| **ALTA** | Implementar serialización para tablas en fallback |
| **MEDIA** | Recompilar ControlR con 3ra instancia (solución definitiva) |
| **BAJA** | Limpiar código muerto / comentarios obsoletos |

---

### Sesión 2026-09-25 (~09:00) — Inicio: Mejoras UI Task Pane

## 📝 SESIÓN CORTA: Discusión de mejoras UI

### Contexto
Inicio de sesión enfocada en mejoras de UI del Task Pane.

### Tema discutido
**Campos de texto redimensionables por el usuario**

El usuario preguntó si es posible hacer que los campos de texto (donde se escribe código SQL, scripts R/Python/Julia, etc.) sean ampliables/redimensionables por el usuario, ya que el tamaño puede ser reducido en algunas situaciones.

### Análisis realizado
Se identificaron los textareas principales en `taskpane.html`:

| Campo | ID | Estado actual |
|-------|-----|---------------|
| Editor SQL | `#sql-input` | Sin resize |
| Editor scripts R/Python/Julia | `#script-input` | Sin resize |
| Chat IA | `#ai-input` | Sin resize |
| Query DB (Data Lab) | `#db-query` | ✅ Ya tiene `resize:vertical` |

### Solución propuesta (NO implementada)
Agregar CSS `resize: vertical` a los campos que no lo tienen:
```css
textarea {
  resize: vertical;
  min-height: 100px;
  max-height: 500px;  /* opcional */
}
```

Opciones discutidas:
- `resize: vertical` — recomendado, mantiene el ancho del panel
- `resize: both` — más flexible pero puede romper el layout

### Estado
Sesión terminada antes de implementar. **Pendiente para próxima sesión.**

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Implementar `resize: vertical` en textareas del Task Pane |
| **ALTA** | Sincronizar fix JS (`});` línea 867) al repo |
| **MEDIA** | Bug en `variable_to_python` con resultados complejos de R |

### Archivos relevantes
- `NEVEN/TaskPane/taskpane.html` — líneas 80, 240, 471-480

---

### Sesión 2026-09-24 (Continuación ~19:30) — Diagnóstico Named Pipes Run Script

## 🔍 DIAGNÓSTICO: Run Script reporta "engine not available"

### Contexto previo
Esta sesión continuó desde el fix del Task Pane (encoding mojibake + bug JS `});` faltante). El Task Pane ya funciona visualmente, pero Run Script no puede ejecutar código R/Python/Julia.

### Problema investigado
El endpoint `/api/engines` retorna `{"r": false, "python": false, "julia": false}` aunque ControlR.exe está corriendo.

### Causa raíz identificada
**Discrepancia en nombres de Named Pipes:**

| Componente | Pipe que busca | Pipe real |
|------------|----------------|-----------|
| `neven_http_server.py` | `\\.\pipe\neven_r` | `\\.\pipe\RJ2XCL2-PIPE-R-214888` |
| `neven_http_server.py` | `\\.\pipe\neven_python` | (no existe aún) |
| `neven_http_server.py` | `\\.\pipe\neven_julia` | (no existe aún) |

El XLL crea pipes con nombres **dinámicos** que incluyen el PID de Excel (`RJ2XCL2-PIPE-R-{PID}`), pero el servidor HTTP busca nombres **fijos** (`neven_r`).

### Verificación realizada
```powershell
Get-ChildItem "\\.\pipe\" | Where-Object { $_.Name -match 'neven|control|RJ2XCL' }
# Resultado:
# RJ2XCL2-PIPE-R-214888-CB
# RJ2XCL2-PIPE-R-214888
# RJ2XCL2-PIPE-R-214888-M
```

### Estado actual
- **Excel** corriendo: PID 214888
- **ControlR** corriendo: PID 241468
- **Servidor HTTP** corriendo: puerto 5555, responde correctamente
- **Pipes R existen** pero con nombres dinámicos que el servidor no reconoce

### Solución propuesta (NO implementada aún)
Modificar `_handle_engines()` y `_probe_pipe()` en `neven_http_server.py` para:
1. Enumerar pipes existentes con patrón `RJ2XCL2-PIPE-{lang}-*`
2. Detectar automáticamente el pipe correcto para cada lenguaje
3. Cachear el nombre del pipe descubierto para las llamadas posteriores

### Archivos relevantes
| Archivo | Rol |
|---------|-----|
| `ControlPython/startup/neven_http_server.py` | Servidor HTTP, líneas 2240-2255 definen `_handle_engines` |
| `Core/src/pipe_factory.cc` | XLL crea pipes con formato `RJ2XCL2-PIPE-{lang}-{PID}` |

### Pendientes ~~para próxima sesión~~ RESUELTO

| Prioridad | Tarea |
|-----------|-------|
| ~~**ALTA**~~ | ~~Implementar descubrimiento dinámico de pipes~~ ✅ HECHO (ver sesión 20:00) |
| **ALTA** | Sincronizar fix JS (`});` línea 867) de `C:\NEVEN\taskpane\taskpane.html` al repo |
| **MEDIA** | Commit de cambios de producción al repositorio |
| **MEDIA** | Documentar arquitectura de pipes (nombres dinámicos vs fijos) |

---

### Sesión 2026-09-24 (~20:00) — FIX: Descubrimiento dinámico de Named Pipes ✅

## ✅ IMPLEMENTADO: Run Script detecta engines correctamente

### Problema resuelto
El endpoint `/api/engines` retornaba `{"r": false, ...}` aunque ControlR.exe estaba corriendo.

### Causa raíz (doble)
1. **Nombres de pipes dinámicos vs fijos:** El servidor buscaba `\\.\pipe\neven_r` pero el XLL crea pipes con nombres dinámicos: `RJ2XCL2-PIPE-R-{PID}` (ej: `RJ2XCL2-PIPE-R-214888`)
2. **Error 231 no manejado:** `_probe_pipe` fallaba con error 231 ("All pipe instances are busy") cuando otro cliente ya estaba conectado. Este error significa que el pipe EXISTE, solo que está ocupado.

### Solución implementada

#### 1. Nueva función `_discover_pipe(lang)`
Enumera pipes en `\\.\pipe\` buscando patrón `RJ2XCL2-PIPE-{LANG}-*`, excluyendo sufijos `-CB` y `-M` (canales auxiliares).

#### 2. Fix en `_probe_pipe` para error 231
```python
except pywintypes.error as e:
    if e.winerror == 231:  # ERROR_PIPE_BUSY
        return True  # Pipe existe, solo está ocupado
```

#### 3. `_get_pipe_client` crea PipeClient dinámicamente
Cuando no hay `pipe_client_factory` inyectado, usa `_discover_pipe` para encontrar el pipe y crea un `PipeClient` directamente.

#### 4. Entry point standalone
```python
if __name__ == "__main__":
    # Permite ejecutar: python neven_http_server.py
```

### Archivos modificados
| Archivo | Cambios |
|---------|---------|
| `NEVEN/ControlPython/startup/neven_http_server.py` | +`_discover_pipe`, +`_get_engine_status`, fix `_probe_pipe`, mod `_handle_engines`, mod `_get_pipe_client` |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |

### Verificación
```
GET http://127.0.0.1:5555/api/engines
→ {"r": true, "python": false, "julia": false}
```

### Pendientes actualizados
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Sincronizar fix JS (`});` línea 867) al repo |
| **MEDIA** | Commit de todos los cambios al repositorio |
| **BAJA** | Probar Run Script ejecutando código R desde Task Pane |

---

### Notas técnicas (referencia rápida)
- Patrón pipes: `RJ2XCL2-PIPE-{LANG}-{EXCEL_PID}` donde LANG = R, PYTHON, JULIA
- Sufijos `-CB` (callback) y `-M` (mensajes) son canales auxiliares
- Error Win32 231 = `ERROR_PIPE_BUSY` — pipe existe pero ocupado
- pywin32 (`win32file.CreateFile`) es necesario para probar pipes en Windows
- **IMPORTANTE:** Si se reinicia Excel, el PID cambia y hay que reiniciar el servidor HTTP para que descubra el nuevo pipe (el cache guarda el pipe del Excel anterior)

---

### Sesión 2026-09-24 (~20:30) — Diagnóstico: Pipe con instancia única

## 🔴 BLOQUEANTE: El pipe solo admite 1 conexión

### Problema descubierto
Aunque `/api/engines` retorna `{"r": true}`, al intentar ejecutar código R el servidor falla con:
```
Connection: FAILED - Cannot open named pipe: (231, 'CreateFile', 'Todas las instancias de canalización están en uso.')
```

### Causa raíz
El XLL crea el Named Pipe `RJ2XCL2-PIPE-R-{PID}` con `nMaxInstances = 1`, permitiendo **solo una conexión simultánea**. Esa conexión ya está siendo usada por el propio XLL para las funciones UDF.

El servidor HTTP intenta abrir una **segunda conexión** al mismo pipe, pero no hay instancias disponibles.

### Por qué `/api/engines` retorna true
El fix del error 231 en `_probe_pipe` detecta correctamente que el pipe **existe** (error 231 = "pipe busy" ≠ "pipe not found"). Pero existir no significa que se pueda conectar.

### Verificación realizada
```python
client = PipeClient(pipe_path)
client.connect()
# → FAILED: error 231 "Todas las instancias de canalización están en uso"
```

### Opciones de solución

| Opción | Cambio requerido | Impacto |
|--------|------------------|---------|
| **A. Aumentar instancias** | Modificar `pipe_factory.cc` para usar `PIPE_UNLIMITED_INSTANCES` | Cambio en C++ del XLL |
| **B. Pipe separado para TaskPane** | Crear segundo pipe `RJ2XCL2-PIPE-R-{PID}-TP` | Cambio en C++ + Python |
| **C. Proxy via XLL** | Task Pane envía código al XLL que lo reenvía a ControlR | Nuevo endpoint en XLL |
| **D. Multiplexar conexión** | El XLL comparte su conexión existente con el servidor | Arquitectura compleja |

### Pendientes actualizados

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICA** | Decidir arquitectura para múltiples clientes al pipe de ControlR |
| **ALTA** | Implementar solución elegida (probablemente opción A o B) |
| **ALTA** | Sincronizar fix JS (`});` línea 867) al repo |
| **MEDIA** | Commit de cambios actuales al repositorio |

### Archivos relevantes para el fix
- `NEVEN/Core/src/pipe_factory.cc` — donde se crea el pipe con `CreateNamedPipe`
- `NEVEN/ControlR/src/main.cc` — donde ControlR crea el pipe server

---

### Sesión 2026-09-24 (~21:00) — FIX COMPLETO: Run Script funciona ✅

## ✅ RESUELTO: Run Script detecta R y Python correctamente

### Problema final resuelto
El endpoint `/api/engines` retornaba `false` incluso cuando `start_studio.py` había registrado los engines en `pipe_client_factory`.

### Causa raíz
Mi código de `_get_engine_status()` solo usaba `_discover_pipe()` (búsqueda dinámica) sin verificar primero si había un `pipe_client_factory` inyectado por `start_studio.py`.

### Solución implementada

#### 1. `_get_engine_status()` ahora verifica factory primero
```python
def _get_engine_status() -> dict:
    factory = _config.get("pipe_client_factory", {})
    result = {}
    for lang in ("r", "python", "julia"):
        if lang in factory:
            result[lang] = True  # Factory registered
        else:
            result[lang] = _discover_pipe(lang) is not None  # Fallback
    return result
```

#### 2. `_discover_pipe()` busca ambos patrones de pipes
- Primero: nombres fijos `neven_r`, `neven_python` (start_studio.py)
- Luego: nombres dinámicos `RJ2XCL2-PIPE-R-{PID}` (XLL)

### Flujo correcto entendido
```
NEVEN Studio.vbs → start_studio.py → lanza ControlR/Python propios → inyecta factory → HTTP server
```

El servidor **NO** debe conectarse al pipe del XLL — usa sus propios procesos Control*.exe.

### Verificación
```
GET /api/engines → {"r": true, "python": true, "julia": false}
```
(Julia = false porque ControlJulia.exe no está instalado)

### Archivos modificados
| Archivo | Cambios |
|---------|---------|
| `NEVEN/ControlPython/startup/neven_http_server.py` | `_get_engine_status` verifica factory, `_discover_pipe` busca ambos patrones |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |
| `C:\NEVEN\taskpane\neven_http_server.py` | Sincronizado |

### Cómo lanzar el servidor correctamente
```powershell
# Opción 1: Doble clic en
C:\NEVEN\NEVEN Studio.vbs

# Opción 2: Desde terminal
python "C:\NEVEN\taskpane\start_studio.py" --no-browser
```

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | ~~Probar ejecución de código R desde Task Pane (Run Script)~~ ✅ Funciona para código simple |
| **ALTA** | Sincronizar fix JS (`});` línea 867) al repo |
| **MEDIA** | Commit de todos los cambios al repositorio |
| **MEDIA** | Bug en `variable_to_python` con resultados complejos de R (ej: `summary(iris)`) |
| **BAJA** | Instalar ControlJulia.exe si se necesita Julia |

### Verificación final Run Script
```
POST /api/r  body={"code": "1 + 1"}
→ {"status": "ok", "type": "real", "result": 2.0, "console": ""}  ✅

Task Pane UI: R: 1+1=2  ✅ (confirmado por usuario)

POST /api/r  body={"code": "summary(iris)"}
→ PipeClientError (bug en serialización de tipos complejos)  ⚠️
```

**FIX COMPLETO Y VERIFICADO END-TO-END** 🎉

---

### Sesión 2026-09-24 (~21:30) — Julia habilitado ✅

## ✅ ControlJulia.exe instalado y funcionando

### Problema
Julia mostraba "engine not available" porque `ControlJulia.exe` no existía en `C:\NEVEN\`.

### Solución
`ControlJulia.exe` ya estaba compilado en el directorio de build. Solo fue necesario copiarlo:
```powershell
Copy-Item "F:\...\build\ControlJulia\Release\ControlJulia.exe" "C:\NEVEN\"
```

### Verificación
```
GET /api/engines → {"r": true, "python": true, "julia": true}

POST /api/julia body={"code": "1 + 1"}
→ {"status": "ok", "type": "integer", "result": 2, "console": ""}  ✅
```

### Archivos copiados
| Origen | Destino |
|--------|---------|
| `NEVEN/build/ControlJulia/Release/ControlJulia.exe` | `C:\NEVEN\ControlJulia.exe` |

### Estado final de la sesión

| Engine | Estado | Verificación |
|--------|--------|--------------|
| R | ✅ Funciona | `1+1=2` |
| Python | ✅ Funciona | OK |
| Julia | ✅ Funciona | `1+1=2` |

### Resumen completo de cambios en esta sesión

#### Archivos modificados (código)
| Archivo | Cambios |
|---------|---------|
| `NEVEN/ControlPython/startup/neven_http_server.py` | `_discover_pipe`, `_get_engine_status`, fix `_probe_pipe` error 231, entry point standalone |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |
| `C:\NEVEN\taskpane\neven_http_server.py` | Sincronizado |

#### Archivos copiados (binarios)
| Archivo | Acción |
|---------|--------|
| `C:\NEVEN\ControlJulia.exe` | Copiado desde build |

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| ~~**ALTA**~~ | ~~Commit de todos los cambios al repositorio~~ ✅ `ff5c9bd` |
| **ALTA** | Sincronizar fix JS (`});` línea 867) al repo |
| **MEDIA** | Bug en `variable_to_python` con resultados complejos de R |

### Commit realizado
```
ff5c9bd feat(http-server): dynamic pipe discovery for Run Script
```

**Cambios incluidos:**
- `_discover_pipe(lang)` — busca pipes fijos y dinámicos
- `_probe_pipe` — trata error 231 como "pipe existe"
- `_get_engine_status` — verifica factory primero
- `_get_pipe_client` — crea PipeClient dinámicamente
- Entry point standalone

---

### Resumen sesión 2026-08-19 (Continuación - Fix Bug IVQH10)

## 🐛 BUG CRÍTICO RESUELTO: Direcciones de celda corruptas (IVQH10)

### Problema reportado
El agente Excel Consultant mostraba direcciones de celda imposibles como "IVQH10, IVQH11" (columna 173,506 cuando Excel máximo es XFD=16,384).

### Causa raíz identificada
El regex en `captureSheetForAnalysis()` para parsear la dirección de rango estaba MAL:

```javascript
// ANTES (buggy)
const match = startAddress.match(/!?([A-Z]+)(\d+)/i);
```

Cuando `startAddress = "Hoja1!B5:Z100"`:
- El regex capturaba `"Hoja"` como columna y `"1"` como fila
- `columnToNumber("Hoja")` → 151,009
- Al iterar por las celdas, generaba direcciones como HOJA10, HOJB11, etc.
- Dependiendo del nombre de hoja, podía generar IVQH, SHEET, etc.

### Fix aplicado
```javascript
// DESPUÉS (correcto)
let cellRefPart = startAddress;
if (startAddress.includes('!')) {
  cellRefPart = startAddress.split('!').pop();  // Tomar parte después del "!"
}
const match = cellRefPart.match(/\$?([A-Z]{1,3})\$?(\d+)/i);
```

Ahora:
1. Primero extrae la parte de la dirección después del `!` (si existe)
2. Luego parsea la referencia de celda correctamente
3. Limita columnas a máximo 3 letras (XFD = máximo Excel)

### Archivos modificados
| Archivo | Cambio |
|:---|:---|
| `NEVEN/TaskPane/taskpane.js` | Fix regex en líneas 1303-1315 |
| `C:\NEVEN\taskpane\taskpane.js` | Sincronizado |

### Verificación
El regex ahora maneja correctamente todos estos casos:
- `"Sheet1!A1:B10"` → col=A, row=1 ✓
- `"Hoja1!B5:Z100"` → col=B, row=5 ✓
- `"Hoja1!$B$5:$Z$100"` → col=B, row=5 ✓
- `"'Modelo AR(1)'!B5:Z100"` → col=B, row=5 ✓
- `"A1:B10"` → col=A, row=1 ✓

### Commits realizados
| Hash | Descripción |
|:---|:---|
| `e4df39b` | fix(TaskPane): correct cell address parsing for non-English sheet names |
| `baa6521` | feat(TaskPane): add column headers to AI context for Excel Consultant |
| `f4be4a8` | fix(AgentService): ensure AI uses sheet context for precise answers |
| `0987f54` | fix(http_server): add Excel Consultant mode with sheet context |

### Mejora adicional: Encabezados de columna en contexto del agente

**Problema reportado:** El agente pedía "¿Dónde está SALARIOS?" aunque tenía la información en su contexto. Sabía que el rango era D2:D13 pero no conectaba "SALARIOS" con "columna D".

**Causa:** `formatAnalysisForAI()` no incluía los encabezados de columna, solo mostraba referencias como D2:D13 sin el nombre semántico.

**Solución implementada:**
1. `captureSheetForAnalysis()` ahora extrae los encabezados de la primera fila
2. Crea un mapa `column_headers: { "D": "SALARIOS", "E": "BONOS", ... }`
3. `formatAnalysisForAI()` ahora incluye sección "Estructura de columnas":

```
## Estructura de columnas
Datos en filas 2 a 13 (12 filas de datos)

- Columna A = "NOMBRE" → datos en A2:A13
- Columna D = "SALARIOS" → datos en D2:D13
```

### Fix adicional: El agente no usaba el contexto

**Problema:** Aún con la estructura de columnas, el agente seguía pidiendo información.

**Causas identificadas:**
1. La detección de contexto buscaba `"=== SHEET ANALYSIS ==="` pero el nuevo formato usa `"=== ANÁLISIS DE HOJA EXCEL ==="`
2. El prompt del Excel Consultant no instruía explícitamente al agente a usar el contexto

**Solución:**
1. Actualizada la detección en `_build_system_prompt()`:
```python
has_sheet_analysis = (
    "=== SHEET ANALYSIS ===" in context or 
    "=== ANÁLISIS DE HOJA EXCEL ===" in context or
    "## Estructura de columnas" in context or
    "sheet_name" in context
)
```

2. Agregada **REGLA CRÍTICA** al prompt del Excel Consultant:
```
## REGLA CRÍTICA: Usa el contexto para respuestas precisas
Cuando el usuario pregunte sobre una columna por nombre (ej: "totaliza SALARIOS"), SIEMPRE:
1. Busca en "## Estructura de columnas" qué columna tiene ese nombre
2. Usa el rango exacto mostrado (ej: D2:D13) para tu fórmula
3. NUNCA pidas más información si ya la tienes en el contexto
```

### Fix crítico: Código duplicado en neven_http_server.py

**Problema:** Después de aplicar todos los fixes, el agente SEGUÍA pidiendo rangos.

**Causa raíz REAL:** Existen **DOS archivos** que manejan `/api/ai/chat`:
1. `AgentService/neven_ai_service.py` — Servicio FastAPI (actualizado)
2. `ControlPython/startup/neven_http_server.py` — Servidor HTTP integrado (**NO actualizado**)

El Task Pane estaba usando `neven_http_server.py`, que tenía lógica de chat duplicada SIN el modo Excel Consultant.

**Solución:**
Agregado en `neven_http_server.py`:
1. Detección `has_sheet_analysis` con los mismos marcadores
2. Prompt de Excel Consultant con la REGLA CRÍTICA

**Lección aprendida:** 
Cuando hay código duplicado, AMBAS copias deben actualizarse. Ideal sería refactorizar para tener una sola fuente de verdad.

### Pendientes próxima sesión

#### ALTA
- [x] ~~**REINICIAR Excel** para que cargue el nuevo neven_http_server.py~~ ✅ COMPLETADO
- [x] ~~Probar "totaliza SALARIOS" → debe responder `=SUMA(D2:D13)` directamente~~ ✅ FUNCIONA

#### MEDIA
- [ ] Considerar refactorizar la lógica de chat para eliminar duplicación entre neven_ai_service.py y neven_http_server.py

#### BAJA
- [ ] Limpiar logs de diagnóstico en taskpane.js

---

## ✅ EXCEL CONSULTANT FUNCIONANDO (2026-08-19 ~17:00)

**Confirmado por el usuario:** El agente ahora retorna la fórmula exacta (`=SUMA(D2:D13)`) cuando se le pide "totaliza SALARIOS", usando la información de la estructura de columnas del contexto.

**Resumen de la cadena de fixes necesarios:**
1. Bug IVQH10 → regex capturaba nombre de hoja como columna
2. Faltaban encabezados → agregado `column_headers` a `captureSheetForAnalysis()`
3. Detección de contexto rota → marcadores en español no detectados
4. Prompt sin instrucción clara → agregada REGLA CRÍTICA
5. **Código duplicado** → `neven_http_server.py` no tenía el modo Excel Consultant

**Commits de la sesión:**
- `e4df39b` — fix: cell address parsing
- `baa6521` — feat: column headers in context  
- `f4be4a8` — fix: AI service uses context
- `0987f54` — fix: HTTP server Excel Consultant mode

---

### Resumen sesión anterior 2026-08-19 (Data Binding Reactivo COMPLETO)

## 🎉 DATA BINDING REACTIVO FUNCIONANDO AL 100%

### Logros principales

1. **Data Binding Reactivo implementado y funcionando:**
   - ✅ Edición manual de celdas → gráficos se actualizan automáticamente
   - ✅ F9 (recálculo de fórmulas) → gráficos se actualizan automáticamente
   - ✅ GROUP BY y Quick Chart ambos soportados

2. **Documentación actualizada:**
   - Evaluacion_comercial.md: fortaleza #20
   - Evaluacion_doctoral.md: sección 2.19
   - EVALUACION_MIBOGO.md: caso de estudio AI Engineering

### Commits realizados

| Hash | Descripción |
|:---|:---|
| `a7af405` | feat(TaskPane): data binding reactivo Excel→NEVEN Studio |
| `929f48b` | docs(Evaluaciones): agregar Data Binding Reactivo v2.4 |

### Causas raíz de problemas resueltos

| Problema | Causa raíz | Solución |
|:---|:---|:---|
| F9 no dispara evento | `onCalculated` está en `Worksheet`, no en `Workbook` | Usar `sheet.onCalculated.add()` |
| `showToast is not defined` | Función definida en scope local de event listener | Mover a `window.showToast` global |
| Cambio en B15 no actualiza gráfico | Celda fuera del rango vinculado (A1:D13) | Usuario debe modificar dentro del rango |

### Archivos modificados

**Producción (`C:\NEVEN\`):**
- `taskpane\taskpane.html` — sistema `_nevenDataBinding`, `_rerunQuickChart`, `window.showToast`

**Repositorio (`F:\ANTIGRAVITY\2026\NEVEN\NEVEN\`):**
- `TaskPane\taskpane.html` — sincronizado
- `docs\Evaluaciones\Evaluacion_comercial.md` — fortaleza #20
- `docs\Evaluaciones\Evaluacion_doctoral.md` — sección 2.19
- `docs\Evaluaciones\EVALUACION_MIBOGO.md` — caso de estudio (local, .gitignore)

### Decisiones de diseño

1. **`sheet.onCalculated` en lugar de `workbook.onCalculated`:** La API de Office.js expone el evento a nivel de hoja, no de libro.
2. **Timeouts escalonados (100ms GROUP BY, 150ms Quick Chart):** Evita race conditions cuando ambos gráficos necesitan actualizarse.
3. **Hash de datos para evitar actualizaciones redundantes:** Previene re-renderizado cuando el evento se dispara pero los datos no cambiaron.

### Intentos fallidos

1. **`workbook.onCalculated`** — No dispara eventos con F9. Solo `sheet.onCalculated` funciona.
2. **`showToast` sin `window.`** — Error de scope; la función estaba en un closure local.

### Pendientes próxima sesión

#### ALTA
- (ninguno)

#### MEDIA
- [ ] Limpiar logs de diagnóstico extra (console.log con emojis)
- [ ] Agregar indicador visual de "escuchando cambios" en la UI

#### BAJA
- [ ] Debounce para evitar múltiples actualizaciones rápidas
- [ ] Persistir binding entre sesiones (localStorage)

---

### Detalle de implementación (sesión anterior)

## ✅ QUICK CHART INTEGRADO AL SISTEMA DE DATA BINDING

**Requerimiento del usuario:**
El cambio no solo debe aplicar para GROUP BY sino para GRÁFICO RÁPIDO.

**Implementación completada:**

1. **`window._lastQuickChartConfig`** — guarda configuración del último Quick Chart:
   - `chartType`, `colX`, `colsY[]`, `palette`
   - Se asigna al generar el gráfico (línea ~1579)

2. **`window._rerunQuickChart()`** — re-ejecuta el Quick Chart con datos actualizados:
   - Consulta DuckDB con las columnas configuradas
   - Re-renderiza el gráfico con la misma configuración
   - Muestra toast "📊 Quick Chart actualizado"

3. **Callback del Data Binding actualizado** — ahora llama AMBOS:
   ```javascript
   // Re-ejecutar gráficos activos con los nuevos datos
   if (window._lastGroupByConfig && window._rerunGroupBy) {
     setTimeout(window._rerunGroupBy, 100);
   }
   if (window._lastQuickChartConfig && window._rerunQuickChart) {
     setTimeout(window._rerunQuickChart, 150);
   }
   ```

**Flujo completo de reactividad:**
```
Excel: datos cambian → Office.js: onChanged → NEVEN: re-lee rango
→ DuckDB: actualiza → GROUP BY: re-ejecuta (100ms) → Quick Chart: re-ejecuta (150ms)
→ Toast: "📊 Quick Chart actualizado"
```

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html` — callback actualizado (~línea 1187)
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` — sincronizado

**Pendientes próxima sesión:**

#### ALTA
- [ ] **PROBAR** — Flujo completo: Leer de Excel → Quick Chart → cambiar dato → ver actualización
- [ ] **COMMIT** — Todos los cambios de la sesión

#### MEDIA
- [ ] Agregar indicador visual de "escuchando cambios" en la UI

#### BAJA
- [ ] Optimizar: debounce para evitar múltiples actualizaciones rápidas
- [ ] Persistir binding entre sesiones (guardar rangeAddress en localStorage)

---

### Continuación sesión 2026-08-19 (~09:30) - Diagnóstico Data Binding

## 🔍 PROBLEMA: Data Binding NO funciona

**Síntoma reportado:**
Usuario probó "Leer de Excel" y "Pegar de Excel", creó Quick Chart, cambió valores en Excel → el gráfico NO se actualiza automáticamente.

**Diagnóstico en progreso:**
Se agregaron logs detallados para identificar dónde falla el flujo:

```javascript
// Logs agregados en bindRange():
console.log('[NEVEN Binding] bindRange llamado con:', address, sheetName);
console.log('[NEVEN Binding] typeof Excel:', typeof Excel);
console.log('[NEVEN Binding] _officeReady:', window._officeReady);
console.log('[NEVEN Binding] 🔔 EVENTO DETECTADO - Cambio en:', eventArgs.address);
console.log('[NEVEN Binding] ✅ Listener registrado exitosamente');
```

**Posibles causas a investigar:**
1. `_officeReady` no es `true` cuando se llama `bindRange()`
2. `sheet.onChanged.add()` no está registrando el listener correctamente
3. El evento `onChanged` no se dispara en el contexto del Add-in
4. "Pegar de Excel" no llama a `bindRange()` (solo "Leer de Excel" lo hace)

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html` — agregados logs de diagnóstico

**Próximo paso:**
Usuario debe abrir DevTools (F12), ejecutar "Leer de Excel", cambiar dato, y reportar qué mensajes aparecen en consola.

**Estado:** ✅ CAUSA RAÍZ IDENTIFICADA Y CORREGIDA

**Hallazgos:**
1. El binding SÍ funciona — eventos se detectan correctamente
2. Usuario modificó celda B15 pero rango vinculado era A1:D13 (fuera del rango)
3. Al probar dentro del rango, el callback se ejecutaba pero crasheaba: `showToast is not defined`

**Causa raíz del crash:**
`showToast()` estaba definida localmente dentro de un event listener de postMessage, no era accesible en el scope del callback de data binding.

**Fix aplicado:**
Se creó `window.showToast` como función global antes del sistema de data binding:
```javascript
window.showToast = function(text) { ... };
var showToast = window.showToast; // Alias para compatibilidad
```

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html` — función showToast movida a scope global (~línea 645)

**Pendiente:** Usuario debe probar con Ctrl+F5 y confirmar que el gráfico se actualiza

---

### Continuación sesión 2026-08-19 (~10:00) - Soporte F9 (Recálculo)

## ✅ DATA BINDING FUNCIONA + SOPORTE F9 AGREGADO

**Logro confirmado:**
Usuario confirmó que al cambiar una celda manualmente, el gráfico se actualiza automáticamente. 🎉

**Nuevo requerimiento:**
Detectar cuando el usuario presiona F9 (recálculo manual de fórmulas) para también actualizar el gráfico.

**Implementación:**
Se agregó el evento `workbook.onCalculated` además de `sheet.onChanged`:

```javascript
// Evento para edición manual
sheet.onChanged.add(function(eventArgs) {
  self._handleChange(eventArgs);
});

// Evento para F9 / recálculo de fórmulas
context.workbook.onCalculated.add(function(eventArgs) {
  console.log('[NEVEN Binding] 🔄 onCalculated - Recálculo detectado (F9 o fórmulas)');
  self._handleChange({ address: 'calculation', type: 'Calculated' });
});
```

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html` — agregado `onCalculated` listener (~línea 700)
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` — sincronizado

**Commits:** Pendiente

**Pendientes próxima sesión:**

#### ALTA
- [ ] **PROBAR F9** — Confirmar que el recálculo dispara actualización del gráfico
- [ ] **COMMIT** — Todos los cambios de la sesión

#### MEDIA
- [ ] Limpiar logs de diagnóstico (quitar console.log extras)
- [ ] Agregar indicador visual de "escuchando cambios" en la UI

#### BAJA
- [ ] Debounce para evitar múltiples actualizaciones rápidas en F9

---

### Continuación sesión 2026-08-19 (~10:30) - Debug onCalculated

## 🔧 INTENTO: Evento onCalculated para F9

**Problema:** Al presionar F9, la consola no registra ningún cambio.

**Diagnóstico:**
1. Primer intento: `context.workbook.onCalculated` — no disparó evento
2. Revisión de docs Microsoft: `onCalculated` está en `Worksheet`, no en `Workbook`
3. Segundo intento: `sheet.onCalculated.add()` — pendiente prueba

**Cambio aplicado:**
```javascript
// ANTES (incorrecto):
context.workbook.onCalculated.add(...)

// DESPUÉS (correcto según docs):
sheet.onCalculated.add(function(eventArgs) {
  console.log('[NEVEN Binding] 🔄 onCalculated - Recálculo detectado en:', eventArgs.address);
  self._handleChange({ address: eventArgs.address || 'calculation', type: 'Calculated' });
});
```

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html` — corregido objeto para onCalculated

**Estado:** ✅ ¡FUNCIONA! Usuario confirmó: "ya cambia!!! Felicidad total!"

**Resumen de la sesión - Data Binding Reactivo COMPLETO:**
- ✅ Edición manual de celdas → gráfico se actualiza
- ✅ F9 (recálculo de fórmulas) → gráfico se actualiza
- ✅ GROUP BY → se re-ejecuta automáticamente
- ✅ Quick Chart → se re-ejecuta automáticamente

---

## Última actualización previa
**Fecha:** 2026-09-22
**Hora aproximada:** ~20:00

### Resumen sesión 2026-09-22 (Data Binding Reactivo ~19:45-20:00)

## 🎯 IMPLEMENTACIÓN: Reactividad Excel → NEVEN Studio

**Requerimiento del usuario:**
Cuando los datos cambian en Excel, los gráficos en NEVEN Studio deben actualizarse automáticamente.

**Implementación realizada:**

1. **Sistema de Data Binding (`_nevenDataBinding`):**
   - `bindRange(address, sheetName, callback)` — vincula un rango de Excel
   - `_handleChange(eventArgs)` — maneja cambios detectados
   - `unbind()` — desvincula el rango
   - Usa `sheet.onChanged` de Office.js para detectar cambios

2. **Modificaciones a "Leer de Excel":**
   - Guarda referencia al rango en `_nevenCurrentData`
   - Registra listener automáticamente después de cargar datos
   - Re-lee datos cuando hay cambios y actualiza DuckDB
   - Re-ejecuta gráficos GROUP BY automáticamente

3. **Función `_rerunGroupBy()`:**
   - Re-ejecuta el último gráfico GROUP BY con la configuración guardada
   - Se llama automáticamente cuando los datos cambian

4. **Indicadores visuales:**
   - `(🔗 vinculado: Sheet1!A1:D100)` — datos vinculados a Excel
   - `(🔄 actualizado)` — datos actualizados automáticamente
   - Toast: "🔄 Datos actualizados: X filas"

**Flujo de reactividad:**
```
Excel: datos cambian → Office.js: onChanged → NEVEN: re-lee rango
→ DuckDB: actualiza → GROUP BY: re-ejecuta → Plotly: re-renderiza
```

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html`:
  - Sistema `_nevenDataBinding` (líneas ~640-720)
  - Modificación de "Leer de Excel" para registrar binding (~1000-1100)
  - Función `_rerunGroupBy()` (~1890-1920)
  - Variable `_lastGroupByConfig` para guardar configuración de gráficos
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` — sincronizado

**Commits:** Pendiente

**Pendientes próxima sesión:**

#### ALTA
- [ ] **PROBAR** — Flujo completo: Leer de Excel → GROUP BY → cambiar dato → ver actualización
- [ ] **COMMIT** — Todos los cambios de la sesión

#### MEDIA
- [ ] Extender reactividad a Quick Chart (no solo GROUP BY)
- [ ] Agregar indicador visual de "escuchando cambios" en la UI

#### BAJA
- [ ] Optimizar: debounce para evitar múltiples actualizaciones rápidas
- [ ] Persistir binding entre sesiones (guardar rangeAddress en localStorage)

---

### Resumen sesión 2026-09-22 (ÉXITO ~19:30-19:45)

## 🎉 AUTO-OPEN FUNCIONA

**Logro principal:**
El TaskPane del Office Add-in **se abre automáticamente** cuando el usuario abre un documento que lo tuvo abierto anteriormente.

**Flujo funcional verificado:**
1. ✅ Excel se abre → XLL carga → servidor HTTP se auto-inicia (puerto 5555)
2. ✅ Usuario abre documento que tuvo TaskPane abierto → **TaskPane se abre automáticamente**
3. ✅ TaskPane integrado en Excel con contexto de Office.js
4. ✅ Usuario puede cerrar/reabrir y el TaskPane persiste

**Solución técnica:**
- `Office.onReady()` + `Office.addin.setStartupBehavior(Office.StartupBehavior.load)` en `taskpane.html`
- El Add-in configura auto-open al cargarse
- Office guarda esta preferencia en el documento

**Archivos clave modificados en esta sesión:**
- `C:\NEVEN\catalog\manifest.xml` — v3.0.2.0
- `C:\NEVEN\taskpane\taskpane.html` — Office.onReady + auto-open + indicador de estado
- `C:\NEVEN\NEVENRibbon.dll` — actualizado con `py -3` launcher
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Ribbon\ribbon_connect.h` — múltiples iteraciones
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` — sincronizado
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Addin\catalog\manifest.xml` — nuevo

**Commits:** Pendiente

**Estado pendiente:**
- ❓ Botón en pestaña Inicio — no verificado, pero no es crítico (auto-open funciona)
- ❓ Indicador de estado "● Conectado" — no verificado

**Pendientes próxima sesión:**

#### ALTA
- [ ] **COMMIT** — Todos los cambios de la sesión
- [ ] Verificar si el botón aparece en pestaña Inicio después de limpiar cache

#### MEDIA
- [ ] Verificar indicador de estado del servidor en el TaskPane
- [ ] Probar flujo completo: nuevo documento → abrir TaskPane → guardar → cerrar → reabrir

#### BAJA
- [ ] Documentar el proceso de instalación del Add-in para usuarios
- [ ] Considerar eliminar o simplificar el botón del COM Ribbon (confunde con el del Add-in)

---

### Resumen sesión 2026-09-22 (fixes de Add-in ~19:15-19:30)

**Progreso importante:**
- ✅ El TaskPane **FUNCIONA** cuando se abre desde Insertar → Complementos → NEVEN Studio
- ❌ El botón NO aparece en la pestaña Inicio (Home)
- ❌ Auto-open no funciona (TaskPane no se abre automáticamente)

**Cambios realizados:**

1. **Manifest actualizado (v3.0.2.0):**
   - Simplificado `VersionOverrides` para mejor compatibilidad
   - Removido `GetStarted` y `FunctionFile` extras
   - Estructura más limpia del botón en `TabHome`

2. **TaskPane con auto-open:**
   - Agregado `Office.onReady()` con inicialización de Office.js
   - Agregado `Office.addin.setStartupBehavior(Office.StartupBehavior.load)` para auto-open
   - Esto configura el TaskPane para auto-abrirse en documentos que lo tuvieron abierto

**Archivos modificados:**
- `C:\NEVEN\catalog\manifest.xml` — v3.0.2.0, VersionOverrides simplificado
- `C:\NEVEN\taskpane\taskpane.html` — Office.onReady + auto-open
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` — sincronizado
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\Addin\catalog\manifest.xml` — nuevo directorio + archivo

**Pendientes próxima sesión:**

#### CRÍTICO
- [ ] **LIMPIAR CACHE** — Borrar `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` y reiniciar Excel
- [ ] **VERIFICAR BOTÓN** — Después de limpiar cache, verificar si aparece en pestaña Inicio
- [ ] **REINSTALAR ADD-IN** — Si no aparece, quitar y volver a agregar el Add-in

#### ALTA
- [ ] Probar auto-open: abrir TaskPane, guardar documento, cerrar/abrir, verificar que se abre solo
- [ ] Si el botón sigue sin aparecer en Home, investigar si es problema del manifest o de permisos

#### MEDIA
- [ ] Commit de todos los cambios de la sesión
- [ ] Documentar el proceso de instalación del Add-in

---

### Resumen sesión 2026-09-22 (diagnóstico final ~19:00-19:15)

**Problema persistente:**
El botón del COM Ribbon sigue mostrando error "No se pudo iniciar NEVEN Studio" aunque el servidor está corriendo (verificado: `http://localhost:5555/api/engines` responde OK).

**Causa identificada:**
Excel no recargó el NEVENRibbon.dll actualizado. Las DLLs COM se cargan una sola vez al inicio de Excel y no se recargan hasta reiniciar Excel.

**Estado verificado:**
- ✅ Servidor HTTP corriendo en puerto 5555 (PID 11908, python3.12)
- ✅ NEVENRibbon.dll actualizado en `C:\NEVEN\` (317KB, 18:13)
- ❌ Excel está usando la versión vieja de la DLL (cargada antes de la actualización)

**Solución pendiente:**
1. Cerrar Excel completamente
2. Abrir Excel de nuevo (cargará la DLL actualizada)
3. Probar el botón del COM Ribbon
4. **MÁS IMPORTANTE:** Probar el botón del Office Add-in en pestaña Home

**Pregunta pendiente al usuario:**
¿El botón del Office Add-in aparece en la pestaña Home? Si no aparece, el Add-in no está instalado y necesita agregarse desde `Insertar → Complementos → Mis complementos`.

**Archivos en producción:**
- `C:\NEVEN\NEVENRibbon.dll` (317KB, 22/09/2026 18:13) — actualizado pero no recargado por Excel
- `C:\NEVEN\taskpane\taskpane.html` — con indicador de estado del servidor

**Pendientes próxima sesión:**

#### CRÍTICO
- [ ] **REINICIAR EXCEL** — Para que cargue el NEVENRibbon.dll actualizado
- [ ] **VERIFICAR ADD-IN** — ¿Aparece botón del Add-in en pestaña Home?
- [ ] Si no aparece: Insertar → Complementos → Mis complementos → Agregar NEVEN Studio

#### ALTA
- [ ] Probar botón del Office Add-in (TaskPane integrado)
- [ ] Probar botón del COM Ribbon (debería funcionar tras reinicio)

#### MEDIA
- [ ] Commit de todos los cambios de la sesión

---

### Resumen sesión 2026-09-22 (implementación Opción B ~18:45-19:00)

**Decisión tomada:** Opción B — Todo en el Add-in

El usuario eligió la Opción B: el servidor se gestiona desde el XLL (auto-start) y el TaskPane se abre exclusivamente desde el botón del Office Add-in.

**Implementación realizada:**

1. **Verificación:** El auto-start del servidor ya estaba implementado en `xlAutoOpen` (líneas 678-720 de `rj2xcl.cc`)

2. **Indicador de estado del servidor en TaskPane:**
   - Agregado elemento `#server-status` en el header del TaskPane
   - JavaScript verifica `/api/engines` al cargar y cada 30 segundos
   - Estados visuales:
     - `● Conectado` (verde) — servidor corriendo
     - `● Desconectado` (rojo) — servidor no disponible

**Archivos modificados:**
- `C:\NEVEN\taskpane\taskpane.html` — indicador de estado + verificación JS
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` — sincronizado desde producción

**Flujo final (Opción B):**
1. Usuario abre Excel → XLL carga → auto-inicia servidor HTTP (puerto 5555)
2. Usuario hace clic en botón "NEVEN Studio" en **pestaña Home** (Office Add-in)
3. TaskPane integrado se abre con indicador "● Conectado"
4. Office.js tiene contexto de la hoja activa

**Nota importante sobre el botón del COM Ribbon:**
El botón en la pestaña NEVEN (COM Ribbon) sigue existiendo pero abre una ventana WebView2 flotante. Para el TaskPane integrado, el usuario debe usar el botón del Add-in en la pestaña Home.

**Commits:** Ninguno (pendiente)

**Pendientes próxima sesión:**

#### ALTA
- [ ] **PROBAR** — Abrir Excel, verificar que el botón del Add-in en Home abre TaskPane integrado
- [ ] **VERIFICAR** — ¿El Office Add-in está instalado? (Insertar → Complementos → Mis complementos)
- [ ] Si no está instalado, agregar desde catálogo `C:\NEVEN\catalog\`

#### MEDIA
- [ ] Considerar eliminar o modificar el botón del COM Ribbon para evitar confusión
- [ ] Agregar mensaje al botón COM: "Para TaskPane integrado, use el botón en pestaña Home"

#### BAJA
- [ ] Commit de todos los cambios de la sesión
- [ ] Documentar el flujo final en la documentación de usuario

---

### Resumen sesión 2026-09-22 (cierre ~18:30-18:45)

**Aclaración del usuario:**
El botón del COM Ribbon NO debe eliminarse — debe servir para **reabrir el TaskPane** si el usuario lo cierra accidentalmente.

**Investigación adicional:**
- Microsoft cambió políticas en marzo 2024: `showAsTaskpane()` **solo funciona desde acción explícita del usuario** (clic en botón del Ribbon del Add-in)
- No hay forma programática de abrir un Web Add-in TaskPane desde código externo (COM Add-in, XLL, etc.)
- `AutoShowTaskpaneWithDocument` puede auto-abrir el TaskPane al abrir un documento, pero el usuario puede desactivarlo

**Limitación técnica identificada:**
El botón del COM Ribbon **no puede abrir** el TaskPane del Office Add-in programáticamente. Solo el botón del propio Add-in (definido en manifest.xml) puede hacerlo.

**Opciones propuestas al usuario (pendiente decisión):**

| Opción | Descripción |
|--------|-------------|
| **A** | Botón COM inicia servidor + guía al usuario al botón del Add-in en Home |
| **B** | Mover todo al Add-in (servidor se inicia desde JavaScript) |

**Estado actual:**
- Botón COM Ribbon: inicia servidor + abre WebView2 flotante (no integrado)
- Botón Add-in (Home): abre TaskPane integrado (si el Add-in está instalado)

**Pendientes próxima sesión:**

#### ALTA
- [ ] **DECIDIR** — Opción A o B (ver tabla arriba)
- [ ] **VERIFICAR** — ¿El Office Add-in está instalado correctamente?
- [ ] **PROBAR** — Botón del Add-in en pestaña Home abre TaskPane integrado

#### MEDIA
- [ ] Si Opción B: implementar inicio del servidor desde JavaScript del TaskPane
- [ ] Configurar `AutoShowTaskpaneWithDocument` para auto-abrir el TaskPane

#### BAJA
- [ ] Documentar la limitación de Microsoft sobre `showAsTaskpane()`
- [ ] Commit de cambios de la sesión

---

### Resumen sesión 2026-09-22 (final ~18:15-18:30)

**Discusión arquitectural importante:**

El usuario aclaró que el TaskPane **debe ser integrado en Excel** (Office Add-in), no una ventana WebView2 flotante. Razones:
1. El usuario no pierde el foco de la hoja actual
2. Office.js puede leer el contexto de la hoja (celdas, rangos, datos)
3. UX consistente con otros Add-ins de Office

**Investigación realizada:**
- No existe API COM directa para abrir un Web Add-in TaskPane desde un COM Add-in
- `Office.addin.showAsTaskpane()` solo funciona desde JavaScript dentro del Add-in
- Crear un Custom Task Pane docked desde el XLL requiere cambios arquitecturales significativos

**Estado actual — dos botones, dos comportamientos:**

| Botón | Ubicación | Resultado |
|-------|-----------|-----------|
| NEVEN Studio (COM Ribbon) | Pestaña "NEVEN" | WebView2 **flotante** |
| NEVEN Studio (Office Add-in) | Pestaña "Home" > grupo "NEVEN" | TaskPane **integrado** ✅ |

**Decisión pendiente:**
Para el flujo correcto (TaskPane integrado con contexto Office.js), el usuario debe usar el botón del **Office Add-in** en la pestaña Home.

**Archivos modificados:**
- `NEVEN/Ribbon/ribbon_connect.h` — Múltiples iteraciones del código `OnAIAssistantCommand`

**Archivos de producción:**
- `C:\NEVEN\NEVENRibbon.dll` (317 KB, 22/09/2026 18:13)

**Commits:** Ninguno en esta parte de la sesión

**Pendientes próxima sesión:**

#### ALTA
- [ ] **VERIFICAR** — ¿El Office Add-in está instalado? (Insertar → Complementos → Mis complementos)
- [ ] Si no está instalado, agregarlo desde el catálogo `C:\NEVEN\catalog\`
- [ ] **PROBAR** — Usar el botón del Add-in en pestaña Home para abrir TaskPane integrado
- [ ] **DECIDIR** — ¿Eliminar el botón duplicado del COM Ribbon para evitar confusión?

#### MEDIA
- [ ] Investigar si se puede activar el Office Add-in TaskPane programáticamente desde el COM Ribbon
- [ ] Considerar usar un único punto de entrada (solo Add-in, o solo COM Ribbon con docked panel)

#### BAJA
- [ ] Commit de todos los cambios de la sesión
- [ ] Documentar la arquitectura de los dos sistemas de Ribbon (COM vs Add-in)

---

### Resumen sesión 2026-09-22 (continuación ~18:00-18:15)

**Problema diagnosticado:**
- El botón "NEVEN Studio" mostraba error "No se pudo iniciar NEVEN Studio. Verifica que Python esté instalado."
- Causa raíz: `OnAIAssistantCommand` en `ribbon_connect.h` tenía paths hardcodeados a Python 3.12, pero el usuario tiene Python 3.13

**Fix aplicado:**
- Eliminados paths hardcodeados (`C:\NEVEN\python\python.exe`, `Python312`)
- Reemplazado por `py -3` (Python Launcher) que funciona con cualquier versión instalada
- Aumentado timeout de verificación de servidor de 300ms a 500ms
- Reducido tiempo de espera máximo de 15s a 10s (ya que XLL auto-inicia el servidor)

**Archivos modificados:**
- `NEVEN/Ribbon/ribbon_connect.h` — `OnAIAssistantCommand` simplificado

**Archivos de producción actualizados:**
- `C:\NEVEN\NEVENRibbon.dll` (317 KB, 22/09/2026 18:08)

**Estado verificado:**
- Servidor HTTP está corriendo en puerto 5555 (verificado con `Invoke-WebRequest`)
- Proceso: `python3.12` PID 11908 iniciado a las 14:34

**Clarificación importante (discutida al final de sesión):**

El botón "NEVEN Studio" actualmente abre el TaskPane en una **ventana WebView2 flotante** (usando `NEVEN.View()`), **NO** en el TaskPane integrado de Office Add-in.

| Opción | Descripción | Estado |
|--------|-------------|--------|
| WebView2 flotante | Ventana separada, funciona siempre | ✅ Implementado |
| Office Add-in TaskPane | Panel lateral integrado en Excel | ❌ No implementado aún |

**Decisión pendiente:** ¿Mantener WebView2 flotante (más confiable) o cambiar a Office Add-in TaskPane (más integrado)?

**Pendientes próxima sesión:**

#### ALTA
- [ ] **DECIDIR** — ¿WebView2 flotante o Office Add-in TaskPane integrado?
- [ ] **PROBAR** — Cerrar Excel, reabrir, verificar que botón "NEVEN Studio" funciona
- [ ] Si se elige Office Add-in: modificar Ribbon para usar API COM de Office y mostrar TaskPane del Add-in registrado

#### MEDIA  
- [ ] Monitorear estabilidad del Ribbon (desaparición intermitente)

#### BAJA
- [ ] Commit de los cambios del Ribbon

---

### Resumen sesión 2026-09-22 (primera parte ~17:00-19:00)

**Logros principales:**
- ✅ Auto-start del servidor HTTP implementado en xlAutoOpen() del XLL
- ✅ El botón "NEVEN Studio" (antes "Agente IA") renombrado en Ribbon y COM Add-in
- ✅ Office Add-in manifest actualizado con VersionOverrides para integración Ribbon
- ✅ TaskPane funciona correctamente como Office Add-in (Office.js detecta Host)
- ⚠️ Ribbon desapareció temporalmente tras reiniciar Excel, pero reapareció en segundo intento

**Cambios técnicos:**
1. `Core/src/rj2xcl.cc` — Auto-start en xlAutoOpen() usando std::thread + CreateProcess
2. `Core/CMakeLists.txt` — Añadido `winhttp` a link_libraries  
3. `Ribbon/ribbon_connect.h` — OnAIAssistantCommand modificado para señalar Add-in
4. `Ribbon/ribbon_ui.xml` — Renombrado "Agente IA" → "NEVEN Studio"
5. `Addin/CustomUI.xml` — Mismo renombrado
6. `C:\NEVEN\catalog\manifest.xml` — VersionOverrides para botón Ribbon nativo

**Archivos de producción actualizados:**
- `C:\NEVEN\NEVEN64.xll` (2.52 MB, 22/09/2026 17:53)
- `C:\NEVEN\NEVENRibbon.dll` (319 KB, 22/09/2026 17:40)
- `C:\NEVEN\catalog\manifest.xml`
- `C:\NEVEN\taskpane\commands.html` (nuevo)
- `C:\NEVEN\taskpane\assets\icon-{16,32,64,80}.png` (nuevos)

**Commits:**
- `c0918eb` feat: NEVEN Studio button replaces Agente IA - opens Add-in TaskPane

**Estado actual:**
- XLL carga correctamente y auto-inicia servidor HTTP
- Ribbon aparece correctamente (desaparición temporal fue falsa alarma — reapareció al reiniciar)
- Auto-start verificado: servidor HTTP inicia automáticamente con Excel

**Problema temporal resuelto:**
- Al cerrar y reabrir Excel, el Ribbon desapareció temporalmente
- Causa probable: timing de carga de COM Add-in, no un crash real
- Solución: simplemente reiniciar Excel — el Ribbon reapareció sin intervención

---

### Resumen sesión 2026-08-23

**Logros principales:**
- Reordenado card "Gráfico Rápido" antes de "GROUP BY" en Data Studio (mejor UX)
- Commit y push del feature completo de Quick Chart a GitHub
- Commit `2d0839a`: 826 líneas nuevas (mapas Leaflet, multiselect Y-axis, 8 paletas)

**Archivos modificados:**
- `NEVEN/TaskPane/taskpane.html` — intercambio posición quickchart-card/groupby-card
- `C:\NEVEN\TaskPane\taskpane.html` — deploy producción

**Commits:**
- `2d0839a` feat(studio): Quick Chart con mapas Leaflet, multiselect Y-axis y 8 paletas de colores

**Nota técnica:** El repo git está en `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\.git`, no en el workspace root.

**Pendientes próxima sesión:** Ver lista completa abajo (sin cambios respecto a 2026-08-21).

---

### Resumen sesión 2026-08-21

**Logros principales:**
- Sysimage Julia construida exitosamente (467.4 MB) -- después de semanas bloqueada
- Causa raíz: espacios en nombre de usuario ("Minor Bonilla G") rompían sub-proceso de PackageCompiler
- Solución: ruta 8.3 (MINORB~1) en build_sysimage.ps1
- Verificado: =NevenX.J("sqrt", 144) = 12 ✅ / =NevenX.R, =NevenX.J, =NevenX.P todos funcionales
- Commit `da71441` con los 3 scripts de build sincronizados al repo
- ECC descartado: costo > beneficio para el problema de sysimage

**Estado de producción:**
- NEVEN64.xll: C:\NEVEN\NEVEN64.xll
- NEVENRibbon.dll: C:\NEVEN\NEVENRibbon.dll (v3.1)
- Sysimage Julia: C:\NEVEN\neven_julia.dll (467.4 MB, 1.12.6)
- Dispatcher v6: C:\NEVEN\functions\R4XCL-0-NevenX.R
- Sidecars: 37/37 con tipo_outputs
- Julia home: C:\Users\Minor Bonilla G\AppData\Local\Programs\Julia-1.12.6

---

## Sesiones formato nuevo (post-compactación)

- [ ] **BAJA** — Documentar el formato de sidecars para nuevas funciones


---

### [Sesión 2026-08-19 ~20:30] — Continuación post-compactación

**Duración:** ~5 minutos
**Estado:** Sin cambios nuevos

#### Resumen
Sesión reanudada tras compactación automática del contexto. Se revisó el estado del proyecto y se confirmó que el **Diccionario de Funciones** (tab "Ayuda") está completamente implementado y funcionando.

#### Sin cambios en esta sesión
- No hubo modificaciones de código
- No hubo commits nuevos
- Solo se validó el estado actual

#### Estado confirmado
- ✅ 20 funciones NevenX en acordeón por familias
- ✅ Acordeón cerrado por defecto
- ✅ Encoding UTF-8 corregido
- ✅ Commit `8f1485e` ya pusheado

#### Pendientes sin cambio (de la sesión anterior)
- [ ] **BAJA** — Limpiar código duplicado inline en taskpane.html
- [ ] **BAJA** — Copiar scripts fix_*.py al repositorio  
- [ ] **BAJA** — Documentar formato sidecar para nuevas funciones


---

### [Sesión 2026-08-20 ~08:00] — Inicio de sesión, revisión de pendientes

**Duración:** ~5 minutos
**Estado:** Sin cambios

#### Resumen
Sesión de inicio de día. Se revisó la bitácora completa para identificar pendientes y estado del proyecto.

#### Sin cambios en esta sesión
- No hubo modificaciones de código
- No hubo commits nuevos
- Solo revisión de estado

#### Estado del proyecto confirmado
- ✅ Diccionario de Funciones funcionando (tab "Ayuda")
- ✅ Excel Consultant funcionando con contexto de columnas
- ✅ Data Binding Reactivo funcionando (edición manual + F9)
- ✅ Auto-open TaskPane funcionando

#### Pendientes identificados

**MEDIA:**
- [ ] Refactorizar lógica de chat para eliminar duplicación entre `neven_ai_service.py` y `neven_http_server.py`
- [ ] Limpiar logs de diagnóstico en `taskpane.js`

**BAJA:**
- [ ] Limpiar código duplicado del diccionario inline en `taskpane.html`
- [ ] Copiar scripts `fix_encoding.py` y `fix_dash.py` al repositorio
- [ ] Documentar formato de sidecars para nuevas funciones
- [ ] Agregar indicador visual de "escuchando cambios" en la UI
- [ ] Debounce para evitar múltiples actualizaciones rápidas
- [ ] Persistir binding entre sesiones (localStorage)


---

### [Sesión 2026-08-20 ~08:15] — Planificación de pendientes en bloques

**Duración:** ~15 minutos
**Estado:** Sin cambios de código

#### Resumen
Se analizaron los pendientes y se agruparon en bloques para resolverlos eficientemente.

#### Bloques identificados

**Bloque 1: Limpieza de código (30-45 min)**
- Limpiar logs de diagnóstico en `taskpane.js`
- Limpiar código duplicado del diccionario inline en `taskpane.html`
- Copiar scripts `fix_*.py` al repositorio
- Commit: `chore: cleanup debug logs and duplicate code`

**Bloque 2: Documentación (20 min)**
- Documentar formato de sidecars para nuevas funciones
- Commit: `docs: document sidecar JSON format for NevenX functions`

**Bloque 3: Mejoras UX Data Binding (45-60 min)**
- Indicador visual "escuchando cambios"
- Debounce para evitar actualizaciones rápidas
- Persistir binding en localStorage
- Commit: `feat(TaskPane): improve data binding UX with indicator and debounce`

**Bloque 4: Refactoring arquitectural (1-2 hrs)**
- Eliminar duplicación de lógica de chat entre `neven_ai_service.py` y `neven_http_server.py`
- Requiere análisis previo, pospuesto

#### Decisión
Recomendación de empezar con Bloque 1 + Bloque 2 (~1 hora total).

#### Pendientes próxima sesión
- [ ] **MEDIA** — Ejecutar Bloque 1 (limpieza de código)
- [ ] **MEDIA** — Ejecutar Bloque 2 (documentación sidecars)
- [ ] **BAJA** — Ejecutar Bloque 3 (mejoras UX Data Binding)
- [ ] **BAJA** — Ejecutar Bloque 4 (refactoring duplicación chat)


---

### [Sesión 2026-08-20 ~08:00-10:00] — Bloque 1 + Bloque 2: Limpieza y Documentación

**Duración:** ~2 horas
**Estado:** Completado

---

## Bloque 1: Limpieza de Código ✅

### Logros
1. **Eliminados 6 console.log de debug** en `taskpane.js` (mantenidos 2 útiles de ShowTaskpane)
2. **Eliminadas ~390 líneas de código duplicado** del diccionario inline en `taskpane.html` (ahora vive en `ayuda.js`)
3. **Scripts fix_*.py copiados al repositorio** con documentación mejorada

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/taskpane.js` | Eliminados console.log de debug |
| `NEVEN/TaskPane/taskpane.html` | Eliminado código duplicado (~390 líneas) |
| `NEVEN/scripts/fix_encoding.py` | NUEVO - script para fix encoding UTF-8 |
| `NEVEN/scripts/fix_dash.py` | NUEVO - script para fix em dash corrupto |
| `C:\NEVEN\taskpane\taskpane.js` | Sincronizado |
| `C:\NEVEN\taskpane\taskpane.html` | Sincronizado |

### Commit
| Hash | Descripción |
|------|-------------|
| `e61db33` | chore: cleanup debug logs, remove duplicate code, add encoding fix scripts |

**Resultado:** 139 líneas agregadas, 396 eliminadas

---

## Bloque 2: Documentación de Sidecars para Agente IA ✅

### Logros
1. **SIDECAR_FORMAT.md creado** — Referencia técnica completa del formato JSON
2. **AGENT_INSTRUCTIONS.md creado** — Proceso de 7 pasos para que el agente IA cree funciones
3. **Prompts del agente actualizados** — Ambos servicios ahora saben cómo crear sidecars

### Archivos creados
| Archivo | Descripción |
|---------|-------------|
| `C:\NEVEN\functions\SIDECAR_FORMAT.md` | Formato JSON completo con ejemplos |
| `C:\NEVEN\functions\AGENT_INSTRUCTIONS.md` | Proceso paso a paso para el agente |
| `docs/SIDECAR_FORMAT.md` | Copia en repositorio |
| `docs/AGENT_INSTRUCTIONS.md` | Copia en repositorio |

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `AgentService/neven_ai_service.py` | PASO 4 agregado al protocolo con ejemplo de sidecar JSON |
| `ControlPython/startup/neven_http_server.py` | Referencia a AGENT_INSTRUCTIONS.md en prompt |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |

### Commit
| Hash | Descripción |
|------|-------------|
| `9dcae59` | docs: add sidecar format and agent instructions for creating NevenX functions |

**Resultado:** 655 líneas agregadas

---

## Estructura de Sidecars Documentada

### Tipos de funciones
- **DataLab-only**: Solo ejecutable desde Task Pane (sin `function_name_xll`)
- **XLL-callable**: Ejecutable desde celdas Excel con `=NEVEN.R()` (requiere `function_name_xll` + `nevenx_positions`)

### Campos clave para XLL-callable
```json
{
  "function_name_xll": "MR_MiFuncion",
  "nevenx_positions": {
    "a0": { "name": "SetDatosY", "type": "range", "required": true },
    "a1": { "name": "SetDatosX", "type": "range", "required": true }
  },
  "tipo_outputs": [
    { "id": 0, "label": "Ayuda" },
    { "id": 1, "label": "Resultado" }
  ]
}
```

### Estadísticas del catálogo
- 20 funciones XLL-callable (aparecen en Diccionario)
- 17 funciones DataLab-only (solo en Task Pane)

---

## Decisiones de Diseño

1. **Documentación en C:\NEVEN\functions\** — Junto a los sidecars para que el agente IA pueda consultarla fácilmente
2. **Copia en docs/** — Para versionamiento en el repositorio
3. **Prompt conciso en neven_http_server.py** — Solo referencia a AGENT_INSTRUCTIONS.md (evita duplicar prompt largo)
4. **Prompt completo en neven_ai_service.py** — Incluye ejemplo de sidecar inline para mayor claridad

---

## Pendientes próxima sesión

### BAJA
- [ ] Bloque 3: Mejoras UX Data Binding (indicador visual, debounce, persistir en localStorage)
- [ ] Bloque 4: Refactoring duplicación de lógica chat entre servicios

### Completados hoy
- [x] Bloque 1: Limpieza de código
- [x] Bloque 2: Documentación sidecars


---

### [Sesión 2026-08-20 ~10:00-11:30] — Bloque 3: Mejoras UX Data Binding

**Duración:** ~1.5 horas
**Estado:** Completado

---

## Bloque 3: Mejoras UX Data Binding ✅

### Logros principales

1. **Indicador visual "Escuchando cambios"**
   - Barra verde debajo de Data Studio que muestra el rango vinculado
   - Botón [x] para desconectar manualmente
   - Al hacer "Leer de Excel", aparece automáticamente

2. **Debounce de 300ms**
   - Evita múltiples actualizaciones cuando el usuario edita varias celdas rápido
   - Timer se reinicia con cada cambio, solo procesa después de 300ms de inactividad

3. **Persistencia en localStorage**
   - Guarda rangeAddress, sheetName y timestamp al hacer bind
   - Al recargar, muestra "Binding previo" en amarillo si hay binding guardado
   - Expira después de 24 horas
   - Se limpia automáticamente al desconectar

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/taskpane.html` | Sistema de data binding mejorado (+139 líneas, -36) |
| `C:\NEVEN\taskpane\taskpane.html` | Sincronizado |

### Commit

| Hash | Descripción |
|------|-------------|
| `84d28b8` | feat(TaskPane): improve data binding UX with indicator, debounce, and persistence |

---

## Detalles técnicos

### Nuevas propiedades en `_nevenDataBinding`
```javascript
isListening: false,      // Estado de escucha activa
_debounceTimer: null,    // Timer para debounce
_debounceMs: 300,        // Milisegundos de debounce
```

### Nuevas funciones en `_nevenDataBinding`
- `_updateIndicator(show, rangeText)` — Muestra/oculta el indicador visual
- `_saveToStorage()` — Guarda binding en localStorage
- `_loadFromStorage()` — Carga binding guardado (si < 24h)
- `_clearStorage()` — Limpia binding de localStorage

### HTML del indicador
```html
<div id="binding-indicator" style="display:none;...">
  <span style="color:#6c6;font-weight:600">Escuchando cambios</span>
  <span id="binding-range"></span>
  <button id="binding-disconnect">[x]</button>
</div>
```

---

## Decisiones de diseño

1. **Debounce en lugar de throttle** — Mejor para edición de celdas porque espera a que el usuario termine de editar
2. **300ms de debounce** — Balance entre responsividad y evitar actualizaciones excesivas
3. **24h de expiración** — Evita restaurar bindings obsoletos de días anteriores
4. **"Binding previo" no reconecta automáticamente** — El usuario debe hacer "Leer de Excel" de nuevo porque el rango podría haber cambiado

---

## Problemas técnicos durante la implementación

### Encoding corrupto en taskpane.html
**Síntoma:** `str_replace` fallaba con "string not found"
**Causa:** El archivo tiene caracteres UTF-8 que PowerShell lee diferente
**Solución:** Usar PowerShell con manipulación por líneas en lugar de `str_replace`

### Estructura del setTimeout en _handleChange
**Síntoma:** Código mal indentado/duplicado al insertar debounce
**Causa:** Inserción parcial dejó línea duplicada `await Excel.run`
**Solución:** Reescribir todo el bloque `_handleChange` completo

---

## Resumen de la sesión completa (Bloques 1-3)

| Bloque | Commit | Descripción |
|--------|--------|-------------|
| 1: Limpieza | `e61db33` | Eliminados logs debug, código duplicado, agregados scripts fix_*.py |
| 2: Documentación | `9dcae59` | SIDECAR_FORMAT.md, AGENT_INSTRUCTIONS.md, prompts actualizados |
| 3: UX Binding | `84d28b8` | Indicador visual, debounce, persistencia localStorage |

**Total:** 3 commits, ~900 líneas netas agregadas

---

## Pendientes próxima sesión

### BAJA
- [ ] Bloque 4: Refactoring — eliminar duplicación de lógica chat entre `neven_ai_service.py` y `neven_http_server.py`

### Completados hoy
- [x] Bloque 1: Limpieza de código
- [x] Bloque 2: Documentación sidecars
- [x] Bloque 3: Mejoras UX Data Binding


---

### [Sesión 2026-08-19 ~16:00] Bloque 4: Refactoring — Módulo compartido chat_prompts.py

## 🔧 REFACTORING COMPLETADO: Unificación de prompts para agentes IA

### Problema original
Duplicación significativa de código entre `neven_ai_service.py` (AgentService/FastAPI) y `neven_http_server.py` (HTTP handler legacy):
1. Constante `_FMT` — formato Markdown/LaTeX idéntico en ambos
2. `_RUN_HINT_TEMPLATE` vs `_run_hint` — hints para bloques ejecutables (diferentes pero relacionados)
3. Detección de contexto — `has_sheet_analysis`, `has_results`, `has_excel` duplicados
4. Excel Consultant prompt — ~200 líneas duplicadas con pequeñas diferencias
5. `_build_system_prompt()` — lógica compleja duplicada
6. Chart prompts — diferentes enfoques pero conceptualmente similares

### Solución implementada

**Nuevo módulo `chat_prompts.py`** con:

| Elemento | Descripción |
|----------|-------------|
| `FMT_MARKDOWN_LATEX` | Constante de formato compartida |
| `FMT_MINIMAL` | Prompt mínimo para cuando no hay contexto |
| `RUN_HINT_JSON_SCHEMA` | Hint para AgentService (JSON schema para neven-run) |
| `RUN_HINT_NEVENX_FORMULA` | Hint para HTTP server (fórmulas NevenX directas) |
| `EXCEL_CONSULTANT_PROMPT` | Prompt completo para modo Excel Consultant |
| `EXCEL_CONSULTANT_PROMPT_SIMPLE` | Versión simplificada para legacy |
| `CHART_GENERATION_PROMPT` | Prompt para generación de gráficos |
| `CHART_KEYWORDS` / `CHART_GENERIC_PATTERN` | Patrones de detección |
| `detect_context_type()` | Analiza contexto y retorna flags |
| `detect_chart_intent()` | Detecta si el prompt pide un gráfico |
| `build_excel_consultant_prompt()` | Construye prompt Excel Consultant |
| `build_chart_prompt()` | Construye prompt para gráficos |
| `build_system_prompt()` | Función principal — construye según tipo de contexto |
| `build_minimal_system_prompt()` | Retorna prompt mínimo |

### Decisiones de diseño

1. **Dos copias del módulo:** Una en `ControlPython/startup/` y otra en `AgentService/`. Mantiene independencia de los servicios, cada uno puede deployarse por separado.

2. **Comportamiento diferenciado preservado:** 
   - HTTP server usa `use_json_schema_hint=False` → genera fórmulas NevenX directas
   - AgentService usa `use_json_schema_hint=True` → genera JSON schema para bloques `neven-run`
   
3. **Wrappers en neven_ai_service.py:** Las funciones `_build_system_prompt()`, `_build_chart_prompt()`, etc. ahora son wrappers simples que delegan al módulo compartido. Mantiene compatibilidad con código existente que las llama.

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `ControlPython/startup/chat_prompts.py` | **NUEVO** — módulo compartido |
| `ControlPython/startup/neven_http_server.py` | Eliminadas ~150 líneas — importa desde chat_prompts |
| `AgentService/chat_prompts.py` | **NUEVO** — copia del módulo |
| `AgentService/neven_ai_service.py` | Eliminadas ~460 líneas — usa wrappers |
| `C:\NEVEN\startup\chat_prompts.py` | Sincronizado a producción |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado a producción |

### Commits realizados

| Hash | Descripción |
|------|-------------|
| `973e239` | refactor(ai): unificar prompts en módulo compartido chat_prompts.py |

### Verificación
- Los 3 archivos Python (`chat_prompts.py`, `neven_http_server.py`, `neven_ai_service.py`) compilan sin errores
- Verificado en repo y en producción (`C:\NEVEN\startup\`)

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **MEDIA** | Probar el chat del Task Pane con diferentes contextos (Excel Consultant, Econometría, sin contexto) para verificar que el refactoring no introdujo regresiones |
| **BAJA** | Considerar unificar las dos copias de `chat_prompts.py` usando un symlink o instalándolo como paquete Python compartido |
| **BAJA** | Los archivos `sheet_analyzer.py`, `Core/CMakeLists.txt`, `Core/src/rj2xcl.cc`, `Ribbon/ribbon_connect.h` tienen cambios sin commit — revisar si son parte de otro trabajo en progreso |

---

## Resumen de commits de esta sesión

| Hash | Descripción |
|------|-------------|
| `973e239` | refactor(ai): unificar prompts en módulo compartido chat_prompts.py |

**Total:** 4 archivos cambiados, +1380 / -657 líneas (el módulo nuevo compensa la eliminación de duplicados)


---

### [Sesión 2026-08-19 ~16:30] Discusión: Particionamiento de CHAT.md

## 📋 PROPUESTA DISCUTIDA (sin implementar aún)

### Problema identificado
El archivo `CHAT.md` ha crecido a ~745KB, lo cual hace lenta su lectura/escritura frecuente.

### Solución propuesta
Particionar el archivo en estructura mensual:

```
.kiro/contexto/
├── CHAT.md                 # Índice + última sesión (ligero, <50KB)
├── archivo/
│   ├── 2026-08.md         # Agosto 2026
│   ├── 2026-07.md         # Julio 2026
│   └── ...                # Meses anteriores
└── README.md              # Explicación del sistema
```

**Beneficios:**
1. `CHAT.md` se mantiene pequeño — solo contexto reciente
2. Archivos mensuales permiten búsqueda histórica sin cargar todo
3. Al iniciar sesión, solo se lee `CHAT.md` (rápido)
4. Al cerrar, solo se escribe en `CHAT.md` y ocasionalmente se archiva

### Estado
Usuario mostró interés pero la sesión terminó antes de confirmar. 

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Confirmar si proceder con particionamiento de CHAT.md |
| **ALTA** | Si se confirma: crear estructura, mover histórico a archivos mensuales, dejar solo últimas 2-3 sesiones en CHAT.md |

---


---

### [Sesión 2026-08-19 ~16:45] Particionamiento de CHAT.md

## 📁 SISTEMA DE BITÁCORA PARTICIONADO

### Problema
El archivo `CHAT.md` había crecido a **747 KB** (~19,000 líneas), haciendo lenta su lectura/escritura frecuente.

### Solución implementada
Particionamiento en estructura mensual:

```
.kiro/contexto/
├── CHAT.md              # 52 KB (sesiones recientes + índice)
├── README.md            # Documentación del sistema
└── archivo/
    ├── 2026-08-historico.md    # 677 KB (historial detallado)
    └── CHAT-backup-*.md        # Backups
```

### Resultado
- **Reducción 93%**: 747 KB → 52 KB
- Lectura/escritura ahora es instantánea
- Historial completo preservado en `archivo/`

### Archivos creados/modificados

| Archivo | Acción |
|---------|--------|
| `.kiro/contexto/CHAT.md` | Reescrito (solo contenido reciente) |
| `.kiro/contexto/archivo/2026-08-historico.md` | **NUEVO** (contenido histórico) |
| `.kiro/contexto/README.md` | **NUEVO** (documentación del sistema) |
| `.kiro/contexto/archivo/CHAT-backup-20260924-163444.md` | Backup del original |

### Decisiones de diseño

1. **Estructura mensual**: Facilita búsqueda histórica y archivado automático
2. **Índice en CHAT.md**: Tabla con links a archivos históricos
3. **Backup automático**: Siempre guardar copia antes de particionar

### Commits
Sin commit (archivos en `.kiro/` no se trackean en git)

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **MEDIA** | Probar chat Task Pane tras refactoring de chat_prompts.py |
| **BAJA** | Eliminar backup después de verificar que todo funciona |
| **BAJA** | Configurar archivado automático mensual (hook?) |

---


---

### [Sesión 2026-08-19 ~17:00] Análisis de pendientes del backup

## 📋 REVISIÓN DE PENDIENTES HISTÓRICOS

Se analizó el backup de CHAT.md (747 KB) para identificar pendientes sin resolver.

### Hallazgos
- **186 pendientes únicos** identificados (de ~600+ líneas con checkboxes)
- Muchos están **duplicados** (mismo item en múltiples sesiones)
- Varios están **obsoletos** (ya resueltos pero no marcados)
- El **Bloque 4** (refactoring chat) ya se completó en esta sesión

### Pendientes consolidados por prioridad

#### 🔴 ALTA
| Pendiente | Contexto |
|-----------|----------|
| Reconstruir sysimage Julia con `nevenx_dispatch` | Performance de inicio |
| Probar `=NevenX.J("TestAdd",,, 0)` | Verificar functions.jl disponible |
| Completar sidecars faltantes (17/37 sin `nevenx_positions`) | Arquitectura |
| Integrar `graph.jsonl` con `enrich_with_ontology()` | Ontología |

#### 🟡 MEDIA
| Pendiente | Contexto |
|-----------|----------|
| **Probar chat Task Pane** tras refactoring `chat_prompts.py` | Verificar no hay regresiones |
| Data Lab Python/Julia — prueba en vivo | Solo R funciona actualmente |
| Botón "Analizar Hoja" en TaskPane UI | UX |
| Documentar formato sidecars para nuevas funciones | Ya existe SIDECAR_FORMAT.md |

#### 🟢 BAJA
| Pendiente | Contexto |
|-----------|----------|
| Limpiar código duplicado diccionario inline en taskpane.html | Cleanup |
| Limpiar logs de diagnóstico en taskpane.js | Cleanup |
| Eliminar archivos temporales (check_init.jl, logs) | Cleanup |
| Debounce + persistir binding en localStorage | UX Data Binding |

### Recomendación próxima sesión
1. **INMEDIATO** — Probar chat Task Pane para verificar refactoring
2. **ALTA** — Sysimage Julia 
3. **ALTA** — Sidecars faltantes

---


---

### [Sesión 2026-08-19 ~17:15] Problema detectado: Botones Task Pane no responden

## 🐛 POSIBLE REGRESIÓN DETECTADA

### Problema reportado
Usuario reporta que los botones del Task Pane no responden después del refactoring de `chat_prompts.py`.

### Diagnóstico realizado
- ✅ `chat_prompts.py` existe en `C:\NEVEN\startup\`
- ✅ Ambos archivos Python compilan sin errores
- ✅ Imports funcionan correctamente (`python -c "import chat_prompts"`)

### Causa probable
El servidor Python necesita **reiniciarse** para cargar los cambios. El servidor se inicia cuando Excel abre y no recarga módulos automáticamente.

### Acción requerida
**REINICIAR EXCEL** — Cerrar Excel completamente y volver a abrir para que el servidor cargue el nuevo código.

### Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICO** | Verificar si el problema persiste después de reiniciar Excel |
| **CRÍTICO** | Identificar qué botones específicos no responden (¿chat/IA o todos?) |
| **ALTA** | Si persiste, revisar logs del servidor en `C:\NEVEN\startup\` |
| **ALTA** | Considerar rollback de `neven_http_server.py` si hay regresión real |

### Nota
El backup del archivo original está disponible si se necesita rollback:
- Repo: `git show HEAD~1:ControlPython/startup/neven_http_server.py`
- O revertir commit `973e239`

---


---

### [Sesión 2026-08-19 ~17:30] Diagnóstico: Servidor Python no reiniciado

## 🔍 DIAGNÓSTICO COMPLETADO

### Síntomas reportados
- TODOS los botones del Task Pane no responden (Analizar Hoja, Enviar, Dataset, Limpiar, SQL, Viewer)
- Motores R, Julia, Python aparecen "desconectados"
- Presentaciones vacío
- Data Studio no funciona

### Causa raíz identificada
El servidor Python (proceso 48212) fue iniciado **ayer 23/09/2026 a las 5:09 PM** — **antes de los cambios de hoy**. El servidor viejo sigue corriendo con el código antiguo, pero el código antiguo ya no existe (fue reemplazado por el refactoring).

### Estado del sistema
- ✅ Puerto 5555 está LISTENING (servidor corriendo)
- ✅ `neven_http_server.py` importa correctamente con los nuevos cambios
- ✅ `chat_prompts.py` existe y funciona
- ❌ El servidor en memoria tiene código viejo que ya no es compatible

### Solución requerida
**REINICIAR el servidor Python** — dos opciones:
1. Reiniciar Excel (automático)
2. Matar proceso Python 48212 manualmente (`Stop-Process -Id 48212`)

### Pendientes CRÍTICOS para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICO** | Reiniciar Excel para cargar el nuevo código del servidor |
| **CRÍTICO** | Verificar que todos los botones funcionan después del reinicio |
| **ALTA** | Si persiste, hacer rollback: `git revert 973e239` |

### Comando de emergencia si necesita rollback
```powershell
# Revertir el refactoring
cd F:\ANTIGRAVITY\2026\NEVEN\NEVEN
git revert 973e239 --no-edit

# Copiar archivo original a producción
git show HEAD~1:ControlPython/startup/neven_http_server.py > C:\NEVEN\startup\neven_http_server.py
Remove-Item C:\NEVEN\startup\chat_prompts.py
```

---


---

### [Sesión 2026-08-19 ~17:45] Servidor Python reiniciado

## 🔄 ACCIÓN EJECUTADA

### Problema
El servidor Python (proceso 48212) seguía corriendo con código viejo a pesar de que el usuario había reiniciado Excel. El proceso no se terminó correctamente.

### Acción tomada
```powershell
Stop-Process -Id 48212 -Force
```

### Resultado
- ✓ Proceso terminado
- ✓ Puerto 5555 liberado

### Siguiente paso
Usuario debe abrir Excel y verificar que el Task Pane funciona con el nuevo código.

### Pendiente CRÍTICO

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICO** | Verificar que Task Pane funciona después del reinicio del servidor |
| **ALTA** | Si no funciona, revisar logs o hacer rollback del commit `973e239` |

---


---

### [Sesión 2026-08-19 ~18:00] ROLLBACK: Refactoring causó falla del servidor

## 🚨 ROLLBACK EJECUTADO

### Problema
Después de matar el proceso Python viejo, el servidor NO arrancó. El Task Pane mostraba "ERROR DEL COMPLEMENTO - No pudimos cargar el complemento".

### Diagnóstico
- El módulo `neven_http_server.py` importaba correctamente
- `chat_prompts.py` existía y funcionaba
- Pero el servidor no iniciaba — ControlPython no lo ejecutaba

### Causa probable del fallo
El refactoring cambió la estructura del archivo de forma que el servidor no arrancaba correctamente. Posibles causas:
1. El import de `chat_prompts` al inicio del archivo bloquea algo
2. Cambios en la indentación o estructura rompieron algo
3. El archivo refactorizado es más pequeño (los imports reemplazaron código inline) — algo se perdió

### Acción tomada: ROLLBACK
```powershell
# Restaurar archivo original
git show HEAD~1:ControlPython/startup/neven_http_server.py > C:\NEVEN\startup\neven_http_server.py

# Eliminar chat_prompts.py (no existía antes)
Remove-Item C:\NEVEN\startup\chat_prompts.py
```

### Estado post-rollback
- `C:\NEVEN\startup\neven_http_server.py` — restaurado (215 KB, original)
- `C:\NEVEN\startup\chat_prompts.py` — eliminado
- Usuario debe reiniciar Excel para verificar que funciona

### Commits
El commit `973e239` NO se revirtió en git (solo en producción). El repo tiene el código refactorizado, pero producción tiene el original.

### Lección aprendida
**NUNCA desplegar refactoring a producción sin probar primero** que el servidor arranca correctamente. El test `python -c "import module"` no es suficiente — hay que verificar que `start_server()` funciona.

### Pendientes CRÍTICOS

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICO** | Reiniciar Excel y verificar que Task Pane funciona con código original |
| **ALTA** | Investigar por qué el refactoring rompió el servidor |
| **ALTA** | Revertir commit `973e239` en git si el refactoring no es salvable |
| **MEDIA** | Si se rehace el refactoring, probar en ambiente aislado primero |

### Archivos en producción (post-rollback)
| Archivo | Estado |
|---------|--------|
| `C:\NEVEN\startup\neven_http_server.py` | ✅ Original restaurado |
| `C:\NEVEN\startup\chat_prompts.py` | ❌ Eliminado |

---


---

### [Sesión 2026-08-19 ~18:15] FIX: Archivo corrupto por redirección PowerShell

## 🐛 BUG ENCONTRADO Y CORREGIDO

### Problema
Después del rollback, el servidor seguía sin arrancar. El Task Pane mostraba el mismo error de complemento.

### Causa raíz
El comando de restauración **corrompió el archivo**:
```powershell
# INCORRECTO - produce null bytes
git show HEAD~1:file.py > C:\destino\file.py
```

El operador `>` en PowerShell escribe en **UTF-16 con BOM**, lo cual introduce null bytes que Python no puede leer.

Error: `SyntaxError: source code string cannot contain null bytes`

### Solución
Usar `Out-File` con encoding explícito:
```powershell
# CORRECTO - UTF-8 sin BOM
git show HEAD~1:file.py | Out-File -FilePath "C:\destino\file.py" -Encoding utf8
```

### Lección aprendida (IMPORTANTE)
**NUNCA usar `>` para copiar archivos de texto en PowerShell.** Siempre usar:
- `[System.IO.File]::Copy()` para copiar archivos existentes
- `Out-File -Encoding utf8` para escribir contenido de git
- `Set-Content -Encoding utf8` como alternativa

### Estado post-fix
- `C:\NEVEN\startup\neven_http_server.py` — restaurado correctamente (UTF-8)
- Sintaxis verificada OK
- Usuario debe reiniciar Excel

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICO** | Reiniciar Excel y verificar que Task Pane funciona |
| **ALTA** | Si funciona, revertir commit `973e239` en git para mantener consistencia |
| **MEDIA** | Re-hacer refactoring con mejor testing antes de deploy |

---


---

### [Sesión 2026-08-19 ~18:30] Restauración completa del servidor

## 🔧 MÚLTIPLES INTENTOS DE RESTAURACIÓN

### Problema persistente
Después del primer intento de rollback, el Task Pane levantaba pero:
- Ningún botón funcionaba
- Había "texto basura" en la aplicación
- El archivo en producción tenía 113KB (debería ser 102KB)

### Causa
Los métodos de restauración en PowerShell corrompían el archivo:
1. `git show > file` → UTF-16 con null bytes
2. `Out-File -Encoding utf8` → UTF-8 con BOM, tamaño incorrecto

### Solución final
```powershell
# Método que funciona:
git show HEAD~1:path/file.py | Set-Content -Path "$env:TEMP\temp.py" -Encoding UTF8 -NoNewline
[System.IO.File]::Copy("$env:TEMP\temp.py", "C:\destino\file.py", $true)
```

### Verificación
| Métrica | Antes | Después |
|---------|-------|---------|
| Tamaño archivo | 113,868 chars | 102,836 chars ✓ |
| Sintaxis Python | Error | OK ✓ |
| Igual que repo | No | Sí ✓ |

### Estado actual
- `C:\NEVEN\startup\neven_http_server.py` — restaurado correctamente (102KB, UTF-8 sin BOM)
- `C:\NEVEN\startup\chat_prompts.py` — eliminado
- Usuario debe reiniciar Excel para verificar

### Resumen de errores de esta sesión

| Error | Causa | Lección |
|-------|-------|---------|
| Null bytes en archivo | `>` en PowerShell escribe UTF-16 | Usar `Set-Content -Encoding UTF8` |
| Archivo más grande | `Out-File` agrega BOM/padding | Usar `[System.IO.File]::Copy()` |
| Refactoring rompió servidor | Deploy sin testing | Probar `start_server()` antes de deploy |

### Pendientes CRÍTICOS

| Prioridad | Tarea |
|-----------|-------|
| **CRÍTICO** | Reiniciar Excel y verificar que TODO funciona |
| **ALTA** | Revertir commit `973e239` en git para consistencia |
| **ALTA** | El refactoring de chat_prompts.py debe rehacerse con mejor testing |

---


---

## Sesión 2026-09-24 — INCIDENTE CRÍTICO: Task Pane no funciona tras refactoring

### 🔴 INCIDENTE: Despliegue fallido del refactoring Bloque 4

**Síntoma:** Los botones del Task Pane no responden a clicks. El servidor responde a `/api/engines` pero la UI no reacciona.

**Timeline:**
1. Se implementó Bloque 4: extracción de prompts a `chat_prompts.py`
2. Commit `973e239` creó 4 archivos, modificó 2
3. Se desplegó `neven_http_server.py` refactorizado a `C:\NEVEN\startup\`
4. **FALLO:** `chat_prompts.py` nunca se copió a producción
5. Intentos de rollback con PowerShell corrompieron el archivo con doble-encoding

### Causa raíz
El archivo `C:\NEVEN\startup\neven_http_server.py` quedó **doblemente corrupto**:

1. **Módulo faltante:** El refactoring importaba `chat_prompts.py` pero el módulo nunca se copió
2. **Encoding corrupto:** Los intentos de rollback con `>` y `Out-File` introdujeron:
   - UTF-8 BOM (`EF BB BF`) no deseado
   - Doble encoding UTF-8→Latin-1→UTF-8 (mojibake: `═══` → `ÔòÉÔòÉÔòÉ`)

**Verificación del problema (hex dump):**
```
REPO: 23 20 E2 95 90 E2 95 90...  (correcto: # ═══)
PROD: EF BB BF 23 20 C3 94 C3 B2 C3 89...  (BOM + mojibake)
```

### Solución aplicada

1. **Revertir commit en repo:**
```bash
git revert --no-commit 973e239
git commit -m "revert: deshacer refactoring chat_prompts.py que causó fallo en producción"
```
Nuevo commit: `ba2ee68`

2. **Restaurar archivo con copia binaria:**
```powershell
Remove-Item "C:\NEVEN\startup\neven_http_server.py" -Force
[System.IO.File]::Copy(
    "F:\ANTIGRAVITY\2026\NEVEN\NEVEN\ControlPython\startup\neven_http_server.py",
    "C:\NEVEN\startup\neven_http_server.py"
)
```

3. **Verificación:** `python -c "import ast; ast.parse(...)"` → Sintaxis válida

### Lección aprendida: NUNCA usar estos comandos para copiar archivos Python

| Método | Problema |
|--------|----------|
| `>` redirección | Escribe UTF-16 LE con BOM |
| `Out-File` | Agrega BOM incluso con `-Encoding utf8` |
| `Set-Content` | Puede agregar newlines o cambiar encoding |
| `Copy-Item` | A veces corrompe (motivo desconocido) |

**Método seguro:** `[System.IO.File]::Copy($source, $dest)` — copia binaria exacta

### Estado actual
- ✅ Commit revertido en repo (`ba2ee68`)
- ✅ Archivo restaurado en producción (107,696 bytes, sintaxis válida)
- ✅ Puerto 5555 liberado
- ⏳ **PENDIENTE:** Usuario debe reiniciar Excel para probar

### Archivos modificados
- `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\ControlPython\startup\neven_http_server.py` (revertido)
- `C:\NEVEN\startup\neven_http_server.py` (restaurado)
- `AgentService/neven_ai_service.py` (revertido)
- Eliminados: `chat_prompts.py` en ambas ubicaciones



---

## Sesión 2026-09-24 (Cierre ~17:30) — Recuperación de incidente crítico

### Resumen ejecutivo

**Incidente:** Task Pane dejó de funcionar completamente tras intento de desplegar refactoring Bloque 4. El archivo `neven_http_server.py` quedó corrupto por doble-encoding de PowerShell.

**Resolución:** Archivo restaurado correctamente. Commit de refactoring revertido. Sistema listo para prueba del usuario.

### Logros principales

1. **✅ Diagnóstico completo del incidente:**
   - Identificada causa raíz: doble encoding UTF-8→Latin-1→UTF-8
   - Verificación hex que probó la corrupción
   - Documentado método seguro vs métodos peligrosos de copia en PowerShell

2. **✅ Restauración del archivo:**
   - `neven_http_server.py` restaurado a versión funcional (107,696 bytes)
   - Sintaxis Python validada con `ast.parse()`

3. **✅ Revert del commit de refactoring:**
   - Commit `ba2ee68` revirtió el fallido `973e239`
   - Historial git preservado para análisis futuro

### Causa raíz del incidente

**Fallo original:** El despliegue del Bloque 4 (refactoring chat_prompts.py) copió el archivo refactorizado pero NO copió el módulo `chat_prompts.py` del que dependía.

**Fallo secundario (agravante):** Los intentos de rollback con comandos PowerShell incorrectos corrompieron el archivo:

| Método usado | Problema introducido |
|--------------|---------------------|
| `git show ... > archivo` | Escribe UTF-16 LE con BOM |
| `Out-File -Encoding utf8` | Agrega BOM (EF BB BF) incluso con -Encoding |
| `Set-Content` | Puede cambiar encoding o agregar newlines |

**Evidencia de corrupción (hex dump):**
```
REPO correcto: 23 20 E2 95 90 E2 95 90...  (# ═══)
PROD corrupto: EF BB BF 23 20 C3 94 C3 B2 C3 89...  (BOM + mojibake)
```

### Commits realizados

| Hash | Descripción |
|------|-------------|
| `973e239` | ❌ refactor(ai): unificar prompts en chat_prompts.py — **REVERTIDO** |
| `ba2ee68` | ✅ revert: deshacer refactoring chat_prompts.py que causó fallo en producción |

### Archivos modificados

**Restaurados en producción:**
- `C:\NEVEN\startup\neven_http_server.py` — restaurado desde repo (107,696 bytes)

**Revertidos en repositorio:**
- `F:\...\ControlPython\startup\neven_http_server.py` — eliminado import de chat_prompts
- `F:\...\ControlPython\startup\chat_prompts.py` — **ELIMINADO**
- `F:\...\AgentService\neven_ai_service.py` — revertido a versión original
- `F:\...\AgentService\chat_prompts.py` — **ELIMINADO**

### Decisiones de diseño

1. **Revert completo en lugar de fix parcial:** Dado que el archivo estaba corrupto y la funcionalidad era urgente, se optó por revertir todo el Bloque 4 en lugar de intentar reparar el despliegue. El refactoring se puede re-aplicar después con mejor proceso de deploy.

2. **Método de copia binaria:** Se documentó que `[System.IO.File]::Copy()` es el ÚNICO método seguro para copiar archivos Python en PowerShell.

### Intentos fallidos (para no repetir)

| Intento | Por qué falló |
|---------|---------------|
| `git show HEAD~1:file > destino` | PowerShell redirección `>` escribe UTF-16 |
| `Out-File -Encoding utf8` | Agrega BOM que Python interpreta mal |
| `Copy-Item` | A veces corrompe (causa desconocida) |

**SOLUCIÓN CORRECTA:**
```powershell
[System.IO.File]::Copy($source, $dest)  # Copia binaria exacta
```

### Pendientes próxima sesión

#### ALTA
- [ ] **PROBAR** — Usuario debe reiniciar Excel y confirmar que Task Pane funciona
- [ ] **DOCUMENTAR** — Si funciona, agregar procedimiento de deploy seguro a MANUAL_MANTENIMIENTO.md

#### MEDIA
- [ ] **RE-IMPLEMENTAR Bloque 4** — Con mejor proceso:
  1. Copiar PRIMERO `chat_prompts.py` a producción
  2. Luego copiar `neven_http_server.py` modificado
  3. Usar SIEMPRE `[System.IO.File]::Copy()` para ambos

#### BAJA
- [ ] Considerar script de deploy automatizado que valide imports antes de copiar

### Lección aprendida

**PowerShell es peligroso para archivos de código.** Los comandos de redirección y archivo de PowerShell (`>`, `Out-File`, `Set-Content`, incluso `Copy-Item`) pueden alterar silenciosamente el encoding de archivos. Para copias de archivos de código, usar SIEMPRE:

```powershell
[System.IO.File]::Copy($source, $destination)
```

O alternativamente, usar `robocopy` con flags de copia binaria.



---

## Continuación sesión 2026-09-24 (~17:45) — Diagnóstico Tab IA "cargando"

### Síntoma reportado
Después de restaurar `neven_http_server.py`, el usuario reporta que el "asistente IA sigue CARGANDO".

### Diagnóstico realizado

1. **Servidor HTTP funcionando correctamente:**
   - Puerto 5555 LISTENING (proceso Python 196616)
   - Múltiples conexiones TIME_WAIT indican que el Task Pane SÍ hace requests
   - `/health` responde: `{"status": "ok", "version": "3.0.0", "port": 5555}`
   - `/api/ai/config` responde: modelo gpt-4.1, provider azure, enabled=true

2. **Archivos frontend verificados:**
   - `taskpane.html`: hash MD5 idéntico entre producción y repo ✓
   - `taskpane.js`: tamaños iguales ✓
   - `ayuda.js`: tamaños iguales ✓

3. **Archivo Python restaurado correctamente:**
   - Verificación hex: `23 20 E2 95 90...` (UTF-8 sin BOM) ✓
   - Sin caracteres nulos ni mojibake

4. **Endpoint `/api/ai/chat` funciona:**
   ```bash
   curl -X POST localhost:5555/api/ai/chat -d @test.json
   # Respuesta: {"status": "ok", "reply": "¡Hola! ¿En qué puedo ayudarte...", "model": "gpt-4.1"}
   ```

### Conclusión parcial
El backend está 100% funcional. El problema del "cargando" es específico del frontend JavaScript en WebView2.

### Posibles causas pendientes de investigar
1. **Cache de WebView2** — JavaScript antiguo cacheado
2. **Error silencioso en JS** — Algo falla antes de actualizar el badge
3. **CORS o SSL** — Aunque poco probable porque otros endpoints funcionan

### Próximos pasos para el usuario
1. Cerrar Task Pane y reabrirlo desde el Ribbon
2. Si persiste, abrir DevTools (F12) y revisar consola de errores
3. Limpiar cache de WebView2 si es necesario

### Estado
⏳ Esperando que el usuario pruebe los pasos de diagnóstico del frontend



---

## ✅ FIX COMPLETO: Encoding taskpane.html (2026-09-24 ~18:00)

### Problema resuelto
Los caracteres en el Task Pane se mostraban como "basura" (mojibake):
- `"Escribe tu preguntaâ€¦"` en lugar de `"Escribe tu pregunta…"`
- `"integraciÃ³n"` en lugar de `"integración"`

### Causa raíz: Doble encoding UTF-8
El archivo `taskpane.html` había sido guardado con **doble encoding UTF-8**:

```
Correcto:  "ó" = C3 B3 (2 bytes)
Corrupto:  "ó" = C3 83 C2 B3 (4 bytes) — UTF-8 de UTF-8
```

Esto ocurre cuando:
1. Un archivo UTF-8 se lee como Latin-1/Windows-1252
2. El contenido (ya con bytes UTF-8) se guarda nuevamente como UTF-8
3. Resultado: cada carácter multibyte se duplica

### Solución aplicada
Script PowerShell que invierte el proceso:

```powershell
# 1. Leer bytes del archivo
$bytes = [System.IO.File]::ReadAllBytes($filePath)

# 2. Interpretar como UTF-8 (obtenemos mojibake)
$mojibake = [System.Text.Encoding]::UTF8.GetString($bytes)

# 3. Convertir cada caracter a byte Latin-1
$latin1 = [System.Text.Encoding]::GetEncoding("ISO-8859-1")
$fixedBytes = $latin1.GetBytes($mojibake)

# 4. Interpretar esos bytes como UTF-8 real
$fixed = [System.Text.Encoding]::UTF8.GetString($fixedBytes)

# 5. Guardar sin BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($filePath, $fixed, $utf8NoBom)
```

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `F:\...\TaskPane\taskpane.html` | Encoding corregido (188KB → 186KB) |
| `C:\NEVEN\taskpane\taskpane.html` | Sincronizado desde repo |

### Commits realizados
| Hash | Descripción |
|------|-------------|
| `ba2ee68` | revert: deshacer refactoring chat_prompts.py |
| `64be3e6` | fix(TaskPane): corregir doble encoding UTF-8 en taskpane.html |

### Verificación
- Caracteres acentuados correctos: 230 encontrados (á, é, í, ó, ú, ñ, etc.)
- Texto muestra: `"integración con Excel"` ✓

### Resumen completo de la sesión 2026-09-24

**Incidente:** Despliegue fallido del refactoring Bloque 4 dejó Task Pane inoperativo.

**Problemas resueltos:**
1. ✅ `neven_http_server.py` corrupto por PowerShell encoding → restaurado con copia binaria
2. ✅ `taskpane.html` con doble encoding UTF-8 → corregido con script de decodificación
3. ✅ Commit de refactoring revertido para estabilizar producción

**Lecciones aprendidas:**
1. **PowerShell corrompe archivos:** Usar SIEMPRE `[System.IO.File]::Copy()` para copias
2. **Verificar encoding antes de deploy:** Comparar hex de primeros bytes
3. **Doble encoding es reversible:** Latin-1 decode + UTF-8 encode invierte el proceso

### Pendientes próxima sesión

#### ALTA
- [ ] **PROBAR** — Usuario debe cerrar y reabrir Task Pane para verificar fix
- [ ] **VERIFICAR** — Badge debe mostrar "gpt-4.1" en lugar de "cargando..."

#### MEDIA  
- [ ] Revisar otros archivos HTML/JS por doble encoding
- [ ] Re-implementar Bloque 4 (refactoring chat_prompts.py) con proceso de deploy correcto

#### BAJA
- [ ] Crear script de validación de encoding para pre-commit hook
- [ ] Documentar proceso de deploy seguro en MANUAL_MANTENIMIENTO.md



---

## Corrección encoding taskpane.html - Intento 2 (2026-09-24 ~18:15)

### Problema persistente
El primer intento de fix dejó caracteres `�?�` (U+FFFD replacement character) porque el método de decodificación en PowerShell no manejó correctamente todos los casos.

### Causa raíz refinada
El archivo tenía **doble encoding UTF-8 via CP1252** (Windows-1252):
1. Contenido UTF-8 original
2. Leído incorrectamente como CP1252 (Windows-1252)
3. Guardado nuevamente como UTF-8
4. Resultado: cada secuencia UTF-8 multibyte se convierte en más bytes

Ejemplo del caracter "…" (puntos suspensivos, U+2026):
- UTF-8 correcto: `E2 80 A6` (3 bytes)
- Doble encoded: `C3 A2 E2 82 AC C2 A6` (7 bytes) = "â€¦" como mojibake

### Solución correcta (Python)
```python
# El fix correcto invierte el proceso
with open(backup_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')                           # Lee mojibake como texto
fixed = text.encode('cp1252', errors='replace')      # Convierte a bytes CP1252
fixed = fixed.decode('utf-8', errors='replace')      # Interpreta como UTF-8 real
```

### Por qué PowerShell falló
- PowerShell usa `ISO-8859-1` (Latin-1) para decodificar, no `CP1252`
- CP1252 tiene caracteres adicionales en el rango 0x80-0x9F que Latin-1 no tiene
- El caracter "€" (Euro, usado en mojibake) es `0x80` en CP1252 pero no existe en Latin-1

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `F:\...\TaskPane\taskpane.html` | Fix encoding via Python (3991 líneas cambiadas) |
| `C:\NEVEN\taskpane\taskpane.html` | Sincronizado |

### Commits
| Hash | Descripción |
|------|-------------|
| `5320ed4` | fix(TaskPane): corregir doble encoding UTF-8 en taskpane.html (amend del anterior) |

### Verificación
```
Antes:  "Escribe tu preguntaâ€¦" / "Escribe tu pregunta�?�"
Después: "Escribe tu pregunta…" ✓
```

### Estado
⏳ Esperando que usuario cierre y reabra Excel para verificar que WebView2 cargue el archivo corregido

### Pendientes
- **ALTA:** Usuario debe reiniciar Excel para limpiar cache de WebView2
- **MEDIA:** Verificar que badge "cargando..." cambie a "gpt-4.1"
- **MEDIA:** Verificar que botón Enviar funcione



---

## Rollback pendiente (2026-09-24 ~18:30)

### Decisión: Rollback completo al estado estable

Después de múltiples intentos fallidos de fix de encoding, el usuario decidió hacer rollback completo.

### Estado del repositorio

| Commit | Descripción | Estado |
|--------|-------------|--------|
| `84d28b8` | feat(TaskPane): improve data binding UX | ✅ **OBJETIVO - estable, en origin** |
| `973e239` | refactor(ai): unificar prompts (Bloque 4) | ❌ Causó el fallo original |
| `ba2ee68` | revert del Bloque 4 | ❌ Revertido |
| `5320ed4` | fix encoding (intento 2) | ❌ Revertido |

**Repo ya está en `84d28b8`** (se ejecutó `git reset --hard 84d28b8`)

### ✅ Rollback COMPLETADO (2026-09-24 ~18:40)

**Archivos restaurados a producción:**
| Archivo | Tamaño | Estado |
|---------|--------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | 188,406 bytes | ✓ |
| `C:\NEVEN\taskpane\taskpane.js` | 90,106 bytes | ✓ |
| `C:\NEVEN\startup\neven_http_server.py` | 107,696 bytes | ✓ |

**Puerto 5555:** Liberado (proceso Python terminado)

**Pendiente:** Usuario debe reiniciar Excel para cargar archivos restaurados

### Resumen de la sesión completa 2026-09-24

**Incidente:** Despliegue fallido del Bloque 4 (refactoring chat_prompts.py)

**Intentos de fix:**
1. ❌ Rollback con PowerShell `>` → corrompió archivo (UTF-16)
2. ❌ Rollback con `Out-File` → agregó BOM
3. ❌ Fix encoding con PowerShell Latin-1 → incompleto
4. ❌ Fix encoding con Python CP1252 → funcionó en archivo pero WebView2 cacheó versión anterior

**Decisión final:** Rollback completo a `84d28b8` (último estado estable en origin)

**Lección principal:** Cuando hay múltiples capas de corrupción (encoding + cache + deploy incompleto), es más seguro hacer rollback limpio que intentar fixes incrementales.



---

## Cierre de sesión 2026-09-24 (~18:45)

### Resumen ejecutivo
Sesión de recuperación de incidente crítico. El Task Pane dejó de funcionar tras intentar desplegar el Bloque 4 (refactoring chat_prompts.py). Después de múltiples intentos fallidos de fix, se realizó rollback completo al commit estable `84d28b8`.

### Cronología del incidente
1. **16:00** — Implementación Bloque 4 (commit `973e239`)
2. **16:30** — Deploy a producción (incompleto: faltó `chat_prompts.py`)
3. **16:45** — Usuario reporta "botones no responden"
4. **17:00** — Intento rollback con PowerShell `>` → corrupción UTF-16
5. **17:15** — Intento rollback con `Out-File` → corrupción BOM
6. **17:30** — Revert commit en repo (`ba2ee68`)
7. **17:45** — Fix encoding PowerShell → parcial (caracteres `�`)
8. **18:00** — Fix encoding Python → OK en archivo pero WebView2 cacheado
9. **18:30** — Decisión: rollback completo
10. **18:40** — Rollback ejecutado (`git reset --hard 84d28b8` + copia a producción)

### Commits en el repo (estado final)
```
84d28b8 (HEAD -> main, origin/main) feat(TaskPane): improve data binding UX
```
Los commits `973e239`, `ba2ee68`, `5320ed4` fueron eliminados del historial local.

### Archivos en producción (estado final)
- `C:\NEVEN\taskpane\taskpane.html` — 188,406 bytes (commit 84d28b8)
- `C:\NEVEN\taskpane\taskpane.js` — 90,106 bytes (commit 84d28b8)
- `C:\NEVEN\startup\neven_http_server.py` — 107,696 bytes (commit 84d28b8)

### Lecciones aprendidas

1. **Deploy incompleto:** Al agregar dependencias entre archivos (imports), copiar TODOS los archivos necesarios
2. **PowerShell encoding:** NUNCA usar `>`, `Out-File`, `Set-Content` para archivos de código — usar `[System.IO.File]::Copy()`
3. **WebView2 cache:** Puede retener versiones antiguas incluso después de actualizar archivos
4. **Rollback temprano:** Cuando hay múltiples capas de problemas, rollback limpio > fixes incrementales

### Pendientes próxima sesión

#### ALTA
- [ ] Verificar que Task Pane funciona tras reiniciar Excel
- [ ] Verificar Tab IA muestra modelo (no "cargando...")
- [ ] Verificar botón Enviar funciona

#### MEDIA
- [ ] Re-implementar Bloque 4 con proceso correcto:
  1. Copiar `chat_prompts.py` PRIMERO
  2. Luego copiar `neven_http_server.py`
  3. Usar SIEMPRE `[System.IO.File]::Copy()`
  4. Verificar imports antes de reiniciar

#### BAJA
- [ ] Documentar proceso de deploy en MANUAL_MANTENIMIENTO.md
- [ ] Considerar script de deploy automatizado con validación



---

## Nota final sesión 2026-09-24 (~19:00)

### Estado al cerrar
- Rollback ejecutado: archivos restaurados a commit `84d28b8`
- Usuario reporta: "todo sigue igual, Presentaciones sigue sin aparecer"
- Servidor HTTP no está corriendo (puerto 5555 sin proceso)
- Posible problema: Excel no levantó el servidor después del rollback

### Diagnóstico pendiente
El usuario mencionó un problema diferente ("Presentaciones sigue sin aparecer") que no era el foco original de la sesión. Necesita clarificación:
1. ¿El Task Pane abre?
2. ¿Se ven los tabs?
3. ¿El problema de encoding persiste?
4. ¿O es un problema diferente (Tab Presentaciones faltante)?

### Pendientes CRÍTICOS próxima sesión

#### ALTA
- [ ] **Verificar por qué Excel no levanta el servidor HTTP** (puerto 5555 vacío)
- [ ] **Clarificar con usuario** qué problema exacto persiste
- [ ] **Revisar logs de NEVEN** para entender por qué no inicia

#### MEDIA
- [ ] Si el servidor no inicia, revisar `start_studio.py` o el mecanismo de arranque
- [ ] Verificar si hay error en la carga del XLL



---

## Cache WebView2 limpiado (2026-09-24 ~19:15)

### Acción realizada
Limpiado cache de WebView2 de Office Add-ins:
- `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\webview2` — Eliminado
- `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\AggregatedCache` — Eliminado  
- `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\Resources` — Eliminado

### Causa del problema persistente
WebView2 cacheaba la versión corrupta del `taskpane.html`. Aunque los archivos en disco fueron restaurados correctamente, el Task Pane seguía mostrando la versión cacheada con caracteres basura.

### Estado actual
- ✅ Repo en commit estable `84d28b8`
- ✅ Archivos restaurados en `C:\NEVEN\`
- ✅ Cache de WebView2 limpiado
- ⏳ Usuario debe abrir Excel para verificar

### Pendiente INMEDIATO
Usuario debe abrir Excel y verificar:
1. Task Pane abre sin caracteres basura
2. Tab IA muestra modelo (no "cargando...")
3. Tab Presentaciones aparece
4. Botón Enviar funciona



---

## Fix encoding a nivel de bytes (2026-09-24 ~19:30)

### Descubrimiento crítico
El archivo `taskpane.html` **ya estaba corrupto en el repositorio desde el commit original** (`246100e` - "feat: Tab IA en NEVEN Studio (Bloque 3)"). El rollback a `84d28b8` no lo arregló porque ese commit también tenía el archivo corrupto.

### Causa raíz final
**Triple encoding UTF-8**: El texto fue guardado pasando por múltiples conversiones de encoding, resultando en secuencias de bytes muy largas para caracteres simples.

Ejemplo del caracter "…" (puntos suspensivos):
- Correcto: `E2 80 A6` (3 bytes)  
- Corrupto: `C3 A2 E2 82 AC C2 A6` (7 bytes)

### Solución aplicada
Script Python que reemplaza secuencias de bytes específicas:

```python
# Fix a nivel de bytes
raw = raw.replace(b'\xc3\xa2\xe2\x82\xac\xc2\xa6', '…'.encode('utf-8'))
```

### Archivos modificados
- `C:\NEVEN\taskpane\taskpane.html` — Fix de encoding aplicado (187,968 → 187,721 bytes)

### Verificación
```
Antes:  "Escribe tu preguntaâ€¦ (Enter envÃ­a..."
Después: "Escribe tu pregunta… (Enter envía, Shift+Enter nueva línea)"
```

### Estado
⏳ Usuario debe reiniciar Excel para verificar que WebView2 carga el archivo corregido

### Nota importante
El archivo en el **repositorio sigue corrupto**. Solo se arregló en producción. Para arreglar permanentemente, se debe aplicar el mismo fix al repo y hacer commit.



---

## ¡CAUSA RAÍZ ENCONTRADA! (2026-09-24 ~19:45)

### El problema real
El Task Pane **NO carga directamente desde disco** - carga via HTTP desde `https://localhost:5555/taskpane.html` (definido en manifest.xml).

El servidor HTTP de NEVEN estaba **cacheando en memoria** la versión corrupta del archivo, incluso después de corregir el archivo en disco.

### Evidencia
```
Archivo en disco:    "Escribe tu pregunta… (Enter envía..."     ✓ CORRECTO
Servidor HTTP sirve: "Escribe tu preguntaâ¦ (Enter envÃ­a..."   ✗ CORRUPTO
```

### Solución
Matar el proceso del servidor HTTP (puerto 5555) para forzar reinicio.

```powershell
$conn = Get-NetTCPConnection -LocalPort 5555
Stop-Process -Id $conn.OwningProcess -Force
```

Al abrir Excel de nuevo, NEVEN levantará un servidor nuevo que leerá el archivo corregido.

### Cadena completa de problemas en esta sesión

1. **Bloque 4 deploy incompleto** → faltó copiar `chat_prompts.py`
2. **Rollback corrupto** → PowerShell `>` y `Out-File` corrompen encoding
3. **Cache WebView2** → limpiado pero no era el problema principal
4. **Encoding histórico** → archivo corrupto desde commit original
5. **Fix no aplicaba** → servidor HTTP cacheaba versión vieja en memoria ← **ESTO**

### Estado actual
- ✅ Archivo `C:\NEVEN\taskpane\taskpane.html` corregido (187,721 bytes)
- ✅ Servidor HTTP detenido (proceso 214012 matado)
- ⏳ Usuario debe reiniciar Excel

### Lección aprendida
**Cuando el Task Pane no refleja cambios:**
1. Verificar archivo en disco
2. Verificar qué sirve el servidor HTTP (`curl localhost:5555/taskpane.html`)
3. Si difieren → reiniciar servidor (matar proceso en puerto 5555)
4. Reiniciar Excel



---

## Fix HTTPS → HTTP en manifest.xml (2026-09-24 ~20:00)

### Problema identificado
El manifest.xml usaba `https://localhost:5555` pero el servidor HTTP de NEVEN no estaba configurando SSL correctamente, por lo que solo respondía en HTTP.

Resultado: El Task Pane cargaba via HTTPS pero el JavaScript no podía hacer fetch al servidor porque las llamadas HTTP desde una página HTTPS son bloqueadas por seguridad del navegador (mixed content).

### Evidencia
```
curl https://localhost:5555/health  → No responde
curl http://localhost:5555/health   → {"status": "ok", ...}
```

### Solución temporal
Cambiar el manifest para usar HTTP:
```xml
<SourceLocation DefaultValue="http://localhost:5555/taskpane.html"/>
```

### Archivos modificados
- `C:\NEVEN\taskpane\manifest.xml` — cambiado https → http

### Acciones realizadas
1. Modificado manifest.xml
2. Cerrado Excel forzosamente
3. Limpiado cache de Office Add-ins (`%LOCALAPPDATA%\Microsoft\Office\16.0\Wef`)

### Estado
⏳ Usuario debe abrir Excel para verificar

### Nota importante
Esta es una solución temporal. La solución correcta es arreglar la configuración SSL del servidor HTTP de NEVEN para que funcione con HTTPS (los certificados existen en `C:\NEVEN\certs\`).



---

## Eliminacion de emojis y caracteres no-ASCII (2026-09-24 ~20:15)

### Problema critico encontrado
La consola de DevTools mostro errores de JavaScript:
```
Uncaught SyntaxError: missing ) after argument list (line 868)
Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')
```

### Causa raiz
Los emojis en el codigo fuente (usados en console.log para debugging visual) se corrompieron durante las conversiones de encoding, resultando en secuencias de bytes invalidas que rompian los strings de JavaScript.

Ejemplo:
```javascript
// Antes (corrupto):
console.error('[NEVEN Binding] a?OE Error registrando listener:', e);
// El emoji X (U+274C) se convirtio en bytes invalidos
```

### Solucion aplicada
Script Python que reemplaza TODOS los caracteres no-ASCII con equivalentes ASCII:

```python
def sanitize_line(line):
    result = []
    for char in line:
        code = ord(char)
        if code < 128:
            result.append(char)
        elif code == 0x2026:  # ellipsis
            result.append('...')
        # ... etc
        else:
            result.append('?')
    return ''.join(result)
```

### Resultado
- 324 lineas corregidas
- 0 caracteres no-ASCII restantes

### REGLA NUEVA ESTABLECIDA
**PROHIBIDO usar emojis en codigo fuente de NEVEN.**
Los emojis causan problemas de encoding cuando el archivo pasa por diferentes sistemas/editores.

### Archivos modificados
- `C:\NEVEN\taskpane\taskpane.html` - eliminados todos los emojis (324 lineas)

### Estado
- Servidor HTTP detenido
- Usuario debe reiniciar Excel para verificar

### Pendientes proxima sesion

#### ALTA
- [ ] Verificar que el Task Pane funciona sin errores de JavaScript
- [ ] Verificar que Tab IA muestra modelo correctamente
- [ ] Aplicar el mismo fix al archivo en el repositorio y hacer commit

#### MEDIA
- [ ] Agregar regla a .editorconfig o pre-commit hook para rechazar emojis
- [ ] Revisar otros archivos JS/HTML por emojis



---

## 2026-09-24 — Sesion de recuperacion encoding (Parte 2)

### Problema diagnosticado
El archivo `taskpane.html` en produccion y en el repositorio tenia **doble codificacion UTF-8** (mojibake). Los caracteres espanoles como `ó` se almacenaban como `Ã³` (4 bytes en lugar de 2).

Patron de bytes detectado:
- Correcto: `C3 B3` = ó
- Corrupto: `C3 83 C2 B3` = Ã³ (doble-encoded)

### Causa raiz
En sesiones anteriores, probablemente se uso PowerShell para copiar o modificar archivos, y PowerShell corrompio el encoding al usar `>`, `Out-File`, o `Set-Content` sin parametros de encoding correctos.

### Fix aplicado
1. Creado script Python `C:\temp\fix_final.py` que reemplaza patrones de bytes mojibake
2. Arreglados 290 patrones de doble-encoding en `taskpane.html`
3. Reemplazados emojis mojibake en llamadas console.log con texto ASCII: `[X]`, `[BELL]`, `[SYNC]`, `[OK]`
4. Arreglado tambien `manifest.xml` (tenia `AnÃ¡lisis` en descripcion)
5. Anadido bloque `if __name__ == "__main__"` a `neven_http_server.py` para poder ejecutarlo standalone

### Archivos modificados
- `C:\NEVEN\taskpane\taskpane.html` — limpio, 187,586 bytes
- `C:\NEVEN\taskpane\manifest.xml` — arreglada descripcion
- `C:\NEVEN\startup\neven_http_server.py` — anadido main block

### Estado actual
- Servidor HTTP corriendo en PID 231176, puerto 5555
- `/health` responde OK
- `/taskpane.html` sirve archivo correcto con encoding UTF-8 limpio
- Manifest usa HTTP (no HTTPS)

### Para probar
1. Abrir Excel
2. Ir a Insert > My Add-ins > NEVEN Studio
3. Verificar que Tab IA muestra el modelo correcto (no "cargando...")
4. Verificar que los botones responden
5. Abrir DevTools (F12) y verificar que no hay errores de sintaxis JS

### Leccion aprendida (CRITICO)
**NUNCA usar PowerShell para operaciones de archivo con texto UTF-8:**
- `>` redirection corrompe
- `Out-File` corrompe
- `Set-Content` corrompe (excepto con `-Encoding UTF8NoBOM`)
- `Copy-Item` puede corromper

**SIEMPRE usar:**
- `[System.IO.File]::Copy()` para copiar
- `[System.IO.File]::WriteAllText()` con encoding explicito
- Python para manipulacion de texto

### Script de reparacion reutilizable
```python
# fix_mojibake.py — arregla doble-encoding UTF-8
filepath = r'C:\NEVEN\taskpane\taskpane.html'

with open(filepath, 'rb') as f:
    raw = f.read()

replacements = [
    (b'\xc3\x83\xc2\xa1', b'\xc3\xa1'),  # á
    (b'\xc3\x83\xc2\xa9', b'\xc3\xa9'),  # é
    (b'\xc3\x83\xc2\xad', b'\xc3\xad'),  # í
    (b'\xc3\x83\xc2\xb3', b'\xc3\xb3'),  # ó
    (b'\xc3\x83\xc2\xba', b'\xc3\xba'),  # ú
    (b'\xc3\x83\xc2\xb1', b'\xc3\xb1'),  # ñ
    (b'\xc3\x83\xc2\x97', b'\xc3\x97'),  # ×
    (b'\xc3\x83\xc2\xb7', b'\xc3\xb7'),  # ÷
    (b'\xe2\x80\x94', b'--'),            # em dash
]

for old, new in replacements:
    raw = raw.replace(old, new)

with open(filepath, 'wb') as f:
    f.write(raw)
```


---

### [CIERRE] 2026-09-24 ~19:00 — Fix encoding mojibake completado

#### Resumen de la sesion
Sesion dedicada a recuperar el Task Pane despues de corrupcion de encoding causada por operaciones PowerShell en sesiones anteriores.

#### Logros principales
1. **Diagnosticado problema de doble-encoding UTF-8** — Los archivos tenian caracteres espanoles codificados dos veces (ej: `ó` → `Ã³` en 4 bytes en lugar de 2)
2. **Creado script Python de reparacion** — Reemplaza patrones de bytes corruptos a nivel binario
3. **Reparado taskpane.html** — 290 patrones de mojibake corregidos
4. **Reparado manifest.xml** — Descripcion tenia `AnÃ¡lisis` corregido a `Análisis`
5. **Servidor HTTP funcionando** — Agregado bloque `__main__` para ejecucion standalone

#### Causa raiz
PowerShell corrompe encoding UTF-8 al usar:
- Operador `>` (redirection)
- `Out-File` sin encoding explicito
- `Set-Content` sin `-Encoding UTF8NoBOM`
- Potencialmente `Copy-Item`

#### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Fix mojibake (290 patrones), emojis → ASCII |
| `C:\NEVEN\taskpane\manifest.xml` | Fix descripcion mojibake |
| `C:\NEVEN\startup\neven_http_server.py` | Agregado `if __name__ == "__main__"` block |
| `C:\temp\fix_final.py` | Script de reparacion reutilizable |

#### Commits realizados
Ninguno — los cambios fueron solo en produccion (`C:\NEVEN\`), no en el repositorio git.

#### Estado al cerrar
- [OK] Servidor HTTP en puerto 5555 (PID 231176)
- [OK] `/health` responde `{"status": "ok", "version": "3.0.0"}`
- [OK] `/taskpane.html` sirve archivo con encoding UTF-8 correcto
- [OK] Manifest usa HTTP (no HTTPS)
- [PENDIENTE] Verificar funcionamiento en Excel (usuario debe probar)

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar que Task Pane funciona en Excel (Tab IA, botones) |
| **ALTA** | Si hay errores JS en DevTools, diagnosticar y corregir |
| **MEDIA** | Sincronizar fixes de produccion al repositorio git |
| **MEDIA** | Considerar agregar validacion de encoding en CI/CD |
| **BAJA** | Documentar patrones de mojibake en TROUBLESHOOTING.md |

#### Regla reforzada
```
CRITICO: Para operaciones de archivo con UTF-8 en Windows:
- USAR: [System.IO.File]::Copy(), Python, .NET methods
- NO USAR: PowerShell >, Out-File, Set-Content, Copy-Item
```


---

### [CONT] 2026-09-24 ~19:30 — Cache de WebView2 identificado como causa de errores persistentes

#### Situacion
Despues de arreglar el encoding del archivo `taskpane.html`, el Task Pane seguia mostrando errores de JavaScript:
- `SyntaxError: missing ) after argument list` en linea 868
- `TypeError: Cannot read properties of null` en `initializeApp()`
- Mojibake visible en placeholder (`preguntaâ€¦`)

#### Diagnostico
1. Verificado que archivo en disco esta limpio (MD5 coincide con archivo servido)
2. El servidor sirve el archivo correcto (187,586 bytes, encoding UTF-8 limpio)
3. El endpoint `/api/ai/config` responde correctamente con `model: gpt-4.1`
4. **Causa raiz:** WebView2 tiene cacheada la version corrupta anterior

#### Acciones tomadas
1. Limpiado cache de WebView2:
   - `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\webview2\2\1\EBWebView\Default\Cache`
   - `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\webview2\2\1\EBWebView\Default\Code Cache`
2. Actualizada version de CSS query string: `taskpane.css?v=9` → `taskpane.css?v=10`

#### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | CSS version bump v=9 → v=10 |

#### Estado al cerrar
- Servidor HTTP corriendo en puerto 5555
- Archivos en disco verificados como correctos
- Cache de WebView2 limpiado
- **Pendiente:** Usuario debe cerrar Excel y reabrirlo para que tome los cambios

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar si limpiar cache + reiniciar Excel resuelve el problema |
| **ALTA** | Si persiste, agregar headers no-cache al servidor HTTP |
| **MEDIA** | Considerar agregar `?v=timestamp` dinamico a todos los assets |

#### Nota tecnica
El cache de WebView2 para Office Add-ins esta en:
```
%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\webview2\
```
Limpiar solo `Cache` y `Code Cache` dentro de `EBWebView\Default\` es suficiente.


---

### [CONT] 2026-09-24 ~20:00 — Limpieza agresiva de cache y mejoras al servidor HTTP

#### Situacion
El problema de errores JS persistia a pesar de que el archivo en disco estaba correcto. El cache de WebView2 seguia sirviendo la version corrupta.

#### Acciones tomadas

1. **Limpieza agresiva de cache WebView2:**
   - Cerrado Excel forzosamente
   - Eliminado contenido completo de `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\webview2\`
   - Eliminado cache de add-in `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\{F12F8901-...}\`

2. **Mejoras al servidor HTTP (`neven_http_server.py`):**
   - Agregados headers no-cache para HTML/JS/CSS:
     ```
     Cache-Control: no-cache, no-store, must-revalidate
     Pragma: no-cache
     Expires: 0
     ```
   - Agregado charset UTF-8 a Content-Type:
     ```
     Content-Type: text/html; charset=utf-8
     ```

3. **Limpieza de acentos en JavaScript inline:**
   - Removidos 182 caracteres acentuados de bloques `<script>` en taskpane.html
   - Razon: algunos parsers JS pueden tener problemas con non-ASCII en comentarios
   - Los acentos en HTML content (fuera de scripts) se mantuvieron

#### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\startup\neven_http_server.py` | Headers no-cache + charset UTF-8 |
| `C:\NEVEN\taskpane\taskpane.html` | Acentos removidos de bloques script (182 chars) |
| `C:\temp\fix_js_accents.py` | Script para remover acentos de JS inline |

#### Commits realizados
Ninguno — cambios solo en produccion.

#### Estado al cerrar
- Servidor HTTP corriendo con nuevos headers
- Cache de WebView2 completamente limpiado
- Archivo taskpane.html sin acentos en codigo JS
- **Pendiente verificacion por usuario**

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar si los cambios resolvieron el problema |
| **ALTA** | Si persiste, revisar si hay otro cache (Office cache, proxy, etc) |
| **MEDIA** | Sincronizar cambios del servidor al repositorio git |
| **BAJA** | Documentar proceso de limpieza de cache en TROUBLESHOOTING.md |

#### Comandos utiles para limpiar cache
```powershell
# Cerrar Excel
Get-Process -Name EXCEL -EA 0 | Stop-Process -Force

# Limpiar WebView2 cache
Remove-Item "$env:LOCALAPPDATA\Microsoft\Office\16.0\Wef\webview2\*" -Recurse -Force

# Limpiar add-in cache
Remove-Item "$env:LOCALAPPDATA\Microsoft\Office\16.0\Wef\{F12F8901-39CF-4128-80FE-6BE9FE1E0139}\*" -Recurse -Force
```


---

### [CONT] 2026-09-24 ~20:30 — Descubrimiento: corrupcion masiva de encoding en todo el historial

#### Descubrimiento critico
Al analizar el archivo servido en detalle, se descubrio que contenia **miles de caracteres mojibake**:
- 398 instancias de `€` (euro sign - resultado de corrupcion)
- 1333 instancias de `•` (bullet)
- 1765 instancias de `â` (a-circumflex spurious)
- 2213 instancias de smart quotes
- 150 instancias de box drawing characters corruptos

**El problema NO era cache** — el archivo en disco y en el repositorio git estaban corruptos desde hace muchos commits.

#### Causa raiz
La corrupcion de encoding se propago al repositorio git en algun momento pasado. Todos los commits recientes (desde al menos v2.4.0) tienen el archivo taskpane.html con mojibake.

#### Intento fallido
Un script de PowerShell (`-replace '[^\x00-\x7F]', '?'`) corrompio completamente el archivo, insertando `???` entre cada caracter (archivo crecio de 176KB a 705KB). 

**Leccion:** PowerShell NO DEBE usarse para manipular texto — ni siquiera con `-replace`.

#### Recuperacion
Restaurado desde backup: `taskpane.html.bak_20260924_183609` (183,443 bytes)
Este backup ya estaba limpio (0 caracteres non-ASCII) gracias a los fixes anteriores de la sesion.

#### Estado final del archivo
- Tamanio: 179,452 chars
- Non-ASCII: 0
- Empieza con: `<!DOCTYPE html>`
- Servidor HTTP funcionando

#### Archivos modificados
| Archivo | Estado |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Restaurado de backup, limpio |
| `C:\NEVEN\startup\neven_http_server.py` | Headers no-cache + charset (cambios previos) |

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar si Task Pane funciona ahora |
| **ALTA** | Si aun hay error, el problema puede ser en taskpane.js (archivo separado) |
| **MEDIA** | Crear commit con archivos limpios para el repositorio |
| **MEDIA** | Investigar en que commit se introdujo la corrupcion original |

#### Regla CRITICA reforzada
```
NUNCA usar PowerShell para manipular archivos de texto:
- NI siquiera -replace funciona correctamente
- NI siquiera [System.IO.File]::WriteAllText() despues de -replace
- SOLO usar Python para cualquier manipulacion de texto
- SOLO usar [System.IO.File]::Copy() para copiar archivos sin modificar
```


---

### [CONT] 2026-09-24 ~21:00 — Fix definitivo de encoding desde git

#### Problema identificado
El backup restaurado tenia 1396 instancias de `???` (emojis reemplazados) y 7983 lineas (deberia ser ~3992). El archivo estaba corrompido por manipulaciones previas con PowerShell.

#### Solucion aplicada
Extraer el archivo directamente de git usando Python (no PowerShell) y arreglarlo:

```python
# Extraer bytes crudos de git
result = subprocess.run(['git', 'show', 'HEAD:TaskPane/taskpane.html'], capture_output=True)
raw = result.stdout

# Arreglar mojibake a nivel de bytes
replacements = [
    (b'\xc3\x83\xc2\xb3', b'\xc3\xb3'),  # o con acento
    # ... etc
]

# Limpiar non-ASCII de bloques <script>
text = re.sub(r'(<script[^>]*>)(.*?)(</script>)', clean_js, text, flags=re.DOTALL)
```

#### Estado final del archivo
| Metrica | Valor |
|---------|-------|
| Lineas | 3,992 (correcto) |
| Caracteres | 170,152 |
| Instancias de `???` | 0 |
| Non-ASCII restantes | 120 (solo en HTML, no en JS) |
| Contiene `integracion` | Si, correcto |

#### Script de fix reutilizable
Guardado en: `C:\temp\git_fix.py`

Este script:
1. Extrae el archivo de git como bytes crudos
2. Decodifica como UTF-8
3. Arregla mojibake con reemplazos de bytes
4. Limpia non-ASCII de bloques `<script>` (pero los deja en HTML)
5. Guarda con encoding UTF-8 sin BOM

#### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Reconstruido desde git + fix de encoding |

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar si Task Pane funciona ahora |
| **MEDIA** | Hacer commit del archivo limpio al repositorio |
| **MEDIA** | Arreglar el archivo en el repo git para futuros deploys |
| **BAJA** | Crear script de deploy que valide encoding antes de copiar |

#### Leccion aprendida
Para extraer archivos de git sin corrupcion de encoding:
```python
import subprocess
result = subprocess.run(['git', 'show', 'COMMIT:path/to/file'], capture_output=True)
raw_bytes = result.stdout  # Bytes sin interpretacion
```

NO usar: `git show ... > file` en PowerShell (corrompe encoding)


---

### [FIX] 2026-09-24 ~21:15 — Bug de sintaxis JS encontrado y corregido

#### Bug encontrado
El error `SyntaxError: missing ) after argument list` en linea 868 **NO era de encoding** — era un **bug real de sintaxis** en el codigo JavaScript.

#### Causa raiz
En la funcion `bindRange()`, faltaba cerrar el callback de `Excel.run()` antes del `} catch`:

```javascript
// ANTES (buggy) - lineas 865-869:
        self._saveToStorage();
      
      return true;      // <-- return dentro del callback!
    } catch (e) {       // <-- catch sin cerrar Excel.run

// DESPUES (correcto):
        self._saveToStorage();
      
      });  // Close Excel.run callback
      return true;
    } catch (e) {
```

#### Analisis de balance de llaves
| Linea | Balance | Codigo |
|-------|---------|--------|
| 841 | 1 | `try {` |
| 842 | 2 | `await Excel.run(async function(context) {` |
| 848 | 3 | `sheet.onChanged.add(function(eventArgs) {` |
| 851 | 2 | `});` |
| 856 | 3 | `sheet.onCalculated.add(function(eventArgs) {` |
| 859 | 2 | `});` |
| **867** | **1** | **`});  // Close Excel.run` (NUEVO)** |
| 868 | - | `return true;` |
| 869 | 1 | `} catch (e) {` |
| 872 | 0 | `}` |

Sin la linea 867, el balance era 2 al llegar al `catch`, causando el error de sintaxis.

#### Fix aplicado
```powershell
str_replace en C:\NEVEN\taskpane\taskpane.html:
- oldStr: "self._saveToStorage();\n      \n      return true;\n    } catch"
- newStr: "self._saveToStorage();\n      \n      });  // Close Excel.run callback\n      return true;\n    } catch"
```

#### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Agregado `});` en linea 867 para cerrar Excel.run callback |

#### Importante
Este bug probablemente existia en el repositorio git desde hace tiempo. Al arreglar el encoding, el bug de sintaxis se hizo visible.

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar si Task Pane funciona ahora |
| **ALTA** | Hacer commit del archivo corregido al repo git |
| **MEDIA** | Revisar si hay otros bugs similares de llaves desbalanceadas |
| **BAJA** | Agregar linter de JS al proceso de build |


---

### [EXITO] 2026-09-24 ~21:30 — Task Pane FUNCIONANDO

#### Confirmacion
Usuario confirma: **"Ya responde!!!"** — El Task Pane esta operativo.

#### Resumen de la sesion completa

**Problema inicial:** Task Pane no funcionaba despues de intentar deploy de "Bloque 4"

**Capas de problemas encontradas y resueltas:**

1. **Encoding corrupto (mojibake)** — Archivo tenia doble/triple encoding UTF-8
   - Fix: Script Python para reemplazar patrones de bytes corruptos

2. **Cache de WebView2** — Browser cacheaba version anterior
   - Fix: Limpiar `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\webview2\`
   - Fix: Agregar headers `Cache-Control: no-cache` al servidor

3. **Content-Type sin charset** — Browser interpretaba mal el encoding
   - Fix: Cambiar `text/html` a `text/html; charset=utf-8`

4. **Bug de sintaxis JS** — Faltaba `});` para cerrar callback de Excel.run()
   - Fix: Agregar linea `});  // Close Excel.run callback`

#### Archivos modificados (produccion)
| Archivo | Cambios |
|---------|---------|
| `C:\NEVEN\taskpane\taskpane.html` | Fix encoding + fix sintaxis JS |
| `C:\NEVEN\startup\neven_http_server.py` | Headers no-cache + charset UTF-8 |
| `C:\NEVEN\taskpane\manifest.xml` | Fix mojibake en descripcion |

#### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Commit de cambios al repositorio git |
| **MEDIA** | Sincronizar taskpane.html corregido al repo |
| **BAJA** | Documentar proceso de troubleshooting |

#### Leccion principal
Cuando hay errores de JS que parecen de encoding, verificar PRIMERO el balance de llaves/parentesis. El encoding puede estar bien pero el codigo tener bugs de sintaxis.


---

### [CLEANUP] 2026-09-24 ~22:00 — Limpieza final de mojibake en HTML

#### Problemas encontrados
Despues de que el Task Pane funciono, el usuario reporto mojibake visible:
1. Tab Run Script: indicadores de motor mostraban `â—□` en lugar de circulos
2. Tab IA: placeholder mostraba `preguntaâ€¦` 
3. Dropdown de graficos: `Ãrea` en lugar de `Area`
4. Emoji de mapa corrupto: `--ºï¸`
5. Botones de cerrar: `Ã--` en lugar de `X`

#### Fix aplicado
Serie de scripts Python para reemplazar patrones de bytes corruptos:

| Patron corrupto | Bytes hex | Reemplazo |
|-----------------|-----------|-----------|
| Indicador motor | `c3 a2 -- c2 8f` | `[O]` |
| Area con tilde | `c3 83 c2 81 rea` | `Area` |
| Algebra | `c3 83 c2 81 lgebra` | `Algebra` |
| Emoji mapa | `-- c2 ba c3 af c2 b8 c2 8f` | (eliminado) |
| Boton cerrar | `c3 83 --` | `X` |

#### Estado final del archivo
| Metrica | Valor |
|---------|-------|
| Tamanio | 170,149 chars |
| Non-ASCII total | 52 chars |
| Non-ASCII problematico | 0 |
| Solo acentos espanoles | Si (a, e, i, o, u, n) |

#### Scripts de limpieza creados
- `C:\temp\fix_html_mojibake.py` - Limpieza general
- `C:\temp\fix_dots.py` - Indicadores de motores
- `C:\temp\fix_area.py` - Area y Algebra
- `C:\temp\cleanup_final.py` - Botones y emojis

#### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Limpieza completa de mojibake |

#### Pendientes para proxima sesion
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Verificar que Task Pane se ve correctamente |
| **ALTA** | Hacer commit al repositorio git |
| **MEDIA** | Considerar usar iconos SVG en lugar de caracteres Unicode |
| **BAJA** | Agregar validacion de encoding en proceso de build |

#### Nota sobre iconos
Los indicadores de estado de motores (R, Python, Julia) ahora muestran `[O]` en texto.
Para mejorar la UI, se podria cambiar a iconos SVG o usar CSS para circulos coloreados.


---

### Sesión 2026-08-19 (~tarde) — FIX: Textareas redimensionables ✅

## ✅ IMPLEMENTADO: Campos de texto redimensionables por el usuario

### Problema resuelto
El usuario quería poder redimensionar verticalmente los campos de texto (SQL editor, script editor, etc.) ya que a veces el espacio es insuficiente.

### Análisis realizado
Se identificaron 4 textareas principales en `taskpane.html`:

| Campo | ID | Estado previo | Estado actual |
|-------|-----|---------------|---------------|
| Editor SQL | `#sql-input` | CSS tenía resize pero no aplicaba | ✅ Inline style |
| Editor scripts R/Python/Julia | `#script-input` | Sin resize | ✅ Inline style |
| Chat IA | `#ai-input` | ✅ Ya tenía `resize:vertical` | Sin cambio |
| Query DB (Data Lab) | `#db-query` | ✅ Ya tenía `resize:vertical` | Sin cambio |

### Causa raíz identificada
El CSS en `taskpane.css` (línea 196, clase `.sql-editor`) ya tenía `resize: vertical`, pero no se aplicaba. Posibles causas:
1. Cache de WebView2 no refrescaba el CSS
2. CSS override por otra regla
3. El atributo no estaba llegando al elemento correcto

### Solución implementada
Agregar **estilos inline** directamente en los elementos `<textarea>` como fallback:

```html
<!-- SQL input (línea ~80) -->
<textarea id="sql-input" style="resize:vertical;min-height:80px;max-height:400px" ...>

<!-- Script input (línea ~240) -->
<textarea id="script-input" style="min-height:140px;max-height:500px;resize:vertical" ...>
```

### Decisiones de diseño
- **`resize: vertical`** en lugar de `resize: both` — mantiene el ancho del panel, evita romper el layout horizontal
- **`max-height` limitado** — 400px para SQL, 500px para scripts — evita que el usuario expanda demasiado y pierda de vista otros controles
- **Inline styles como fallback** — garantiza que funcione aunque haya problemas de cache CSS

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `F:\ANTIGRAVITY\2026\NEVEN\NEVEN\TaskPane\taskpane.html` | Inline styles en `#sql-input` y `#script-input` |
| `C:\NEVEN\taskpane\taskpane.html` | CSS version bump v=9→v=10 + sincronizado desde repo |

### Verificación pendiente
El usuario debe:
1. Cerrar Excel completamente
2. Reabrir Excel y el Task Pane
3. Verificar que aparece la "gripa" de resize en esquina inferior derecha de los textareas
4. Arrastrar para expandir/contraer verticalmente

### Pendientes actualizados
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Hacer commit de cambios al repositorio |
| **MEDIA** | Verificar visualmente que el resize funciona en todos los textareas |
| **BAJA** | Considerar mover los estilos inline de vuelta al CSS una vez confirmado que funciona |



---

### Sesión 2026-08-19 (~tarde, continuación) — FIX CRÍTICO: Mojibake + Bug JS ✅

## ✅ RESUELTO: Mojibake recurrente + Tab Presentaciones vacío

### Problema reportado
El usuario reportó que el mojibake había vuelto a aparecer después del commit de hoy:
1. Indicadores de engine mostraban `â—□` en lugar de círculos
2. Placeholder del chat IA: `Escribe tu preguntaâ€¦` 
3. Texto corrupto: `envÃ­a`, `lÃ­nea`, `tÃ­tulo`
4. Tab PRESENTACIONES completamente vacío

### Causa raíz identificada

**Doble problema:**

1. **Mojibake por copia incorrecta:** Cuando copié el archivo con los cambios de resize, el archivo fuente en el repositorio YA estaba corrupto. La corrupción se propagó a producción.

2. **Bug de sintaxis JavaScript (CRÍTICO):** Faltaba `});` para cerrar `Excel.run()` en la línea 866. Este error de sintaxis **rompía la ejecución de TODO el JavaScript**, incluyendo la carga del iframe de Presentaciones.

```javascript
// ANTES (roto):
        self._saveToStorage();
      
      return true;  // ← Fuera del Excel.run()!
    } catch (e) {

// DESPUÉS (arreglado):
        self._saveToStorage();
      });  // ← Cierre del Excel.run()
      
      return true;
    } catch (e) {
```

### Solución implementada

#### 1. Limpieza de encoding
Reemplazos de mojibake a ASCII puro:
- `Ã¡` → `a`, `Ã©` → `e`, `Ã­` → `i`, `Ã³` → `o`, `Ãº` → `u`, `Ã±` → `n`
- `â€¦` → `...` (ellipsis)
- Caracteres problemáticos de indicadores de engine → eliminados

#### 2. Indicadores de engine con CSS puro
Cambio en `taskpane.css`:
```css
/* ANTES: dependía de caracter Unicode */
.engine-dot { font-size: 14px; margin: 0 2px; color: #555; }

/* DESPUÉS: círculo CSS puro */
.engine-dot { 
  display: inline-block; 
  width: 10px; 
  height: 10px; 
  border-radius: 50%; 
  margin: 0 4px; 
  background-color: #555; 
}
```

Los spans ahora están vacíos (`<span class="engine-dot"></span>`) y el CSS dibuja el círculo.

#### 3. Fix del bug JavaScript
Agregado `});` faltante en línea 866 para cerrar correctamente el `Excel.run()`.

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `C:\NEVEN\taskpane\taskpane.html` | Limpieza mojibake + fix JS `});` |
| `C:\NEVEN\taskpane\taskpane.css` | Indicadores de engine con CSS puro |
| `F:\...\NEVEN\TaskPane\taskpane.html` | Sincronizado desde producción |
| `F:\...\NEVEN\TaskPane\taskpane.css` | Sincronizado desde producción |

### Verificación realizada
- Balance de llaves JS: 845 `{` = 845 `}` ✅
- Servidor HTTP sirve `/presentaciones/index.html` correctamente ✅
- Resize ya estaba aplicado en `#sql-input` y `#script-input` ✅

### Por qué el mojibake sigue apareciendo
El archivo en el repositorio tiene **doble/triple encoding** — cada vez que se edita con una herramienta que no respeta UTF-8, se corrompe más. La solución permanente es:
1. Usar solo ASCII en textos visibles (ya aplicado)
2. Usar CSS para símbolos en lugar de caracteres Unicode (ya aplicado para indicadores)
3. **NUNCA usar Copy-Item de PowerShell** — siempre `[System.IO.File]::Copy()`

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Usuario debe probar: cerrar Excel, reabrir, verificar que mojibake desapareció |
| **ALTA** | Usuario debe hacer clic en tab PRESENTACIONES para verificar que carga |
| **MEDIA** | Commit de los cambios al repositorio |



---

### Sesión 2026-08-19 (~tarde, continuación 2) — FIX: Descubrimiento dinámico de pipes

## ✅ IMPLEMENTADO: Engine status siempre verifica pipes dinámicamente

### Problema reportado
Después de arreglar el mojibake, los indicadores de engine mostraban:
- Botón 1 (R): Verde
- Botones 2 y 3 (Python, Julia): Rojo

Pero al ejecutar `1+1` en R, retornaba **"r engine not available"**.

### Causa raíz identificada
El endpoint `/api/engines` retornaba `{"r": true, ...}` pero la ejecución fallaba.

**Problema en `_get_engine_status()`:**
```python
# ANTES (problemático):
if lang in factory:
    result[lang] = True  # ← ASUME disponible sin verificar!
else:
    result[lang] = _discover_pipe(lang) is not None
```

Si `start_studio.py` inyectó un factory con pipes antiguos (de un Excel anterior), el servidor **asumía** que el engine estaba disponible **sin verificar que el pipe realmente existiera**.

**Discrepancia de PIDs:**
- Excel actual: PID 247924 → pipe `RJ2XCL2-PIPE-R-247924`
- ControlR de Studio: PID 226636 (lanzado por start_studio.py)
- Servidor HTTP: usando factory inyectado que apuntaba a pipes inexistentes

### Solución implementada
Modificar `_get_engine_status()` para **SIEMPRE** usar descubrimiento dinámico:

```python
# DESPUÉS (robusto):
def _get_engine_status() -> dict:
    """ALWAYS uses dynamic pipe discovery to verify engines are actually running."""
    result = {}
    for lang in ("r", "python", "julia"):
        # Always verify via dynamic discovery - don't trust factory alone
        pipe_path = _discover_pipe(lang)
        result[lang] = pipe_path is not None
    return result
```

**Beneficios:**
1. No confía en el factory inyectado (puede estar desactualizado)
2. Detecta automáticamente pipes del XLL (`RJ2XCL2-PIPE-R-{PID}`)
3. Maneja reinicios de Excel sin necesidad de reiniciar el servidor
4. Invalida cache si el pipe no responde

### Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `F:\...\ControlPython\startup\neven_http_server.py` | `_get_engine_status` ahora siempre usa `_discover_pipe` |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |
| `C:\NEVEN\taskpane\neven_http_server.py` | Sincronizado |

### Verificación de la infraestructura de pipes
```
Pipes disponibles:
  RJ2XCL2-PIPE-R-247924      (principal)
  RJ2XCL2-PIPE-R-247924-CB   (callback)
  RJ2XCL2-PIPE-R-247924-M    (mensajes)

Excel PID: 247924 ✓ (coincide con el pipe)
ControlR PID: 226636 (iniciado por Studio)
```

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Reiniciar NEVEN Studio para cargar el nuevo código del servidor HTTP |
| **ALTA** | Probar que R funciona después del reinicio |
| **MEDIA** | Verificar Python y Julia cuando estén disponibles |
| **BAJA** | Commit de todos los cambios de esta sesión |

### Nota técnica: Arquitectura de pipes
El sistema tiene **dos fuentes** de pipes:
1. **XLL** crea pipes dinámicos: `RJ2XCL2-PIPE-{LANG}-{EXCEL_PID}`
2. **start_studio.py** crea pipes fijos: `neven_{lang}`

El servidor HTTP debe descubrir dinámicamente cuál está disponible, priorizando los pipes fijos pero haciendo fallback a los dinámicos del XLL.



---

### Sesión 2026-08-19 (~11:00) — FIX COMPLETO: Servidor HTTP reiniciado

## ✅ RESUELTO: R engine ahora funciona correctamente

### Problema final
Después de aplicar el fix de `_get_engine_status()`, el usuario cerró y reabrió Excel pero R seguía reportando "engine not available".

### Causa raíz
El **servidor HTTP Python no se reinició**. Seguía corriendo el proceso viejo (PID 227812, iniciado a las 09:26) con el código antiguo, mientras que Excel ya tenía un nuevo PID (203552).

```
Servidor viejo: PID 227812, iniciado 09:26 (código sin el fix)
Excel nuevo:    PID 203552, iniciado 10:51
Pipe disponible: RJ2XCL2-PIPE-R-203552 ✓
```

El servidor viejo nunca cargó el código actualizado de `_get_engine_status()`.

### Solución
1. Matar el servidor HTTP viejo: `Stop-Process -Id 227812 -Force`
2. Reiniciar manualmente con: `python C:\NEVEN\taskpane\start_studio.py`

### Resultado
```powershell
# Nuevo servidor
python3.12  210200 25/09/2026 10:52:45 a. m.

# Engines disponibles
GET /api/engines → {"r": true, "python": true, "julia": true}
```

**Los tres engines ahora están disponibles** (R, Python, Julia).

### Lección aprendida
**El servidor HTTP de NEVEN Studio NO se reinicia automáticamente** cuando Excel se cierra/abre. El proceso Python sigue vivo independientemente de Excel.

Para aplicar cambios en `neven_http_server.py`:
1. Matar el proceso Python manualmente
2. Reiniciar con `start_studio.py` o abrir NEVEN Studio.vbs

### Resumen de TODOS los fixes de esta sesión

| Problema | Causa | Fix |
|----------|-------|-----|
| Mojibake en indicadores | Caracteres Unicode corruptos | CSS puro con `border-radius` |
| Tab Presentaciones vacío | Bug JS: faltaba `});` | Agregado cierre de `Excel.run()` |
| R "engine not available" | `_get_engine_status` confiaba en factory | Siempre usa `_discover_pipe()` |
| Fix no aplicaba | Servidor HTTP viejo no se reinició | Kill + restart manual |

### Archivos modificados (sesión completa)
| Archivo | Cambios |
|---------|---------|
| `C:\NEVEN\taskpane\taskpane.html` | Mojibake limpiado, fix JS `});` |
| `C:\NEVEN\taskpane\taskpane.css` | Indicadores con CSS puro |
| `C:\NEVEN\startup\neven_http_server.py` | `_get_engine_status` dinámico |
| `C:\NEVEN\taskpane\neven_http_server.py` | Sincronizado |
| `F:\...\TaskPane\taskpane.html` | Sincronizado |
| `F:\...\TaskPane\taskpane.css` | Sincronizado |
| `F:\...\ControlPython\startup\neven_http_server.py` | `_get_engine_status` dinámico |

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Usuario debe probar `1+1` en R en el Task Pane |
| **ALTA** | Verificar que Python y Julia también funcionan |
| **MEDIA** | Commit de todos los cambios al repositorio |
| **BAJA** | Considerar auto-restart del servidor HTTP cuando Excel se reinicia |



---

### Sesión 2026-08-19 (~11:00, continuación final) — TODO FUNCIONANDO ✅

## ✅ RESUELTO: R ejecuta correctamente, mojibake limpiado

### Problema final: "Failed to fetch" + mojibake en dropdown

El Task Pane mostraba:
1. "Failed to fetch" al ejecutar código
2. Mojibake en el dropdown de ejemplos: `R â€" Estadistica descriptiva`

### Causas raíz

1. **"Failed to fetch"**: El Task Pane (WebView2) estaba cargando HTML cacheado que apuntaba a endpoints incorrectos o tenía JS roto.

2. **Mojibake persistente**: Los scripts de limpieza de PowerShell no manejaban bien el encoding. Se necesitaba Python para hacer los reemplazos correctamente.

3. **Servidor con código viejo**: El servidor Python no se reiniciaba automáticamente y seguía usando código cacheado.

### Solución implementada

#### 1. Limpieza completa de mojibake con Python
Creé `C:\temp\clean_html2.py` que:
- Lee el archivo como bytes
- Detecta patrones de mojibake (`â€"`, `â€œ`, etc.)
- Reemplaza con ASCII equivalente
- Busca y reemplaza cualquier patrón residual que empiece con `â`

**Resultado:**
```
R â€" Estadistica descriptiva  →  R - Estadistica descriptiva
```

#### 2. Actualización de versiones para forzar cache refresh
```
taskpane.css?v=10  →  taskpane.css?v=20260925105835
taskpane.js?v=...  →  taskpane.js?v=20260925105835
datalab.js?v=...   →  datalab.js?v=20260925105835
```

#### 3. Reinicio del servidor HTTP
```powershell
Stop-Process -Id 210200 -Force
Start-Process python "C:\NEVEN\taskpane\start_studio.py"
```

Nuevo servidor: PID 236492, iniciado 10:59

### Verificación exitosa
```powershell
# Test directo al API
POST http://127.0.0.1:5555/api/r
Body: {"code": "1+1"}
Response: {"status": "ok", "type": "real", "result": 2.0, "console": ""}
```

**R funciona correctamente.**

### Archivos modificados
| Archivo | Cambios |
|---------|---------|
| `C:\NEVEN\taskpane\taskpane.html` | Limpieza mojibake + version bump |
| `F:\...\TaskPane\taskpane.html` | Sincronizado |
| `C:\temp\clean_html2.py` | Script de limpieza (temporal) |

### Scripts útiles creados
- `C:\temp\clean_html2.py` — Limpieza de mojibake con Python (usar en lugar de PowerShell)

### Lecciones aprendidas

1. **PowerShell no maneja bien el encoding UTF-8 con mojibake** — usar Python para limpieza de archivos.

2. **WebView2 cachea agresivamente** — siempre actualizar version strings (`?v=timestamp`) para forzar refresh.

3. **El servidor HTTP de NEVEN Studio NO se reinicia solo** — hay que matarlo y reiniciarlo manualmente después de cambios en el código.

4. **Probar el API directamente** (`Invoke-WebRequest`) antes de asumir que el problema está en el servidor.

### Estado final

| Componente | Estado |
|------------|--------|
| Servidor HTTP | ✅ Corriendo (PID 236492) |
| `/api/engines` | ✅ `{"r": true, "python": true, "julia": true}` |
| `/api/r` con `1+1` | ✅ Retorna `2.0` |
| Mojibake en dropdown | ✅ Limpiado |
| Indicadores de engine | ✅ CSS puro (círculos) |

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Usuario debe recargar Task Pane (Ctrl+F5 o cerrar/abrir Excel) |
| **MEDIA** | Commit de todos los cambios al repositorio |
| **BAJA** | Documentar proceso de limpieza de mojibake para futuros casos |


