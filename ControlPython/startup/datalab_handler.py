# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — DataLabHandler
# Maneja GET /api/datalab/catalog y POST /api/datalab/run
# ═══════════════════════════════════════════════════════════════════════════════
import os
import json
import time
import threading
from typing import Any

# Constantes
FUNCTIONS_DIR_DEFAULT = r"C:\NEVEN\functions"
CATALOG_TIMEOUT_MS    = 2000
REQUIRED_SIDECAR_FIELDS = {
    "id", "family", "family_label", "name", "description",
    "languages", "function_name", "file", "variable_roles", "parameters"
}


class DataLabHandler:
    """Maneja los endpoints GET /api/datalab/catalog y POST /api/datalab/run."""

    # ------------------------------------------------------------------
    # handle_catalog
    # ------------------------------------------------------------------
    def handle_catalog(self, config: dict) -> dict:
        """
        Escanea el directorio de funciones, valida cada .json y retorna
        el catálogo agrupado por idioma → familia.

        Args:
            config: Diccionario de configuración del servidor. Se lee la clave
                    "functions_dir" (por defecto FUNCTIONS_DIR_DEFAULT).

        Returns:
            dict con keys: status, catalog, warnings, scan_time_ms
        """
        functions_dir = config.get("functions_dir", FUNCTIONS_DIR_DEFAULT)
        start_ms = time.time() * 1000
        warnings = []
        catalog = {}  # {language: {family: [FunctionCard, ...]}}

        if not os.path.isdir(functions_dir):
            return {
                "status": "ok",
                "catalog": {},
                "warnings": [f"Directorio no encontrado: {functions_dir}"],
                "scan_time_ms": 0,
            }

        json_files = [
            f for f in os.listdir(functions_dir) if f.lower().endswith(".json")
        ]

        for fname in json_files:
            # Verificar timeout
            if (time.time() * 1000 - start_ms) > CATALOG_TIMEOUT_MS:
                warnings.append("Escaneo interrumpido: tiempo límite de 2000ms alcanzado")
                break

            fpath = os.path.join(functions_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    card = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                warnings.append(f"{fname}: JSON inválido — {exc}")
                continue

            # Validar campos obligatorios
            missing = REQUIRED_SIDECAR_FIELDS - set(card.keys())
            if missing:
                warnings.append(f"{fname}: faltan campos obligatorios: {missing}")
                continue

            # Validar parámetros select tienen options con value+label
            for param in card.get("parameters", []):
                if param.get("type") == "select":
                    opts = param.get("options", [])
                    if not opts or not all("value" in o and "label" in o for o in opts):
                        warnings.append(
                            f"{fname}: parámetro '{param.get('name')}' type=select "
                            f"requiere options con 'value' y 'label'"
                        )

            # Verificar que el archivo fuente existe (advertencia, no rechazo)
            file_basename = card.get("file", "")
            source_path = os.path.join(functions_dir, file_basename)
            if file_basename and not os.path.isfile(source_path):
                warnings.append(
                    f"{fname}: archivo fuente '{file_basename}' no encontrado "
                    f"(la función será incluida de todas formas)"
                )

            card["_source_file"] = fpath

            # Agrupar por idioma → familia
            for lang in card.get("languages", []):
                family = card.get("family", "GENERAL")
                catalog.setdefault(lang, {}).setdefault(family, []).append(card)

        scan_time = round(time.time() * 1000 - start_ms)
        return {
            "status": "ok",
            "catalog": catalog,
            "warnings": warnings,
            "scan_time_ms": scan_time,
        }

    # ------------------------------------------------------------------
    # handle_run
    # ------------------------------------------------------------------
    def handle_run(self, body: dict, config: dict,
                   db, db_lock: threading.Lock,
                   get_pipe_client) -> dict:
        """
        Valida el cuerpo, consulta DuckDB, genera código R, lo envía por Named
        Pipe y retorna la lista de slots.

        Args:
            body:            Cuerpo JSON del POST /api/datalab/run.
            config:          Configuración del servidor.
            db:              Conexión DuckDB (_db de neven_http_server.py).
            db_lock:         Lock de DuckDB (_db_lock).
            get_pipe_client: Callable(lang) → PipeClient (NEVENHandler._get_pipe_client).

        Returns:
            dict con keys: status, slots, execution_time_ms  (o status, message, code)
        """
        start_ms = time.time() * 1000

        # ── Caso especial: DS_Wooldridge — cargar dataset directamente sin Named Pipe ──
        function_id_early = body.get("function_id", "").strip()
        if function_id_early == "DS_Wooldridge":
            return self._handle_wooldridge(body, config, db, db_lock)

        # 1. Validar campos obligatorios del body
        function_id   = body.get("function_id", "").strip()
        language      = body.get("language", "r").strip().lower()
        column_roles  = body.get("column_roles", {})
        parameters    = body.get("parameters", {})
        filter_clause = body.get("filter_clause", "").strip()
        functions_dir = config.get("functions_dir", FUNCTIONS_DIR_DEFAULT)

        if not function_id:
            return {"status": "error", "message": "Falta el campo 'function_id'.",
                    "code": "VALIDATION_ERROR"}
        if language not in ("r", "python", "julia"):
            return {"status": "error",
                    "message": f"Idioma '{language}' no soportado. Use 'r', 'python' o 'julia'.",
                    "code": "VALIDATION_ERROR"}

        # ── Caso Python: ejecutar función Python directamente ──────────────────
        if language == "python":
            return self._handle_python_function(
                function_id, column_roles, parameters, filter_clause,
                db, db_lock, functions_dir
            )

        # ── Caso Julia: enviar código Julia por Named Pipe ─────────────────────
        if language == "julia":
            return self._handle_julia_function(
                function_id, column_roles, parameters, filter_clause,
                db, db_lock, functions_dir, get_pipe_client
            )

        # ── Verificación de paquetes (advertencia, sin bloquear) ───────────────
        _pkg_advertencia_slot = None
        try:
            import package_manager_service as _pms  # type: ignore
            if _pms._PKG_SERVICE_AVAILABLE and _pms._pkg_service is not None:
                import concurrent.futures as _cf
                with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                    _fut = _ex.submit(_pms._pkg_service.verificar_funcion, function_id)
                    try:
                        _pkg_check = _fut.result(timeout=3)
                        _faltantes = [p for p in _pkg_check if not p.get("instalado")]
                        if _faltantes:
                            _nombres = ", ".join(p["paquete"] for p in _faltantes)
                            _pkg_advertencia_slot = {
                                "name":  "advertencia_paquetes",
                                "label": "Paquetes faltantes detectados",
                                "type":  "scalar",
                                "value": (f"ADVERTENCIA: Faltan paquetes R requeridos: {_nombres}. "
                                          f"Instalarlos en NEVEN Studio > Data Lab > 'Verificar paquetes' "
                                          f"o con: =NEVEN.R(\"install.packages(c('{_nombres.replace(', ', chr(39)+','+chr(39))}'))\""),
                                "tier":  1,
                            }
                    except _cf.TimeoutError:
                        pass  # Timeout silencioso — no bloquear
        except Exception:
            pass  # PKG service no disponible — continuar sin advertencia

        # 2. Construir la lista de columnas desde column_roles (deduplicada)
        all_columns = []
        for role_key, cols in column_roles.items():
            for col in cols:
                if col not in all_columns:
                    all_columns.append(col)

        # 3. Verificar tabla dataset en DuckDB solo cuando hay columnas requeridas
        if all_columns:
            try:
                with db_lock:
                    db.execute("SELECT COUNT(*) FROM dataset")
            except Exception:
                return {"status": "error",
                        "message": "No hay datos cargados. Cargue un dataset primero.",
                        "code": "NO_DATASET"}

        # 4. Query DuckDB o datos vacíos (funciones sin roles como DS_Wooldridge)
        if not all_columns:
            col_names    = []
            raw_rows     = []
            json_escaped = "[]"
        else:
            quoted_cols = ", ".join(f'"{c}"' for c in all_columns)
            sql = f"SELECT {quoted_cols} FROM dataset"
            if filter_clause:
                sql += f" WHERE {filter_clause}"

            try:
                with db_lock:
                    result = db.execute(sql)
                    col_names = [d[0] for d in result.description]
                    raw_rows  = result.fetchall()
            except Exception as exc:
                err_msg = str(exc)
                # Mensaje amigable para columna no encontrada (usuario cambio de caso sin recargar)
                if "not found in FROM clause" in err_msg or "Binder Error" in err_msg:
                    return {"status": "error",
                            "message": (
                                "El dataset en Data Studio no corresponde al ejemplo seleccionado. "
                                "Ejecute primero sin asignar columnas Y/X para cargar el dataset correcto, "
                                "luego asigne las columnas y ejecute de nuevo."
                            ),
                            "code": "FILTER_ERROR"}
                return {"status": "error",
                        "message": f"Error en filtro DuckDB: {exc}",
                        "code": "FILTER_ERROR"}

            # 5. Serializar datos a JSON para pasarlos a R
            rows_as_dicts = [
                {col: (row[i] if row[i] is not None else None)
                 for i, col in enumerate(col_names)}
                for row in raw_rows
            ]
            json_data = json.dumps(rows_as_dicts, default=str)
            json_escaped = json_data.replace("\\", "\\\\").replace("'", "\\'")

        # 6. Construir el script R — resolver el archivo fuente desde el sidecar
        source_file  = ""
        sidecar_role_order = []  # orden de roles según el sidecar
        try:
            json_files = [f for f in os.listdir(functions_dir) if f.lower().endswith(".json")]
            for fname in json_files:
                fpath = os.path.join(functions_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    card = json.load(f)
                if card.get("id") == function_id:
                    file_basename = card.get("file", "")
                    if file_basename:
                        candidate = os.path.join(functions_dir, file_basename)
                        if os.path.isfile(candidate):
                            source_file = candidate
                    # Capturar orden de roles del sidecar (preserva inserción en JSON)
                    sidecar_role_order = list(card.get("variable_roles", {}).keys())
                    break
        except Exception:
            pass  # No encontrar el archivo es no fatal — R lanzará su propio error

        r_lines = self._build_r_script(
            function_id, column_roles, parameters, json_escaped, col_names,
            functions_dir=functions_dir, source_file=source_file,
            sidecar_role_order=sidecar_role_order
        )

        # 7. Enviar a ControlR
        # Para funciones que retornan datasets grandes (DS_Wooldridge_Benchmark, etc.)
        # usamos un cliente fresco con timeout extendido en lugar del cliente compartido.
        _HEAVY_FUNCTIONS = {"DS_Wooldridge_Benchmark"}
        try:
            if function_id in _HEAVY_FUNCTIONS:
                # Cliente fresco con timeout de 5 minutos para funciones pesadas
                from pipe_client import PipeClient  # type: ignore[import]
                client = PipeClient(r"\\.\pipe\neven_r", timeout_ms=300_000)
                client.connect()
            else:
                client = get_pipe_client("r")
        except KeyError:
            return {"status": "error",
                    "message": "El motor R no está disponible. Verifique que ControlR.exe esté activo.",
                    "code": "ENGINE_UNAVAILABLE"}
        except Exception as exc:
            return {"status": "error",
                    "message": f"No se pudo conectar a ControlR: {exc}",
                    "code": "ENGINE_UNAVAILABLE"}

        try:
            var = client.send_code(r_lines, wait=True)
        except Exception as exc:
            msg = str(exc)
            if "timed out" in msg.lower():
                return {"status": "error",
                        "message": "La ejecución superó el tiempo límite.",
                        "code": "ENGINE_UNAVAILABLE"}
            return {"status": "error",
                    "message": f"Error en ControlR: {msg}",
                    "code": "R_ERROR"}

        # 8. Convertir Variable → lista de slots
        from pipe_client import variable_to_python  # type: ignore
        raw = variable_to_python(var)
        
        slots = self._parse_slots_from_variable(raw)
        
        # Si no hay slots, retornar el raw como diagnostico
        if not slots:
            try:
                import json as _jd
                _dbg = _jd.dumps(raw, default=str)[:2000]
            except Exception:
                _dbg = str(raw)[:2000]
            return {"status": "ok",
                    "slots": [{"name": "debug_raw", "label": "Debug: raw response",
                               "type": "scalar", "value": f"raw={_dbg}", "tier": 1}],
                    "execution_time_ms": 0}

        # 9. Detectar marcador de carga de dataset Wooldridge
        import base64 as _b64, re as _re
        load_slots = [s for s in slots if isinstance(s.get("value"), str)
                      and "<neven-load-dataset" in s.get("value", "")]
        if load_slots:
            try:
                html_val = load_slots[0]["value"]
                m = _re.search(r'name="([^"]+)">(.*?)</neven-load-dataset>', html_val, _re.DOTALL)
                if m:
                    ds_name  = m.group(1)
                    ds_b64   = m.group(2).strip()
                    ds_json  = _b64.b64decode(ds_b64).decode("utf-8")
                    rows_list = json.loads(ds_json)
                    if rows_list:
                        cols_list = list(rows_list[0].keys())
                        types_map = {}
                        for c in cols_list:
                            sample = [r[c] for r in rows_list[:50] if r.get(c) is not None]
                            types_map[c] = "numeric" if sample and all(
                                isinstance(v, (int, float)) for v in sample
                            ) else "text"
                        with db_lock:
                            db.execute("DROP TABLE IF EXISTS dataset")
                            col_defs = ", ".join(
                                f'"{c}" {"DOUBLE" if types_map[c]=="numeric" else "VARCHAR"}'
                                for c in cols_list
                            )
                            db.execute(f"CREATE TABLE dataset ({col_defs})")
                            vals_list = [
                                [row.get(c) for c in cols_list] for row in rows_list
                            ]
                            placeholders = ", ".join(["?"] * len(cols_list))
                            db.executemany(f"INSERT INTO dataset VALUES ({placeholders})", vals_list)

                        confirm_slot = {
                            "name":  "dataset_cargado",
                            "label": f"Dataset '{ds_name}' cargado",
                            "type":  "scalar",
                            "value": (f"\u2713 '{ds_name}' cargado en DuckDB: "
                                      f"{len(rows_list):,} filas \u00d7 {len(cols_list)} columnas. "
                                      f"Columnas: {', '.join(cols_list[:10])}"
                                      f"{'...' if len(cols_list) > 10 else ''}"),
                            "tier":  1,
                        }
                        slots = [confirm_slot if s is load_slots[0] else s for s in slots]
            except Exception as _e:
                slots = [
                    {"name": "error_carga", "label": "Error al cargar dataset",
                     "type": "scalar", "value": f"Error: {_e}", "tier": 1}
                    if s is load_slots[0] else s for s in slots
                ]

        exec_time = round(time.time() * 1000 - start_ms)
        # Inyectar advertencia de paquetes faltantes al inicio si existe
        if _pkg_advertencia_slot and slots:
            slots = [_pkg_advertencia_slot] + slots
        elif _pkg_advertencia_slot:
            slots = [_pkg_advertencia_slot]
        return {"status": "ok", "slots": slots, "execution_time_ms": exec_time}

    # ------------------------------------------------------------------
    # Métodos auxiliares internos
    # ------------------------------------------------------------------
    def _handle_wooldridge(self, body: dict, config: dict,
                            db, db_lock: threading.Lock) -> dict:
        """Carga un dataset Wooldridge directamente en DuckDB via subprocess R."""
        import subprocess, tempfile, csv as _csv
        start_ms = time.time() * 1000

        dataset_name = body.get("parameters", {}).get("Dataset", "wage1")
        if not dataset_name or not str(dataset_name).isidentifier():
            dataset_name = "wage1"
        dataset_name = str(dataset_name)

        # Encontrar Rscript
        r_paths = [
            r"C:\Program Files\R\R-4.4.1\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.4.2\bin\Rscript.exe",
            r"C:\Program Files\R\R-4.4.3\bin\Rscript.exe",
        ]
        rscript = next((p for p in r_paths if os.path.isfile(p)), "Rscript")

        tmp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp_path = tmp_csv.name
        tmp_csv.close()

        r_code = (
            f"library(wooldridge);"
            f"data('{dataset_name}', package='wooldridge');"
            f"df <- get('{dataset_name}');"
            f"df <- as.data.frame(df);"
            f"write.csv(df, '{tmp_path.replace(chr(92), '/')}', row.names=FALSE, na='');"
            f"cat('ROWS:', nrow(df), 'COLS:', ncol(df), 'NAMES:', "
            f"paste(names(df), collapse=','), '\\n')"
        )

        try:
            result = subprocess.run(
                [rscript, "--vanilla", "-e", r_code],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr[:500])

            # Parse output to get dimensions
            import re as _re
            m = _re.search(r"ROWS:\s*(\d+)\s+COLS:\s*(\d+)\s+NAMES:\s*(.+)", result.stdout)
            n_rows  = int(m.group(1)) if m else 0
            n_cols  = int(m.group(2)) if m else 0
            col_names_str = m.group(3).strip() if m else ""
            col_list = [c.strip() for c in col_names_str.split(",") if c.strip()]

            # Load CSV into DuckDB
            with db_lock:
                db.execute("DROP TABLE IF EXISTS dataset")
                db.execute(
                    f"CREATE TABLE dataset AS SELECT * FROM "
                    f"read_csv_auto('{tmp_path.replace(chr(92), '/')}')"
                )
                actual_cols = [d[0] for d in db.execute("DESCRIBE dataset").fetchall()]

        except Exception as e:
            try: os.unlink(tmp_path)
            except Exception: pass
            return {"status": "error",
                    "message": f"Error al cargar dataset '{dataset_name}': {e}",
                    "code": "R_ERROR"}
        finally:
            try: os.unlink(tmp_path)
            except Exception: pass

        # Build preview table (first 20 rows)
        with db_lock:
            preview_rows = db.execute(f"SELECT * FROM dataset LIMIT 20").fetchall()

        preview_table = [dict(zip(actual_cols, row)) for row in preview_rows]

        # Column info
        col_info = [{"Columna": c, "Tipo": "numeric"} for c in actual_cols]

        exec_ms = round(time.time() * 1000 - start_ms)
        confirm_msg = (
            f"DATASET CARGADO EXITOSAMENTE\n\n"
            f"Nombre: {dataset_name}\n"
            f"Filas: {n_rows:,} | Columnas: {n_cols}\n"
            f"Columnas: {', '.join(actual_cols[:15])}"
            f"{'...' if len(actual_cols) > 15 else ''}\n\n"
            f"Puedes ir a Regresion, Analisis de Datos o Series de Tiempo para analizarlo."
        )

        slots = [
            {"name": "dataset_cargado", "label": f"Dataset '{dataset_name}' cargado en DuckDB",
             "type": "scalar", "value": confirm_msg, "tier": 1},
            {"name": "columnas",        "label": "Columnas disponibles",
             "type": "table",  "value": col_info, "tier": 1},
            {"name": "preview",         "label": "Primeras 20 filas",
             "type": "table",  "value": preview_table, "tier": 1},
        ]
        return {"status": "ok", "slots": slots, "execution_time_ms": exec_ms}

    def _handle_python_function(self, function_id: str, column_roles: dict,
                                  parameters: dict, filter_clause: str,
                                  db, db_lock, functions_dir: str) -> dict:
        """
        Ejecuta una función Studio Python directamente en este proceso.

        El archivo `{function_id}.Studio.py` en functions_dir debe definir
        una función `{function_id}_Studio(df, **params) -> list[dict]`
        donde cada dict tiene keys: name, label, type, value, tier.
        """
        import importlib.util, sys as _sys
        start_ms = time.time() * 1000

        # Localizar el archivo .Studio.py
        py_file = os.path.join(functions_dir, f"{function_id}.Studio.py")
        if not os.path.isfile(py_file):
            return {"status": "error",
                    "message": f"Archivo '{function_id}.Studio.py' no encontrado en {functions_dir}",
                    "code": "R_ERROR"}

        # Cargar dinámicamente el módulo
        try:
            spec   = importlib.util.spec_from_file_location(function_id, py_file)
            module = importlib.util.module_from_spec(spec)
            # Añadir functions_dir al path para que el módulo pueda hacer imports relativos
            if functions_dir not in _sys.path:
                _sys.path.insert(0, functions_dir)
            spec.loader.exec_module(module)
        except Exception as e:
            return {"status": "error",
                    "message": f"Error al cargar {function_id}.Studio.py: {e}",
                    "code": "R_ERROR"}

        # Obtener la función Studio
        func_name = f"{function_id}_Studio"
        if not hasattr(module, func_name):
            return {"status": "error",
                    "message": f"La función '{func_name}' no está definida en {function_id}.Studio.py",
                    "code": "R_ERROR"}
        studio_fn = getattr(module, func_name)

        # Obtener datos de DuckDB si hay roles
        all_columns = []
        for role_key, cols in column_roles.items():
            for col in cols:
                if col not in all_columns:
                    all_columns.append(col)

        df_dict = {}  # {roleKey: list[dict]}
        if all_columns:
            try:
                with db_lock:
                    db.execute("SELECT COUNT(*) FROM dataset")
            except Exception:
                return {"status": "error",
                        "message": "No hay datos cargados.",
                        "code": "NO_DATASET"}

            for role_key, cols in column_roles.items():
                if not cols:
                    continue
                quoted = ", ".join(f'"{c}"' for c in cols)
                sql = f"SELECT {quoted} FROM dataset"
                if filter_clause:
                    sql += f" WHERE {filter_clause}"
                try:
                    with db_lock:
                        res      = db.execute(sql)
                        col_names = [d[0] for d in res.description]
                        rows     = res.fetchall()
                    df_dict[role_key] = [dict(zip(col_names, row)) for row in rows]
                except Exception as exc:
                    return {"status": "error",
                            "message": f"Error DuckDB: {exc}",
                            "code": "FILTER_ERROR"}

        # Llamar a la función
        try:
            slots = studio_fn(df_dict, **parameters)
        except Exception as e:
            return {"status": "error",
                    "message": f"Error en {func_name}: {e}",
                    "code": "R_ERROR"}

        exec_ms = round(time.time() * 1000 - start_ms)
        return {"status": "ok", "slots": slots, "execution_time_ms": exec_ms}

    def _handle_julia_function(self, function_id: str, column_roles: dict,
                                parameters: dict, filter_clause: str,
                                db, db_lock, functions_dir: str,
                                get_pipe_client) -> dict:
        """
        Ejecuta una función Studio Julia enviando código al pipe de ControlJulia.

        El archivo `{function_id}.Studio.jl` en functions_dir debe definir una
        función `{function_id}_Studio(df::Dict; kwargs...) -> Vector{Dict}` donde
        cada Dict tiene keys: name, label, type, value, tier.

        Protocolo de comunicación:
        1. Leer datos de DuckDB según column_roles
        2. Serializar como JSON
        3. Construir código Julia que carga el archivo .Studio.jl y lo llama
        4. Enviar por Named Pipe al ControlJulia.exe
        5. Parsear la Variable devuelta como slots
        """
        start_ms = time.time() * 1000

        # Localizar el archivo .Studio.jl
        jl_file = os.path.join(functions_dir, f"{function_id}.Studio.jl")
        if not os.path.isfile(jl_file):
            return {"status": "error",
                    "message": f"Archivo '{function_id}.Studio.jl' no encontrado en {functions_dir}",
                    "code": "ENGINE_UNAVAILABLE"}

        # Obtener datos de DuckDB
        all_columns = []
        for role_key, cols in column_roles.items():
            for col in cols:
                if col not in all_columns:
                    all_columns.append(col)

        data_by_role = {}  # {roleKey: list[dict]}
        if all_columns:
            try:
                with db_lock:
                    db.execute("SELECT COUNT(*) FROM dataset")
            except Exception:
                return {"status": "error",
                        "message": "No hay datos cargados. Cargue un dataset primero.",
                        "code": "NO_DATASET"}

            for role_key, cols in column_roles.items():
                if not cols:
                    continue
                quoted = ", ".join(f'"{c}"' for c in cols)
                sql = f"SELECT {quoted} FROM dataset"
                if filter_clause:
                    sql += f" WHERE {filter_clause}"
                try:
                    with db_lock:
                        res       = db.execute(sql)
                        col_names = [d[0] for d in res.description]
                        rows      = res.fetchall()
                    data_by_role[role_key] = [dict(zip(col_names, row)) for row in rows]
                except Exception as exc:
                    return {"status": "error",
                            "message": f"Error DuckDB: {exc}",
                            "code": "FILTER_ERROR"}

        # Construir código Julia
        jl_path   = jl_file.replace("\\", "/")
        data_json = json.dumps(data_by_role, default=str)
        # Escapar para string Julia: \ → \\ y " → \"
        data_json_esc = data_json.replace("\\", "\\\\").replace('"', '\\"')
        param_json    = json.dumps(parameters, default=str)
        param_json_esc = param_json.replace("\\", "\\\\").replace('"', '\\"')

        jl_lines = [
            f'include("{jl_path}")',
            f'_neven_data  = JSON3.read("""{data_json}""", Dict{{String, Any}})',
            f'_neven_params = JSON3.read("""{param_json}""", Dict{{String, Any}})',
            f'_neven_result = {function_id}_Studio(_neven_data; _neven_params...)',
            f'_neven_result',
        ]

        # Enviar al pipe de Julia
        try:
            client = get_pipe_client("julia")
        except KeyError:
            return {"status": "error",
                    "message": "El motor Julia no está disponible. Verifique que ControlJulia.exe esté activo.",
                    "code": "ENGINE_UNAVAILABLE"}
        except Exception as exc:
            return {"status": "error",
                    "message": f"No se pudo conectar a ControlJulia: {exc}",
                    "code": "ENGINE_UNAVAILABLE"}

        try:
            var = client.send_code(jl_lines, wait=True)
        except Exception as exc:
            msg = str(exc)
            if "timed out" in msg.lower():
                return {"status": "error",
                        "message": "La ejecución Julia superó el tiempo límite.",
                        "code": "ENGINE_UNAVAILABLE"}
            return {"status": "error",
                    "message": f"Error en ControlJulia: {msg}",
                    "code": "R_ERROR"}

        # Parsear Variable → slots (mismo formato que R)
        from pipe_client import variable_to_python  # type: ignore
        raw   = variable_to_python(var)
        slots = self._parse_slots_from_variable(raw)

        # Si no hay slots, retornar el raw como diagnóstico
        if not slots:
            try:
                _dbg = json.dumps(raw, default=str)[:2000]
            except Exception:
                _dbg = str(raw)[:2000]
            return {"status": "ok",
                    "slots": [{"name": "debug_raw", "label": "Debug: Julia raw response",
                               "type": "scalar", "value": f"raw={_dbg}", "tier": 1}],
                    "execution_time_ms": 0}

        exec_ms = round(time.time() * 1000 - start_ms)
        return {"status": "ok", "slots": slots, "execution_time_ms": exec_ms}

    def _build_r_script(self, function_id: str, column_roles: dict,
                        parameters: dict, json_escaped: str,
                        col_names: list, functions_dir: str = FUNCTIONS_DIR_DEFAULT,
                        source_file: str = "", sidecar_role_order: list = None) -> list:
        """Genera las líneas de código R para ejecutar el wrapper.

        Incluye un source() del archivo del wrapper si source_file está
        disponible, para que ControlR cargue la función aunque no esté
        en startup.r.
        """
        lines = []

        # Source del serializador si no está ya cargado
        r_slots_path = os.path.join(os.path.dirname(functions_dir), "startup", "r_object_to_slots.R")
        if not os.path.isfile(r_slots_path):
            # Fallback: ruta estándar de producción
            r_slots_path = r"C:\NEVEN\startup\r_object_to_slots.R"
        r_slots_r = r_slots_path.replace("\\", "/")
        lines.append(f"if (!exists('r_object_to_slots', mode='function')) {{")
        lines.append(f"  source('{r_slots_r}', local=FALSE)")
        lines.append("}")
        lines.append("")

        # Source del wrapper — siempre se recarga para garantizar que
        # cualquier cambio en el archivo .R se refleje sin reiniciar ControlR.
        # Primero eliminamos la definición anterior del globalenv para forzar
        # que source() registre la nueva versión.
        if source_file:
            r_path = source_file.replace("\\", "/")
            lines.append(f"if (exists('{function_id}.Studio', envir=globalenv())) {{")
            lines.append(f"  rm(list='{function_id}.Studio', envir=globalenv())")
            lines.append(f"}}")
            lines.append(f"source('{r_path}', local=FALSE)")
            # Propagar la función recién cargada al environment NEVEN si existe,
            # para que ControlR use la versión nueva y no la cacheada en NEVEN.
            lines.append(f"if (exists('NEVEN', envir=globalenv()) && is.environment(get('NEVEN', envir=globalenv()))) {{")
            lines.append(f"  if (exists('{function_id}.Studio', envir=globalenv())) {{")
            lines.append(f"    assign('{function_id}.Studio', get('{function_id}.Studio', envir=globalenv()), envir=get('NEVEN', envir=globalenv()))")
            lines.append(f"  }}")
            lines.append(f"}}")
            lines.append("")

        lines += [
            f"data_json <- '{json_escaped}'",
            "data <- jsonlite::fromJSON(data_json)",
            "data <- as.data.frame(data)",
            "",
        ]

        # Construir un sub-data.frame por cada rol asignado
        # Convención: rol X → data_X, rol Y → data_Y, rol Z → data_Z, etc.
        # Si solo hay rol X (funciones clásicas), el primer argumento es data_X
        role_var_names = {}  # {roleKey: "data_X"/"data_Y"/...}
        for role_key, cols in column_roles.items():
            if not cols:
                continue
            var_name = f"data_{role_key}"
            role_var_names[role_key] = var_name
            quoted = ", ".join(f'"{c}"' for c in cols)
            lines.append(f'{var_name} <- data[, c({quoted}), drop=FALSE]')

        # Si el rol X no fue asignado pero el sidecar lo declara (requerido o no),
        # generar un índice secuencial 1..N para que la función tenga algo en data_X.
        # Esto aplica a GR_Lineas, GR_Barras, GR_SeriesTiempo y similares.
        if "X" not in role_var_names and sidecar_role_order and "X" in sidecar_role_order:
            # Determinar N desde la primera columna asignada (Y u otro rol)
            if col_names:
                lines.append("data_X <- data.frame(.idx = seq_len(nrow(data)))")
            else:
                lines.append("data_X <- data.frame(.idx = integer(0))")
            role_var_names["X"] = "data_X"

        lines.append("")

        # Construir llamada al wrapper
        # Orden de roles: seguir el orden del sidecar si está disponible.
        # Fallback: Y primero (patrón regresión), luego X, luego el resto.
        positional_args = []
        if sidecar_role_order:
            # Usar el orden exacto del sidecar (respeta X antes de Y en GR, Y antes en RG)
            for rk in sidecar_role_order:
                if rk in role_var_names:
                    positional_args.append(role_var_names[rk])
            # Agregar roles asignados que no estén en el sidecar (por si acaso)
            for rk, var in role_var_names.items():
                if var not in positional_args:
                    positional_args.append(var)
        else:
            # Fallback al orden original: Y, X, resto alfabético
            if "Y" in role_var_names:
                positional_args.append(role_var_names["Y"])
            if "X" in role_var_names:
                positional_args.append(role_var_names["X"])
            for rk in sorted(role_var_names.keys()):
                if rk not in ("Y", "X"):
                    positional_args.append(role_var_names[rk])

        # Construir parámetros nombrados — solo los que el sidecar declara para esta función
        # Esto evita que parámetros de una función anterior contaminen la llamada
        param_strs = []
        if sidecar_role_order is not None:
            # Tenemos el sidecar cargado; filtrar parameters contra los nombres declarados
            # Re-leer el sidecar para obtener la lista de parámetros aceptados
            accepted_params = set()
            try:
                json_files = [f for f in os.listdir(functions_dir) if f.lower().endswith(".json")]
                for fname in json_files:
                    fpath = os.path.join(functions_dir, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        card = json.load(f)
                    if card.get("id") == function_id:
                        for p in card.get("parameters", []):
                            accepted_params.add(p.get("name", ""))
                        break
            except Exception:
                pass  # si falla, enviamos todos (comportamiento previo)

            filtered_params = {k: v for k, v in parameters.items()
                               if not accepted_params or k in accepted_params}
        else:
            filtered_params = parameters

        for k, v in filtered_params.items():
            if isinstance(v, bool):
                param_strs.append(f"{k}={'TRUE' if v else 'FALSE'}")
            elif isinstance(v, str):
                param_strs.append(f"{k}='{v}'")
            else:
                param_strs.append(f"{k}={v}")

        params_r   = ", ".join(param_strs)
        args_r     = ", ".join(positional_args)
        # Build function call: handle case with no positional args (e.g. DS_Wooldridge)
        if args_r:
            func_call = f"result <- {function_id}.Studio({args_r}"
        else:
            func_call = f"result <- {function_id}.Studio("
        if params_r:
            if args_r:
                func_call += f", {params_r}"
            else:
                func_call += params_r
        func_call += ")"
        lines.append(func_call)

        # El wrapper GR ya llama r_object_to_slots() internamente y retorna
        # el data.frame de slots. ControlR devuelve el último valor evaluado.
        # NO llamar r_object_to_slots() de nuevo aquí.
        return lines

    def _parse_slots_from_variable(self, raw: Any) -> list:
        """
        Convierte la representacion Python de una Variable arr en una lista de Slots.

        ControlR serializa el data.frame (N slots x 5 campos) como matriz flatten row-major:
          columns = ["name","label","type","value","tier"]
          rows[i] contiene segmentos de los campos de varios slots intercalados.

        Para N slots y 5 campos, el valor flat[i + j*N] corresponde al campo j del slot i.

        Tambien soporta formato DIRECTO (BoxPlot) donde cada row IS un slot completo (N=1 slot).
        """
        if not isinstance(raw, dict):
            return []
        col_headers = raw.get("columns", [])
        rows        = raw.get("rows", [])
        if not col_headers or not rows:
            return []

        try:
            col_idx = {c.lower(): i for i, c in enumerate(col_headers)}
            has_required = (
                isinstance(col_idx.get("name"), int)
                and isinstance(col_idx.get("type"), int)
            )
            if not has_required:
                return []

            n_fields = len(col_headers)  # = 5 (name,label,type,value,tier)
            first_row = rows[0] if rows else []

            # ── Detectar formato DIRECTO (1 slot, fila completa) ──────────────
            # En formato directo n_rows=1 y row[type_idx] es un tipo conocido.
            KNOWN_TYPES = {"html", "table", "scalar", "vector", "unknown", "plotly",
                           "integer", "numeric", "character"}
            ti = col_idx.get("type", 2)
            vi = col_idx.get("value", 3)

            n_rows = len(rows)
            type_in_row0 = first_row[ti] if isinstance(first_row, list) and ti < len(first_row) else None

            is_direct = (
                n_rows == 1
                and isinstance(first_row, list)
                and len(first_row) == n_fields
                and isinstance(type_in_row0, str)
                and type_in_row0.lower() in KNOWN_TYPES
            )

            if is_direct:
                ni = col_idx.get("name",  0)
                li = col_idx.get("label", 1)
                ri = col_idx.get("tier",  4)
                row = first_row
                slot_type  = row[ti] if ti < len(row) else "scalar"
                slot_value = row[vi] if vi < len(row) else None
                if isinstance(slot_value, str) and slot_type != "html":
                    try: slot_value = json.loads(slot_value)
                    except: pass
                try: tier_int = int(row[ri]) if ri < len(row) else 1
                except: tier_int = 1
                return [{
                    "name":  row[ni] if ni < len(row) else "slot_0",
                    "label": row[li] if li < len(row) else row[ni],
                    "type":  slot_type,
                    "value": slot_value,
                    "tier":  tier_int,
                }]

            # ── Formato FLATTEN (ControlR data.frame N slots x 5 campos) ─────
            # Aplanar todas las rows en un array secuencial.
            flat = []
            for row in rows:
                if isinstance(row, list):
                    flat.extend(row)
                else:
                    flat.append(row)

            total = len(flat)
            if total == 0 or total % n_fields != 0:
                return []

            n_slots = total // n_fields

            fi_name  = col_idx.get("name",  0)
            fi_label = col_idx.get("label", 1)
            fi_type  = col_idx.get("type",  2)
            fi_value = col_idx.get("value", 3)
            fi_tier  = col_idx.get("tier",  4)

            def _get(slot_i, field_j):
                idx = slot_i + field_j * n_slots
                return flat[idx] if idx < len(flat) else None

            def _parse_val(v, stype):
                if not isinstance(v, str): return v
                if stype == "html": return v
                try: return json.loads(v)
                except: return v

            slots = []
            for i in range(n_slots):
                s_name  = _get(i, fi_name)  or f"slot_{i}"
                s_label = _get(i, fi_label) or s_name
                s_type  = _get(i, fi_type)  or "scalar"
                s_value = _get(i, fi_value)
                s_tier  = _get(i, fi_tier)

                if not isinstance(s_type, str):
                    s_type = "scalar"

                s_value = _parse_val(s_value, s_type)
                try: tier_int = int(s_tier)
                except: tier_int = 1

                slots.append({
                    "name":  str(s_name),
                    "label": str(s_label),
                    "type":  str(s_type),
                    "value": s_value,
                    "tier":  tier_int,
                })

            return slots

        except Exception:
            return []
