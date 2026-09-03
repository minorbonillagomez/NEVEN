# =============================================================================
# NEVEN AI Service — Microservicio independiente del Agente IA
# =============================================================================
#
# Servicio FastAPI que expone el Agente IA de NEVEN como un endpoint HTTP
# independiente del servidor local de cómputo (neven_http_server.py).
#
# Diseñado para:
#   - Correr localmente junto a NEVEN Studio (puerto 5556)
#   - Desplegarse en cloud para usuarios macOS / Excel Web (sin instalación local)
#   - Servir el Office Add-in autónomo del agente (agent.html)
#
# Endpoints:
#   POST /api/ai/chat                   → Conversación con el LLM
#   POST /api/ai/context                → Recibir contexto de Excel
#   GET  /api/ai/context/pending        → Leer y consumir contexto pendiente
#   DELETE /api/ai/context/{session_id} → Limpiar contexto de una sesión
#   GET  /api/ai/history/{session_id}   → Historial de chat
#   DELETE /api/ai/history/{session_id} → Limpiar historial
#   GET  /health                        → Health check
#   GET  /ready                         → Readiness check
#   GET  /                              → Sirve agent.html (task pane)
#   GET  /{path}                        → Sirve archivos estáticos del add-in
#
# Requisitos:
#   pip install fastapi==0.115.0 uvicorn==0.30.6
#   (sin dependencias adicionales — usa urllib.request para llamadas al LLM)
#
# Arranque:
#   python neven_ai_service.py [--port 5556] [--config C:\NEVEN\neven-config.json]
# =============================================================================

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
import threading
import time
import urllib.request as _url_req
from collections import defaultdict
from pathlib import Path
from typing import Any

# ── FastAPI ───────────────────────────────────────────────────────────────────
try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False
    print(
        "[NEVEN AI] FastAPI no está instalado.\n"
        "  Instala con: pip install fastapi==0.115.0 uvicorn==0.30.6",
        file=sys.stderr
    )
    sys.exit(1)

# =============================================================================
# Configuración
# =============================================================================

DEFAULT_CONFIG_PATHS = [
    r"C:\NEVEN\neven-config.json",
    "/opt/neven/neven-config.json",
    str(Path(__file__).parent.parent / "neven-config.json"),
]

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("neven.ai")


def _load_config(config_path: str | None = None) -> dict:
    """Carga neven-config.json desde la ruta indicada o desde las rutas default."""
    paths = ([config_path] if config_path else []) + DEFAULT_CONFIG_PATHS
    for p in paths:
        if p and os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                log.info(f"Config cargada: {p}")
                return cfg
            except Exception as exc:
                log.warning(f"No se pudo leer {p}: {exc}")
    log.warning("neven-config.json no encontrado — usando defaults")
    return {}


# Config global (se inicializa en startup)
_config: dict = {}
_ai_cfg: dict = {}

# =============================================================================
# Gestión de sesiones y contexto
# =============================================================================

_context_lock = threading.Lock()

# Contexto pendiente por session_id: {session_id: {text, timestamp, ...}}
# Cada entrada se consume (borra) al ser leída por el cliente
_pending_context: dict[str, dict] = {}

# Historial de mensajes por session_id: {session_id: [{role, content}, ...]}
_chat_history: dict[str, list] = defaultdict(list)

# TTL de sesiones inactivas (segundos). Limpieza periódica cada 10 min.
SESSION_TTL_SEC = 24 * 3600  # 24 horas
_session_last_active: dict[str, float] = {}


def _touch_session(session_id: str) -> None:
    _session_last_active[session_id] = time.time()


def _cleanup_stale_sessions() -> None:
    """Elimina sesiones inactivas para liberar memoria."""
    cutoff = time.time() - SESSION_TTL_SEC
    stale = [sid for sid, t in _session_last_active.items() if t < cutoff]
    with _context_lock:
        for sid in stale:
            _pending_context.pop(sid, None)
            _chat_history.pop(sid, None)
            _session_last_active.pop(sid, None)
    if stale:
        log.info(f"Sesiones eliminadas por inactividad: {len(stale)}")


