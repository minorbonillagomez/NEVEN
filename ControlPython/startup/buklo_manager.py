# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN — BukloManager
# Gestor del formato de proyecto .buklo
#
# Un .buklo es un archivo ZIP con extensión propia que empaqueta:
#   data/dataset.parquet     — Dataset activo (comprimido ~10x vs CSV)
#   project/CHAT.md          — Historia de interacciones con el LLM
#   project/plan.json        — Plan metodológico del análisis
#   project/metadata.json    — Versión NEVEN, fecha, perfil del usuario
#   MANIFEST.json            — Versión del formato + checksums
#
# Exportación: DuckDB → Parquet (nativo, sin pyarrow) → ZIP → .buklo
# Importación: .buklo → ZIP → Parquet → DuckDB READ_PARQUET()
# ═══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import threading
import zipfile
from datetime import datetime
from typing import Any

logger = logging.getLogger("neven.buklo")

BUKLO_VERSION   = "1.0"
BUKLO_EXTENSION = ".buklo"

# Archivos dentro del ZIP
_PATH_DATASET      = "data/dataset.parquet"
_PATH_CHAT         = "project/CHAT.md"
_PATH_PLAN         = "project/plan.json"
_PATH_METADATA     = "project/metadata.json"
_PATH_MANIFEST     = "MANIFEST.json"
_PATH_ANALYSIS_LOG = "project/analysis_log.jsonl"


