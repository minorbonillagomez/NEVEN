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

# New MIT 14.387 entities
new_entities = [
    {
        "id": "framework_mostly_harmless_bigdata",
        "type": "Framework",
        "properties": {
            "name": "Applied Econometrics & Mostly Harmless Big Data (MIT 14.387 - Angrist & Chernozhukov)",
            "description": "Marco de econometría aplicada de posgrado enfocado en identificación causal con efectos heterogéneos (LATE, Angrist) e inferencia en alta dimensión con machine learning ortogonalizado (Double/Debiased ML, Chernozhukov).",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist & Chernozhukov)",
                "chapter": "Syllabus & Lecture Notes: LATE and High-Dimensional Big Data",
                "pages": "Lectures 1-15"
            }
        }
    },
    {
        "id": "dataset_ak91",
        "type": "Dataset",
        "properties": {
            "name": "ak91 (Angrist & Krueger 1991)",
            "package": "AER",
            "description": "Muestra del Censo de EE.UU. 1980 (329,509 individuos) que evalúa el retorno salarial de la educación utilizando el trimestre de nacimiento (qob) como instrumento exógeno basado en leyes de escolaridad obligatoria.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture: Instrumental Variables in Action",
                "pages": "pp. 1-28 (Angrist & Krueger QJE 1991)"
            },
            "variables": "wage (salario semanal), educ (años de educación), qob (trimestre de nacimiento 1-4), yob (año de nacimiento), sob (estado de nacimiento)",
            "target": "wage"
        }
    },
    {
        "id": "dataset_401k",
        "type": "Dataset",
        "properties": {
            "name": "401k (Chernozhukov & Hansen 2004)",
            "package": "hdm",
            "description": "Muestra de 9,915 individuos del SIPP 1991 que analiza el efecto de la elegibilidad a planes de pensión 401(k) sobre los activos financieros netos, controlando por múltiples covariables e ingresos en alta dimensión.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Inference in High-Dimensional Partially Linear Models",
                "pages": "pp. 1-35 (Chernozhukov & Hansen JEP 2004)"
            },
            "variables": "net_tfa (activos financieros netos), e401 (elegibilidad 401k), inc (ingresos), age, fsize, educ, marr, twoearn",
            "target": "net_tfa"
        }
    },
    {
        "id": "dataset_penn46",
        "type": "Dataset",
        "properties": {
            "name": "penn46 (Pennsylvania Reemployment Bonus)",
            "package": "hdm",
            "description": "Experimento aleatorizado de 5,099 solicitantes de seguro de desempleo en Pensilvania (1988-1989) para evaluar el impacto de incentivos económicos de reempleo sobre la duración del desempleo.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Randomized Experiments & Program Evaluation with Controls",
                "pages": "pp. 1-22"
            },
            "variables": "inuidur1 (semanas de beneficio cobradas), tg (grupo de tratamiento), female, black, hisp, agelt35, agegt54",
            "target": "inuidur1"
        }
    },
    {
        "id": "method_late_wald",
        "type": "Method",
        "properties": {
            "name": "LATE / Estimador Wald de Efectos Heterogéneos (Angrist & Imbens)",
            "description": "Estimador causal para tratamientos heterogéneos bajo cumplimiento imperfecto. Identifica el efecto promedio de tratamiento exclusivamente para la subpoblación de Compliers: E[Y|Z=1] - E[Y|Z=0] / E[D|Z=1] - E[D|Z=0].",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture: Instrumental Variables with Heterogeneous Potential Outcomes",
                "pages": "pp. 1-30"
            },
            "r_syntax": "iv_robust(wage ~ educ | qob, data = ak91, se_type = 'stata')",
            "dataset": "ak91",
            "interpretation_guide": "El estimador LATE mide el efecto causal de un año adicional de educación exclusivamente en aquellos estudiantes inducidos a estudiar más por haber nacido a principios o finales de año (Compliers)."
        }
    },
    {
        "id": "method_double_ml",
        "type": "Method",
        "properties": {
            "name": "Double / Debiased Machine Learning (Chernozhukov et al.)",
            "description": "Marco econométrico de frontera que utiliza algoritmos de Machine Learning (Random Forest, Lasso, Gradient Boosting) para estimar funciones nuisance mientras preserva inferencia asintótica estándar raíz-n mediante Ortogonalidad de Neyman y Cross-Fitting.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Double Machine Learning for Treatment and Structural Parameters",
                "pages": "pp. 1-45 (Chernozhukov et al. Econometrics Journal 2018)"
            },
            "r_syntax": "dml_plr <- DoubleMLPLR$new(data = obj_dml_data, ml_l = lrn('regr.ranger'), ml_m = lrn('regr.ranger'), n_folds = 5); dml_plr$fit()",
            "dataset": "401k",
            "interpretation_guide": "El coeficiente theta representa el efecto causal estructural desesgado tras purgar de forma no paramétrica las funciones de confusión g(X) y m(X) mediante residuos cruzados ortogonales."
        }
    },
    {
        "id": "method_post_lasso",
        "type": "Method",
        "properties": {
            "name": "Post-Double-Selection Lasso (Belloni, Chernozhukov & Hansen)",
            "description": "Método de dos etapas que selecciona covariables predictoras tanto del resultado Y como del tratamiento D usando penalización Lasso teórica, seguido de OLS sobre la unión de controles seleccionados para evitar el sesgo de regularización.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: High-Dimensional Controls & Post-Lasso Inference",
                "pages": "pp. 1-32 (Belloni et al. Restud 2014)"
            },
            "r_syntax": "rlassoEffect(x = X, y = y, d = d, method = 'double selection')",
            "dataset": "401k",
            "interpretation_guide": "Garantiza intervalos de confianza uniformemente válidos al incluir todas las variables que predicen fuertemente el tratamiento D o la respuesta Y, eliminando el sesgo de variables omitidas inducido por selección ingenua."
        }
    },
    {
        "id": "method_fuzzy_rdd",
        "type": "Method",
        "properties": {
            "name": "Fuzzy Regression Discontinuity Design (Fuzzy RDD)",
            "description": "Diseño cuasiexperimental donde la probabilidad de recibir el tratamiento salta discontinuamente en un umbral c pero sin alcanzar 0 o 1. Se estima como un modelo de variables instrumentales locales donde el corte sirve de instrumento.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture: Regression Discontinuity: Sharp vs Fuzzy",
                "pages": "pp. 1-25"
            },
            "r_syntax": "rdrobust(y = outcome, x = score, c = threshold, fuzzy = treatment)",
            "dataset": "CASchools",
            "interpretation_guide": "Estima el efecto LATE en el entorno inmediato del umbral de corte (cutoff) para los individuos cuya condición de tratamiento fue modificada por cruzar dicho umbral."
        }
    },
    {
        "id": "concept_late",
        "type": "Concept",
        "properties": {
            "name": "Local Average Treatment Effect (LATE)",
            "definition": "Efecto causal promedio del tratamiento evaluado únicamente sobre el subconjunto de unidades que modifican su estado de tratamiento en respuesta al instrumento (Compliers).",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture: Heterogeneous Treatment Effects and IV",
                "pages": "pp. 5-18"
            },
            "interpretation_guide": "A diferencia del ATE global, el LATE es específico al instrumento utilizado y no extrapola necesariamente a Always-Takers o Never-Takers."
        }
    },
    {
        "id": "concept_complier",
        "type": "Concept",
        "properties": {
            "name": "Tipología de Cumplimiento (Compliers, Always-Takers, Never-Takers, Defiers)",
            "definition": "Clasificación de cuatro subpoblaciones contrafácticas mutuamente excluyentes en modelos de variables instrumentales: Compliers (D(1)=1, D(0)=0), Always-Takers (D(1)=1, D(0)=1), Never-Takers (D(1)=0, D(0)=0) y Defiers (D(1)=0, D(0)=1).",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture: Potential Outcomes with Instruments",
                "pages": "pp. 10-22"
            },
            "interpretation_guide": "Bajo el supuesto de monotonía, los Defiers no existen, permitiendo identificar el LATE sobre los Compliers."
        }
    },
    {
        "id": "concept_neyman_orthogonality",
        "type": "Concept",
        "properties": {
            "name": "Ortogonalidad de Neyman (Neyman Orthogonality)",
            "definition": "Propiedad matemática de una función de momentos/score psi(W; theta, eta) donde la derivada de Gateaux respecto al parámetro nuisance eta evaluada en el valor verdadero eta_0 es exactamente cero. Hace a la estimación de theta insensible de primer orden a errores en eta.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Neyman Orthogonality and Double ML",
                "pages": "pp. 1-28"
            },
            "interpretation_guide": "Permite usar estimadores de Machine Learning con tasas de convergencia más lentas (n^-1/4) sin sesgar la inferencia asintótica normal raíz-n del parámetro causal theta."
        }
    },
    {
        "id": "concept_cross_fitting",
        "type": "Concept",
        "properties": {
            "name": "Partición de Muestra y Cross-Fitting K-Fold",
            "definition": "Procedimiento de partición muestral donde los modelos de machine learning para las funciones nuisance se entrenan en un subconjunto k^c y se evalúan en el subconjunto k restante, promediando las estimaciones para eliminar el sesgo de sobreajuste (overfitting bias).",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Sample Splitting & Cross-Fitting Algorithms",
                "pages": "pp. 8-20"
            },
            "interpretation_guide": "Elimina el sesgo de Donsker y garantiza la validez de los teoremas de límite central cuando se usan algoritmos complejos como Deep Learning o Random Forest."
        }
    },
    {
        "id": "concept_regularization_bias",
        "type": "Concept",
        "properties": {
            "name": "Sesgo de Regularización (Regularization Bias)",
            "definition": "Distorsión asintótica que surge al aplicar técnicas de regularización (como Lasso) directamente sobre la ecuación de resultado Y sin forzar la retención de confusores que están correlacionados moderadamente con el tratamiento D.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: High-Dimensional Selection Bias",
                "pages": "pp. 4-15"
            },
            "interpretation_guide": "El sesgo de regularización convierte confusores omitidos en endogeneidad residual si no se aplica Double Selection o Double ML."
        }
    },
    {
        "id": "assumption_monotonicity",
        "type": "Assumption",
        "properties": {
            "name": "Monotonía en Instrumentos (Monotonicity / No-Defiers)",
            "definition": "Supuesto de Angrist e Imbens que establece que la asignación del instrumento afecta el tratamiento en la misma dirección para todos los individuos: D_i(1) >= D_i(0) para todo i (prohibiendo la existencia de Defiers).",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture: Identification of LATE",
                "pages": "pp. 12-24"
            }
        }
    },
    {
        "id": "assumption_neyman_orthogonality",
        "type": "Assumption",
        "properties": {
            "name": "Condición de Ortogonalidad de Neyman del Score",
            "definition": "Supuesto estructural que exige que la función de momentos psi sea de Neyman-ortogonal respecto a las funciones nuisance poblacionales: d/d_eta E[psi(W; theta_0, eta_0)] = 0.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Orthogonal Moment Conditions",
                "pages": "pp. 6-18"
            }
        }
    },
    {
        "id": "rpkg_hdm",
        "type": "RPackage",
        "properties": {
            "name": "hdm",
            "purpose": "High-Dimensional Metrics: Paquete oficial de Chernozhukov, Hansen y Spindler para Lasso con penalización basada en teoría, post-double-selection y regresión instrumental en alta dimensión.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "R Lab: High-Dimensional Inference with hdm",
                "pages": "pp. 1-30"
            }
        }
    },
    {
        "id": "rpkg_doubleml",
        "type": "RPackage",
        "properties": {
            "name": "DoubleML",
            "purpose": "Implementación orientada a objetos en R de Double/Debiased Machine Learning (DML) para modelos PLR, PLIV, IRM e IIVM usando mlr3.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "R Lab: Double Machine Learning in Practice",
                "pages": "pp. 1-40"
            }
        }
    },
    {
        "id": "rpkg_estimatr",
        "type": "RPackage",
        "properties": {
            "name": "estimatr",
            "purpose": "Estimadores rápidos para inferencia basada en diseño (lm_robust, iv_robust, difference_in_means) con soporte estándar para correcciones HC2/HC3 y errores agrupados por cluster.",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Lecture & Recitation: Robust Standard Errors and Clustering",
                "pages": "pp. 1-15"
            }
        }
    },
    {
        "id": "rfunc_rlasso",
        "type": "RFunction",
        "properties": {
            "name": "rlasso()",
            "package": "hdm",
            "description": "Ajusta modelos lineales con regularización Lasso rigurosa, calculando penalizaciones dependientes de la heterocedasticidad de los datos sin depender de validación cruzada ad-hoc.",
            "r_syntax": "rlasso(y ~ ., data = df, post = TRUE)",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Rigorous Lasso Theory & Practice",
                "pages": "pp. 1-25"
            },
            "interpretation_guide": "Selecciona los controles relevantes controlando la tasa de falso descubrimiento y aplica Post-Lasso OLS sobre los coeficientes no nulos."
        }
    },
    {
        "id": "rfunc_rlasso_iv",
        "type": "RFunction",
        "properties": {
            "name": "rlassoIV()",
            "package": "hdm",
            "description": "Estima modelos de variables instrumentales con muchos instrumentos y controles mediante selección de instrumentos por Post-Lasso.",
            "r_syntax": "rlassoIV(y ~ d + (x1 + x2 + ...) | (z1 + z2 + ...), data = df, select_Z = TRUE)",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Many Instruments & High-Dimensional IV",
                "pages": "pp. 1-30"
            },
            "interpretation_guide": "Supera el sesgo de instrumentos débiles o excesivos mediante regularización formal de la primera etapa."
        }
    },
    {
        "id": "rfunc_double_ml_plr",
        "type": "RFunction",
        "properties": {
            "name": "DoubleMLPLR$new()",
            "package": "DoubleML",
            "description": "Crea y ajusta un modelo parcialmente lineal (Partially Linear Regression) doblemente desesgado con algoritmos de Machine Learning y cross-fitting.",
            "r_syntax": "dml_plr <- DoubleMLPLR$new(dml_data, ml_l = lrn('regr.ranger'), ml_m = lrn('regr.ranger'), n_folds = 5); dml_plr$fit()",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Chernozhukov)",
                "chapter": "Lecture: Double ML for Partially Linear Models",
                "pages": "pp. 1-35"
            },
            "interpretation_guide": "Devuelve estimaciones consistentes, eficientes y asintóticamente normales del coeficiente de tratamiento theta_0."
        }
    },
    {
        "id": "rfunc_iv_robust",
        "type": "RFunction",
        "properties": {
            "name": "iv_robust()",
            "package": "estimatr",
            "description": "Estima regresiones de variables instrumentales en dos etapas (2SLS) incorporando errores estándar robustos a heterocedasticidad (HC1/HC2/HC3) o clusterizados.",
            "r_syntax": "iv_robust(wage ~ educ + exper | qob + exper, data = ak91, clusters = state, se_type = 'CR2')",
            "reference": {
                "book": "MIT 14.387 Applied Econometrics (Angrist)",
                "chapter": "Recitation: 2SLS Inference & Cluster Corrections",
                "pages": "pp. 1-18"
            },
            "interpretation_guide": "Proporciona inferencia válida bajo heterocedasticidad no modelada y dependencia intracluster."
        }
    }
]

