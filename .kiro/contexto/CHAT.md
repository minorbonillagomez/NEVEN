# NEVEN — Bitácora de Sesión de Trabajo con Kiro

> **Propósito:** Registro de sesiones de trabajo recientes.
> Para historial anterior, ver CHAT_LARGO.md en este mismo directorio.
> **Última actualización:** 2026-08-19 (sesión: RAG multi-formato + browse)

---
### Sesión 2026-08-19 (~12:45) — EN PROGRESO: Soporte multi-idioma RAG

## 🔧 EN PROGRESO: Columna `language` y traducción de queries

### Contexto
El usuario reportó que al preguntar por "ACP" (Análisis de Componentes Principales), el RAG devolvía fuentes de Excel en lugar de estadística. Causa: los libros están en inglés y usan "PCA", el score semántico era bajo (< 0.70).

Se solicitó:
1. Agregar metadato de idioma por documento (`language`)
2. Traducir queries automáticamente al idioma de los libros indexados
3. Idiomas soportados: inglés (en), español (es), portugués (pt), francés (fr)

### Cambios realizados

**1. Schema de base de datos actualizado (`rag_engine.py`):**
```sql
CREATE TABLE documents (
    ...
    language VARCHAR DEFAULT 'en',  -- NUEVO
    ...
)
```

**2. Método `add_pdf_with_pages` actualizado:**
```python
def add_pdf_with_pages(self, file_path, doc_name, domain="general", 
                       language="en", metadata=None):  # NUEVO parámetro
```

**3. Método `get_available_languages()` agregado:**
```python
def get_available_languages(self) -> List[str]:
    """Retorna lista de idiomas únicos en el índice."""
```

**4. Diccionario de traducciones bidireccional ES↔EN:**
Ya existía en el servidor HTTP (`_term_translations`) y en `rag_engine.py` (`translate_query_for_languages`).

**5. Script de indexación actualizado (`index_books.py`):**
```python
# Formato: (ruta, dominio, nombre, idioma)
BOOKS = [
    (r"...\wooldridge.pdf", "econometria", "Wooldridge", "en"),
    ...
]
```

### Archivos modificados

| Archivo repo | Cambio |
|--------------|--------|
| `NEVEN/TaskPane/rag_engine.py` | +language en schema y add_pdf_with_pages |
| `NEVEN/Install/scripts/index_books.py` | Tuplas de 4 elementos con idioma |

| Archivo producción | Cambio |
|--------------------|--------|
| `C:\NEVEN\TaskPane\rag_engine.py` | Sincronizado desde repo |

### Estado de re-indexación

**El proceso de indexación está EN CURSO** al momento de cerrar la sesión:
- PID: 161324
- Tiempo corriendo: ~9 minutos
- CPU consumido: ~60 min (7x paralelo)
- Memoria RAM: 8.5 GB
- Estado: Generando embeddings con fastembed

El proceso es válido — fastembed genera todos los embeddings en memoria antes de escribir a DuckDB, por eso la DB aún muestra 0.01 MB.

### Servidor HTTP detenido

El servidor HTTP (PID 166808) fue detenido para liberar la base de datos durante la re-indexación. **DEBE reiniciarse** después de que termine la indexación.

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Esperar a que termine indexación (~5-10 min más) |
| **ALTA** | Reiniciar servidor HTTP: `cd C:\NEVEN\startup; python neven_http_server.py` |
| **ALTA** | Verificar que la tabla documents tenga columna `language` |
| **ALTA** | Expandir diccionario de traducciones a 4 idiomas (EN/ES/PT/FR) — quedó interrumpido |
| **MEDIA** | git commit + push de cambios de idioma |
| **MEDIA** | Integrar `translate_query_for_languages()` del RAGEngine en vez de `_term_translations` duplicado |
| **BAJA** | Agregar libros en español/portugués/francés para probar multi-idioma |

### Notas técnicas

- La base de datos existente **no tenía** columna `language` — por eso se necesita re-indexar
- fastembed usa ~8.5 GB de RAM con el modelo `bge-small-en-v1.5`
- Ratio CPU/Real de 7x indica procesamiento paralelo saludable
- Total estimado: ~3400 páginas = ~6800 chunks = ~15-25 min de indexación



---

### Sesión 2026-08-19 (~12:50) — COMPLETADO: Soporte multi-idioma RAG

## ✅ COMPLETADO: Columna `language` y traducción de queries multilingüe

### Contexto
El usuario reportó que al preguntar por "ACP" (Análisis de Componentes Principales en español), el RAG devolvía fuentes de Excel en lugar de estadística. Causa: los libros están en inglés y usan "PCA", el score semántico era bajo.

Se solicitó:
1. Agregar metadato de idioma por documento (`language`)
2. Traducir queries automáticamente al idioma de los libros
3. Idiomas soportados: inglés (en), español (es), portugués (pt), francés (fr)

### Implementación completada

**1. Schema de base de datos actualizado:**
```sql
CREATE TABLE documents (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR,
    domain VARCHAR,
    language VARCHAR DEFAULT 'en',  -- NUEVO
    created_at TIMESTAMP,
    metadata JSON
)
```

**2. Diccionario multilingüe en `rag_engine.py`:**
~40 términos econométricos traducidos en 4 idiomas:
- Heterocedasticidad / heteroscedasticity / hétéroscédasticité / heterocedasticidade
- Componentes principales / PCA / ACP / analyse en composantes principales
- Series temporales / time series / série temporelle / séries temporais
- Variable instrumental / instrumental variable / variable instrumentale / variável instrumental
- Y muchos más...

**3. Servidor HTTP refactorizado:**
Eliminado diccionario local `_term_translations` y reemplazado por llamada al método del RAGEngine:
```python
engine = _get_rag_engine()
available_languages = engine.get_available_languages()
query_for_rag = engine.translate_query_for_languages(
    last_question, 
    available_languages if available_languages else ["en", "es"]
)
```

**4. Re-indexación completada:**
- 9 documentos, 3,690 chunks
- Base de datos: 12.26 MB
- Columna `language` presente (todos marcados como `en`)

### Archivos modificados

| Archivo repo | Cambio |
|--------------|--------|
| `NEVEN/TaskPane/rag_engine.py` | +language en schema, +diccionario multilingüe ~130 líneas |
| `NEVEN/ControlPython/startup/neven_http_server.py` | Refactorizado para usar translate_query_for_languages() |
| `NEVEN/Install/scripts/index_books.py` | Tuplas de 4 elementos (path, domain, name, language) |

| Archivo producción | Sincronizado |
|--------------------|--------------|
| `C:\NEVEN\TaskPane\rag_engine.py` | ✅ |
| `C:\NEVEN\startup\neven_http_server.py` | ✅ |
| `C:\NEVEN\data\rag_index.duckdb` | ✅ Re-indexado con columna language |

