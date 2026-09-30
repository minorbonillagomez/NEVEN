# NEVEN-SIM: High-Level Design

## 1. Architecture Overview

NEVEN-SIM is a **separate XLL** (`NEVEN-SIM.xll`) that loads alongside `NEVEN64.xll` in Excel. It does **not** modify or recompile the base XLL — instead it discovers and consumes the engines (R, Julia) already running via their Named Pipes.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Microsoft Excel Process                          │
│                                                                          │
│  ┌─────────────────────┐        ┌──────────────────────────────────┐    │
│  │   NEVEN64.xll       │        │     NEVEN-SIM.xll                │    │
│  │   (Base Add-in)     │        │     (Simulation Module)          │    │
│  │                     │        │                                  │    │
│  │ • LanguageManager   │◄──────►│ • SimBridge (discovers pipes)    │    │
│  │ • ViewerManager     │        │ • SimEngine (orchestration)      │    │
│  │ • ConfigService     │        │ • FitService (→R)                │    │
│  │ • FileWatchService  │        │ • MonteCarloService (→Julia)     │    │
│  │ • PlutoManager      │        │ • SensitivityService             │    │
│  │                     │        │ • SimViewerManager (WebView2)    │    │
│  └────────┬────────────┘        └────────┬─────────────────────────┘    │
│           │                               │                              │
└───────────┼───────────────────────────────┼──────────────────────────────┘
            │  Named Pipes (existing)       │  Named Pipes (shared)
            ▼                               ▼
     ┌─────────────┐              ┌─────────────┐         ┌────────────────┐
     │ ControlR.exe│              │ControlJulia │         │ WebView2       │
     │ (R 4.4+)   │              │   (Julia    │         │ (SIM Workspace)│
     │             │              │    1.12+)   │         │                │
     │ • fitdistr  │              │ • Distribu- │         │ • Plotly.js    │
     │ • forecast  │              │   tions.jl  │         │ • Assumption   │
     │ • MASS      │              │ • Copulas.jl│         │   Editor       │
     └─────────────┘              │ • Random    │         │ • Results      │
                                  └─────────────┘         └────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate XLL | Modular installation — users install only what they need |
| XLL as orchestrator | C++ controls the pipeline; no Python coordination layer |
| Julia for Monte Carlo | 1M iterations in <10s; Julia threads for parallelism |
| R for fitting | `fitdistrplus` + `forecast` are mature, battle-tested |
| Shared Named Pipes | Reuse existing engines from NEVEN base (zero overhead) |
| WebView2 workspace | Single interactive window with Plotly.js charts |
| Protobuf for IPC | Typed, versioned, already proven in NEVEN base |

---

## 2. Inter-XLL Communication: SimBridge

The critical challenge is: how does NEVEN-SIM.xll communicate with the language engines that NEVEN64.xll owns?

### Strategy: Shared Named Pipe Discovery

NEVEN64.xll creates Named Pipes with predictable names:
```
\\.\pipe\RJ2XCL2-PIPE-R-{PID}
\\.\pipe\RJ2XCL2-PIPE-J-{PID}
\\.\pipe\RJ2XCL2-PIPE-R-{PID}-M   (management pipe)
\\.\pipe\RJ2XCL2-PIPE-J-{PID}-M   (management pipe)
```

NEVEN-SIM uses a **dedicated management pipe** approach:

1. **SimBridge** reads `neven-config.json` to confirm NEVEN base is installed
2. On `xlAutoOpen`, SimBridge queries NEVEN64.xll's exported function `NEVEN_GetEngineStatus()` via `xlUDF`
3. If NEVEN base is loaded, SimBridge obtains pipe names via a shared config file (`C:\NEVEN\sim-bridge.json`) written by NEVEN64.xll at startup
4. SimBridge creates its **own Named Pipe clients** to the same ControlR/ControlJulia processes using the management pipe protocol

### Alternative (Simpler — Phase 1): Excel UDF Relay

For Phase 1 MVP, NEVEN-SIM can call NEVEN base functions directly via `xlUDF`:

```cpp
// SimBridge calls NEVEN.r() and NEVEN.j() via Excel's function dispatch
XLOPER12 result;
XLOPER12 code_arg;
Convert::StringToXLOPER(&code_arg, r_fitting_code.c_str(), true);
Excel12(xlUDF, &result, 2, &funcName_NEVEN_r, &code_arg);
```

