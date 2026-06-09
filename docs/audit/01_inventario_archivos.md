# Inventario de Archivos del Proyecto NEVEN

## Resumen General

| Métrica | Valor |
|---------|-------|
| **Total de archivos descubiertos** | 1,121 |
| **Directorios analizados** | 15 |
| **Lenguajes de programación** | 6 (C++, R, Julia, Python, TypeScript, JavaScript) |
| **Tipos de configuración** | 5 (CMake, JSON, YAML, XML, Protobuf) |

## Clasificación por Lenguaje

| Lenguaje | Extensiones | Archivos |
|----------|-------------|----------|
| C++ | .cc, .h, .cpp, .hpp, .c | 195 |
| JavaScript | .js | 277 |
| TypeScript | .ts | 41 |
| R | .R | 34 |
| Julia | .jl | 6 |
| Python | .py | 1 |
| **Total código fuente** | | **554** |

> **Nota**: La mayoría de archivos JavaScript (274 de 277) están en `docs/api/html/` y son generados por Doxygen. Solo 3 archivos .js son código fuente del proyecto (en Console/).

## Clasificación por Configuración

| Tipo | Extensión/Nombre | Archivos |
|------|-----------------|----------|
| CMake | CMakeLists.txt | 9 |
| JSON | .json | 12 |
| YAML | .yml | 1 |
| XML | .xml | 10 |
| Protobuf | .proto | 1 |
| **Total configuración** | | **33** |

## Distribución por Módulo

| Módulo | Total Archivos | Lenguajes Principales |
|--------|---------------|----------------------|
| Core/ | 53 | C++ |
| Common/ | 84 | C++ |
| ControlR/ | 28 | C++ |
| ControlJulia/ | 19 | C++ |
| ControlPython/ | 4 | C++ |
| Console/ | 77 | TypeScript, JavaScript |
| Ribbon/ | 60 | C++ |
| PB/ | 5 | Protobuf, C++ (generado) |
| tests/ | 26 | C++ |
| startup/ | 6 | R, Julia, Python |
| libreria/R/ | 33 | R |
| libreria/JULIA/ | 5 | Julia |
| docs/ | 715 | Markdown, HTML/JS (Doxygen) |
| Addin/ | 2 | CMake, XML |
| .github/ | 4 | YAML, Markdown |

---

## Listado Detallado por Módulo


### Core/ — NEVEN_Core (NEVEN.dll)

**53 archivos** | Lenguaje principal: C++

#### C++ (47 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| Core/include/basic_functions.h | .h | Header |
| Core/include/callback_info.h | .h | Header |
| Core/include/CallbackDispatcher.h | .h | Header |
| Core/include/com_object_map.h | .h | Header |
| Core/include/COMHandler.h | .h | Header |
| Core/include/excel_api_functions.h | .h | Header |
| Core/include/excel_com_type_libraries.h | .h | Header |
| Core/include/file_change_watcher.h | .h | Header |
| Core/include/FileWatchService.h | .h | Header |
| Core/include/function_descriptor.h | .h | Header |
| Core/include/GraphicsHandler.h | .h | Header |
| Core/include/ICallbackHandler.h | .h | Header |
| Core/include/IExcelBridge.h | .h | Header |
| Core/include/language_desc.h | .h | Header |
| Core/include/language_service.h | .h | Header |
| Core/include/LanguageManager.h | .h | Header |
| Core/include/MockExcelBridge.h | .h | Header |
| Core/include/RaiiXlOper.h | .h | Header |
| Core/include/RibbonService.h | .h | Header |
| Core/include/rj2xcl.h | .h | Header |
| Core/include/rj2xcl_graphics.h | .h | Header |
| Core/include/rj2xcl_integration_constants.h | .h | Header |
| Core/include/rj2xcl_version.h | .h | Header |
| Core/include/stdafx.h | .h | Header |
| Core/include/targetver.h | .h | Header |
| Core/include/type_conversions.h | .h | Header |
| Core/include/WinExcelBridge.h | .h | Header |
| Core/resource.h | .h | Header |
| Core/src/basic_functions.cc | .cc | Implementación |
| Core/src/CallbackDispatcher.cc | .cc | Implementación |
| Core/src/com_object_map.cc | .cc | Implementación |
| Core/src/COMHandler.cc | .cc | Implementación |
| Core/src/dllmain.cpp | .cpp | Implementación |
| Core/src/excel_api_functions.cc | .cc | Implementación |
| Core/src/file_change_watcher.cc | .cc | Implementación |
| Core/src/FileWatchService.cc | .cc | Implementación |
| Core/src/GraphicsHandler.cc | .cc | Implementación |
| Core/src/language_desc.cc | .cc | Implementación |
| Core/src/language_service.cc | .cc | Implementación |
| Core/src/LanguageManager.cc | .cc | Implementación |
| Core/src/RaiiXlOper.cc | .cc | Implementación |
| Core/src/REPLLanguageAccessorImpl.cc | .cc | Implementación |
| Core/src/RibbonService.cc | .cc | Implementación |
| Core/src/rj2xcl.cc | .cc | Implementación |
| Core/src/rj2xcl_graphics.cc | .cc | Implementación |
| Core/src/WinExcelBridge.cc | .cc | Implementación |
| Core/src/xlcall_stubs.cc | .cc | Implementación |

