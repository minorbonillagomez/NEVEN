# NEVEN-SIM: Requirements

## Overview
NEVEN-SIM is a modular Excel add-in (separate XLL) that provides stochastic simulation, time series forecasting, and risk analysis capabilities. It depends on the NEVEN base XLL for language engine connectivity (R, Julia, Python) and WebView2 infrastructure.

## Architecture Principle
- **Separate XLL**: `NEVEN-SIM.xll` loads alongside `NEVEN64.xll`, consuming its services
- **Modular Installation**: Users install only NEVEN-SIM if they need simulation capabilities
- **Orchestrator**: The XLL (C++) coordinates all engines directly via existing Named Pipes
- **No Excel Recalculation Loop**: Julia runs simulations internally and returns aggregated results

---

## Functional Requirements

### FR-1: Assumption Definition (Input Variables)
- **FR-1.1**: User selects a range of historical data in Excel and defines it as a simulation input ("Assumption")
- **FR-1.2**: System supports two types of assumptions:
  - **Static Distribution**: Historical data fitted to a parametric distribution (Normal, Triangular, Lognormal, Uniform, Beta, Gamma, Weibull, Custom)
  - **Time Series Model**: Historical data modeled as ARIMA, Neural Network Autoregressive (NNETAR), or Exponential Smoothing
- **FR-1.3**: Multiple assumptions can be defined per simulation (multi-variable model)
- **FR-1.4**: Assumptions are persisted in the workbook (named ranges or hidden sheet)

### FR-2: Distribution Fitting (R Engine)
- **FR-2.1**: Automatic fit of historical data to candidate distributions using Maximum Likelihood Estimation (MLE)
- **FR-2.2**: Goodness-of-fit tests: Kolmogorov-Smirnov, Anderson-Darling, Chi-squared
- **FR-2.3**: Return ranked list of best-fitting distributions with parameters and p-values
- **FR-2.4**: Support for at least 8 common distributions (Normal, Lognormal, Triangular, Uniform, Beta, Gamma, Weibull, Exponential)
- **FR-2.5**: R libraries required: `fitdistrplus`, `MASS`

### FR-3: Time Series Forecasting (R Engine)
- **FR-3.1**: Automatic model selection via Auto-ARIMA (`forecast` package)
- **FR-3.2**: Neural Network Autoregressive model (`nnetar`) for non-linear patterns
- **FR-3.3**: Exponential Smoothing (ETS) as alternative
- **FR-3.4**: Return model coefficients, residual variance, and forecast horizon
- **FR-3.5**: R libraries required: `forecast`, `fable` (optional)

### FR-4: Dependency Modeling - Copulas (Julia Engine)
- **FR-4.1**: Support for correlated assumptions (joint distribution sampling)
- **FR-4.2**: Gaussian copula for general correlation
- **FR-4.3**: Archimedean copulas (Clayton, Gumbel, Frank) for tail dependencies
- **FR-4.4**: User specifies correlation matrix or copula type between assumption pairs
- **FR-4.5**: Julia libraries required: `Distributions.jl`, `Copulas.jl`

### FR-5: Monte Carlo Simulation Engine (Julia)
- **FR-5.1**: Generate N samples (10,000 to 10,000,000) from configured distributions/models
- **FR-5.2**: Respect copula dependencies when generating correlated samples
- **FR-5.3**: Evaluate a user-defined financial model function (Julia code) using sampled inputs
- **FR-5.4**: Return full result array + summary statistics (mean, median, std, percentiles 1-99)
- **FR-5.5**: Multi-period simulation for time series (generate trajectory fans)
- **FR-5.6**: Execution must be parallelizable (Julia threads)
- **FR-5.7**: Julia libraries required: `Distributions.jl`, `Copulas.jl`, `Random.jl`

### FR-6: Sensitivity Analysis
- **FR-6.1**: Spearman rank correlation between each input assumption and the output forecast
- **FR-6.2**: Tornado chart visualization (horizontal bars sorted by absolute contribution)
- **FR-6.3**: Identify the top-N most impactful assumptions