### Decisiones de diseño

1. **Un solo diccionario de traducciones** — En `rag_engine.py` en lugar de duplicarlo en el servidor HTTP. DRY.

2. **Traducción bidireccional** — Cada término tiene traducciones a los otros 3 idiomas. Permite buscar en cualquier dirección.

3. **Idioma como metadato del documento** — No del chunk, porque un documento entero está en un solo idioma.

### Servidor HTTP reiniciado y funcionando

```
[RAG] Ontologia cargada: 2 schemas, 199 entidades
[RAG] Contexto enriquecido: 3 chunks, dominios: ['econometria']
```

### Commits pendientes

No se hizo commit en esta sesión. Cambios listos para commit:
- feat(rag): soporte multi-idioma EN/ES/PT/FR

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | git commit + push de cambios de idioma |
| **MEDIA** | Probar en Excel query "ACP" y verificar que encuentre PCA |
| **MEDIA** | Agregar libros en español para probar multi-idioma real |
| **BAJA** | Arreglar errores YAML en ontologías (preexistentes) |



---

### Sesión 2026-08-19 (~13:00) — VALIDACIÓN: Problema ACP resuelto

## ✅ VALIDADO: Traducción multilingüe + umbral funcionan correctamente

### Prueba realizada

**Query original:** `"que es el ACP"`

**Query expandida automáticamente:** 
```
"que es el ACP PCA principal component analysis componentes principales"
```

### Resultados

| # | Libro | Dominio | Score |
|---|-------|---------|-------|
| 1 | Time Series Analysis in R | econometria | 0.711 ✅ |
| 2 | Time Series Analysis in R | econometria | 0.706 ✅ |
| 3 | Time Series Analysis in R | econometria | 0.705 ✅ |
| 4 | R for Social Sciences | estadistica | 0.704 ✅ |
| 5 | Time Series Analysis in R | econometria | 0.704 ✅ |

- **5 de 5 pasan el umbral** (>= 0.70)
- **0 resultados de Excel** (antes era el problema)
- Dominios correctos: econometría y estadística

### Comparación antes vs ahora

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Query | Sin traducir | Expandida con sinónimos EN/ES/PT/FR |
| Score típico | ~0.50 | ~0.70+ |
| Resultados | Excel irrelevante | Econometría/estadística relevante |
| Filtro | Ninguno | MIN_RAG_SCORE = 0.70 |

### Conclusión

El problema del ACP está **completamente resuelto** con la combinación de:
1. Traducción automática de términos técnicos
2. Umbral de relevancia mínima



---

### Sesión 2026-08-19 (~13:15) — FIX: Fuentes RAG no se mostraban

## 🔧 CORREGIDO: Variable rag_sources no inicializada

### Síntoma
Al preguntar "Que es el ACP?" en el chat, no aparecía el botón "Ver fuentes" aunque los logs mostraban `[RAG] Contexto enriquecido: 3 chunks`.

### Causa raíz
La variable `rag_sources` **no estaba inicializada** como lista vacía antes del bloque RAG:

```python
# ANTES (bug)
rag_context = ""
rag_domains = []
if _RAG_AVAILABLE and _get_rag_engine:
    ...
    rag_sources = [...]  # Solo se define aquí dentro

# Más adelante se usa:
"rag_sources": rag_sources if rag_context else []  # NameError si no hubo RAG
```

### Fix aplicado

```python
# DESPUÉS (correcto)
rag_context = ""
rag_domains = []
rag_sources = []  # Inicializar fuentes RAG
if _RAG_AVAILABLE and _get_rag_engine:
    ...
```

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/ControlPython/startup/neven_http_server.py` | +`rag_sources = []` en línea ~1788 |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |

### Servidor reiniciado
El servidor HTTP fue reiniciado para aplicar el fix.

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar en Excel que aparezca botón "Ver fuentes" con query ACP |
| **ALTA** | git commit + push de todos los cambios de esta sesión |



---

### Sesión 2026-08-19 (~13:30) — FEATURE: Umbral RAG configurable

## ✅ IMPLEMENTADO: minScore configurable en neven-config.json

### Problema
Con el umbral fijo de 0.70, muchas queries devolvían chunks vacíos porque los scores no alcanzaban el umbral, especialmente cuando la traducción no mejoraba suficientemente el match semántico.

### Solución
Hacer el umbral configurable por el usuario en `neven-config.json`:

```json
"RAG": {
    "enabled": true,
    "minScore": 0.50,
    "topK": 3,
    "indexPath": "C:\\NEVEN\\data\\rag_index.duckdb",
    "ontologyPath": "C:\\NEVEN\\docs\\ontologia"
}
```

### Código modificado

```python
# Leer umbral mínimo desde config (default 0.50)
rag_config = full_cfg.get("RAG", {})
MIN_RAG_SCORE = rag_config.get("minScore", 0.50)

# Filtrar chunks con score mínimo de relevancia
relevant_chunks = [c for c in chunks if c.get("score", 0) >= MIN_RAG_SCORE]
```

### Valores recomendados

| minScore | Comportamiento |
|----------|----------------|
| 0.50 | Más resultados, puede incluir menos relevantes |
| 0.60 | Balance cantidad/relevancia |
| 0.70 | Solo muy relevantes (puede dar vacío) |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/ControlPython/startup/neven_http_server.py` | Lee `minScore` de config en vez de hardcoded |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado |
| `C:\NEVEN\neven-config.json` | +sección RAG con minScore, topK, paths |

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar en Excel con minScore=0.50 |
| **ALTA** | git commit + push de todos los cambios |
| **MEDIA** | Agregar UI en TaskPane para ajustar minScore |



---

### Sesión 2026-08-19 (~13:40) — VERIFICACIÓN: Flujo de traducción RAG

## ✅ CONFIRMADO: Orden correcto de traducción

El flujo de traducción multilingüe está implementado correctamente:

```
1. engine.get_available_languages()     → ['en'] (idiomas en el índice)
2. engine.translate_query_for_languages(query, languages)  → query expandida
3. engine.query_with_ontology(expanded_query)  → búsqueda con traducción
```

**Ejemplo con "Que es el ACP?":**
- Input: `"Que es el ACP?"`
- Idiomas detectados: `['en']`
- Query expandida: `"Que es el ACP? PCA principal component analysis componentes principales"`
- Búsqueda ejecutada con la query traducida

**Cuando se agreguen libros en otros idiomas:**
- `get_available_languages()` devolverá `['en', 'es', 'pt', 'fr']`
- La traducción incluirá términos en todos esos idiomas

No se realizaron cambios de código en esta sesión.



