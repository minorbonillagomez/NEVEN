# Documento de Requisitos: Renombrar RJ2XCL a NEVEN

## Introduccion

Este documento especifica los requisitos para renombrar el proyecto RJ2XCL a NEVEN. NEVEN es un add-in XLL de Excel desarrollado como tesis de maestria en la Universidad de Costa Rica, que integra R, Julia, WebView2, Pluto.jl y Quarto en un ecosistema unificado. El renombramiento se ejecuta en dos fases: documentacion (Fase 1) y codigo (Fase 2), con el objetivo de establecer una identidad de marca coherente y concisa.

### Convencion de nombres nuevos

| Nombre anterior | Nombre nuevo | Descripcion |
|:---|:---|:---|
| `RJ2XCL.VIEW(...)` | `NEVEN.v(...)` | Funciones de visor WebView2 |
| `RJ2XCL.R(...)` | `NEVEN.r(...)` | Funciones de ejecucion R |
| `RJ2XCL.J(...)` | `NEVEN.j(...)` | Funciones de ejecucion Julia |
| `RJ2XCL.QUARTO(...)` | `NEVEN.q(...)` | Funciones de Quarto |
| `R.func()`, `J.func()` | `R.func()`, `J.func()` | Alias cortos (sin cambio) |

## Glosario

- **NEVEN**: NEVEN es la integracion simetrica que une la potencia de Julia, R, Quarto y futuros lenguajes dentro de Excel. Inspirado en la calendula --la flor que no se marchita--, su nombre representa una conexion robusta, resiliente e inalterable. Es el punto de encuentro donde la ciencia de datos avanzada y la agilidad de los negocios convergen en un equilibrio perfecto. Reemplaza a RJ2XCL en todas las interfaces visibles al usuario.
- **Sistema_XLL**: El add-in XLL principal que se carga en Excel (archivo NEVEN64.xll, antes RJ2XCL64.xll).
- **Sistema_Ribbon**: El COM Add-in que proporciona la cinta de opciones en Excel (NEVENRibbon.dll, antes RJ2XCLRibbon.dll).
- **Sistema_Build**: El sistema de compilacion basado en CMake que genera todos los binarios del proyecto.
- **Sistema_Config**: El servicio de configuracion que lee archivos JSON y variables de entorno.
- **Sistema_Log**: El servicio de logging estructurado que escribe al archivo de registro.
- **Sistema_Docs**: El conjunto de documentos Markdown en docs/, docs/docusaurus/ y Examples/.
- **Nombre_Excel_Visible**: El nombre de funcion que el usuario escribe en una celda de Excel (ej: `=NEVEN.v(...)`).
- **Nombre_Interno_CPP**: El nombre de la funcion C++ exportada desde la DLL (ej: `RJ_View`). Estos nombres NO cambian.
- **Directorio_Deploy**: La carpeta de despliegue en el sistema del usuario (C:\NEVEN\, antes C:\RJ2XCL\).
- **Registro_COM**: Las entradas en el registro de Windows que permiten a Excel encontrar el COM Add-in.
- **Alias_Corto**: Los prefijos `R.` y `J.` para funciones de lenguaje especifico (no cambian).

## Requisitos

### Requisito 1: Renombrar nombres de funciones Excel visibles

**User Story:** Como usuario de Excel, quiero que las formulas usen el prefijo NEVEN en lugar de RJ2XCL, para que la interfaz refleje el nombre oficial del proyecto.

#### Criterios de Aceptacion

1. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones de visor con el prefijo `NEVEN.v` en lugar de `RJ2XCL.VIEW` (ej: `NEVEN.v`, `NEVEN.v.close`, `NEVEN.v.list`, `NEVEN.v.send`).
2. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones Pluto con el prefijo `NEVEN.pluto` en lugar de `RJ2XCL.PLUTO` (ej: `NEVEN.pluto.start`, `NEVEN.pluto.stop`, `NEVEN.pluto.status`, `NEVEN.pluto.data`).
3. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones de notebook con el prefijo `NEVEN.notebook` en lugar de `RJ2XCL.NOTEBOOK` (ej: `NEVEN.notebook.open`, `NEVEN.notebook.list`, `NEVEN.notebook.export`).
4. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones de presentacion con el prefijo `NEVEN.presentation` en lugar de `RJ2XCL.PRESENTATION`.
5. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar la funcion Quarto como `NEVEN.q` en lugar de `RJ2XCL.QUARTO`.
6. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones de informacion con el prefijo `NEVEN` (ej: `NEVEN.about`, `NEVEN.help`, `NEVEN.editor`, `NEVEN.lang.toggle`).
7. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones de ejecucion de lenguaje como `NEVEN.r`, `NEVEN.j` y `NEVEN.Call`/`NEVEN.Exec` en lugar de `RJ2XCL.R`, `RJ2XCL.J` y `RJ2XCL.Call`/`RJ2XCL.Exec`.
8. WHEN el Sistema_XLL se registra en Excel, THE Sistema_XLL SHALL registrar las funciones de comando con el prefijo `NEVEN.cmd` en lugar de `RJ2XCL.CMD`.
9. THE Sistema_XLL SHALL mantener los Nombre_Interno_CPP sin cambios (prefijo `RJ_` en funciones C++ exportadas).
10. THE Sistema_XLL SHALL mantener los Alias_Corto `R.` y `J.` sin cambios para funciones de lenguaje especifico.

### Requisito 2: Renombrar la cinta de opciones (Ribbon)

**User Story:** Como usuario de Excel, quiero que la pestana del Ribbon muestre "NEVEN" en lugar de "RJ2XCL", para que la interfaz sea consistente con el nuevo nombre.

#### Criterios de Aceptacion

