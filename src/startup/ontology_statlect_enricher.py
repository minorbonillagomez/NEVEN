#!/usr/bin/env python3
"""
Enriquecedor de ontología basado en Statlect.com

Statlect es un textbook digital de probabilidad, estadística y álgebra matricial.
Este script agrega entidades y relaciones basadas en su estructura de contenido.

Fuente: https://statlect.com/
Enfoque: Knowledge-based (contenido codificado manualmente)
"""

import json
import os
from typing import Dict, List, Set, Tuple
from datetime import datetime

GRAPH_PATH = r"C:\NEVEN\ontology\econometria\graph.jsonl"

# ═══════════════════════════════════════════════════════════════════════════════
# CONOCIMIENTO EXTRAÍDO DE STATLECT
# ═══════════════════════════════════════════════════════════════════════════════

# Entidades nuevas a crear (si no existen)
# Formato: {id: {type, name, description, url}}
STATLECT_ENTITIES = {
    # ─── Fundamentos de Probabilidad ───────────────────────────────────────────
    "concept_moment_generating_function": {
        "type": "Concept",
        "name": "Moment Generating Function (MGF)",
        "description": "Function used to characterize probability distributions. Its derivatives at zero equal the moments of the random variable.",
        "url": "https://statlect.com/fundamentals-of-probability/moment-generating-function"
    },
    "concept_characteristic_function": {
        "type": "Concept",
        "name": "Characteristic Function",
        "description": "Complex-valued function that completely characterizes a probability distribution. Always exists, unlike MGF.",
        "url": "https://statlect.com/fundamentals-of-probability/characteristic-function"
    },
    "concept_conditional_expectation": {
        "type": "Concept",
        "name": "Conditional Expectation",
        "description": "Expected value of a random variable given information about another variable. Fundamental in regression and filtering.",
        "url": "https://statlect.com/fundamentals-of-probability/conditional-expectation"
    },
    "concept_law_iterated_expectations": {
        "type": "Concept",
        "name": "Law of Iterated Expectations",
        "description": "E[E[X|Y]] = E[X]. The unconditional expectation equals the expectation of the conditional expectation.",
        "url": "https://statlect.com/fundamentals-of-probability/conditional-expectation"
    },
    
    # ─── Distribuciones de Probabilidad ────────────────────────────────────────
    "dist_chi_square": {
        "type": "Model",
        "name": "Chi-Square Distribution",
        "description": "Distribution of a sum of squared standard normal variables. Used in hypothesis testing and confidence intervals.",
        "url": "https://statlect.com/probability-distributions/chi-square-distribution"
    },
    "dist_f_distribution": {
        "type": "Model",
        "name": "F Distribution",
        "description": "Ratio of two chi-square variables divided by their degrees of freedom. Used in ANOVA and regression F-tests.",
        "url": "https://statlect.com/probability-distributions/F-distribution"
    },
    "dist_t_distribution": {
        "type": "Model",
        "name": "Student's t Distribution",
        "description": "Distribution of sample mean when population variance is unknown. Heavier tails than normal.",
        "url": "https://statlect.com/probability-distributions/student-t-distribution"
    },
    "dist_gamma": {
        "type": "Model",
        "name": "Gamma Distribution",
        "description": "Continuous distribution with shape and rate parameters. Generalizes exponential and chi-square.",
        "url": "https://statlect.com/probability-distributions/gamma-distribution"
    },
    "dist_beta": {
        "type": "Model",
        "name": "Beta Distribution",
        "description": "Continuous distribution on [0,1]. Used to model uncertainty about probabilities. Conjugate prior for binomial.",
        "url": "https://statlect.com/probability-distributions/beta-distribution"
    },
    "dist_multivariate_normal": {
        "type": "Model",
        "name": "Multivariate Normal Distribution",
        "description": "Generalization of normal to multiple dimensions. Characterized by mean vector and covariance matrix.",
        "url": "https://statlect.com/probability-distributions/multivariate-normal-distribution"
    },
    
    # ─── Teoría Asintótica ─────────────────────────────────────────────────────
    "concept_convergence_probability": {
        "type": "Concept",
        "name": "Convergence in Probability",
        "description": "A sequence Xn converges in probability to X if P(|Xn - X| > ε) → 0 for all ε > 0.",
        "url": "https://statlect.com/asymptotic-theory/convergence-in-probability"
    },
    "concept_convergence_distribution": {
        "type": "Concept",
        "name": "Convergence in Distribution",
        "description": "Weakest form of stochastic convergence. Fn(x) → F(x) at all continuity points of F.",
        "url": "https://statlect.com/asymptotic-theory/convergence-in-distribution"
    },
    "concept_almost_sure_convergence": {
        "type": "Concept",
        "name": "Almost Sure Convergence",
        "description": "Strongest form of convergence. P(Xn → X) = 1. Implies convergence in probability.",
        "url": "https://statlect.com/asymptotic-theory/almost-sure-convergence"
    },
    "theorem_clt": {
        "type": "Concept",
        "name": "Central Limit Theorem (CLT)",
        "description": "Sample mean of iid variables converges in distribution to normal as n→∞, regardless of original distribution.",
        "url": "https://statlect.com/asymptotic-theory/central-limit-theorem"
    },
    "theorem_lln": {
        "type": "Concept",
        "name": "Law of Large Numbers (LLN)",
        "description": "Sample mean converges to population mean as sample size increases. Weak LLN: in probability. Strong LLN: almost surely.",
        "url": "https://statlect.com/asymptotic-theory/law-of-large-numbers"
    },
    "concept_slutsky_theorem": {
        "type": "Concept",
        "name": "Slutsky's Theorem",
        "description": "If Xn →d X and Yn →p c, then Xn + Yn →d X + c and XnYn →d cX. Key for asymptotic inference.",
        "url": "https://statlect.com/asymptotic-theory/Slutsky-theorem"
    },
    "concept_delta_method": {
        "type": "Concept",
        "name": "Delta Method",
        "description": "Technique to derive asymptotic distribution of g(Xn) from that of Xn using Taylor expansion.",
        "url": "https://statlect.com/asymptotic-theory/delta-method"
    },
    
    # ─── Estimación ────────────────────────────────────────────────────────────
    "concept_point_estimation": {
        "type": "Concept",
        "name": "Point Estimation",
        "description": "Using sample data to compute a single value (estimate) as best guess for unknown parameter.",
        "url": "https://statlect.com/fundamentals-of-statistics/point-estimation"
    },
    "concept_interval_estimation": {
        "type": "Concept",
        "name": "Interval Estimation",
        "description": "Constructing an interval that contains the true parameter with specified probability (confidence level).",
        "url": "https://statlect.com/fundamentals-of-statistics/interval-estimation"
    },
    "concept_unbiasedness": {
        "type": "Concept",
        "name": "Unbiasedness",
        "description": "An estimator is unbiased if E[θ̂] = θ. Its expected value equals the true parameter.",
        "url": "https://statlect.com/fundamentals-of-statistics/point-estimation"
    },
    "concept_consistency": {
        "type": "Concept",
        "name": "Consistency",
        "description": "An estimator is consistent if it converges in probability to the true parameter as n→∞.",
        "url": "https://statlect.com/fundamentals-of-statistics/consistent-estimator"
    },
    "concept_efficiency_estimator": {
        "type": "Concept",
        "name": "Efficiency (Estimator)",
        "description": "An efficient estimator achieves the Cramér-Rao lower bound. Has minimum variance among unbiased estimators.",
        "url": "https://statlect.com/fundamentals-of-statistics/efficient-estimator"
    },
    "concept_cramer_rao_bound": {
        "type": "Concept",
        "name": "Cramér-Rao Lower Bound",
        "description": "Lower bound on variance of any unbiased estimator: Var(θ̂) ≥ 1/I(θ), where I is Fisher information.",
        "url": "https://statlect.com/fundamentals-of-statistics/Cramer-Rao-bound"
    },
    "concept_fisher_information": {
        "type": "Concept",
        "name": "Fisher Information",
        "description": "Measure of information a sample carries about parameter θ. I(θ) = E[(∂logL/∂θ)²].",
        "url": "https://statlect.com/fundamentals-of-statistics/Fisher-information"
    },
    
    # ─── Maximum Likelihood ────────────────────────────────────────────────────
    "estimator_mle": {
        "type": "Estimator",
        "name": "Maximum Likelihood Estimator (MLE)",
        "description": "Estimator that maximizes the likelihood function. Consistent, asymptotically normal, and efficient.",
        "url": "https://statlect.com/fundamentals-of-statistics/maximum-likelihood"
    },
    "concept_likelihood_function": {
        "type": "Concept",
        "name": "Likelihood Function",
        "description": "L(θ|x) = f(x|θ). Probability of observed data as function of parameters. Not a probability distribution.",
        "url": "https://statlect.com/fundamentals-of-statistics/maximum-likelihood"
    },
    "concept_log_likelihood": {
        "type": "Concept",
        "name": "Log-Likelihood",
        "description": "Natural logarithm of likelihood. Easier to maximize and sum across observations.",
        "url": "https://statlect.com/fundamentals-of-statistics/maximum-likelihood"
    },
    "concept_score_function": {
        "type": "Concept",
        "name": "Score Function",
        "description": "Gradient of log-likelihood with respect to parameters. S(θ) = ∂logL/∂θ. Zero at MLE.",
        "url": "https://statlect.com/fundamentals-of-statistics/score-function"
    },
    "concept_hessian_matrix": {
        "type": "Concept",
        "name": "Hessian Matrix",
        "description": "Matrix of second derivatives of log-likelihood. Used for asymptotic variance and Newton-Raphson.",
        "url": "https://statlect.com/fundamentals-of-statistics/maximum-likelihood"
    },
    
    # ─── Tests de Hipótesis ────────────────────────────────────────────────────
    "test_likelihood_ratio": {
        "type": "Test",
        "name": "Likelihood Ratio Test (LRT)",
        "description": "Test based on ratio of restricted to unrestricted likelihood. -2log(LR) ~ χ² under H0.",
        "url": "https://statlect.com/fundamentals-of-statistics/likelihood-ratio-test"
    },
    "test_wald": {
        "type": "Test",
        "name": "Wald Test",
        "description": "Test using only unrestricted estimates. (θ̂ - θ0)'V⁻¹(θ̂ - θ0) ~ χ² under H0.",
        "url": "https://statlect.com/fundamentals-of-statistics/Wald-test"
    },
    "test_score": {
        "type": "Test",
        "name": "Score Test (Lagrange Multiplier)",
        "description": "Test using only restricted estimates. Based on score evaluated at restricted MLE.",
        "url": "https://statlect.com/fundamentals-of-statistics/score-test"
    },
    "concept_test_size": {
        "type": "Concept",
        "name": "Size of a Test",
        "description": "Probability of Type I error (rejecting H0 when true). α = P(reject H0 | H0 true).",
        "url": "https://statlect.com/fundamentals-of-statistics/hypothesis-testing"
    },
    "concept_test_power": {
        "type": "Concept",
        "name": "Power of a Test",
        "description": "Probability of correctly rejecting H0. Power = 1 - β = P(reject H0 | H1 true).",
        "url": "https://statlect.com/fundamentals-of-statistics/hypothesis-testing"
    },
    "concept_p_value": {
        "type": "Concept",
        "name": "P-Value",
        "description": "Probability of observing test statistic as extreme as observed, assuming H0 is true.",
        "url": "https://statlect.com/fundamentals-of-statistics/hypothesis-testing"
    },
    
    # ─── Regresión Lineal ──────────────────────────────────────────────────────
    "concept_gauss_markov": {
        "type": "Concept",
        "name": "Gauss-Markov Theorem",
        "description": "Under classical assumptions, OLS is BLUE (Best Linear Unbiased Estimator).",
        "url": "https://statlect.com/fundamentals-of-statistics/Gauss-Markov-theorem"
    },
    "estimator_gls": {
        "type": "Estimator",
        "name": "Generalized Least Squares (GLS)",
        "description": "Efficient estimation when errors are heteroskedastic or correlated. Transforms model by Ω^(-1/2).",
        "url": "https://statlect.com/fundamentals-of-statistics/generalized-least-squares"
    },
    "estimator_fgls": {
        "type": "Estimator",
        "name": "Feasible GLS (FGLS)",
        "description": "GLS with estimated covariance matrix. Consistent but generally not efficient in finite samples.",
        "url": "https://statlect.com/fundamentals-of-statistics/generalized-least-squares"
    },
    "concept_multicollinearity": {
        "type": "Concept",
        "name": "Multicollinearity",
        "description": "High correlation among regressors. Causes imprecise coefficient estimates (large standard errors).",
        "url": "https://statlect.com/fundamentals-of-statistics/multicollinearity"
    },
    "estimator_ridge": {
        "type": "Estimator",
        "name": "Ridge Regression",
        "description": "Biased estimator that adds penalty λ||β||² to OLS objective. Reduces variance, can lower MSE.",
        "url": "https://statlect.com/fundamentals-of-statistics/ridge-regression"
    },
    "concept_dummy_variables": {
        "type": "Concept",
        "name": "Dummy Variables",
        "description": "Binary variables (0/1) used to encode categorical features in regression models.",
        "url": "https://statlect.com/fundamentals-of-statistics/dummy-variables"
    },
    
    # ─── Modelos de Clasificación ──────────────────────────────────────────────
    "model_logit": {
        "type": "Model",
        "name": "Logit Model",
        "description": "Binary classification model. P(Y=1|X) = 1/(1+exp(-Xβ)). Estimated by MLE.",
        "url": "https://statlect.com/fundamentals-of-statistics/logit-model"
    },
    "model_probit": {
        "type": "Model",
        "name": "Probit Model",
        "description": "Binary classification using normal CDF. P(Y=1|X) = Φ(Xβ). Alternative to logit.",
        "url": "https://statlect.com/fundamentals-of-statistics/probit-model"
    },
    
    # ─── Estadística Bayesiana ─────────────────────────────────────────────────
    "concept_bayesian_inference": {
        "type": "Concept",
        "name": "Bayesian Inference",
        "description": "Updating beliefs about parameters using Bayes' rule: posterior ∝ likelihood × prior.",
        "url": "https://statlect.com/fundamentals-of-statistics/Bayesian-inference"
    },
    "concept_prior_distribution": {
        "type": "Concept",
        "name": "Prior Distribution",
        "description": "Probability distribution representing beliefs about parameter before observing data.",
        "url": "https://statlect.com/fundamentals-of-statistics/Bayesian-inference"
    },
    "concept_posterior_distribution": {
        "type": "Concept",
        "name": "Posterior Distribution",
        "description": "Updated probability distribution of parameter after observing data. Combines prior and likelihood.",
        "url": "https://statlect.com/fundamentals-of-statistics/Bayesian-inference"
    },
    "concept_conjugate_prior": {
        "type": "Concept",
        "name": "Conjugate Prior",
        "description": "Prior that yields posterior in same parametric family. Simplifies Bayesian computation.",
        "url": "https://statlect.com/fundamentals-of-statistics/conjugate-prior"
    },
    "technique_mcmc": {
        "type": "Technique",
        "name": "Markov Chain Monte Carlo (MCMC)",
        "description": "Algorithms to sample from posterior distributions. Includes Gibbs sampling, Metropolis-Hastings.",
        "url": "https://statlect.com/fundamentals-of-statistics/Markov-Chain-Monte-Carlo"
    },
    
    # ─── Series de Tiempo ──────────────────────────────────────────────────────
    "concept_stationarity": {
        "type": "Concept",
        "name": "Stationarity",
        "description": "Time series property where distribution doesn't change over time. Strict vs weak (covariance) stationarity.",
        "url": "https://statlect.com/time-series-analysis/stationarity"
    },
    "concept_autocorrelation": {
        "type": "Concept",
        "name": "Autocorrelation Function (ACF)",
        "description": "Correlation of time series with its own lagged values. ρ(k) = Cov(Xt, Xt-k)/Var(Xt).",
        "url": "https://statlect.com/time-series-analysis/autocorrelation"
    },
    "concept_markov_chain": {
        "type": "Concept",
        "name": "Markov Chain",
        "description": "Stochastic process where future depends only on present, not past. Memoryless property.",
        "url": "https://statlect.com/time-series-analysis/Markov-chains"
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# RELACIONES ENTRE CONCEPTOS DE STATLECT Y ENTIDADES EXISTENTES
# ═══════════════════════════════════════════════════════════════════════════════

STATLECT_RELATIONS = [
    # ─── Convergencia y Teoremas Límite ────────────────────────────────────────
    ("concept_convergence_probability", "concept_convergence_distribution", "implies"),
    ("concept_almost_sure_convergence", "concept_convergence_probability", "implies"),
    ("theorem_clt", "concept_convergence_distribution", "uses"),
    ("theorem_clt", "dist_normal", "converges_to"),
    ("theorem_lln", "concept_convergence_probability", "uses"),
    ("concept_slutsky_theorem", "concept_convergence_distribution", "extends"),
    ("concept_delta_method", "theorem_clt", "uses"),
    
    # ─── Distribuciones ────────────────────────────────────────────────────────
    ("dist_chi_square", "dist_normal", "derived_from"),
    ("dist_f_distribution", "dist_chi_square", "derived_from"),
    ("dist_t_distribution", "dist_normal", "derived_from"),
    ("dist_t_distribution", "dist_chi_square", "uses"),
    ("dist_gamma", "dist_exponential", "generalizes"),
    ("dist_chi_square", "dist_gamma", "special_case_of"),
    ("dist_beta", "dist_uniform", "generalizes"),
    ("dist_multivariate_normal", "dist_normal", "generalizes"),
    
    # ─── Estimación ────────────────────────────────────────────────────────────
    ("concept_point_estimation", "concept_interval_estimation", "related_to"),
    ("concept_unbiasedness", "concept_point_estimation", "property_of"),
    ("concept_consistency", "concept_point_estimation", "property_of"),
    ("concept_efficiency_estimator", "concept_point_estimation", "property_of"),
    ("concept_cramer_rao_bound", "concept_efficiency_estimator", "defines"),
    ("concept_fisher_information", "concept_cramer_rao_bound", "used_in"),
    
    # ─── Maximum Likelihood ────────────────────────────────────────────────────
    ("estimator_mle", "concept_likelihood_function", "maximizes"),
    ("concept_log_likelihood", "concept_likelihood_function", "transformation_of"),
    ("concept_score_function", "concept_log_likelihood", "derivative_of"),
    ("concept_hessian_matrix", "concept_log_likelihood", "second_derivative_of"),
    ("estimator_mle", "concept_consistency", "has_property"),
    ("estimator_mle", "concept_efficiency_estimator", "achieves"),
    ("concept_fisher_information", "concept_hessian_matrix", "related_to"),
    
    # ─── Tests de Hipótesis ────────────────────────────────────────────────────
    ("test_likelihood_ratio", "estimator_mle", "uses"),
    ("test_wald", "estimator_mle", "uses"),
    ("test_score", "concept_score_function", "uses"),
    ("test_likelihood_ratio", "dist_chi_square", "converges_to"),
    ("test_wald", "dist_chi_square", "converges_to"),
    ("test_score", "dist_chi_square", "converges_to"),
    ("concept_test_power", "concept_test_size", "tradeoff_with"),
    ("concept_p_value", "concept_test_size", "related_to"),
    
    # ─── Regresión ─────────────────────────────────────────────────────────────
    ("concept_gauss_markov", "estimator_ols", "applies_to"),
    ("estimator_gls", "estimator_ols", "generalizes"),
    ("estimator_fgls", "estimator_gls", "approximates"),
    ("estimator_ridge", "estimator_ols", "alternative_to"),
    ("concept_multicollinearity", "estimator_ridge", "motivates"),
    ("concept_dummy_variables", "model_linear_regression", "used_in"),
    
    # ─── Clasificación ─────────────────────────────────────────────────────────
    ("model_logit", "estimator_mle", "estimated_by"),
    ("model_probit", "estimator_mle", "estimated_by"),
    ("model_logit", "model_probit", "alternative_to"),
    
    # ─── Bayesiana ─────────────────────────────────────────────────────────────
    ("concept_bayesian_inference", "concept_prior_distribution", "uses"),
    ("concept_bayesian_inference", "concept_posterior_distribution", "produces"),
    ("concept_posterior_distribution", "concept_likelihood_function", "uses"),
    ("concept_conjugate_prior", "concept_prior_distribution", "type_of"),
    ("technique_mcmc", "concept_posterior_distribution", "samples_from"),
    ("technique_mcmc", "concept_markov_chain", "uses"),
    
    # ─── Series de Tiempo ──────────────────────────────────────────────────────
    ("concept_autocorrelation", "concept_stationarity", "assumes"),
    ("concept_markov_chain", "concept_stationarity", "related_to"),
    
    # ─── Conexiones con entidades existentes ───────────────────────────────────
    ("theorem_clt", "concept_asymptotic_normality", "related_to"),
    ("theorem_lln", "concept_sample_mean", "applies_to"),
    ("estimator_mle", "model_linear_regression", "applies_to"),
    ("test_wald", "test_t", "related_to"),
    ("test_likelihood_ratio", "test_f", "related_to"),
    ("concept_gauss_markov", "assumption_homoscedasticity", "requires"),
    ("concept_gauss_markov", "assumption_no_multicollinearity", "requires"),
    ("dist_chi_square", "test_chi_square", "used_in"),
    ("dist_f_distribution", "test_f", "used_in"),
    ("dist_t_distribution", "test_t", "used_in"),
    ("concept_conditional_expectation", "model_regression", "fundamental_to"),
    ("concept_law_iterated_expectations", "concept_conditional_expectation", "property_of"),
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


def enrich_from_statlect():
    """Enriquece la ontología con conocimiento de Statlect."""
    
    print("=" * 70)
    print("NEVEN Statlect Enricher")
    print("Fuente: https://statlect.com/")
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
    print(f"\n[1/2] Creando entidades de Statlect...")
    
    for entity_id, entity_data in STATLECT_ENTITIES.items():
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
                    "source": "Statlect",
                    "url": entity_data["url"]
                }
            }
        }
        new_entries.append(entry)
        existing_entities.add(entity_id)  # Para las relaciones
        stats["entities_created"] += 1
        print(f"  + {entity_id}: {entity_data['name']}")
    
    # ─── Crear relaciones ──────────────────────────────────────────────────────
    print(f"\n[2/2] Creando relaciones...")
    
    for source, target, rel_type in STATLECT_RELATIONS:
        # Verificar que ambos nodos existen
        if source not in existing_entities:
            stats["relations_skipped_no_target"] += 1
            continue
        if target not in existing_entities:
            stats["relations_skipped_no_target"] += 1
            continue
        
        # Verificar que la relación no existe
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
    enrich_from_statlect()
