# Requirements Document

## Introduction

NEVEN integra tres motores de scripting (R, Julia, Python) como procesos hijos del add-in Excel.
Cada motor depende de paquetes de terceros: R requiere `jsonlite`, `plm`, `stargazer`, `e1071`,
`rpart`, `VGAM`, `tseries`, `FactoMineR`, entre otros; Python requiere paquetes de análisis de
texto y ML; Julia requiere paquetes registrados en su depósito oficial. Al actualizar la versión
de un motor (p.ej. R 4.4.1 → 4.6.1), los paquetes instalados en la ruta antigua **no migran**,
causando errores del tipo _"no hay paquete llamado 'X'"_ en DataLab.

El **NEVEN Package Manager** es un subsistema proactivo que verifica la presencia de paquetes
requeridos en los tres motores, informa al usuario cuando alguno falta y solicita autorización
explícita antes de instalar cualquier dependencia. Actúa en tres momentos: al arrancar NEVEN,
al seleccionar una función en DataLab, y cuando el usuario lo solicita manualmente desde
NEVEN Studio.

---

## Glossary

- **Package_Manager**: Subsistema de NEVEN que verifica e instala paquetes de los motores R,
  Julia y Python.
- **Motor**: Proceso hijo que embebe un lenguaje de scripting (ControlR.exe, ControlJulia.exe,
  ControlPython.exe).
- **Paquete**: Biblioteca de terceros requerida por una función del catálogo DataLab o de la
  librería NEVEN (p.ej. `jsonlite` en R, `DataFrames.jl` en Julia, `scikit-learn` en Python).
- **Manifiesto**: Archivo JSON (`packages-manifest.json`) que declara el conjunto de paquetes
  requeridos por motor, junto con la versión mínima aceptable y la función DataLab que los necesita.
- **Verificación**: Proceso que compara los paquetes instalados en el Motor activo con los
  declarados en el Manifiesto y produce una lista de paquetes ausentes o desactualizados.
- **Instalación**: Proceso de descarga e integración de un paquete en el Motor correspondiente,
  ejecutado únicamente con autorización previa del usuario.
- **NEVEN Studio**: Servidor HTTP Python (puerto 5555) con interfaz web que actúa como panel de
  control de NEVEN.
- **DataLab**: Módulo de NEVEN Studio que expone el catálogo de funciones estadísticas y
  ejecuta scripts en los Motores.
- **Sidecar JSON**: Archivo `.json` que acompaña a cada función `.Studio.R` / `.Studio.py` del
  catálogo DataLab y declara los metadatos de la función.
- **Cola_de_Instalación**: Estructura interna que acumula las solicitudes de instalación
  autorizadas por el usuario y las ejecuta secuencialmente.

---

## Requirements

### Requirement 1: Manifiesto de paquetes requeridos

**User Story:** Como administrador de NEVEN, quiero que el sistema mantenga un
manifiesto centralizado de paquetes requeridos por motor, para tener una única fuente de
verdad que el Package Manager pueda consultar.

#### Acceptance Criteria

