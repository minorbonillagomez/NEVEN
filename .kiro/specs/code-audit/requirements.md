# Requirements Document

## Introduction

Este documento especifica los requerimientos para una auditoría integral del código fuente del proyecto NEVEN, un add-in XLL de C++17 para Microsoft Excel que integra R 4.4.1, Julia 1.12.6 y Python 3.13 como motores de scripting embebidos. La auditoría cubrirá cuatro dimensiones: seguridad, arquitectura, código muerto y calidad de documentación. El entregable es un informe estructurado en español con debilidades priorizadas por severidad, oportunidades de mejora y fortalezas identificadas. La auditoría abarca código C++, R, Julia, Python, TypeScript y archivos de configuración.

## Glossary

- **Auditor**: El sistema o agente que ejecuta el análisis de código y genera el informe de auditoría.
- **Informe_de_Auditoría**: El documento estructurado en español que contiene los hallazgos de la auditoría, organizado por dimensión (seguridad, arquitectura, código muerto, documentación).
- **Hallazgo**: Una observación individual identificada durante la auditoría, clasificada como debilidad, oportunidad de mejora o fortaleza.
- **Severidad**: Clasificación de un hallazgo en una escala de cuatro niveles: Crítica, Alta, Media, Baja.
- **NEVEN_Core**: El proyecto C++ principal (`Core/`) que produce NEVEN.dll (el XLL cargado por Excel).
- **ControlX_Process**: Cualquiera de los procesos hijos (ControlR.exe, ControlJulia.exe, ControlPython.exe) que hospedan un runtime de lenguaje.
- **Common_Lib**: La biblioteca estática compartida (`Common/`) con utilidades de IPC, configuración, seguridad y visualización.
- **Console_App**: La aplicación REPL Electron (`Console/`) escrita en TypeScript.
- **Librería_R**: El conjunto de funciones R (`libreria/R/`) que componen R4XCL.
- **Librería_Julia**: El conjunto de funciones Julia (`libreria/JULIA/`) que componen J4XCL.
- **Startup_Scripts**: Los scripts de inicialización (`startup/`) para R, Julia y Python.
- **Código_Muerto**: Funciones no invocadas, código inalcanzable, bloques comentados y archivos obsoletos que no contribuyen a la funcionalidad activa del sistema.
- **Patrón_Inseguro**: Cualquier construcción de código que introduce vulnerabilidades de seguridad, incluyendo inyección, desbordamiento de buffer, exposición de credenciales o bypass de sandbox.
- **Sandbox**: El mecanismo de aislamiento que restringe las operaciones que los scripts de usuario pueden ejecutar dentro de los motores embebidos.
- **Named_Pipe**: Mecanismo IPC de Windows utilizado para la comunicación bidireccional entre el XLL y cada ControlX_Process.
- **Protobuf**: Protocol Buffers v21.12, el formato de serialización usado para mensajes IPC entre el XLL y los procesos hijos.

## Requirements

### Requerimiento 1: Análisis de Seguridad del Código C++

**User Story:** Como responsable del proyecto, quiero identificar vulnerabilidades de seguridad en el código C++ de NEVEN_Core, Common_Lib y los ControlX_Process, para poder remediar riesgos antes del despliegue en producción.

#### Criterios de Aceptación

1. THE Auditor SHALL analizar todos los archivos `.cc` y `.h` en los directorios `Core/`, `Common/`, `ControlR/`, `ControlJulia/` y `ControlPython/` en busca de Patrones_Inseguros.
2. WHEN el Auditor identifica uso de funciones de manejo de strings sin verificación de límites (strcpy, sprintf, strcat), THE Auditor SHALL registrar un Hallazgo de Severidad Alta con la ubicación exacta del archivo y línea.
3. WHEN el Auditor identifica datos de usuario pasados directamente a llamadas de sistema (CreateProcess, ShellExecute, system), THE Auditor SHALL registrar un Hallazgo de Severidad Crítica por riesgo de inyección de comandos.
4. WHEN el Auditor identifica credenciales, tokens o rutas sensibles hardcodeadas en el código fuente, THE Auditor SHALL registrar un Hallazgo de Severidad Crítica por exposición de credenciales.
5. WHEN el Auditor identifica handles de Named_Pipe sin validación antes de operaciones de lectura o escritura, THE Auditor SHALL registrar un Hallazgo de Severidad Alta por uso de handle inválido.
6. WHEN el Auditor identifica memoria asignada con new o malloc sin liberación correspondiente en todas las rutas de ejecución, THE Auditor SHALL registrar un Hallazgo de Severidad Media por fuga de memoria.
7. WHEN el Auditor identifica mecanismos de Sandbox que pueden ser evadidos por scripts de usuario, THE Auditor SHALL registrar un Hallazgo de Severidad Crítica por bypass de sandbox.
8. THE Auditor SHALL verificar que las comunicaciones por Named_Pipe validan la integridad y autenticidad de los mensajes Protobuf recibidos.

