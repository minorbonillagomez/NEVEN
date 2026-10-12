/**
 * @file fit_service.cc
 * @brief FitService implementation — distribution fitting via R.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include "fit_service.h"
#include "sim_bridge.h"
#include "json11/json11.hpp"
#include <sstream>
#include <algorithm>
#include <string>

namespace neven_sim {

bool FitService::FitDistributions(const std::vector<double>& data,
                                   std::vector<FitResult>& results) {
    if (data.size() < 10) return false; // Need minimum data points

    std::string r_code = GenerateFitCode(data);
    std::string response = SimBridge::Instance().CallR(r_code);

    if (response.find("[ERROR]") == 0) return false;

    return ParseFitResults(response, results);
}

bool FitService::FitSpecific(const std::vector<double>& data,
                              const std::string& dist_name,
                              FitResult& result) {
    if (data.size() < 10) return false;

    std::ostringstream ss;
    ss << "tryCatch({"
       << "d <- c(";
    for (size_t i = 0; i < data.size(); i++) {
        if (i > 0) ss << ",";
        ss << data[i];
    }
    ss << "); "
       << "fit <- fitdistrplus::fitdist(d, '" << dist_name << "'); "
       << "gof <- fitdistrplus::gofstat(fit); "
       << "paste('" << dist_name << "', "
       << "paste(names(fit$estimate), fit$estimate, sep='=', collapse=','), "
       << "fit$aic, gof$ks, sep='|')"
       << "}, error=function(e) paste('[ERROR]', e$message))";

    std::string response = SimBridge::Instance().CallR(ss.str());
    if (response.find("[ERROR]") == 0) return false;

    // Parse: "dist_name|param1=val1,param2=val2|aic|ks"
    // Simplified parsing for single-dist result
    result.dist_name = dist_name;
    // Full parsing would extract params from response
    return true;
}

bool FitService::CheckDependencies() {
    std::string result = SimBridge::Instance().CallR(
        "if(requireNamespace('fitdistrplus', quietly=TRUE)) 'OK' else 'NO'"
    );
    return result == "OK";
}

std::string FitService::GenerateFitCode(const std::vector<double>& data) {
    std::ostringstream ss;

    // Build R code that fits multiple distributions and returns JSON
    ss << "tryCatch({"
       << "if(!requireNamespace('fitdistrplus',quietly=TRUE)) stop('fitdistrplus no instalado'); ";

    // Check if jsonlite is available, otherwise return structured text
    ss << "has_json <- requireNamespace('jsonlite', quietly=TRUE); ";

    // Inject data vector
    ss << "data_vec <- c(";
    for (size_t i = 0; i < data.size(); i++) {
        if (i > 0) ss << ",";
        ss << data[i];
    }
    ss << "); ";

    // Only fit distributions valid for the data
    ss << "candidates <- c('norm','lnorm','gamma','weibull','exp','unif'); ";
    
    // Add beta only if data is in [0,1]
    ss << "if(min(data_vec)>=0 && max(data_vec)<=1) candidates <- c(candidates,'beta'); ";

    // Filter: lognorm/gamma/weibull need positive data
    ss << "if(min(data_vec)<=0) candidates <- setdiff(candidates, c('lnorm','gamma','weibull')); ";

    ss << "results <- list(); ";
    ss << "for(dist in candidates) { ";
    ss << "  tryCatch({ ";
    ss << "    fit <- fitdistrplus::fitdist(data_vec, dist); ";
    ss << "    gof <- fitdistrplus::gofstat(fit); ";
    ss << "    results[[dist]] <- list( ";
    ss << "      params=as.list(fit$estimate), ";
    ss << "      aic=fit$aic, ";
    ss << "      ks_stat=gof$ks, ";
    ss << "      ad_stat=ifelse(is.null(gof$ad), NA, gof$ad) ";
    ss << "    ); ";
    ss << "  }, error=function(e) NULL) ";
    ss << "}; ";

    // Return as JSON if possible, otherwise structured text
    ss << "if(has_json) { ";
    ss << "  jsonlite::toJSON(results, auto_unbox=TRUE) ";
    ss << "} else { ";
    ss << "  paste(sapply(names(results), function(n) { ";
    ss << "    r <- results[[n]]; ";
    ss << "    paste(n, paste(names(r$params), r$params, sep='=', collapse=','), ";
    ss << "          r$aic, r$ks_stat, sep='|') ";
    ss << "  }), collapse=';;') ";
    ss << "}";

    ss << "}, error=function(e) paste('[ERROR]', e$message))";

    return ss.str();
}

bool FitService::ParseFitResults(const std::string& json_str,
                                  std::vector<FitResult>& results) {
    results.clear();

    // Reject error strings immediately
    if (json_str.find("[ERROR]") != std::string::npos) return false;
    if (json_str.empty()) return false;

    // Try JSON parsing first
    std::string err;
    json11::Json json = json11::Json::parse(json_str, err);

    if (!err.empty() || !json.is_object()) {
        // Fallback: parse structured text format "dist|params|aic|ks;;..."
        std::istringstream stream(json_str);
        std::string entry;
        while (std::getline(stream, entry, ';')) {
            if (entry.empty() || entry == ";") continue;
            // Parse "norm|mean=5.2,sd=1.3|2340.5|0.04"
            std::istringstream es(entry);
            std::string dist, params, aic_str, ks_str;
            std::getline(es, dist, '|');
            std::getline(es, params, '|');
            std::getline(es, aic_str, '|');
            std::getline(es, ks_str, '|');

            FitResult fr;
            fr.dist_name = dist;
            try { fr.aic = std::stod(aic_str); } catch (...) {}
            try { fr.ks_p = std::stod(ks_str); } catch (...) {}
            
            // Parse params "mean=5.2,sd=1.3"
            std::istringstream ps(params);
            std::string param;
            int param_idx = 0;
            while (std::getline(ps, param, ',')) {
                auto eq = param.find('=');
                if (eq != std::string::npos) {
                    double val = 0;
                    try { val = std::stod(param.substr(eq + 1)); } catch (...) {}
                    if (param_idx == 0) fr.param1 = val;
                    else if (param_idx == 1) fr.param2 = val;
                    param_idx++;
                }
            }
            results.push_back(fr);
        }
    } else {
        // JSON format from jsonlite
        for (auto& item : json.object_items()) {
            FitResult fr;
            fr.dist_name = item.first;
            auto& val = item.second;
            
            fr.aic = val["aic"].number_value();
            fr.ks_p = val["ks_stat"].number_value();
            fr.ad_p = val["ad_stat"].number_value();

            auto params = val["params"];
            if (params.is_object()) {
                auto items = params.object_items();
                int idx = 0;
                for (auto& p : items) {
                    if (idx == 0) fr.param1 = p.second.number_value();
                    else if (idx == 1) fr.param2 = p.second.number_value();
                    idx++;
                }
            }

            results.push_back(fr);
        }
    }

    // Sort by AIC (lower is better)
    std::sort(results.begin(), results.end(),
        [](const FitResult& a, const FitResult& b) { return a.aic < b.aic; });

    return !results.empty();
}

} // namespace neven_sim
