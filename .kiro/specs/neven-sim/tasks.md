# NEVEN-SIM: Implementation Tasks

## Phase 1 — MVP

### Task 1: Project Scaffolding & Build System
- [ ] Create `NEVEN-SIM/` directory structure (Core/, UI/, include/, libreria/, tests/)
- [ ] Create `NEVEN-SIM/CMakeLists.txt` — builds `NEVEN-SIM.xll` (.dll renamed)
- [ ] Link against Common.lib, PB.lib, WebView2 SDK, Excel SDK
- [ ] Add `option(BUILD_NEVEN_SIM OFF)` to root CMakeLists.txt
- [ ] Create `sim_exports.h` with `xlAutoOpen`/`xlAutoClose`/`xlAutoFree12` stubs
- [ ] Verify clean build produces NEVEN-SIM.xll alongside NEVEN64.xll

### Task 2: SimBridge — NEVEN Base Discovery
- [ ] Implement `SimBridge` class (singleton)
- [ ] On `xlAutoOpen`: check if NEVEN64.xll is loaded via `xlGetName` enumeration or `xlUDF("NEVEN.status")`
- [ ] Read `C:\NEVEN\neven-config.json` to confirm installation path
- [ ] Expose `IsBaseAvailable()`, `CallR(code)`, `CallJulia(code)` methods
- [ ] `CallR`/`CallJulia` use `Excel12(xlUDF, ...)` to invoke `NEVEN.r()` / `NEVEN.j()`
- [ ] Graceful error: if base not loaded, all SIM functions return informative error string
- [ ] Write unit tests with mock Excel bridge

