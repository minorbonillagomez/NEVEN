# NEVEN AI Service — Guía de implementación

## Qué es

El Agente IA de NEVEN puede funcionar de dos formas:

1. **Modo integrado (default):** El tab IA de NEVEN Studio habla directamente con el servidor local en `localhost:5555`. Todo corre en la máquina del usuario Windows con NEVEN instalado.

2. **Modo servicio independiente (Fase 1 Enterprise):** El Agente IA corre como un microservicio FastAPI separado (`neven_ai_service.py`) en el puerto 5556 (o en cloud). Esto permite:
   - Usar el agente desde **Excel en macOS** sin instalar NEVEN
   - Usar el agente desde **Excel Web** (browser)
   - Desplegar el agente en **cloud** para usuarios sin instalación local
   - El agente como **Office Add-in autónomo** visible en el task pane lateral de Excel

---

## Archivos del proyecto

```
NEVEN/AgentService/
├── neven_ai_service.py         ← Microservicio FastAPI (el corazón)
├── manifest.xml                ← Manifest producción (→ ai.neven.app)
├── manifest.dev.xml            ← Manifest desarrollo (→ localhost:5556)
├── sideload.ps1                ← Script de instalación local para desarrollo
└── static/
    ├── agent.html              ← Office Add-in del agente (UI completa)
    ├── commands.html           ← Requerido por el manifest (slot FunctionFile)
    └── icon-*.svg              ← Íconos del add-in
```

**Archivos modificados en el sistema existente:**

| Archivo | Cambio |
|---------|--------|
| `neven-config.json` | Sección `AIService` nueva con `enabled` y `url` |
| `TaskPane/taskpane.html` | `AI_API` variable + `_resolveAiServiceUrl()` — todos los fetch `/api/ai/*` usan `AI_API` |
| `ControlPython/startup/neven_http_server.py` | Endpoint `GET /api/ai/service-url` |
| `Core/src/basic_functions.cc` | `RJ_IA_Contexto` lee `AIService` del config para el puerto del POST |

---

## Arranque rápido — desarrollo local

### 1. Instalar dependencias

```powershell
pip install fastapi==0.115.0 uvicorn==0.30.6
```

### 2. Iniciar el servicio IA

```powershell
cd F:\ANTIGRAVITY\2026\NEVEN\NEVEN\AgentService
python neven_ai_service.py --port 5556
```

El servicio levanta en `http://localhost:5556` y sirve `agent.html` en la raíz.

Verificar que funciona:
```powershell
Invoke-RestMethod http://localhost:5556/health
# → {"status":"ok","service":"neven-ai","version":"1.0.0",...}
```

### 3. Registrar el add-in en Excel (sideloading)

```powershell
cd F:\ANTIGRAVITY\2026\NEVEN\NEVEN\AgentService
PowerShell -ExecutionPolicy Bypass -File sideload.ps1
```

El script:
- Crea `%LOCALAPPDATA%\NEVEN\AddInCatalog\`
- Copia `manifest.dev.xml` como `neven-ai-agent.xml`
- Registra la carpeta como catálogo confiable en el registro de Windows

### 4. Activar en Excel

1. Abre Excel (o reinícialo si ya estaba abierto)
2. **Insertar → Mis complementos → CARPETA COMPARTIDA**
3. Selecciona **NEVEN AI [DEV]** → Agregar
4. El panel aparece en el lado derecho de la hoja

### 5. (Opcional) Activar el servicio en NEVEN Studio

Para que el tab IA de NEVEN Studio también use el servicio independiente, edita `C:\NEVEN\neven-config.json`:

```json
"AIService": {
    "enabled": true,
    "url": "http://localhost:5556"
}
```

Reinicia el servidor Python de NEVEN Studio para aplicar el cambio.

---

## Flujo de datos completo

```
┌─────────────────────────────────────────────────────────────┐
│                       Excel Desktop                         │
│                                                             │
│  ┌──────────────────┐        ┌─────────────────────────┐   │
│  │  NEVEN64.xll     │        │  Office Add-in          │   │
│  │                  │        │  (agent.html)           │   │
│  │ =NEVEN.IA.       │        │                         │   │
│  │  Contexto(A1:D50)│        │  Office.js              │   │
│  │                  │        │  Excel.run()            │   │
│  │  Lee config →    │        │  getSelectedRange()     │   │
│  │  AIService.url   │        │                         │   │
│  └────────┬─────────┘        └──────────┬──────────────┘   │
└───────────┼───────────────────────────  ┼  ────────────────┘
            │                             │
            │ POST /api/ai/context        │ POST /api/ai/context
            │ (datos CSV + rangos)        │ (datos CSV + Excel.js)
            ▼                             ▼
