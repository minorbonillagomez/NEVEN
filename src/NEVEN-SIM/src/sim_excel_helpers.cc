/**
 * @file sim_excel_helpers.cc
 * @brief Excel data extraction and fitting helpers for NEVEN-SIM.
 *
 * Copyright (c) 2026 NEVEN Project — GPL v3
 */

#include <windows.h>
#undef ERROR

#include "sim_excel_helpers.h"
#include "fit_service.h"
#include <sstream>
#include <iomanip>

// Excel12 functions (from xlcall_stubs.cc)
extern "C" int pascal Excel12(int xlfn, LPXLOPER12 operRes, int count, ...);

namespace neven_sim {

bool ExtractRangeData(LPXLOPER12 pxRange, std::vector<double>& values) {
    values.clear();

    if (!pxRange) return false;

    // If it's already a multi-cell array
    if (pxRange->xltype == xltypeMulti) {
        int count = pxRange->val.array.rows * pxRange->val.array.columns;
        for (int i = 0; i < count; i++) {
            XLOPER12& cell = pxRange->val.array.lparray[i];
            if (cell.xltype == xltypeNum) {
                values.push_back(cell.val.num);
            } else if (cell.xltype == xltypeInt) {
                values.push_back((double)cell.val.w);
            }
            // Skip strings, errors, blanks
        }
        return !values.empty();
    }

    // If it's a single number
    if (pxRange->xltype == xltypeNum) {
        values.push_back(pxRange->val.num);
        return true;
    }

    if (pxRange->xltype == xltypeInt) {
        values.push_back((double)pxRange->val.w);
        return true;
    }

    // If it's a reference, try to coerce to multi
    if (pxRange->xltype == xltypeSRef || pxRange->xltype == xltypeRef) {
        XLOPER12 xlMulti;
        memset(&xlMulti, 0, sizeof(xlMulti));

        // Coerce reference to multi-cell array
        XLOPER12 xlType;
        xlType.xltype = xltypeInt;
        xlType.val.w = xltypeMulti;

        int err = Excel12(xlCoerce, &xlMulti, 2, pxRange, &xlType);
        if (err == 0 && xlMulti.xltype == xltypeMulti) {
            int count = xlMulti.val.array.rows * xlMulti.val.array.columns;
            for (int i = 0; i < count; i++) {
                XLOPER12& cell = xlMulti.val.array.lparray[i];
                if (cell.xltype == xltypeNum) {
                    values.push_back(cell.val.num);
                } else if (cell.xltype == xltypeInt) {
                    values.push_back((double)cell.val.w);
                }
            }
            // Free the coerced result
            XLOPER12 xlFreeType;
            xlFreeType.xltype = xltypeInt;
            xlFreeType.val.w = 0;
            Excel12(xlFree, 0, 1, &xlMulti);
        }
        return !values.empty();
    }

    return false;
}

std::string FitRangeData(LPXLOPER12 pxRange, LPXLOPER12 pxDist) {
    // Extract data from range
    std::vector<double> data;
    if (!ExtractRangeData(pxRange, data)) {
        return "Error: No se pudieron extraer datos del rango";
    }

    if (data.size() < 10) {
        return "Error: Se necesitan al menos 10 datos (tiene " + std::to_string(data.size()) + ")";
    }

    // Check if a specific distribution was requested
    std::string specific_dist;
    if (pxDist && pxDist->xltype == xltypeStr && pxDist->val.str) {
        int len = pxDist->val.str[0];
        if (len > 0) {
            std::wstring ws(pxDist->val.str + 1, len);
            specific_dist.resize(len);
            for (int i = 0; i < len; i++) specific_dist[i] = (char)ws[i];
        }
    }

    if (!specific_dist.empty()) {
        // Fit a specific distribution
        FitResult result;
        if (FitService::FitSpecific(data, specific_dist, result)) {
            std::ostringstream ss;
            ss << result.dist_name << ": param1=" << std::fixed << std::setprecision(4) << result.param1
               << ", param2=" << result.param2 << " | AIC=" << std::setprecision(1) << result.aic;
            return ss.str();
        }
        return "Error: No se pudo ajustar " + specific_dist;
    }

    // Fit all candidates
    std::vector<FitResult> results;
    if (!FitService::FitDistributions(data, results)) {
        return "Error: Fitting fallo. Verifique que R tiene fitdistrplus instalado.";
    }

    if (results.empty()) {
        return "Error: Ninguna distribucion ajusto los datos";
    }

    // Format: "Best: Normal(μ=5.2, σ=1.3) AIC=2340 | 2nd: Gamma(...) | ..."
    std::ostringstream ss;
    for (size_t i = 0; i < results.size() && i < 3; i++) {
        if (i > 0) ss << " | ";
        if (i == 0) ss << "Mejor: ";
        else ss << (i + 1) << ": ";
        ss << results[i].dist_name
           << "(p1=" << std::fixed << std::setprecision(3) << results[i].param1
           << ", p2=" << results[i].param2 << ")"
           << " AIC=" << std::setprecision(0) << results[i].aic;
    }

    // Also add the best fit to the engine's first assumption (if workspace is configuring)
    // This enables =SIM.Fit(A1:A100) followed by =SIM.Run() workflow

    return ss.str();
}

} // namespace neven_sim