def _start_cleanup_thread() -> None:
    def _loop():
        while True:
            time.sleep(600)  # cada 10 minutos
            try:
                _cleanup_stale_sessions()
            except Exception as exc:
                log.warning(f"Error en limpieza de sesiones: {exc}")

    t = threading.Thread(target=_loop, daemon=True)
    t.start()

# =============================================================================
# Motor de construcción del system prompt
# (lógica extraída de neven_http_server.py — idéntica para compatibilidad)
# =============================================================================

_FMT = (
    "Responde siempre en español a menos que el usuario escriba en otro idioma. "
    "Usa Markdown para formatear tu respuesta. "
    "Para fórmulas matemáticas usa SIEMPRE delimitadores Markdown estándar: "
    "$$...$$ para fórmulas en bloque y $...$ para fórmulas inline. "
    "NUNCA uses \\(...\\) ni \\[...\\] ni ninguna otra notación LaTeX."
)

_RUN_HINT_TEMPLATE = (
    "Cuando sugieras un nuevo análisis o corrección metodológica, "
    "incluye un bloque ```neven-run con el JSON de la llamada. "
    "El schema EXACTO es: "
    "{\"function_id\": string, \"language\": \"r\"|\"python\"|\"julia\", "
    "\"column_roles\": {\"Y\": [...], \"X\": [...], \"Z\": [...]}, "
    "\"parameters\": {}, \"context_note\": string}. "
    "IMPORTANTE: language SIEMPRE debe ser \"r\", \"python\" o \"julia\" en minúsculas. "
    "Los function_id disponibles para R son: RG_Lineal, RG_2SLS, RG_Logistica, "
    "RG_Poisson, RG_Tobit, RG_HECKIT, RG_DatosPanel, RG_FGLS, RG_Newey_West, "
    "RG_RESET, ST_VAR, ST_ECM. "
    "Usa EXACTAMENTE uno de estos IDs. "
    "El usuario podrá ejecutarlo con un clic desde el chat. "
)


def _build_system_prompt(context: str) -> str:
    """
    Construye el system prompt según el tipo de contexto detectado.
    Lógica idéntica a neven_http_server.py para compatibilidad total.
    """
    has_method  = "=== CONTEXTO METODOLÓGICO ===" in context
    has_dataset = "Dataset:" in context or "filas" in context
    has_results = "=== RESULTADOS DEL ANÁLISIS ===" in context
    has_history = "=== HISTORIAL DE MODELOS ===" in context
    has_excel   = "=== DATOS DE EXCEL ===" in context

    run_hint = _RUN_HINT_TEMPLATE if (has_results or has_history) else ""

    if has_history:
        return (
            "Eres NEVEN Assistant, un econometrista experto. "
            "Tienes acceso al historial completo de modelos estimados en esta sesión. "
            "Tu tarea principal es comparar especificaciones, coeficientes y métricas "
            "entre los modelos del historial y razonar sobre la evolución del análisis. "
            "Basa tu razonamiento en la ontología econométrica de NEVEN "
            "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
            + run_hint
            + f"Historial de modelos estimados:\n\n{context}\n\n"
            + _FMT
        )
    elif has_results and has_method:
        return (
            "Eres NEVEN Assistant, un econometrista experto. "
            "Tienes acceso a la estimación real del usuario: coeficientes, "
            "p-valores, R², tests diagnósticos y advertencias metodológicas. "
            "Responde sobre ESTE modelo específico, no en abstracto. "
            "Tu base de conocimiento incluye la ontología econométrica de NEVEN "
            "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
            + run_hint
            + f"Contexto completo del usuario:\n\n{context}\n\n"
            + _FMT
        )
    elif has_results and has_dataset:
        return (
            "Eres NEVEN Assistant, un analista de datos experto. "
            "Tienes acceso a los resultados reales del análisis del usuario "
            "y a la estructura de sus datos. "
            "Responde sobre ESTE modelo específico. "
            + run_hint
            + f"Contexto del usuario:\n\n{context}\n\n"
            + _FMT
        )
    elif has_results:
        return (
            "Eres NEVEN Assistant, un econometrista experto. "
            "Tienes acceso a los resultados del análisis del usuario. "
            "Responde sobre ESTE modelo específico. "
            + run_hint
            + f"Resultados del análisis:\n\n{context}\n\n"
            + _FMT
        )
    elif has_method and has_dataset:
        return (
            "Eres NEVEN Assistant, un econometrista y analista de datos experto. "
            "El usuario trabaja con NEVEN, un add-in de Excel que integra R, Julia y Python. "
            "Tu base de conocimiento incluye la ontología econométrica de NEVEN "
            "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
            f"Contexto actual del usuario:\n\n{context}\n\n"
            "Sé preciso y pedagógico: explica el razonamiento, no solo el resultado. "
            + _FMT
        )
    elif has_method:
        return (
            "Eres NEVEN Assistant, un econometrista experto especializado en "
            "R, Julia y Python aplicados al análisis de datos. "
            "Tu base de conocimiento incluye la ontología econométrica de NEVEN "
            "(Wooldridge, Hanck et al., MIT 14.382/14.384/14.387). "
            f"Marco metodológico activo del usuario:\n\n{context}\n\n"
            + _FMT
        )
    elif has_excel:
        return (
            "Eres NEVEN Assistant, un analista de datos experto. "
            "El usuario ha enviado datos directamente desde su hoja de cálculo de Excel. "
            "Tienes acceso a los datos reales con los que está trabajando. "
            "Responde sobre ESTOS datos específicos, no en abstracto. "
            "Cuando sugieras un análisis, menciona las columnas por su nombre real. "
            + run_hint
            + f"Datos de la hoja de cálculo del usuario:\n\n{context}\n\n"
            + _FMT
        )
    else:
        return (
            "Eres NEVEN Assistant, un analista de datos experto. "
            "El usuario está trabajando con NEVEN, "
            "un add-in de Excel con R, Julia y Python. "
            f"Contexto del dataset actual:\n\n{context}\n\n"
            + _FMT
        )


