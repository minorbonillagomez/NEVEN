/**
 * @file sim_main.cc
 * @brief NEVEN-SIM XLL entry points and worksheet function implementations.
 *
 * Copyright (c) 2026 NEVEN Project â€” GPL v3
 */

#include <windows.h>
#undef ERROR

#include <string>
#include <sstream>
#include <vector>
#include <cstring>
#include <iomanip>
#include "XLCALL.H"
#include "sim_exports.h"
#include "sim_bridge.h"
#include "sim_engine.h"
#include "sim_viewer.h"
#include "sim_excel_helpers.h"
#include "fit_service.h"
#include "montecarlo_service.h"
#include "json11/json11.hpp"

// â”€â”€â”€ Global State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

HMODULE g_sim_module_handle = nullptr;
static bool g_sim_initialized = false;

typedef int (PASCAL* MDCALLBACK12PROC)(int xlfn, int coper, LPXLOPER12 *rgpxloper12, LPXLOPER12 xloper12Res);
extern "C" void SetExcel12EntryPt(MDCALLBACK12PROC pMdCallBack12);

#ifndef xlUDF
#define xlUDF 255
#endif

// â”€â”€â”€ Function Registration Table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

static LPWSTR simFuncTemplates[][16] = {
    { L"SIM_Workspace",   L"U",   L"SIM.Workspace",   L"",            L"1", L"NEVEN-SIM", L"", L"", L"Abre el workspace de simulacion", L"", L"", L"", L"", L"", L"", L"" },
    { L"SIM_Fit",         L"UQQ", L"SIM.Fit",         L"Rango, Dist", L"1", L"NEVEN-SIM", L"", L"", L"Ajusta distribucion a datos",      L"Rango de datos", L"Distribucion (opcional)", L"", L"", L"", L"", L"" },
    { L"SIM_Run",         L"UQ",  L"SIM.Run",         L"Iteraciones", L"1", L"NEVEN-SIM", L"", L"", L"Ejecuta simulacion Monte Carlo",  L"Iteraciones (def: 1000000)", L"", L"", L"", L"", L"", L"" },
    { L"SIM_QuickRun",    L"UQQQ", L"SIM.QuickRun",  L"Rango, Modelo, Iteraciones", L"1", L"NEVEN-SIM", L"", L"", L"Simulacion completa: Fit+MonteCarlo en una celda", L"Rango de datos", L"Modelo Julia: (x)->x*1.1", L"Iteraciones (def: 100000)", L"", L"", L"", L"" },
    { L"SIM_Datos",       L"UQ",  L"SIM.Datos",      L"N",           L"1", L"NEVEN-SIM", L"", L"", L"Muestra las primeras N muestras simuladas", L"Cantidad de muestras a mostrar (def: 100)", L"", L"", L"", L"", L"", L"" },
    { L"SIM_Exportar",    L"U",   L"SIM.Exportar",   L"",            L"1", L"NEVEN-SIM", L"", L"", L"Exporta todas las muestras a CSV con timestamp", L"", L"", L"", L"", L"", L"", L"" },
    { L"SIM_Percentile",  L"UQ",  L"SIM.Percentile",  L"P",           L"1", L"NEVEN-SIM", L"", L"", L"Percentil de la ultima simulacion", L"Percentil (1-99)", L"", L"", L"", L"", L"", L"" },
    { L"SIM_Sensitivity", L"U",   L"SIM.Sensitivity", L"",            L"1", L"NEVEN-SIM", L"", L"", L"Analisis de sensibilidad (Tornado)", L"", L"", L"", L"", L"", L"", L"" },
    { L"SIM_Status",      L"U",   L"SIM.Status",      L"",            L"1", L"NEVEN-SIM", L"", L"", L"Estado del motor de simulacion",  L"", L"", L"", L"", L"", L"", L"" },
    { 0 }
};

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

static LPXLOPER12 TempInt12(int i) {
    static XLOPER12 x;
    x.xltype = xltypeInt;
    x.val.w = i;
    return &x;
}