### Requerimiento 2: Análisis de Seguridad de Scripts Embebidos

**User Story:** Como responsable del proyecto, quiero identificar riesgos de seguridad en los scripts R, Julia y Python que se ejecutan dentro de los motores embebidos, para asegurar que la Librería_R, Librería_Julia y Startup_Scripts no introducen vulnerabilidades.

#### Criterios de Aceptación

1. THE Auditor SHALL analizar todos los archivos `.R` en `libreria/R/` y `startup/` en busca de llamadas a funciones peligrosas (system, system2, shell, eval con entrada no sanitizada).
2. THE Auditor SHALL analizar todos los archivos `.jl` en `libreria/JULIA/` y `startup/` en busca de uso de `run`, `eval`, `Meta.parse` con entrada no controlada.
3. THE Auditor SHALL analizar todos los archivos `.py` en `startup/` en busca de uso de `exec`, `eval`, `subprocess`, `os.system` con entrada no sanitizada.
4. WHEN el Auditor identifica un script que ejecuta comandos del sistema operativo con parámetros derivados de entrada de usuario sin sanitización, THE Auditor SHALL registrar un Hallazgo de Severidad Crítica.
5. WHEN el Auditor identifica un script que accede al sistema de archivos fuera del directorio de trabajo esperado sin restricción, THE Auditor SHALL registrar un Hallazgo de Severidad Alta.
6. WHEN el Auditor identifica dependencias externas (paquetes R, Julia o Python) cargadas sin verificación de versión o integridad, THE Auditor SHALL registrar un Hallazgo de Severidad Media.
7. THE Auditor SHALL verificar que los Startup_Scripts no exponen variables de entorno sensibles a los scripts de usuario.

### Requerimiento 3: Análisis de Seguridad de la Console_App

**User Story:** Como responsable del proyecto, quiero identificar vulnerabilidades en la aplicación Electron (Console_App), para prevenir ataques XSS, inyección de código y escalación de privilegios en el REPL.

#### Criterios de Aceptación

1. THE Auditor SHALL analizar todos los archivos `.ts` y `.js` en `Console/` en busca de Patrones_Inseguros específicos de Electron y aplicaciones web.
2. WHEN el Auditor identifica uso de `nodeIntegration: true` o `contextIsolation: false` en la configuración de Electron, THE Auditor SHALL registrar un Hallazgo de Severidad Crítica.
3. WHEN el Auditor identifica inserción de contenido no sanitizado en el DOM (innerHTML, document.write con datos de usuario), THE Auditor SHALL registrar un Hallazgo de Severidad Alta por riesgo de XSS.
4. WHEN el Auditor identifica comunicación IPC entre renderer y main process sin validación de origen o contenido, THE Auditor SHALL registrar un Hallazgo de Severidad Alta.
5. WHEN el Auditor identifica dependencias npm con vulnerabilidades conocidas en `package.json`, THE Auditor SHALL registrar un Hallazgo con Severidad proporcional al CVSS de la vulnerabilidad.
6. THE Auditor SHALL verificar que la Console_App no expone APIs privilegiadas del sistema al contexto del renderer.

### Requerimiento 4: Evaluación de Arquitectura y Diseño

**User Story:** Como responsable del proyecto, quiero una evaluación de la arquitectura de NEVEN que identifique problemas de acoplamiento, cohesión y separación de responsabilidades, para planificar mejoras estructurales.

#### Criterios de Aceptación

