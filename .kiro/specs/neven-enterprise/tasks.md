# NEVEN Enterprise — Tareas

Las tareas están organizadas por fase. Solo la Fase 1 tiene tareas detalladas — las fases posteriores se detallarán cuando la anterior esté completa.

## Fase 1 — Agente IA como servicio independiente

### Bloque A: Servicio IA (backend)

- [ ] **A1** Crear `neven_ai_service.py` con FastAPI extrayendo `_handle_ai_chat`, `_handle_ai_context`, y `GET /api/ai/context/pending` del servidor actual
- [ ] **A2** Agregar gestión de sesiones basada en `session_id` con TTL configurable (default 24h)
- [ ] **A3** Agregar soporte para múltiples workers con estado compartido (Redis o variable de módulo con lock — Redis para producción, variable para desarrollo local)
- [ ] **A4** Agregar endpoint `WebSocket /ws/ai/chat` para streaming de respuestas del LLM
- [ ] **A5** Configurar CORS para permitir requests desde `*.neven.app` y `localhost`
- [ ] **A6** Agregar `GET /health` y `GET /ready` para health checks
- [ ] **A7** Tests de integración del servicio IA (pytest, sin mocks del LLM — usar cuenta Azure real en tests de integración)

### Bloque B: Office Add-in del agente (frontend)

- [ ] **B1** Crear `agent.html` — versión standalone del tab IA actual, adaptada a 350px de ancho
- [ ] **B2** Integrar `office.js` de CDN de Microsoft y llamar `Office.onReady()` al iniciar
- [ ] **B3** Implementar `readSelectedRange()` con `Excel.run()` — reemplaza `NEVEN.IA.Contexto`
- [ ] **B4** Agregar botón "Enviar selección al agente" que lee el rango activo y hace POST a `/api/ai/context`
- [ ] **B5** Implementar `onSelectionChanged` listener para actualizar un preview del rango seleccionado en el panel
- [ ] **B6** Conectar `_aiCallLLM` al servicio IA en lugar de al servidor local, con fallback a local si está disponible
- [ ] **B7** Adaptar CSS del tab IA para layout de 350px (task pane width)

### Bloque C: Manifest y despliegue

- [ ] **C1** Crear `manifest.xml` del Office Add-in con `SourceLocation` apuntando al servicio IA
- [ ] **C2** Crear script de sideloading para desarrollo local (registro en `HKCU\Software\Microsoft\Office\16.0\WEF\Developer`)
- [ ] **C3** Configurar HTTPS en el servidor del agente (Let's Encrypt o certificado existente)
- [ ] **C4** Desplegar `neven_ai_service.py` en servidor con HTTPS
- [ ] **C5** Desplegar `agent.html` y assets estáticos
- [ ] **C6** Verificar funcionamiento en Excel Desktop Windows, Excel Desktop Mac (si hay acceso), y Excel Web

### Bloque D: Integración con NEVEN local

- [ ] **D1** Actualizar `neven-config.json` con sección `"AIService"` que permite apuntar a URL externa
- [ ] **D2** Actualizar `taskpane.html` para que el tab IA use la URL del servicio IA si está configurada
- [ ] **D3** Actualizar `RJ_IA_Contexto()` en C++ para hacer POST al servicio IA (URL configurable) en lugar de siempre a `localhost:5555`
- [ ] **D4** Documentar el flujo completo en `docs/AGENTE_IA_SERVICE.md`

## Fase 2 — Custom Functions (pendiente Fase 1)
*Detallar al completar Fase 1*

## Fase 3 — Servidor cloud multi-sesión (pendiente Fase 2)
*Detallar al completar Fase 2*

## Fase 4 — Enterprise features (pendiente Fase 3)
*Detallar al completar Fase 3*