---

### Sesión 2026-08-19 (~13:45) — FIX: BOM en neven-config.json

## 🔧 CORREGIDO: UTF-8 BOM causaba error de parsing

### Error
```
No se pudo leer neven-config.json: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
```

### Causa raíz
PowerShell `Set-Content -Encoding UTF8` agrega BOM (bytes `239 187 191`) al inicio del archivo. Python `json.load()` con encoding `utf-8` no tolera BOM.

### Fix aplicado
```powershell
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
```

### Recordatorio
**NUNCA usar `Set-Content -Encoding UTF8` para archivos que Python leerá.**
Siempre usar:
```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
```

### Archivos corregidos
- `C:\NEVEN\neven-config.json` — BOM eliminado



---

### Sesión 2026-08-19 (~13:55) — DEBUG: Fuentes RAG no se muestran

## 🔧 EN PROGRESO: Diagnóstico de rag_sources vacío

### Síntoma
El chat responde correctamente pero no muestra el botón "Ver fuentes" aunque el RAG está activo (endpoint `/api/rag/stats` funciona).

### Diagnóstico en curso

1. **Frontend verificado** — `_showRagSourcesPopup` y el código del botón existen en producción
2. **RAG Engine funciona** — `/api/rag/stats` devuelve 9 docs, 3690 chunks
3. **Logs no muestran RAG** — No aparecen mensajes `[RAG]` durante el chat

### Hipótesis
El bloque RAG no se está ejecutando o hay un error silencioso antes del logging.

### Acción tomada
Agregado logging de diagnóstico:
```python
_log.info(f"[RAG] _RAG_AVAILABLE={_RAG_AVAILABLE}, _get_rag_engine={_get_rag_engine is not None}")
```

### Archivos modificados
- `NEVEN/ControlPython/startup/neven_http_server.py` — +logging diagnóstico
- `C:\NEVEN\startup\neven_http_server.py` — Sincronizado

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar en Excel y revisar logs para ver si `_RAG_AVAILABLE=True` |
| **ALTA** | Identificar por qué el bloque RAG no se ejecuta |
| **MEDIA** | Agregar UI para configurar minScore |
| **MEDIA** | git commit + push de todos los cambios |



---

### Sesión 2026-08-19 (~14:10) — DEBUG: Continuación diagnóstico RAG

## 🔧 EN PROGRESO: Logs no aparecen en servidor

### Observaciones
- TaskPane muestra `[NEVEN] _aiCallLLM payload:` — el request se envía
- Servidor no muestra logs de `[RAG]` ni `[AI_CHAT]`
- El endpoint `/api/rag/stats` funciona (9 docs, 3690 chunks)

### Acciones tomadas
1. Agregado log `[AI_CHAT] Request recibido` al inicio de `_handle_ai_chat()`
2. Servidor reiniciado

### Archivos modificados (temporalmente para debug)
- `C:\NEVEN\startup\neven_http_server.py` — +logging en _handle_ai_chat

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar y verificar si aparece `[AI_CHAT] Request recibido` |
| **ALTA** | Identificar por qué el bloque RAG no genera logs |
| **ALTA** | Sincronizar cambios de debug al repo |



---

### Sesión 2026-08-19 (~14:20) — FIX: Servidores HTTP duplicados

## 🔧 IDENTIFICADO: Dos servidores escuchando en puerto 5555

### Causa raíz
Había **dos procesos Python** (PIDs 52916 y 71868) escuchando en el puerto 5555. El TaskPane se conectaba al servidor viejo que no tenía los cambios de RAG.

### Solución
1. Matar ambos procesos: `Stop-Process -Id 52916, 71868 -Force`
2. Reiniciar un solo servidor limpio
3. Recargar el TaskPane en Excel

### Comando para verificar duplicados
```powershell
netstat -ano | Select-String ":5555.*LISTENING"
```

### Lección aprendida
Siempre verificar que no haya procesos duplicados antes de diagnosticar problemas de "logs no aparecen".

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Recargar TaskPane y probar fuentes RAG |
| **ALTA** | Verificar que aparece `[AI_CHAT] Request recibido` en logs |



---

### Sesión 2026-08-19 (~14:30) — FIX: Caché Python con código viejo

## 🔧 IDENTIFICADO: Error 'get_available_languages' no encontrado

### Error en logs
```
[RAG] Error consultando: 'RAGEngine' object has no attribute 'get_available_languages'
```

### Causa raíz
Python había cacheado una versión vieja de `rag_engine.py` en `__pycache__/`. Aunque el archivo fuente tenía el método, el bytecode compilado no lo incluía.

### Solución
```powershell
Remove-Item "C:\NEVEN\TaskPane\__pycache__" -Recurse -Force
Remove-Item "C:\NEVEN\startup\__pycache__" -Recurse -Force
```
Luego reiniciar el servidor.

### Lección aprendida
**Siempre limpiar `__pycache__` después de actualizar archivos Python en producción.**

### Logs ahora muestran
```
[AI_CHAT] Request recibido
[RAG] _RAG_AVAILABLE=True, _get_rag_engine=True
```
El diagnóstico funcionó — el bloque RAG sí se está ejecutando.

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar en Excel después de limpiar caché |
| **ALTA** | Verificar que aparecen fuentes RAG |



---

### Sesión 2026-08-19 (~14:40) — FIX: Dos copias de rag_engine.py

## ✅ CORREGIDO: Servidor cargaba versión vieja de rag_engine.py

### Error
```
[RAG] Error consultando: 'RAGEngine' object has no attribute 'get_available_languages'
```

### Causa raíz
Había **dos copias** de `rag_engine.py` en producción:

| Ubicación | Tamaño | Versión |
|-----------|--------|---------|
| `C:\NEVEN\TaskPane\rag_engine.py` | 42,574 bytes | ✅ Actualizada |
| `C:\NEVEN\startup\rag_engine.py` | 33,957 bytes | ❌ Vieja |

