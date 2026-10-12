#!/usr/bin/env python3
"""
Enriquecedor de ontología basado en Wolfram MathWorld.

MathWorld es una enciclopedia matemática con definiciones rigurosas,
fórmulas y referencias académicas.

Fuente: https://mathworld.wolfram.com/
Enfoque: Knowledge-based (contenido codificado manualmente)
"""

import json
import os
from typing import Dict, List, Set, Tuple
from datetime import datetime

GRAPH_PATH = r"C:\NEVEN\ontology\econometria\graph.jsonl"

# ═══════════════════════════════════════════════════════════════════════════════
# CONOCIMIENTO EXTRAÍDO DE MATHWORLD
# ═══════════════════════════════════════════════════════════════════════════════

MATHWORLD_ENTITIES = {
    # ─── Distribuciones Continuas ──────────────────────────────────────────────
    "dist_cauchy": {
        "type": "Model",
        "name": "Cauchy Distribution",
        "description": "Heavy-tailed distribution with no defined mean or variance. Ratio of two standard normals.",
        "url": "https://mathworld.wolfram.com/CauchyDistribution.html"
    },
    "dist_laplace": {
        "type": "Model",
        "name": "Laplace Distribution",
        "description": "Double exponential distribution. Difference of two iid exponentials.",
        "url": "https://mathworld.wolfram.com/LaplaceDistribution.html"
    },
    "dist_weibull": {
        "type": "Model",
        "name": "Weibull Distribution",
        "description": "Flexible distribution for reliability analysis and survival times. Generalizes exponential.",
        "url": "https://mathworld.wolfram.com/WeibullDistribution.html"
    },
    "dist_pareto": {
        "type": "Model",
        "name": "Pareto Distribution",
        "description": "Power-law distribution used for income, city sizes, and other heavy-tailed phenomena.",
        "url": "https://mathworld.wolfram.com/ParetoDistribution.html"
    },
    "dist_lognormal": {
        "type": "Model",
        "name": "Lognormal Distribution",
        "description": "Distribution of exp(X) where X is normal. Used for stock prices, income, particle sizes.",
        "url": "https://mathworld.wolfram.com/LogNormalDistribution.html"
    },
    "dist_inverse_gaussian": {
        "type": "Model",
        "name": "Inverse Gaussian Distribution",
        "description": "Also called Wald distribution. Models first passage time of Brownian motion.",
        "url": "https://mathworld.wolfram.com/InverseGaussianDistribution.html"
    },
    
    # ─── Distribuciones Discretas ──────────────────────────────────────────────
    "dist_geometric": {
        "type": "Model",
        "name": "Geometric Distribution",
        "description": "Number of Bernoulli trials until first success. Memoryless discrete distribution.",
        "url": "https://mathworld.wolfram.com/GeometricDistribution.html"
    },
    "dist_negative_binomial": {
        "type": "Model",
        "name": "Negative Binomial Distribution",
        "description": "Number of failures before r successes. Generalizes geometric distribution.",
        "url": "https://mathworld.wolfram.com/NegativeBinomialDistribution.html"
    },
    "dist_hypergeometric": {
        "type": "Model",
        "name": "Hypergeometric Distribution",
        "description": "Sampling without replacement from finite population. Converges to binomial as N→∞.",
        "url": "https://mathworld.wolfram.com/HypergeometricDistribution.html"
    },
    "dist_multinomial": {
        "type": "Model",
        "name": "Multinomial Distribution",
        "description": "Generalization of binomial to k categories. Joint distribution of category counts.",
        "url": "https://mathworld.wolfram.com/MultinomialDistribution.html"
    },
    
    # ─── Funciones Especiales ──────────────────────────────────────────────────
    "func_erf": {
        "type": "Function",
        "name": "Error Function (erf)",
        "description": "erf(x) = (2/√π)∫₀ˣ e^(-t²)dt. Related to normal CDF: Φ(x) = ½[1 + erf(x/√2)].",
        "url": "https://mathworld.wolfram.com/Erf.html"
    },
    "func_gamma_function": {
        "type": "Function",
        "name": "Gamma Function",
        "description": "Γ(n) = (n-1)! for integers. Extends factorial to complex numbers.",
        "url": "https://mathworld.wolfram.com/GammaFunction.html"
    },
    "func_beta_function": {
        "type": "Function",
        "name": "Beta Function",
        "description": "B(a,b) = Γ(a)Γ(b)/Γ(a+b). Normalizing constant for Beta distribution.",
        "url": "https://mathworld.wolfram.com/BetaFunction.html"
    },
    "func_digamma": {
        "type": "Function",
        "name": "Digamma Function",
        "description": "ψ(x) = d/dx ln Γ(x). Derivative of log-gamma function.",
        "url": "https://mathworld.wolfram.com/DigammaFunction.html"
    },
    
    # ─── Teoremas y Desigualdades ──────────────────────────────────────────────
    "theorem_chebyshev_inequality": {
        "type": "Concept",
        "name": "Chebyshev's Inequality",
        "description": "P(|X - μ| ≥ kσ) ≤ 1/k². Universal bound on tail probabilities.",
        "url": "https://mathworld.wolfram.com/ChebyshevInequality.html"
    },
    "theorem_markov_inequality": {
        "type": "Concept",
        "name": "Markov's Inequality",
        "description": "P(X ≥ a) ≤ E[X]/a for non-negative X. Basis for Chebyshev.",
        "url": "https://mathworld.wolfram.com/MarkovInequality.html"
    },
    "theorem_jensen_inequality": {
        "type": "Concept",
        "name": "Jensen's Inequality",
        "description": "For convex f: E[f(X)] ≥ f(E[X]). Fundamental in information theory.",
        "url": "https://mathworld.wolfram.com/JensensInequality.html"
    },
    "theorem_cauchy_schwarz": {
        "type": "Concept",
        "name": "Cauchy-Schwarz Inequality",
        "description": "|E[XY]|² ≤ E[X²]E[Y²]. Implies correlation ∈ [-1,1].",
        "url": "https://mathworld.wolfram.com/Cauchy-SchwarzInequality.html"
    },
    "theorem_boole_inequality": {
        "type": "Concept",
        "name": "Boole's Inequality (Union Bound)",
        "description": "P(∪Aᵢ) ≤ ΣP(Aᵢ). Upper bound on probability of union.",
        "url": "https://mathworld.wolfram.com/BoolesInequality.html"
    },
    
    # ─── Estadísticos y Estimadores ────────────────────────────────────────────
    "concept_sample_mean": {
        "type": "Concept",
        "name": "Sample Mean",
        "description": "x̄ = (1/n)Σxᵢ. Unbiased estimator of population mean.",
        "url": "https://mathworld.wolfram.com/SampleMean.html"
    },
    "concept_sample_variance": {
        "type": "Concept",
        "name": "Sample Variance",
        "description": "s² = Σ(xᵢ - x̄)²/(n-1). Unbiased estimator of population variance.",
        "url": "https://mathworld.wolfram.com/SampleVariance.html"
    },
    "concept_order_statistic": {
        "type": "Concept",
        "name": "Order Statistic",
        "description": "X₍ₖ₎ is k-th smallest value in sample. X₍₁₎ = min, X₍ₙ₎ = max.",
        "url": "https://mathworld.wolfram.com/OrderStatistic.html"
    },
    "concept_sufficient_statistic": {
        "type": "Concept",
        "name": "Sufficient Statistic",
        "description": "Statistic that captures all information about parameter. Fisher-Neyman factorization.",
        "url": "https://mathworld.wolfram.com/SufficientStatistic.html"
    },
    "concept_complete_statistic": {
        "type": "Concept",
        "name": "Complete Statistic",
        "description": "Sufficient statistic with no unbiased estimator of zero. Lehmann-Scheffé theorem.",
        "url": "https://mathworld.wolfram.com/CompletenessStatistic.html"
    },
    "concept_ancillary_statistic": {
        "type": "Concept",
        "name": "Ancillary Statistic",
        "description": "Statistic whose distribution doesn't depend on parameter. Contains no information.",
        "url": "https://mathworld.wolfram.com/AncillaryStatistic.html"
    },
    
    # ─── Tests de Hipótesis ────────────────────────────────────────────────────
    "test_kolmogorov_smirnov": {
        "type": "Test",
        "name": "Kolmogorov-Smirnov Test",
        "description": "Non-parametric test comparing empirical CDF to theoretical or another sample.",
        "url": "https://mathworld.wolfram.com/Kolmogorov-SmirnovTest.html"
    },
    "test_anderson_darling": {
        "type": "Test",
        "name": "Anderson-Darling Test",
        "description": "Goodness-of-fit test giving more weight to tails than Kolmogorov-Smirnov.",
        "url": "https://mathworld.wolfram.com/Anderson-DarlingStatistic.html"
    },
    "test_shapiro_wilk": {
        "type": "Test",
        "name": "Shapiro-Wilk Test",
        "description": "Test for normality based on correlation between data and normal quantiles.",
        "url": "https://mathworld.wolfram.com/Shapiro-WilkWTest.html"
    },
    "test_runs": {
        "type": "Test",
        "name": "Runs Test",
        "description": "Non-parametric test for randomness based on number of runs in sequence.",
        "url": "https://mathworld.wolfram.com/RunsTest.html"
    },
    "test_sign": {
        "type": "Test",
        "name": "Sign Test",
        "description": "Non-parametric test for median. Based on signs of differences from hypothesized value.",
        "url": "https://mathworld.wolfram.com/SignTest.html"
    },
    "test_wilcoxon_signed_rank": {
        "type": "Test",
        "name": "Wilcoxon Signed-Rank Test",
        "description": "Non-parametric alternative to paired t-test. Uses ranks of absolute differences.",
        "url": "https://mathworld.wolfram.com/WilcoxonSignedRankTest.html"
    },
    "test_mann_whitney": {
        "type": "Test",
        "name": "Mann-Whitney U Test",
        "description": "Non-parametric test for comparing two independent samples. Rank-based.",
        "url": "https://mathworld.wolfram.com/Mann-WhitneyTest.html"
    },
    "test_kruskal_wallis": {
        "type": "Test",
        "name": "Kruskal-Wallis Test",
        "description": "Non-parametric alternative to one-way ANOVA. Extends Mann-Whitney to k groups.",
        "url": "https://mathworld.wolfram.com/Kruskal-WallisTest.html"
    },
    
    # ─── Conceptos de Correlación ──────────────────────────────────────────────
    "concept_pearson_correlation": {
        "type": "Concept",
        "name": "Pearson Correlation Coefficient",
        "description": "ρ = Cov(X,Y)/(σₓσᵧ). Measures linear relationship, ∈ [-1,1].",
        "url": "https://mathworld.wolfram.com/CorrelationCoefficient.html"
    },
    "concept_spearman_correlation": {
        "type": "Concept",
        "name": "Spearman Rank Correlation",
        "description": "Pearson correlation applied to ranks. Measures monotonic relationship.",
        "url": "https://mathworld.wolfram.com/SpearmanRankCorrelationCoefficient.html"
    },
    "concept_kendall_tau": {
        "type": "Concept",
        "name": "Kendall's Tau",
        "description": "Correlation based on concordant/discordant pairs. More robust than Spearman.",
        "url": "https://mathworld.wolfram.com/KendallsTau.html"
    },
    "concept_partial_correlation": {
        "type": "Concept",
        "name": "Partial Correlation",
        "description": "Correlation between X and Y controlling for Z. Removes confounding.",
        "url": "https://mathworld.wolfram.com/PartialCorrelation.html"
    },
    
    # ─── Conceptos de Regresión ────────────────────────────────────────────────
    "concept_residual": {
        "type": "Concept",
        "name": "Residual",
        "description": "eᵢ = yᵢ - ŷᵢ. Difference between observed and fitted value.",
        "url": "https://mathworld.wolfram.com/Residual.html"
    },
    "concept_leverage": {
        "type": "Concept",
        "name": "Leverage",
        "description": "hᵢᵢ = diagonal of hat matrix. Measures influence of xᵢ on ŷᵢ.",
        "url": "https://mathworld.wolfram.com/LeveragePoint.html"
    },
    "concept_cooks_distance": {
        "type": "Concept",
        "name": "Cook's Distance",
        "description": "Measures influence of observation on all fitted values. Combines leverage and residual.",
        "url": "https://mathworld.wolfram.com/CooksDistance.html"
    },
    "concept_r_squared": {
        "type": "Concept",
        "name": "Coefficient of Determination (R²)",
        "description": "R² = 1 - SSE/SST. Proportion of variance explained by model.",
        "url": "https://mathworld.wolfram.com/CorrelationCoefficient.html"
    },
    
    # ─── Métodos de Muestreo ───────────────────────────────────────────────────
    "technique_bootstrap": {
        "type": "Technique",
        "name": "Bootstrap",
        "description": "Resampling with replacement to estimate sampling distribution of statistic.",
        "url": "https://mathworld.wolfram.com/Bootstrap.html"
    },
    "technique_jackknife": {
        "type": "Technique",
        "name": "Jackknife",
        "description": "Leave-one-out resampling to estimate bias and variance of estimator.",
        "url": "https://mathworld.wolfram.com/Jackknife.html"
    },
    "technique_importance_sampling": {
        "type": "Technique",
        "name": "Importance Sampling",
        "description": "Variance reduction technique using alternative sampling distribution.",
        "url": "https://mathworld.wolfram.com/ImportanceSampling.html"
    },
    
    # ─── Procesos Estocásticos ─────────────────────────────────────────────────
    "concept_brownian_motion": {
        "type": "Concept",
        "name": "Brownian Motion (Wiener Process)",
        "description": "Continuous-time stochastic process with independent normal increments. B(t) ~ N(0,t).",
        "url": "https://mathworld.wolfram.com/WienerProcess.html"
    },
    "concept_poisson_process": {
        "type": "Concept",
        "name": "Poisson Process",
        "description": "Counting process with independent increments. Inter-arrival times are exponential.",
        "url": "https://mathworld.wolfram.com/PoissonProcess.html"
    },
    "concept_random_walk": {
        "type": "Concept",
        "name": "Random Walk",
        "description": "Discrete-time process where position changes by iid steps. Sₙ = Σᵢ Xᵢ.",
        "url": "https://mathworld.wolfram.com/RandomWalk.html"
    },
    
    # ─── Teoría de la Información ──────────────────────────────────────────────
    "concept_entropy": {
        "type": "Concept",
        "name": "Shannon Entropy",
        "description": "H(X) = -Σ p(x) log p(x). Measure of uncertainty or information content.",
        "url": "https://mathworld.wolfram.com/Entropy.html"
    },
    "concept_kl_divergence": {
        "type": "Concept",
        "name": "Kullback-Leibler Divergence",
        "description": "D_KL(P||Q) = Σ P(x) log(P(x)/Q(x)). Measures difference between distributions.",
        "url": "https://mathworld.wolfram.com/Kullback-LeiblerDivergence.html"
    },
    "concept_mutual_information": {
        "type": "Concept",
        "name": "Mutual Information",
        "description": "I(X;Y) = H(X) - H(X|Y). Measures information shared between variables.",
        "url": "https://mathworld.wolfram.com/MutualInformation.html"
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# RELACIONES
# ═══════════════════════════════════════════════════════════════════════════════

MATHWORLD_RELATIONS = [
    # ─── Distribuciones ────────────────────────────────────────────────────────
    ("dist_cauchy", "dist_normal", "derived_from"),
    ("dist_cauchy", "dist_t_distribution", "special_case_of"),
    ("dist_laplace", "dist_exponential", "derived_from"),
    ("dist_weibull", "dist_exponential", "generalizes"),
    ("dist_pareto", "concept_power_law", "follows"),
    ("dist_lognormal", "dist_normal", "derived_from"),
    ("dist_inverse_gaussian", "concept_brownian_motion", "related_to"),
    ("dist_geometric", "dist_binomial", "related_to"),
    ("dist_negative_binomial", "dist_geometric", "generalizes"),
    ("dist_hypergeometric", "dist_binomial", "converges_to"),
    ("dist_multinomial", "dist_binomial", "generalizes"),
    
    # ─── Funciones especiales ──────────────────────────────────────────────────
    ("func_erf", "dist_normal", "related_to"),
    ("func_gamma_function", "dist_gamma", "used_in"),
    ("func_beta_function", "dist_beta", "normalizes"),
    ("func_digamma", "func_gamma_function", "derivative_of"),
    
    # ─── Desigualdades ─────────────────────────────────────────────────────────
    ("theorem_chebyshev_inequality", "theorem_markov_inequality", "derived_from"),
    ("theorem_chebyshev_inequality", "concept_variance", "uses"),
    ("theorem_markov_inequality", "concept_expected_value", "uses"),
    ("theorem_jensen_inequality", "concept_expected_value", "applies_to"),
    ("theorem_cauchy_schwarz", "concept_pearson_correlation", "implies_bounds"),
    
    # ─── Estadísticos ──────────────────────────────────────────────────────────
    ("concept_sample_mean", "concept_expected_value", "estimates"),
    ("concept_sample_variance", "concept_variance", "estimates"),
    ("concept_sample_mean", "theorem_lln", "converges_by"),
    ("concept_sample_mean", "theorem_clt", "converges_by"),
    ("concept_order_statistic", "concept_sample_mean", "related_to"),
    ("concept_sufficient_statistic", "concept_fisher_information", "related_to"),
    ("concept_complete_statistic", "concept_sufficient_statistic", "type_of"),
    ("concept_ancillary_statistic", "concept_sufficient_statistic", "complement_of"),
    
    # ─── Tests no paramétricos ─────────────────────────────────────────────────
    ("test_kolmogorov_smirnov", "dist_normal", "tests"),
    ("test_anderson_darling", "test_kolmogorov_smirnov", "alternative_to"),
    ("test_shapiro_wilk", "dist_normal", "tests"),
    ("test_wilcoxon_signed_rank", "test_t", "alternative_to"),
    ("test_mann_whitney", "test_t", "alternative_to"),
    ("test_kruskal_wallis", "test_f", "alternative_to"),
    ("test_sign", "test_wilcoxon_signed_rank", "simpler_than"),
    ("test_runs", "concept_random_walk", "tests"),
    
    # ─── Correlación ───────────────────────────────────────────────────────────
    ("concept_spearman_correlation", "concept_pearson_correlation", "rank_version_of"),
    ("concept_kendall_tau", "concept_spearman_correlation", "alternative_to"),
    ("concept_partial_correlation", "concept_pearson_correlation", "generalizes"),
    ("concept_partial_correlation", "concept_confounding", "controls_for"),
    
    # ─── Regresión ─────────────────────────────────────────────────────────────
    ("concept_residual", "model_linear_regression", "computed_from"),
    ("concept_leverage", "concept_residual", "related_to"),
    ("concept_cooks_distance", "concept_leverage", "uses"),
    ("concept_cooks_distance", "concept_residual", "uses"),
    ("concept_r_squared", "concept_residual", "computed_from"),
    ("concept_r_squared", "model_linear_regression", "evaluates"),
    
    # ─── Resampling ────────────────────────────────────────────────────────────
    ("technique_bootstrap", "concept_sample_variance", "estimates"),
    ("technique_jackknife", "technique_bootstrap", "related_to"),
    ("technique_jackknife", "concept_unbiasedness", "estimates"),
    ("technique_importance_sampling", "technique_mcmc", "related_to"),
    
    # ─── Procesos estocásticos ─────────────────────────────────────────────────
    ("concept_brownian_motion", "dist_normal", "has_increments"),
    ("concept_poisson_process", "dist_poisson", "related_to"),
    ("concept_poisson_process", "dist_exponential", "has_interarrivals"),
    ("concept_random_walk", "concept_brownian_motion", "discrete_analog_of"),
    ("concept_random_walk", "theorem_clt", "converges_by"),
    
    # ─── Teoría de información ─────────────────────────────────────────────────
    ("concept_entropy", "dist_normal", "maximized_by"),
    ("concept_kl_divergence", "concept_entropy", "related_to"),
    ("concept_kl_divergence", "estimator_mle", "minimized_by"),
    ("concept_mutual_information", "concept_entropy", "derived_from"),
    ("concept_mutual_information", "concept_pearson_correlation", "generalizes"),
    
    # ─── Conexiones con entidades existentes ───────────────────────────────────
    ("concept_sample_mean", "estimator_ols", "used_in"),
    ("concept_residual", "func_rstudent", "standardized_as"),
    ("test_kolmogorov_smirnov", "concept_goodness_of_fit", "type_of"),
    ("concept_leverage", "concept_outlier_detection", "used_for"),
    ("concept_cooks_distance", "concept_outlier_detection", "used_for"),
]


def load_existing_entities(graph_path: str) -> Set[str]:
    """Carga IDs de entidades existentes."""
    entities = set()
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get('op') == 'create' and 'entity' in obj:
                    entities.add(obj['entity']['id'])
            except json.JSONDecodeError:
                continue
    return entities


def load_existing_relations(graph_path: str) -> Set[Tuple[str, str, str]]:
    """Carga relaciones existentes."""
    relations = set()
    with open(graph_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get('op') == 'relate' and 'relation' in obj:
                    rel = obj['relation']
                    relations.add((rel.get('from', ''), rel.get('to', ''), rel.get('type', '')))
            except json.JSONDecodeError:
                continue
    return relations


def enrich_from_mathworld():
    """Enriquece la ontología con conocimiento de MathWorld."""
    
    print("=" * 70)
    print("NEVEN MathWorld Enricher")
    print("Fuente: https://mathworld.wolfram.com/")
    print("=" * 70)
    
    existing_entities = load_existing_entities(GRAPH_PATH)
    existing_relations = load_existing_relations(GRAPH_PATH)
    
    print(f"\nEstado inicial:")
    print(f"  Entidades existentes: {len(existing_entities)}")
    print(f"  Relaciones existentes: {len(existing_relations)}")
    
    stats = {
        "entities_created": 0,
        "entities_skipped": 0,
        "relations_created": 0,
        "relations_skipped_exists": 0,
        "relations_skipped_no_target": 0,
    }
    
    new_entries = []
    
    # ─── Crear entidades nuevas ────────────────────────────────────────────────
    print(f"\n[1/2] Creando entidades de MathWorld...")
    
    for entity_id, entity_data in MATHWORLD_ENTITIES.items():
        if entity_id in existing_entities:
            stats["entities_skipped"] += 1
            continue
        
        entry = {
            "op": "create",
            "entity": {
                "id": entity_id,
                "type": entity_data["type"],
                "properties": {
                    "name": entity_data["name"],
                    "description": entity_data["description"],
                    "source": "MathWorld",
                    "url": entity_data["url"]
                }
            }
        }
        new_entries.append(entry)
        existing_entities.add(entity_id)
        stats["entities_created"] += 1
        print(f"  + {entity_id}: {entity_data['name']}")
    
    # ─── Crear relaciones ──────────────────────────────────────────────────────
    print(f"\n[2/2] Creando relaciones...")
    
    for source, target, rel_type in MATHWORLD_RELATIONS:
        if source not in existing_entities:
            stats["relations_skipped_no_target"] += 1
            continue
        if target not in existing_entities:
            stats["relations_skipped_no_target"] += 1
            continue
        
        if (source, target, rel_type) in existing_relations:
            stats["relations_skipped_exists"] += 1
            continue
        
        entry = {
            "op": "relate",
            "relation": {
                "type": rel_type,
                "from": source,
                "to": target
            }
        }
        new_entries.append(entry)
        existing_relations.add((source, target, rel_type))
        stats["relations_created"] += 1
    
    # ─── Escribir al archivo ───────────────────────────────────────────────────
    if new_entries:
        with open(GRAPH_PATH, 'a', encoding='utf-8') as f:
            for entry in new_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    # ─── Resumen ───────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("RESULTADOS")
    print(f"{'='*70}")
    print(f"Entidades creadas:    {stats['entities_created']}")
    print(f"Entidades saltadas:   {stats['entities_skipped']} (ya existían)")
    print(f"Relaciones creadas:   {stats['relations_created']}")
    print(f"Relaciones saltadas:  {stats['relations_skipped_exists']} (ya existían)")
    print(f"                      {stats['relations_skipped_no_target']} (target no existe)")
    
    return stats


if __name__ == "__main__":
    enrich_from_mathworld()