class BukloManager:
    """
    Gestiona la serialización y deserialización del formato .buklo.
    Thread-safe: usa un lock interno para operaciones de I/O.
    """

    def __init__(self):
        self._lock = threading.Lock()

    # ── Guardar proyecto ──────────────────────────────────────────────────────

    def save(self,
             path: str,
             db,
             db_lock: threading.Lock,
             chat_history: str = "",
             plan: dict | None = None,
             metadata: dict | None = None,
             analysis_log: list | None = None,
             report_content: str = "",
             report_format: str = "tex",
             report_pdf_bytes: bytes | None = None) -> dict:
        """
        Exporta el proyecto activo a un archivo .buklo.

        Args:
            path:         Ruta de destino (debe terminar en .buklo).
            db:           Conexión DuckDB activa (_db de neven_http_server).
            db_lock:      Lock de DuckDB.
            chat_history: Contenido Markdown del historial de chat.
            plan:         Plan metodológico como dict (opcional).
            metadata:     Metadatos adicionales del usuario (opcional).

        Returns:
            {"status": "ok", "path": str, "size_kb": float, "n_rows": int,
             "n_cols": int, "has_dataset": bool}
            o {"status": "error", "message": str}
        """
        if not path.endswith(BUKLO_EXTENSION):
            path = path + BUKLO_EXTENSION

        with self._lock:
            tmp_dir = tempfile.mkdtemp(prefix="neven_buklo_")
            try:
                result = self._do_save(
                    path, db, db_lock, tmp_dir,
                    chat_history, plan or {}, metadata or {},
                    analysis_log or [],
                    report_content   = report_content,
                    report_format    = report_format,
                    report_pdf_bytes = report_pdf_bytes,
                )
                return result
            except Exception as exc:
                logger.error(f"[BukloManager] Error al guardar: {exc}")
                return {"status": "error", "message": str(exc)}
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _do_save(self, path, db, db_lock, tmp_dir,
                 chat_history, plan, metadata, analysis_log=None,
                 report_content="", report_format="tex", report_pdf_bytes=None):
        """Implementación interna de save."""

        # ── 1. Exportar dataset a Parquet si existe ───────────────────────────
        parquet_path = os.path.join(tmp_dir, "dataset.parquet")
        n_rows = 0
        n_cols = 0
        has_dataset = False

        try:
            with db_lock:
                count = db.execute("SELECT COUNT(*) FROM dataset").fetchone()[0]
                if count > 0:
                    db.execute(
                        f"COPY dataset TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
                    )
                    cols_info = db.execute("DESCRIBE dataset").fetchall()
                    n_rows = count
                    n_cols = len(cols_info)
                    has_dataset = True
        except Exception as exc:
            # No hay dataset activo — guardar el .buklo igualmente sin datos
            logger.info(f"[BukloManager] Sin dataset activo: {exc}")
            has_dataset = False

        # ── 2. Serializar contenido del proyecto ─────────────────────────────
        now = datetime.utcnow().isoformat() + "Z"

        full_metadata = {
            "neven_version":    "3.0",
            "buklo_version":    BUKLO_VERSION,
            "created_at":       now,
            "n_rows":           n_rows,
            "n_cols":           n_cols,
            "has_dataset":      has_dataset,
            **(metadata or {}),
        }

        plan_json     = json.dumps(plan or {}, ensure_ascii=False, indent=2)
        metadata_json = json.dumps(full_metadata, ensure_ascii=False, indent=2)

        # ── 3. Calcular checksums ─────────────────────────────────────────────
        checksums = {}
        if has_dataset and os.path.isfile(parquet_path):
            checksums[_PATH_DATASET] = _sha256_file(parquet_path)
        checksums[_PATH_CHAT]     = _sha256_str(chat_history)
        checksums[_PATH_PLAN]     = _sha256_str(plan_json)
        checksums[_PATH_METADATA] = _sha256_str(metadata_json)

        manifest = {
            "buklo_version": BUKLO_VERSION,
            "created_at":    now,
            "checksums":     checksums,
        }

        # ── 4. Empaquetar en ZIP ──────────────────────────────────────────────
        tmp_zip = path + ".tmp"
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            # Dataset Parquet (ya comprimido con ZSTD — no comprimir dos veces)
            if has_dataset and os.path.isfile(parquet_path):
                zf.write(parquet_path, _PATH_DATASET,
                         compress_type=zipfile.ZIP_STORED)

            # Archivos de texto
            zf.writestr(_PATH_CHAT,     chat_history.encode("utf-8"))
            zf.writestr(_PATH_PLAN,     plan_json.encode("utf-8"))
            zf.writestr(_PATH_METADATA, metadata_json.encode("utf-8"))
            zf.writestr(_PATH_MANIFEST,
                        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
            # Historial de modelos (JSONL — una línea por modelo, solo metadatos compactos)
            log_lines = []
            for entry in (analysis_log or []):
                compact = {
                    "id":           entry.get("id"),
                    "label":        entry.get("label", ""),
                    "function_id":  entry.get("function_id", ""),
                    "timestamp":    entry.get("timestamp", ""),
                    "source":       entry.get("source", "user"),
                    "context_note": entry.get("context_note", ""),
                    "column_roles": entry.get("column_roles", {}),
                    "n_slots":      len(entry.get("slots", [])),
                    "metrics_text": str(entry.get("metrics_text", ""))[:500],
                }
                log_lines.append(json.dumps(compact, ensure_ascii=False))
            zf.writestr(_PATH_ANALYSIS_LOG,
                        "\n".join(log_lines).encode("utf-8"))
            # Informe analítico (.tex o .qmd) y PDF si existen
            if report_content:
                ext = ".qmd" if report_format == "qmd" else ".tex"
                zf.writestr("project/report" + ext,
                            report_content.encode("utf-8"))
            if report_pdf_bytes:
                zf.writestr("project/report.pdf",
                            report_pdf_bytes)

        # Renombrar al destino final (operación atómica en el mismo volumen)
        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp_zip, path)

        size_kb = round(os.path.getsize(path) / 1024, 1)
        logger.info(
            f"[BukloManager] Guardado: {path} "
            f"({size_kb} KB, {n_rows} filas × {n_cols} cols)"
        )

        return {
            "status":      "ok",
            "path":        path,
            "size_kb":     size_kb,
            "n_rows":      n_rows,
            "n_cols":      n_cols,
            "has_dataset": has_dataset,
        }

    # ── Cargar proyecto ───────────────────────────────────────────────────────

    def load(self,
             path: str,
             db,
             db_lock: threading.Lock) -> dict:
        """
        Abre un archivo .buklo y restaura el estado del proyecto.

        Carga el Parquet en DuckDB (tabla 'dataset') y retorna el
        contenido del CHAT.md, el plan metodológico y los metadatos.

        Returns:
            {"status": "ok", "metadata": dict, "chat_history": str,
             "plan": dict, "n_rows": int, "n_cols": int, "columns": [str]}
            o {"status": "error", "message": str}
        """
        if not os.path.isfile(path):
            return {"status": "error", "message": f"Archivo no encontrado: {path}"}

        with self._lock:
            tmp_dir = tempfile.mkdtemp(prefix="neven_buklo_load_")
            try:
                return self._do_load(path, db, db_lock, tmp_dir)
            except Exception as exc:
                logger.error(f"[BukloManager] Error al cargar: {exc}")
                return {"status": "error", "message": str(exc)}
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _do_load(self, path, db, db_lock, tmp_dir):
        """Implementación interna de load."""

        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()

            # ── Validar que es un .buklo válido ───────────────────────────────
            if _PATH_MANIFEST not in names:
                return {
                    "status": "error",
                    "message": "El archivo no es un .buklo válido (falta MANIFEST.json)"
                }

            manifest = json.loads(zf.read(_PATH_MANIFEST).decode("utf-8"))
            buklo_ver = manifest.get("buklo_version", "?")
            if buklo_ver != BUKLO_VERSION:
                logger.warning(
                    f"[BukloManager] Versión del formato: {buklo_ver} "
                    f"(actual: {BUKLO_VERSION}) — intentando cargar de todas formas"
                )

            # ── Leer archivos de texto ────────────────────────────────────────
            chat_history = ""
            if _PATH_CHAT in names:
                chat_history = zf.read(_PATH_CHAT).decode("utf-8")

            plan = {}
            if _PATH_PLAN in names:
                try:
                    plan = json.loads(zf.read(_PATH_PLAN).decode("utf-8"))
                except Exception:
                    plan = {}

            metadata = {}
            if _PATH_METADATA in names:
                try:
                    metadata = json.loads(zf.read(_PATH_METADATA).decode("utf-8"))
                except Exception:
                    metadata = {}

            # ── Leer historial de modelos ─────────────────────────────────────
            analysis_log = []
            if _PATH_ANALYSIS_LOG in names:
                try:
                    log_text = zf.read(_PATH_ANALYSIS_LOG).decode("utf-8")
                    for line in log_text.strip().split("\n"):
                        line = line.strip()
                        if line:
                            analysis_log.append(json.loads(line))
                except Exception as exc:
                    logger.warning(f"[BukloManager] Error leyendo analysis_log: {exc}")

            # ── Cargar dataset Parquet en DuckDB ──────────────────────────────
            n_rows = 0
            n_cols = 0
            columns = []
            has_dataset = False

            if _PATH_DATASET in names:
                parquet_path = os.path.join(tmp_dir, "dataset.parquet")
                with open(parquet_path, "wb") as f:
                    f.write(zf.read(_PATH_DATASET))

                try:
                    with db_lock:
                        db.execute("DROP TABLE IF EXISTS dataset")
                        db.execute(
                            f"CREATE TABLE dataset AS "
                            f"SELECT * FROM read_parquet('{parquet_path}')"
                        )
                        n_rows = db.execute(
                            "SELECT COUNT(*) FROM dataset"
                        ).fetchone()[0]
                        cols_info = db.execute("DESCRIBE dataset").fetchall()
                        n_cols   = len(cols_info)
                        columns  = [row[0] for row in cols_info]
                    has_dataset = True
                    logger.info(
                        f"[BukloManager] Dataset cargado: "
                        f"{n_rows} filas × {n_cols} cols"
                    )
                except Exception as exc:
                    logger.error(
                        f"[BukloManager] Error al cargar Parquet: {exc}"
                    )

        return {
            "status":        "ok",
            "metadata":      metadata,
            "chat_history":  chat_history,
            "plan":          plan,
            "n_rows":        n_rows,
            "n_cols":        n_cols,
            "columns":       columns,
            "has_dataset":   has_dataset,
            "analysis_log":  analysis_log,
        }

    # ── Estado del proyecto ───────────────────────────────────────────────────

    def status(self, path: str | None = None) -> dict:
        """
        Retorna el estado del proyecto actual.

        Args:
            path: Ruta del último .buklo guardado/cargado (opcional).

        Returns:
            {"has_saved_project": bool, "path": str|None,
             "last_saved": str|None, "size_kb": float|None}
        """
        if not path or not os.path.isfile(path):
            return {
                "has_saved_project": False,
                "path": None,
                "last_saved": None,
                "size_kb": None,
            }

        stat = os.stat(path)
        return {
            "has_saved_project": True,
            "path":        path,
            "last_saved":  datetime.utcfromtimestamp(
                stat.st_mtime
            ).isoformat() + "Z",
            "size_kb":     round(stat.st_size / 1024, 1),
        }

    # ── Listar .buklo en un directorio ────────────────────────────────────────

    def list_projects(self, directory: str) -> list[dict]:
        """
        Lista todos los archivos .buklo en un directorio.

        Returns:
            Lista de {"name", "path", "size_kb", "last_saved"}
        """
        if not os.path.isdir(directory):
            return []
        result = []
        for fname in sorted(os.listdir(directory)):
            if fname.lower().endswith(BUKLO_EXTENSION):
                fpath = os.path.join(directory, fname)
                stat  = os.stat(fpath)
                result.append({
                    "name":       fname,
                    "path":       fpath,
                    "size_kb":    round(stat.st_size / 1024, 1),
                    "last_saved": datetime.utcfromtimestamp(
                        stat.st_mtime
                    ).isoformat() + "Z",
                })
        return result


# ── Helpers privados ──────────────────────────────────────────────────────────

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]  # 16 chars suficiente para verificación


def _sha256_str(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ── Singleton global ──────────────────────────────────────────────────────────

_buklo_instance: BukloManager | None = None
_buklo_current_path: str | None = None   # último .buklo guardado/cargado


def get_buklo_manager() -> BukloManager:
    """Retorna la instancia singleton del BukloManager."""
    global _buklo_instance
    if _buklo_instance is None:
        _buklo_instance = BukloManager()
    return _buklo_instance


def set_current_path(path: str | None) -> None:
    global _buklo_current_path
    _buklo_current_path = path


def get_current_path() -> str | None:
    return _buklo_current_path