This is simpler (no pipe management) and already works. The limitation is that it's synchronous and goes through Excel's thread. For Phase 1 (short R fitting calls + one Julia simulation call), this is acceptable.

**Phase 2** upgrades to direct pipe communication for async/parallel execution.

---

## 3. Component Breakdown

### 3.1 SimEngine (Orchestrator)

The central coordinator. Receives user commands from UI or worksheet functions and orchestrates the full pipeline.

```
SimEngine
├── ValidateAssumptions()     → check all inputs are defined
├── RunFitting()              → dispatch to FitService (R)
├── BuildSimPayload()         → assemble Protobuf for Julia
├── RunSimulation()           → dispatch to MonteCarloService (Julia)
├── ComputeSensitivity()      → dispatch to SensitivityService
├── PushResults()             → write back to Excel cells
└── OpenWorkspace()           → launch WebViewer with results
```

**State Machine:**
```
IDLE → CONFIGURING → FITTING → SIMULATING → ANALYZING → COMPLETE
                                    ↑              │
                                    └──────────────┘ (iterate)
```

### 3.2 FitService (R Engine Integration)

Sends R code to ControlR.exe via the relay mechanism. Responsibilities:

- Generate R code dynamically for `fitdistrplus::fitdist()`
- Parse returned Protobuf results (distribution name, parameters, GoF stats)
- Rank candidate distributions by AIC/BIC and GoF p-value

**R Code Template (generated by C++):**
```r
.neven_sim_fit <- function(data_vec) {
  library(fitdistrplus)
  library(MASS)
  candidates <- c("norm","lnorm","gamma","weibull","exp","unif","beta")
  results <- list()
  for (dist in candidates) {
    tryCatch({
      fit <- fitdist(data_vec, dist)
      gof <- gofstat(fit)
      results[[dist]] <- list(
        params = as.list(fit$estimate),
        aic = fit$aic,
        ks_stat = gof$ks, ks_p = gof$kstest,
        ad_stat = gof$ad, ad_p = gof$adtest
      )
    }, error = function(e) NULL)
  }
  # Return as JSON string for easy parsing
  jsonlite::toJSON(results, auto_unbox = TRUE)
}
.neven_sim_fit(c(...DATA...))
```

### 3.3 MonteCarloService (Julia Engine Integration)

Sends Julia code/function calls to ControlJulia.exe. This is where the heavy computation happens.

**Julia Simulation Module** (loaded as a library file):
```julia
module NEVENSim

using Distributions, Random

struct Assumption
    name::String
    dist::Distribution
end

function run_montecarlo(assumptions::Vector{Assumption}, 
                        model_func::Function, 
                        n_iterations::Int;
                        seed::Int=42)
    rng = MersenneTwister(seed)
    n_vars = length(assumptions)
    samples = Matrix{Float64}(undef, n_iterations, n_vars)
    
    # Generate samples
    for (j, a) in enumerate(assumptions)
        samples[:, j] = rand(rng, a.dist, n_iterations)
    end
    
    # Evaluate model
    results = Vector{Float64}(undef, n_iterations)
    Threads.@threads for i in 1:n_iterations
        results[i] = model_func(samples[i, :]...)
    end
    
    return (samples=samples, results=results)
end

function summary_stats(results::Vector{Float64})
    sorted = sort(results)
    n = length(sorted)
    percentiles = [1,5,10,25,50,75,90,95,99]
    pct_values = [sorted[max(1, Int(ceil(p/100*n)))] for p in percentiles]
    
    return (
        mean = mean(results),
        std = std(results),
        min = minimum(results),
        max = maximum(results),
        percentiles = Dict(zip(percentiles, pct_values))
    )
end

export Assumption, run_montecarlo, summary_stats

end # module
```

### 3.4 SensitivityService

Computes Spearman rank correlations between each input variable and the output. Can run in Julia (fast) or C++ (no engine dependency for small N).

```
For each assumption i:
    ρᵢ = spearman_correlation(samples[:, i], results)
    contribution_i = ρᵢ² / Σ(ρⱼ²)  → percentage contribution
```

### 3.5 SimViewerManager (WebView2 Workspace)

A specialized viewer window (reuses the ViewerManager pattern from NEVEN base) that hosts the interactive simulation workspace.

**Architecture:**
```
SimViewerManager
├── CreateWorkspace()         → opens single workspace window
├── SendAssumptions()         → push assumption config to JS
├── SendFitResults()          → push fitting results for charts
├── SendSimResults()          → push MC results + percentiles
├── SendSensitivity()         → push Tornado chart data
└── HandleMessage()           → receive commands from JS (run, configure, export)
```

