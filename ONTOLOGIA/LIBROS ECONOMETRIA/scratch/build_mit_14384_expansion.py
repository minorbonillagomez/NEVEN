import json
import yaml
from collections import Counter

# Load schema
with open('memory/ontology/schema.yaml', 'r', encoding='utf-8') as f:
    schema = yaml.safe_load(f)

# Load existing graph
nodes = {}
edges = []

with open('memory/ontology/graph.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get('op') == 'create':
            nodes[d['entity']['id']] = d['entity']
        elif d.get('op') == 'relate':
            edges.append(d)

print(f"Loaded existing graph: {len(nodes)} entities, {len(edges)} relations.")

# New MIT 14.384 entities
new_entities = [
    {
        "id": "framework_graduate_time_series",
        "type": "Framework",
        "properties": {
            "name": "Graduate Time Series Analysis & Macroeconometrics (MIT 14.384 - Mikusheva)",
            "description": "Marco avanzado de series de tiempo de posgrado enfocado en la identificación estructural en VARs (SVAR), contrastes multivariados de cointegración (VECM Johansen), modelos de estado-espacio con filtro de Kalman y modelos de factores dinámicos.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Syllabus & Lecture Notes 1-26",
                "pages": "Lectures 1-26"
            }
        }
    },
    {
        "id": "dataset_us_macro_sw",
        "type": "Dataset",
        "properties": {
            "name": "USMacro (Stock & Watson 2002)",
            "package": "urca",
            "description": "Panel macroeconómico trimestral de EE.UU. (1953-2001, N=196) con variables de PIB real, inflación del IPC, tasa de interés de la Fed y tasa de desempleo para análisis de cointegración y VAR monetario.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 10 & 18: SVAR & Cointegration in US Macro Data",
                "pages": "pp. 1-25"
            },
            "variables": "gdp_growth (crecimiento PIB), cpi_infl (inflación), fed_funds (tasa de fondos federales), unemp (desempleo)",
            "target": "gdp_growth"
        }
    },
    {
        "id": "dataset_oil_shocks",
        "type": "Dataset",
        "properties": {
            "name": "OilShocks (Kilian 2009)",
            "package": "AER",
            "description": "Serie mensual global (1973-2007) para descomponer shocks estructurales en la oferta de petróleo, actividad económica global y demanda especulativa de inventarios.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 12: Structural Shocks and SVAR Identification",
                "pages": "pp. 1-30 (Kilian AER 2009)"
            },
            "variables": "d_prod (variación de producción de crudo), rea (índice de actividad económica real global de fletes marítimos), rpo (precio real del petróleo)",
            "target": "rpo"
        }
    },
    {
        "id": "dataset_monetary_shocks",
        "type": "Dataset",
        "properties": {
            "name": "MonetarySurprises (Gertler & Karadi 2015)",
            "package": "AER",
            "description": "Serie de sorpresas de política monetaria en ventanas de 30 minutos alrededor de anuncios del FOMC (1990-2012) utilizadas como instrumento exógeno en Proxy-SVAR.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 13: External Instruments in SVAR (Proxy-SVAR)",
                "pages": "pp. 1-22 (Gertler & Karadi AEJ 2015)"
            },
            "variables": "ff4_hf (sorpresa de futuros de fondos federales a 4 meses), gs1 (tasa del bono del tesoro a 1 año), ebp (excess bond premium)",
            "target": "gs1"
        }
    },
    {
        "id": "method_svar_identification",
        "type": "Method",
        "properties": {
            "name": "Structural VAR Identification (Sims / Blanchard-Quah / Uhlig)",
            "description": "Método de identificación econométrica que mapea las innovaciones reducidas de un VAR a shocks económicos ortogonales mediante esquemas triangulares contemporáneos de Cholesky (Sims), restricciones de neutralidad de largo plazo (Blanchard-Quah) o restricciones de signos.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 10-13: Structural VARs and Identification",
                "pages": "pp. 1-45"
            },
            "r_syntax": "SVAR(x = var_model, estmethod = 'direct', Amat = A_mat, Bmat = B_mat)",
            "dataset": "dataset_oil_shocks",
            "interpretation_guide": "Permite aislar el efecto causal dinámico de un shock puro de política monetaria o de oferta agregada sin contaminación de respuestas endógenas simultáneas."
        }
    },
    {
        "id": "method_vecm_johansen",
        "type": "Method",
        "properties": {
            "name": "Vector Error Correction Model (VECM) & Johansen MLE",
            "description": "Modelo dinámico para sistemas de variables integradas I(1) cointegradas, que descompone la matriz de impacto Delta Y_t = alpha beta' Y_t-1 + sum Gamma_i Delta Y_t-i + u_t, donde beta contiene los vectores de cointegración y alpha las velocidades de ajuste al equilibrio.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 18 & 19: Cointegration and Vector Error Correction",
                "pages": "pp. 1-35 (Johansen Econometrica 1991)"
            },
            "r_syntax": "ca.jo(x = ts_matrix, type = 'trace', ecdet = 'const', K = 2)",
            "dataset": "dataset_us_macro_sw",
            "interpretation_guide": "El rango de cointegración r determina cuántas relaciones estables de largo plazo existen; los coeficientes de alpha negativos y significativos confirman convergencia correctora de error."
        }
    },
    {
        "id": "method_kalman_filter",
        "type": "Method",
        "properties": {
            "name": "State-Space Representation & Kalman Filter (KFAS)",
            "description": "Algoritmo recursivo exacto de predicción y actualización que estima la trayectoria óptima de variables de estado latentes no observables (ej. PIB potencial, inflación tendencial o expectativas) gobernadas por ecuaciones de medida y transición estocásticas.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 21 & 22: State-Space Models and Kalman Filter",
                "pages": "pp. 1-30"
            },
            "r_syntax": "kfs_res <- KFS(SSModel(y ~ SSMtrend(1, Q = NA) + SSMcycle(period = 20, Q = NA), H = NA))",
            "dataset": "dataset_us_macro_sw",
            "interpretation_guide": "Calcula la log-verosimilitud exacta mediante la descomposición del error de predicción y obtiene estimaciones filtradas y suavizadas del ciclo económico en tiempo real."
        }
    },
    {
        "id": "method_factor_models_ts",
        "type": "Method",
        "properties": {
            "name": "Dynamic Factor Models (Stock & Watson / Bai & Ng)",
            "description": "Marco de reducción de dimensión para macroeconomía de alta dimensión donde cientos de series temporales se descomponen en una combinación lineal de pocos factores comunes latentes f_t y componentes idiosincráticos e_it.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 14 & 15: Large Factor Models and PCA",
                "pages": "pp. 1-28 (Stock & Watson JBES 2002)"
            },
            "r_syntax": "prcomp(macro_matrix, scale. = TRUE)",
            "dataset": "dataset_growth",
            "interpretation_guide": "Los factores estimados sintetizan las condiciones macroeconómicas generales y mejoran radicalmente el pronóstico de inflación y actividad económica."
        }
    },
    {
        "id": "concept_structural_shock",
        "type": "Concept",
        "properties": {
            "name": "Shocks Estructurales Macroeconómicos (Structural Shocks)",
            "definition": "Innovaciones primitivas no anticipadas, independientes y ortogonales eps_t ~ (0, I) que tienen una interpretación económica causal directa (ej. shock tecnológico, shock de preferencia o sorpresa monetaria).",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 10: SVAR Fundamentals",
                "pages": "pp. 3-15"
            },
            "interpretation_guide": "A diferencia de los residuos reducidos u_t (correlacionados contemporáneamente), los shocks estructurales permiten análisis contrafáctico."
        }
    },
    {
        "id": "concept_irf_fevd",
        "type": "Concept",
        "properties": {
            "name": "Funciones de Impulso-Respuesta (IRF) y FEVD",
            "definition": "Herramientas de análisis dinámico en VARs: la IRF traza la trayectoria temporal de una variable ante un choque de una desviación estándar en un shock estructural; la FEVD cuantifica el porcentaje de varianza del error de predicción atribuible a cada shock a diferentes horizontes h.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 11: Dynamic Multipliers and FEVD",
                "pages": "pp. 5-22"
            },
            "interpretation_guide": "Permite evaluar la persistencia de las perturbaciones y qué choques dominan la volatilidad del ciclo económico en el corto versus largo plazo."
        }
    },
    {
        "id": "concept_johansen_cointegration",
        "type": "Concept",
        "properties": {
            "name": "Rango de Cointegración de Johansen (Cointegrating Rank)",
            "definition": "Propiedad matricial en sistemas VECM donde el rango r de la matriz Pi = alpha beta' determina el número de combinaciones lineales estacionarias independientes entre variables I(1).",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 18: Multivariate Cointegration Theory",
                "pages": "pp. 8-25"
            },
            "interpretation_guide": "Si r = 0, el modelo se estima en primeras diferencias (VAR clásico); si r = K, las variables son estacionarias en niveles; si 0 < r < K, existe equilibrio de largo plazo VECM."
        }
    },
    {
        "id": "concept_state_space_kalman",
        "type": "Concept",
        "properties": {
            "name": "Representación Estado-Espacio (State-Space Representation)",
            "definition": "Estructura probabilística compuesta por una Ecuación de Medida y_t = Z alpha_t + d_t + eps_t y una Ecuación de Transición alpha_t = T alpha_t-1 + c_t + R eta_t, que describe la evolución de variables latentes alpha_t.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 21: State-Space Formulation",
                "pages": "pp. 1-18"
            },
            "interpretation_guide": "Estructura matemática universal para modelos DSGE, componentes no observados de tendencia-ciclo y filtros predictivos."
        }
    },
    {
        "id": "concept_wold_decomposition",
        "type": "Concept",
        "properties": {
            "name": "Teorema de Descomposición de Wold",
            "definition": "Teorema fundamental que establece que todo proceso estocástico estacionario en covarianza puede descomponerse de forma única en la suma de un proceso lineal MA(infinito) de innovaciones ortogonales y un componente puramente determinístico predecible.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 1: Stationarity & Wold Theorem",
                "pages": "pp. 4-18"
            },
            "interpretation_guide": "Justifica teóricamente la aproximación de cualquier serie temporal estacionaria mediante modelos autorregresivos VAR o ARMA."
        }
    },
    {
        "id": "assumption_svar_orthogonality",
        "type": "Assumption",
        "properties": {
            "name": "Ortogonalidad Contemporánea de Shocks Estructurales",
            "definition": "Supuesto de que los shocks estructurales son mutuamente incorrelados y presentan matriz de varianzas-covarianzas diagonal o normalizada a la identidad: E[eps_t eps_t'] = I_K.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 10: SVAR Orthogonality Assumption",
                "pages": "pp. 6-16"
            }
        }
    },
    {
        "id": "assumption_cointegrating_rank",
        "type": "Assumption",
        "properties": {
            "name": "Condición de Rango de Cointegración VECM",
            "definition": "Supuesto de que la matriz de impacto Pi tiene rango reducido 0 < r < K, garantizando la existencia de r relaciones de equilibrio cointegradas.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 18: Cointegrating Rank Conditions",
                "pages": "pp. 10-22"
            }
        }
    },
    {
        "id": "rpkg_urca",
        "type": "RPackage",
        "properties": {
            "name": "urca",
            "purpose": "Unit Root and Cointegration Analysis: Paquete estándar de R para tests de Johansen (ca.jo), Dickey-Fuller aumentado (ur.df) y Phillips-Perron (ur.pp).",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "R Lab: Cointegration in R with urca",
                "pages": "pp. 1-20"
            }
        }
    },
    {
        "id": "rpkg_kfas",
        "type": "RPackage",
        "properties": {
            "name": "KFAS",
            "purpose": "Kalman Filter and Smoother for Exponential Family State Space Models: Filtrado y suavizado rápido de modelos estado-espacio lineales y no gaussianos.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "R Lab: State-Space Modeling in R",
                "pages": "pp. 1-25"
            }
        }
    },
    {
        "id": "rpkg_svars",
        "type": "RPackage",
        "properties": {
            "name": "svars",
            "purpose": "Data-Driven Structural Vector Autoregressions: Identificación de SVAR mediante restricciones de signos, heterocedasticidad y análisis de componentes independientes.",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "R Lab: Advanced SVAR Identification",
                "pages": "pp. 1-22"
            }
        }
    },
    {
        "id": "rfunc_svar",
        "type": "RFunction",
        "properties": {
            "name": "SVAR()",
            "package": "vars",
            "description": "Estima un modelo SVAR identificando matrices estructurales A y B a partir de las innovaciones del VAR en forma reducida.",
            "r_syntax": "svar_est <- SVAR(x = var_fit, estmethod = 'direct', Amat = A_matrix, Bmat = B_matrix)",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 10-12: SVAR Estimation",
                "pages": "pp. 1-25"
            },
            "interpretation_guide": "Devuelve la matriz contemporánea estructural insesgada y permite computar las funciones de impulso respuesta causales."
        }
    },
    {
        "id": "rfunc_cajo",
        "type": "RFunction",
        "properties": {
            "name": "ca.jo()",
            "package": "urca",
            "description": "Ejecuta el test de cointegración multivariado de Johansen calculando los estadísticos de la Traza y del Máximo Valor Propio.",
            "r_syntax": "cajo_res <- ca.jo(macro_data, type = 'trace', ecdet = 'const', K = 2); summary(cajo_res)",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 18: Johansen Trace Test in Practice",
                "pages": "pp. 1-25"
            },
            "interpretation_guide": "Si el estadístico de la traza excede el valor crítico al 5% para r=0 pero no para r=1, se concluye la presencia de un único vector de cointegración."
        }
    },
    {
        "id": "rfunc_kfas_filter",
        "type": "RFunction",
        "properties": {
            "name": "KFS()",
            "package": "KFAS",
            "description": "Ejecuta el algoritmo recursivo de Kalman sobre un objeto SSModel, devolviendo los estados filtrados, suavizados y perturbaciones.",
            "r_syntax": "kfs_out <- KFS(ss_model, filtering = 'state', smoothing = 'state')",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 21-22: Kalman Filtering in R",
                "pages": "pp. 1-25"
            },
            "interpretation_guide": "Extrae la trayectoria del estado no observado (como la brecha del producto) con su correspondiente intervalo de confianza bayesiano."
        }
    },
    {
        "id": "rfunc_irf_bootstrap",
        "type": "RFunction",
        "properties": {
            "name": "irf() [Bootstrap]",
            "package": "vars",
            "description": "Calcula y grafica las funciones de impulso-respuesta ortogonalizadas de un modelo VAR/SVAR con bandas de confianza mediante remuestreo bootstrap.",
            "r_syntax": "irf_res <- irf(svar_fit, impulse = 'shock_oil', response = c('gdp', 'infl'), boot = TRUE, runs = 1000)",
            "reference": {
                "book": "MIT 14.384 Time Series Analysis (Mikusheva)",
                "chapter": "Lecture 11: Computing and Bootstrapping IRFs",
                "pages": "pp. 1-20"
            },
            "interpretation_guide": "Permite verificar si el impacto de un shock en el horizonte h es significativamente distinto de cero si las bandas de confianza no contienen al cero."
        }
    }
]