#### Configuración (3 archivos)

| Ruta Relativa | Tipo |
|---------------|------|
| Core/CMakeLists.txt | CMake |
| Core/RJ2XCL.vcxproj.xml | XML (VS Project) |
| Core/RJ2XCL.vcxproj.filters.xml | XML (VS Filters) |

#### Otros (3 archivos)

| Ruta Relativa | Extensión | Descripción |
|---------------|-----------|-------------|
| Core/README.md | .md | Documentación |
| Core/RJ2XCL.rc | .rc | Resource script |
| Core/src/rj2xcl.def | .def | Module definition |

---

### Common/ — Common.lib (Utilidades compartidas)

**84 archivos** | Lenguaje principal: C++

#### C++ (82 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| Common/AutoLoader.cc | .cc | Implementación |
| Common/child_log.h | .h | Header |
| Common/child_process_log.cc | .cc | Implementación |
| Common/child_process_log.h | .h | Header |
| Common/ConfigService.cc | .cc | Implementación |
| Common/ConfigService.h | .h | Header |
| Common/Constants.h | .h | Header |
| Common/ContentPipeline.cc | .cc | Implementación |
| Common/ContentPipeline.h | .h | Header |
| Common/CrashHandler.cc | .cc | Implementación |
| Common/CrashHandler.h | .h | Header |
| Common/debug_functions.cc | .cc | Implementación |
| Common/debug_functions.h | .h | Header |
| Common/DiagnosticRouter.cc | .cc | Implementación |
| Common/DiagnosticRouter.h | .h | Header |
| Common/DiscoveryService.cc | .cc | Implementación |
| Common/DiscoveryService.h | .h | Header |
| Common/EnvService.cc | .cc | Implementación |
| Common/EnvService.h | .h | Header |
| Common/GCMonitor.cc | .cc | Implementación |
| Common/json11/json11.cpp | .cpp | Implementación (terceros) |
| Common/json11/json11.hpp | .hpp | Header (terceros) |
| Common/LogService.cc | .cc | Implementación |
| Common/LogService.h | .h | Header |
| Common/MenuService.cc | .cc | Implementación |
| Common/MenuService.h | .h | Header |
| Common/message_utilities.cc | .cc | Implementación |
| Common/message_utilities.h | .h | Header |
| Common/module_functions.cc | .cc | Implementación |
| Common/module_functions.h | .h | Header |
| Common/NevenBackgroundConnector.cc | .cc | Implementación |
| Common/NevenBackgroundConnector.h | .h | Header |
| Common/NevenInitOrchestrator.cc | .cc | Implementación |
| Common/NevenInitOrchestrator.h | .h | Header |
| Common/NevenProgressiveRegisterExport.cc | .cc | Implementación |
| Common/NevenProgressiveRegisterExport.h | .h | Header |
| Common/NevenProgressiveRegistrar.cc | .cc | Implementación |
| Common/NevenProgressiveRegistrar.h | .h | Header |
| Common/NevenStartupConfig.cc | .cc | Implementación |
| Common/NevenStartupConfig.h | .h | Header |
| Common/NevenStartupTypes.h | .h | Header |
| Common/NevenStatusBarReporter.cc | .cc | Implementación |
| Common/NevenStatusBarReporter.h | .h | Header |
| Common/NevenWatchdogTimer.cc | .cc | Implementación |
| Common/NevenWatchdogTimer.h | .h | Header |
| Common/NotebookExporter.cc | .cc | Implementación |
| Common/NotebookExporter.h | .h | Header |
| Common/NotebookLibrary.cc | .cc | Implementación |
| Common/NotebookLibrary.h | .h | Header |
| Common/pipe.cc | .cc | Implementación |
| Common/pipe.h | .h | Header |
| Common/PlutoManager.cc | .cc | Implementación |
| Common/PlutoManager.h | .h | Header |
| Common/PostMessageBridge.cc | .cc | Implementación |
| Common/PostMessageBridge.h | .h | Header |
| Common/PresentationBuilder.cc | .cc | Implementación |
| Common/PresentationBuilder.h | .h | Header |
| Common/process_exit_codes.h | .h | Header |
| Common/QuartoService.cc | .cc | Implementación |
| Common/QuartoService.h | .h | Header |
| Common/REPLBridge.cc | .cc | Implementación |
| Common/REPLBridge.h | .h | Header |
| Common/REPLLanguageAccessor.cc | .cc | Implementación |
| Common/REPLLanguageAccessor.h | .h | Header |
| Common/REPLManager.cc | .cc | Implementación |
| Common/REPLManager.h | .h | Header |
| Common/result.h | .h | Header |
| Common/RuntimeLoader.cc | .cc | Implementación |
| Common/SandboxVerifier.cc | .cc | Implementación |
| Common/SecurityService.cc | .cc | Implementación |
| Common/SecurityService.h | .h | Header |
| Common/string_utilities.h | .h | Header |
| Common/UniqueHandle.h | .h | Header |
| Common/user_button.h | .h | Header |
| Common/ViewerManager.cc | .cc | Implementación |
| Common/ViewerManager.h | .h | Header |
| Common/ViewerWindow.cc | .cc | Implementación |
| Common/ViewerWindow.h | .h | Header |
| Common/WindowManager.cc | .cc | Implementación |
| Common/WindowManager.h | .h | Header |
| Common/windows_api_functions.cc | .cc | Implementación |
| Common/windows_api_functions.h | .h | Header |