_FMT_MINIMAL = (
    "Eres NEVEN Assistant, un analista de datos y econometrista experto. "
    "Responde siempre en español a menos que el usuario escriba en otro idioma. "
    "Usa Markdown para formatear tu respuesta. "
    "Para fórmulas matemáticas usa SIEMPRE delimitadores Markdown estándar: "
    "$$...$$ para fórmulas en bloque y $...$ para fórmulas inline. "
    "NUNCA uses \\(...\\) ni \\[...\\] ni ninguna otra notación LaTeX."
)

# =============================================================================
# Cliente HTTP al LLM (reutiliza la lógica existente de neven_http_server.py)
# =============================================================================

def _call_llm(messages: list[dict], ai: dict) -> dict:
    """
    Llama al LLM configurado y retorna {reply, model, tokens_used}.
    Soporta: azure, openrouter, lmstudio, ollama, openai-compatible.
    Lanza RuntimeError con mensaje legible en caso de error.
    """
    endpoint    = ai.get("endpoint", "http://localhost:1234/v1/chat/completions")
    model       = ai.get("model", "local-model")
    max_tokens  = int(ai.get("maxTokens", 1000))
    temperature = float(ai.get("temperature", 0.3))
    timeout_sec = int(ai.get("timeout", 60))
    api_key     = ai.get("apiKey", "")
    provider    = ai.get("provider", "lmstudio")

    headers = {"Content-Type": "application/json"}

    if api_key and provider not in ("ollama", "lmstudio"):
        headers["Authorization"] = f"Bearer {api_key}"

    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://neven-studio.app"
        headers["X-Title"]      = "NEVEN Studio"

    if provider == "azure":
        headers.pop("Authorization", None)
        headers["api-key"] = api_key
        api_version = ai.get("apiVersion", "2024-02-15-preview")
        azure_base  = endpoint.rstrip("/")
        endpoint    = (
            f"{azure_base}/openai/deployments/{model}"
            f"/chat/completions?api-version={api_version}"
        )
        body = json.dumps({
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temperature,
        }, ensure_ascii=False).encode("utf-8")
    else:
        body = json.dumps({
            "model":       model,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temperature,
        }, ensure_ascii=False).encode("utf-8")

    try:
        req = _url_req.Request(endpoint, data=body, headers=headers, method="POST")
        with _url_req.urlopen(req, timeout=timeout_sec) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except _url_req.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8")
            err_json = json.loads(err_body)
            detail = (
                err_json.get("error", {}).get("message")
                or err_json.get("message")
                or err_body[:300]
            )
        except Exception:
            detail = str(exc)
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
    except _url_req.URLError as exc:
        reason = str(exc.reason) if hasattr(exc, "reason") else str(exc)
        raise RuntimeError(
            f"No se pudo conectar al LLM ({provider}). Detalle: {reason}"
        ) from exc

    try:
        reply  = data["choices"][0]["message"]["content"].strip()
        tokens = data.get("usage", {}).get("total_tokens", 0)
    except (KeyError, IndexError) as exc:
        raise RuntimeError(
            f"Respuesta inesperada del LLM: {str(data)[:200]}"
        ) from exc

    return {"reply": reply, "model": model, "tokens_used": tokens}