# New relationships for MIT 14.384
new_relations = [
    # part_of -> framework_graduate_time_series
    {"op": "relate", "from": "method_svar_identification", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "method_vecm_johansen", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "method_kalman_filter", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "method_factor_models_ts", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "concept_structural_shock", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "concept_irf_fevd", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "concept_johansen_cointegration", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "concept_state_space_kalman", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "concept_wold_decomposition", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "assumption_svar_orthogonality", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "assumption_cointegrating_rank", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rpkg_urca", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rpkg_kfas", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rpkg_svars", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rfunc_svar", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rfunc_cajo", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rfunc_kfas_filter", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "rfunc_irf_bootstrap", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "dataset_us_macro_sw", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "dataset_oil_shocks", "rel": "part_of", "to": "framework_graduate_time_series"},
    {"op": "relate", "from": "dataset_monetary_shocks", "rel": "part_of", "to": "framework_graduate_time_series"},

    # Cross-framework connections
    {"op": "relate", "from": "method_svar_identification", "rel": "part_of", "to": "framework_time_series"},
    {"op": "relate", "from": "method_vecm_johansen", "rel": "part_of", "to": "framework_time_series"},
    {"op": "relate", "from": "concept_johansen_cointegration", "rel": "part_of", "to": "concept_cointegration"},

    # requires
    {"op": "relate", "from": "method_svar_identification", "rel": "requires", "to": "assumption_svar_orthogonality"},
    {"op": "relate", "from": "method_svar_identification", "rel": "requires", "to": "concept_structural_shock"},
    {"op": "relate", "from": "method_vecm_johansen", "rel": "requires", "to": "assumption_cointegrating_rank"},
    {"op": "relate", "from": "method_kalman_filter", "rel": "requires", "to": "concept_state_space_kalman"},
    {"op": "relate", "from": "method_svar_identification", "rel": "requires", "to": "concept_irf_fevd"},

    # adjusts_for
    {"op": "relate", "from": "method_vecm_johansen", "rel": "adjusts_for", "to": "concept_unit_root"},
    {"op": "relate", "from": "method_svar_identification", "rel": "adjusts_for", "to": "concept_serial_correlation"},

    # alternative_to
    {"op": "relate", "from": "method_svar_identification", "rel": "alternative_to", "to": "method_var"},
    {"op": "relate", "from": "method_vecm_johansen", "rel": "alternative_to", "to": "method_var"},
    {"op": "relate", "from": "method_kalman_filter", "rel": "alternative_to", "to": "method_arima"},

    # uses_r_function
    {"op": "relate", "from": "method_svar_identification", "rel": "uses_r_function", "to": "rfunc_svar"},
    {"op": "relate", "from": "method_svar_identification", "rel": "uses_r_function", "to": "rfunc_irf_bootstrap"},
    {"op": "relate", "from": "method_vecm_johansen", "rel": "uses_r_function", "to": "rfunc_cajo"},
    {"op": "relate", "from": "method_kalman_filter", "rel": "uses_r_function", "to": "rfunc_kfas_filter"},

    # implemented_in_r_package
    {"op": "relate", "from": "rfunc_svar", "rel": "implemented_in_r_package", "to": "rpkg_vars"},
    {"op": "relate", "from": "rfunc_irf_bootstrap", "rel": "implemented_in_r_package", "to": "rpkg_vars"},
    {"op": "relate", "from": "rfunc_cajo", "rel": "implemented_in_r_package", "to": "rpkg_urca"},
    {"op": "relate", "from": "rfunc_kfas_filter", "rel": "implemented_in_r_package", "to": "rpkg_kfas"},
    {"op": "relate", "from": "dataset_us_macro_sw", "rel": "implemented_in_r_package", "to": "rpkg_urca"},
    {"op": "relate", "from": "dataset_oil_shocks", "rel": "implemented_in_r_package", "to": "rpkg_aer"},
    {"op": "relate", "from": "dataset_monetary_shocks", "rel": "implemented_in_r_package", "to": "rpkg_aer"},

    # uses_dataset
    {"op": "relate", "from": "method_svar_identification", "rel": "uses_dataset", "to": "dataset_oil_shocks"},
    {"op": "relate", "from": "method_vecm_johansen", "rel": "uses_dataset", "to": "dataset_us_macro_sw"},
    {"op": "relate", "from": "method_kalman_filter", "rel": "uses_dataset", "to": "dataset_us_macro_sw"},
    {"op": "relate", "from": "rfunc_svar", "rel": "uses_dataset", "to": "dataset_oil_shocks"},
    {"op": "relate", "from": "rfunc_cajo", "rel": "uses_dataset", "to": "dataset_us_macro_sw"},

    # evaluates
    {"op": "relate", "from": "rfunc_cajo", "rel": "evaluates", "to": "assumption_cointegrating_rank"},
    {"op": "relate", "from": "rfunc_svar", "rel": "evaluates", "to": "assumption_svar_orthogonality"}
]