#### Configuración (1 archivo)

| Ruta Relativa | Tipo |
|---------------|------|
| Common/CMakeLists.txt | CMake |

#### Otros (1 archivo)

| Ruta Relativa | Extensión | Descripción |
|---------------|-----------|-------------|
| Common/README.md | .md | Documentación |

---


### ControlR/ — ControlR.exe (Integración con R)

**28 archivos** | Lenguaje principal: C++

#### C++ (16 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| ControlR/include/console_graphics_device.h | .h | Header |
| ControlR/include/controlr.h | .h | Header |
| ControlR/include/controlr_common.h | .h | Header |
| ControlR/include/convert.h | .h | Header |
| ControlR/include/gdi_graphics_device.h | .h | Header |
| ControlR/include/R_Environment.h | .h | Header |
| ControlR/include/R_ext/Complex.h | .h | Header |
| ControlR/include/spreadsheet_graphics_device.h | .h | Header |
| ControlR/src/console_graphics_device.cc | .cc | Implementación |
| ControlR/src/controlr.cc | .cc | Implementación |
| ControlR/src/convert.cc | .cc | Implementación |
| ControlR/src/gdi_graphics_device.cc | .cc | Implementación |
| ControlR/src/R_Environment.cpp | .cpp | Implementación |
| ControlR/src/rinterface_common.cc | .cc | Implementación |
| ControlR/src/rinterface_win.cc | .cc | Implementación |
| ControlR/src/spreadsheet_graphics_device.cc | .cc | Implementación |

#### Configuración (3 archivos)

| Ruta Relativa | Tipo |
|---------------|------|
| ControlR/CMakeLists.txt | CMake |
| ControlR/ControlR.vcxproj.xml | XML (VS Project) |
| ControlR/ControlR.vcxproj.filters.xml | XML (VS Filters) |

#### Otros (9 archivos)

| Ruta Relativa | Extensión | Descripción |
|---------------|-----------|-------------|
| ControlR/.gitignore | .gitignore | Git ignore |
| ControlR/README.md | .md | Documentación |
| ControlR/lib/R64.def | .def | Definición de exports R |
| ControlR/lib/R64.exp | .exp | Export library |
| ControlR/lib/R64.lib | .lib | Import library |
| ControlR/lib/RebuildLibs.ps1 | .ps1 | Script de build |
| ControlR/lib/RGraphApp64.def | .def | Definición de exports |
| ControlR/lib/RGraphApp64.exp | .exp | Export library |
| ControlR/lib/RGraphApp64.lib | .lib | Import library |

