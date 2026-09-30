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

# New MIT 14.382 entities
new_entities = [
    {
        "id": "framework_graduate_econometrics_core",
        "type": "Framework",
        "properties": {
            "name": "Graduate Econometrics Core & Semiparametric Theory (MIT 14.382 - Chernozhukov)",
            "description": "Marco nuclear de econometría asintótica de posgrado enfocado en estimadores de M, regresión cuantílica y de distribución, análisis contrafáctico, GMM no lineal, ecuaciones de Euler y métodos de remuestreo robusto (Wild Bootstrap).",
            "reference": {
                "book": "MIT 14.382 Econometrics Graduate Core (Chernozhukov)",
                "chapter": "Syllabus & Lecture Notes 1-12",
                "pages": "Lectures 1-12"
            }
        }
    },
    {
        "id": "dataset_growth",
        "type": "Dataset",
        "properties": {
            "name": "Growth (Barro-Lee 1994)",
            "package": "hdm",
            "description": "Panel macroeconómico de 90 países con tasa de crecimiento del PIB per cápita y 60+ covariables institucionales, educativas y demográficas para convergencia condicional en alta dimensión.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 1: Adaptive Partialling-Out & High-Dimensional Controls",
                "pages": "pp. 1-20 (Barro-Lee 1994)"
            },
            "variables": "Outcome: Crecimiento PIB per cápita; Controles: PIB inicial, escolaridad, esperanza de vida, términos de intercambio",
            "target": "Outcome"
        }
    },
    {
        "id": "dataset_fish",
        "type": "Dataset",
        "properties": {
            "name": "FultonFish (Graddy 1995)",
            "package": "AER",
            "description": "Registro diario de 111 transacciones en el Fulton Fish Market de Nueva York (1991-1992) para estimar simultáneamente curvas de oferta y demanda con condiciones meteorológicas en el mar como instrumentos exógenos.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 2 & 3: Structural Equations Models and IV/GMM",
                "pages": "pp. 1-28 (Graddy JEP 1995)"
            },
            "variables": "price (precio mayorista), quantity (volumen comerciado), stormy (condición meteorológica en alta mar), day_of_week",
            "target": "quantity"
        }
    },
    {
        "id": "dataset_gun_violence",
        "type": "Dataset",
        "properties": {
            "name": "Guns (Ayres & Donohue 2003)",
            "package": "AER",
            "description": "Panel balanceado de 50 estados de EE.UU. más Washington D.C. (1977-1999, N=1,173) que analiza el efecto de la ley 'shall-issue' de porte oculto de armas sobre delitos violentos con pocos clusters estatales.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 8 & 10: Panel Data & Cluster Robust Inference",
                "pages": "pp. 1-25"
            },
            "variables": "violent (tasa de crímenes violentos), law (presencia de ley shall-issue), prisoners, density, income, pop",
            "target": "violent"
        }
    },
    {
        "id": "method_distribution_regression",
        "type": "Method",
        "properties": {
            "name": "Distribution Regression & Counterfactual Analysis (Chernozhukov et al.)",
            "description": "Método semiparamétrico que estima la función de distribución acumulada condicional completa F_Y|X(y|x) ajustando una serie de modelos binarios en diferentes umbrales, permitiendo descomponer diferencias salariales y efectos de tratamiento en toda la distribución.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 7: Distribution Regression and Counterfactual Analysis",
                "pages": "pp. 1-35 (Chernozhukov, Fernández-Val & Melly Econometrica 2013)"
            },
            "r_syntax": "counterfactual(formula = log(wage) ~ educ + exper, data = df, group = treat, nreg = 100)",
            "dataset": "dataset_growth",
            "interpretation_guide": "Permite descomponer la brecha salarial contrafáctica en efecto composición (características) y efecto estructura salarial (retornos) en cualquier cuantil sin asumir linealidad."
        }
    },
    {
        "id": "method_quantile_regression",
        "type": "Method",
        "properties": {
            "name": "Quantile Regression (Koenker & Bassett)",
            "description": "Modelo semiparamétrico que minimiza la pérdida asimétrica en valor absoluto (check function) para estimar la función de cuantil condicional Q_Y|X(tau|x) en cualquier cuantil tau in (0, 1).",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 6: M-Estimation and Quantile Regression",
                "pages": "pp. 1-30"
            },
            "r_syntax": "rq(log(wage) ~ educ + exper, tau = c(0.1, 0.5, 0.9), data = df)",
            "dataset": "dataset_ak91",
            "interpretation_guide": "Un coeficiente beta(0.9) superior a beta(0.1) evidencia que el retorno a la educación es heterogéneo y mayor en la cola superior de la distribución de ingresos."
        }
    },
    {
        "id": "method_nonlinear_gmm",
        "type": "Method",
        "properties": {
            "name": "Nonlinear GMM & Euler Equations (Hansen & Singleton)",
            "description": "Estimación de modelos macrofinancieros y de elección intertemporal donde las condiciones de primer orden de optimización no lineales implican ortogonalidad respecto a la información pasada: E[u'(c_t+1)/u'(c_t) * (1+r_t+1) - 1 | I_t] = 0.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 4: Euler Equations and Nonlinear GMM",
                "pages": "pp. 1-28 (Hansen & Singleton Econometrica 1982)"
            },
            "r_syntax": "gmm(g = moment_function, x = instruments, t0 = c(beta = 0.99, gamma = 2), type = 'twoStep')",
            "dataset": "dataset_cref",
            "interpretation_guide": "Permite estimar parámetros estructurales profundos (tasa de descuento intertemporal beta y aversión relativa al riesgo gamma) contrastando sobreidentificación con el test J de Hansen."
        }
    },
    {
        "id": "method_liml_jive",
        "type": "Method",
        "properties": {
            "name": "LIML & Jackknife IV (JIVE) para Instrumentos Débiles",
            "description": "Estimadores de variables instrumentales modificados que eliminan el sesgo de segundo orden de 2SLS cuando el número de instrumentos crece proporcionalmente a la muestra (many weak instruments) mediante eliminación cruzada (jackknife).",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 2 & 9: Many Instruments, LIML & JIVE",
                "pages": "pp. 1-24 (Angrist, Imbens & Krueger 1999)"
            },
            "r_syntax": "ivreg(quantity ~ price | stormy + day_of_week, data = FultonFish, method = 'LIML')",
            "dataset": "dataset_fish",
            "interpretation_guide": "LIML y JIVE proporcionan estimaciones asintóticamente insesgadas del parámetro de demanda incluso cuando el estadístico F de primer estadio es moderado o débil."
        }
    },
    {
        "id": "concept_counterfactual_distribution",
        "type": "Concept",
        "properties": {
            "name": "Distribución Contrafáctica (Counterfactual Distribution)",
            "definition": "Distribución marginal acumulada F_Y(t)|X que habría presentado una población si sus características X se hubiesen distribuido de acuerdo con otra subpoblación de referencia.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 7: Counterfactual Distributions",
                "pages": "pp. 5-20"
            },
            "interpretation_guide": "Base formal para descomponer brechas de género o efectos de políticas públicas en toda la distribución sin depender de medias condicionales exclusivamente."
        }
    },
    {
        "id": "concept_m_estimation",
        "type": "Concept",
        "properties": {
            "name": "Estimadores de M y Teoría Asintótica (M-Estimation)",
            "definition": "Clase unificada de estimadores definidos mediante la minimización de un criterio muestral sum_i m(w_i, theta) o como raíces de condiciones de primer orden sum_i psi(w_i, theta) = 0.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 6: Non-Linear Regression & M-Estimation",
                "pages": "pp. 1-18"
            },
            "interpretation_guide": "Engloba OLS, MLE, NLS, GMM y Regresión Cuantílica bajo un marco unificado de normalidad asintótica mediante matrices Hessian e Info (sandwich generalizado)."
        }
    },
    {
        "id": "concept_wild_bootstrap",
        "type": "Concept",
        "properties": {
            "name": "Wild Cluster Bootstrap (Multiplier Bootstrap)",
            "definition": "Método de remuestreo residual no paramétrico donde los residuos de cada cluster se multiplican por variables aleatorias independientes de media cero y varianza unitaria (pesos Rademacher/Mammen) para corregir la subestimación de errores estándar cuando el número de clusters G es reducido (G < 30).",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 5: Bootstrapping in Econometrics",
                "pages": "pp. 10-26 (Cameron, Gelbach & Miller 2008)"
            },
            "interpretation_guide": "Resuelve el problema de tasas de rechazo empíricas sobredimensionadas en paneles estatales con inferencia cluster convencional."
        }
    },
    {
        "id": "concept_incidental_parameters",
        "type": "Concept",
        "properties": {
            "name": "Problema de Parámetros Incidentales (Incidental Parameters Problem)",
            "definition": "Sesgo asintótico severo que surge en modelos no lineales de panel (Logit/Probit/Tobit) con efectos fijos individuales cuando N tiende a infinito con T fijo, donde el número de parámetros crece al mismo ritmo que la muestra.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 10: Nonlinear Panel Data",
                "pages": "pp. 1-22 (Neyman & Scott 1948 / Hahn & Newey 2004)"
            },
            "interpretation_guide": "Impide estimar efectos fijos incondicionales directamente por dummies; requiere métodos condicionales (Chamberlain) o correcciones analíticas de sesgo."
        }
    },
    {
        "id": "concept_simultaneous_inference",
        "type": "Concept",
        "properties": {
            "name": "Inferencia Simultánea y Control de Error Familiar (Simultaneous Inference)",
            "definition": "Procedimientos de contrastes de hipótesis múltiples diseñados para controlar la probabilidad de cometer al menos un error de Tipo I (Family-Wise Error Rate, FWER) mediante algoritmos stepdown de Romano-Wolf o correcciones de Holm/Bonferroni.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 1: Adaptive Partialling-Out & Simultaneous Inference",
                "pages": "pp. 8-22 (Romano & Wolf 2005)"
            },
            "interpretation_guide": "Indispensable al evaluar simultáneamente múltiples variables de política o múltiples resultados (multi-outcome testing) para evitar falsos descubrimientos."
        }
    },
    {
        "id": "assumption_gmm_identification",
        "type": "Assumption",
        "properties": {
            "name": "Identificación Global de Momentos GMM",
            "definition": "Condición que exige que E[g(W, theta)] = 0 si y solo si theta = theta_0, junto con el supuesto de que la matriz Jacobiana E[d/dtheta g(W, theta_0)] tiene rango pleno de columnas.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 3: GMM Identification & Asymptotics",
                "pages": "pp. 4-15"
            }
        }
    },
    {
        "id": "assumption_quantile_monotonicity",
        "type": "Assumption",
        "properties": {
            "name": "Monotonía Estricta en Regresión Cuantílica",
            "definition": "Supuesto de que la función de distribución acumulada condicional F_Y|X(y|x) es estrictamente monótona creciente y continuamente diferenciable en el soporte de Y.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 6: Quantile Regression Assumptions",
                "pages": "pp. 6-16"
            }
        }
    },
    {
        "id": "rpkg_quantreg",
        "type": "RPackage",
        "properties": {
            "name": "quantreg",
            "purpose": "Paquete líder en R para regresión cuantílica lineal, no lineal y no paramétrica, procesos cuantílicos y contrastes de hipótesis de Koenker.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 6: Quantile Regression in R",
                "pages": "pp. 1-20"
            }
        }
    },
    {
        "id": "rpkg_counterfactual",
        "type": "RPackage",
        "properties": {
            "name": "Counterfactual",
            "purpose": "Paquete oficial de Chernozhukov, Fernández-Val y Melly para estimación e inferencia en distribuciones contrafácticas, regresión de distribución y descomposición salarial.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 7: Counterfactual R Lab",
                "pages": "pp. 1-25"
            }
        }
    },
    {
        "id": "rpkg_fwildclusterboot",
        "type": "RPackage",
        "properties": {
            "name": "fwildclusterboot",
            "purpose": "Implementación de alto rendimiento en R para Wild Cluster Bootstrap rápido, compatible con modelos lm, feols y fixest para muestras con clusters pequeños.",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 5 & 8: Wild Bootstrap in R",
                "pages": "pp. 1-18"
            }
        }
    },
    {
        "id": "rfunc_rq",
        "type": "RFunction",
        "properties": {
            "name": "rq()",
            "package": "quantreg",
            "description": "Ajusta modelos de regresión cuantílica para uno o múltiples cuantiles simultáneos utilizando programación lineal simplex modificada.",
            "r_syntax": "rq(y ~ x1 + x2, tau = c(0.25, 0.5, 0.75), data = df)",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 6: Quantile Regression",
                "pages": "pp. 1-20"
            },
            "interpretation_guide": "Devuelve la pendiente marginal del cuantil tau condicional ante variaciones unitarias en los regresores."
        }
    },
    {
        "id": "rfunc_counterfactual",
        "type": "RFunction",
        "properties": {
            "name": "counterfactual()",
            "package": "Counterfactual",
            "description": "Calcula distribuciones contrafácticas, cuantiles contrafácticos e intervalos de confianza uniformes basados en remuestreo.",
            "r_syntax": "counterfactual(log(wage) ~ educ + exper, data = df, group = treat, method = 'qr', nreg = 100)",
            "reference": {
                "book": "MIT 14.387 / 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 7: Counterfactual Estimation",
                "pages": "pp. 1-25"
            },
            "interpretation_guide": "Descompone cambios en la desigualdad o brechas de ingreso entre grupos en componentes de dotación y precios."
        }
    },
    {
        "id": "rfunc_gmm_nonlinear",
        "type": "RFunction",
        "properties": {
            "name": "gmm() [Nonlinear]",
            "package": "gmm",
            "description": "Estimación por GMM de funciones de momentos no lineales de Euler minimizando la forma cuadrática con matriz sándwich óptima de Newey-West.",
            "r_syntax": "gmm(g = moment_function, x = instruments, t0 = initial_values, type = 'twoStep')",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 4: Nonlinear GMM",
                "pages": "pp. 1-22"
            },
            "interpretation_guide": "El contraste J de Hansen (specTest) evalúa la validez conjunta de los momentos sobreidentificados."
        }
    },
    {
        "id": "rfunc_boottest",
        "type": "RFunction",
        "properties": {
            "name": "boottest()",
            "package": "fwildclusterboot",
            "description": "Calcula p-valores e intervalos de confianza para coeficientes de regresión mediante el Wild Cluster Bootstrap rápido de Cameron, Gelbach y Miller.",
            "r_syntax": "boottest(model, param = 'treatment', clustid = 'state', B = 9999, type = 'rademacher')",
            "reference": {
                "book": "MIT 14.382 Econometrics (Chernozhukov)",
                "chapter": "Lecture 5: Bootstrap Methods",
                "pages": "pp. 1-20"
            },
            "interpretation_guide": "Proporciona inferencia exacta y control de tasa de error tipo I incluso con tan solo 10 a 20 conglomerados."
        }
    }
]