### FR-7: Interactive WebViewer Workspace
- **FR-7.1**: Single-window workspace opened via `=NEVEN.SIM()` or Ribbon button
- **FR-7.2**: Left panel: assumption configuration (list, type, parameters, dependencies)
- **FR-7.3**: Right panel: live visualization (PDF curves, trajectory fans, histograms)
- **FR-7.4**: Reactive sliders for parameter tuning (redraw PDF/trajectory in real-time)
- **FR-7.5**: "Run Simulation" button triggers Julia execution
- **FR-7.6**: Results panel: histogram of output, percentile table, Tornado chart
- **FR-7.7**: Communication: PostMessageBridge (JS ↔ C++ XLL)

### FR-8: Reporting
- **FR-8.1**: One-click export to PDF/HTML via Quarto (already integrated in NEVEN base)
- **FR-8.2**: Report includes: assumptions summary, distribution fits, simulation parameters, result histogram, percentiles, Tornado chart
- **FR-8.3**: Auditable and reproducible (all parameters documented)

### FR-9: Excel Integration
- **FR-9.1**: Results written back to Excel cells (summary statistics, percentile table)
- **FR-9.2**: Array formula support for full result vector (dynamic arrays)
- **FR-9.3**: Named functions: `=SIM.Run()`, `=SIM.Percentile()`, `=SIM.Sensitivity()`
- **FR-9.4**: Status indicator during long simulations

---

## Non-Functional Requirements

### NFR-1: Performance
- 1,000,000 iterations with 5 variables must complete in < 10 seconds (Julia JIT compiled)
- WebViewer PDF redraw on slider change must respond in < 200ms
- No Excel freeze during simulation (async execution)

### NFR-2: Modularity
- NEVEN-SIM.xll must not modify NEVEN64.xll
- NEVEN-SIM depends on NEVEN base for: R/Julia/Python engines, WebView2, Protobuf IPC
- If NEVEN base is not loaded, NEVEN-SIM shows informative error

### NFR-3: Data Integrity
- Protobuf for all inter-engine data transport (typed, versioned)
- No silent data truncation for arrays > 1M elements
- Simulation results stored with full precision (Float64)

### NFR-4: Usability
- Zero-code operation for basic simulations (GUI-driven via WebViewer)
- Power users can write custom Julia model functions for advanced scenarios
- Tooltips and help text for all parameters in the WebViewer UI

### NFR-5: Compatibility
- Windows 10+ (64-bit)
- Excel 2016+ / Microsoft 365
- NEVEN v2.0+ as base dependency
- R 4.4+, Julia 1.12+

---

## Constraints

- **C-1**: NEVEN-SIM is a separate XLL that loads alongside NEVEN64.xll (not a modification)
- **C-2**: The XLL (C++) is the orchestrator — Python is NOT the coordinator
- **C-3**: Monte Carlo runs entirely inside Julia (no Excel recalculation loop)
- **C-4**: All inter-engine communication uses existing Named Pipe + Protobuf infrastructure
- **C-5**: WebViewer UI is built with standard HTML/CSS/JS (no additional frameworks beyond Plotly.js)
- **C-6**: Must work without internet connection after initial package installation

---

## Phasing

### Phase 1 (MVP)
- FR-1 (Assumption definition)
- FR-2 (Distribution fitting via R)
- FR-5.1-5.4 (Basic Monte Carlo in Julia, single-period)
- FR-6 (Sensitivity/Tornado)
- FR-7 (WebViewer workspace, basic)
- FR-9.1-9.2 (Results to Excel)

### Phase 2 (Advanced)
- FR-3 (Time Series forecasting)
- FR-4 (Copulas/dependencies)
- FR-5.5-5.6 (Multi-period + parallelization)
- FR-7.4 (Reactive sliders with live redraw)
- FR-8 (Quarto reports)
- Optimization under uncertainty (OptQuest-like, using BlackBoxOptim.jl)

---

## Acceptance Criteria Summary

| Requirement | Acceptance Criteria |
|-------------|--------------------|
| FR-1 | User selects range → system identifies it as assumption with type and parameters |
| FR-2 | R fits ≥ 4 candidate distributions and returns ranked results with GoF stats |
| FR-5 | Julia runs 1M iterations in < 10s and returns correct percentile statistics |
| FR-6 | Tornado chart correctly identifies most impactful variable by Spearman rank |
| FR-7 | WebViewer opens, shows assumptions, runs simulation, displays results |
| FR-9 | Percentiles and statistics appear in Excel cells after simulation |

---

*NEVEN-SIM v1.0 — Requirements Document*
*Author: Minor Bonilla Gomez | Date: July 2026*