---

### ControlJulia/ — ControlJulia.exe (Integración con Julia)

**19 archivos** | Lenguaje principal: C++

#### C++ (9 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| ControlJulia/include/control_julia.h | .h | Header |
| ControlJulia/include/julia_compat.h | .h | Header |
| ControlJulia/include/Julia_Environment.h | .h | Header |
| ControlJulia/include/julia_interface.h | .h | Header |
| ControlJulia/include/JuliaConversion.h | .h | Header |
| ControlJulia/src/control_julia.cc | .cc | Implementación |
| ControlJulia/src/Julia_Environment.cpp | .cpp | Implementación |
| ControlJulia/src/julia_interface.cc | .cc | Implementación |
| ControlJulia/src/JuliaConversion.cpp | .cpp | Implementación |

#### Configuración (3 archivos)

| Ruta Relativa | Tipo |
|---------------|------|
| ControlJulia/CMakeLists.txt | CMake |
| ControlJulia/ControlJulia.vcxproj.xml | XML (VS Project) |
| ControlJulia/ControlJulia.vcxproj.filters.xml | XML (VS Filters) |

#### Otros (7 archivos)

| Ruta Relativa | Extensión | Descripción |
|---------------|-----------|-------------|
| ControlJulia/.gitignore | .gitignore | Git ignore |
| ControlJulia/README.md | .md | Documentación |
| ControlJulia/lib/libjulia.def | .def | Definición de exports Julia |
| ControlJulia/lib/libjulia.def.txt | .txt | Referencia de exports |
| ControlJulia/lib/libjulia.exp | .exp | Export library |
| ControlJulia/lib/libjulia.lib | .lib | Import library |
| ControlJulia/lib/rebuild-julia-lib.ps1 | .ps1 | Script de build |

---

### ControlPython/ — ControlPython.exe (Integración con Python — DEPRECADO)

**4 archivos** | Lenguaje principal: C++

#### C++ (3 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| ControlPython/include/python_interface.h | .h | Header |
| ControlPython/src/control_python.cc | .cc | Implementación |
| ControlPython/src/python_interface.cc | .cc | Implementación |

#### Configuración (1 archivo)

| Ruta Relativa | Tipo |
|---------------|------|
| ControlPython/CMakeLists.txt | CMake |

> **Nota**: Python está deprecado (OFF por defecto en CMake). Este módulo es código residual.

---

### Console/ — REPL Electron (Aplicación de consola)

**77 archivos** | Lenguajes principales: TypeScript, JavaScript

#### TypeScript (41 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| Console/REPL.ts | .ts | Entry point REPL |
| Console/typings.d.ts | .ts | Type declarations |
| Console/src/common/config_manager.ts | .ts | Gestión de configuración |
| Console/src/common/data_cache.ts | .ts | Cache de datos |
| Console/src/common/file_watcher.ts | .ts | Observador de archivos |
| Console/src/common/message_utilities.ts | .ts | Utilidades de mensajes |
| Console/src/common/observed_proxy.ts | .ts | Proxy observable |
| Console/src/common/properties.ts | .ts | Propiedades |
| Console/src/common/update_check.ts | .ts | Verificación de actualizaciones |
| Console/src/common/utilities.ts | .ts | Utilidades generales |
| Console/src/editor/editor.ts | .ts | Editor |
| Console/src/editor/editor_document.ts | .ts | Documento del editor |
| Console/src/editor/editor_status_bar.ts | .ts | Barra de estado |
| Console/src/editor/julia_tokenizer.ts | .ts | Tokenizador Julia |
| Console/src/io/management_pipe.ts | .ts | Pipe de gestión |
| Console/src/io/pipe.ts | .ts | Comunicación por pipe |
| Console/src/io/stdio_pipe.ts | .ts | Pipe stdio |
| Console/src/json.d.ts | .ts | Type declarations JSON |
| Console/src/renderer.ts | .ts | Entry point renderer |
| Console/src/shell/annotation_addon.ts | .ts | Addon de anotaciones |
| Console/src/shell/cursor_client_position_addon.ts | .ts | Addon de cursor |
| Console/src/shell/custom-fit.ts | .ts | Ajuste personalizado |
| Console/src/shell/fontmetrics.ts | .ts | Métricas de fuente |
| Console/src/shell/graphics_device.ts | .ts | Dispositivo gráfico |
| Console/src/shell/language_interface.ts | .ts | Interfaz de lenguaje |
| Console/src/shell/language_interface_julia.ts | .ts | Interfaz Julia |
| Console/src/shell/language_interface_julia-0.7.ts | .ts | Interfaz Julia 0.7 |
| Console/src/shell/language_interface_r.ts | .ts | Interfaz R |
| Console/src/shell/multiplexed_terminal.ts | .ts | Terminal multiplexado |
| Console/src/shell/png_graphics_device.ts | .ts | Dispositivo gráfico PNG |
| Console/src/shell/svg_graphics_device.ts | .ts | Dispositivo gráfico SVG |
| Console/src/shell/terminal_implementation.ts | .ts | Implementación terminal |
| Console/src/shell/terminal_state.ts | .ts | Estado del terminal |
| Console/src/shell/text_formatter.ts | .ts | Formateador de texto |
| Console/src/ui/alert.ts | .ts | Alertas UI |
| Console/src/ui/dialog.ts | .ts | Diálogos UI |
| Console/src/ui/menu_utilities.ts | .ts | Utilidades de menú |
| Console/src/ui/splitter.ts | .ts | Splitter UI |
| Console/src/ui/tab_panel.ts | .ts | Panel de pestañas |
| Console/src/ui/user_stylesheet.ts | .ts | Estilos de usuario |
| Console/src/ui/virtual_list.ts | .ts | Lista virtual |