# New relationships for MIT 14.382
new_relations = [
    # part_of -> framework_graduate_econometrics_core
    {"op": "relate", "from": "method_distribution_regression", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "method_quantile_regression", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "method_nonlinear_gmm", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "method_liml_jive", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "concept_counterfactual_distribution", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "concept_m_estimation", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "concept_wild_bootstrap", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "concept_incidental_parameters", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "concept_simultaneous_inference", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "assumption_gmm_identification", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "assumption_quantile_monotonicity", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rpkg_quantreg", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rpkg_counterfactual", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rpkg_fwildclusterboot", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rfunc_rq", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rfunc_counterfactual", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rfunc_gmm_nonlinear", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "rfunc_boottest", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "dataset_growth", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "dataset_fish", "rel": "part_of", "to": "framework_graduate_econometrics_core"},
    {"op": "relate", "from": "dataset_gun_violence", "rel": "part_of", "to": "framework_graduate_econometrics_core"},

    # Cross-framework connections
    {"op": "relate", "from": "method_quantile_regression", "rel": "part_of", "to": "framework_microeconometrics"},
    {"op": "relate", "from": "method_distribution_regression", "rel": "part_of", "to": "framework_potential_outcomes"},
    {"op": "relate", "from": "concept_incidental_parameters", "rel": "part_of", "to": "framework_microeconometrics"},

    # requires
    {"op": "relate", "from": "method_distribution_regression", "rel": "requires", "to": "concept_counterfactual_distribution"},
    {"op": "relate", "from": "method_quantile_regression", "rel": "requires", "to": "assumption_quantile_monotonicity"},
    {"op": "relate", "from": "method_nonlinear_gmm", "rel": "requires", "to": "assumption_gmm_identification"},
    {"op": "relate", "from": "method_liml_jive", "rel": "requires", "to": "assumption_instrument_relevance"},
    {"op": "relate", "from": "method_liml_jive", "rel": "requires", "to": "assumption_exclusion_restriction"},
    {"op": "relate", "from": "method_distribution_regression", "rel": "requires", "to": "assumption_positivity"},

    # adjusts_for
    {"op": "relate", "from": "method_distribution_regression", "rel": "adjusts_for", "to": "concept_confounder"},
    {"op": "relate", "from": "method_liml_jive", "rel": "adjusts_for", "to": "concept_endogeneity"},

    # alternative_to
    {"op": "relate", "from": "method_distribution_regression", "rel": "alternative_to", "to": "method_quantile_regression"},
    {"op": "relate", "from": "method_quantile_regression", "rel": "alternative_to", "to": "method_ols"},
    {"op": "relate", "from": "method_liml_jive", "rel": "alternative_to", "to": "method_iv"},
    {"op": "relate", "from": "method_nonlinear_gmm", "rel": "alternative_to", "to": "method_gmm"},

    # uses_r_function
    {"op": "relate", "from": "method_distribution_regression", "rel": "uses_r_function", "to": "rfunc_counterfactual"},
    {"op": "relate", "from": "method_quantile_regression", "rel": "uses_r_function", "to": "rfunc_rq"},
    {"op": "relate", "from": "method_nonlinear_gmm", "rel": "uses_r_function", "to": "rfunc_gmm_nonlinear"},
    {"op": "relate", "from": "method_liml_jive", "rel": "uses_r_function", "to": "rfunc_ivreg"},

    # implemented_in_r_package
    {"op": "relate", "from": "rfunc_rq", "rel": "implemented_in_r_package", "to": "rpkg_quantreg"},
    {"op": "relate", "from": "rfunc_counterfactual", "rel": "implemented_in_r_package", "to": "rpkg_counterfactual"},
    {"op": "relate", "from": "rfunc_gmm_nonlinear", "rel": "implemented_in_r_package", "to": "rpkg_gmm"},
    {"op": "relate", "from": "rfunc_boottest", "rel": "implemented_in_r_package", "to": "rpkg_fwildclusterboot"},
    {"op": "relate", "from": "dataset_growth", "rel": "implemented_in_r_package", "to": "rpkg_hdm"},
    {"op": "relate", "from": "dataset_fish", "rel": "implemented_in_r_package", "to": "rpkg_aer"},
    {"op": "relate", "from": "dataset_gun_violence", "rel": "implemented_in_r_package", "to": "rpkg_aer"},

    # uses_dataset
    {"op": "relate", "from": "method_distribution_regression", "rel": "uses_dataset", "to": "dataset_growth"},
    {"op": "relate", "from": "method_liml_jive", "rel": "uses_dataset", "to": "dataset_fish"},
    {"op": "relate", "from": "rfunc_boottest", "rel": "uses_dataset", "to": "dataset_gun_violence"},
    {"op": "relate", "from": "rfunc_rq", "rel": "uses_dataset", "to": "dataset_ak91"},
    {"op": "relate", "from": "rfunc_counterfactual", "rel": "uses_dataset", "to": "dataset_growth"},

    # evaluates
    {"op": "relate", "from": "rfunc_boottest", "rel": "evaluates", "to": "concept_wild_bootstrap"},
    {"op": "relate", "from": "rfunc_gmm_nonlinear", "rel": "evaluates", "to": "assumption_gmm_identification"}
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
