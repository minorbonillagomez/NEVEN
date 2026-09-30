# NEVEN Enterprise — Diseño

## Visión general de la arquitectura

NEVEN Enterprise es una extensión de la arquitectura actual, no un reemplazo. El principio guía es **adición sin ruptura**: cada capa nueva es opcional desde la perspectiva del cliente existente.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEVEN Enterprise                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Capa de Presentación                      │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌───────────────────┐  ┌──────────────┐  │   │
│  │  │ NEVEN64.xll  │  │  Office Add-in    │  │  Excel Web   │  │   │
│  │  │ (Windows)    │  │  (Win + Mac)      │  │  (Browser)   │  │   │
│  │  │ XLL nativo   │  │  Office.js        │  │  Office.js   │  │   │
│  │  │ 200ms        │  │  Custom Functions │  │  Sin install │  │   │
│  │  └──────┬───────┘  └────────┬──────────┘  └──────┬───────┘  │   │
│  └─────────┼───────────────────┼─────────────────────┼──────────┘   │
│            │                   │                     │              │
│            ▼                   ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Capa de Enrutamiento                      │   │
│  │                                                              │   │
│  │   Router: local (localhost:5555) → cloud (api.neven.app)    │   │
│  │   Preferencia local cuando está disponible                   │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│            ┌────────────────┼────────────────┐                      │
│            ▼                ▼                ▼                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ NEVEN Local  │  │ NEVEN Cloud  │  │  Agente IA Service       │  │
│  │ (existente)  │  │ (nuevo)      │  │  (nuevo, independiente)  │  │
│  │              │  │              │  │                          │  │
│  │ localhost:   │  │ api.neven.   │  │  ai.neven.app            │  │
│  │ 5555         │  │ app          │  │  (o localhost:5556)      │  │
│  │              │  │              │  │                          │  │
│  │ R, Julia,    │  │ R, Julia,    │  │  Solo LLM proxy          │  │
│  │ Python,      │  │ Python       │  │  Gestión de sesiones     │  │
│  │ DuckDB       │  │ (contenedor  │  │  Historial de chat       │  │
│  │              │  │ por sesión)  │  │  Office.js bridge        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Componentes nuevos

### 1. NEVEN Cloud Server

El servidor Python actual (`neven_http_server.py`) ya tiene la API correcta. La evolución para cloud agrega:

**Gestión de sesiones**
```python
# Cada usuario tiene su propio espacio de trabajo
class Session:
    session_id: str          # UUID generado al autenticar
    user_id: str             # Identidad del usuario (Entra ID sub)
    tenant_id: str           # Organización
    r_process: subprocess    # Proceso R aislado para esta sesión
    python_env: dict         # Entorno Python aislado
    duckdb_conn: Connection  # Conexión DuckDB propia
    last_active: datetime    # Para limpieza de sesiones inactivas
    created_at: datetime
```

**Containerización de motores**
Cada sesión R corre en un proceso con restricciones:
- `rlimit` para memoria (configurable, default 2GB)
- Directorio de trabajo temporal aislado
- Sin acceso a filesystem del servidor fuera del directorio temporal
- Timeout de inactividad configurable (default 30 min)

**API idéntica al servidor local**
El servidor cloud expone exactamente la misma API que `localhost:5555`. El cliente (add-in, XLL) no sabe si está hablando con el servidor local o el cloud — solo cambia la URL base.

```
GET  /api/engines           → Estado de motores disponibles
POST /api/r                 → Ejecutar código R
POST /api/python            → Ejecutar código Python
POST /api/julia             → Ejecutar código Julia
POST /api/datalab/run       → Ejecutar análisis DataLab
POST /api/ai/chat           → Chat con LLM
GET  /api/ai/context/pending → Contexto pendiente de Excel
POST /api/load              → Cargar dataset en DuckDB
...
```

**Nuevos endpoints exclusivos del servidor cloud**
```
POST /auth/token            → Intercambio de token Entra ID
GET  /admin/sessions        → Panel de administración
GET  /admin/audit-log       → Log de auditoría
GET  /health                → Health check
GET  /ready                 → Readiness check
GET  /metrics               → Métricas Prometheus
```

---

### 2. Office Add-in