El servidor HTTP corre desde `C:\NEVEN\startup\` y Python importa `rag_engine` desde el **directorio local primero** (antes de buscar en `sys.path`).

### Solución
```powershell
[System.IO.File]::Copy(
    "C:\NEVEN\TaskPane\rag_engine.py",
    "C:\NEVEN\startup\rag_engine.py",
    $true
)
Remove-Item "C:\NEVEN\startup\__pycache__" -Recurse -Force
```

### Lección aprendida
En NEVEN hay archivos Python en **múltiples directorios**:
- `C:\NEVEN\startup\` — servidor HTTP y scripts de inicio
- `C:\NEVEN\TaskPane\` — módulos del TaskPane

Cuando se actualiza un módulo compartido como `rag_engine.py`, hay que copiarlo a **TODOS** los directorios donde pueda ser importado.

### Archivos sincronizados
- `C:\NEVEN\startup\rag_engine.py` — ahora tiene la versión actualizada

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar en Excel que aparezcan fuentes RAG |
| **MEDIA** | Considerar eliminar la copia en startup y usar import desde TaskPane |
| **MEDIA** | git commit + push de todos los cambios |



---

### Sesión 2026-08-19 (~14:50) — DEBUG: Agregando más logs

## 🔧 EN PROGRESO: Verificando resultados RAG

### Avances
- La traducción de query funciona: `Que es el ACP? PCA principal component analysis componentes principales`
- El log muestra `[RAG] Query expandida (1 idiomas)...` ✅

### Problema pendiente
No aparece log de "Contexto enriquecido" ni "Chunks descartados", lo que indica que:
1. `query_with_ontology` no devuelve resultados, o
2. Hay un error silencioso

### Acción tomada
Agregado log para ver resultado de la query:
```python
rag_result = engine.query_with_ontology(query_for_rag, top_k=3)
_log.info(f"[RAG] Resultado: {len(rag_result.get('results', []))} chunks encontrados")
```

### Archivos modificados
- `C:\NEVEN\startup\neven_http_server.py` — +log de resultado RAG

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar y revisar logs para ver cuántos chunks se encuentran |
| **ALTA** | Identificar por qué no se muestran fuentes |



---

### Sesión 2026-10-05 (~inicio) — OBS Overlay de prueba

## HTML de prueba para OBS (Browser Source)

### Contexto
Solicitud puntual fuera del flujo principal de NEVEN: crear un HTML de prueba con fondo transparente para calibrar overlays en OBS (Open Broadcaster Software).

### Archivo creado

| Archivo | Descripción |
|---------|-------------|
| `NEVEN/docs/obs-test-overlay.html` | Overlay HTML para OBS con transparencia y controles |

### Características del overlay

- `background: transparent` en `body` — compatible con Browser Source de OBS
- Slider de opacidad (0–100%) para calibrar en previsualización del navegador
- **Reloj en vivo** actualizado cada segundo (esquina superior izquierda)
- **Badge "En vivo"** con punto parpadeante (esquina superior derecha)
- **Headline central** con fondo semitransparente y borde azul
- **Lower Third** con nombre y afiliación UCR
- **Ticker de noticias** con scroll continuo (~28 s por ciclo, datos del proyecto NEVEN)
- **Grilla de calibración** al centro: 9 swatches de blanco puro → transparente → negro puro
- Resolución base: 1920 × 1080 px

### Decisión de diseño
El slider de opacidad solo afecta el `div#overlay` (no el panel de controles), para poder calibrar sin perder acceso al control. En OBS se usa la opacidad nativa de la fuente, no el slider.

### Commits realizados
Ninguno — archivo de utilidad local, no crítico para el proyecto.

### Pendientes próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| **ALTA** | Completar commits pendientes de la sesión 2026-08-20 |
| **MEDIA** | Verificar que fórmulas LaTeX se renderizan en chat AI |


---

### Sesión 2026-10-05 (~continuación) — Texto grande en OBS Overlay

## Agregado texto "ESTO ES UNA PRUEBA" al overlay

### Cambio realizado
Agregado texto de prueba grande centrado en el overlay OBS.

### Archivo modificado

| Archivo | Cambio |
|---------|--------|
| `NEVEN/docs/obs-test-overlay.html` | +clase `.test-text` en CSS + `<div class="test-text">` en HTML |

### Detalles de implementación
- Tamaño: `font-size: 120px`, `font-weight: 900`
- Posición: centrado absoluto con `top:50% / left:50% / transform: translate(-50%,-50%)`
- Estilo: texto blanco con sombra doble (glow blanco difuso + sombra negra sólida) para visibilidad sobre cualquier fondo
- `white-space: nowrap` para evitar que el texto se parta en dos líneas

### Nota técnica
El primer intento de `str_replace` falló porque los guiones del comentario CSS (`──`) tenían distinta longitud que el string buscado. Se resolvió buscando el patrón exacto con `grep_search` antes de reemplazar.

### Commits realizados
Ninguno.

### Pendientes próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| **ALTA** | Completar commits pendientes de sesión 2026-08-20 |
| **MEDIA** | Verificar renderizado de fórmulas LaTeX en chat AI |


---

### Sesión 2026-10-05 (~continuación 2) — OBS Overlay: fondo 100% transparente

## Corrección de transparencia en overlay OBS

### Problema
El usuario aclaró que al pedir "transparencia" se refería a que **todo el fondo** fuera transparente — no solo el `body`. Los elementos del overlay (reloj, badge, headline, lower third, ticker) tenían fondos `rgba(...)` semitransparentes que bloqueaban parcialmente la escena de OBS.

### Causa raíz
El diseño inicial usó fondos de color en los elementos para mejorar el contraste del texto, asumiendo que "transparencia" era solo del body. La intención real era que **nada** tuviera fondo — solo letras flotando sobre la escena.

### Solución aplicada
Eliminados todos los `background: rgba(...)` de los elementos del overlay. Compensado el contraste perdido con `text-shadow` negra en cada elemento de texto.

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/docs/obs-test-overlay.html` | Eliminados fondos de `.clock`, `.live-badge`, `.headline-box`, `.lower-third .name`, `.lower-third .title`, `.ticker`. Agregado `text-shadow` a cada uno. Eliminados `border-radius`, `backdrop-filter` y `border-left` decorativos. |

### Decisiones de diseño
- El panel de control (`#controls`) conserva su fondo oscuro — es solo visible en el navegador, no en OBS.
- Se agregó `text-shadow: 2px 2px 6px rgba(0,0,0,0.9)` a todos los textos para mantener legibilidad sobre fondos claros.
- La clase `.live-dot` (punto parpadeante) quedó blanca — sin fondo de badge rojo ya no se distingue bien; pendiente revisar si conviene cambiar a rojo sólido.

### Commits realizados
Ninguno.

### Pendientes próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| **ALTA** | Completar commits pendientes de sesión 2026-08-20 |
| **MEDIA** | Revisar visibilidad del punto `.live-dot` sin fondo rojo |
| **MEDIA** | Verificar renderizado de fórmulas LaTeX en chat AI |

---

### Sesión 2026-10-05 (~continuación 3) — Eliminado texto de prueba del overlay

## Cambio menor

Eliminado el texto "ESTO ES UNA PRUEBA" del overlay OBS: se removió el `<div class="test-text">` del HTML y la clase `.test-text` completa del CSS.

### Archivo modificado

| Archivo | Cambio |
|---------|--------|
| `NEVEN/docs/obs-test-overlay.html` | Eliminado div `.test-text` y su bloque CSS |

