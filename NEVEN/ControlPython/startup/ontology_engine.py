# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Ontology Engine
# Motor de razonamiento sobre el Knowledge Graph econométrico.
#
# Lee memory/ontology/graph.jsonl en memoria al iniciar.
# Construye índices por ID, tipo y relación para consultas O(1).
# Expone métodos de alto nivel al resto del sistema:
#   - get_method_node(function_id)
#   - get_assumptions(method_id)
#   - get_concepts(method_id)
#   - get_r_functions(method_id)
#   - suggest_from_profile(profile)
#   - build_diagnostic_plan(method_id, profile)
#   - build_pedagogy_warning(assumption_id, context)
#
# No modifica el grafo. Solo lectura.
# ═══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("neven.ontology")

# ── Rutas candidatas para el grafo (en orden de prioridad) ────────────────────
_GRAPH_PATH_CANDIDATES = [
    # 1. Configurable en neven-config.json > OntologyPath
    None,  # placeholder, se resuelve en __init__
    # 2. Path del repositorio de desarrollo
    r"F:\ANTIGRAVITY\2026\NEVEN\ONTOLOGIA\LIBROS\memory\ontology\graph.jsonl",
    # 3. Path de producción (tras deploy)
    r"C:\NEVEN\ontology\graph.jsonl",
]

# ── Tipos de nodo reconocidos ──────────────────────────────────────────────────
_VALID_TYPES = {"Framework", "Method", "Concept", "Assumption",
                "RPackage", "RFunction", "Dataset"}

# ── Relaciones reconocidas ─────────────────────────────────────────────────────
_VALID_RELATIONS = {
    "requires", "adjusts_for", "produces_bias_if_adjusted",
    "evaluates", "alternative_to", "implemented_in_r_package",
    "uses_r_function", "uses_dataset", "part_of",
}


