# Requirements Document

## Introduction

Este documento define los requisitos para la remediación integral de seguridad del proyecto NEVEN, un add-in XLL de C++17 para Excel que integra R y Julia. Se basa en los hallazgos de la auditoría de código (INFORME_AUDITORIA.md) que identificó 36 hallazgos: 8 críticos, 7 de severidad alta, 5 media y 14 baja. El desarrollo de nuevas funcionalidades queda congelado hasta que se completen los requisitos de Prioridad 1 y Prioridad 2, garantizando a la comunidad que la herramienta no facilita vectores de ataque.

## Glossary

- **NEVEN_Core**: Módulo principal del add-in (NEVEN64.xll/NEVEN.dll) que gestiona la comunicación con Excel y los procesos hijos.
- **SandboxVerifier**: Componente en Common/ responsable de verificar que el código de usuario no invoque funciones peligrosas antes de su ejecución.
- **AutoLoader**: Componente en Common/ que carga y ejecuta automáticamente scripts R/Julia del directorio de trabajo del usuario al inicio.
- **ContentPipeline**: Componente en Common/ que gestiona la conversión de documentos mediante Pandoc.
- **QuartoService**: Componente en Common/ que gestiona el renderizado de archivos .qmd mediante Quarto CLI.
- **ConfigService**: Componente en Common/ que lee y gestiona la configuración desde neven-config.json.
- **Console**: Aplicación REPL basada en Electron 1.8.2 que permite ejecución interactiva de código R/Julia.
- **REPLManager**: Componente en Common/ que gestiona la comunicación entre la consola REPL y los motores de lenguaje.
- **InputSanitizer**: Módulo propuesto para centralizar la validación y sanitización de entradas antes de su uso en líneas de comando.
- **Named_Pipe**: Mecanismo IPC de Windows usado para comunicación entre NEVEN_Core y los procesos hijos (ControlR, ControlJulia).
- **Protobuf_Frame**: Estructura de mensaje Protocol Buffers con prefijo de longitud usada en la comunicación IPC.
- **CI_Pipeline**: Workflow de GitHub Actions que compila y ejecuta tests del proyecto.
- **MSVC_Security_Flags**: Opciones de compilación de Microsoft Visual C++ que habilitan protecciones de memoria y control de flujo (/GS, /guard:cf, /DYNAMICBASE, /NXCOMPAT).

## Requirements

### Requisito 1: Sanitización de entradas en creación de procesos

**Historia de Usuario:** Como usuario de NEVEN, quiero que las entradas provenientes de celdas de Excel sean sanitizadas antes de usarse en líneas de comando, para que un atacante no pueda inyectar comandos del sistema operativo mediante metacaracteres en rutas de archivo.

#### Criterios de Aceptación

1. WHEN una celda de Excel provee una ruta de archivo a la función RJ_Q, THE InputSanitizer SHALL validar que la ruta contenga únicamente caracteres alfanuméricos, separadores de ruta (\ y /), puntos, guiones y guiones bajos antes de pasarla a CreateProcessA.
2. WHEN una celda de Excel provee una ruta de archivo a ContentPipeline::ConvertWithPandoc, THE InputSanitizer SHALL validar que la ruta contenga únicamente caracteres permitidos por la allowlist antes de construir la línea de comando.
3. WHEN la ruta contiene caracteres fuera de la allowlist (incluyendo &, |, ;, `, <, >, ", \n, \r, %), THE InputSanitizer SHALL rechazar la entrada y retornar un código de error descriptivo sin ejecutar el proceso.
4. THE NEVEN_Core SHALL pasar la ruta del ejecutable en el parámetro lpApplicationName de CreateProcessA, separándola de los argumentos en lpCommandLine.
5. WHEN QuartoService::ValidateInputSecurity recibe una entrada, THE QuartoService SHALL bloquear los caracteres ", \n, \r y % además de los ya bloqueados (&, |, ;, `, <, >).
6. FOR ALL rutas procesadas por InputSanitizer, sanitizar y luego re-sanitizar SHALL producir el mismo resultado (propiedad de idempotencia).

---

### Requisito 2: Eliminación o actualización del módulo Console (Electron)

**Historia de Usuario:** Como mantenedor del proyecto, quiero resolver las vulnerabilidades críticas de Electron 1.8.2 (50+ CVEs, nodeIntegration sin contextIsolation), para que la consola REPL no sea un vector de ejecución remota de código.

#### Criterios de Aceptación