1. THE Auditor SHALL evaluar el acoplamiento entre NEVEN_Core, Common_Lib y cada ControlX_Process, midiendo las dependencias directas entre módulos.
2. THE Auditor SHALL evaluar la cohesión de cada módulo principal (Core, Common, ControlR, ControlJulia, ControlPython, Console, Ribbon) verificando que cada módulo tiene una responsabilidad única y bien definida.
3. WHEN el Auditor identifica una clase o módulo con más de una responsabilidad principal, THE Auditor SHALL registrar un Hallazgo de Severidad Media por violación del principio de responsabilidad única.
4. WHEN el Auditor identifica dependencias circulares entre módulos, THE Auditor SHALL registrar un Hallazgo de Severidad Alta con el ciclo completo de dependencias.
5. THE Auditor SHALL evaluar la escalabilidad del diseño IPC (Named_Pipe + Protobuf) para determinar si soporta la adición de nuevos lenguajes sin modificaciones estructurales.
6. THE Auditor SHALL evaluar la consistencia de los patrones de diseño utilizados (Singleton, Factory, Observer) a través de todos los módulos.
7. WHEN el Auditor identifica código que mezcla lógica de negocio con lógica de presentación o infraestructura, THE Auditor SHALL registrar un Hallazgo de Severidad Media por violación de separación de capas.
8. THE Auditor SHALL evaluar la testabilidad de la arquitectura, verificando que las dependencias externas (Excel, R, Julia, Python) están abstraídas detrás de interfaces que permiten mocking.
9. WHEN el Auditor identifica patrones de diseño bien implementados que facilitan mantenimiento y extensibilidad, THE Auditor SHALL registrar un Hallazgo positivo como fortaleza.

### Requerimiento 5: Detección de Código Muerto en C++

**User Story:** Como desarrollador, quiero identificar código muerto en los módulos C++ del proyecto, para reducir la complejidad del mantenimiento y el tamaño del binario.

#### Criterios de Aceptación

1. THE Auditor SHALL identificar funciones definidas en archivos `.cc` y `.h` de `Core/`, `Common/`, `ControlR/`, `ControlJulia/` y `ControlPython/` que no son invocadas desde ningún otro punto del código fuente.
2. THE Auditor SHALL identificar bloques de código comentados (más de 5 líneas consecutivas) en todos los archivos C++ del proyecto.
3. THE Auditor SHALL identificar directivas de preprocesador (`#ifdef`, `#if 0`) que encierran código que no se compila en ninguna configuración activa del CMakeLists.txt.
4. WHEN el Auditor identifica un archivo `.cc` o `.h` completo que no es referenciado por ningún CMakeLists.txt ni incluido por otro archivo, THE Auditor SHALL registrar un Hallazgo de Severidad Baja como archivo obsoleto.
5. WHEN el Auditor identifica funciones exportadas del XLL que no están registradas en la tabla de funciones de Excel, THE Auditor SHALL registrar un Hallazgo de Severidad Media.
6. THE Auditor SHALL identificar variables miembro de clase que son asignadas pero nunca leídas.
7. WHEN el Auditor identifica código muerto que fue funcional en versiones anteriores (especialmente código Python deprecado), THE Auditor SHALL registrar un Hallazgo de Severidad Baja con recomendación de eliminación.

### Requerimiento 6: Detección de Código Muerto en Scripts

**User Story:** Como desarrollador, quiero identificar funciones y archivos no utilizados en la Librería_R, Librería_Julia y Startup_Scripts, para simplificar el mantenimiento de los scripts.

#### Criterios de Aceptación

1. THE Auditor SHALL identificar funciones definidas en `libreria/R/` que no son invocadas desde ningún otro archivo R, ni referenciadas desde el código C++ o la documentación como funciones disponibles para el usuario.
2. THE Auditor SHALL identificar funciones exportadas en `libreria/JULIA/` que no son invocadas desde ningún otro archivo Julia ni referenciadas desde el código C++ o la documentación.
3. THE Auditor SHALL identificar archivos completos en `libreria/R/` o `libreria/JULIA/` que no son cargados por los Startup_Scripts ni referenciados por el sistema de auto-carga.
4. WHEN el Auditor identifica funciones de script que duplican funcionalidad ya provista por otra función en la misma librería, THE Auditor SHALL registrar un Hallazgo de Severidad Baja con recomendación de consolidación.
5. THE Auditor SHALL identificar código comentado (más de 3 líneas consecutivas) en archivos R y Julia.
6. WHEN el Auditor identifica scripts Python residuales del período de integración deprecada, THE Auditor SHALL registrar un Hallazgo de Severidad Baja con recomendación de archivo o eliminación.

