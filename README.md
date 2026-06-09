# NEVEN — Open Source Polyglot Infrastructure for Excel

[![Build](https://img.shields.io/badge/build-CMake_3.15+-blue)](CMakeLists.txt) [![Tests](https://img.shields.io/badge/tests-228_passing-brightgreen)]() [![License](https://img.shields.io/badge/license-GPL_v3-green)](LICENSE) [![C++](https://img.shields.io/badge/C++-17-orange)](CMakeLists.txt) [![Quality](https://img.shields.io/badge/quality-8.9%2F10-brightgreen)]()

> **NEVEN** transforms Microsoft Excel into an auditable data science environment by integrating **R**, **Julia**, and **Python** as embedded scripting engines. Execute statistical models, machine learning, and interactive visualizations directly from Excel cells — with full transparency and reproducibility.

> Creo fielmente en un mundo más igualitario en el que todos podamos colaborar. NEVEN es una invitación a construir comunidad, a compartir conocimiento sin barreras, y a inspirar a otros a crear un mundo donde la humanidad avance junta, no dividida.

---

## Key Features

| Feature | Description |
|---|---|
| **Multi-language** | R 4.4.1, Julia 1.12.6, Python 3.10+ running simultaneously from Excel |
| **95+ Functions** | Complete R4XCL statistical library (regression, ACP, SVM, time series, panel data, text mining) |
| **Interactive Graphics** | Plotly, D3.js, Sankey, dashboards → HTML with zoom, hover, tooltips via WebView2 |
| **Pluto Notebooks** | Reactive Julia notebooks with Excel↔Julia↔Pluto data pipeline |
| **Quarto Integration** | Render .qmd documents directly from Excel cells |
| **AI Integration** | Local LLM support (LM Studio, Ollama) via `=P.ai_call()` |
| **Sandbox Security** | 30+ blocked patterns (shell, file, network, native code, bypass prevention) |
| **228 Unit Tests** | GTest framework with security, config, conversion, IPC, and reliability coverage |
| **Function Discovery** | Auto-maps R/Julia docstrings to Excel's Function Wizard (Shift+F3) |
| **Hot Reload** | Automatic re-sourcing when `.R` files change |
| **Centralized Config** | JSON configuration with path validation and security checks |
| **CI/CD** | GitHub Actions pipeline for automated build and test |

---

## Quick Start

### From Excel

```
=NEVEN.r("1+1")                           → 2
=NEVEN.r("sqrt(144)")                      → 12
=NEVEN.j("sqrt(144)")                      → 12
=R.MR_Lineal(Y, X, 1)                     → Linear regression
=R.AD_Dashboard(Data, 0)                   → Interactive dashboard
=NEVEN.r("system('dir')")                  → BLOCKED (sandbox)
```

### Writing Custom Functions

Create a file in `Documents\NEVEN\functions\my_functions.R`:

```r
MiSuma <- function(a, b) a + b
attr(MiSuma, "description") <- list("Suma dos valores", a="Primer valor", b="Segundo valor")
attr(MiSuma, "category") <- "Mis Funciones"
```

Use in Excel: `=R.MiSuma(A1, B1)` — appears in Function Wizard with description.

---

## Architecture

```
┌───────────────────────────────────────────┐
│           Microsoft Excel                  │
│  ┌─────────────────────────────────────┐  │
│  │          NEVEN64.xll                 │  │
│  │  • Registers R./J./P. functions      │  │
│  │  • Sandbox validates code            │  │
│  │  • Converts Excel ↔ Protobuf         │  │
│  │  • WebView2 viewer management        │  │
│  └────────────────┬────────────────────┘  │
└───────────────────┼───────────────────────┘
                    │ Named Pipes + Protobuf
          ┌─────────┼─────────┐
     ┌────┴────┐  ┌─┴──────┐  ┌────┴─────┐
     │ControlR │  │Control  │  │Control   │
     │  .exe   │  │Julia.exe│  │Python.exe│
     │ R 4.4.1 │  │Jl 1.12.6│  │Py 3.10+  │
     └─────────┘  └─────────┘  └──────────┘
```

**Design principles:**
- **Process isolation** — R/Julia/Python crashes don't kill Excel
- **Language-agnostic protocol** — adding a new language = creating a ControlX.exe
- **RAII memory management** — zero leaks in Excel type lifecycle
- **Auditable** — every cell result traces back to visible source code

---

## Building from Source

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Visual Studio | 2022 | C++ Desktop Development workload |
| CMake | 3.15+ | Included with VS 2022 |
| R | 4.4.1+ | For ControlR.exe |
| Julia | 1.12.6+ | For ControlJulia.exe (optional) |
| Python | 3.10+ | For ControlPython.exe (optional) |

### Build Commands

```powershell
# Full build
.\build.ps1

# Build + run tests
.\build.ps1 -Test

# Clean build + tests + package distribution
.\build.ps1 -Clean -Test -Package

# Debug build
.\build.ps1 -Config Debug
```

Or manually with CMake:

```cmd
cmake -S . -B Build -A x64
cmake --build Build --config Release --parallel
```

### Running Tests

```powershell
.\build.ps1 -Test
```

Or directly:

```cmd
Build\tests\Release\rj2xcl_tests.exe
```

Expected: `228 tests from 24 test suites — 228 passing, 0 failed`

### CI-Only Build (no R/Julia/Python needed)

```cmd
cmake -S . -B Build -A x64 -DSKIP_LANGUAGE_TARGETS=ON
cmake --build Build --config Release --target rj2xcl_tests
```

---

## Repository Structure

```
NEVEN/
├── Core/              → NEVEN_Core (NEVEN64.xll) — heart of the project
├── ControlR/          → ControlR.exe — R integration
├── ControlJulia/      → ControlJulia.exe — Julia integration
├── ControlPython/     → ControlPython.exe — Python/AI integration
├── Common/            → Common.lib — shared utilities (pipes, config, security)
├── PB/                → PB.lib — Protocol Buffers (variable.proto)
├── Ribbon/            → NEVENRibbon.dll — COM Ribbon add-in
├── Addin/             → XLL packaging and CustomUI
├── Install/           → Installer scripts and configuration
├── Include/           → Mock headers for R, Julia, Excel SDK
├── OfficeTypes/       → Pre-generated COM type libraries
├── tests/             → 228 tests with GTest v1.14.0
├── libreria/R/        → R4XCL function library (~95 functions, 34 files)
├── libreria/JULIA/    → Julia J4XCL modules (5 files)
├── libreria/PYTHON/   → Python AI functions
├── startup/           → R, Julia, Python startup scripts
├── scripts/           → Build and maintenance automation
├── notebooks/         → Example Pluto/R notebooks
├── docs/              → Full project documentation
├── CMakeLists.txt     → Top-level CMake configuration
├── build.ps1          → One-command build automation
└── CONTRIBUTING.md    → How to contribute
```

---

## Installing for End Users

Download the latest release from [GitHub Releases](https://github.com/minor-bonilla/NEVEN/releases) and run `Install-NEVEN.exe`. The installer:

1. Detects installed R, Julia, and Python automatically
2. Deploys binaries to `C:\NEVEN\`
3. Registers the XLL in Excel
4. Installs required R/Julia/Python packages
5. Creates user directories in `Documents\NEVEN\`

See [docs/ANTES_DE_INICIAR.md](docs/ANTES_DE_INICIAR.md) for the first-use guide.

---

## Security

NEVEN includes a comprehensive sandbox for `=NEVEN.r()` and `=NEVEN.j()` cells:

- **Shell execution**: `system()`, `shell()`, `run()`, backtick literals → BLOCKED
- **File manipulation**: `file.remove()`, `unlink()`, `rm()` → BLOCKED
- **Network access**: `download.file()`, `url()` → BLOCKED
- **Native code**: `.Call()`, `ccall()`, `dyn.load()` → BLOCKED
- **Dynamic bypass**: `eval(parse())`, `paste()` concatenation → BLOCKED
- **Config validation**: Path traversal and command injection in JSON → BLOCKED

Registered functions (`=R.MR_Lineal(...)`) bypass the sandbox — they execute pre-loaded, trusted code.

---

## Documentation

Full documentation is in `docs/`:

| Document | Description |
|---|---|
| [Antes de Iniciar](docs/ANTES_DE_INICIAR.md) | First-use guide |
| [Contributing](CONTRIBUTING.md) | Development setup, coding standards, PR process |
| [Changelog](CHANGELOG.md) | Version history |
| [docs/Arquitectura/](docs/Arquitectura/) | 4-layer architecture documentation |
| [docs/Mantenimiento/](docs/Mantenimiento/) | Build, deploy, troubleshooting |
| [docs/Estado/](docs/Estado/) | Function catalog and project state |
| [docs/Evaluaciones/](docs/Evaluaciones/) | Technical evaluations and audits |
| [docs/Requerimientos/](docs/Requerimientos/) | Feature specifications |

---

## System Requirements

| Component | Requirement |
|---|---|
| **OS** | Windows 10+ (64-bit) |
| **Excel** | 2013, 2016, 2019, or Microsoft 365 (64-bit recommended) |
| **R** | 4.4.1+ (required for statistical functions) |
| **Julia** | 1.12.6+ (optional — math/ML) |
| **Python** | 3.10+ (optional — AI functions) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and the PR process.

If this project is useful to you, share it. If you can improve it, contribute. Together we go further.

---

## License

GNU General Public License v3.0 — See [LICENSE](LICENSE)

---

*Created by Minor Bonilla G. — Building community, one function at a time.*
