/**
 * @file montecarlo_service.cc
 * @brief MonteCarloService implementation — Julia Monte Carlo simulation.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include "montecarlo_service.h"
#include "sim_bridge.h"
#include "json11/json11.hpp"
#include <sstream>
#include <chrono>
#include <algorithm>
#include <cmath>

namespace neven_sim {

bool MonteCarloService::RunSimulation(const std::vector<Assumption>& assumptions,
                                       const std::string& model_function,
                                       int iterations,
                                       SimSummary& summary) {
    if (assumptions.empty()) return false;

    auto start = std::chrono::high_resolution_clock::now();

    std::string julia_code = GenerateSimCode(assumptions, model_function, iterations);
    std::string response = SimBridge::Instance().CallJulia(julia_code);

    auto end = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double, std::milli>(end - start).count();

    if (response.find("[ERROR]") == 0) return false;

    // Parse JSON response from Julia
    std::string err;
    json11::Json json = json11::Json::parse(response, err);
    if (!err.empty() || !json.is_object()) {
        // Try parsing as pipe-separated values (fallback)
        return false;
    }

    summary.mean = json["mean"].number_value();
    summary.std_dev = json["std"].number_value();
    summary.min_val = json["min"].number_value();
    summary.max_val = json["max"].number_value();
    summary.p1 = json["p1"].number_value();
    summary.p5 = json["p5"].number_value();
    summary.p10 = json["p10"].number_value();
    summary.p25 = json["p25"].number_value();
    summary.p50 = json["p50"].number_value();
    summary.p75 = json["p75"].number_value();
    summary.p90 = json["p90"].number_value();
    summary.p95 = json["p95"].number_value();
    summary.p99 = json["p99"].number_value();
    summary.iterations = iterations;
    summary.elapsed_ms = elapsed;

    return true;
}

bool MonteCarloService::ComputeSensitivity(const std::vector<Assumption>& assumptions,
                                            std::vector<SensitivityEntry>& sensitivity) {
    if (assumptions.empty()) return false;

    // Generate Julia code for Spearman correlation computation
    std::ostringstream ss;
    ss << "let\n";
    ss << "  import Statistics: cor\n";
    ss << "  n_vars = " << assumptions.size() << "\n";
    ss << "  # Retrieve samples and results from last simulation\n";
    ss << "  if !isdefined(Main, :_sim_samples) || !isdefined(Main, :_sim_results)\n";
    ss << "    \"[ERROR] No simulation data available\"\n";
    ss << "  else\n";
    ss << "    samples = Main._sim_samples\n";
    ss << "    results = Main._sim_results\n";
    ss << "    # Spearman rank correlation\n";
    ss << "    function rank_vec(x)\n";
    ss << "      sorted_indices = sortperm(x)\n";
    ss << "      ranks = similar(x, Float64)\n";
    ss << "      for (r, i) in enumerate(sorted_indices)\n";
    ss << "        ranks[i] = Float64(r)\n";
    ss << "      end\n";
    ss << "      return ranks\n";
    ss << "    end\n";
    ss << "    rho = Float64[]\n";
    ss << "    r_results = rank_vec(results)\n";
    ss << "    for j in 1:n_vars\n";
    ss << "      r_samples = rank_vec(samples[:, j])\n";
    ss << "      push!(rho, cor(r_samples, r_results))\n";
    ss << "    end\n";
    ss << "    # JSON output\n";
    ss << "    sum_rho2 = sum(rho .^ 2)\n";
    ss << "    contributions = (rho .^ 2) ./ sum_rho2\n";
    ss << "    parts = String[]\n";
    ss << "    names = [";
    for (size_t i = 0; i < assumptions.size(); i++) {
        if (i > 0) ss << ", ";
        ss << "\"" << assumptions[i].name << "\"";
    }
    ss << "]\n";
    ss << "    for i in 1:n_vars\n";
    ss << "      push!(parts, \"{\\\"name\\\":\\\"\" * names[i] * \"\\\",\\\"rho\\\":\" * string(round(rho[i], digits=4)) * \",\\\"contrib\\\":\" * string(round(contributions[i], digits=4)) * \"}\")\n";
    ss << "    end\n";
    ss << "    \"[\" * join(parts, \",\") * \"]\"\n";
    ss << "  end\n";
    ss << "end";

    std::string response = SimBridge::Instance().CallJulia(ss.str());
    if (response.find("[ERROR]") == 0) return false;

    // Parse JSON array
    std::string err;
    json11::Json json = json11::Json::parse(response, err);
    if (!err.empty() || !json.is_array()) return false;

    sensitivity.clear();
    for (auto& item : json.array_items()) {
        SensitivityEntry entry;
        entry.name = item["name"].string_value();
        entry.spearman_rho = item["rho"].number_value();
        entry.contribution = item["contrib"].number_value();
        sensitivity.push_back(entry);
    }

    // Sort by absolute contribution (descending)
    std::sort(sensitivity.begin(), sensitivity.end(),
        [](const SensitivityEntry& a, const SensitivityEntry& b) {
            return std::abs(a.spearman_rho) > std::abs(b.spearman_rho);
        });

    return !sensitivity.empty();
}

bool MonteCarloService::CheckDependencies() {
    std::string result = SimBridge::Instance().CallJulia(
        "try using Distributions; \"OK\" catch; \"NO\" end"
    );
    return result == "OK";
}

bool MonteCarloService::LoadSimModule() {
    auto& bridge = SimBridge::Instance();
    std::string home = bridge.GetHomePath();
    std::string module_path = home + "libreria\\\\JULIA\\\\NEVENSim.jl";
    std::string result = bridge.CallJulia("include(\"" + module_path + "\"); \"OK\"");
    return result == "OK";
}

std::string MonteCarloService::GenerateSimCode(const std::vector<Assumption>& assumptions,
                                                const std::string& model_function,
                                                int iterations) {
    std::ostringstream ss;

    ss << "let\n";
    ss << "  using Distributions, Random\n";
    ss << "  rng = MersenneTwister(42)\n";
    ss << "  n = " << iterations << "\n";
    ss << "  n_vars = " << assumptions.size() << "\n";
    ss << "\n";

    // Define distributions
    ss << "  # Distributions from fitted parameters\n";
    ss << "  dists = [\n";
    for (size_t i = 0; i < assumptions.size(); i++) {
        if (i > 0) ss << ",\n";
        ss << "    " << FitToJuliaDistribution(assumptions[i].best_fit);
    }
    ss << "\n  ]\n\n";

    // Generate samples
    ss << "  # Generate samples matrix (n × n_vars)\n";
    ss << "  samples = Matrix{Float64}(undef, n, n_vars)\n";
    ss << "  for j in 1:n_vars\n";
    ss << "    samples[:, j] = rand(rng, dists[j], n)\n";
    ss << "  end\n\n";

    // Define model function
    ss << "  # User model function\n";
    ss << "  model = " << model_function << "\n\n";

    // Evaluate model
    ss << "  # Evaluate model for all iterations\n";
    ss << "  results = Vector{Float64}(undef, n)\n";
    ss << "  for i in 1:n\n";
    ss << "    results[i] = model(";
    for (size_t i = 0; i < assumptions.size(); i++) {
        if (i > 0) ss << ", ";
        ss << "samples[i, " << (i + 1) << "]";
    }
    ss << ")\n";
    ss << "  end\n\n";

    // Store for sensitivity analysis
    ss << "  # Store globally for sensitivity analysis\n";
    ss << "  global _sim_samples = samples\n";
    ss << "  global _sim_results = results\n\n";

    // Compute summary statistics
    ss << "  # Summary statistics\n";
    ss << "  sorted = sort(results)\n";
    ss << "  function pct(p)\n";
    ss << "    idx = max(1, Int(ceil(p/100*n)))\n";
    ss << "    return sorted[idx]\n";
    ss << "  end\n\n";
    ss << "  import Statistics: mean, std\n";
    ss << "  m = mean(results)\n";
    ss << "  s = std(results)\n\n";

    // Return JSON
    ss << "  # Return as JSON string\n";
    ss << "  \"{\\\"mean\\\":\" * string(round(m, digits=4)) *\n";
    ss << "   \",\\\"std\\\":\" * string(round(s, digits=4)) *\n";
    ss << "   \",\\\"min\\\":\" * string(round(minimum(results), digits=4)) *\n";
    ss << "   \",\\\"max\\\":\" * string(round(maximum(results), digits=4)) *\n";
    ss << "   \",\\\"p1\\\":\" * string(round(pct(1), digits=4)) *\n";
    ss << "   \",\\\"p5\\\":\" * string(round(pct(5), digits=4)) *\n";
    ss << "   \",\\\"p10\\\":\" * string(round(pct(10), digits=4)) *\n";
    ss << "   \",\\\"p25\\\":\" * string(round(pct(25), digits=4)) *\n";
    ss << "   \",\\\"p50\\\":\" * string(round(pct(50), digits=4)) *\n";
    ss << "   \",\\\"p75\\\":\" * string(round(pct(75), digits=4)) *\n";
    ss << "   \",\\\"p90\\\":\" * string(round(pct(90), digits=4)) *\n";
    ss << "   \",\\\"p95\\\":\" * string(round(pct(95), digits=4)) *\n";
    ss << "   \",\\\"p99\\\":\" * string(round(pct(99), digits=4)) *\n";
    ss << "   \"}\"\n";
    ss << "end";

    return ss.str();
}

std::string MonteCarloService::FitToJuliaDistribution(const FitResult& fit) {
    // Map R distribution names to Julia Distributions.jl constructors
    if (fit.dist_name == "norm") {
        return "Normal(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
    } else if (fit.dist_name == "lnorm") {
        return "LogNormal(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
    } else if (fit.dist_name == "gamma") {
        return "Gamma(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
    } else if (fit.dist_name == "weibull") {
        return "Weibull(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
    } else if (fit.dist_name == "exp") {
        return "Exponential(" + std::to_string(fit.param1) + ")";
    } else if (fit.dist_name == "unif") {
        return "Uniform(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
    } else if (fit.dist_name == "beta") {
        return "Beta(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
    }
    // Fallback to Normal
    return "Normal(" + std::to_string(fit.param1) + ", " + std::to_string(fit.param2) + ")";
}

} // namespace neven_sim