### Task 3: FitService — Distribution Fitting via R
- [ ] Create `fit_service.h/.cc`
- [ ] Generate R code string for `fitdistrplus::fitdist()` with dynamic data injection
- [ ] Support 7 candidate distributions: Normal, LogNormal, Gamma, Weibull, Exponential, Uniform, Beta
- [ ] Parse JSON result string from R into C++ struct `FitResult { dist_name, params, aic, ks_p, ad_p }`
- [ ] Rank results by AIC (lower is better) and KS p-value (higher is better)
- [ ] Create `neven_sim_fit.R` library file (installed to `C:\NEVEN\libreria\R\`)
- [ ] Handle errors: missing packages → return "Instale fitdistrplus: =R.instalar(\"fitdistrplus\")"
- [ ] Unit tests with sample data vectors

### Task 4: MonteCarloService — Julia Simulation Engine
- [ ] Create `montecarlo_service.h/.cc`
- [ ] Generate Julia code string that defines assumptions and runs simulation
- [ ] Create `NEVENSim.jl` module (installed to `C:\NEVEN\libreria\JULIA\`)
  - [ ] `Assumption` struct (name, distribution)
  - [ ] `run_montecarlo(assumptions, model_func, n_iterations; seed)` function
  - [ ] `summary_stats(results)` → mean, std, min, max, percentiles
  - [ ] `histogram_bins(results, n_bins=50)` → bins + counts for Plotly
- [ ] Parse returned Julia array (Float64 vector) via existing Protobuf Array handling
- [ ] Handle large result vectors (>1M elements) — return summary only, store full in Julia
- [ ] Unit tests with known distribution seeds (verify percentiles match theory)

### Task 5: SensitivityService — Spearman Rank Correlation
- [ ] Create `sensitivity_service.h/.cc`
- [ ] Implement in Julia (faster for large N): `spearman_sensitivity(samples, results)`
- [ ] Add to `NEVENSim.jl`: function that returns Vector{Float64} of ρ values
- [ ] Compute contribution percentages: `ρᵢ² / Σ(ρⱼ²)`
- [ ] Return as named array: assumption names + ρ values + contribution %
- [ ] Unit test: verify correlation sign and magnitude with controlled inputs

### Task 6: SimEngine — Orchestration Pipeline
- [ ] Create `sim_engine.h/.cc` (singleton)
- [ ] Define `SimState` enum: IDLE, CONFIGURING, FITTING, SIMULATING, ANALYZING, COMPLETE, ERROR
- [ ] Implement `DefineAssumption(name, range, type)` — stores assumption metadata
- [ ] Implement `RunPipeline()`:
  1. Read Excel ranges for all assumptions → vector<double> per assumption
  2. For each assumption: call FitService → get FitResult
  3. Build Julia code string with best-fit distributions
  4. Call MonteCarloService → get results
  5. Call SensitivityService → get Tornado data
  6. Push results to SimViewerManager + Excel cells
- [ ] Implement async execution (Windows thread) so Excel doesn't freeze
- [ ] Store last simulation results for `=SIM.Percentile()` queries
- [ ] Error propagation from each stage to status string

### Task 7: Excel Function Registration
- [ ] Implement `xlAutoOpen` for NEVEN-SIM.xll
  - [ ] Initialize SimBridge, SimEngine, SimViewerManager
  - [ ] Register worksheet functions via `xlfRegister`
- [ ] `=SIM.Workspace()` → opens WebViewer workspace, returns "OK"
- [ ] `=SIM.Fit(range, [distribution])` → fit data and return best-fit string
- [ ] `=SIM.Run(iterations)` → trigger full pipeline, return summary stats as array
- [ ] `=SIM.Percentile(p)` → return percentile from last simulation
- [ ] `=SIM.Sensitivity()` → return Tornado data as 2D array (names + values)
- [ ] `=SIM.Status()` → return current engine state
- [ ] Implement `xlAutoClose` — shutdown all services cleanly

### Task 8: SimViewerManager — WebView2 Workspace
- [ ] Create `sim_viewer_manager.h/.cc` (singleton, reuses ViewerManager pattern)
- [ ] Create dedicated STA thread for WebView2 (or reuse NEVEN base's ViewerManager)
- [ ] Implement `OpenWorkspace()` — creates single workspace window from embedded HTML
- [ ] Implement `SendToWorkspace(json)` — post message to JS context
- [ ] Implement `HandleWebMessage(json)` — receive commands from JS
- [ ] Message handlers:
  - [ ] "add-assumption" → SimEngine::DefineAssumption()
  - [ ] "run-simulation" → SimEngine::RunPipeline()
  - [ ] "export-report" → (Phase 2 — stub for now)

### Task 9: Workspace HTML/JS/CSS
- [ ] Create `workspace/sim-workspace.html` — single-file with embedded CSS + JS
- [ ] Left panel: Assumption list with accordion UI
  - [ ] "Add Assumption" button → prompts for range reference
  - [ ] Display fitted distribution + parameters per assumption
  - [ ] "Remove" button per assumption
- [ ] Right panel: Plotly.js charts
  - [ ] Distribution PDF overlay (histogram of data + fitted PDF curve)
  - [ ] Simulation result histogram with percentile vertical lines
  - [ ] Tornado chart (horizontal bars sorted by |ρ|)
- [ ] Bottom status bar: simulation state + elapsed time
- [ ] Model input: text area for Julia model expression
- [ ] Iterations input: numeric with default 1,000,000
- [ ] "Run Simulation" button → posts message to C++
- [ ] Responsive layout (CSS Grid, min-width 900px)
- [ ] Bundle Plotly.js minified (~3MB) or use CDN with offline fallback

### Task 10: Integration Testing & Packaging
- [ ] End-to-end test: define 3 assumptions → fit → simulate → verify results
- [ ] Performance test: 1M iterations with 5 variables → must complete < 10s
- [ ] Test NEVEN-SIM loads alongside NEVEN64.xll without conflicts
- [ ] Test graceful degradation when NEVEN base is not loaded
- [ ] Create distribution package structure (`NEVEN-SIM/Dist/`)
- [ ] Update `Install-NEVEN.ps1` with `-IncludeSIM` parameter
- [ ] Create `neven-sim-config.json` (default settings: iterations, seed, etc.)

---

## Phase 2 — Advanced (Future)

### Task 11: Time Series Forecasting (R)
- [ ] Implement ARIMA fitting via R `forecast::auto.arima()`
- [ ] Implement NNETAR via R `forecast::nnetar()`
- [ ] Implement ETS via R `forecast::ets()`
- [ ] Multi-period trajectory generation (forecast horizon fan)
- [ ] Integration with SimEngine for time-series type assumptions

### Task 12: Copula Dependencies (Julia)
- [ ] Integrate `Copulas.jl` into NEVENSim.jl
- [ ] Implement Gaussian copula with correlation matrix input
- [ ] Implement Archimedean copulas (Clayton, Gumbel, Frank)
- [ ] UI for specifying correlation pairs in workspace
- [ ] Test: verify correlated samples preserve target Spearman ρ

### Task 13: Parallel Julia Execution
- [ ] Enable `Threads.@threads` in `run_montecarlo` (Julia must start with JULIA_NUM_THREADS)
- [ ] Set thread count in `neven-sim-config.json`
- [ ] Benchmark: compare single-thread vs multi-thread for 1M-10M iterations

### Task 14: Reactive Sliders (WebViewer)
- [ ] Add parameter sliders to each assumption in the workspace
- [ ] On slider change: regenerate PDF chart in <200ms (JS-only, no engine call)
- [ ] Use Plotly.js `Plotly.react()` for efficient partial updates

### Task 15: Quarto Report Export
- [ ] Generate `.qmd` template with simulation parameters + results
- [ ] Include Plotly charts as static images (base64 PNG)
- [ ] Trigger `quarto render` via existing QuartoService in NEVEN base
- [ ] Output: PDF or HTML report

### Task 16: Direct Pipe Communication (Replace xlUDF Relay)
- [ ] SimBridge reads pipe names from `C:\NEVEN\sim-bridge.json`
- [ ] Create dedicated pipe client connections (separate from NEVEN base's)
- [ ] Implement async call/response with own transaction IDs
- [ ] Enables parallel R fitting + Julia simulation

---

*NEVEN-SIM v1.0 — Implementation Tasks*
*Date: July 2026*