# Merge into full graph
all_nodes = dict(nodes)
for ent in new_entities:
    all_nodes[ent['id']] = ent

all_edges = list(edges)
for rel in new_relations:
    all_edges.append(rel)

print(f"Total entities after addition: {len(all_nodes)}")
print(f"Total relations after addition: {len(all_edges)}")

# Validate schema rules
valid = True
for nid, n in all_nodes.items():
    ntype = n.get('type')
    if ntype not in schema['types']:
        print(f"ERROR: Node {nid} has invalid type {ntype}")
        valid = False
    req = schema['types'][ntype].get('required', [])
    for field in req:
        if field not in n['properties']:
            print(f"ERROR: Node {nid} missing required field {field}")
            valid = False

for e in all_edges:
    src_id = e['from']
    tgt_id = e['to']
    rel = e['rel']
    if src_id not in all_nodes:
        print(f"ERROR: Edge from non-existent node {src_id}")
        valid = False
    if tgt_id not in all_nodes:
        print(f"ERROR: Edge to non-existent node {tgt_id}")
        valid = False
    if rel not in schema['relations']:
        print(f"ERROR: Invalid relation predicate {rel}")
        valid = False
    else:
        src_type = all_nodes[src_id]['type']
        tgt_type = all_nodes[tgt_id]['type']
        allowed_from = schema['relations'][rel]['from_types']
        allowed_to = schema['relations'][rel]['to_types']
        if src_type not in allowed_from:
            print(f"ERROR: Relation {rel} does not allow from_type {src_type} (node {src_id})")
            valid = False
        if tgt_type not in allowed_to:
            print(f"ERROR: Relation {rel} does not allow to_type {tgt_type} (node {tgt_id})")
            valid = False

# Check connectivity
connected = set()
for e in all_edges:
    connected.add(e['from'])
    connected.add(e['to'])

isolated = set(all_nodes.keys()) - connected
if isolated:
    print(f"ERROR: Found {len(isolated)} isolated nodes:", isolated)
    valid = False
else:
    print("Zero isolated nodes! Graph is fully connected.")

if valid:
    print("Schema and graph validation PASSED with 100% compliance!")
    with open('memory/ontology/graph.jsonl', 'w', encoding='utf-8') as f:
        for ent in all_nodes.values():
            f.write(json.dumps({"op": "create", "entity": ent}, ensure_ascii=False) + '\n')
        for rel in all_edges:
            f.write(json.dumps(rel, ensure_ascii=False) + '\n')
    print("Updated memory/ontology/graph.jsonl successfully written.")
else:
    print("Validation failed.")