1. THE NEVEN_Core SHALL funcionar completamente sin el módulo Console presente en el sistema de archivos.
2. WHEN el módulo Console se mantiene en el repositorio, THE Console SHALL usar Electron versión 28 o superior con contextIsolation habilitado y nodeIntegration deshabilitado.
3. WHEN el módulo Console se mantiene, THE Console SHALL usar contextBridge para toda comunicación entre el proceso renderer y el proceso main.
4. WHEN el módulo Console se mantiene, THE Console SHALL usar sandbox: true en las webPreferences del BrowserWindow.
5. IF el módulo Console se determina reemplazado por WebView2, THEN THE NEVEN_Core SHALL archivar Console en una rama separada y eliminarlo del repositorio principal.
6. WHEN el módulo Console se mantiene, THE Console SHALL reemplazar todos los usos de innerHTML por APIs DOM seguras (textContent, createTextNode) o sanitización con DOMPurify para contenido que requiera formato HTML.
7. WHEN el módulo Console se mantiene, THE Console SHALL condicionar electron-reload a process.env.NODE_ENV === 'development'.

---

### Requisito 3: Fortalecimiento del Sandbox

**Historia de Usuario:** Como usuario de NEVEN en un entorno compartido, quiero que el sandbox sea robusto contra intentos de bypass, para que código malicioso en celdas de Excel o scripts auto-cargados no pueda ejecutar operaciones peligrosas del sistema.

#### Criterios de Aceptación

1. WHEN un usuario ejecuta código desde la consola REPL, THE SandboxVerifier SHALL aplicar las mismas verificaciones de seguridad que aplica al código ejecutado desde celdas de Excel.
2. WHEN el AutoLoader carga un script del directorio de trabajo, THE SandboxVerifier SHALL verificar el contenido del script antes de su ejecución.
3. THE SandboxVerifier SHALL bloquear en R las funciones: system, system2, shell, shell.exec, file.rename, file.remove, file.copy, download.file, readLines (con argumento pipe), url, socketConnection, get, source, library (sin restricción de repositorio), open, Sys.getenv, Sys.setenv, proc.time, .Internal, .Call, .External, .C, .Fortran, además de las ya bloqueadas.
4. THE SandboxVerifier SHALL bloquear en Julia las funciones: run, ccall, unsafe_load, unsafe_store!, unsafe_pointer_to_objref, unsafe_wrap, ENV, open (para procesos), download, Sockets.connect, eval (con Meta.parse), include, además de las ya bloqueadas.
5. WHEN el campo sandbox.enabled de neven-config.json se modifica a false, THE ConfigService SHALL requerir confirmación interactiva del usuario mediante un diálogo de Excel antes de desactivar el sandbox.
6. WHEN el sandbox se desactiva, THE ConfigService SHALL registrar el evento en el log del sistema incluyendo timestamp y usuario de Windows.
7. IF un script de usuario intenta ejecutar una función bloqueada por el sandbox, THEN THE SandboxVerifier SHALL retornar un mensaje de error que identifique la función bloqueada y la razón del bloqueo.
8. FOR ALL cadenas de código de usuario, verificar con SandboxVerifier y luego verificar de nuevo SHALL producir el mismo resultado de aprobación o rechazo (propiedad de idempotencia).

---

### Requisito 4: Flags de seguridad de compilación MSVC

**Historia de Usuario:** Como mantenedor del proyecto, quiero que el binario compilado tenga todas las protecciones de memoria y control de flujo habilitadas, para que exploits de corrupción de memoria sean significativamente más difíciles de ejecutar.

#### Criterios de Aceptación

1. THE CI_Pipeline SHALL compilar todos los targets con la opción /GS (buffer security check) habilitada explícitamente.
2. THE CI_Pipeline SHALL compilar todos los targets con la opción /guard:cf (Control Flow Guard) habilitada explícitamente.
3. THE CI_Pipeline SHALL enlazar todos los targets con las opciones /DYNAMICBASE (ASLR) y /NXCOMPAT (DEP) habilitadas explícitamente.
4. WHEN se agrega un nuevo target al proyecto, THE CMakeLists.txt raíz SHALL aplicar automáticamente los flags de seguridad sin requerir configuración adicional por target.

---

### Requisito 5: Mejora del .gitignore

**Historia de Usuario:** Como desarrollador del proyecto, quiero que el .gitignore raíz excluya archivos sensibles y artefactos de compilación, para que credenciales, símbolos de depuración y directorios generados no se publiquen accidentalmente en el repositorio.

#### Criterios de Aceptación