#### JavaScript (3 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| Console/main.js | .js | Entry point Electron main |
| Console/generated/variable_pb.js | .js | Protobuf generado |
| Console/script/generate-symbol-table.js | .js | Script de generación |

#### Configuración (12 archivos)

| Ruta Relativa | Tipo |
|---------------|------|
| Console/package.json | JSON (npm) |
| Console/tsconfig.json | JSON (TypeScript) |
| Console/less-watch-compiler.config.json | JSON (LESS compiler) |
| Console/data/constants.json | JSON (constantes) |
| Console/data/default_config.json | JSON (config por defecto) |
| Console/data/symbol_table.json | JSON (tabla de símbolos) |
| Console/data/menus/application_menu.json | JSON (menú app) |
| Console/data/menus/editor_tab_context_menu.json | JSON (menú contexto) |
| Console/data/menus/terminal_context_menu.json | JSON (menú terminal) |
| Console/data/schemas/config.schema.json | JSON (schema config) |
| Console/data/schemas/schema.schema.json | JSON (meta-schema) |
| Console/data/themes/test-theme.json | JSON (tema) |

#### Otros (21 archivos)

| Ruta Relativa | Extensión | Descripción |
|---------------|-----------|-------------|
| Console/.gitignore | .gitignore | Git ignore |
| Console/index.html | .html | Página principal |
| Console/repl.html | .html | Página REPL |
| Console/rj2xcl.ico | .ico | Icono |
| Console/yarn.lock | .lock | Lock de dependencias |
| Console/ext/cogs/cogs.css | .css | Estilos iconos cogs |
| Console/ext/cogs/cogs.woff | .woff | Fuente cogs |
| Console/ext/cogs/README.md | .md | Documentación cogs |
| Console/ext/icomoon.css | .css | Estilos icomoon |
| Console/ext/icomoon.woff | .woff | Fuente icomoon |
| Console/style/alert.less | .less | Estilos alertas |
| Console/style/common.less | .less | Estilos comunes |
| Console/style/dialog.less | .less | Estilos diálogos |
| Console/style/editor.less | .less | Estilos editor |
| Console/style/markdown.less | .less | Estilos markdown |
| Console/style/splitter_window.less | .less | Estilos splitter |
| Console/style/style.less | .less | Estilos principales |
| Console/style/tab_panel.less | .less | Estilos pestañas |
| Console/style/terminal_overlay.less | .less | Estilos overlay |
| Console/style/terminal3.less | .less | Estilos terminal |
| Console/style/virtual-list.less | .less | Estilos lista virtual |

---


### Ribbon/ — NEVENRibbon.dll (COM Ribbon Add-in)

**60 archivos** | Lenguaje principal: C++