### Commits realizados
Ninguno.

### Pendientes próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| **ALTA** | Completar commits pendientes de sesión 2026-08-20 |
| **MEDIA** | Revisar visibilidad del punto `.live-dot` sin fondo rojo |
| **MEDIA** | Verificar renderizado de fórmulas LaTeX en chat AI |


---

### Sesión 2026-08-19 (~noche-2) — Validación soporte EPUB en RAG

## Problema identificado

**Síntoma:** Se solicitó verificar si la implementación de MarkItDown en el RAG soporta archivos `.epub`.

**Causa raíz:** Existían dos funciones de extracción de texto paralelas en `rag_engine.py`:
1. `extract_text_with_pages_markitdown()` — usa MarkItDown, soporta 20+ formatos
2. `extract_text_from_file()` — versión vieja, solo soportaba `.pdf` y texto básico

El método `add_document()` (línea 538) usaba `extract_text_from_file()`, limitando el RAG a PDF y archivos de texto. **EPUB no estaba soportado aunque MarkItDown sí lo permite.**

## Fix implementado

Modificada función `extract_text_from_file()` para usar MarkItDown como primera opción:

```python
def extract_text_from_file(file_path: str) -> str:
    # Intentar con MarkItDown primero (soporta 20+ formatos incluyendo EPUB)
    try:
        from markitdown import MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        if result.markdown.strip():
            return result.markdown
    except ImportError:
        pass  # MarkItDown no instalado, usar fallbacks
    # ... fallbacks para texto plano y PDF con PyMuPDF
```

**Archivos modificados:**
| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/rag_engine.py` | `extract_text_from_file()` ahora usa MarkItDown primero |
| `NEVEN/Install/Dist/startup/rag_engine.py` | Sincronizado |
| `C:\NEVEN\startup\rag_engine.py` | Sincronizado a producción |

## Dependencia faltante: ebooklib

**Hallazgo:** MarkItDown soporta EPUB **pero requiere `ebooklib`** como dependencia. Al verificar:
```python
import importlib.util
epub_spec = importlib.util.find_spec('ebooklib')
# Resultado: ebooklib installed: False
```

## Investigación de formatos MarkItDown

Se investigaron todos los formatos soportados y sus dependencias:

| Formato | Dependencia | Recomendación NEVEN |
|---------|-------------|---------------------|
| PDF | `markitdown[pdf]` | ✓ Instalar |
| DOCX | `markitdown[docx]` | ✓ Instalar |
| PPTX | `markitdown[pptx]` | ✓ Instalar |
| XLSX | `markitdown[xlsx]` | ✓ Instalar |
| XLS | `markitdown[xls]` | ✗ Formato obsoleto |
| EPUB | `ebooklib` (separado) | ✓ Instalar |
| HTML/CSV/JSON/XML | (incluido) | ✓ Ya funciona |
| Outlook MSG | `markitdown[outlook]` | ✗ No aplica |
| Audio | `markitdown[audio-transcription]` | ✗ Requiere API externa |
| YouTube | `markitdown[youtube-transcription]` | ✗ Requiere API externa |
| Azure | `markitdown[az-*]` | ✗ Requiere suscripción |
| OCR | `markitdown-ocr` | ✗ Requiere GPT-4o |

## Decisión de diseño

**Instalar solo lo que funciona 100% offline:**
```powershell
pip install 'markitdown[pdf,docx,pptx,xlsx]' ebooklib
```

Esto habilita: PDF, DOCX, PPTX, XLSX, EPUB, HTML, CSV, JSON, XML sin APIs externas.

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Instalar dependencias MarkItDown: `pip install 'markitdown[pdf,docx,pptx,xlsx]' ebooklib` | **Pendiente** |
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| **ALTA** | Regenerar ZIP después de instalar dependencias | Pendiente |
| MEDIA | Documentar formatos soportados en RAG_GUIDE.md | Pendiente |

---


### Sesión 2026-08-19 (~noche-3) — Dependencias MarkItDown instaladas + ZIP regenerado

## Acciones completadas

### 1. Instalación de dependencias offline completas

```powershell
pip install 'markitdown[pdf,docx,xlsx,pptx,xls]' ebooklib
```

**Resultado:**
- `ebooklib-0.20` instalado (EPUB support)
- `xlrd` ya estaba instalado (XLS legacy support)
- Todas las otras dependencias ya estaban presentes

### 2. Actualización del instalador

**Archivo:** `NEVEN/Install/Install-NEVEN.ps1`

Modificado array de paquetes pip (líneas 1401-1416):
```powershell
# MarkItDown with ALL offline document formats:
#   - PDF (pdfminer-six, pdfplumber)
#   - DOCX (mammoth)
#   - PPTX (python-pptx)
#   - XLSX (openpyxl, pandas)
#   - XLS legacy (xlrd)
#   - EPUB (ebooklib)
#   - HTML, CSV, JSON, XML, TXT, MD, ZIP (built-in, no deps)
$pipPkgsMarkItDown = @('markitdown[pdf,docx,xlsx,pptx,xls]','ebooklib')
```

### 3. Actualización de requirements.txt

**Archivo:** `NEVEN/TaskPane/requirements.txt`

Agregado:
```
markitdown[pdf,docx,xlsx,pptx,xls]>=0.1.0   # Microsoft's converter (MIT license)
ebooklib>=0.18          # EPUB support for MarkItDown
```

### 4. ZIP regenerado

**Archivo:** `NEVEN/Install/NEVEN-v3.2-Setup.zip`
- **Tamaño:** 21.96 MB
- **Archivos:** 426
- **Fecha:** 2026-10-05 01:14:58

## Formatos soportados por RAG (todos offline)

| Formato | Extensión | Dependencia |
|---------|-----------|-------------|
| PDF | .pdf | pdfminer-six, pdfplumber |
| Word | .docx | mammoth |
| PowerPoint | .pptx | python-pptx |
| Excel nuevo | .xlsx | openpyxl, pandas |
| Excel viejo | .xls | xlrd |
| EPUB | .epub | ebooklib |
| HTML | .html, .htm | (built-in) |
| CSV | .csv | (built-in) |
| JSON | .json | (built-in) |
| XML | .xml | (built-in) |
| Texto | .txt, .md | (built-in) |
| ZIP | .zip | (built-in, itera contenido) |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/rag_engine.py` | `extract_text_from_file()` usa MarkItDown primero |
| `NEVEN/TaskPane/requirements.txt` | +ebooklib, +xls en markitdown extras |
| `NEVEN/Install/Install-NEVEN.ps1` | +xls, +ebooklib en $pipPkgsMarkItDown |
| `NEVEN/Install/Dist/startup/rag_engine.py` | Sincronizado |
| `NEVEN/Install/Dist/startup/requirements.txt` | Sincronizado |
| `C:\NEVEN\startup\rag_engine.py` | Sincronizado a producción |
| `NEVEN/Install/NEVEN-v3.2-Setup.zip` | Regenerado |