1. THE .gitignore raíz SHALL excluir el directorio Build/ y todos sus contenidos.
2. THE .gitignore raíz SHALL excluir el directorio node_modules/ y todos sus contenidos.
3. THE .gitignore raíz SHALL excluir archivos de símbolos de depuración (*.pdb).
4. THE .gitignore raíz SHALL excluir el directorio __pycache__/ y todos sus contenidos.
5. THE .gitignore raíz SHALL excluir el archivo neven-config.json para prevenir publicación de API keys.
6. THE .gitignore raíz SHALL excluir archivos de entorno (*.env), claves privadas (*.key, *.pem) y crash dumps (crashes/).

---

### Requisito 6: Permisos mínimos en GitHub Actions

**Historia de Usuario:** Como mantenedor del proyecto, quiero que el workflow de CI/CD opere con permisos mínimos, para que un compromiso del workflow no permita escritura en el repositorio ni acceso a secretos innecesarios.

#### Criterios de Aceptación

1. THE CI_Pipeline SHALL declarar permissions: { contents: read } a nivel de workflow.
2. WHEN se agrega un nuevo job al workflow, THE CI_Pipeline SHALL requerir declaración explícita de permisos adicionales si necesita más que lectura de contenido.

---

### Requisito 7: Validación de mensajes Protobuf en IPC

**Historia de Usuario:** Como mantenedor del proyecto, quiero que los mensajes Protobuf recibidos por Named Pipes sean validados antes de su procesamiento, para que un mensaje malformado no cause comportamiento indefinido ni corrupción de memoria.

#### Criterios de Aceptación

1. WHEN un Protobuf_Frame es recibido por la función Unframe(), THE NEVEN_Core SHALL validar que el prefijo de longitud no exceda un límite máximo configurable (por defecto 64 MB).
2. WHEN el prefijo de longitud excede el límite máximo, THE NEVEN_Core SHALL descartar el mensaje y registrar un error en el log.
3. WHEN el contenido del frame no puede deserializarse como un mensaje Protobuf válido, THE NEVEN_Core SHALL descartar el mensaje y retornar un error al llamador.
4. FOR ALL mensajes Protobuf válidos, serializar (Frame) y luego deserializar (Unframe) SHALL producir un mensaje equivalente al original (propiedad de round-trip).

---

### Requisito 8: Validación de handles de Named Pipes

**Historia de Usuario:** Como mantenedor del proyecto, quiero que los handles de Named Pipes sean validados atómicamente antes de su uso, para que condiciones de carrera (TOCTOU) no causen acceso a handles inválidos.

#### Criterios de Aceptación

1. WHEN NEVEN_Core obtiene un handle de Named Pipe, THE NEVEN_Core SHALL verificar la validez del handle inmediatamente antes de cada operación de lectura o escritura en una sola operación atómica.
2. IF un handle de Named Pipe resulta inválido durante una operación, THEN THE NEVEN_Core SHALL cerrar el handle, registrar el error y reintentar la conexión con el proceso hijo.
3. THE NEVEN_Core SHALL usar un mutex o sección crítica para proteger el acceso concurrente a handles de pipe compartidos entre threads.

---

### Requisito 9: Eliminación de eval(parse()) en funciones R

**Historia de Usuario:** Como usuario de NEVEN, quiero que las funciones de la librería R no usen eval(parse()) para construir fórmulas, para que entradas maliciosas no puedan ejecutar código arbitrario a través de la evaluación dinámica.

#### Criterios de Aceptación

1. THE librería R de NEVEN SHALL usar as.formula() en lugar de eval(parse(text=...)) para construir objetos de fórmula a partir de strings.
2. THE librería R de NEVEN SHALL no contener invocaciones de eval(parse()) en ningún archivo de producción del directorio libreria/R/.
3. WHEN una función R necesita construir una fórmula dinámicamente, THE función SHALL usar as.formula(paste(...)) como mecanismo seguro de construcción.

---

### Requisito 10: Bloqueo de acceso a variables de entorno desde sandbox

**Historia de Usuario:** Como usuario de NEVEN en un entorno corporativo, quiero que el sandbox bloquee el acceso a variables de entorno del sistema, para que scripts maliciosos no puedan leer tokens, API keys u otra información sensible almacenada en el entorno.

#### Criterios de Aceptación

