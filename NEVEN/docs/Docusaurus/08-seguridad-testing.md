---
id: seguridad-testing
title: Capitulo 8 -- Seguridad y Testing
sidebar_label: 8. Seguridad y Testing
sidebar_position: 8
---

# Capitulo 8: Seguridad y Testing

## 8.1 Sandbox de seguridad

Cuando el usuario ejecuta codigo arbitrario con `=NEVEN.r("...")` o `=NEVEN.j("...")`, el sandbox bloquea operaciones peligrosas **antes** de enviarlas al motor.

### Patrones bloqueados en R

| Categoria | Comandos bloqueados |
|:---|:---|
| Shell | `system()`, `system2()`, `shell()`, `shell.exec()`, `pipe()` |
| Archivos | `file.remove()`, `unlink()`, `file.rename()` |
| Red | `download.file()`, `url()`, `socketConnection()` |
| Codigo dinamico | `eval(parse())`, `do.call()`, `get()`, `.Call()` |
| Entorno | `Sys.setenv()`, `setwd()` |

### Patrones bloqueados en Julia

| Categoria | Comandos bloqueados |
|:---|:---|
| Shell | `run()`, `pipeline()`, backtick literals |
| Codigo nativo | `ccall()`, `@ccall`, `cglobal()`, `unsafe_*` |
| Codigo dinamico | `eval()`, `Meta.parse()`, `include()` |

### Proteccion contra bypass

$
\texttt{sys tem()} \xrightarrow{\text{strip whitespace}} \texttt{system()} \xrightarrow{\text{match}} \text{BLOQUEADO}
$

- Whitespace stripping normaliza antes de comparar
- String concatenation (`paste0("sys","tem()")`) se detecta
- Case insensitive: `SYSTEM()` = `system()`

### Verificacion de integridad SHA-256

Al iniciar, NEVEN calcula el hash SHA-256 de los scripts criticos (`startup.r`, `startup.jl`) y lo compara con el valor almacenado. Si el hash no coincide, el motor correspondiente no se carga y se registra una advertencia en el log. Esto previene la ejecucion de scripts modificados por terceros.

$
\text{SHA-256}(\texttt{startup.r}) = h_{\text{actual}} \stackrel{?}{=} h_{\text{esperado}} \quad \Rightarrow \quad \begin{cases} \text{OK: cargar motor} \\ \text{FAIL: bloquear + log} \end{cases}
$

:::note
Las funciones registradas (`=R.MR_Lineal(...)`, `=J.Algebra(...)`) **no** pasan por el sandbox -- se ejecutan directamente via el pipe.
:::

## 8.2 Validacion de configuracion

`ConfigService` valida `neven-config.json` al cargar:

- Paths no contienen `..` (path traversal)
- Paths no contienen `|`, `&`, `;`, `` ` `` (command injection)
- `callTimeoutMs` en rango $[0, 1\,800\,000]$
- `maxRetries` en rango $[0, 10]$

## 8.3 Suite de tests

| Categoria | Tests | Cobertura |
|:---|:---:|:---|
| Sandbox (R + Julia + Python) | 109 | Patrones bloqueados, bypass prevention |
| NewFunctionsSandboxTest | 16 | Pivot, D3, Esquisse, Map sandbox validation |
| E2ETest | 8 | Rename verification, config keys, version |
| Property-based (reliability) | 3 | Timeout clamping, error messages |
| Property-based (WebView2) | 5 | Size routing, content detection, config clamping |
| Property-based (Python sandbox) | 3 | 450 iteraciones |
| Config, Security, Discovery | 16 | Singleton, JSON, path validation |
| Type conversions, RAII | 7 | Thread safety, move semantics |
| Reliability (unit) | 35 | Health status, error formats, timeouts |
| Basic functions, COM, callbacks | 27 | Version, bounds, input validation |
| **Total** | **228** | **100% pass rate, 0 regresiones** |

### Property-Based Testing

Los tests PBT verifican propiedades universales con entradas aleatorias:

$
\forall V \in \mathbb{Z}: \text{clamp}(V, 1, 16) = \max(1, \min(16, V))
$

Cada propiedad se verifica con 150 iteraciones minimo usando `std::mt19937`.

## 8.4 Compilacion y ejecucion de tests

```powershell
# Compilar
cmake --build Build --config Release --parallel

# Ejecutar tests
.\Build\tests\Release\rj2xcl_tests.exe
```

Resultado esperado:
```
[==========] 228 tests from 27 test suites ran.
[  PASSED  ] 228 tests.
```