**Communication: PostMessage Bridge (JS ↔ C++)**
```
C++ → JS:  window.chrome.webview.postMessage(JSON)
JS → C++:  window.chrome.webview.postMessage(JSON) → WebMessageReceived handler
```

---

## 4. Data Flow

### 4.1 Full Pipeline (User clicks "Run Simulation")

```
┌────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Excel  │───►│ SimEngine │───►│FitService│───►│  R (via  │───►│  Return  │
│ (data) │    │(orchestr.)│    │          │    │  pipe)   │    │fit params│
└────────┘    └─────┬─────┘    └──────────┘    └──────────┘    └────┬─────┘
                    │                                                │
                    │◄──────────────────────────────────────────────┘
                    │
                    ▼
              ┌───────────┐    ┌──────────┐    ┌──────────┐
              │Build Julia│───►│  Julia   │───►│  Return  │
              │  Payload  │    │(MC runs) │    │ results  │
              └───────────┘    └──────────┘    └────┬─────┘
                    │                                │
                    │◄──────────────────────────────┘
                    │
                    ▼
              ┌───────────┐    ┌──────────┐
              │Sensitivity│───►│ WebView2 │
              │  Analysis │    │Workspace │
              └───────────┘    └──────────┘
```

### 4.2 Data Format: Excel → XLL → Engine

**Step 1: Read historical data from Excel range**
```cpp
// SimEngine reads the assumption's source range
XLOPER12 range_data;
Excel12(xlCoerce, &range_data, 2, &ref, TempInt12(xltypeMulti));
// Convert to vector<double>
```

**Step 2: Send to R for fitting (as Protobuf Variable::Array)**
```protobuf
// Existing variable.proto is sufficient:
Variable {
  arr: Array {
    rows: 1000
    cols: 1
    data: [real: 3.14, real: 2.71, ...]
  }
}
```

**Step 3: R returns fit results as JSON string**
```protobuf
Variable {
  str: "{\"norm\":{\"params\":{\"mean\":5.2,\"sd\":1.3},\"aic\":2340.5,...}}"
}
```

**Step 4: Send to Julia for simulation**
```julia
# Generated Julia code sent via NEVEN.j():
using NEVENSim
assumptions = [
    Assumption("ventas", Normal(5.2, 1.3)),
    Assumption("costos", LogNormal(3.1, 0.4)),
    Assumption("tipo_cambio", Uniform(500, 600))
]
model(ventas, costos, tc) = ventas * tc - costos * tc
result = run_montecarlo(assumptions, model, 1_000_000)
stats = summary_stats(result.results)
```

**Step 5: Julia returns results as Array (Protobuf)**
```protobuf
Variable {
  arr: Array {
    rows: 1000000   // or summary only
    cols: 1
    data: [real: ..., real: ..., ...]
  }
}
```

---

## 5. Protobuf Schema Additions

The existing `variable.proto` is **already sufficient** for Phase 1. All data fits within the existing `Variable`, `Array`, and `CallResponse` types.

For Phase 2 (persistent simulation definitions), a new proto file will define simulation metadata:

```protobuf
// simulation.proto (Phase 2 — NOT needed for MVP)
syntax = "proto3";
package NEVENSim;

message Assumption {
    string name = 1;
    string source_range = 2;       // "Sheet1!A1:A1000"
    string distribution = 3;       // "Normal", "LogNormal", etc.
    repeated double parameters = 4; // [mean, std] or [shape, scale]
    string fit_method = 5;         // "MLE", "MME"
}

message SimulationConfig {
    repeated Assumption assumptions = 1;
    string model_code = 2;         // Julia expression
    int32 iterations = 3;          // 10000 - 10000000
    int32 seed = 4;
    string copula_type = 5;        // "none", "gaussian", "clayton"
    repeated double correlation_matrix = 6; // flattened
}

message SimulationResult {
    repeated double results = 1;    // full result vector (or summary)
    double mean = 2;
    double std_dev = 3;
    repeated double percentiles = 4; // P1, P5, P10, P25, P50, P75, P90, P95, P99
    repeated double sensitivity = 5; // Spearman ρ per assumption
}
```

---

## 6. WebViewer Workspace Architecture