1. WHILE el sandbox está habilitado, THE SandboxVerifier SHALL bloquear llamadas a Sys.getenv() y Sys.setenv() en código R de usuario.
2. WHILE el sandbox está habilitado, THE SandboxVerifier SHALL bloquear acceso al diccionario ENV en código Julia de usuario.
3. IF un script de usuario intenta acceder a variables de entorno, THEN THE SandboxVerifier SHALL retornar un error indicando que el acceso a variables de entorno está bloqueado por política de seguridad.

---

### Requisito 11: Gestión de memoria en pipes de procesos hijos

**Historia de Usuario:** Como mantenedor del proyecto, quiero que los handles y buffers de stdio pipes se liberen correctamente al terminar los procesos hijos, para que no haya fugas de memoria durante sesiones prolongadas de Excel.

#### Criterios de Aceptación

1. WHEN un proceso hijo (ControlR o ControlJulia) termina, THE NEVEN_Core SHALL cerrar todos los handles de pipe asociados (stdin, stdout, stderr) y liberar los buffers de lectura.
2. WHEN NEVEN_Core detecta que un proceso hijo no responde dentro del timeout configurado, THE NEVEN_Core SHALL terminar el proceso, cerrar los handles y liberar la memoria asociada.
3. IF un error ocurre durante la creación de pipes para un proceso hijo, THEN THE NEVEN_Core SHALL liberar todos los recursos parcialmente asignados antes de retornar el error.

---

### Requisito 12: Refactorización del módulo Common

**Historia de Usuario:** Como desarrollador del proyecto, quiero que el módulo Common esté dividido en sub-módulos por responsabilidad, para que sea más fácil de mantener, testear y comprender.

#### Criterios de Aceptación

1. THE módulo Common SHALL estar organizado en sub-directorios por responsabilidad: IPC/, Security/, Config/, Viewers/, Startup/.
2. WHEN se agrega nueva funcionalidad al módulo Common, THE desarrollador SHALL colocarla en el sub-directorio correspondiente a su responsabilidad.
3. THE sub-módulo Security/ SHALL contener SandboxVerifier, SecurityService e InputSanitizer.
4. THE sub-módulo IPC/ SHALL contener pipe.cc/h, message_utilities.cc/h y REPLBridge.cc/h.
5. THE compilación del proyecto SHALL completarse exitosamente después de la reorganización sin cambios en la API pública de Common.

---

### Requisito 13: Eliminación de código muerto

**Historia de Usuario:** Como mantenedor del proyecto, quiero que el código muerto y duplicado sea eliminado o archivado, para reducir la superficie de ataque y la confusión en el mantenimiento.

#### Criterios de Aceptación

1. THE repositorio SHALL no contener el archivo Console/src/shell/language_interface_julia-0.7.ts.
2. THE repositorio SHALL no contener el directorio startup/__pycache__/.
3. THE función .neven_webview_dir() SHALL estar definida en un único archivo R compartido, eliminando las 6 copias duplicadas.
4. THE archivo renderer.ts SHALL no contener bloques de código comentado que excedan 3 líneas consecutivas.
5. WHEN el módulo ControlPython permanece deprecado, THE repositorio SHALL mover su código fuente a una rama archive/python.

---

### Requisito 14: Documentación Doxygen en headers públicos

**Historia de Usuario:** Como desarrollador del proyecto, quiero que los headers públicos tengan documentación Doxygen completa, para que la API sea comprensible sin necesidad de leer la implementación.

#### Criterios de Aceptación

1. THE headers públicos de Common/ SHALL contener comentarios Doxygen con @brief, @param y @return para cada función pública.
2. THE headers públicos de Core/include/ SHALL contener comentarios Doxygen con @brief, @param y @return para cada función pública.
3. WHEN se agrega una nueva función pública a un header, THE desarrollador SHALL incluir documentación Doxygen antes de la declaración.

---

### Requisito 15: Unificación de nomenclatura y documentación de identidad

**Historia de Usuario:** Como nuevo contribuidor del proyecto, quiero que la relación entre los nombres NEVEN, RJ2XCL y BERT esté documentada explícitamente, para comprender el código sin confusión terminológica.

#### Criterios de Aceptación

1. THE documentación del proyecto SHALL incluir un documento que explique la relación histórica entre NEVEN (nombre público), RJ2XCL (prefijo interno C++) y BERT (proyecto original).
2. THE variables de entorno nuevas SHALL usar el prefijo NEVEN_ en lugar de RJ2XCL_ o BERT_.
3. WHILE existan variables de entorno legacy (RJ2XCL_*, BERT_*), THE NEVEN_Core SHALL mantener fallbacks que lean ambos prefijos con prioridad para NEVEN_.