# =============================================================================
# Aplicación FastAPI
# =============================================================================

app = FastAPI(
    title="NEVEN AI Service",
    description="Agente IA de NEVEN como microservicio independiente",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# CORS: permite requests desde cualquier origen (Office Add-in, localhost, dominio cloud)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-Id"],
)

# Directorio de archivos estáticos del add-in (agent.html, etc.)
_STATIC_DIR = Path(__file__).parent / "static"

# =============================================================================
# Startup / shutdown
# =============================================================================

@app.on_event("startup")
async def _startup():
    global _config, _ai_cfg

    # Parsear argumentos de línea de comandos
    # (FastAPI no los expone directamente — leer de sys.argv)
    cfg_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            cfg_path = sys.argv[i + 1]

    _config  = _load_config(cfg_path)
    _ai_cfg  = _config.get("AI", {})

    if not _ai_cfg.get("enabled", False):
        log.warning(
            "AI.enabled=false en neven-config.json. "
            "El servicio arrancará pero el endpoint /api/ai/chat retornará 503."
        )

    _start_cleanup_thread()
    log.info("NEVEN AI Service iniciado")

# =============================================================================
# Health / readiness
# =============================================================================

@app.get("/health")
async def health() -> dict:
    """Health check — retorna 200 si el proceso está activo."""
    return {
        "status":    "ok",
        "service":   "neven-ai",
        "version":   "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


@app.get("/ready")
async def ready() -> dict:
    """Readiness check — retorna 200 cuando el servicio está listo para recibir tráfico."""
    ai_ok = bool(_ai_cfg.get("enabled", False))
    if not ai_ok:
        raise HTTPException(503, "AI no habilitada en neven-config.json")
    return {"status": "ready", "provider": _ai_cfg.get("provider", "?")}

# =============================================================================
# POST /api/ai/chat
# =============================================================================

@app.post("/api/ai/chat")
async def ai_chat(request: Request) -> JSONResponse:
    """
    Conversación con el LLM.

    Body JSON:
        session_id  : str (opcional) — identificador de sesión para historial
        messages    : [{role, content}] — historial completo
        context     : str (opcional) — contexto inyectado como system prompt
        prompt_id   : str (opcional) — ID de prompt template

    Returns:
        {status, reply, model, tokens_used}
    """
    # Recargar config en cada request para reflejar cambios en neven-config.json
    # sin reiniciar el servicio (util en desarrollo)
    ai = _config.get("AI", {})
    if not ai.get("enabled", False):
        raise HTTPException(503, "AI.enabled=false en neven-config.json")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Body JSON inválido")

    session_id = (body.get("session_id") or
                  request.headers.get("X-Session-Id") or
                  "default")
    messages   = body.get("messages", [])
    context    = (body.get("context") or "").strip()
    prompt_id  = (body.get("prompt_id") or "").strip()

    _touch_session(session_id)

    # Resolver prompt template si se solicita
    if prompt_id:
        prompts_dir = ai.get("promptsDirectory", r"C:\NEVEN\prompts")
        tmpl_path   = os.path.join(prompts_dir, f"{prompt_id}.txt")
        if os.path.isfile(tmpl_path):
            try:
                template = open(tmpl_path, "r", encoding="utf-8").read()
                template = template.replace("{{resultado}}", context)
                template = template.replace("{{datos}}", context)
                template = template.replace("{{contexto}}", "")
                if not messages:
                    messages = [{"role": "user", "content": template}]
            except Exception:
                pass

    if not messages:
        raise HTTPException(400, "El campo 'messages' no puede estar vacío")

    # Validar estructura de mensajes
    valid_roles = {"user", "assistant", "system"}
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            raise HTTPException(400, "Cada mensaje debe tener 'role' y 'content'")
        if msg["role"] not in valid_roles:
            raise HTTPException(400, f"Rol inválido '{msg['role']}'")

    # Inyectar system prompt según contexto
    if context:
        sys_content = _build_system_prompt(context)
        sys_msg     = {"role": "system", "content": sys_content}
        messages    = [sys_msg] + [m for m in messages if m.get("role") != "system"]
    else:
        if not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": _FMT_MINIMAL}] + messages

    # Llamar al LLM
    try:
        result = _call_llm(messages, ai)
    except RuntimeError as exc:
        log.error(f"[{session_id}] LLM error: {exc}")
        raise HTTPException(502, str(exc))

    log.info(
        f"[{session_id}] chat ok — {result['tokens_used']} tokens "
        f"({result['model']})"
    )

    return JSONResponse({
        "status":      "ok",
        "reply":       result["reply"],
        "model":       result["model"],
        "tokens_used": result["tokens_used"],
        "session_id":  session_id,
    })

# =============================================================================
# POST /api/ai/context  —  recibir contexto de Excel
# =============================================================================

@app.post("/api/ai/context")
async def ai_context_post(request: Request) -> JSONResponse:
    """
    Recibe contexto desde Excel (rangos de datos y/o resultados).
    Llamado por =NEVEN.IA.Contexto() desde el XLL o por el add-in vía Office.js.

    Body JSON:
        session_id     : str (opcional)
        dataset_text   : str — datos en formato CSV
        results_text   : str (opcional) — resultados del modelo en CSV
        source         : str — "excel_xll" | "excel_officejs" | "studio"
        n_rows         : int
        n_cols         : int
        columns        : [str] — nombres de columnas
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Body JSON inválido")

    session_id   = (body.get("session_id") or
                    request.headers.get("X-Session-Id") or
                    "default")
    dataset_text = body.get("dataset_text", "").strip()
    results_text = body.get("results_text", "").strip()
    source       = body.get("source", "excel")
    n_rows       = body.get("n_rows", 0)
    columns      = body.get("columns", [])

    if not dataset_text and not results_text:
        raise HTTPException(400, "dataset_text o results_text requerido")

    # Construir el texto de contexto enriquecido
    context_parts = ["=== DATOS DE EXCEL ==="]
    if n_rows:
        context_parts.append(f"Filas: {n_rows}")
    if columns:
        context_parts.append(f"Variables: {', '.join(columns)}")
    context_parts.append("")

    if dataset_text:
        context_parts.append("Datos:")
        context_parts.append(dataset_text)

    if results_text:
        context_parts.append("\n=== RESULTADOS DEL ANÁLISIS ===")
        context_parts.append(results_text)

    context_text = "\n".join(context_parts)

    with _context_lock:
        _pending_context[session_id] = {
            "text":      context_text,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source":    source,
            "columns":   columns,
            "n_rows":    n_rows,
        }

    _touch_session(session_id)
    log.info(
        f"[{session_id}] contexto recibido — {len(context_text)} chars "
        f"({source})"
    )

    return JSONResponse({
        "status":     "ok",
        "message":    f"Contexto almacenado ({len(context_text)} chars)",
        "session_id": session_id,
    })

# =============================================================================
# GET /api/ai/context/pending  —  consumir contexto pendiente
# =============================================================================

@app.get("/api/ai/context/pending")
async def ai_context_pending(request: Request) -> JSONResponse:
    """
    Retorna y borra el contexto pendiente de una sesión.
    El contexto se consume al leerlo (patrón one-shot).

    Query params:
        session_id : str (opcional, default "default")
    """
    session_id = (
        request.query_params.get("session_id")
        or request.headers.get("X-Session-Id")
        or "default"
    )

    with _context_lock:
        ctx = _pending_context.pop(session_id, None)

    if ctx:
        _touch_session(session_id)
        return JSONResponse({"status": "ok", "context": ctx})
    return JSONResponse({"status": "empty"})

# =============================================================================
# DELETE /api/ai/context/{session_id}
# =============================================================================

@app.delete("/api/ai/context/{session_id}")
async def ai_context_delete(session_id: str) -> JSONResponse:
    """Limpia el contexto pendiente de una sesión sin consumirlo."""
    with _context_lock:
        removed = _pending_context.pop(session_id, None)
    return JSONResponse({
        "status":  "ok",
        "removed": removed is not None,
    })

# =============================================================================
# GET /api/ai/history/{session_id}
# =============================================================================

@app.get("/api/ai/history/{session_id}")
async def ai_history_get(session_id: str) -> JSONResponse:
    """Retorna el historial de mensajes de una sesión."""
    messages = _chat_history.get(session_id, [])
    return JSONResponse({
        "status":     "ok",
        "session_id": session_id,
        "messages":   messages,
        "count":      len(messages),
    })

# =============================================================================
# DELETE /api/ai/history/{session_id}
# =============================================================================

@app.delete("/api/ai/history/{session_id}")
async def ai_history_delete(session_id: str) -> JSONResponse:
    """Limpia el historial de mensajes de una sesión."""
    with _context_lock:
        count = len(_chat_history.pop(session_id, []))
    return JSONResponse({
        "status":   "ok",
        "deleted":  count,
        "session_id": session_id,
    })

# =============================================================================
# GET /api/ai/sessions  —  para administración / debug
# =============================================================================

@app.get("/api/ai/sessions")
async def ai_sessions() -> JSONResponse:
    """Lista las sesiones activas con metadata básica."""
    now = time.time()
    sessions = []
    for sid, last_t in list(_session_last_active.items()):
        sessions.append({
            "session_id":      sid,
            "idle_seconds":    int(now - last_t),
            "has_context":     sid in _pending_context,
            "history_count":   len(_chat_history.get(sid, [])),
        })
    sessions.sort(key=lambda s: s["idle_seconds"])
    return JSONResponse({
        "status":   "ok",
        "count":    len(sessions),
        "sessions": sessions,
    })

# =============================================================================
# Archivos estáticos del add-in (agent.html + assets)
# =============================================================================

@app.get("/")
async def serve_agent_root() -> FileResponse:
    """Sirve agent.html como raíz del add-in."""
    index = _STATIC_DIR / "agent.html"
    if not index.exists():
        raise HTTPException(404, "agent.html no encontrado en static/")
    return FileResponse(str(index), media_type="text/html")


@app.get("/manifest.xml")
async def serve_manifest() -> FileResponse:
    """Sirve el manifest del add-in."""
    manifest = Path(__file__).parent / "manifest.xml"
    if not manifest.exists():
        raise HTTPException(404, "manifest.xml no encontrado")
    return FileResponse(str(manifest), media_type="application/xml")


# Montar archivos estáticos si el directorio existe
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# =============================================================================
# Punto de entrada
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="NEVEN AI Service — Agente IA como microservicio independiente"
    )
    parser.add_argument("--port",   type=int, default=5556,
                        help="Puerto HTTP (default: 5556)")
    parser.add_argument("--host",   default="127.0.0.1",
                        help="Host (default: 127.0.0.1; usa 0.0.0.0 para acceso en red)")
    parser.add_argument("--config", default=None,
                        help="Ruta a neven-config.json")
    parser.add_argument("--reload", action="store_true",
                        help="Hot reload (solo para desarrollo)")
    args = parser.parse_args()

    log.info(f"Iniciando NEVEN AI Service en http://{args.host}:{args.port}")
    log.info(f"Documentación: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "neven_ai_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