1. WHEN Excel carga el COM Add-in, THE Sistema_Ribbon SHALL mostrar la pestana con la etiqueta "NEVEN" en lugar de "RJ2XCL".
2. WHEN el usuario solicita la etiqueta de la consola, THE Sistema_Ribbon SHALL retornar "NEVEN Console" en lugar de "RJ2XCL Console".
3. WHEN el usuario hace clic en "Acerca de", THE Sistema_Ribbon SHALL mostrar "NEVEN v2.0" en lugar de "RJ2XCL v2.0" en el supertip y en el dialogo.
4. WHEN el usuario hace clic en "Config JSON", THE Sistema_Ribbon SHALL abrir el archivo `neven-config.json` en lugar de `rj2xcl-config.json`.
5. WHEN el usuario hace clic en "Carpeta Scripts", THE Sistema_Ribbon SHALL abrir el Directorio_Deploy `C:\NEVEN\` en lugar de `C:\RJ2XCL\`.
6. WHEN el Sistema_Ribbon invoca funciones del XLL, THE Sistema_Ribbon SHALL usar los nuevos Nombre_Excel_Visible con prefijo NEVEN (ej: `NEVEN.cmd.pluto.start` en lugar de `RJ2XCL.CMD.PLUTO.START`).
7. THE Sistema_Ribbon SHALL actualizar todos los supertips que referencian "RJ2XCL" para usar "NEVEN".

### Requisito 3: Renombrar archivos de configuracion

**User Story:** Como desarrollador, quiero que los archivos de configuracion usen el nombre NEVEN, para que la estructura del proyecto sea coherente.

#### Criterios de Aceptacion

1. THE Sistema_Config SHALL leer la configuracion principal desde el archivo `neven-config.json` en lugar de `rj2xcl-config.json`.
2. THE Sistema_Config SHALL leer las definiciones de lenguaje desde el archivo `neven-languages.json` en lugar de `rj2xcl-languages.json`.
3. THE Sistema_Config SHALL establecer la variable de entorno `NEVEN_HOME` en lugar de `RJ2XCL_HOME`.
4. THE Sistema_Config SHALL leer la clave de registro `NEVEN.DevOptions` en lugar de `RJ2XCL.DevOptions`.

### Requisito 4: Renombrar archivos binarios y de despliegue

**User Story:** Como desarrollador, quiero que los binarios generados usen el nombre NEVEN, para que la instalacion sea consistente con la marca.

#### Criterios de Aceptacion

1. WHEN el Sistema_Build compila el XLL, THE Sistema_Build SHALL generar el archivo de salida como `NEVEN64.xll` en lugar de `RJ2XCL64.xll`.
2. WHEN el Sistema_Build compila el Ribbon, THE Sistema_Build SHALL generar el archivo de salida como `NEVENRibbon.dll` en lugar de `RJ2XCLRibbon.dll`.
3. THE Sistema_Build SHALL actualizar los nombres de target en CMakeLists.txt para reflejar el nombre NEVEN (ej: `NEVEN_Core`, `NEVENRibbon`).
4. WHEN se despliega el proyecto, THE Sistema_Build SHALL copiar los binarios al Directorio_Deploy `C:\NEVEN\` en lugar de `C:\RJ2XCL\`.

### Requisito 5: Actualizar registro COM de Windows

**User Story:** Como desarrollador, quiero que el registro COM use el nombre NEVEN, para que Excel encuentre el add-in con la nueva identidad.

#### Criterios de Aceptacion

1. THE Sistema_Ribbon SHALL registrarse en Windows con el ProgID `NEVENRibbon.Connect` en lugar de `RJ2XCLRibbon.Connect`.
2. THE Sistema_Ribbon SHALL registrarse en la clave de Excel Add-ins como `HKCU:\Software\Microsoft\Office\Excel\Addins\NEVENRibbon.Connect`.
3. THE Sistema_Ribbon SHALL actualizar el resource ID del registro (IDR_RJ2XCLRIBBON) para reflejar el nombre NEVEN (IDR_NEVENRIBBON).
4. WHEN el Sistema_Ribbon busca el modulo XLL cargado, THE Sistema_Ribbon SHALL buscar modulos que contengan "NEVEN" en el nombre de archivo en lugar de "RJ2XCL".

### Requisito 6: Actualizar el servicio de logging

**User Story:** Como desarrollador, quiero que el archivo de log use el nombre NEVEN, para facilitar la identificacion de registros del sistema.

#### Criterios de Aceptacion

1. WHEN el Sistema_Log se inicializa, THE Sistema_Log SHALL escribir al archivo `neven.log` en lugar de `rj2xcl.log`.
2. THE Sistema_Log SHALL usar el prefijo "NEVEN" en los mensajes de log internos que referencian el nombre del proyecto.

### Requisito 7: Actualizar scripts de inicio (startup)

**User Story:** Como desarrollador, quiero que los scripts de inicio de R y Julia usen el nombre NEVEN, para que los modulos internos sean consistentes.

#### Criterios de Aceptacion

1. WHEN el script startup.r se ejecuta, THE Sistema_XLL SHALL crear el entorno R con el nombre `NEVEN` en lugar de `RJ2XCL`.
2. WHEN el script startup.r genera graficos, THE Sistema_XLL SHALL usar el prefijo `neven_plot_` en los nombres de archivos temporales en lugar de `rj2xcl_plot_`.
3. WHEN el script startup.r completa la carga, THE Sistema_XLL SHALL imprimir "NEVEN R startup complete" en lugar de "RJ2XCL R startup complete".
4. WHEN el script startup.jl se ejecuta, THE Sistema_XLL SHALL definir el modulo Julia como `NEVEN` en lugar de `RJ2XCL`.
5. THE Sistema_XLL SHALL mantener el alias Julia `RJ` como alias adicional del modulo NEVEN para compatibilidad interna.
6. WHEN el script startup.jl escribe datos compartidos, THE Sistema_XLL SHALL usar la variable de entorno `NEVEN_HOME` como directorio base, con fallback a `C:\NEVEN`.

### Requisito 8: Actualizar la documentacion (Fase 1)

**User Story:** Como usuario, quiero que toda la documentacion refleje el nombre NEVEN, para que las guias y ejemplos sean consistentes con la interfaz.

#### Criterios de Aceptacion

1. THE Sistema_Docs SHALL reemplazar todas las referencias textuales a "RJ2XCL" por "NEVEN" en los archivos Markdown de docs/.
2. THE Sistema_Docs SHALL actualizar todos los ejemplos de formulas Excel para usar los nuevos Nombre_Excel_Visible (ej: `=NEVEN.v(...)` en lugar de `=RJ2XCL.VIEW(...)`).
3. THE Sistema_Docs SHALL actualizar los 11 capitulos de Docusaurus en docs/docusaurus/ con el nombre NEVEN.
4. THE Sistema_Docs SHALL actualizar el archivo EJEMPLOS_USUARIO.md con las nuevas formulas y nombres de funciones.
5. THE Sistema_Docs SHALL actualizar los diagramas de arquitectura para reflejar los nuevos nombres de binarios (NEVEN64.xll, NEVENRibbon.dll).
6. THE Sistema_Docs SHALL actualizar las rutas de directorio en la documentacion de `C:\RJ2XCL\` a `C:\NEVEN\`.
7. THE Sistema_Docs SHALL actualizar las referencias a archivos de configuracion de `rj2xcl-config.json` a `neven-config.json`.
8. THE Sistema_Docs SHALL evitar caracteres especiales (acentos, flechas Unicode) que puedan corromperse en codificacion UTF-8.

### Requisito 9: Actualizar las pruebas automatizadas

**User Story:** Como desarrollador, quiero que las pruebas automatizadas reflejen los nuevos nombres, para que la suite de 205 tests valide correctamente el sistema renombrado.

#### Criterios de Aceptacion

1. WHEN se ejecutan las pruebas, THE Sistema_Build SHALL compilar y ejecutar los 205 tests existentes sin errores.
2. THE Sistema_Build SHALL actualizar las cadenas de texto en los archivos de test que referencian "RJ2XCL" para usar "NEVEN".
3. THE Sistema_Build SHALL actualizar las rutas de archivos en los tests que referencian `C:\RJ2XCL\` para usar `C:\NEVEN\`.
4. THE Sistema_Build SHALL actualizar las referencias a nombres de funciones Excel en los tests para usar los nuevos Nombre_Excel_Visible.

### Requisito 10: Actualizar el archivo de exportaciones DLL

**User Story:** Como desarrollador, quiero que el archivo .def refleje la nueva identidad del proyecto, para que la DLL se exporte correctamente.

#### Criterios de Aceptacion

1. THE Sistema_Build SHALL mantener todos los simbolos exportados en rj2xcl.def con el prefijo `RJ_` sin cambios (los Nombre_Interno_CPP no cambian).
2. THE Sistema_Build SHALL actualizar los comentarios del archivo .def que referencian "RJ2XCL" para usar "NEVEN".
3. THE Sistema_Build SHALL actualizar la directiva LIBRARY del archivo .def si referencia el nombre RJ2XCL.

### Requisito 11: Mantener compatibilidad durante la transicion

**User Story:** Como usuario existente, quiero recibir un mensaje claro si uso formulas con el nombre antiguo, para saber que debo actualizar mis hojas de calculo.

#### Criterios de Aceptacion

1. IF un usuario ingresa una formula con el prefijo antiguo `RJ2XCL.` que ya no esta registrada, THEN THE Sistema_XLL SHALL retornar un error `#NAME?` de Excel (comportamiento estandar cuando una funcion no existe).
2. THE Sistema_Docs SHALL incluir una seccion de migracion que liste el mapeo completo de nombres antiguos a nombres nuevos.
3. THE Sistema_Docs SHALL documentar el procedimiento de despliegue que incluye: detener procesos (`Stop-Process -Name "EXCEL","ControlR","ControlJulia","julia" -Force`), compilar (`cmake --build build_new --config Release --parallel`), y copiar al Directorio_Deploy.

### Requisito 12: Actualizar la categoria de funciones en Excel

**User Story:** Como usuario de Excel, quiero que las funciones aparezcan bajo la categoria "NEVEN" en el Asistente de Funciones, para encontrarlas facilmente.

#### Criterios de Aceptacion

1. WHEN el Sistema_XLL registra funciones en Excel, THE Sistema_XLL SHALL usar la categoria "NEVEN" en lugar de "RJ2XCL" en el sexto campo del descriptor de funcion (funcTemplates y callTemplates).