class OntologyEngine:
    """
    Motor de conocimiento sobre el Knowledge Graph econométrico de NEVEN.

    Se instancia una sola vez al arrancar el servidor HTTP.
    Todas las operaciones de consulta son de solo lectura y thread-safe
    (el estado interno es inmutable después de __init__).
    """

    def __init__(self, graph_path: str | None = None,
                 function_map_path: str | None = None):
        """
        Carga el grafo JSONL y construye los índices internos.

        Args:
            graph_path: Ruta explícita a graph.jsonl. Si es None, se prueba
                        _GRAPH_PATH_CANDIDATES en orden.
            function_map_path: Ruta al kg_function_map.json. Si es None,
                               se busca junto a este archivo .py.
        """
        self._loaded = False
        self._nodes_by_id:    dict[str, dict]         = {}
        self._nodes_by_type:  dict[str, list[dict]]   = {}
        self._edges_from:     dict[str, list[tuple]]  = {}   # id → [(rel, target_id)]
        self._edges_to:       dict[str, list[tuple]]  = {}   # id → [(rel, source_id)]
        self._function_map:   dict[str, str]          = {}   # function_id → method_id
        self._n_nodes  = 0
        self._n_edges  = 0
        self._graph_path_used = ""

        # ── Resolver path del grafo ───────────────────────────────────────────
        resolved_path = self._resolve_graph_path(graph_path)
        if not resolved_path:
            logger.warning(
                "[OntologyEngine] graph.jsonl no encontrado en ninguna ruta candidata. "
                "El motor estará disponible pero vacío."
            )
            return

        # ── Cargar y parsear ──────────────────────────────────────────────────
        try:
            self._load_graph(resolved_path)
        except Exception as exc:
            logger.error(f"[OntologyEngine] Error al cargar grafo: {exc}")
            return

        # ── Cargar mapeo function_id → method_id ─────────────────────────────
        map_path = function_map_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "kg_function_map.json"
        )
        self._load_function_map(map_path)

        self._loaded = True
        logger.info(
            f"[OntologyEngine] Cargado: {self._n_nodes} nodos, "
            f"{self._n_edges} aristas, "
            f"{len(self._function_map)} mapeos de funciones. "
            f"Ruta: {self._graph_path_used}"
        )

    # ── Propiedades públicas ──────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        """True si el grafo se cargó correctamente."""
        return self._loaded

    @property
    def stats(self) -> dict:
        """Estadísticas del grafo cargado."""
        return {
            "loaded": self._loaded,
            "n_nodes": self._n_nodes,
            "n_edges": self._n_edges,
            "n_function_mappings": len(self._function_map),
            "graph_path": self._graph_path_used,
            "types": {t: len(nodes) for t, nodes in self._nodes_by_type.items()},
        }

    # ── API pública ───────────────────────────────────────────────────────────

    def get_method_node(self, function_id: str) -> dict | None:
        """
        Dado un function_id del catálogo DataLab (ej: 'RG_OLS'),
        retorna el nodo Method correspondiente del grafo.

        Estrategia de búsqueda:
        1. Mapeo explícito en kg_function_map.json
        2. Búsqueda por nombre normalizado entre nodos Method

        Returns:
            dict con todas las propiedades del nodo, o None si no se encuentra.
        """
        if not self._loaded:
            return None

        # 1. Mapeo explícito
        method_id = self._function_map.get(function_id)
        if method_id and method_id in self._nodes_by_id:
            return self._nodes_by_id[method_id]

        # 2. Búsqueda por nombre normalizado (fallback)
        normalized = function_id.lower().replace("rg_", "").replace("_", "")
        for node in self._nodes_by_type.get("Method", []):
            node_name = node.get("properties", {}).get("name", "").lower()
            node_name_norm = node_name.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if normalized in node_name_norm:
                return node

        return None

    def get_node(self, node_id: str) -> dict | None:
        """Retorna un nodo por su ID exacto."""
        return self._nodes_by_id.get(node_id)

    def get_nodes_by_type(self, node_type: str) -> list[dict]:
        """Retorna todos los nodos de un tipo dado."""
        return self._nodes_by_type.get(node_type, [])

    def get_related_nodes(self, node_id: str, relation: str,
                          direction: str = "from") -> list[dict]:
        """
        Retorna todos los nodos relacionados desde/hacia node_id via 'relation'.

        Args:
            node_id:   ID del nodo origen.
            relation:  Tipo de relación (ej: 'requires', 'uses_r_function').
            direction: 'from' (salientes) o 'to' (entrantes).

        Returns:
            Lista de nodos completos (dicts con id, type, properties).
        """
        if not self._loaded:
            return []

        if direction == "from":
            edges = self._edges_from.get(node_id, [])
            return [
                self._nodes_by_id[target_id]
                for rel, target_id in edges
                if rel == relation and target_id in self._nodes_by_id
            ]
        else:
            edges = self._edges_to.get(node_id, [])
            return [
                self._nodes_by_id[source_id]
                for rel, source_id in edges
                if rel == relation and source_id in self._nodes_by_id
            ]

    def get_assumptions(self, method_id: str) -> list[dict]:
        """
        Retorna todos los nodos Assumption que el método requiere.
        Relaciones consideradas: 'requires'.
        """
        if not self._loaded:
            return []
        return [
            n for n in self.get_related_nodes(method_id, "requires")
            if n.get("type") == "Assumption"
        ]

    def get_concepts(self, method_id: str) -> list[dict]:
        """
        Retorna nodos Concept vinculados al método.
        Relaciones consideradas: 'requires', 'adjusts_for'.
        """
        if not self._loaded:
            return []
        concepts = set()
        result = []
        for rel in ("requires", "adjusts_for"):
            for n in self.get_related_nodes(method_id, rel):
                if n.get("type") == "Concept" and n["id"] not in concepts:
                    concepts.add(n["id"])
                    result.append(n)
        return result

    def get_r_functions(self, method_id: str) -> list[dict]:
        """
        Retorna nodos RFunction vinculados al método.
        Relación: 'uses_r_function'.
        """
        return [
            n for n in self.get_related_nodes(method_id, "uses_r_function")
            if n.get("type") == "RFunction"
        ]

    def get_r_packages(self, method_id: str) -> list[dict]:
        """
        Retorna nodos RPackage vinculados al método directamente
        o a través de sus funciones R.
        """
        if not self._loaded:
            return []
        packages = {}

        # Paquetes directos del método
        for n in self.get_related_nodes(method_id, "implemented_in_r_package"):
            if n.get("type") == "RPackage":
                packages[n["id"]] = n

        # Paquetes de las funciones R del método
        for fn in self.get_r_functions(method_id):
            for pkg in self.get_related_nodes(fn["id"], "implemented_in_r_package"):
                if pkg.get("type") == "RPackage":
                    packages[pkg["id"]] = pkg

        return list(packages.values())

    def get_datasets(self, method_id: str) -> list[dict]:
        """Retorna los datasets de demostración del método."""
        return [
            n for n in self.get_related_nodes(method_id, "uses_dataset")
            if n.get("type") == "Dataset"
        ]

    def get_alternatives(self, method_id: str) -> list[dict]:
        """Retorna métodos alternativos (relación 'alternative_to', bidireccional)."""
        if not self._loaded:
            return []
        alts = {}
        for n in self.get_related_nodes(method_id, "alternative_to", "from"):
            if n.get("type") == "Method":
                alts[n["id"]] = n
        for n in self.get_related_nodes(method_id, "alternative_to", "to"):
            if n.get("type") == "Method":
                alts[n["id"]] = n
        return list(alts.values())

    def suggest_from_profile(self, profile: dict) -> list[dict]:
        """
        Dado un perfil de dataset, sugiere métodos aplicables.

        profile = {
            "n_rows": int,
            "has_time_dimension": bool,
            "has_panel_structure": bool,
            "has_spatial_dimension": bool,
            "outcome_type": "continuous" | "binary" | "count" | "ordered",
            "has_endogeneity_concern": bool,
        }

        Returns:
            Lista de nodos Method ordenados por relevancia (score desc).
        """
        if not self._loaded:
            return []

        scored: list[tuple[int, dict]] = []

        for method in self._nodes_by_type.get("Method", []):
            score = self._score_method_for_profile(method, profile)
            if score > 0:
                scored.append((score, method))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:10]]

    def build_diagnostic_plan(self, method_id: str, profile: dict) -> dict:
        """
        Construye el plan metodológico antes de ejecutar un análisis.

        Returns:
            {
                "method": {id, name, description, r_syntax, reference},
                "rationale": str,
                "assumptions": [{id, name, definition, reference}],
                "steps": [{step, action, r_function, package, threshold}],
                "warnings": [],      # se llenan en tiempo de ejecución
                "references": [{book, chapter, pages}],
                "r_functions": [{name, package, r_syntax}],
                "alternatives": [{id, name}],
            }
        """
        if not self._loaded:
            return {"status": "unavailable"}

        method = self._nodes_by_id.get(method_id)
        if not method:
            return {"status": "not_found", "method_id": method_id}

        props = method.get("properties", {})
        ref   = props.get("reference", {})

        assumptions = self.get_assumptions(method_id)
        r_functions = self.get_r_functions(method_id)
        packages    = self.get_r_packages(method_id)
        alternatives = self.get_alternatives(method_id)

        # Construir pasos de diagnóstico a partir de las funciones de evaluación
        steps = self._build_steps(method_id, assumptions, r_functions)

        # Construir racional narrativo
        rationale = self._build_rationale(props, profile)

        # Consolidar referencias únicas
        references = self._collect_references(method, assumptions, r_functions)

        return {
            "status":       "ok",
            "method": {
                "id":                  method_id,
                "name":                props.get("name", method_id),
                "description":         props.get("description", ""),
                "r_syntax":            props.get("r_syntax", ""),
                "interpretation_guide": props.get("interpretation_guide", ""),
                "reference":           ref,
            },
            "rationale":    rationale,
            "assumptions":  [self._serialize_assumption(a) for a in assumptions],
            "steps":        steps,
            "warnings":     [],
            "references":   references,
            "r_functions":  [self._serialize_r_function(f) for f in r_functions],
            "r_packages":   [p.get("properties", {}).get("name", "") for p in packages],
            "alternatives": [
                {"id": a["id"], "name": a.get("properties", {}).get("name", a["id"])}
                for a in alternatives
            ],
        }

    def build_pedagogy_warning(self, assumption_id: str,
                                context: dict) -> dict:
        """
        Construye una advertencia pedagógica completa de 5 capas
        para un supuesto violado o en tensión.

        Args:
            assumption_id: ID del nodo Assumption (ej: 'assumption_homoscedasticity')
            context: {
                "test_statistic": float,
                "p_value": float,
                "threshold": float,
                "variable_name": str,
                "correction_applied": str,  # ej: "HC1"
            }

        Returns:
            {
                "compact": str,
                "phenomenon": str,
                "implication": str,
                "action": str,
                "reference": {text, book, chapter, pages},
                "reflection_question": str,
            }
        """
        if not self._loaded:
            return {"compact": "Advertencia metodológica (ontología no disponible)"}

        node = self._nodes_by_id.get(assumption_id)
        if not node:
            return {"compact": f"Supuesto '{assumption_id}' no encontrado en la ontología"}

        props = node.get("properties", {})
        name  = props.get("name", assumption_id)
        defn  = props.get("definition", "")
        ref   = props.get("reference", {})

        # Extraer contexto del test
        p_val      = context.get("p_value")
        stat       = context.get("test_statistic")
        threshold  = context.get("threshold", 0.05)
        var_name   = context.get("variable_name", "los residuos")
        correction = context.get("correction_applied", "")

        # ── Nivel compacto ────────────────────────────────────────────────────
        compact = self._build_compact_warning(
            assumption_id, name, p_val, stat, threshold, correction, ref
        )

        # ── Fenómeno ─────────────────────────────────────────────────────────
        phenomenon = self._build_phenomenon(
            assumption_id, defn, p_val, stat, var_name
        )

        # ── Implicación ───────────────────────────────────────────────────────
        implication = self._build_implication(assumption_id, p_val)

        # ── Acción ────────────────────────────────────────────────────────────
        action = self._build_action(assumption_id, correction)

        # ── Referencia ────────────────────────────────────────────────────────
        ref_text = self._build_reference_text(assumption_id, ref)

        # ── Pregunta de reflexión ─────────────────────────────────────────────
        reflection = self._build_reflection(assumption_id, var_name)

        return {
            "compact":             compact,
            "phenomenon":          phenomenon,
            "implication":         implication,
            "action":              action,
            "reference": {
                "text":    ref_text,
                "book":    ref.get("book", ""),
                "chapter": ref.get("chapter", ""),
                "pages":   ref.get("pages", ""),
            },
            "reflection_question": reflection,
        }

    def serialize_for_api(self, node: dict) -> dict:
        """
        Serializa un nodo para enviarlo como JSON en la API REST.
        Aplana 'properties' al nivel raíz para facilitar el consumo en JS.
        """
        if not node:
            return {}
        result = {
            "id":   node.get("id", ""),
            "type": node.get("type", ""),
        }
        result.update(node.get("properties", {}))
        return result

    # ── Internals: carga ──────────────────────────────────────────────────────

    def _resolve_graph_path(self, explicit_path: str | None) -> str | None:
        """Retorna la primera ruta candidata que existe."""
        candidates = []
        if explicit_path:
            candidates.append(explicit_path)

        # Config externa (neven-config.json) — se inyecta en __init__ si se pasa
        for c in _GRAPH_PATH_CANDIDATES[1:]:
            candidates.append(c)

        for path in candidates:
            if path and os.path.isfile(path):
                return path
        return None

    def _load_graph(self, path: str) -> None:
        """Carga graph.jsonl y construye todos los índices internos."""
        self._graph_path_used = path

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        n_nodes = 0
        n_edges = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                op = json.loads(line)
            except json.JSONDecodeError:
                continue

            op_type = op.get("op")

            if op_type == "create":
                entity = op.get("entity", {})
                node_id   = entity.get("id", "")
                node_type = entity.get("type", "")

                if not node_id or node_type not in _VALID_TYPES:
                    continue

                # Normalizar: aplanar properties si las tiene, o construir desde campos directos
                props = entity.get("properties", {})
                if not props:
                    # Algunos nodos del update tienen la info directamente en entity
                    props = {k: v for k, v in entity.items()
                             if k not in ("id", "type", "properties")}

                node = {
                    "id":         node_id,
                    "type":       node_type,
                    "properties": props,
                }

                # Índice por ID (última definición gana — permite parches)
                self._nodes_by_id[node_id] = node

                # Índice por tipo
                self._nodes_by_type.setdefault(node_type, [])
                # Evitar duplicados en el índice por tipo
                existing_ids = {n["id"] for n in self._nodes_by_type[node_type]}
                if node_id not in existing_ids:
                    self._nodes_by_type[node_type].append(node)
                else:
                    # Actualizar en lugar de duplicar
                    self._nodes_by_type[node_type] = [
                        node if n["id"] == node_id else n
                        for n in self._nodes_by_type[node_type]
                    ]

                n_nodes += 1

            elif op_type == "relate":
                from_id  = op.get("from", "")
                to_id    = op.get("to", "")
                relation = op.get("rel", "")

                if not from_id or not to_id or relation not in _VALID_RELATIONS:
                    continue

                self._edges_from.setdefault(from_id, []).append((relation, to_id))
                self._edges_to.setdefault(to_id, []).append((relation, from_id))
                n_edges += 1

        self._n_nodes = len(self._nodes_by_id)
        self._n_edges = n_edges

    def _load_function_map(self, path: str) -> None:
        """Carga el mapeo function_id → method_id desde JSON.
        
        Ignora claves que empiezan con '_' (comentarios y metadatos).
        Solo incluye entradas cuyo valor es un string no vacío (method_id real).
        """
        if not os.path.isfile(path):
            logger.warning(f"[OntologyEngine] kg_function_map.json no encontrado: {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Filtrar: solo pares donde clave no empieza con '_' y valor es string no nulo
            self._function_map = {
                k: v
                for k, v in raw.items()
                if not k.startswith("_") and isinstance(v, str) and v
            }
            logger.debug(
                f"[OntologyEngine] {len(self._function_map)} mapeos cargados "
                f"(de {len(raw)} entradas en el archivo)."
            )
        except Exception as exc:
            logger.warning(f"[OntologyEngine] Error cargando function map: {exc}")

    # ── Internals: plan metodológico ──────────────────────────────────────────

    def _build_rationale(self, method_props: dict, profile: dict) -> str:
        """Genera el texto narrativo del racional metodológico."""
        name = method_props.get("name", "este método")
        desc = method_props.get("description", "")

        n_rows = profile.get("n_rows", 0)
        has_panel = profile.get("has_panel_structure", False)
        has_time  = profile.get("has_time_dimension", False)

        lines = []

        # Primera oración: qué hace el método
        if desc:
            # Tomar la primera oración de la descripción
            first_sentence = desc.split(".")[0] + "."
            lines.append(first_sentence)

        # Segunda oración: por qué aplica a estos datos
        if has_panel:
            lines.append(
                f"Tu dataset tiene estructura de panel (entidades × tiempo), "
                f"lo que hace a {name.split('(')[0].strip()} especialmente relevante "
                f"para controlar heterogeneidad no observada."
            )
        elif has_time:
            lines.append(
                f"Tu dataset tiene dimensión temporal, lo que requiere "
                f"considerar la posible autocorrelación serial en los errores."
            )

        if n_rows > 0:
            if n_rows < 50:
                lines.append(
                    f"Con solo {n_rows} observaciones, los tests diagnósticos "
                    f"tienen poca potencia. Interprete los resultados con cautela."
                )
            elif n_rows >= 1000:
                lines.append(
                    f"Con {n_rows:,} observaciones, los tests diagnósticos "
                    f"tienen alta potencia y pueden rechazar H₀ incluso con "
                    f"violaciones prácticas menores."
                )

        return " ".join(lines) if lines else f"Método seleccionado: {name}."

    def _build_steps(self, method_id: str, assumptions: list[dict],
                     r_functions: list[dict]) -> list[dict]:
        """
        Construye la secuencia de pasos diagnósticos del método.
        Cada paso corresponde a verificar un supuesto con su función R.
        """
        # Mapeo supuesto → función de evaluación preferida
        _ASSUMPTION_TEST_MAP = {
            "assumption_homoscedasticity":      ("bptest()", "lmtest"),
            "assumption_no_multicollinearity":  ("vif()", "car"),
            "assumption_strict_exogeneity":     ("phtest()", "plm"),
            "assumption_instrument_relevance":  ("summary(first_stage)$fstatistic", "stats"),
            "assumption_exclusion_restriction": (None, None),  # No hay test formal
            "assumption_parallel_trends":       (None, None),  # Verificación gráfica
            "assumption_positivity":            ("summary(propensity_model)", "stats"),
            "assumption_ignorability":          (None, None),  # No hay test formal
            "assumption_sutva":                 (None, None),  # Verificación teórica
            "assumption_unit_root_absence":     ("adf.test()", "tseries"),
            "assumption_monotonicity":          (None, None),  # Verificación teórica
            "assumption_neyman_orthogonality":  (None, None),  # Verificación teórica
        }

        steps = []
        step_num = 1

        for assumption in assumptions:
            aid = assumption.get("id", "")
            aname = assumption.get("properties", {}).get("name", aid)

            test_fn, test_pkg = _ASSUMPTION_TEST_MAP.get(aid, (None, None))

            step = {
                "step":        step_num,
                "action":      f"Verificar: {aname}",
                "assumption_id": aid,
                "r_function":  test_fn,
                "package":     test_pkg,
                "threshold":   self._get_threshold_text(aid),
                "has_formal_test": test_fn is not None,
            }
            steps.append(step)
            step_num += 1

        # Paso final: estimación del modelo
        main_r_syntax = ""
        if r_functions:
            main_r_syntax = r_functions[0].get("properties", {}).get("r_syntax", "")

        steps.append({
            "step":        step_num,
            "action":      "Estimación del modelo",
            "assumption_id": None,
            "r_function":  main_r_syntax,
            "package":     None,
            "threshold":   None,
            "has_formal_test": False,
        })

        return steps

    def _collect_references(self, method: dict, assumptions: list[dict],
                            r_functions: list[dict]) -> list[dict]:
        """Consolida referencias bibliográficas únicas."""
        seen = set()
        refs = []

        def _add(ref: dict):
            key = (ref.get("book", ""), ref.get("chapter", ""))
            if key[0] and key not in seen:
                seen.add(key)
                refs.append(ref)

        _add(method.get("properties", {}).get("reference", {}))
        for a in assumptions:
            _add(a.get("properties", {}).get("reference", {}))
        for f in r_functions:
            _add(f.get("properties", {}).get("reference", {}))

        return refs

    def _serialize_assumption(self, node: dict) -> dict:
        props = node.get("properties", {})
        return {
            "id":         node.get("id", ""),
            "name":       props.get("name", ""),
            "definition": props.get("definition", ""),
            "reference":  props.get("reference", {}),
        }

    def _serialize_r_function(self, node: dict) -> dict:
        props = node.get("properties", {})
        return {
            "id":                  node.get("id", ""),
            "name":                props.get("name", ""),
            "package":             props.get("package", ""),
            "description":         props.get("description", ""),
            "r_syntax":            props.get("r_syntax", ""),
            "interpretation_guide": props.get("interpretation_guide", ""),
            "cran_url": (
                f"https://cran.r-project.org/web/packages/{props.get('package', '')}"
                f"/{props.get('package', '')}.pdf"
                if props.get("package") else ""
            ),
        }

    def _get_threshold_text(self, assumption_id: str) -> str | None:
        """Retorna el umbral convencional de decisión para un supuesto."""
        _THRESHOLDS = {
            "assumption_homoscedasticity":     "p-valor > 0.05 (no rechazar homocedasticidad)",
            "assumption_no_multicollinearity": "VIF < 5 (sin colinealidad severa)",
            "assumption_unit_root_absence":    "p-valor < 0.05 en ADF (rechazar raíz unitaria)",
            "assumption_instrument_relevance": "F de primer estadio > 10",
        }
        return _THRESHOLDS.get(assumption_id)

    # ── Internals: advertencias pedagógicas ───────────────────────────────────

    def _build_compact_warning(self, assumption_id: str, name: str,
                                p_val: float | None, stat: float | None,
                                threshold: float, correction: str,
                                ref: dict) -> str:
        """Construye el texto compacto de la advertencia."""
        ref_text = ""
        book = ref.get("book", "")
        chapter = ref.get("chapter", "")
        if book and chapter:
            # Extraer nombre corto del libro: primer apellido del autor entre paréntesis
            # "Introduction to Econometrics with R (Hanck et al.)" → "Hanck"
            import re as _re
            match = _re.search(r'\(([^)]+)\)', book)
            if match:
                short_book = match.group(1).split()[0]  # primer token dentro de ()
            else:
                short_book = book.split()[0]
            # Extraer capítulo corto: "Chapter 5: ..." → "Cap. 5"
            chap_match = _re.search(r'[Cc]hapter\s+(\d+)', chapter)
            chap_short = f"Cap. {chap_match.group(1)}" if chap_match else chapter.split(":")[0]
            ref_text = f" · Ver {short_book} {chap_short}"

        stat_text = ""
        if p_val is not None:
            stat_text = f" (p={p_val:.4f})"
        elif stat is not None:
            stat_text = f" (F={stat:.2f})"

        correction_text = f" — corregido con {correction}" if correction else ""

        # Mapeo supuesto → texto compacto
        _COMPACT = {
            "assumption_homoscedasticity":
                f"⚠ Heterocedasticidad detectada{stat_text}{correction_text}{ref_text}",
            "assumption_no_multicollinearity":
                f"⚠ Multicolinealidad elevada detectada{stat_text}{ref_text}",
            "assumption_instrument_relevance":
                f"⚠ Instrumento potencialmente débil{stat_text}{ref_text}",
            "assumption_exclusion_restriction":
                f"⚠ Verifique la restricción de exclusión del instrumento{ref_text}",
            "assumption_parallel_trends":
                f"ℹ Verifique visualmente el supuesto de tendencias paralelas{ref_text}",
            "assumption_unit_root_absence":
                f"⚠ Posible raíz unitaria detectada{stat_text}{ref_text}",
            "assumption_strict_exogeneity":
                f"ℹ Verifique la exogeneidad estricta (test de Hausman recomendado){ref_text}",
            "assumption_positivity":
                f"⚠ Posible violación de positividad en puntuaciones de propensión{ref_text}",
        }

        return _COMPACT.get(
            assumption_id,
            f"⚠ Supuesto en tensión: {name}{stat_text}{ref_text}"
        )

    def _build_phenomenon(self, assumption_id: str, definition: str,
                           p_val: float | None, stat: float | None,
                           var_name: str) -> str:
        """Descripción del fenómeno en lenguaje accesible."""
        _PHENOMENA = {
            "assumption_homoscedasticity": (
                f"El test de Breusch-Pagan detectó que la varianza de {var_name} "
                f"no es constante a lo largo del rango de los regresores. "
                f"Esto se llama heterocedasticidad: algunos valores predichos "
                f"tienen residuos sistemáticamente más grandes que otros."
            ),
            "assumption_no_multicollinearity": (
                f"Dos o más variables explicativas están fuertemente correlacionadas "
                f"entre sí en tu dataset. Esto no viola los supuestos de Gauss-Markov "
                f"directamente, pero infla la varianza de los estimadores."
            ),
            "assumption_instrument_relevance": (
                f"El estadístico F de la primera etapa {('es {:.2f}'.format(stat) if stat else '')} "
                f"está cerca o por debajo del umbral convencional de 10. "
                f"Un instrumento débil genera un segundo estadio con sesgo similar al de MCO."
            ),
            "assumption_unit_root_absence": (
                f"La prueba ADF no rechaza la hipótesis de raíz unitaria en la serie. "
                f"Esto indica que la serie puede ser integrada de orden 1 — I(1) — "
                f"es decir, que sus shocks pasados tienen efecto permanente en el nivel."
            ),
            "assumption_parallel_trends": (
                "El supuesto de tendencias paralelas no puede verificarse formalmente "
                "con datos post-intervención, pero puede evaluarse indirectamente "
                "comparando las tendencias pre-tratamiento entre grupos."
            ),
        }

        text = _PHENOMENA.get(assumption_id, "")
        if not text and definition:
            # Fallback: usar los primeros 200 caracteres de la definición del grafo
            text = definition[:200] + ("..." if len(definition) > 200 else "")
        return text

    def _build_implication(self, assumption_id: str,
                            p_val: float | None) -> str:
        """Por qué importa para el análisis del usuario."""
        _IMPLICATIONS = {
            "assumption_homoscedasticity": (
                "Esto no sesga los coeficientes estimados — OLS sigue siendo consistente. "
                "Sin embargo, los errores estándar clásicos están mal calculados, "
                "lo que puede llevar a declarar como significativas relaciones que no lo son, "
                "o viceversa. La inferencia estadística (p-valores, intervalos de confianza) "
                "es incorrecta sin corrección."
            ),
            "assumption_no_multicollinearity": (
                "Los coeficientes individuales pierden precisión: sus errores estándar se "
                "inflan y los t-valores caen. El modelo en su conjunto (F-global, R²) puede "
                "ser excelente mientras que ningún coeficiente individual resulta significativo. "
                "Esto no es una contradicción — es un síntoma de la colinealidad."
            ),
            "assumption_instrument_relevance": (
                "Con instrumentos débiles, el estimador 2SLS puede ser más sesgado que MCO "
                "en muestras finitas, y los intervalos de confianza convencionales no tienen "
                "cobertura nominal. El problema se agrava cuando hay múltiples instrumentos."
            ),
            "assumption_unit_root_absence": (
                "Regresar una serie I(1) sobre otra I(1) sin verificar cointegración produce "
                "regresión espuria: R² alto y coeficientes aparentemente significativos que "
                "no reflejan ninguna relación real entre las variables."
            ),
        }
        return _IMPLICATIONS.get(
            assumption_id,
            "Esta condición puede afectar la validez de la inferencia estadística."
        )

    def _build_action(self, assumption_id: str, correction: str) -> str:
        """Lo que NEVEN hará (o hizo) en respuesta."""
        _ACTIONS = {
            "assumption_homoscedasticity": (
                f"Se calcularán errores estándar robustos a heterocedasticidad "
                f"({'tipo ' + correction if correction else 'tipo HC1, White 1980'}). "
                f"Los coeficientes no cambian — solo su precisión estimada. "
                f"Se usa `coeftest(modelo, vcov = vcovHC(modelo, type = 'HC1'))` "
                f"del paquete `lmtest` + `sandwich`."
            ),
            "assumption_no_multicollinearity": (
                "NEVEN reportará los VIF de cada variable. "
                "Si algún VIF supera 10, considera eliminar una de las variables "
                "correlacionadas o usar una transformación (centrado, ridge, PCA)."
            ),
            "assumption_instrument_relevance": (
                "Se reporta el estadístico F de la primera etapa. "
                "Si F < 10, considera buscar instrumentos adicionales o usar "
                "LIML en lugar de 2SLS, que tiene mejor comportamiento con instrumentos débiles."
            ),
            "assumption_unit_root_absence": (
                "Se recomienda diferenciar la serie (d=1) antes de modelar, "
                "o verificar si existe cointegración con otras series I(1) del dataset. "
                "NEVEN ejecutará ARIMA con d≥1 automáticamente si se confirma la raíz unitaria."
            ),
        }
        return _ACTIONS.get(
            assumption_id,
            "NEVEN aplicará la corrección estándar documentada en la literatura."
            + (f" Corrección aplicada: {correction}." if correction else "")
        )

    def _build_reference_text(self, assumption_id: str, ref: dict) -> str:
        """Frase que hace la referencia apetecible para el usuario."""
        _REF_TEXTS = {
            "assumption_homoscedasticity": (
                "La explicación más clara de por qué los errores estándar clásicos fallan "
                "con heterocedasticidad y cómo funciona la corrección de White:"
            ),
            "assumption_no_multicollinearity": (
                "La derivación de cómo VIF se relaciona con la varianza del estimador, "
                "y cuándo la multicolinealidad es realmente un problema práctico:"
            ),
            "assumption_instrument_relevance": (
                "El criterio F > 10 tiene una justificación asintótica precisa. "
                "Aquí está la derivación del sesgo de segundo orden de 2SLS con instrumentos débiles:"
            ),
            "assumption_unit_root_absence": (
                "Por qué la regresión espuria ocurre y cómo la prueba ADF detecta "
                "la no estacionariedad antes de que los resultados sean engañosos:"
            ),
            "assumption_parallel_trends": (
                "El supuesto más importante — y más difícil de defender — en DiD. "
                "Cómo evaluarlo y qué alternativas existen cuando no se sostiene:"
            ),
        }
        base = _REF_TEXTS.get(assumption_id, "Referencia canónica:")
        book    = ref.get("book", "")
        chapter = ref.get("chapter", "")
        pages   = ref.get("pages", "")
        if book:
            return f"{base} {book}, {chapter}, {pages}."
        return base

    def _build_reflection(self, assumption_id: str, var_name: str) -> str:
        """Pregunta de reflexión que invita al usuario a pensar."""
        _REFLECTIONS = {
            "assumption_homoscedasticity": (
                f"¿Tiene sentido económico o teórico que la varianza de {var_name} "
                f"varíe con el nivel de las variables explicativas? "
                f"Si la respuesta es sí, la heterocedasticidad es esperada y la corrección es la opción correcta."
            ),
            "assumption_no_multicollinearity": (
                "¿Estas variables miden conceptos realmente distintos, "
                "o están capturando esencialmente el mismo fenómeno subyacente? "
                "Si son casi sinónimas, puede ser más informativo usar solo una."
            ),
            "assumption_instrument_relevance": (
                "¿Por qué este instrumento debería afectar la variable endógena? "
                "¿Hay una historia causal clara que lo justifique, "
                "más allá de la correlación estadística observada?"
            ),
            "assumption_unit_root_absence": (
                "¿Esperarías que un shock en esta serie (una crisis, una política pública) "
                "tuviera efectos permanentes o transitorios? "
                "Si son permanentes, la serie probablemente es I(1)."
            ),
            "assumption_parallel_trends": (
                "¿Hay razones para creer que el grupo tratado y el control "
                "habrían evolucionado de forma similar en ausencia de la intervención? "
                "Verifica si las tendencias pre-tratamiento son paralelas en tus datos."
            ),
        }
        return _REFLECTIONS.get(assumption_id, "")

    # ── Internals: scoring para suggest_from_profile ─────────────────────────

    def _score_method_for_profile(self, method: dict, profile: dict) -> int:
        """
        Asigna un score de relevancia a un método dado el perfil del dataset.
        Score > 0 significa que el método es candidato.
        """
        method_id = method.get("id", "")
        score = 0

        has_time    = profile.get("has_time_dimension", False)
        has_panel   = profile.get("has_panel_structure", False)
        has_spatial = profile.get("has_spatial_dimension", False)
        outcome     = profile.get("outcome_type", "continuous")
        n_rows      = profile.get("n_rows", 0)
        endogeneity = profile.get("has_endogeneity_concern", False)

        # Métodos de series de tiempo
        if has_time and not has_panel:
            if method_id in ("method_arima", "method_garch", "method_var",
                              "method_svar_identification", "method_vecm_johansen"):
                score += 10

        # Métodos de panel
        if has_panel:
            if method_id in ("method_fixed_effects", "method_random_effects",
                              "method_dynamic_panel"):
                score += 10
            if method_id == "method_did":
                score += 8

        # Métodos espaciales
        if has_spatial:
            if method_id in ("method_sar", "method_sem", "method_sdm"):
                score += 10

        # Métodos por tipo de resultado
        if outcome == "binary":
            if method_id in ("method_logit", "method_probit"):
                score += 10
            if method_id == "method_heckman":
                score += 5
        elif outcome == "count":
            if method_id == "method_poisson":
                score += 10
        elif outcome == "ordered":
            if method_id == "method_ordinal_logit":
                score += 10
        elif outcome == "continuous":
            if method_id == "method_ols":
                score += 8
            if method_id in ("method_quantile_regression", "method_tobit"):
                score += 5

        # Endogeneidad
        if endogeneity:
            if method_id in ("method_iv", "method_double_ml", "method_post_lasso"):
                score += 10

        # Penalización por tamaño de muestra insuficiente
        if n_rows > 0:
            if n_rows < 30 and method_id in ("method_double_ml", "method_vecm_johansen"):
                score -= 5

        return max(score, 0)


# ── Singleton global ──────────────────────────────────────────────────────────

_engine_instance: OntologyEngine | None = None


def get_engine(graph_path: str | None = None,
               function_map_path: str | None = None) -> OntologyEngine:
    """
    Retorna la instancia singleton del OntologyEngine.
    Se crea en la primera llamada y se reutiliza en las siguientes.

    Args:
        graph_path: Solo se usa en la primera llamada (inicialización).
        function_map_path: Solo se usa en la primera llamada.
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = OntologyEngine(
            graph_path=graph_path,
            function_map_path=function_map_path,
        )
    return _engine_instance


def reset_engine() -> None:
    """Resetea el singleton. Útil para tests."""
    global _engine_instance
    _engine_instance = None