## Decisión de diseño

**Instalar TODOS los formatos offline:** Se decidió incluir `xls` (Excel legacy) aunque es formato obsoleto porque:
1. No agrega dependencias pesadas (solo xlrd)
2. Algunos usuarios pueden tener archivos .xls antiguos
3. Funciona 100% offline

**NO instalar formatos que requieren API externa:**
- `[audio-transcription]` — requiere servicio de transcripción
- `[youtube-transcription]` — requiere API YouTube
- `[az-*]` — requiere Azure
- `markitdown-ocr` — requiere GPT-4o

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| ~~ALTA~~ | ~~Instalar dependencias MarkItDown~~ | Completado |
| ~~ALTA~~ | ~~Regenerar ZIP~~ | Completado |
| MEDIA | Documentar formatos soportados en RAG_GUIDE.md | Pendiente |
| BAJA | Agregar filtro por extensión en UI de indexado | Pendiente |

---


### Sesión 2026-08-19 (~noche-4) — UI actualizada con formatos RAG y capítulos

## Correcciones en TaskPane

### 1. Lista de formatos soportados en panel RAG

**Problema:** El placeholder del input de archivos decía "PDF, TXT, MD" pero ahora soportamos 12+ formatos.

**Solución:** Agregada línea informativa debajo del input:
```html
<div style="font-size:9px;color:var(--text-secondary)">
  <strong>Formatos:</strong> PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD
</div>
```

### 2. Número de capítulos en Tab Ayuda

**Problema:** Decía "Manual de 14 capítulos" pero ahora tenemos 16 (capítulos 0-15).

**Solución:** Cambiado a "Manual de 16 capítulos con guías y ejemplos".

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/taskpane.html` | +lista formatos RAG, +16 capítulos |
| `NEVEN/Install/Dist/taskpane/taskpane.html` | Sincronizado |
| `C:\NEVEN\TaskPane\taskpane.html` | Sincronizado a producción |
| `NEVEN/Install/NEVEN-v3.2-Setup.zip` | Regenerado (21.96 MB) |

## Resumen cambios completos esta sesión

| Cambio | Archivo |
|--------|---------|
| `extract_text_from_file()` usa MarkItDown primero | rag_engine.py |
| +ebooklib, +xls en dependencias | requirements.txt, Install-NEVEN.ps1 |
| Lista de formatos visible al usuario | taskpane.html |
| "16 capítulos" en Tab Ayuda | taskpane.html |

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| ~~ALTA~~ | ~~Soporte EPUB/DOCX/PPTX/XLSX en RAG~~ | Completado |
| ~~ALTA~~ | ~~Indicar formatos al usuario~~ | Completado |
| ~~MEDIA~~ | ~~Corregir "14 capítulos" → "16 capítulos"~~ | Completado |
| MEDIA | Documentar formatos en RAG_GUIDE.md | Pendiente |

---


### Sesión 2026-08-19 (~noche-5) — Botón browse para selector de archivos RAG

## Problema reportado

El botón "..." en el panel RAG no hacía nada al hacer clic.

**Causa raíz:** El botón HTML existía pero no tenía ningún event listener asociado. Además, los browsers no permiten obtener la ruta completa de un archivo por seguridad (solo el nombre).

## Solución implementada

### 1. Nuevo endpoint en servidor HTTP

**Endpoint:** `GET /api/rag/browse`

Usa `tkinter.filedialog` para abrir el diálogo nativo de Windows:

```python
def _handle_rag_browse(self):
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    filetypes = [
        ("Todos los soportados", "*.pdf;*.docx;*.pptx;*.xlsx;*.xls;*.epub;*.html;*.htm;*.csv;*.json;*.xml;*.txt;*.md"),
        ("PDF", "*.pdf"),
        # ... etc
    ]
    
    file_path = filedialog.askopenfilename(...)
    # Devuelve {"status": "ok", "path": "C:\\ruta\\completa.pdf", "filename": "archivo.pdf"}
```

### 2. Handler del botón en TaskPane

```javascript
browseBtn.addEventListener('click', async function() {
    var response = await fetch(API + '/api/rag/browse');
    var data = await response.json();
    if (data.status === 'ok' && data.path) {
        document.getElementById('rag-file-path').value = data.path;
        showToast('Archivo seleccionado: ' + data.filename);
    }
});
```

## Intento fallido

**Primer intento:** Usar `window.showOpenFilePicker()` (File System Access API)
- **Problema:** Esta API no expone la ruta completa del archivo por seguridad del browser
- **Resultado:** Solo se obtenía el nombre del archivo, no la ruta necesaria para el servidor

**Solución correcta:** Usar el servidor HTTP para abrir el diálogo nativo de Windows con tkinter, que sí devuelve la ruta completa.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/neven_http_server.py` | +endpoint GET /api/rag/browse, +_handle_rag_browse() |
| `NEVEN/TaskPane/taskpane.html` | +event listener para rag-browse-btn |
| `NEVEN/ControlPython/startup/neven_http_server.py` | Sincronizado |
| `NEVEN/Install/Dist/startup/neven_http_server.py` | Sincronizado |
| `NEVEN/Install/Dist/taskpane/taskpane.html` | Sincronizado |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado a producción |
| `C:\NEVEN\TaskPane\taskpane.html` | Sincronizado a producción |
| `NEVEN/Install/NEVEN-v3.2-Setup.zip` | Regenerado (21.96 MB) |

## Decisión de diseño

**tkinter vs win32:** Se eligió tkinter porque:
1. Viene incluido con Python (no requiere pywin32)
2. `filedialog.askopenfilename()` es simple y funcional
3. Devuelve la ruta completa del archivo
4. El diálogo se muestra al frente con `attributes('-topmost', True)`

---

### Resumen completo de la sesión 2026-08-19

| Cambio | Estado |
|--------|--------|
| Soporte EPUB/DOCX/PPTX/XLSX/XLS en RAG | Completado |
| Instalar ebooklib + markitdown[xls] | Completado |
| Lista de formatos visible en UI | Completado |
| "16 capítulos" en Tab Ayuda | Completado |
| Botón browse abre explorador de archivos | Completado |
| ZIP instalador regenerado | Completado |

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| **ALTA** | Reiniciar servidor HTTP para probar botón browse | Pendiente |
| MEDIA | Documentar formatos en RAG_GUIDE.md | Pendiente |
| BAJA | Agregar botón browse al panel de ontología también | Pendiente |