### 6.1 Single-Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  NEVEN-SIM Workspace                                         [─][□][×]│
├─────────────────────────┬───────────────────────────────────────────┤
│  ASSUMPTIONS            │  VISUALIZATION                             │
│                         │                                            │
│  ┌───────────────────┐  │  ┌──────────────────────────────────────┐ │
│  │ + Add Assumption  │  │  │                                      │ │
│  └───────────────────┘  │  │         Distribution PDF              │ │
│                         │  │     (Plotly.js overlay chart)         │ │
│  ▼ Ventas (Normal)      │  │                                      │ │
│    μ = 5.2  σ = 1.3     │  │                                      │ │
│    Source: A1:A1000     │  └──────────────────────────────────────┘ │
│    [Re-fit] [Remove]    │                                            │
│                         │  ┌──────────────────────────────────────┐ │
│  ▼ Costos (LogNormal)   │  │                                      │ │
│    μ = 3.1  σ = 0.4     │  │       Simulation Histogram           │ │
│    Source: B1:B1000     │  │     (Plotly.js + percentile lines)   │ │
│    [Re-fit] [Remove]    │  │                                      │ │
│                         │  │                                      │ │
│  ─────────────────────  │  └──────────────────────────────────────┘ │
│  MODEL                  │                                            │
│  ┌───────────────────┐  │  ┌──────────────────────────────────────┐ │
│  │ f(v,c) = v - c    │  │  │                                      │ │
│  └───────────────────┘  │  │         Tornado Chart                 │ │
│                         │  │     (Horizontal Spearman bars)        │ │
│  Iterations: [1000000]  │  │                                      │ │
│                         │  │                                      │ │
│  [▶ Run Simulation]     │  └──────────────────────────────────────┘ │
│  [📊 Export Report]     │                                            │
├─────────────────────────┴───────────────────────────────────────────┤
│  Status: Simulation complete — 1,000,000 iterations in 4.2s         │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 JS ↔ C++ Message Protocol

```javascript
// JS → C++ (commands)
window.chrome.webview.postMessage({
    type: "add-assumption",
    range: "Sheet1!A1:A1000",
    name: "Ventas"
});

window.chrome.webview.postMessage({
    type: "run-simulation",
    iterations: 1000000,
    model: "function(ventas, costos) ventas - costos end"
});

// C++ → JS (data updates)
// Received via: window.chrome.webview.addEventListener('message', handler)
{
    type: "fit-results",
    assumption: "Ventas",
    distributions: [
        { name: "Normal", params: {mean: 5.2, sd: 1.3}, aic: 2340, ks_p: 0.87 },
        { name: "LogNormal", params: {meanlog: 1.6, sdlog: 0.3}, aic: 2355, ks_p: 0.72 }
    ]
}

{
    type: "simulation-results",
    stats: { mean: 42300, std: 8200, min: 12000, max: 89000 },
    percentiles: { "1": 22000, "5": 28000, ..., "99": 63000 },
    histogram: { bins: [...], counts: [...] },  // pre-binned for Plotly
    elapsed_ms: 4200
}

{
    type: "sensitivity",
    variables: ["Ventas", "Costos", "TipoCambio"],
    spearman: [0.82, -0.45, 0.31],
    contribution: [0.58, 0.28, 0.14]
}
```

### 6.3 Technology Stack (WebViewer)

- **Plotly.js** (~3MB, CDN or bundled) — histograms, PDF curves, bar charts
- **Vanilla JS + CSS Grid** — no frameworks (per constraint C-5)
- **PostMessage Bridge** — already proven in NEVEN base ViewerManager

---

## 7. Excel Integration Functions

### 7.1 Worksheet Functions (registered by NEVEN-SIM.xll)

| Function | Description | Returns |
|----------|-------------|---------|
| `=SIM.Workspace()` | Opens the interactive WebViewer workspace | "OK" |
| `=SIM.Fit(range, [dist])` | Fit distribution to data range | Best-fit name + params |
| `=SIM.Run(config_range)` | Run simulation (reads config from sheet) | Summary statistics array |
| `=SIM.Percentile(p)` | Get percentile from last simulation | Value |
| `=SIM.Sensitivity()` | Get sensitivity analysis from last run | Tornado data array |
| `=SIM.Status()` | Current simulation state | Status string |

### 7.2 Ribbon Integration

NEVEN-SIM adds a "Simulación" group to the NEVEN Ribbon tab (via NEVENRibbon.dll extension point or its own COM add-in):