┌───────────────────────────────────────────────────────────┐
│              neven_ai_service.py (FastAPI)                │
│                         :5556                             │
│                                                           │
│  _pending_context[session_id] = { text, columns, n_rows } │
│                                                           │
│  GET /api/ai/context/pending?session_id=X                 │
│    ← agent.html hace polling cada 3s                      │
│    ← NEVEN Studio hace polling cada 3s                    │
│                                                           │
│  POST /api/ai/chat                                        │
│    → _build_system_prompt(context)                        │
│    → _call_llm(messages, ai_config)                       │
│    → Azure OpenAI / OpenRouter / LM Studio                │
│    ← {reply, tokens_used, model}                          │
└───────────────────────────────────────────────────────────┘
```

### Flujo A — usuario con XLL (Windows)

1. Usuario selecciona rangos en Excel y ejecuta `=NEVEN.IA.Contexto(A1:D50, G1:G20)`
2. `RJ_IA_Contexto` lee `AIService.url` de `neven-config.json` → determina el puerto
3. Hace `POST localhost:5556/api/ai/context` con el CSV de los rangos
4. El servicio almacena el contexto en `_pending_context[session_id]`
5. El add-in (`agent.html`) hace polling a `GET /api/ai/context/pending`
6. Al recibir el contexto, lo muestra en el chat y lo inyecta en `_aiState.context`
7. El usuario escribe una pregunta → `POST /api/ai/chat` → respuesta del LLM

### Flujo B — usuario sin XLL (macOS, Excel Web)

1. Usuario abre el add-in → `agent.html` se carga en el task pane
2. Usuario selecciona un rango en Excel
3. Pulsa **Enviar selección** → `Excel.run()` lee el rango vía Office.js
4. `agent.html` hace `POST /api/ai/context` con el CSV
5. El contexto se inyecta directamente en `_aiState.context` (sin polling)
6. El usuario escribe una pregunta → `POST /api/ai/chat` → respuesta del LLM

---

## Configuración de neven-config.json

```json
{
  "AIService": {
    "enabled": false,
    "url": "http://localhost:5556",
    "comment": "Cambiar a https://ai.neven.app para cloud"
  }
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `enabled` | bool | `false` = usar servidor local (default). `true` = usar URL externa |
| `url` | string | URL base del servicio IA. Sin `/` al final |

**Cuando `enabled: false`** (default): todo funciona exactamente igual que antes. El tab IA y `RJ_IA_Contexto` hablan con `localhost:5555`. No hay cambio de comportamiento.

**Cuando `enabled: true`**: el tab IA usa `AI_API = url` para los endpoints `/api/ai/*`. `RJ_IA_Contexto` hace el POST al puerto extraído de `url`.

---

## Endpoints del servicio

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Health check — estado del proceso |
| `GET` | `/ready` | Readiness — confirma que el LLM está configurado |
| `GET` | `/` | Sirve `agent.html` (el Office Add-in) |
| `GET` | `/manifest.xml` | Sirve el manifest del add-in |
| `POST` | `/api/ai/chat` | Conversación con el LLM |
| `POST` | `/api/ai/context` | Recibir contexto de Excel (rangos) |
| `GET` | `/api/ai/context/pending` | Leer y consumir contexto pendiente |
| `DELETE` | `/api/ai/context/{session_id}` | Limpiar contexto de una sesión |
| `GET` | `/api/ai/history/{session_id}` | Historial de chat |
| `DELETE` | `/api/ai/history/{session_id}` | Limpiar historial |
| `GET` | `/api/ai/sessions` | Lista de sesiones activas (admin/debug) |
| `GET` | `/docs` | Documentación interactiva de la API (FastAPI Swagger) |

---

## Opciones de arranque

```
python neven_ai_service.py [opciones]

  --port    INT     Puerto HTTP (default: 5556)
  --host    STR     Host (default: 127.0.0.1)
                    Usar 0.0.0.0 para acceso en red / cloud
  --config  PATH    Ruta a neven-config.json
  --reload          Hot reload (solo desarrollo)
```

Ejemplos:

```powershell
# Desarrollo local
python neven_ai_service.py --port 5556 --reload

# Producción en servidor (escuchar en todas las interfaces)
python neven_ai_service.py --port 5556 --host 0.0.0.0

# Con config en ruta no estándar
python neven_ai_service.py --config D:\configs\neven-config.json
```

---

## Despliegue en cloud

### Requisitos mínimos del servidor

- Python 3.12+
- `pip install fastapi==0.115.0 uvicorn==0.30.6`
- Acceso a internet para llamar a Azure OpenAI / OpenRouter
- HTTPS con certificado válido (requerido por Office Add-ins en producción)

### Variables de entorno (alternativa al config file)

El servicio lee la configuración desde `neven-config.json`. Para despliegue en cloud se puede crear el archivo de config a partir de variables de entorno en el script de inicio:

```bash
#!/bin/bash
cat > /opt/neven/neven-config.json << EOF
{
  "AI": {
    "enabled": true,
    "provider": "azure",
    "apiKey": "$AZURE_OPENAI_KEY",
    "model": "$AZURE_MODEL",
    "endpoint": "$AZURE_ENDPOINT",
    "apiVersion": "2024-02-15-preview",
    "maxTokens": 2000,
    "temperature": 0.3,
    "timeout": 120
  }
}
EOF
python neven_ai_service.py --host 0.0.0.0 --port 443 --config /opt/neven/neven-config.json
```

### Nginx como proxy inverso (HTTPS)

```nginx
server {
    listen 443 ssl;
    server_name ai.neven.app;

    ssl_certificate     /etc/letsencrypt/live/ai.neven.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.neven.app/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:5556;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 130s;  # mayor que el timeout del LLM (120s)
    }
}
```

### Actualizar el manifest para producción

Reemplazar `localhost:5556` con el dominio real en `manifest.xml`:

```xml
<SourceLocation DefaultValue="https://ai.neven.app/"/>
```

Y actualizar `neven-config.json` en los clientes:

```json
"AIService": {
    "enabled": true,
    "url": "https://ai.neven.app"
}
```

---

## Desinstalar el add-in (sideloading)

```powershell
PowerShell -ExecutionPolicy Bypass -File sideload.ps1 -Remove
```

O manualmente en Excel: **Insertar → Mis complementos → ··· → Quitar**

---

## Gestión de sesiones

Cada instancia del add-in genera un `session_id` único almacenado en `sessionStorage`. El servicio mantiene:

- **Contexto pendiente** (`_pending_context`): TTL implícito de 10 minutos por inactividad
- **Historial de chat** (`_chat_history`): TTL de 24 horas
- **Limpieza automática** cada 10 minutos — sesiones inactivas >24h se eliminan

Para compartir contexto entre usuarios (funcionalidad futura), el `session_id` puede pasarse como parámetro en la URL del add-in: `https://ai.neven.app/?session=XXXXX`.

---

## Diferencias con el modo integrado (localhost:5555)

| Característica | Modo integrado | Modo servicio |
|----------------|---------------|---------------|
| Requiere NEVEN instalado | Sí | No |
| Funciona en macOS | No | Sí |
| Funciona en Excel Web | No | Sí |
| Latencia | ~0ms (local) | ~50-200ms (local) / variable (cloud) |
| Soporte de streaming | No | Planificado en Fase 2 |
| Historial persistente | Solo en `.buklo` | En memoria (cloud: base de datos) |
| Configuración centralizada | Por máquina | Por servidor |
| `=NEVEN.IA.Contexto()` | Sí | Sí (puerto configurable) |
| Office.js `Excel.run()` | No | Sí (reemplaza la función XLL) |

---

## Hoja de ruta (fases futuras)

- **Fase 2 — Custom Functions:** `=NEVEN.R()` y `=NEVEN.J()` como Custom Functions de Office.js, con recálculo automático, para usuarios macOS
- **Fase 3 — Servidor cloud multi-sesión:** R y Julia en contenedores Docker por sesión, autenticación con Entra ID
- **Fase 4 — Enterprise features:** roles, auditoría, GDPR, on-premise deployment

Ver el spec completo: `.kiro/specs/neven-enterprise/`