#### C++ (10 archivos fuente)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| Ribbon/dllmain.cpp | .cpp | Implementación |
| Ribbon/resource.h | .h | Header |
| Ribbon/resource_utf8.h | .h | Header |
| Ribbon/ribbon.cc | .cc | Implementación |
| Ribbon/ribbon_connect.cc | .cc | Implementación |
| Ribbon/ribbon_connect.h | .h | Header |
| Ribbon/RJ2XCLRibbon_i.c | .c | Implementación COM |
| Ribbon/RJ2XCLRibbon_i.h | .h | Header COM |
| Ribbon/stdafx.cpp | .cpp | Precompiled header |
| Ribbon/stdafx.h | .h | Header |
| Ribbon/targetver.h | .h | Header |

#### Configuración (4 archivos)

| Ruta Relativa | Tipo |
|---------------|------|
| Ribbon/CMakeLists.txt | CMake |
| Ribbon/ribbon_ui.xml | XML (UI definition) |
| Ribbon/RJ2XCLRibbon.vcxproj.xml | XML (VS Project) |
| Ribbon/RJ2XCLRibbon.vcxproj.filters.xml | XML (VS Filters) |

#### Otros (46 archivos)

| Categoría | Archivos | Descripción |
|-----------|----------|-------------|
| Imágenes (.png) | 14 | Iconos del ribbon (16px y 32px) |
| Build artifacts (.obj, .pch, .pdb, .res, .tlb, .tlh) | 10 | Artefactos de compilación |
| Build logs (.tlog, .lastbuildstate) | 15 | Logs de MSBuild |
| COM (.idl, .rgs, .rc, .def, .tlb) | 6 | Archivos COM/ATL |
| Otros (.gitignore, .md) | 2 | Metadatos |

> **Nota**: El directorio `Ribbon/x64/Release/` contiene artefactos de compilación que deberían estar en .gitignore.

---

### PB/ — Protocol Buffers

**5 archivos** | Tipo: Protobuf + C++ generado

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| PB/variable.proto | .proto | Definición Protobuf |
| PB/variable.pb.cc | .cc | C++ generado por protoc |
| PB/variable.pb.h | .h | Header generado por protoc |
| PB/CMakeLists.txt | .txt | CMake |
| PB/build.sh | .sh | Script de build |

---

### tests/ — Suite de Tests (GTest)

**26 archivos** | Lenguaje: C++

#### C++ (26 archivos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| tests/basic_functions_tests.cc | .cc | Tests unitarios |
| tests/callback_behavior_tests.cc | .cc | Tests de callbacks |
| tests/callback_dispatcher_tests.cc | .cc | Tests dispatcher |
| tests/CMakeLists.txt | .txt | CMake |
| tests/common_tests.cc | .cc | Tests Common |
| tests/com_object_map_tests.cc | .cc | Tests COM |
| tests/config_service_tests.cc | .cc | Tests configuración |
| tests/discovery_tests.cc | .cc | Tests discovery |
| tests/e2e_tests.cc | .cc | Tests end-to-end |
| tests/integration_tests.cc | .cc | Tests integración |
| tests/language_service_tests.cc | .cc | Tests language service |
| tests/mock_engine_backend.cc | .cc | Mock del engine |
| tests/new_functions_tests.cc | .cc | Tests nuevas funciones |
| tests/python_reactivation_exploration_pbt.cc | .cc | PBT Python reactivación |
| tests/python_reactivation_preservation_pbt.cc | .cc | PBT Python preservación |
| tests/python_sandbox_pbt.cc | .cc | PBT Python sandbox |
| tests/raii_xloper_tests.cc | .cc | Tests RAII XlOper |
| tests/reliability_pbt.cc | .cc | PBT confiabilidad |
| tests/reliability_tests.cc | .cc | Tests confiabilidad |
| tests/sandbox_tests.cc | .cc | Tests sandbox |
| tests/security_tests.cc | .cc | Tests seguridad |
| tests/type_conversion_tests.cc | .cc | Tests conversión tipos |
| tests/viewer_professional_tests.cc | .cc | Tests viewer |
| tests/webview2_pbt.cc | .cc | PBT WebView2 |
| tests/mocks/mock_language_service.h | .h | Mock language service |
| tests/mocks/mock_type_info.h | .h | Mock type info |

---

### startup/ — Scripts de Inicialización

**6 archivos** | Lenguajes: R, Julia, Python

