# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN-SIM: Monte Carlo Simulation Module for Julia
# ═══════════════════════════════════════════════════════════════════════════════
#
# Provides distribution sampling, Monte Carlo simulation, and sensitivity analysis.
# Loaded by NEVEN-SIM.xll into the Julia runtime managed by NEVEN base.
#
# Required packages: Distributions.jl (install via =J.Instalar("Distributions"))
# Optional packages: Copulas.jl (Phase 2)
#
# Copyright (c) 2026 NEVEN Project — GPL v3

module NEVENSim

using Distributions
using Random
import Statistics: mean, std, cor

export Assumption, run_montecarlo, summary_stats, sensitivity_analysis, histogram_bins

"""
    Assumption(name, dist)

A simulation input variable with a name and a probability distribution.
"""
struct Assumption
    name::String
    dist::Distribution
end

"""
    run_montecarlo(assumptions, model_func, n_iterations; seed=42)

Run a Monte Carlo simulation.

# Arguments
- `assumptions::Vector{Assumption}`: Input distributions
- `model_func::Function`: Model function f(x1, x2, ..., xn) → output
- `n_iterations::Int`: Number of random samples
- `seed::Int`: Random seed for reproducibility

# Returns
Named tuple `(samples, results)`:
- `samples::Matrix{Float64}`: n_iterations × n_variables matrix
- `results::Vector{Float64}`: model output for each iteration
"""
function run_montecarlo(assumptions::Vector{Assumption},
                        model_func::Function,
                        n_iterations::Int;
                        seed::Int=42)
    rng = MersenneTwister(seed)
    n_vars = length(assumptions)

    # Generate samples from each distribution
    samples = Matrix{Float64}(undef, n_iterations, n_vars)
    for (j, a) in enumerate(assumptions)
        samples[:, j] = rand(rng, a.dist, n_iterations)
    end

    # Evaluate model for each iteration
    results = Vector{Float64}(undef, n_iterations)
    for i in 1:n_iterations
        results[i] = model_func(ntuple(j -> samples[i, j], n_vars)...)
    end

    # Store globally for sensitivity analysis
    global _sim_samples = samples
    global _sim_results = results

    return (samples=samples, results=results)
end

"""
    summary_stats(results)

Compute summary statistics for simulation results.

# Returns
Named tuple with mean, std, min, max, and percentiles (1,5,10,25,50,75,90,95,99).
"""
function summary_stats(results::Vector{Float64})
    sorted = sort(results)
    n = length(sorted)

    function pct(p)
        idx = max(1, Int(ceil(p / 100 * n)))
        return sorted[idx]
    end

    return (
        mean = mean(results),
        std = std(results),
        min = minimum(results),
        max = maximum(results),
        n = n,
        p1 = pct(1),
        p5 = pct(5),
        p10 = pct(10),
        p25 = pct(25),
        p50 = pct(50),
        p75 = pct(75),
        p90 = pct(90),
        p95 = pct(95),
        p99 = pct(99)
    )
end

"""
    sensitivity_analysis(assumptions, samples, results)

Compute Spearman rank correlation between each input and the output.
Returns a vector of (name, rho, contribution%) tuples.
"""
function sensitivity_analysis(assumptions::Vector{Assumption},
                               samples::Matrix{Float64},
                               results::Vector{Float64})
    n_vars = length(assumptions)

    # Rank-based correlation (Spearman)
    function rank_vec(x)
        sorted_indices = sortperm(x)
        ranks = similar(x, Float64)
        for (r, i) in enumerate(sorted_indices)
            ranks[i] = Float64(r)
        end
        return ranks
    end

    r_results = rank_vec(results)
    rho = Float64[]

    for j in 1:n_vars
        r_samples = rank_vec(samples[:, j])
        push!(rho, cor(r_samples, r_results))
    end

    # Contribution percentages
    sum_rho2 = sum(rho .^ 2)
    contributions = sum_rho2 > 0 ? (rho .^ 2) ./ sum_rho2 : zeros(n_vars)

    return [(name=assumptions[i].name, rho=rho[i], contribution=contributions[i]) for i in 1:n_vars]
end

"""
    histogram_bins(results, n_bins=50)

Compute histogram bins and counts for Plotly visualization.
Returns (edges, counts) suitable for bar chart plotting.
"""
function histogram_bins(results::Vector{Float64}; n_bins::Int=50)
    mn, mx = extrema(results)
    bin_width = (mx - mn) / n_bins
    edges = [mn + i * bin_width for i in 0:n_bins]
    counts = zeros(Int, n_bins)

    for val in results
        idx = min(n_bins, max(1, Int(floor((val - mn) / bin_width)) + 1))
        counts[idx] += 1
    end

    # Return as string vectors (Excel compatible)
    centers = [(edges[i] + edges[i+1]) / 2 for i in 1:n_bins]
    return (centers=centers, counts=counts)
end

"""
    to_json_summary(stats)

Convert summary_stats output to JSON string for C++ parsing.
"""
function to_json_summary(stats)
    return "{" *
        "\"mean\":$(round(stats.mean, digits=4))," *
        "\"std\":$(round(stats.std, digits=4))," *
        "\"min\":$(round(stats.min, digits=4))," *
        "\"max\":$(round(stats.max, digits=4))," *
        "\"p1\":$(round(stats.p1, digits=4))," *
        "\"p5\":$(round(stats.p5, digits=4))," *
        "\"p10\":$(round(stats.p10, digits=4))," *
        "\"p25\":$(round(stats.p25, digits=4))," *
        "\"p50\":$(round(stats.p50, digits=4))," *
        "\"p75\":$(round(stats.p75, digits=4))," *
        "\"p90\":$(round(stats.p90, digits=4))," *
        "\"p95\":$(round(stats.p95, digits=4))," *
        "\"p99\":$(round(stats.p99, digits=4))" *
        "}"
end

end # module NEVENSim