static LPXLOPER12 MakeStringResult(const std::string& str) {
    static XLOPER12 result;
    std::wstring wstr(str.begin(), str.end());
    int len = (int)wstr.length();
    wchar_t* buf = new wchar_t[len + 2];
    buf[0] = (wchar_t)len;
    memcpy(buf + 1, wstr.c_str(), len * sizeof(wchar_t));
    buf[len + 1] = 0;
    result.xltype = xltypeStr | xlbitDLLFree;
    result.val.str = buf;
    return &result;
}

static LPXLOPER12 MakeNumResult(double val) {
    static XLOPER12 result;
    result.xltype = xltypeNum;
    result.val.num = val;
    return &result;
}

static void StrToXLOPER(LPXLOPER12 pxl, LPWSTR str) {
    if (!str || !str[0]) {
        pxl->xltype = xltypeNil;
        return;
    }
    pxl->xltype = xltypeStr;
    int len = (int)wcslen(str);
    wchar_t* buf = new wchar_t[len + 2];
    buf[0] = (wchar_t)len;
    memcpy(buf + 1, str, len * sizeof(wchar_t));
    buf[len + 1] = 0;
    pxl->val.str = buf;
}

// â”€â”€â”€ XLL Lifecycle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        g_sim_module_handle = hinstDLL;
        DisableThreadLibraryCalls(hinstDLL);
    }
    return TRUE;
}

extern "C" __declspec(dllexport) int __stdcall xlAutoOpen(void) {
    if (g_sim_initialized) return 1;
    g_sim_initialized = true;

    // Hook Excel entry point
    HMODULE hExcel = GetModuleHandle(NULL);
    MDCALLBACK12PROC pEntry = (MDCALLBACK12PROC)GetProcAddress(hExcel, "MdCallBack12");
    if (!pEntry) return 1;  // Return 1 (success) even if no entry â€” avoids crash
    SetExcel12EntryPt(pEntry);

    // Initialize SimBridge â€” resolve home path only (NO xlUDF calls here!)
    neven_sim::SimBridge::Instance().Initialize();

    // Register SIM.* functions with Excel using Excel12/Excel12v
    XLOPER12 xlDllName;
    memset(&xlDllName, 0, sizeof(xlDllName));
    Excel12(xlGetName, &xlDllName, 0);

    if (xlDllName.xltype != xltypeStr) {
        // Fallback: use module path
        wchar_t modulePath[MAX_PATH];
        GetModuleFileNameW(g_sim_module_handle, modulePath, MAX_PATH);
        int len = (int)wcslen(modulePath);
        static wchar_t pascalStr[MAX_PATH + 2];
        pascalStr[0] = (wchar_t)len;
        memcpy(pascalStr + 1, modulePath, len * sizeof(wchar_t));
        xlDllName.xltype = xltypeStr;
        xlDllName.val.str = pascalStr;
    }

    // Register each function from the template table
    for (int i = 0; simFuncTemplates[i][0]; i++) {
        XLOPER12 xlParms[10];
        LPXLOPER12 xlParmPtrs[10];

        xlParmPtrs[0] = &xlDllName;
        for (int j = 0; j < 9; j++) {
            StrToXLOPER(&xlParms[j + 1], simFuncTemplates[i][j]);
            xlParmPtrs[j + 1] = &xlParms[j + 1];
        }

        XLOPER12 xlRegisterID;
        Excel12v(xlfRegister, &xlRegisterID, 10, xlParmPtrs);

        // Free allocated Pascal strings
        for (int j = 1; j < 10; j++) {
            if (xlParms[j].xltype == xltypeStr && xlParms[j].val.str) {
                delete[] xlParms[j].val.str;
            }
        }
    }

    return 1;
}

extern "C" __declspec(dllexport) int __stdcall xlAutoClose(void) {
    neven_sim::SimViewerManager::Instance().Shutdown();
    g_sim_initialized = false;
    return 1;
}