### Requerimiento 7: Detección de Código Muerto en Console_App

**User Story:** Como desarrollador, quiero identificar código TypeScript no utilizado en la Console_App, para reducir el tamaño del bundle y la complejidad.

#### Criterios de Aceptación

1. THE Auditor SHALL identificar funciones y clases exportadas en `Console/src/` que no son importadas por ningún otro módulo.
2. THE Auditor SHALL identificar archivos TypeScript en `Console/src/` que no son importados directa o transitivamente desde los puntos de entrada (`main.js`, `renderer.ts`, `REPL.ts`).
3. WHEN el Auditor identifica dependencias declaradas en `Console/package.json` que no son importadas por ningún archivo del proyecto, THE Auditor SHALL registrar un Hallazgo de Severidad Baja como dependencia no utilizada.
4. THE Auditor SHALL identificar rutas de código condicional en TypeScript que son inalcanzables dado el flujo de datos estático.
5. WHEN el Auditor identifica assets (CSS, imágenes, fuentes) en `Console/` que no son referenciados por ningún archivo HTML o TypeScript, THE Auditor SHALL registrar un Hallazgo de Severidad Baja.

### Requerimiento 8: Evaluación de Calidad de Documentación

**User Story:** Como responsable del proyecto, quiero evaluar la calidad y completitud de la documentación existente en `docs/`, para identificar brechas entre el código actual y lo documentado.

#### Criterios de Aceptación

1. THE Auditor SHALL verificar que cada módulo principal (Core, Common, ControlR, ControlJulia, ControlPython, Console, Ribbon) tiene documentación correspondiente en `docs/`.
2. THE Auditor SHALL verificar que las funciones públicas exportadas del XLL están documentadas en la documentación de API (`docs/api/`).
3. WHEN el Auditor identifica una función pública sin documentación Doxygen en su header, THE Auditor SHALL registrar un Hallazgo de Severidad Baja.
4. WHEN el Auditor identifica discrepancias entre el comportamiento documentado y la implementación actual del código, THE Auditor SHALL registrar un Hallazgo de Severidad Media por documentación desactualizada.
5. THE Auditor SHALL evaluar la consistencia terminológica entre los documentos en `docs/`, verificando que los mismos conceptos usan los mismos nombres.
6. THE Auditor SHALL verificar que los procedimientos de build, deploy y troubleshooting documentados en `docs/Mantenimiento/` corresponden a los scripts y configuraciones actuales del proyecto.
7. WHEN el Auditor identifica secciones de documentación marcadas como TODO, FIXME o pendientes, THE Auditor SHALL registrar un Hallazgo de Severidad Baja con la ubicación.
8. THE Auditor SHALL evaluar la cobertura de documentación de la Librería_R y Librería_Julia, verificando que cada función exportada tiene descripción de parámetros, valor de retorno y al menos un ejemplo de uso.
9. WHEN el Auditor identifica documentación bien estructurada, completa y actualizada, THE Auditor SHALL registrar un Hallazgo positivo como fortaleza.

### Requerimiento 9: Análisis de Archivos de Configuración

**User Story:** Como responsable del proyecto, quiero que la auditoría incluya los archivos de configuración (CMake, JSON, YAML, workflows), para identificar configuraciones inseguras, obsoletas o inconsistentes.

#### Criterios de Aceptación