1. THE Package_Manager SHALL mantener un archivo `packages-manifest.json` en el directorio
   de configuración de NEVEN (`C:\NEVEN\`).
2. THE Package_Manager SHALL incluir en el Manifiesto, por cada paquete, los campos: nombre,
   motor (`R` | `Julia` | `Python`), versión mínima requerida y la lista de funciones DataLab
   que dependen de él.
3. WHEN el Manifiesto no existe al iniciar NEVEN, THE Package_Manager SHALL generar el
   Manifiesto con los valores predeterminados del catálogo DataLab instalado.
4. WHEN el catálogo DataLab contiene una función nueva cuyas dependencias no están en el
   Manifiesto, THE Package_Manager SHALL añadir esas dependencias al Manifiesto durante la
   próxima Verificación.
5. IF el Manifiesto contiene una entrada con formato inválido, THEN THE Package_Manager SHALL
   omitir esa entrada, registrar una advertencia en el log de NEVEN y continuar con las
   entradas válidas.

---

### Requirement 2: Verificación proactiva al iniciar NEVEN

**User Story:** Como usuario de NEVEN, quiero que el sistema verifique automáticamente
los paquetes requeridos al iniciar, para conocer el estado antes de ejecutar cualquier función.

#### Acceptance Criteria

1. WHEN NEVEN inicia y los Motores están disponibles, THE Package_Manager SHALL ejecutar
   la Verificación de todos los paquetes del Manifiesto para cada Motor activo.
2. WHILE la Verificación de inicio está en progreso, THE Package_Manager SHALL ejecutarla
   en un hilo de fondo sin bloquear la carga del add-in Excel ni la interfaz de NEVEN Studio.
3. WHEN la Verificación de inicio detecta al menos un paquete ausente, THE Package_Manager
   SHALL mostrar en NEVEN Studio una notificación con la lista de paquetes faltantes y la
   opción de instalarlos.
4. WHEN la Verificación de inicio concluye sin paquetes faltantes, THE Package_Manager SHALL
   registrar el resultado en el log de NEVEN con nivel INFO y no mostrar notificaciones al
   usuario.
5. THE Package_Manager SHALL completar la Verificación de inicio en un tiempo máximo de
   30 segundos por Motor; si excede ese límite, SHALL registrar el resultado parcial y
   continuar sin bloquear.

---

### Requirement 3: Verificación al seleccionar una función en DataLab

**User Story:** Como analista de datos, quiero que NEVEN verifique los paquetes de
una función específica antes de ejecutarla, para recibir una advertencia oportuna si falta
alguna dependencia.

#### Acceptance Criteria

1. WHEN el usuario selecciona una función en el catálogo DataLab, THE Package_Manager SHALL
   verificar únicamente los paquetes declarados para esa función en el Manifiesto.
2. WHEN la verificación detecta paquetes faltantes para la función seleccionada, THE
   Package_Manager SHALL mostrar en la interfaz DataLab el nombre de los paquetes faltantes
   y un botón de acción para instalarlos antes de ejecutar la función.
3. WHEN todos los paquetes requeridos por la función seleccionada están presentes, THE
   Package_Manager SHALL permitir la ejecución de la función sin interrupciones adicionales.
4. THE Package_Manager SHALL completar la verificación de una función individual en un tiempo
   máximo de 5 segundos para no degradar la experiencia de selección en DataLab.
5. WHILE una función está siendo ejecutada, THE Package_Manager SHALL omitir verificaciones
   adicionales para esa misma función hasta que la ejecución concluya.

---

### Requirement 4: Verificación manual desde NEVEN Studio

**User Story:** Como usuario avanzado de NEVEN, quiero disponer de un botón en
NEVEN Studio para revisar manualmente el estado de todos los paquetes, para poder anticipar
problemas antes de trabajar con una función específica.

#### Acceptance Criteria

1. THE NEVEN Studio SHALL exponer en su interfaz web un botón "Verificar paquetes" accesible
   desde el panel de administración.
2. WHEN el usuario activa el botón "Verificar paquetes", THE Package_Manager SHALL ejecutar
   la Verificación completa de todos los motores activos y mostrar un reporte en pantalla.
3. THE Package_Manager SHALL estructurar el reporte de verificación manual con: motor, nombre
   del paquete, versión instalada (o "ausente"), versión requerida y funciones DataLab afectadas.
4. WHEN el reporte de verificación manual identifica paquetes faltantes, THE NEVEN Studio
   SHALL mostrar para cada paquete faltante un botón individual "Instalar" y un botón global
   "Instalar todos los faltantes".
5. WHEN el usuario cierra o recarga la página de NEVEN Studio, THE Package_Manager SHALL
   preservar el resultado del último reporte de verificación para que esté disponible al
   reabrir el panel.

---

### Requirement 5: Autorización del usuario antes de instalar

**User Story:** Como usuario de NEVEN, quiero que el sistema me pida confirmación
explícita antes de instalar cualquier paquete, para mantener control sobre lo que se instala
en mi entorno.

#### Acceptance Criteria

1. THE Package_Manager SHALL requerir autorización explícita del usuario para cada operación
   de instalación; nunca instalará paquetes de forma automática sin intervención del usuario.
2. WHEN el usuario autoriza la instalación de uno o más paquetes, THE Package_Manager SHALL
   agregar esos paquetes a la Cola_de_Instalación y ejecutarlos secuencialmente, uno por uno.
3. WHILE la Cola_de_Instalación tiene paquetes pendientes, THE NEVEN Studio SHALL mostrar
   el progreso de instalación indicando: nombre del paquete en curso, número de paquetes
   completados y número total autorizado.
4. WHEN la instalación de un paquete se completa con éxito, THE Package_Manager SHALL
   actualizar el Manifiesto con la versión instalada y notificar al usuario con el resultado.
5. IF la instalación de un paquete falla, THEN THE Package_Manager SHALL registrar el error
   completo en el log de NEVEN, notificar al usuario con el mensaje de error del gestor de
   paquetes nativo y continuar con el siguiente paquete de la Cola_de_Instalación.
6. THE Package_Manager SHALL instalar paquetes en la ruta del Motor activo en ese momento,
   de modo que los paquetes sean compatibles con la versión del Motor en uso.

---

### Requirement 6: Instalación de paquetes R

**User Story:** Como usuario de NEVEN, quiero que el Package Manager instale
paquetes R de forma confiable, para resolver dependencias del catálogo DataLab sin salir de
Excel.

#### Acceptance Criteria

1. WHEN el usuario autoriza la instalación de un paquete R, THE Package_Manager SHALL
   ejecutar `install.packages()` en el Motor R activo usando el repositorio CRAN configurado
   en `neven-config.json`, o `https://cloud.r-project.org` como valor predeterminado.
2. THE Package_Manager SHALL instalar paquetes R en la biblioteca de usuario
   (`Sys.getenv("R_LIBS_USER")`) del Motor R activo para preservar los paquetes ante futuras
   actualizaciones menores de R.
3. WHEN la instalación de un paquete R requiere dependencias adicionales, THE Package_Manager
   SHALL instalarlas con `dependencies = TRUE` e informar al usuario el número de paquetes
   adicionales descargados.
4. THE Package_Manager SHALL verificar la presencia de paquetes R usando `requireNamespace()`
   sobre el proceso ControlR.exe activo, no sobre el proceso Python del servidor NEVEN Studio.
5. THE Package_Manager SHALL incluir en el Manifiesto predeterminado los paquetes R mínimos
   del catálogo DataLab: `jsonlite`, `plm`, `stargazer`, `e1071`, `rpart`, `VGAM`, `tseries`,
   `FactoMineR`, `wooldridge`, `cluster`, `PerformanceAnalytics`, `plotly`, `htmlwidgets`,
   `fitdistrplus`.

---

### Requirement 7: Instalación de paquetes Julia

**User Story:** Como usuario de NEVEN, quiero que el Package Manager instale
paquetes Julia de forma confiable, para usar funciones del catálogo DataLab que dependen
de bibliotecas Julia.

#### Acceptance Criteria

1. WHEN el usuario autoriza la instalación de un paquete Julia, THE Package_Manager SHALL
   ejecutar `Pkg.add()` en el Motor Julia activo mediante el protocolo Named Pipe + Protobuf.
2. THE Package_Manager SHALL verificar la presencia de un paquete Julia usando
   `Base.find_package()` o `Pkg.status()` sobre el proceso ControlJulia.exe activo.
3. IF el Motor Julia no está activo al momento de la instalación, THEN THE Package_Manager
   SHALL diferir la instalación hasta que el Motor Julia esté disponible y notificar al usuario
   que la instalación quedó pendiente.
4. THE Package_Manager SHALL respetar el entorno de proyecto Julia activo (`Project.toml`) en
   el directorio `C:\NEVEN\` para evitar conflictos con instalaciones globales de Julia.

---

### Requirement 8: Instalación de paquetes Python

**User Story:** Como usuario de NEVEN, quiero que el Package Manager instale
paquetes Python de forma confiable, para usar funciones del catálogo DataLab que dependen
de bibliotecas Python.

#### Acceptance Criteria

1. WHEN el usuario autoriza la instalación de un paquete Python, THE Package_Manager SHALL
   invocar `pip install` usando el ejecutable Python localizado mediante `python3.dll` del
   Motor ControlPython.exe activo, reutilizando la lógica de `_get_python_exe()` del módulo
   `package_manager.py` existente.
2. THE Package_Manager SHALL verificar la presencia de un paquete Python usando `pip show`
   sobre el mismo ejecutable Python del Motor activo.
3. THE Package_Manager SHALL extender el módulo `package_manager.py` existente para exponer
   las funciones de verificación al endpoint HTTP `/api/packages` de NEVEN Studio, evitando
   duplicar la lógica de detección del ejecutable Python.
4. THE Package_Manager SHALL incluir en el Manifiesto predeterminado los paquetes Python
   mínimos del catálogo DataLab: `nltk`, `scikit-learn`, `pandas`, `numpy`.

---

### Requirement 9: Endpoint HTTP en NEVEN Studio

**User Story:** Como desarrollador de NEVEN, quiero que el Package Manager exponga
endpoints HTTP en NEVEN Studio para que la interfaz web pueda consultar el estado de paquetes
e iniciar instalaciones, sin duplicar lógica en el cliente.

#### Acceptance Criteria

1. THE NEVEN Studio SHALL exponer el endpoint `GET /api/packages/status` que retorna el
   estado de todos los paquetes del Manifiesto para todos los motores activos.
2. THE NEVEN Studio SHALL exponer el endpoint `GET /api/packages/status/{motor}` que retorna
   el estado de los paquetes de un motor específico (`r`, `julia`, `python`).
3. THE NEVEN Studio SHALL exponer el endpoint `POST /api/packages/install` que recibe una
   lista de paquetes autorizados por el usuario e inicia la Cola_de_Instalación.
4. WHEN un cliente realiza `GET /api/packages/status`, THE NEVEN Studio SHALL retornar la
   respuesta en formato JSON con el esquema: `{motor, paquete, instalado: bool,
   version_instalada, version_requerida, funciones_afectadas[]}`.
5. IF el Motor correspondiente no está disponible al consultar su estado, THEN THE NEVEN Studio
   SHALL retornar el campo `motor_disponible: false` en lugar de un error HTTP 5xx, para que
   la interfaz pueda mostrar un estado informativo.
6. THE NEVEN Studio SHALL exponer el endpoint `GET /api/packages/progress` que retorna el
   estado actual de la Cola_de_Instalación en tiempo real usando polling con intervalo máximo
   de 2 segundos.

---

### Requirement 10: Persistencia y logging

**User Story:** Como administrador de NEVEN, quiero que el Package Manager registre
todas sus operaciones en el log del sistema, para poder diagnosticar problemas de instalación
sin acceso a la interfaz gráfica.

#### Acceptance Criteria

1. THE Package_Manager SHALL registrar en el log de NEVEN (`C:\NEVEN\neven.log`) el resultado
   de cada Verificación con nivel INFO, incluyendo: motor, paquetes verificados, paquetes
   faltantes y duración de la verificación en milisegundos.
2. THE Package_Manager SHALL registrar en el log de NEVEN cada solicitud de instalación con
   nivel INFO, incluyendo: motor, nombre del paquete, versión objetivo y resultado.
3. IF una instalación falla, THEN THE Package_Manager SHALL registrar el error en el log de
   NEVEN con nivel ERROR, incluyendo el mensaje completo del gestor de paquetes nativo.
4. THE Package_Manager SHALL persistir el último estado de verificación en un archivo
   `packages-status-cache.json` en `C:\NEVEN\`, actualizado tras cada Verificación completa,
   para que NEVEN Studio pueda mostrarlo aunque el Motor no esté disponible en ese momento.
5. THE Package_Manager SHALL incluir en `packages-status-cache.json` la marca de tiempo ISO 8601
   de la última verificación exitosa de cada Motor, para informar al usuario cuándo fue la
   última revisión.