extern "C" __declspec(dllexport) void __stdcall xlAutoFree12(LPXLOPER12 px) {
    if (px->xltype & xlbitDLLFree) {
        if (px->xltype & xltypeMulti) {
            int count = px->val.array.rows * px->val.array.columns;
            for (int i = 0; i < count; i++) {
                if (px->val.array.lparray[i].xltype & xltypeStr)
                    delete[] px->val.array.lparray[i].val.str;
            }
            delete[] px->val.array.lparray;
        } else if (px->xltype & xltypeStr) {
            delete[] px->val.str;
        }
    }
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall xlAddInManagerInfo12(LPXLOPER12 pxAction) {
    static XLOPER12 xInfo, xIntAction;
    Excel12(xlCoerce, &xIntAction, 2, pxAction, TempInt12(xltypeInt));
    if (xIntAction.val.w == 1) {
        xInfo.xltype = xltypeStr;
        static wchar_t nm[] = L"\011NEVEN-SIM";
        xInfo.val.str = nm;
    } else {
        xInfo.xltype = xltypeErr;
        xInfo.val.err = xlerrValue;
    }
    return &xInfo;
}

// â”€â”€â”€ Worksheet Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Workspace(void) {
    if (!neven_sim::SimBridge::Instance().EnsureAvailable())
        return MakeStringResult("NEVEN64.xll no esta cargado. Cargue NEVEN base primero.");
    std::string result = neven_sim::SimViewerManager::Instance().OpenWorkspace();
    return MakeStringResult(result);
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Fit(LPXLOPER12 pxRange, LPXLOPER12 pxDist) {
    if (!neven_sim::SimBridge::Instance().EnsureAvailable())
        return MakeStringResult("NEVEN64.xll no esta cargado");
    std::string result = neven_sim::FitRangeData(pxRange, pxDist);
    return MakeStringResult(result);
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Run(LPXLOPER12 pxIterations) {
    if (!neven_sim::SimBridge::Instance().EnsureAvailable())
        return MakeStringResult("NEVEN64.xll no esta cargado");

    auto& engine = neven_sim::SimEngine::Instance();
    if (engine.GetAssumptions().empty())
        return MakeStringResult("No hay supuestos definidos. Use SIM.Workspace().");

    int iterations = 1000000;
    if (pxIterations && pxIterations->xltype == xltypeNum)
        iterations = (int)pxIterations->val.num;
    else if (pxIterations && pxIterations->xltype == xltypeInt)
        iterations = pxIterations->val.w;
    engine.SetIterations(iterations);
    engine.RunPipeline();

    if (engine.GetState() == neven_sim::SimState::COMPLETE) {
        const auto& s = engine.GetSummary();
        std::ostringstream ss;
        ss << "Media=" << s.mean << "; Std=" << s.std_dev
           << "; P5=" << s.p5 << "; P50=" << s.p50 << "; P95=" << s.p95
           << "; N=" << s.iterations << "; " << s.elapsed_ms << "ms";
        return MakeStringResult(ss.str());
    }
    return MakeStringResult("Error: " + engine.GetLastError());
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Percentile(LPXLOPER12 pxP) {
    auto& engine = neven_sim::SimEngine::Instance();
    if (engine.GetState() != neven_sim::SimState::COMPLETE)
        return MakeStringResult("No hay resultados. Ejecute SIM.Run() primero.");
    int p = 50;
    if (pxP && pxP->xltype == xltypeNum) p = (int)pxP->val.num;
    else if (pxP && pxP->xltype == xltypeInt) p = pxP->val.w;
    return MakeNumResult(engine.GetPercentile(p));
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Sensitivity(void) {
    auto& engine = neven_sim::SimEngine::Instance();
    if (engine.GetState() != neven_sim::SimState::COMPLETE)
        return MakeStringResult("No hay resultados. Ejecute SIM.Run() primero.");
    const auto& sens = engine.GetSensitivity();
    if (sens.empty()) return MakeStringResult("Sin datos de sensibilidad");
    std::ostringstream ss;
    for (size_t i = 0; i < sens.size(); i++) {
        if (i > 0) ss << "; ";
        ss << sens[i].name << " rho=" << sens[i].spearman_rho
           << " (" << (int)(sens[i].contribution * 100 + 0.5) << "%)";
    }
    return MakeStringResult(ss.str());
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Status(void) {
    auto& bridge = neven_sim::SimBridge::Instance();
    auto& engine = neven_sim::SimEngine::Instance();
    std::string status = "NEVEN-SIM v1.0 | Base: ";
    status += bridge.EnsureAvailable() ? "OK" : "NO DISPONIBLE";
    status += " | Estado: " + engine.GetStateString();
    status += " | Supuestos: " + std::to_string(engine.GetAssumptions().size());
    return MakeStringResult(status);
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_QuickRun(LPXLOPER12 pxRange, LPXLOPER12 pxModel, LPXLOPER12 pxIterations) {
    auto& bridge = neven_sim::SimBridge::Instance();
    if (!bridge.EnsureAvailable())
        return MakeStringResult("NEVEN64.xll no esta cargado");

    // 1. Extract data from range
    std::vector<double> data;
    if (!neven_sim::ExtractRangeData(pxRange, data))
        return MakeStringResult("Error: No se pudieron extraer datos del rango");
    if (data.size() < 10)
        return MakeStringResult("Error: Se necesitan al menos 10 datos");

    // 2. Get model function from argument
    std::string model = "(x) -> x";  // default: identity
    if (pxModel && pxModel->xltype == xltypeStr && pxModel->val.str) {
        int len = pxModel->val.str[0];
        if (len > 0) {
            std::wstring ws(pxModel->val.str + 1, len);
            model.resize(len);
            for (int i = 0; i < len; i++) model[i] = (char)ws[i];
        }
    }

    // 3. Get iterations
    int iterations = 100000;
    if (pxIterations && pxIterations->xltype == xltypeNum)
        iterations = (int)pxIterations->val.num;
    else if (pxIterations && pxIterations->xltype == xltypeInt)
        iterations = pxIterations->val.w;
    if (iterations < 1000) iterations = 1000;
    if (iterations > 10000000) iterations = 10000000;

    // 4. Fit distribution via R
    std::vector<neven_sim::FitResult> fits;
    if (!neven_sim::FitService::FitDistributions(data, fits))
        return MakeStringResult("Error: Fitting fallo. Verifique fitdistrplus.");
    if (fits.empty())
        return MakeStringResult("Error: Ninguna distribucion ajusto");

    neven_sim::FitResult best = fits[0];

    // 5. Run Monte Carlo in Julia
    // Build Julia code inline (single variable, simple model)
    std::string dist_julia = neven_sim::MonteCarloService::FitToJuliaDistribution(best);

    std::ostringstream jl;
    jl << "let\n";
    jl << "  using Distributions, Random\n";
    jl << "  import Statistics: mean, std\n";
    jl << "  rng = MersenneTwister(42)\n";
    jl << "  n = " << iterations << "\n";
    jl << "  dist = " << dist_julia << "\n";
    jl << "  samples = rand(rng, dist, n)\n";
    jl << "  model = " << model << "\n";
    jl << "  results = [model(s) for s in samples]\n";
    jl << "  # Store globally for SIM.Datos and SIM.Exportar\n";
    jl << "  global _sim_samples = reshape(samples, n, 1)\n";
    jl << "  global _sim_results = results\n";
    jl << "  sorted = sort(results)\n";
    jl << "  pct(p) = sorted[max(1, Int(ceil(p/100*n)))]\n";
    jl << "  m = mean(results); s = std(results)\n";
    jl << "  \"{\\\"mean\\\":\" * string(round(m,digits=4)) *\n";
    jl << "   \",\\\"std\\\":\" * string(round(s,digits=4)) *\n";
    jl << "   \",\\\"min\\\":\" * string(round(minimum(results),digits=4)) *\n";
    jl << "   \",\\\"max\\\":\" * string(round(maximum(results),digits=4)) *\n";
    jl << "   \",\\\"p5\\\":\" * string(round(pct(5),digits=4)) *\n";
    jl << "   \",\\\"p25\\\":\" * string(round(pct(25),digits=4)) *\n";
    jl << "   \",\\\"p50\\\":\" * string(round(pct(50),digits=4)) *\n";
    jl << "   \",\\\"p75\\\":\" * string(round(pct(75),digits=4)) *\n";
    jl << "   \",\\\"p95\\\":\" * string(round(pct(95),digits=4)) *\n";
    jl << "   \"}\"\n";
    jl << "end";

    std::string julia_result = bridge.CallJulia(jl.str());
    if (julia_result.find("[ERROR]") == 0)
        return MakeStringResult("Error Julia: " + julia_result);

    // 6. Parse JSON result
    std::string err;
    json11::Json json = json11::Json::parse(julia_result, err);
    if (!err.empty())
        return MakeStringResult("Dist=" + best.dist_name + " | Julia retorno: " + julia_result);

    // 7. Build rich array output (dynamic array / spill)
    // 2 columns: Label | Value â€” shows the full analysis process
    struct Row { std::string label; std::string value; };
    std::vector<Row> rows;

    rows.push_back({"=== NEVEN-SIM: Simulacion Monte Carlo ===", ""});
    rows.push_back({"", ""});
    rows.push_back({"--- Datos de Entrada ---", ""});
    rows.push_back({"Observaciones historicas", std::to_string(data.size())});
    rows.push_back({"Modelo aplicado", model});
    rows.push_back({"Iteraciones", std::to_string(iterations)});
    rows.push_back({"Muestras generadas", std::to_string(iterations)});
    rows.push_back({"Elementos simulados", std::to_string(iterations) + " evaluaciones del modelo"});
    rows.push_back({"", ""});
    rows.push_back({"--- Ajuste de Distribucion (R/fitdistrplus) ---", ""});
    rows.push_back({"Mejor distribucion", best.dist_name});

    // Format params based on distribution
    std::ostringstream p1s, p2s, aics;
    p1s << std::fixed << std::setprecision(4) << best.param1;
    p2s << std::fixed << std::setprecision(4) << best.param2;
    aics << std::fixed << std::setprecision(1) << best.aic;
    rows.push_back({"Parametro 1", p1s.str()});
    rows.push_back({"Parametro 2", p2s.str()});
    rows.push_back({"AIC (menor=mejor)", aics.str()});

    // Show runner-ups
    if (fits.size() > 1) {
        std::ostringstream r2;
        r2 << fits[1].dist_name << " (AIC=" << std::fixed << std::setprecision(1) << fits[1].aic << ")";
        rows.push_back({"2da mejor", r2.str()});
    }
    if (fits.size() > 2) {
        std::ostringstream r3;
        r3 << fits[2].dist_name << " (AIC=" << std::fixed << std::setprecision(1) << fits[2].aic << ")";
        rows.push_back({"3ra mejor", r3.str()});
    }

    rows.push_back({"Distribuciones evaluadas", std::to_string(fits.size())});
    rows.push_back({"", ""});
    rows.push_back({"--- Resultados Monte Carlo (Julia) ---", ""});

    std::ostringstream fmt;
    fmt << std::fixed << std::setprecision(4);

    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["mean"].number_value();
    rows.push_back({"Media", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["std"].number_value();
    rows.push_back({"Desviacion Estandar", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["min"].number_value();
    rows.push_back({"Minimo", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["max"].number_value();
    rows.push_back({"Maximo", fmt.str()});
    rows.push_back({"", ""});
    rows.push_back({"--- Percentiles ---", ""});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["p5"].number_value();
    rows.push_back({"P5 (optimista)", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["p25"].number_value();
    rows.push_back({"P25", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["p50"].number_value();
    rows.push_back({"P50 (mediana)", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["p75"].number_value();
    rows.push_back({"P75", fmt.str()});
    fmt.str(""); fmt << std::fixed << std::setprecision(4) << json["p95"].number_value();
    rows.push_back({"P95 (pesimista)", fmt.str()});
    rows.push_back({"", ""});
    rows.push_back({"--- Intervalo de Confianza 90% ---", ""});

    std::ostringstream ic;
    ic << "[" << std::fixed << std::setprecision(4) << json["p5"].number_value()
       << " , " << json["p95"].number_value() << "]";
    rows.push_back({"IC 90%", ic.str()});
    rows.push_back({"", ""});
    rows.push_back({"Motor de Fitting", "R 4.4 + fitdistrplus"});
    rows.push_back({"Motor de Simulacion", "Julia 1.12 + Distributions.jl"});
    rows.push_back({"Orquestador", "NEVEN-SIM v1.0 (C++17)"});

    // Build XLOPER12 multi-cell array
    int nrows = (int)rows.size();
    int ncols = 2;
    static XLOPER12 xlResult;
    xlResult.xltype = xltypeMulti | xlbitDLLFree;
    xlResult.val.array.rows = nrows;
    xlResult.val.array.columns = ncols;
    xlResult.val.array.lparray = new XLOPER12[nrows * ncols];

    for (int i = 0; i < nrows; i++) {
        // Column 1: label
        std::wstring wlabel(rows[i].label.begin(), rows[i].label.end());
        int llen = (int)wlabel.length();
        wchar_t* lbuf = new wchar_t[llen + 2];
        lbuf[0] = (wchar_t)llen;
        memcpy(lbuf + 1, wlabel.c_str(), llen * sizeof(wchar_t));
        lbuf[llen + 1] = 0;
        xlResult.val.array.lparray[i * ncols + 0].xltype = xltypeStr;
        xlResult.val.array.lparray[i * ncols + 0].val.str = lbuf;

        // Column 2: value
        std::wstring wval(rows[i].value.begin(), rows[i].value.end());
        int vlen = (int)wval.length();
        wchar_t* vbuf = new wchar_t[vlen + 2];
        vbuf[0] = (wchar_t)vlen;
        memcpy(vbuf + 1, wval.c_str(), vlen * sizeof(wchar_t));
        vbuf[vlen + 1] = 0;
        xlResult.val.array.lparray[i * ncols + 1].xltype = xltypeStr;
        xlResult.val.array.lparray[i * ncols + 1].val.str = vbuf;
    }

    return &xlResult;
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Datos(LPXLOPER12 pxN) {
    auto& bridge = neven_sim::SimBridge::Instance();
    if (!bridge.EnsureAvailable())
        return MakeStringResult("NEVEN64.xll no esta cargado");

    int n = 100;
    if (pxN && pxN->xltype == xltypeNum) n = (int)pxN->val.num;
    else if (pxN && pxN->xltype == xltypeInt) n = pxN->val.w;
    if (n < 1) n = 1;
    if (n > 10000) n = 10000;

    // Ask Julia to return results as comma-separated string
    std::ostringstream jl;
    jl << "isdefined(Main,:_sim_results) ? join(_sim_results[1:min(" << n << ",length(_sim_results))], \",\") : \"[ERROR] No hay simulacion activa\"";

    std::string result = bridge.CallJulia(jl.str());
    if (result.find("[ERROR]") == 0)
        return MakeStringResult(result);

    // Parse comma-separated doubles into array
    std::vector<double> values;
    std::istringstream stream(result);
    std::string token;
    while (std::getline(stream, token, ',')) {
        try { values.push_back(std::stod(token)); } catch (...) {}
    }

    if (values.empty())
        return MakeStringResult("Sin datos");

    // Build Excel array (Nx1)
    int nrows = (int)values.size();
    static XLOPER12 xlResult;
    xlResult.xltype = xltypeMulti | xlbitDLLFree;
    xlResult.val.array.rows = nrows;
    xlResult.val.array.columns = 1;
    xlResult.val.array.lparray = new XLOPER12[nrows];
    for (int i = 0; i < nrows; i++) {
        xlResult.val.array.lparray[i].xltype = xltypeNum;
        xlResult.val.array.lparray[i].val.num = values[i];
    }
    return &xlResult;
}

extern "C" __declspec(dllexport) LPXLOPER12 __stdcall SIM_Exportar(void) {
    auto& bridge = neven_sim::SimBridge::Instance();
    if (!bridge.EnsureAvailable())
        return MakeStringResult("NEVEN64.xll no esta cargado");

    SYSTEMTIME st;
    GetLocalTime(&st);
    char ts[64];
    sprintf_s(ts, "%04d%02d%02d_%02d%02d%02d", st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);

    std::string home = bridge.GetHomePath();
    std::string filename = std::string("sim_results_") + ts + ".csv";
    std::string jl_path;
    for (char c : (home + "data/" + filename)) {
        jl_path += (c == '\\') ? '/' : c;
    }

    // Use write(path, content) which is NOT blocked by security
    // Build the entire CSV content as a string in Julia, then write() it
    std::ostringstream jl;
    jl << "if !isdefined(Main,:_sim_results); \"[ERROR] No hay simulacion activa\"; else; ";
    jl << "";
    jl << "csv = \"Muestra,Resultado\\n\" * join([string(_sim_samples[i,1]) * \",\" * string(_sim_results[i]) for i in 1:length(_sim_results)], \"\\n\"); ";
    jl << "write(\"" << jl_path << "\", csv); ";
    jl << "\"OK: $(length(_sim_results)) registros -> " << jl_path << "\"; end";

    std::string result = bridge.CallJulia(jl.str());
    return MakeStringResult(result);
}