| Ruta Relativa | Extensión | Lenguaje/Tipo |
|---------------|-----------|---------------|
| startup/startup.r | .R | R |
| startup/startup.r.sha256 | .sha256 | Checksum integridad |
| startup/startup.jl | .jl | Julia |
| startup/startup.jl.sha256 | .sha256 | Checksum integridad |
| startup/startup.py | .py | Python (deprecado) |
| startup/__pycache__/startup.cpython-312.pyc | .pyc | Python bytecode |

---

### libreria/R/ — R4XCL (Librería R)

**33 archivos** | Lenguaje: R

| Ruta Relativa | Extensión | Categoría |
|---------------|-----------|-----------|
| libreria/R/R4XCL-0-Interno-1.R | .R | Interno (core) |
| libreria/R/R4XCL-0-Interno-2.R | .R | Interno (core) |
| libreria/R/R4XCL-0-Interno-3.R | .R | Interno (core) |
| libreria/R/R4XCL-0-UT-Ayuda.R | .R | Utilidades - Ayuda |
| libreria/R/R4XCL-0-UT-InstalaPaqueterias.R | .R | Utilidades - Paquetes |
| libreria/R/R4XCL-AD-ACP.R | .R | Análisis - ACP |
| libreria/R/R4XCL-AD-D3.R | .R | Análisis - D3 |
| libreria/R/R4XCL-AD-Dashboard.R | .R | Análisis - Dashboard |
| libreria/R/R4XCL-AD-Esquisse.R | .R | Análisis - Esquisse |
| libreria/R/R4XCL-AD-KMediass.R | .R | Análisis - K-Medias |
| libreria/R/R4XCL-AD-Map.R | .R | Análisis - Mapas |
| libreria/R/R4XCL-AD-NonParRolCor.R | .R | Análisis - No paramétrico |
| libreria/R/R4XCL-AD-Pivot.R | .R | Análisis - Pivot |
| libreria/R/R4XCL-AD-TextMining.R | .R | Análisis - Text Mining |
| libreria/R/R4XCL-BD-ObtieneDatos.R | .R | Base de datos |
| libreria/R/R4XCL-DS-Wooldridge.R | .R | Datasets - Wooldridge |
| libreria/R/R4XCL-FX-Aleatorios.R | .R | Funciones - Aleatorios |
| libreria/R/R4XCL-FX-Calculos.R | .R | Funciones - Cálculos |
| libreria/R/R4XCL-GR-Graficacion.R | .R | Gráficos - Graficación |
| libreria/R/R4XCL-GR-Interactivos.R | .R | Gráficos - Interactivos |
| libreria/R/R4XCL-GR-Mapa.R | .R | Gráficos - Mapas |
| libreria/R/R4XCL-GR-PlotlyView.R | .R | Gráficos - Plotly |
| libreria/R/R4XCL-GR-QuickPlot.R | .R | Gráficos - QuickPlot |
| libreria/R/R4XCL-MT-AlgebraLineal.R | .R | Matemáticas - Álgebra |
| libreria/R/R4XCL-RG-ArbolDecision.R | .R | Regresión - Árbol |
| libreria/R/R4XCL-RG-Binaria.R | .R | Regresión - Binaria |
| libreria/R/R4XCL-RG-DatosPanel.R | .R | Regresión - Panel |
| libreria/R/R4XCL-RG-Lineal.R | .R | Regresión - Lineal |
| libreria/R/R4XCL-RG-Poisson.R | .R | Regresión - Poisson |
| libreria/R/R4XCL-RG-SeriesTiempo.R | .R | Regresión - Series |
| libreria/R/R4XCL-RG-SVM.R | .R | Regresión - SVM |
| libreria/R/R4XCL-RG-Tobit.R | .R | Regresión - Tobit |
| libreria/R/R4XCL-UT-Pivote.R | .R | Utilidades - Pivote |

---

### libreria/JULIA/ — J4XCL (Librería Julia)

**5 archivos** | Lenguaje: Julia

| Ruta Relativa | Extensión | Categoría |
|---------------|-----------|-----------|
| libreria/JULIA/functions.jl | .jl | Funciones principales |
| libreria/JULIA/J4XCL-CN-Conectividad.jl | .jl | Conectividad |
| libreria/JULIA/J4XCL-ML-Aprendizaje.jl | .jl | Machine Learning |
| libreria/JULIA/J4XCL-MT-Matematicas.jl | .jl | Matemáticas |
| libreria/JULIA/J4XCL-OP-Optimizacion.jl | .jl | Optimización |

