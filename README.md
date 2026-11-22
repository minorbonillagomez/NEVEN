# NEVEN

[![NEVEN Build and Test](https://github.com/minorbonillagomez/NEVEN/actions/workflows/build-and-test.yml/badge.svg?branch=master)](https://github.com/minorbonillagomez/NEVEN/actions/workflows/build-and-test.yml)

**Add-in de Microsoft Excel que ejecuta R, Julia y Python desde celdas de hoja de cálculo.**

NEVEN es un add-in XLL escrito en C++17 que embebe tres motores de scripting en procesos
independientes y los expone como funciones nativas de Excel. Una celda puede llamar a un modelo de
R, a una simulación en Julia o a un script de Python, y recibir el resultado como valor, tabla o
gráfico interactivo.

```excel
=NEVEN.r("lm(mpg ~ wt, data = mtcars)")
=NEVEN.j("using Statistics; mean(rand(10_000))")
=NEVEN.P("import numpy as np; np.linalg.svd(A)")
```

## Arquitectura

Cuatro capas, con los motores aislados en procesos hijo para que un fallo en el lenguaje no derribe
Excel.

| Componente | Qué hace |
|---|---|
| `NEVEN64.xll` | Add-in principal que Excel carga. Registra las funciones y orquesta el resto |
| `ControlR.exe` | Embebe R 4.4.1 |
| `ControlJulia.exe` | Embebe Julia 1.12.6 |
| `ControlPython.exe` | Embebe Python 3.13 (Stable ABI) |
| `NEVENRibbon.dll` | Pestaña nativa en la cinta de Excel (COM add-in) |
| TaskPane | Interfaz web de nueve módulos servida en local |

La comunicación entre el XLL y los procesos de lenguaje usa **Named Pipes de Windows con Protocol
Buffers**. El visor de resultados es **WebView2**, e integra notebooks reactivos de **Pluto.jl** y
documentos de **Quarto**.

## Estructura del repositorio

El proyecto vive bajo `src/`. El resto de la raíz es soporte.

```
src/              Código fuente: Core, ControlR, ControlJulia, ControlPython,
                  Common, PB, Ribbon, NEVEN-SIM, TaskPane, libreria, tests, docs
docs/             Ontologías del proyecto
android/          Cliente Android (NEVEN Launcher)
external/         Dependencias de terceros
.github/          Integración continua
.kiro/            Especificaciones, ontología y bitácora de desarrollo
```

## Construcción

Requisitos: **Visual Studio 2022** con herramientas de C++, **CMake 3.15+**, y los runtimes de R,
Julia y Python si se quieren los motores correspondientes. Protocol Buffers v21.12 y GoogleTest
v1.14.0 se descargan vía `FetchContent`.

```powershell
cmake -S src -B src/Build -DCMAKE_BUILD_TYPE=Release
cmake --build src/Build --config Release
```

El directorio de instalación en producción es `C:\NEVEN\`.

## Tests

**369 tests automatizados en 47 suites**, de los cuales 133 cubren el sandbox de ejecución. Se
ejecutan sin necesidad de Excel, R ni Julia gracias a cabeceras simuladas y a un puente de Excel de
prueba.

```powershell
ctest --test-dir src/Build -C Release --output-on-failure
```

## Librería de funciones

- **R:** 93 definiciones repartidas en 63 ficheros `.R` (paquete `R4XCL`), con descriptores JSON que
  alimentan el asistente de funciones de Excel.
- **Julia:** módulos `J4XCL`, con una imagen de sistema precompilada que elimina el arranque en frío.

## Documentación

| Documento | Contenido |
|---|---|
| `src/docs/Arquitectura/Arquitectura.md` | Arquitectura detallada |
| `src/docs/MANUAL_MANTENIMIENTO.md` | Construcción, despliegue y diagnóstico |
| `src/docs/TROUBLESHOOTING.md` | Problemas conocidos |
| `docs/ontologia/` | Ontología del proyecto: invariantes técnicas por componente |

## Estado de los módulos

**NEVEN-SIM**, el módulo de simulación Monte Carlo, está **congelado** y desactivado en la
construcción (`BUILD_NEVEN_SIM=OFF`). Su alcance original era mayor que el de un módulo y quedó
pendiente de replantear. El motivo y la condición para retomarlo están en
`.kiro/specs/neven-sim/tasks.md`.

## Procedencia

Trabajo de tesis de maestría de **Minor Bonilla Gómez**, Universidad de Costa Rica. El artículo que
describe el sistema está en `src/docs/Paper/`.

Licencia: ver `src/LICENSE`.