**Manifest (add-in only manifest)**
```xml
<OfficeApp>
  <Id>neven-enterprise-{tenant-guid}</Id>
  <Version>4.0.0</Version>
  <ProviderName>NEVEN</ProviderName>
  <DefaultLocale>es-419</DefaultLocale>
  <DisplayName DefaultValue="NEVEN Studio"/>
  
  <Hosts>
    <Host Name="Workbook"/>
  </Hosts>

  <DefaultSettings>
    <SourceLocation DefaultValue="https://{tenant}.neven.app/taskpane.html"/>
  </DefaultSettings>

  <!-- Custom Functions para recálculo automático -->
  <VersionOverrides>
    <Hosts>
      <Host xsi:type="Workbook">
        <FunctionFile resid="Functions.Url"/>
        <ExtensionPoint xsi:type="CustomFunctions">
          <Script>
            <SourceLocation resid="Functions.Script"/>
          </Script>
          <Page>
            <SourceLocation resid="Functions.Html"/>
          </Page>
          <Metadata>
            <SourceLocation resid="Functions.Json"/>
          </Metadata>
        </ExtensionPoint>
      </Host>
    </Hosts>
  </VersionOverrides>
</OfficeApp>
```

**Custom Functions (functions.js)**
```javascript
// Función principal — equivalente a =NEVEN.R() del XLL
async function nevenR(code, ...args) {
    const session = await getOrCreateSession();
    const response = await fetch(NEVEN_API + '/api/r', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + session.token
        },
        body: JSON.stringify({ code, args })
    });
    const data = await response.json();
    if (data.status === 'ok') return data.result;
    return CustomFunctions.Error.VALUE;  // #VALUE! en celda
}

// Registro en functions.json
{
  "functions": [{
    "id": "R",
    "name": "NEVEN.R",
    "description": "Ejecuta código R y retorna el resultado",
    "parameters": [
      { "name": "código", "description": "Código R a ejecutar" },
      { "name": "argumentos", "description": "Rangos o valores opcionales",
        "repeating": true }
    ],
    "result": { "dimensionality": "any" },
    "options": { "stream": false, "cancelable": true }
  }]
}
```

**Lectura de rangos con Office.js (reemplaza Excel Bridge)**
```javascript
// En el task pane — reemplaza el botón "Leer de Excel"
async function readSelectedRange() {
    return Excel.run(async (ctx) => {
        const range = ctx.workbook.getSelectedRange();
        range.load(['values', 'address', 'rowCount', 'columnCount',
                    'formulas', 'numberFormat']);
        await ctx.sync();
        return {
            values:    range.values,
            address:   range.address,
            rowCount:  range.rowCount,
            colCount:  range.columnCount
        };
    });
}

// Evento de cambio de selección — para el agente IA
Excel.run(async (ctx) => {
    ctx.workbook.onSelectionChanged.add(async (event) => {
        const data = await readSelectedRange();
        // Actualizar contexto del agente automáticamente
        updateAgentContext(data);
    });
    await ctx.sync();
});
```

---

### 3. Agente IA Service

Microservicio independiente. No tiene dependencia de R, Julia, ni DuckDB. Su único trabajo es gestionar conversaciones con el LLM y mantener contexto de sesión.

**Stack mínimo**
```
Python 3.12
FastAPI (reemplaza el HTTPServer manual)
Redis (gestión de sesiones y contexto pendiente)
PostgreSQL o SQLite (historial de chat persistente)
```

**API**
```
POST /api/ai/chat
  Body: { session_id, messages, context, prompt_id }
  Auth: Bearer token (Entra ID o API key)
  Returns: { status, reply, model, tokens_used }

POST /api/ai/context
  Body: { session_id, dataset_text, results_text, source }
  Returns: { status, message }

GET  /api/ai/context/pending?session_id=X
  Returns: { status, context } — consume y borra el contexto

GET  /api/ai/history?session_id=X
  Returns: { messages: [...] }

DELETE /api/ai/history?session_id=X
  Returns: { status: "ok" }

WebSocket /ws/ai/chat
  Para streaming de respuestas del LLM
```

**Gestión de sesiones**
```python
# El session_id se genera en el cliente y se envía en cada request
# No hay estado en el servidor más allá del contexto pendiente y el historial

# Redis keys:
# ai:context:{session_id}       → contexto pendiente (TTL 10 min)
# ai:history:{session_id}       → historial de mensajes (TTL 24h)
# ai:session:{session_id}:meta  → metadatos de sesión (TTL 24h)
```

**Office Add-in autónomo del agente**

El agente puede desplegarse como add-in independiente del Studio completo. Manifest mínimo:

```xml
<OfficeApp>
  <Id>neven-ai-agent-{guid}</Id>
  <DisplayName DefaultValue="NEVEN AI"/>
  <DefaultSettings>
    <SourceLocation DefaultValue="https://ai.neven.app/agent.html"/>
  </DefaultSettings>
</OfficeApp>
```

`agent.html` es una versión reducida del tab IA actual, con:
- Historial de chat
- Botón "Enviar selección" (lee rango con Office.js)
- Botones "+ Datos", "+ Resultados" (si hay conexión al servidor local)
- Sin los otros tabs (DataLab, Run Script, etc.)