# New relationships
new_relations = [
    # part_of -> framework_mostly_harmless_bigdata
    {"op": "relate", "from": "method_late_wald", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "method_double_ml", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "method_post_lasso", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "method_fuzzy_rdd", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "concept_late", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "concept_complier", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "concept_neyman_orthogonality", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "concept_cross_fitting", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "concept_regularization_bias", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "assumption_monotonicity", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "assumption_neyman_orthogonality", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rpkg_hdm", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rpkg_doubleml", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rpkg_estimatr", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rfunc_rlasso", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rfunc_rlasso_iv", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rfunc_double_ml_plr", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "rfunc_iv_robust", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "dataset_ak91", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "dataset_401k", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    {"op": "relate", "from": "dataset_penn46", "rel": "part_of", "to": "framework_mostly_harmless_bigdata"},
    
    # Interconnections with existing frameworks
    {"op": "relate", "from": "method_late_wald", "rel": "part_of", "to": "framework_potential_outcomes"},
    {"op": "relate", "from": "method_fuzzy_rdd", "rel": "part_of", "to": "framework_potential_outcomes"},

    # requires
    {"op": "relate", "from": "method_late_wald", "rel": "requires", "to": "assumption_monotonicity"},
    {"op": "relate", "from": "method_late_wald", "rel": "requires", "to": "concept_complier"},
    {"op": "relate", "from": "method_late_wald", "rel": "requires", "to": "assumption_instrument_relevance"},
    {"op": "relate", "from": "method_late_wald", "rel": "requires", "to": "assumption_exclusion_restriction"},
    {"op": "relate", "from": "method_double_ml", "rel": "requires", "to": "assumption_neyman_orthogonality"},
    {"op": "relate", "from": "method_double_ml", "rel": "requires", "to": "concept_cross_fitting"},
    {"op": "relate", "from": "method_post_lasso", "rel": "requires", "to": "concept_regularization_bias"},
    {"op": "relate", "from": "method_fuzzy_rdd", "rel": "requires", "to": "assumption_monotonicity"},

    # adjusts_for
    {"op": "relate", "from": "method_double_ml", "rel": "adjusts_for", "to": "concept_confounder"},
    {"op": "relate", "from": "method_post_lasso", "rel": "adjusts_for", "to": "concept_ovb"},
    {"op": "relate", "from": "method_fuzzy_rdd", "rel": "adjusts_for", "to": "concept_selection_bias"},

    # alternative_to
    {"op": "relate", "from": "method_late_wald", "rel": "alternative_to", "to": "method_iv"},
    {"op": "relate", "from": "method_double_ml", "rel": "alternative_to", "to": "method_aipw"},
    {"op": "relate", "from": "method_post_lasso", "rel": "alternative_to", "to": "method_ols"},
    {"op": "relate", "from": "method_fuzzy_rdd", "rel": "alternative_to", "to": "method_rdd"},

    # uses_r_function
    {"op": "relate", "from": "method_late_wald", "rel": "uses_r_function", "to": "rfunc_iv_robust"},
    {"op": "relate", "from": "method_late_wald", "rel": "uses_r_function", "to": "rfunc_ivreg"},
    {"op": "relate", "from": "method_double_ml", "rel": "uses_r_function", "to": "rfunc_double_ml_plr"},
    {"op": "relate", "from": "method_post_lasso", "rel": "uses_r_function", "to": "rfunc_rlasso"},
    {"op": "relate", "from": "method_post_lasso", "rel": "uses_r_function", "to": "rfunc_rlasso_iv"},
    {"op": "relate", "from": "method_fuzzy_rdd", "rel": "uses_r_function", "to": "rfunc_rdrobust"},

    # implemented_in_r_package
    {"op": "relate", "from": "rfunc_rlasso", "rel": "implemented_in_r_package", "to": "rpkg_hdm"},
    {"op": "relate", "from": "rfunc_rlasso_iv", "rel": "implemented_in_r_package", "to": "rpkg_hdm"},
    {"op": "relate", "from": "rfunc_double_ml_plr", "rel": "implemented_in_r_package", "to": "rpkg_doubleml"},
    {"op": "relate", "from": "rfunc_iv_robust", "rel": "implemented_in_r_package", "to": "rpkg_estimatr"},
    {"op": "relate", "from": "dataset_ak91", "rel": "implemented_in_r_package", "to": "rpkg_aer"},
    {"op": "relate", "from": "dataset_401k", "rel": "implemented_in_r_package", "to": "rpkg_hdm"},
    {"op": "relate", "from": "dataset_penn46", "rel": "implemented_in_r_package", "to": "rpkg_hdm"},

    # uses_dataset
    {"op": "relate", "from": "method_late_wald", "rel": "uses_dataset", "to": "dataset_ak91"},
    {"op": "relate", "from": "method_double_ml", "rel": "uses_dataset", "to": "dataset_401k"},
    {"op": "relate", "from": "method_post_lasso", "rel": "uses_dataset", "to": "dataset_401k"},
    {"op": "relate", "from": "rfunc_iv_robust", "rel": "uses_dataset", "to": "dataset_ak91"},
    {"op": "relate", "from": "rfunc_double_ml_plr", "rel": "uses_dataset", "to": "dataset_401k"},
    {"op": "relate", "from": "rfunc_rlasso", "rel": "uses_dataset", "to": "dataset_penn46"},

    # evaluates
    {"op": "relate", "from": "rfunc_rlasso", "rel": "evaluates", "to": "concept_regularization_bias"},
    {"op": "relate", "from": "rfunc_rlasso_iv", "rel": "evaluates", "to": "assumption_instrument_relevance"}
]

# Add to test structures
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
    # Write out updated graph.jsonl
    with open('memory/ontology/graph.jsonl', 'w', encoding='utf-8') as f:
        for ent in all_nodes.values():
            f.write(json.dumps({"op": "create", "entity": ent}, ensure_ascii=False) + '\n')
        for rel in all_edges:
            f.write(json.dumps(rel, ensure_ascii=False) + '\n')
    print("Updated memory/ontology/graph.jsonl successfully written.")
else:
    print("Validation failed. Please fix errors before writing.")
