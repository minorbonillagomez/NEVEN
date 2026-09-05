# =============================================================================
# NEVEN — catalog_loader.py
# Carga dinámica del catálogo de funciones de C:\NEVEN\functions\
# =============================================================================
#
# Lee los archivos *.json de functions/ + functions_catalog.json base
# y construye el catálogo completo en memoria para el agente IA.
#
# El catálogo se usa en _build_system_prompt() para que el agente conozca
# TODAS las funciones disponibles y pueda sugerir la más apropiada.
# =============================================================================

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("neven.catalog")

# Ruta de producción
_FUNCTIONS_DIR = Path(r"C:\NEVEN\functions")
_BASE_CATALOG  = Path(__file__).parent / "functions_catalog.json"

# Cache en memoria — se recarga si el directorio cambia
_catalog_cache: dict | None = None
_catalog_mtime: float = 0.0


def _load_base_catalog() -> dict:
    """Carga el catálogo base desde functions_catalog.json."""
    if _BASE_CATALOG.exists():
        try:
            with open(_BASE_CATALOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"No se pudo leer {_BASE_CATALOG}: {e}")
    return {"functions": [], "families": {}, "libraries_inventory": {}}


def _load_sidecar_functions(functions_dir: Path) -> list[dict]:
    """Lee todos los *.json de functions/ como entradas adicionales del catálogo."""
    extras = []
    if not functions_dir.exists():
        return extras

    for json_file in sorted(functions_dir.glob("*.json")):
        # Saltar archivos que no son sidecars de funciones
        if json_file.name.startswith("_") or json_file.name == "DS_Wooldridge_Benchmark.json":
            pass  # incluir igualmente

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Solo incluir si tiene la estructura mínima de sidecar
            if not data.get("id") or not data.get("name"):
                continue

            # Construir entrada normalizada
            entry = {
                "function_id":   data.get("id"),
                "family":        data.get("family", "UC"),
                "name":          data.get("name", ""),
                "description":   data.get("description", ""),
                "languages":     data.get("languages", ["r"]),
                "studio_file":   data.get("file", ""),
                "wikipedia_url": data.get("wikipedia_url", ""),
                "column_roles":  {
                    role: meta.get("label", role)
                    for role, meta in data.get("variable_roles", {}).items()
                },
                "parameters": {
                    p["name"]: f"{p.get('label','')}, default: {p.get('default','?')}"
                    for p in data.get("parameters", [])
                    if "name" in p
                },
                "_source": "sidecar",
            }
            extras.append(entry)

        except Exception as e:
            log.debug(f"Sidecar {json_file.name} ignorado: {e}")

    return extras


def load_catalog(force_reload: bool = False) -> dict:
    """
    Retorna el catálogo completo en memoria.
    Se recarga automáticamente si los archivos de functions/ cambiaron.
    """
    global _catalog_cache, _catalog_mtime

    # Verificar si el directorio cambió
    current_mtime = 0.0
    if _FUNCTIONS_DIR.exists():
        current_mtime = max(
            (p.stat().st_mtime for p in _FUNCTIONS_DIR.glob("*.json")),
            default=0.0
        )

    if not force_reload and _catalog_cache is not None and current_mtime <= _catalog_mtime:
        return _catalog_cache

    # Cargar catálogo base
    base = _load_base_catalog()

    # Cargar sidecars dinámicos
    sidecar_entries = _load_sidecar_functions(_FUNCTIONS_DIR)

    # IDs ya en el catálogo base (para no duplicar)
    base_ids = {f["function_id"] for f in base.get("functions", [])}

    # Agregar solo los que no están en el catálogo base
    new_entries = [e for e in sidecar_entries if e["function_id"] not in base_ids]

    combined_functions = base.get("functions", []) + new_entries

    _catalog_cache = {
        "families":           base.get("families", {}),
        "functions":          combined_functions,
        "libraries_inventory": base.get("libraries_inventory", {}),
        "_total":             len(combined_functions),
        "_from_base":         len(base.get("functions", [])),
        "_from_sidecars":     len(new_entries),
    }
    _catalog_mtime = current_mtime

    log.info(
        f"Catálogo cargado: {_catalog_cache['_total']} funciones "
        f"({_catalog_cache['_from_base']} base + {_catalog_cache['_from_sidecars']} sidecars)"
    )
    return _catalog_cache


def build_catalog_prompt_section() -> str:
    """
    Genera el texto del catálogo para inyectar en el system prompt del agente.
    Formato compacto para no saturar el contexto del LLM.
    """
    cat = load_catalog()
    families = cat.get("families", {})
    functions = cat.get("functions", [])

    if not functions:
        return ""

    # Agrupar por familia
    by_family: dict[str, list] = {}
    for fn in functions:
        fam = fn.get("family", "UC")
        by_family.setdefault(fam, []).append(fn)

    lines = [
        "## Funciones NEVEN disponibles",
        "",
        "Usa SIEMPRE uno de estos function_id en bloques neven-run.",
        "Prefiere funciones existentes antes de proponer código nuevo.",
        "",
    ]

    for fam_code, fns in sorted(by_family.items()):
        fam_label = families.get(fam_code, fam_code)
        lines.append(f"### {fam_code} — {fam_label}")
        for fn in fns:
            fid   = fn.get("function_id", "?")
            name  = fn.get("name", "")
            desc  = fn.get("description", "")[:120]
            xll   = fn.get("xll_example", "")
            roles = fn.get("column_roles", {})
            roles_str = ", ".join(f"{k}={v[:40]}" for k, v in list(roles.items())[:4])

            line = f"- **{fid}** — {name}"
            if desc:
                line += f": {desc}"
            if xll:
                line += f"  _(XLL: `{xll}`)_"
            if roles_str:
                line += f"  Roles: [{roles_str}]"

            # Alternativas ontológicas
            alts = fn.get("alternativas_ontologicas", {})
            if alts:
                alt_str = "; ".join(f"{k} → {v}" for k, v in list(alts.items())[:3])
                line += f"  Alternativas: [{alt_str}]"

            lines.append(line)
        lines.append("")

    # Árbol de decisión
    lines += [
        "## Árbol de decisión para sugerencias",
        "",
        "1. ¿El problema se resuelve con una función Studio existente? → `neven-run` con function_id exacto",
        "2. ¿O con una función XLL con TipoOutput diferente? → indica `=R.FUNCION(rangos, TipoOutput=N)` con rangos reales",
        "3. ¿La librería tiene la funcionalidad pero no está expuesta? → propone nuevo wrapper `.Studio.R` + `.json` siguiendo el protocolo NEVEN",
        "4. ¿Requiere librería nueva? → `neven-install` + nuevo wrapper",
        "",
        "Cuando sugieras una fórmula Excel, usa las columnas reales del contexto. Ejemplo:",
        "`=NEVEN.r(\"MR_Lineal\", lwage, educ+exper+tenure, TipoOutput=7)`",
        "",
    ]

    return "\n".join(lines)


def get_function_by_id(function_id: str) -> dict | None:
    """Retorna la entrada completa de una función por su ID."""
    cat = load_catalog()
    for fn in cat.get("functions", []):
        if fn.get("function_id") == function_id:
            return fn
    return None


def get_alternatives(function_id: str) -> dict:
    """Retorna las alternativas ontológicas de una función."""
    fn = get_function_by_id(function_id)
    if fn:
        return fn.get("alternativas_ontologicas", {})
    return {}


def get_libraries_for_function(function_id: str) -> list[str]:
    """Retorna las librerías requeridas por una función."""
    fn = get_function_by_id(function_id)
    if fn:
        return fn.get("libraries_required", [])
    return []