---

### 4. Router de API

Componente JavaScript que resuelve la URL del servidor en tiempo de ejecución:

```javascript
class NevenRouter {
    constructor(config) {
        this.localUrl  = config.localUrl  || 'http://localhost:5555';
        this.cloudUrl  = config.cloudUrl  || 'https://api.neven.app';
        this.aiUrl     = config.aiUrl     || 'https://ai.neven.app';
        this._local    = null;  // null = no verificado aún
    }

    async getComputeUrl() {
        // Verificar si el servidor local está disponible
        if (this._local === null) {
            try {
                await fetch(this.localUrl + '/api/engines', 
                    { signal: AbortSignal.timeout(500) });
                this._local = true;
            } catch {
                this._local = false;
            }
        }
        return this._local ? this.localUrl : this.cloudUrl;
    }

    getAiUrl() {
        // El agente IA siempre va al servicio de IA
        // (puede ser local o cloud según config)
        return this.aiUrl;
    }
}
```

---

## Plan de fases

### Fase 1 — Agente IA como servicio independiente (6-8 semanas)
*Esta es la primera implementación — ver spec separado*

- Extraer `_handle_ai_chat` y endpoints de contexto a `neven_ai_service.py`
- FastAPI + Redis para gestión de sesiones
- Office Add-in mínimo (`agent.html`) con Office.js
- Lectura de rangos con `Excel.run()`
- Despliegue en servidor con HTTPS

Resultado: El agente funciona en Excel Windows, Mac, y Web sin instalar NEVEN.

### Fase 2 — Custom Functions para macOS (8-10 semanas)

- Implementar `functions.js` con `NEVEN.R()` y `NEVEN.J()`
- API de sesiones en el servidor local existente
- Manifest completo del add-in
- Testing en macOS con Excel para Mac

Resultado: `=NEVEN.R()` funciona en Mac con latencia de red.

### Fase 3 — Servidor cloud multi-sesión (12-16 semanas)

- Containerización de motores R/Julia por sesión (Docker)
- Gestión de sesiones en el servidor
- Autenticación con Entra ID
- Despliegue en Azure App Service o equivalente

Resultado: NEVEN funciona sin instalación local en Windows y Mac.

### Fase 4 — Enterprise features (12-16 semanas)

- Roles y permisos (admin/analyst/viewer)
- Log de auditoría
- Panel de administración
- Cumplimiento GDPR
- On-premise deployment package

Resultado: NEVEN es vendible a enterprise.

### Fase 5 — Ecosistema (continuo)

- `.buklo` en Azure Blob / S3
- Compartir sesiones de análisis
- Integración con Microsoft Teams
- API pública para integraciones third-party

---

## Decisiones de diseño

**¿Por qué FastAPI en lugar del HTTPServer manual para el servicio IA?**
El servidor actual usa `http.server.BaseHTTPRequestHandler` — correcto para un servidor local de baja concurrencia. El servicio IA en cloud necesita manejar decenas de conexiones concurrentes con timeouts de 120 segundos (duración del request LLM). FastAPI con uvicorn/gunicorn está diseñado para exactamente ese patrón asíncrono.

**¿Por qué Redis para el contexto pendiente?**
El contexto pendiente actual usa una variable global Python (`_excel_context_pending`). En un servidor con múltiples workers (necesario para concurrencia), esa variable no se comparte entre procesos. Redis es la solución estándar para estado compartido entre workers sin complejidad de base de datos relacional.

**¿Por qué mantener el servidor Python existente en lugar de reescribirlo?**
El servidor actual tiene ~1,500 líneas de lógica probada en producción para DataLab, BUKLO, exportación de informes, y gestión de paquetes. Reescribirlo introduce riesgo sin beneficio. La estrategia es extraer el servicio IA a FastAPI y dejar el resto en su implementación actual, migrando incrementalmente.

**¿Por qué no usar el SDK oficial de Office Add-ins (Yeoman generator)?**
El taskpane actual es HTML + JS vanilla sin framework. El SDK de Yeoman genera proyectos React/TypeScript con Webpack. Migrar a ese stack es trabajo de semanas y agrega una cadena de build que hoy no existe. Para la Fase 1 (agente IA), es más eficiente escribir `agent.html` con el mismo estilo que el taskpane actual.

**¿Por qué session_id generado en el cliente?**
Simplifica el servidor (no necesita mantener estado de autenticación por token), permite que el cliente controle el ciclo de vida de la sesión, y facilita el escenario de "compartir sesión" — el usuario simplemente comparte su session_id. La seguridad se delega a la capa de autenticación (Bearer token) independientemente del session_id.