```
[Simulación]
  [📊 Workspace]  [▶ Ejecutar]  [📋 Reporte]
```

---

## 8. Build System & Directory Structure

```
NEVEN-SIM/                          (new top-level directory in repo)
├── CMakeLists.txt                  (builds NEVEN-SIM.xll)
├── Core/
│   ├── sim_engine.h/.cc
│   ├── sim_bridge.h/.cc            (discovers NEVEN base pipes)
│   ├── fit_service.h/.cc           (R integration)
│   ├── montecarlo_service.h/.cc    (Julia integration)
│   └── sensitivity_service.h/.cc
├── UI/
│   ├── sim_viewer_manager.h/.cc    (WebView2 workspace)
│   └── workspace.html              (embedded HTML + JS + CSS)
├── include/
│   └── sim_exports.h               (xlAutoOpen, xlfRegister exports)
├── libreria/
│   ├── JULIA/
│   │   └── NEVENSim.jl            (Monte Carlo + Distributions module)
│   └── R/
│       └── neven_sim_fit.R         (fitting functions)
└── tests/
    ├── sim_engine_test.cc
    ├── fit_service_test.cc
    └── montecarlo_test.cc
```

### Build Integration

The root `CMakeLists.txt` gets a new option:
```cmake
option(BUILD_NEVEN_SIM "Build NEVEN-SIM simulation module" OFF)

if(BUILD_NEVEN_SIM)
    add_subdirectory(NEVEN-SIM)
endif()
```

NEVEN-SIM links against:
- `Common.lib` (shared utilities — pipes, config, JSON, security)
- `PB.lib` (Protocol Buffers — variable.proto)
- WebView2 SDK (same as NEVEN base)
- Excel SDK headers (`XLCALL.H`)

It does **not** link against `NEVEN_Core.lib` — communication is via Excel UDF relay or pipe discovery.

---

## 9. Installation & Distribution

```
C:\NEVEN\                           (existing base installation)
├── NEVEN64.xll                     (base)
├── NEVEN-SIM.xll                   (simulation module — optional)
├── neven-config.json
├── neven-sim-config.json           (SIM-specific settings)
├── libreria/
│   ├── R/
│   │   └── neven_sim_fit.R
│   └── JULIA/
│       └── NEVENSim.jl
├── workspace/
│   └── sim-workspace.html          (WebViewer workspace HTML)
└── functions/                      (user functions — existing)
```

The installer (`Install-NEVEN.ps1`) gets a new optional flag:
```powershell
.\Install-NEVEN.ps1 -IncludeSIM
```

Or NEVEN-SIM can ship as a separate installer entirely.

---

## 10. Error Handling & Graceful Degradation

| Scenario | Behavior |
|----------|----------|
| NEVEN base not loaded | `=SIM.Workspace()` returns "NEVEN64.xll no está cargado" |
| R not connected | FitService returns error; user can still do manual distribution entry |
| Julia not connected | MonteCarloService returns error; cannot run simulation |
| WebView2 not available | Workspace doesn't open; results still written to cells |
| Fitting fails for a distribution | Skip that candidate; report only successful fits |
| Julia simulation throws error | Propagate error message to workspace status bar |

---

## 11. Phase 1 (MVP) Scope

For the initial deliverable:

1. **SimBridge** — detect NEVEN base via `xlUDF` relay (no direct pipe)
2. **FitService** — fit 7 distributions via R `fitdistrplus`
3. **MonteCarloService** — basic MC (independent variables, no copulas)
4. **SensitivityService** — Spearman rank correlation
5. **SimViewerManager** — workspace with PDF overlay + histogram + Tornado
6. **Excel functions** — `=SIM.Workspace()`, `=SIM.Fit()`, `=SIM.Run()`
7. **Julia library** — `NEVENSim.jl` with `run_montecarlo` + `summary_stats`
8. **R library** — `neven_sim_fit.R` with distribution fitting

**Not in Phase 1**: Copulas, time series, multi-period, parallel Julia threads, Quarto reports, reactive sliders.

---

## 12. Security Considerations

- Julia model functions execute user-provided code — same trust model as `=NEVEN.j()`
- No network access during simulation (constraint C-6)
- Protobuf validates all incoming data types (no buffer overflow risk)
- WebView2 workspace restricts navigation to `about:blank` and local files only

---

*NEVEN-SIM v1.0 — High-Level Design Document*
*Author: Minor Bonilla Gomez | Date: July 2026*