---

### docs/ — Documentación

**715 archivos** | Tipos: Markdown, HTML/JS/CSS (Doxygen generado), LaTeX

| Subcategoría | Archivos | Descripción |
|--------------|----------|-------------|
| Doxygen HTML (docs/api/html/) | ~580 | Documentación API generada |
| Doxygen JS (docs/api/html/) | 274 | Scripts de navegación Doxygen |
| Markdown (docs/*.md, subdirs) | ~83 | Documentación manual |
| LaTeX (docs/tesis/) | ~15 | Documento de tesis |
| Otros (PNG, PDF, CSS) | ~30 | Assets de documentación |

> **Nota**: La gran mayoría de archivos en docs/ son generados por Doxygen (HTML + JS). Los archivos de documentación manual son los .md en la raíz de docs/ y subdirectorios como docs/Mantenimiento/.

---

### Addin/ — Empaquetado XLL

**2 archivos** | Tipo: Configuración

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| Addin/CMakeLists.txt | .txt | CMake |
| Addin/CustomUI.xml | .xml | UI personalizada Office |

---

### .github/ — CI/CD y Templates

**4 archivos** | Tipo: YAML, Markdown

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| .github/workflows/build-and-test.yml | .yml | GitHub Actions workflow |
| .github/PULL_REQUEST_TEMPLATE.md | .md | Template PR |
| .github/ISSUE_TEMPLATE/bug_report.md | .md | Template bug report |
| .github/ISSUE_TEMPLATE/feature_request.md | .md | Template feature request |

---

## Resumen de Extensiones (Todas)

| Extensión | Cantidad | Clasificación |
|-----------|----------|---------------|
| .html | 308 | Documentación generada |
| .js | 277 | JavaScript (274 Doxygen + 3 proyecto) |
| .cc | 93 | C++ implementación |
| .h | 93 | C++ headers |
| .md | 83 | Documentación Markdown |
| .ts | 41 | TypeScript |
| .r | 34 | R |
| .png | 20 | Imágenes |
| .tex | 15 | LaTeX |
| .tlog | 14 | Build logs |
| .json | 12 | Configuración JSON |
| .less | 11 | Estilos LESS |
| .txt | 10 | Texto/CMake |
| .xml | 10 | Configuración XML |
| .log | 8 | Logs |
| .cpp | 7 | C++ implementación |
| .css | 6 | Estilos CSS |
| .jl | 6 | Julia |
| .pdf | 6 | Documentos PDF |
| .def | 5 | Module definitions |
| .gz | 5 | Archivos comprimidos |
| .gitignore | 4 | Git ignore |
| .obj | 4 | Objetos compilados |
| .aux | 4 | LaTeX auxiliar |
| .exp | 3 | Export libraries |
| .lib | 3 | Import libraries |
| .out | 3 | LaTeX output |
| .rc | 3 | Resource scripts |
| .ps1 | 2 | PowerShell scripts |
| .sha256 | 2 | Checksums |
| .tlb | 2 | Type libraries |
| .woff | 2 | Fuentes web |
| .yml | 1 | YAML |
| .proto | 1 | Protocol Buffers |
| .py | 1 | Python |
| .hpp | 1 | C++ header |
| .c | 1 | C |
| .ico | 1 | Icono |
| .idl | 1 | IDL (COM) |
| .lock | 1 | Lock file |
| .sh | 1 | Shell script |
| .svg | 1 | Imagen vectorial |
| Otros | 15 | Build artifacts, cache, etc. |

---

## Archivos Raíz del Proyecto (fuera de módulos)

| Ruta Relativa | Extensión | Tipo |
|---------------|-----------|------|
| CMakeLists.txt | .txt | CMake raíz |
| build.ps1 | .ps1 | Script de build |
| Doxyfile | — | Configuración Doxygen |
| .gitignore | .gitignore | Git ignore |
| README.md | .md | Documentación |
| CHANGELOG.md | .md | Historial de cambios |
| CODE_OF_CONDUCT.md | .md | Código de conducta |
| CONTRIBUTING.md | .md | Guía de contribución |
| LICENSE | — | Licencia |
| REBUILD_CHECKLIST.md | .md | Checklist de rebuild |

---

*Inventario generado como parte de la Fase 1 de la auditoría integral del proyecto NEVEN.*