---


### Sesión 2026-08-19 (~noche-6) — Fix botón browse con subprocess

## Problema

El botón "..." del panel RAG retornaba "Error al abrir selector de archivos".

**Causa raíz:** tkinter GUI requiere ejecutarse en el hilo principal de Python, pero el servidor HTTP maneja requests en threads separados. Ejecutar `filedialog.askopenfilename()` directamente en un thread secundario causa error.

## Solución

Cambiar de ejecución directa de tkinter a usar `subprocess` para lanzar un proceso Python separado:

```python
def _handle_rag_browse(self):
    script = '''
import tkinter as tk
from tkinter import filedialog
import json, os

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
root.focus_force()

file_path = filedialog.askopenfilename(...)
root.destroy()

print(json.dumps({"status": "ok", "path": file_path, ...}))
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)
    data = json.loads(result.stdout.strip())
    self._send_json(data)
```

**Por qué funciona:** El subprocess crea un nuevo proceso Python con su propio hilo principal, donde tkinter puede ejecutar correctamente.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/neven_http_server.py` | `_handle_rag_browse()` usa subprocess |
| `NEVEN/ControlPython/startup/neven_http_server.py` | Sincronizado |
| `NEVEN/Install/Dist/startup/neven_http_server.py` | Sincronizado |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado a producción |
| `NEVEN/Install/NEVEN-v3.2-Setup.zip` | Regenerado |

## Intento fallido

**Primer intento:** Ejecutar tkinter directamente en el handler HTTP
- **Error:** tkinter no funciona en threads secundarios
- **Síntoma:** "Error al abrir selector de archivos"

## Verificación

El diálogo nativo de Windows SÍ aparece cuando se ejecuta el script como subprocess (usuario confirmó que lo cerró manualmente).

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Reiniciar Excel y probar botón browse | Pendiente |
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| MEDIA | Documentar formatos en RAG_GUIDE.md | Pendiente |

---


### Sesión 2026-08-19 (~noche-7) — Diagnóstico servidor HTTP viejo

## Problema persistente

El botón "..." seguía retornando error después de sincronizar el código.

**Diagnóstico:**
```powershell
Invoke-WebRequest -Uri 'http://localhost:5555/api/rag/browse'
# Error: (404) No se encontró
```

**Causa raíz:** El servidor HTTP que estaba corriendo era una instancia vieja (antes de agregar el endpoint `/api/rag/browse`). Sincronizar archivos no reinicia el servidor automáticamente.

## Solución

Terminar los procesos Python del servidor HTTP viejo:
```powershell
Get-Process python* | ... # Encontró PIDs 86348 y 94980
Stop-Process -Id 86348 -Force
Stop-Process -Id 94980 -Force
```

Al reabrir Excel, el servidor se iniciará con el código actualizado.

## Lección aprendida

**IMPORTANTE:** Después de modificar `neven_http_server.py`, es necesario:
1. Cerrar Excel completamente
2. O matar los procesos Python que ejecutan el servidor
3. Luego reabrir Excel

Solo copiar archivos no es suficiente — el proceso Python en memoria sigue ejecutando el código viejo.

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Reabrir Excel y probar botón browse | Pendiente |
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| MEDIA | Documentar formatos en RAG_GUIDE.md | Pendiente |

---


### Sesión 2026-08-19 (~noche-final) — Commit consolidado de mejoras RAG

## Confirmación final

Usuario confirmó: **"ahora si abre el selector de archivos"** ✓

## Commit realizado

| Hash | Descripción |
|------|-------------|
| `3edbbca` | feat(rag): add multi-format support and file browser |

### Contenido del commit

**Archivos modificados (7):**
- `NEVEN/TaskPane/rag_engine.py` — `extract_text_from_file()` usa MarkItDown primero
- `NEVEN/TaskPane/requirements.txt` — +ebooklib, +markitdown[xls]
- `NEVEN/TaskPane/neven_http_server.py` — +endpoint /api/rag/browse con subprocess+tkinter
- `NEVEN/TaskPane/taskpane.html` — +lista formatos, +16 capítulos, +handler botón browse
- `NEVEN/Install/Install-NEVEN.ps1` — +ebooklib, +xls en dependencias pip
- `NEVEN/ControlPython/startup/neven_http_server.py` — sincronizado
- `.kiro/contexto/CHAT.md` — bitácora actualizada

### Funcionalidades agregadas

1. **Soporte 12+ formatos en RAG:** PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD
2. **Botón browse funcional:** Abre explorador de archivos nativo de Windows
3. **Lista de formatos visible:** Usuario ve qué tipos de archivo puede indexar
4. **Contador de capítulos corregido:** 14 → 16 en Tab Ayuda

### Decisiones técnicas clave

| Decisión | Razón |
|----------|-------|
| subprocess para tkinter | tkinter requiere hilo principal; HTTP server usa threads secundarios |
| ebooklib separado | MarkItDown no lo incluye como dependencia transitiva |
| markitdown[xls] incluido | Soporte offline para Excel legacy (.xls) |

---

## Resumen completo sesión 2026-08-19

### Commits del día

| Hash | Descripción |
|------|-------------|
| `ff31c4e` | docs: remove emojis from Docusaurus |
| `b9f227d` | feat(rag): add minScore slider to RAG settings panel |
| `0acc6b4` | feat(ontology): add interactive visualization for NEVEN-core |
| `0ecf651` | docs(eval): add markitdown-ocr evaluation for scanned PDFs |
| `3edbbca` | feat(rag): add multi-format support and file browser |

### Logros principales

- ✅ Emojis eliminados de documentación Docusaurus
- ✅ Slider minScore en panel RAG Settings
- ✅ Visualización interactiva ontología NEVEN-core
- ✅ Evaluación markitdown-ocr (decisión: NO integrar)
- ✅ Soporte 12+ formatos de documentos en RAG
- ✅ Botón browse con diálogo nativo Windows
- ✅ ZIP instalador actualizado (21.96 MB)

---

### Pendientes actualizados

| Prioridad | Tarea | Estado |
|-----------|-------|--------|
| **ALTA** | Probar instalador en máquina limpia | Pendiente |
| MEDIA | Documentar formatos soportados en RAG_GUIDE.md | Pendiente |
| BAJA | Push a repositorio remoto | Pendiente (si se desea) |

---


### Sesión 2026-08-19 (~noche-final) — Commit y push completados

## Commit realizado

| Hash | Descripción |
|------|-------------|
| `3edbbca` | feat(rag): add multi-format support and file browser |

**Archivos en el commit:**
- `NEVEN/TaskPane/rag_engine.py`
- `NEVEN/TaskPane/requirements.txt`
- `NEVEN/TaskPane/neven_http_server.py`
- `NEVEN/TaskPane/taskpane.html`
- `NEVEN/Install/Install-NEVEN.ps1`
- `NEVEN/ControlPython/startup/neven_http_server.py`
- `.kiro/contexto/CHAT.md`

## Push realizado

Repositorio sincronizado con `origin/master`.

## Resumen completo de commits del día

| Hash | Descripción |
|------|-------------|
| `ff31c4e` | docs: remove emojis from Docusaurus |
| `b9f227d` | feat(rag): add minScore slider to RAG settings panel |
| `0acc6b4` | feat(ontology): add interactive visualization for NEVEN-core |
| `0ecf651` | docs(eval): add markitdown-ocr evaluation for scanned PDFs |
| `3edbbca` | feat(rag): add multi-format support and file browser |

## Funcionalidades completadas hoy

1. Emojis eliminados de documentación
2. Slider minScore en RAG Settings
3. Visualización interactiva NEVEN-core
4. Soporte 12+ formatos en RAG (PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD)
5. Botón browse con diálogo nativo Windows
6. ZIP instalador actualizado (21.96 MB)

---

### Pendientes

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| MEDIA | Documentar formatos en RAG_GUIDE.md |

---


---

### Sesión 2026-08-19 (~noche) — RAG multi-formato, browse nativo, limpieza de UI

## Logros principales

### 1. Soporte de 12+ formatos en RAG

**Problema diagnosticado:** `rag_engine.py` tenía dos funciones de extracción paralelas:
- `extract_text_with_pages_markitdown()` — usaba MarkItDown, soporta 20+ formatos
- `extract_text_from_file()` — versión vieja, solo soportaba PDF y texto plano

El método `add_document()` llamaba a la función vieja. **EPUB, DOCX, PPTX, XLSX no funcionaban aunque MarkItDown los soporta.**

**Fix:** Modificada `extract_text_from_file()` para usar MarkItDown como primera opción, con fallback a PyMuPDF para PDF y lectura directa para texto plano.

### 2. Dependencias instaladas (offline, sin APIs externas)

```powershell
pip install 'markitdown[pdf,docx,pptx,xlsx,xls]' ebooklib
```

| Formato | Dependencia |
|---------|-------------|
| PDF | pdfminer-six, pdfplumber |
| DOCX | mammoth |
| PPTX | python-pptx |
| XLSX | openpyxl, pandas |
| XLS | xlrd |
| EPUB | ebooklib |
| HTML/CSV/JSON/XML/TXT/MD/ZIP | built-in (sin deps) |

### 3. Botón "..." para explorador de archivos nativo

**Primer intento fallido:** Ejecutar `tkinter.filedialog` directamente en el handler HTTP.
- **Error:** "Error al abrir selector de archivos"
- **Causa:** tkinter requiere el hilo principal de Python; el servidor HTTP corre en threads secundarios.

**Segundo intento fallido:** Usar `window.showOpenFilePicker()` (File System Access API).
- **Problema:** Los browsers no exponen la ruta completa del archivo por seguridad. Solo devuelve el nombre.

**Solución correcta:** Endpoint `GET /api/rag/browse` que lanza un subprocess Python separado con tkinter:

```python
result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, timeout=60)
```

El subprocess tiene su propio hilo principal → tkinter funciona correctamente → devuelve ruta completa.

**Problema adicional:** El endpoint devolvía 404 porque el servidor HTTP en memoria era una versión anterior. Se detectaron dos procesos viejos (PIDs 86348 y 94980) y se terminaron con `Stop-Process`. Al reabrir Excel, cargó el código actualizado.

### 4. Correcciones de UI

- Placeholder del input de archivos RAG actualizado (antes decía "PDF, TXT, MD")
- Agregada línea informativa: "Formatos: PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, CSV, JSON, XML, TXT, MD"
- Tab Ayuda: "14 capítulos" → "16 capítulos"

### 5. Mantenimiento de CHAT.md

Archivadas primeras 11,000 líneas a CHAT_LARGO.md (que ahora tiene 17,550 líneas). CHAT.md reducido a 1,380 líneas con el tracto reciente.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `NEVEN/TaskPane/rag_engine.py` | `extract_text_from_file()` usa MarkItDown primero |
| `NEVEN/TaskPane/requirements.txt` | +ebooklib, +markitdown[xls] |
| `NEVEN/TaskPane/neven_http_server.py` | +endpoint GET /api/rag/browse con subprocess |
| `NEVEN/TaskPane/taskpane.html` | +lista formatos RAG, +"16 capítulos" en Ayuda, +handler browse |
| `NEVEN/Install/Install-NEVEN.ps1` | +markitdown[xls], +ebooklib en $pipPkgsMarkItDown |
| `NEVEN/ControlPython/startup/neven_http_server.py` | Sincronizado |
| `NEVEN/Install/Dist/startup/rag_engine.py` | Sincronizado |
| `NEVEN/Install/Dist/startup/neven_http_server.py` | Sincronizado |
| `NEVEN/Install/Dist/taskpane/taskpane.html` | Sincronizado |
| `C:\NEVEN\startup\rag_engine.py` | Sincronizado a producción |
| `C:\NEVEN\startup\neven_http_server.py` | Sincronizado a producción |
| `C:\NEVEN\TaskPane\taskpane.html` | Sincronizado a producción |
| `NEVEN/Install/NEVEN-v3.2-Setup.zip` | Regenerado (21.96 MB, 426 archivos) |
| `.kiro/contexto/CHAT.md` | Archivado tracto antiguo |
| `.kiro/contexto/CHAT_LARGO.md` | +11,000 líneas archivadas |

## Commits realizados

| Hash | Descripción |
|------|-------------|
| `3edbbca` | feat(rag): add multi-format support and file browser |
| `a2c9cbb` | docs(chat): update session log with RAG multi-format implementation |
| `ecd380c` | docs(chat): archive first 11000 lines to CHAT_LARGO.md |

## Decisiones de diseño

| Decisión | Razón |
|----------|-------|
| subprocess para tkinter | tkinter necesita hilo principal; HTTP handlers corren en threads |
| Instalar `markitdown[xls]` aunque es obsoleto | No agrega peso, aumenta compatibilidad sin costo |
| NO instalar audio/youtube/azure | Requieren APIs externas, rompen filosofía offline de NEVEN |

## Pendientes para próxima sesión

| Prioridad | Tarea |
|-----------|-------|
| **ALTA** | Probar instalador en máquina limpia |
| **ALTA** | Reiniciar servidor y verificar botón browse funciona en Excel en vivo |
| MEDIA | Documentar formatos soportados en RAG_GUIDE.md |
| BAJA | Agregar botón browse al panel de indexado de ontologías también |

---