1. THE Auditor SHALL analizar todos los archivos `CMakeLists.txt` verificando que las opciones de compilación incluyen flags de seguridad apropiados para C++17 en MSVC.
2. WHEN el Auditor identifica flags de compilación que desactivan protecciones de seguridad (desactivación de ASLR, stack canaries, DEP), THE Auditor SHALL registrar un Hallazgo de Severidad Alta.
3. THE Auditor SHALL analizar los archivos de configuración JSON (`neven-config.json`, `package.json`, `tsconfig.json`) verificando que no contienen valores sensibles hardcodeados.
4. THE Auditor SHALL analizar los workflows de GitHub Actions (`.github/workflows/`) verificando que no exponen secretos en logs y que usan versiones fijadas de acciones.
5. WHEN el Auditor identifica permisos excesivos en workflows de CI/CD, THE Auditor SHALL registrar un Hallazgo de Severidad Media.
6. THE Auditor SHALL verificar que los archivos `.gitignore` excluyen adecuadamente archivos de build, credenciales, y artefactos temporales.
7. WHEN el Auditor identifica archivos sensibles (claves privadas, tokens, archivos .env) que no están excluidos por `.gitignore`, THE Auditor SHALL registrar un Hallazgo de Severidad Crítica.

### Requerimiento 10: Estructura y Formato del Informe de Auditoría

**User Story:** Como responsable del proyecto, quiero que el informe de auditoría tenga una estructura clara y consistente, para facilitar la priorización y seguimiento de las acciones correctivas.

#### Criterios de Aceptación

1. THE Auditor SHALL generar el Informe_de_Auditoría en idioma español.
2. THE Informe_de_Auditoría SHALL contener las siguientes secciones en orden: Resumen Ejecutivo, Metodología, Hallazgos de Seguridad, Hallazgos de Arquitectura, Hallazgos de Código Muerto, Hallazgos de Documentación, Fortalezas Identificadas, Recomendaciones Priorizadas, Anexos.
3. THE Auditor SHALL clasificar cada Hallazgo negativo con una Severidad (Crítica, Alta, Media, Baja) y una categoría (Seguridad, Arquitectura, Código_Muerto, Documentación).
4. THE Auditor SHALL incluir para cada Hallazgo: identificador único, título descriptivo, descripción detallada, ubicación en el código (archivo y línea cuando aplique), severidad, categoría, y recomendación de remediación.
5. THE Auditor SHALL incluir un Resumen Ejecutivo con conteo de hallazgos por severidad y categoría, y una puntuación general de salud del código en escala 1-10.
6. THE Auditor SHALL incluir una sección de Fortalezas Identificadas que destaque patrones positivos, buenas prácticas y decisiones de diseño acertadas encontradas durante la auditoría.
7. THE Auditor SHALL incluir una sección de Recomendaciones Priorizadas ordenada por impacto (de mayor a menor), donde cada recomendación referencia los hallazgos que resuelve.
8. WHEN el Auditor completa el análisis de todos los módulos, THE Auditor SHALL generar una tabla resumen con métricas: total de archivos analizados, total de líneas de código, hallazgos por severidad, y cobertura de la auditoría por módulo.

### Requerimiento 11: Cobertura y Alcance de la Auditoría

**User Story:** Como responsable del proyecto, quiero asegurar que la auditoría cubre todos los lenguajes y componentes del proyecto de forma exhaustiva, para no dejar puntos ciegos.

#### Criterios de Aceptación

1. THE Auditor SHALL analizar código en los siguientes lenguajes: C++ (.cc, .h), R (.R), Julia (.jl), Python (.py), TypeScript (.ts), JavaScript (.js).
2. THE Auditor SHALL analizar archivos de configuración en los siguientes formatos: CMake (CMakeLists.txt), JSON (.json), YAML (.yml), XML (.xml), Protocol Buffers (.proto).
3. THE Auditor SHALL cubrir los siguientes directorios del proyecto: Core/, Common/, ControlR/, ControlJulia/, ControlPython/, Console/, Ribbon/, PB/, tests/, startup/, libreria/R/, libreria/JULIA/, docs/, Addin/, .github/.
4. THE Auditor SHALL registrar en el Informe_de_Auditoría la lista completa de archivos analizados y archivos excluidos (con justificación de exclusión).
5. WHEN el Auditor encuentra un directorio o archivo que no puede analizar (binarios, archivos generados, dependencias de terceros), THE Auditor SHALL documentar la exclusión con justificación en la sección de Metodología del informe.
6. THE Auditor SHALL analizar los 245 tests en `tests/` evaluando cobertura de casos, calidad de assertions y presencia de tests para las funcionalidades críticas de seguridad.
