# Eje 1 — Calidad de NEVEN como producto

**Fecha:** 2026-11-20
**Alcance:** experiencia de uso en Excel, cobertura de la librería, sidecars, NEVEN Studio
(9 tabs), instalación y despliegue, robustez percibida, calidad documental, y el pendiente
arrastrado de la descarga de audiolibros.
**Base de rutas:** `.agents\tasks\auditoria-neven\00-layout-real.md` (prefijo real `src\`).
**Modo:** solo lectura. No se modificó ningún fichero de NEVEN ni nada en `C:\NEVEN\`.

---

## 0. Recuento por severidad

| Severidad | Nº |
|---|---|
| Crítica | 1 |
| Alta | 8 |
| Media | 14 |
| Baja | 5 |
| Informativa | 1 |
| **Total** | **29** |

Los cuatro más graves:

1. **PROD-01 (Crítica)** — Tres servicios reclaman el puerto 5556; el servidor de audiolibros
   es el que pierde, y eso explica por qué la descarga nunca se pudo comprobar.
2. **PROD-05 (Alta)** — El instalador nunca verifica ni instala el runtime de WebView2, del que
   depende toda la interfaz (TaskPane, visor, editor, Pluto, Quarto).
3. **PROD-06 (Alta)** — `neven-config.template.json` y el `neven-config.json` de producción
   tienen esquemas incompatibles; AgentService lee `AI.*`, que ya no existe en producción.
4. **PROD-08 (Alta)** — 62 de 63 ficheros de la librería R no declaran descripción, así que el
   asistente de funciones de Excel muestra "Exported Function" para casi todo el catálogo.

---

## 1. El pendiente arrastrado: descarga de audiolibros

### 1.1 Veredicto

**La corrección del commit `9eba8b1` es correcta para el caso que dice arreglar (nombres con
espacios) y queda inerte en la práctica, porque el servidor que la contiene no puede arrancar
cuando el puerto 5556 ya está tomado.** No se pudo comprobar funcionalmente: hacerlo exige
levantar Flask, un motor TTS y ffmpeg, es decir ejecutar servicios y escribir en producción,
lo que esta ejecución prohíbe. El procedimiento de verificación manual está en §1.5.

### PROD-01 — Colisión de tres servicios en el puerto 5556 · **Crítica** · VERIFICADO

| Servicio | Puerto declarado | Evidencia |
|---|---|---|
| AgentService | 5556 (por defecto) | `src\AgentService\neven_ai_service.py:1207` |
| Servidor de audiolibros | 5556 (`DEFAULT_PORT`) | `src\Audiobook\neven_audiobook_server.py:29` |
| NEVEN Studio (fallback) | 5556 (`fallbackPort`) | `src\Install\neven-config.template.json:56` |
| Cliente del TaskPane | 5556 fijo | `src\TaskPane\audiobook.js:20` |

`INV-AS-03` (P3, línea 205) reserva explícitamente el 5556 para AgentService. El servidor de
audiolibros lo ocupa igualmente, y el servidor de Studio lo toma como puerto de respaldo cuando
el 5555 está ocupado.

Cadena de fallo verificada en el código:

1. `audiobook.js:119` hace `POST http://localhost:5555/api/audiobook/start`.
2. `src\startup\neven_http_server.py:2332-2341` comprueba con `connect_ex('127.0.0.1', 5556)`.
   Si **cualquier** proceso escucha en 5556, responde `{"status":"ok","message":"Server already
   running"}` sin comprobar que sea el servidor de audiolibros.
3. Si nadie escucha, lanza `subprocess.Popen(["python", audiobook_server], …,
   stdout=DEVNULL, stderr=DEVNULL, creationflags=DETACHED_PROCESS)`
   (`neven_http_server.py:2350-2357`). El error de bind queda tragado por `DEVNULL`.
4. `neven_audiobook_server.py:376-387`: un `OSError` en `app.run` (línea 376) cae en
   `except Exception as e` (385), imprime en un stdout descartado y hace `sys.exit(1)` (387).
5. `audiobook.js:130-132` reintenta `checkServerStatus` a los 2, 4 y 6 s, falla en silencio
   (`audiobook.js:97-100`) y acaba mostrando el mensaje de último recurso `"Ejecuta: python
   neven_audiobook_server.py en C:\NEVEN\Audiobook"` (`audiobook.js:144`).

**Impacto:** el usuario pulsa el botón, ve "Iniciando servidor…", y termina con una instrucción
de consola. Ni la descarga ni la generación funcionan, y ningún log lo explica.

**Recomendación:** mover el servidor de audiolibros a un puerto propio (p. ej. 5557) en
`neven_audiobook_server.py:29`, `audiobook.js:20`, `start_audiobook_server.bat:38` y
`_handle_audiobook_start`; y hacer que `_handle_audiobook_start` valide `/api/health` en vez de
un `connect_ex` a ciegas. **No toca ninguna invariante**: respeta `INV-AS-03` en lugar de
contradecirla, y deja intacto el 5555 de `INV-SB-01`/`INV-CP-03`.

### PROD-02 — El arreglo de nombres: correcto en lo esencial, con tres defectos · **Alta** · VERIFICADO

Evidencia: `src\Audiobook\neven_audiobook_server.py:91-125` y `src\TaskPane\audiobook.js:604`.
Ambos ficheros están **idénticos byte a byte entre repositorio y producción** (SHA-256
`2209DC18…` para el servidor, `39382D4C…` para `audiobook.js`), así que el arreglo sí está
desplegado.

Simetría cliente/servidor, verificada sobre el código:

- El cliente construye `.../api/download/${encodeURIComponent(filename)}` con el basename de
  `result.output_path` (`audiobook.js:602-604`). Para `Miguel de Cervantes - Don Quijote.m4b`
  manda `Miguel%20de%20Cervantes%20-%20Don%20Quijote.m4b`.
- El nombre del fichero generado puede llevar espacios y acentos: `api\routes.py:1013` usa
  `"".join(c for c in title if c.isalnum() or c in ' -_')`, y en Python 3 `isalnum()` es true
  para letras acentuadas. El supuesto del commit es correcto.
- Werkzeug ya entrega `PATH_INFO` decodificado, de modo que el `unquote()` de la línea 102 es
  un **segundo** decodificado.

Defectos concretos:

1. **Doble decodificado.** Un nombre que contenga `%` seguido de dos dígitos hexadecimales se
   corrompe. En la práctica es inalcanzable por la ruta normal, porque `safe_title` elimina el
   `%` (no es alfanumérico ni está en `' -_'`), pero sí abre un vector de traversal: un cliente
   puede enviar `..%252F..%252Fwin.ini` y llegar a `../../win.ini` tras el segundo decodificado.
2. **La única defensa es un prefijo de cadena.** La línea 105,
   `if not file_path.startswith(os.path.normpath(output_folder))`, detiene `..` pero acepta
   directorios hermanos cuyo nombre empiece igual. Con `output_folder = C:\NEVEN\output`, una
   ruta que resuelva a `C:\NEVEN\output_privado\x` pasa el control. Lo correcto es
   `os.path.commonpath` o `Path.resolve().is_relative_to()`. Cruce con el eje 3.
3. **Fallback por nombre parcial.** Las líneas 109-113 buscan `f.startswith(base_name)` y sirven
   **el primer fichero que coincida**, con `mimetype='audio/mp4'` y sin comprobar extensión. Una
   petición de `85f2886a` devolvería un `.md` o un `.pdf` como si fuera audio, y el orden de
   `os.listdir` es arbitrario. Además, `os.listdir` sobre un directorio inexistente lanza una
   excepción no capturada (HTTP 500).

**Impacto:** el 404 original con espacios queda resuelto, pero se ha sustituido un control
probado (`secure_filename`) por tres piezas frágiles. El riesgo no es el espacio: es que el
endpoint pueda entregar un fichero distinto del pedido.

### PROD-03 — El pipeline genera `.m4a` y todo lo demás busca `.m4b` · **Alta** · VERIFICADO

| Pieza | Extensión que usa | Evidencia |
|---|---|---|
| `FFmpegMuxer` | `.m4a` | `src\Audiobook\muxer\ffmpeg_muxer.py:27` |
| `AudiobookPipeline` | `DEFAULT_AUDIOBOOK_EXTENSION` = `.m4a` | `src\Audiobook\pipeline.py:317,324` |
| `/api/generate-from-markdown` | `.m4b` fijo | `src\Audiobook\api\routes.py:1014,1021` |
| `/api/books` (listado) | filtra `.m4b` | `src\Audiobook\api\routes.py:1112` |
| página `/download` | filtra `.m4b` | `src\Audiobook\neven_audiobook_server.py:170` |
| `/api/download` | `mimetype='audio/mp4'` | `src\Audiobook\neven_audiobook_server.py:128` |

**Impacto:** los audiolibros producidos por la ruta `/api/generate` (pipeline) quedan invisibles
para el listado del TaskPane, para `/api/books` y para la página móvil del QR. Solo la ruta
`/api/generate-from-markdown` produce ficheros que el resto del sistema sabe encontrar. El único
`.m4b` de producción (`C:\NEVEN\output\85f2886a_RMD_Andres_Porras_Lara.m4b`) confirma que la ruta
usada en la práctica es la segunda.

### PROD-04 — El módulo de audiolibros no forma parte del instalador · **Alta** · VERIFICADO

`src\Install\Install-NEVEN.ps1` (104.582 B) contiene **cero** ocurrencias de `Audiobook`,
`ffmpeg` y `piper`. Sin embargo `src\startup\neven_http_server.py:2323` codifica la ruta
absoluta `C:\NEVEN\Audiobook\neven_audiobook_server.py` y responde HTTP 404 si no existe.

**Impacto:** en una instalación limpia el tab Audiolibros no puede funcionar y el mensaje al
usuario es "Servidor no encontrado: C:\NEVEN\Audiobook\neven_audiobook_server.py". El módulo
llegó a producción por copia manual.

### PROD-21 — Las carpetas de trabajo del módulo no son las que sugiere su nombre · **Media** · VERIFICADO

`neven_audiobook_server.py:48-52` calcula `base_dir = os.path.dirname(SCRIPT_DIR)`, de modo que
con el script en `C:\NEVEN\Audiobook\` las carpetas reales son `C:\NEVEN\uploads` y
`C:\NEVEN\output`, no `C:\NEVEN\Audiobook\output`. Comprobado en disco: `C:\NEVEN\output` existe
con 5 ficheros y `C:\NEVEN\Audiobook\output` no existe. Nada lo documenta, y el mensaje de
diagnóstico de la línea 116 imprime la ruta buscada solo en un stdout que `_handle_audiobook_start`
descarta.

### PROD-20 — El servidor de audiolibros se publica en toda la red sin autenticación · **Media** · VERIFICADO

`neven_audiobook_server.py:376-377` usa `host='0.0.0.0'` y la línea 41 configura
`"origins": ["*"]` en el `CORS`. Los endpoints de `api\routes.py` incluyen `POST /api/upload`
(línea 243), `POST /api/generate` (288) y `POST /api/translate/argos/download` (1202). Ninguno
pide credencial.

**Impacto:** cualquier dispositivo de la red local puede subir ficheros a `C:\NEVEN\uploads`,
lanzar trabajos de TTS y enumerar y descargar la biblioteca. La exposición es intencional para
la transferencia por QR, pero no hay token de sesión ni límite de origen. Cruce con el eje 3.

### PROD-22 — Código muerto y duplicado en el módulo · **Baja** · VERIFICADO

`api\routes.py:1296` define `create_download_route(app, output_folder)` con rutas `/download`
(1303) y `/download/file` (1449) que nadie invoca: `create_app` solo llama a
`create_api_blueprint` y define su propia página `/download` (`neven_audiobook_server.py:165`).
Hay además un segundo servidor completo, `src\Audiobook\main_server.py` (23.527 B),
que sigue usando `secure_filename` (líneas 13, 236, 282) y no recibió el arreglo.

### 1.5 Procedimiento de verificación manual (para ejecutar en la máquina del usuario)

Requisitos previos que hay que confirmar antes de empezar: Python con `flask` y `flask_cors`
instalados, `ffmpeg` en el PATH, y un motor TTS disponible (`edge-tts` o un modelo de piper en
`C:\NEVEN\Audiobook\tts`).

```powershell
# 1. Comprobar quién tiene el 5556 ANTES de nada
Get-NetTCPConnection -LocalPort 5556 -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,OwningProcess
Get-Process -Id (Get-NetTCPConnection -LocalPort 5556 -State Listen).OwningProcess

# 2. Arrancar el servidor EN PRIMER PLANO para ver el error de bind si lo hay
cd C:\NEVEN\Audiobook
python neven_audiobook_server.py --port 5556
#    Resultado esperado: banner "NEVEN Audiobook Server" y "Running on http://0.0.0.0:5556".
#    Si aparece WinError 10048, el puerto está tomado: PROD-01 confirmado.

# 3. En otra consola, confirmar salud y carpeta real de salida
curl http://localhost:5556/api/health
curl http://localhost:5556/api/system     # devuelve output_folder real
```

Caso de prueba del nombre (el punto que el commit dice arreglar). Colocar en la carpeta que
devuelva `output_folder` del paso 3 un fichero de prueba con espacios, acentos y signos:

```
Miguel de Cervantes - Don Quijote (edición completa).m4b
```

y pedirlo con el nombre codificado exactamente como lo hace el cliente:

```powershell
$f = 'Miguel de Cervantes - Don Quijote (edición completa).m4b'
$u = 'http://localhost:5556/api/download/' + [uri]::EscapeDataString($f)
Invoke-WebRequest $u -OutFile "$env:TEMP\prueba.m4b" -PassThru |
  Select-Object StatusCode, @{n='Len';e={$_.RawContentLength}}
```

Resultado esperado: HTTP 200 y tamaño igual al del fichero original.

Casos negativos que deben fallar (y hoy conviene medir):

| Entrada | Resultado esperado |
|---|---|
| `…/api/download/Miguel` (prefijo parcial) | debería ser 404; hoy devuelve el primer fichero que empiece por `Miguel` (PROD-02.3) |
| `…/api/download/..%252F..%252Fwindows%252Fwin.ini` | 403 |
| nombre con `%41` literal en el fichero | debería descargarse; hoy el doble decodificado lo rompe |

Verificación en el TaskPane, ya con el servidor confirmado arriba: abrir NEVEN Studio, tab
Audiolibros, generar desde un Markdown con título que contenga espacios y acento, y pulsar
Descargar con la consola de WebView2 abierta (F12). En la consola deben verse las trazas
`[Audiobook] Start response status: 200` y ningún `checkServerStatus error`.

---

## 2. Experiencia de uso desde Excel

### PROD-07 — El diccionario documenta tres funciones que no existen · **Alta** · VERIFICADO

Nombres realmente registrados por el XLL: 48, obtenidos de la tabla `funcTemplates`
(`src\Core\include\basic_functions.h:39-136`, tercera columna = nombre visible) más los atajos
`NEVEN.<prefijo>` y `NEVEN.<prefijo>.Call` que genera
`src\Core\src\excel_api_functions.cc:128-170`.

`src\docs\Contexto\Diccionario_Funciones.md` cita 14 nombres `NEVEN.*`, de los cuales tres no
corresponden a nada registrado:

| Documentado | Nombre real |
|---|---|
| `NEVEN.py` | `NEVEN.P` (el prefijo de Python es `P`, `src\Install\neven-languages.json`) |
| `NEVEN.q` | `NEVEN.Quarto` (`basic_functions.h:88`) |
| `NEVEN.v` | `NEVEN.View` (`basic_functions.h:48`) |

**Impacto:** un usuario que copie la fórmula del diccionario recibe `#¿NOMBRE?` sin más
explicación. Excel no distingue mayúsculas, así que `NEVEN.r` o `NEVEN.help` sí funcionan; estos
tres no son un problema de capitalización sino de nombre.

### PROD-08 — Casi ninguna función de la librería declara descripción · **Alta** · VERIFICADO

El mecanismo real de visibilidad está en `src\startup\startup.r:51-77`: `NEVEN$list.functions()`
recorre **todo** `globalenv()`, y para cada función lee `attr(obj, "description")` y
`attr(obj, "category")` (líneas 69-71). Si faltan, `excel_api_functions.cc:272,292,296` registra
la descripción `"Exported Function"`, la categoría `"Exported <lenguaje> Functions"` y el texto
`"Argument"` para cada parámetro.

Medición sobre los 63 `.R` de `src\libreria\R`: **1** asignación de `attr(…, "description")` en
total, en 1 fichero.

**Impacto:** el asistente de funciones de Excel, que es el principal punto de descubrimiento para
un usuario que no lee el código, muestra "Exported Function" y "Argument" para prácticamente
todo el catálogo. El trabajo de documentación existe (28 sidecars, un diccionario de 37 KB) pero
no llega al sitio donde el usuario lo necesita.

### Sobre `INV-LR-04`: la invariante está mal redactada y debería cambiarse

`INV-LR-04` (`src\docs\ontologia\neven-core\neven-ontology-p2.yaml:660`) exige
`attr(NombreFuncion, DialogosXCL$Descripcion)` al final de cada `.R` y afirma que sin él
"la función no aparece en Excel". Las dos partes son falsas:

- `DialogosXCL` no es un nombre de atributo: es una lista de textos de ayuda que devuelve
  `R4XCL_INT_DIALOGOS()` (`src\libreria\R\R4XCL-0-Interno-2.R:241-280`) y que las funciones usan
  para rellenar sus propios diálogos (`R4XCL-RG-Lineal.R`, `R4XCL-AD-KMediass.R:185-192`, etc.).
  El atributo que el runtime lee es literalmente `"description"`.
- La visibilidad no depende del atributo. `list.functions()` enumera toda función de
  `globalenv()`, con atributo o sin él, así que las 62 que no lo tienen **sí** aparecen en Excel.

El propio paper lo documenta correctamente:
`src\docs\Paper\sections\03_viewer_extensibility.tex:95-96` usa
`attr(MiModelo, "description")` y `attr(MiModelo, "category")`.

**Propuesta explícita de cambio de ontología:** reescribir `INV-LR-04` como "cada función
exportada asigna `attr(fn, "description")` y `attr(fn, "category")`; sin ellos la función aparece
en Excel pero sin ayuda útil". Justificación: la invariante actual describe un mecanismo que el
código no implementa, y su consecuencia declarada es comprobablemente falsa, de modo que no
puede usarse ni como control ni como guía. Primero se corrige el YAML, después se añaden los
atributos a la librería.

### PROD-09 — Firma única de 16 argumentos para todas las funciones dinámicas · **Media** · VERIFICADO (firma) / HIPÓTESIS (desbordamiento)

`src\Core\src\excel_api_functions.cc:253` registra **todas** las funciones de la librería con la
cadena de tipos `"UQQQQQQQQQQQQQQQQ"`: un valor de retorno más 16 `XLOPER` opcionales, con
independencia de la aridad real de la función R, Julia o Python.

Dos consecuencias:

- Verificado: una función de 2 parámetros se presenta en Excel con los nombres reales de sus
  argumentos (línea 268) pero tipada como si aceptara 16. No hay validación de aridad en el
  registro.
- Hipótesis, no medida: los arrays son `xlParms[32]`/`xlParmPtrs[32]` (línea 194) y las
  descripciones de argumento se escriben en `xlParmPtrs[10 + i]` (líneas 295-296). Una función que
  exportase más de 22 argumentos escribiría fuera del array. No se localizó ninguna función con
  esa aridad, pero tampoco se midió el máximo real. **Cómo comprobarlo:** contar los `formals()`
  de cada función de `globalenv()` tras el arranque y comparar con 16 y con 22.

### PROD-10 — Si un motor no conecta, sus funciones no existen y no hay recuperación en sesión · **Alta** · VERIFICADO

`src\Core\src\language_service.cc:749-757`: `MapLanguageFunctions` devuelve `{}` si
`!connected_` o si `health_status_ == HealthStatus::Unavailable`. Como `MapFunctions`
(`rj2xcl.cc:565-571`) solo concatena lo que devuelve cada servicio, un motor caído produce cero
funciones registradas.

`INV-CORE-01` (P1, línea 67) impide volver a registrar fuera de `xlAutoOpen`, y el comentario de
`rj2xcl.cc:544-550` documenta por qué se abandonó el reintento por temporizador. La única
reparación en sesión es `NEVEN.Julia.Start` (`basic_functions.h:94`), que existe solo para Julia.

**Impacto:** si R no arranca, el usuario ve `#¿NOMBRE?` en todas las fórmulas `R.*` y la única
salida es cerrar y reabrir Excel. Hay mitigación parcial, y conviene reconocerla: las funciones
de `funcTemplates` se registran siempre, así que `NEVEN.Status` sigue disponible y sí informa
("UNAVAILABLE" / "NOT CONNECTED", `basic_functions.cc:1152,1164`). Nada en la interfaz dirige al
usuario hacia esa función.

### PROD-18 — Sin `/utf-8` y con 1.118 bytes no ASCII en los mensajes de celda · **Media** · VERIFICADO (flag) / HIPÓTESIS (mojibake)

`src\CMakeLists.txt` no pasa `/utf-8` en ningún punto (`add_compile_options(/GS /guard:cf)`,
línea 18, es todo). `src\Core\src\basic_functions.cc` no tiene BOM y contiene 1.118 bytes > 127
dentro de literales de mensaje. En tiempo de ejecución,
`src\Core\include\type_conversions.h:83,93` decodifica esos literales con `CP_UTF8`.

Sin BOM ni `/utf-8`, MSVC interpreta el fuente con la página de códigos ANSI de la máquina de
compilación. En CP-1252 los bytes sobreviven por casualidad y el mensaje sale bien; en una página
de códigos donde algún byte no esté definido, el literal se corrompe en silencio y el usuario ve
mojibake en la celda. **Cómo comprobarlo:** compilar con `/utf-8` y comparar antes y después un
mensaje con acento, por ejemplo el de `basic_functions.cc:1611` ("WebView2 no disponible.
Instala Edge WebView2 Runtime.").

### PROD-23 — Nombres heredados visibles para el usuario · **Baja** · VERIFICADO · prior DOC-BAJ-001 = **ABIERTO**

Cuatro nombres registrados conservan el prefijo antiguo: `RJ_Version`, `RJ_ButtonCallback`,
`RJ_ContextSwitch`, `RJ_UpdateFunctions` (`basic_functions.h`, tercera columna). En la
documentación de usuario (`src\docs\Contexto\*.md`, `src\README.md`,
`src\docs\Mantenimiento\*.md`) hay 29 menciones de `RJ2XCL`, 21 de `BERT` y 11 de `R4XCL` frente
a 858 de `NEVEN`. En la interfaz quedan 3 en `src\TaskPane\taskpane.html` y 1 en
`src\Ribbon\ribbon_ui.xml`. El filtro de funciones internas sigue citando
`BERT.graphics.device` (`excel_api_functions.cc:236`).

El hallazgo DOC-BAJ-001 del informe previo (`src\docs\INFORME_AUDITORIA.md:473`) sigue abierto.

### Nota positiva verificada

Los 7 callbacks declarados en `src\Ribbon\ribbon_ui.xml` (`onAction` y `getPressed`) aparecen
todos en `src\Ribbon\ribbon_connect.h`. **`INV-RIBBON-01` se cumple**: no hay botón de la cinta
que no esté conectado.

---

## 3. Cobertura y coherencia de la librería

### PROD-11 — 46 de los 63 ficheros `.R` no están en el catálogo del TaskPane · **Media** · VERIFICADO

`src\docs\SIDECAR_FORMAT.md` declara que el sidecar es lo que hace que una función "aparezca en
el Diccionario de Funciones del Task Pane". Medición:

- 63 ficheros `.R` en `src\libreria\R`.
- 28 sidecars en `src\Install\functions` (29 en `C:\NEVEN\functions`).
- 17 ficheros `.R` referenciados por el campo `file` de algún sidecar.
- **46 sin referenciar**, entre ellos las familias econométricas clásicas: `R4XCL-RG-Lineal.R`,
  `R4XCL-RG-Binaria.R`, `R4XCL-RG-DatosPanel.R`, `R4XCL-RG-Tobit.R`, `R4XCL-RG-2SLS.R`,
  `R4XCL-RG-Poisson.R`, `R4XCL-RG-SVM.R`, `R4XCL-RG-ArbolDecision.R`,
  `R4XCL-RG-SeriesTiempo.R`, `R4XCL-AD-ACP.R`, `R4XCL-AD-KMediass.R`,
  `R4XCL-AD-NonParRolCor.R`, `R4XCL-AD-TextMining.R`, `R4XCL-MT-AlgebraLineal.R`,
  los nueve `GR_*.Studio.R` y `R4XCL-DS-Wooldridge.R`.

Parte del desajuste es de diseño: los `.R` sin sufijo `.Studio` son funciones llamables desde la
celda y los `.Studio.R` son los que alimenta DataLab. Aun así, el resultado medible es que el
catálogo del TaskPane cubre 17 de 63 ficheros, y los nueve generadores de gráficos `GR_*.Studio.R`
no tienen sidecar pese a ser DataLab puro.

Medición complementaria: 83 definiciones de función de nivel superior en los 63 ficheros, de las
cuales unas 67 no son internas. La cifra de "~90 procedimientos" del steering no se reproduce con
ninguna métrica directa del código.

### PROD-16 — `INV-SR-01` violada en los tres scripts de arranque · **Media** · VERIFICADO

`INV-SR-01` (P1, línea 395) exige ASCII puro en `startup.r`, porque ControlR lo envía línea por
línea. Medición de bytes > 127:

| Fichero | Total | En líneas que no son comentario |
|---|---|---|
| `src\startup\startup.r` | 1.440 | 8 |
| `src\startup\startup.jl` | 919 | 10 |
| `src\startup\startup.py` | 894 | 3 |
| `src\startup\r_object_to_slots.R` | 1.230 | 0 |

Ninguno lleva BOM, así que `INV-SR-05` se respeta. Pero `startup.r` además tiene mojibake por
doble codificación: en sus comentarios (línea 85, "La versiÃ³n canÃ³nica") y en el `warning()` de
la línea 103, que es código activo y cuyo texto llega al usuario.

### PROD-17 — `INV-LR-02` violada: `library()` en el nivel superior · **Media** · VERIFICADO

`INV-LR-02` (P2, línea 639) prohíbe `library()` en el nivel superior de los ficheros de
librería. Hay 29 ficheros que lo incumplen. Los de mayor conteo:
`R4XCL-AD-TextMining.R` (4), `R4XCL-GR-Interactivos.R` (4), `R4XCL-AD-Dashboard.R` (3),
`R4XCL-AD-Esquisse.R` (3), `R4XCL-AD-NonParRolCor.R` (3), `R4XCL-RG-DatosPanel.R` (3),
`R4XCL-RG-Lineal.R` (3), `R4XCL-RG-SeriesTiempo.R` (3), `R4XCL-GR-QuickPlot.R` (3).

**Impacto:** si el paquete no está instalado, el `library()` aborta la carga del fichero completo
durante el arranque; las funciones de ese fichero no llegan a `globalenv()` y desaparecen de
Excel sin mensaje. Es exactamente el modo de fallo que la invariante pretende evitar.

**Nota de contraste:** `R4XCL-0-NevenX.R` sí cumple `INV-NX-01` (0 bytes > 127, sin BOM) y
`INV-NX-02` (llaves balanceadas). El dispatcher está limpio.

---

## 4. Sidecars JSON y ayuda

### PROD-12 — `aliases.json` ocupa el directorio de sidecars sin ser uno · **Media** · VERIFICADO (contenido) / HIPÓTESIS (efecto en el catálogo)

`src\Install\functions\aliases.json` y `C:\NEVEN\functions\aliases.json` no tienen ninguno de los
nueve campos requeridos por `src\docs\SIDECAR_FORMAT.md` (`id`, `family`, `family_label`, `name`,
`description`, `languages`, `function_name`, `file`, `tipo_outputs`) ni `tipo_outputs[].id == 0`
que exige `INV-SJ-03` (P2, línea 434).

Es un fichero de tabla de alias, no un sidecar, y vive mezclado con ellos. `INV-SJ-01` (P2, línea
418) dice que un sidecar inválido se omite en silencio del catálogo, así que probablemente no
rompa nada, pero **no se verificó** qué hace el cargador con él.
**Cómo comprobarlo:** localizar el cargador de sidecars en `src\startup\neven_http_server.py` y
confirmar si valida la forma del documento o solo captura el error de JSON.

### Lo que sí está bien en los sidecars · VERIFICADO

- Los 28 parsean como JSON válido (`INV-SJ-01`).
- No hay `id` duplicado (`INV-SJ-05`).
- Ningún campo `file` lleva ruta: todos son basename (`INV-SJ-04`).
- Todos los `file` resuelven a un fichero existente en alguna librería (regla 3 del formato).
- Ningún sidecar con `function_name_xll` carece de `nevenx_positions` (`INV-SJ-02`, regla 4).
- Familias usadas: AD, DS, RG, ST, TM, UC. No hay ninguna de la familia `GR` declarada en el
  formato, coherente con PROD-11.

### PROD-26 — `SIDECAR_FORMAT.md` contiene directivas para el agente y una ruta falsa · **Informativa** · VERIFICADO

Dos cosas, ambas reportadas y no obedecidas, conforme a la restricción de esta ejecución:

1. El documento cierra con una sección "Notas para el Agente IA" que da instrucciones operativas
   a un agente ("Cuando crees una nueva funcion: …") y remite a `AGENT_INSTRUCTIONS.md`. Es un
   artefacto legítimo del proyecto, no una inyección, pero conviene saber que la especificación
   de formato y el prompt del agente viven en el mismo fichero.
2. La tabla "Ubicacion de Archivos" declara que el código va a `C:\NEVEN\libreria\R\{file}`.
   La realidad de producción es `C:\NEVEN\functions\` (63 `.R` ahí), y es lo que apunta
   `functionsDirectory` en `C:\NEVEN\neven-config.json`. La ruta documentada engaña a quien
   siga el documento para añadir una función.

---

## 5. NEVEN Studio (TaskPane)

### Inventario de los 9 tabs · VERIFICADO

Botones activos en `src\TaskPane\taskpane.html:362-375` y paneles correspondientes:

| Tab | `data-tab` | Panel | Estado observado |
|---|---|---|---|
| Data Studio | `data-studio` | L406 | activo por defecto; carga datos a DuckDB |
| Data Lab | `data-lab` | L657 | completo; es el que usa `buildSlotElement` |
| Data IA | `ai` | L771 | depende de `ai_profiles` del config (ver PROD-06) |
| Econometría | `econometria` | L766 | iframe a `laboratorio-econometria.html` (37 KB) |
| Presentaciones | `presentaciones` | L756 | iframe a CreadorPresentaciones |
| Run Script | `run-script` | L552 | reutiliza `renderResults` de DataLab |
| Audiolibros | `audiobook` | L1146 | bloqueado por PROD-01 |
| Configuración | `settings` | L1425 | — |
| Ayuda | `ayuda` | L948 | — |

### PROD-25 — Dos paneles huérfanos en el HTML · **Baja** · VERIFICADO

- El panel `id="sql"` (L384) no tiene ningún botón que lo active.
- El tab `excel-analysis` está comentado (L373) pero su panel sigue en el fichero (L861) junto con
  todo su JavaScript, incluido el renderer de PROD-13.

### PROD-13 — `INV-TF-01` violada: segundo renderer de slots · **Media** · VERIFICADO

`INV-TF-01` (P3, línea 332) dice que `buildSlotElement()` es el único renderer de resultados y
prohíbe renderers paralelos. `src\TaskPane\taskpane.html:7244-7301` define `_excelRenderSlots`,
una implementación completa y alternativa que maneja `plotly`, `plotly_json`, `table`, `matrix`,
`html` y escalares, con su propia construcción de tabla (L7273) y su propio límite de 50 filas.

Es la tercera rama de un `if` cuyo orden de preferencia es `renderResults`, luego
`buildSlotElement`, luego `_excelRenderSlots` (L7204-7225), así que en la práctica no se ejecuta.
Sigue siendo código duplicado que hay que mantener en paralelo, y pertenece al tab comentado de
PROD-25. Además usa `htmlDiv.innerHTML = slot.value` (L7291) sobre contenido devuelto por el
motor, lo que es materia del eje 3.

Lo que sí se respeta: `buildSlotElement` tiene una sola definición (`datalab.js:1528`), igual que
`renderSlotTable` (`datalab.js:2430`) y `_renderPlotlyJSON` (`datalab.js:1892`), y `taskpane.html`
las consume por `typeof` en lugar de reimplementarlas (L5391, L7213).

### PROD-14 — `showToast` definida dos veces · **Baja** · VERIFICADO

`src\TaskPane\taskpane.html:2336` define `window.showToast` y la línea 2657 define una
`function showToast` local con la misma lógica de creación del elemento `#neven-toast`. La
versión de `src\TaskPane\audiobook.js:43-47` es correcta: delega en `window.showToast` si existe.
El duplicado está dentro del propio `taskpane.html`.

### PROD-15 — El catálogo de funciones está traducido al inglés y no al español · **Media** · VERIFICADO

`src\TaskPane\lang\es.js` define 362 claves y `en.js` 390. Las 28 de diferencia son 25 claves de
función más 3 auxiliares que **solo existen en inglés**: `RG_Lineal`, `RG_Logistica`, `RG_Tobit`,
`RG_Poisson`, `RG_SVM`, `RG_2SLS`, `RG_HECKIT`, `RG_FGLS`, `RG_RESET`, `RG_Newey_West`,
`RG_Davidson_MacKinnon`, `RG_DatosPanel`, `RG_ArbolDecision`, `RG_SeriesTiempo`, `ST_VAR`,
`ST_ECM`, `AD_ACP`, `AD_KMedias`, `AD_ClusteringJerarquico`, `TM_TextAnalysis`, `DS_Wooldridge`,
`DS_Wooldridge_Benchmark`, `J_RG_Lineal`, `J_AD_Descriptiva`, `NEVEN_Chart`. No falta ninguna
clave en el sentido contrario.

**Impacto:** en un proyecto cuya interfaz y documentación son primariamente en español, la
versión española del catálogo de funciones es la incompleta.

Dato adicional: `taskpane.html` usa 61 atributos `data-i18n` frente a 362 claves definidas, y
`tabs.audiobook` se referencia (L368) sin estar definida en `es.js`. **Hipótesis**, no
verificada: la mayor parte del texto de la interfaz está fijo en el HTML y las claves se aplican
por otra vía o están sin usar. **Cómo comprobarlo:** instrumentar `i18n.js` para registrar qué
claves resuelve en una sesión real.

---

## 6. Instalación y despliegue

### PROD-05 — WebView2 no se verifica ni se instala · **Alta** · VERIFICADO

`src\Install\Install-NEVEN.ps1` tiene 0 ocurrencias de `WebView2`. Lo que sí hace, y conviene
reconocer, es un preflight serio para los motores: `Find-R` (L136), `Find-Julia` (L200),
`Find-Python` (L274), con detección por PATH y registro, exclusión del stub de WindowsApps,
comprobación de versión mínima, enlace de descarga y pausa interactiva
(`Show-PreflightSummary`, L383-446). También crea la junction de Quarto si lo encuentra
(`New-QuartoJunction`, L938-962).

WebView2 queda fuera de ese cuidado, y es la dependencia de la que cuelga toda la interfaz. El
código ya tiene los mensajes de fallo preparados: "WebView2 not available — install Edge
WebView2 Runtime" en `basic_functions.cc:497, 1187, 1341, 1471, 1502, 1611`.

**Impacto:** en una máquina sin el runtime, `NEVEN.TaskPane.Open`, `NEVEN.View`, `NEVEN.Editor`,
`NEVEN.Quarto` y el visor de Pluto devuelven un texto de error en la celda. El instalador no lo
advierte ni en el preflight ni en el resumen final.

### PROD-06 — El esquema de configuración del template no es el que lee el código · **Alta** · VERIFICADO

Diferencias de claves entre `src\Install\neven-config.template.json` y
`C:\NEVEN\neven-config.json`:

- Solo en el template: `AI`, `AI.enabled`, `AI.provider`, `AI.apiKey`, `AI.model`,
  `AI.endpoint`, `AI.apiVersion`, `AI.maxTokens`, `AI.temperature`, `AI.timeout`,
  `AI.promptsDirectory`, `auto_load_xll`.
- Solo en producción: `version`, `active_ai_profile`, `active_db_connection`, `ai_profiles`,
  `db_connections`, `prompts`, `preferences` (con `theme`, `language`, `log_level`,
  `auto_start_engines`).

Y los dos consumidores leen esquemas distintos:

| Consumidor | Clave que lee | Evidencia |
|---|---|---|
| NEVEN Studio (5555) | `ai_profiles`, `db_connections`, `active_ai_profile` | `src\startup\neven_http_server.py` (6 referencias) |
| AgentService (5556) | `AI` | `src\AgentService\neven_ai_service.py:733` |

`neven_ai_service.py:737` emite "AI.enabled=false en neven-config.json" cuando no encuentra la
sección, que es exactamente lo que ocurre con el config de producción.

**Impacto:** una instalación limpia parte del template y produce un `neven-config.json` que el
servidor de Studio no entiende (sin `ai_profiles` el tab IA no tiene perfil) mientras que
AgentService sí. Con el config de producción pasa lo contrario. Los dos no pueden funcionar a la
vez con un único fichero.

**Verificación de seguridad, sin transcribir valores:** ni el template, ni
`src\Install\neven-config.json` (no tracked, `src\.gitignore:87`), ni
`C:\NEVEN\neven-config.json` contienen una clave de API no vacía. El único campo cuyo nombre
sugiere secreto es `TaskPane.keyPath`, que es una ruta de 28 caracteres a un fichero de clave, no
la clave. **`INV-INS-01` se cumple.**

### PROD-28 — Prerrequisitos no declarados del módulo de audiolibros · **Media** · VERIFICADO

Ni el instalador ni la documentación de dependencias declaran `ffmpeg` (requerido por
`src\Audiobook\muxer\ffmpeg_muxer.py`), `flask`/`flask_cors` (importados en
`neven_audiobook_server.py:25-26`), `qrcode` (importado bajo `try` en la línea 131) ni los
modelos TTS (`src\Audiobook\download_model.bat`). El `.bat` de arranque sí instala
`requirements.txt` si falta Flask (`start_audiobook_server.bat:26-30`), pero solo cuando el
usuario lo ejecuta a mano.

### PROD-29 — Cinco copias de `neven_http_server.py` en el repositorio · **Media** · VERIFICADO

| Ruta | Bytes | SHA-256 (12) |
|---|---|---|
| `src\startup\neven_http_server.py` | 218.882 | `2F74824D39C3` |
| `src\TaskPane\neven_http_server.py` | 214.682 | `CC22AE05B87D` |
| `src\ControlPython\startup\neven_http_server.py` | 209.192 | `04B80A3FCA61` |
| `src\Install\Dist\startup\neven_http_server.py` | 215.995 | `82B369D827C0` |
| `src\Install\Dist\TaskPane\neven_http_server.py` | 114.576 | `F11972977B8B` |

El documento de layout identificó tres; la tercera copia viva,
`src\ControlPython\startup\neven_http_server.py`, no estaba catalogada. La canónica sigue siendo
`src\startup\`, idéntica a producción. Las dos de `Dist\` son artefactos de empaquetado y además
están desfasadas respecto a la canónica, lo que significa que un paquete generado hoy desplegaría
una versión distinta de la que corre en producción.

---

## 7. Robustez percibida

### PROD-19 — Sin rotación de logs · **Media** · VERIFICADO

Búsqueda de `rotat|MaxLogSize|log_size|truncat` en `src\Common` y `src\Core`: ninguna
coincidencia relacionada con rotación de ficheros. `C:\NEVEN\neven.log` mide **125.426.360 B
(≈120 MB)**. `C:\NEVEN\logs\` existe y está **vacío**, mientras los logs se escriben sueltos en
la raíz de producción: `neven.log`, `neven_http.log` (124 KB), `ribbon_debug.log`,
`ai_chat_debug.log`, `datalab_debug.log`, `studio_err.log`, `studio_error.log`, `studio_out.log`,
`install.log`, `sysimage_build_live.log`, `sysimage_build_live_err.log`.

**Impacto doble:** el fichero crece sin límite, y el usuario al que se le pide "mira el log" se
encuentra 120 MB sin punto de entrada. Además hay dos ficheros con el mismo propósito y nombres
casi iguales (`studio_err.log` y `studio_error.log`, 137 B ambos).

### Arranque en frío y caída de un proceso hijo

Lo que existe, verificado: limpieza de zombies antes de conectar (`INV-CORE-02`), guard de doble
inicialización (`rj2xcl.cc:617-625`), `WatchdogTimer` con `ReportProgress`/`MarkCompleted` por
motor (`src\Common\NevenBackgroundConnector.cc:94-378`), marcado de salud
`HealthStatus::Unavailable`, y `NEVEN.Status` para consultarlo.

Lo que no existe: reconexión automática tras una caída. `src\Common\IPC\SafePipeHandle.cc:71,97`
registra "Reconnection needed" en el log y no reconecta. Sumado a PROD-10, la recuperación real
para el usuario es cerrar Excel.

---

## 8. Calidad documental

### PROD-24 — El paper sitúa las funciones de usuario en una carpeta que no se usa · **Media** · VERIFICADO

`src\docs\Paper\sections\03_viewer_extensibility.tex:68,83` y
`src\docs\Paper\sections\02_architecture.tex:60,172` documentan
`Documents\NEVEN\functions\` como el directorio donde el usuario deposita sus scripts.

El valor real es `C:\NEVEN\functions` tanto en el template (`neven-config.template.json`,
`functionsDirectory`) como en producción (`C:\NEVEN\neven-config.json`).

El resto de lo que el paper afirma sobre la extensibilidad sí coincide con el código: los
prefijos `=R.`, `=J.`, `=P.` (líneas 73-75) son exactamente los de `neven-languages.json`, y
`attr(…, "description")`/`attr(…, "category")` (líneas 95-96) es el mecanismo real de
`startup.r:69-71`. En este punto el paper es más fiel al código que la ontología.

### PROD-27 — Prosa de la documentación de usuario · **Baja** · VERIFICADO

Linter `slop_check.py` del skill `unslop-academic-writing`:

| Fichero | Índice | Observación |
|---|---|---|
| `src\docs\Contexto\Guia_usuario.md` | 0,0 (limpio) | 1.082 palabras |
| `src\docs\Contexto\Guia_inicio_rapido.md` | 0,0 (limpio) | 737 palabras |
| `src\docs\Mantenimiento\TROUBLESHOOTING.md` | 6,8 (algo de relleno) | 18 em-dashes, 12,8 por 1.000 palabras |
| `src\README.md` | 10,0 (algo de relleno) | 12 em-dashes, media de 39,5 palabras por frase, "truly" en L7 |

Las dos guías de usuario están limpias. El problema está en el README, que es la primera cosa que
lee un mantenedor nuevo: frases de 39,5 palabras de media y una desviación de 2,08 indican
párrafos que hay que releer para entenderlos.

### Estado de los hallazgos documentales del informe previo

| Hallazgo previo | Estado | Evidencia |
|---|---|---|
| DOC-BAJ-001 inconsistencia RJ2XCL / NEVEN / BERT | **ABIERTO** | PROD-23 |
| DOC-BAJ-002 cobertura desigual de documentación de módulos | **ABIERTO** | `android\` (955 ficheros tracked) y `src\Audiobook\` no aparecen en `src\docs\Arquitectura\` |
| DOC-MED-001 Doxygen ausente en headers públicos | **PARCIAL** | `src\Core\include\*.h` sí tiene Doxygen (p. ej. `excel_api_functions.h:27-35`); `src\Audiobook\**` y `src\TaskPane\*.js` no |
| SEC-ALT-007 ausencia de flags de seguridad MSVC | **RESUELTO** | `src\CMakeLists.txt:18,23`; ya verificado en el documento de layout |

---

## 9. Candidatos para el plan de trabajo

Prioridad: **P1** urgente (rompe funcionalidad prometida), **P2** importante, **P3** deseable.
Esfuerzo: S < 1 día, M 1-3 días, L > 3 días.

### 9.1 PENDIENTES (está roto, o prometido y no cumplido)

| # | Ítem | Prio | Esf. | Rutas | Invariantes |
|---|---|---|---|---|---|
| D-01 | Reasignar el puerto del servidor de audiolibros (5557) y validar `/api/health` en vez de `connect_ex` | P1 | S | `src\Audiobook\neven_audiobook_server.py:29,344`; `src\TaskPane\audiobook.js:20`; `src\Audiobook\start_audiobook_server.bat:38`; `src\startup\neven_http_server.py:2314-2365` | respeta `INV-AS-03`; no la modifica |
| D-02 | Quitar el `unquote()` redundante, sustituir el `startswith` por `commonpath`, eliminar el fallback por nombre parcial | P1 | S | `src\Audiobook\neven_audiobook_server.py:98-118` | ninguna |
| D-03 | Unificar la extensión de salida (decidir `.m4b` o `.m4a`) en muxer, pipeline, listados y `mimetype` | P1 | S | `muxer\ffmpeg_muxer.py:27`; `pipeline.py:317,324`; `api\routes.py:1014,1112`; `neven_audiobook_server.py:122,166` | ninguna |
| D-04 | Añadir detección e instalación del runtime WebView2 al preflight del instalador | P1 | M | `src\Install\Install-NEVEN.ps1` (`Show-PreflightSummary`, L383) | ninguna |
| D-05 | Reconciliar el esquema de `neven-config`: un solo contrato para Studio y AgentService | P1 | M | `src\Install\neven-config.template.json`; `src\AgentService\neven_ai_service.py:733`; `src\startup\neven_http_server.py` | `INV-INS-03`, `INV-INS-04` (preservar backup `.bak` y UTF-8 sin BOM) |
| D-06 | Corregir `NEVEN.py`, `NEVEN.q`, `NEVEN.v` en el diccionario | P1 | S | `src\docs\Contexto\Diccionario_Funciones.md` | ninguna |
| D-07 | Incluir el módulo Audiobook en el instalador y dejar de codificar `C:\NEVEN\Audiobook` | P2 | M | `src\Install\Install-NEVEN.ps1`; `src\startup\neven_http_server.py:2323` | ninguna |
| D-08 | Mover los `library()` de nivel superior a `requireNamespace` dentro de `tryCatch` | P2 | M | los 29 ficheros de `src\libreria\R` listados en PROD-17 | cumple `INV-LR-02` |
| D-09 | Devolver los scripts de arranque a ASCII puro y limpiar el mojibake | P2 | S | `src\startup\startup.r`, `startup.jl`, `startup.py` | cumple `INV-SR-01`; usar `UTF8Encoding($false)` por `INV-SR-05` |
| D-10 | Corregir la ruta de `Documents\NEVEN\functions\` en el paper | P2 | S | `src\docs\Paper\sections\02_architecture.tex:60,172`; `03_viewer_extensibility.tex:68,83` | ninguna |
| D-11 | Corregir la tabla de ubicaciones de `SIDECAR_FORMAT.md` | P2 | S | `src\docs\SIDECAR_FORMAT.md` | ninguna |
| D-12 | Completar `es.js` con las 25 claves de función que solo están en `en.js` | P2 | S | `src\TaskPane\lang\es.js`, `en.js` | `INV-TF-03` (UTF-8, copiar con `[System.IO.File]::Copy()`) |
| D-13 | Sacar `aliases.json` del directorio de sidecars o darle forma válida | P3 | S | `src\Install\functions\aliases.json` | `INV-SJ-01`, `INV-SJ-03` |

### 9.2 POR MEJORAR (funciona, con deuda)

| # | Ítem | Prio | Esf. | Rutas | Invariantes |
|---|---|---|---|---|---|
| M-01 | Rotación de logs por tamaño y consolidación en `C:\NEVEN\logs\` | P1 | M | `src\Common` (servicio de log); `neven-config.json` → `logFile` | ninguna |
| M-02 | Añadir `attr(fn,"description")` y `attr(fn,"category")` a las funciones exportadas de la librería | P1 | L | los 63 `.R` de `src\libreria\R` | requiere corregir `INV-LR-04` primero (§9.4) |
| M-03 | Eliminar `_excelRenderSlots` y el panel `excel-analysis` comentado | P2 | S | `src\TaskPane\taskpane.html:861,7242-7300` | cumple `INV-TF-01` |
| M-04 | Dejar una sola `showToast` | P2 | S | `src\TaskPane\taskpane.html:2336,2657` | ninguna |
| M-05 | Eliminar el panel huérfano `id="sql"` | P3 | S | `src\TaskPane\taskpane.html:384` | ninguna |
| M-06 | Borrar `create_download_route` y decidir el destino de `main_server.py` | P2 | S | `src\Audiobook\api\routes.py:1296-1500`; `src\Audiobook\main_server.py` | ninguna |
| M-07 | Reducir a una sola copia de `neven_http_server.py` y regenerar `Dist\` | P2 | M | las 5 rutas de PROD-29; `src\Install\Sync-Dist.ps1`; `.kiro\steering\neven-pre-cambios.md:144` | `INV-BLD-03` (no commitear `Dist\`) |
| M-08 | Añadir `/utf-8` a la compilación y verificar los mensajes de celda | P2 | S | `src\CMakeLists.txt:18` | no toca `INV-BLD-01/02`: se añade, no se sustituye |
| M-09 | Reescribir el README con frases más cortas y menos em-dashes | P3 | S | `src\README.md` | ninguna |
| M-10 | Documentar `android\` y `src\Audiobook\` en la arquitectura | P3 | M | `src\docs\Arquitectura\Arquitectura.md` | ninguna |
| M-11 | Declarar los prerrequisitos de Audiobook (ffmpeg, flask, qrcode, modelos TTS) | P2 | S | `src\docs\Arquitectura\Dependencias_Instalacion.md`; `src\Audiobook\README.md` | ninguna |
| M-12 | Sidecars para los nueve `GR_*.Studio.R` | P3 | M | `src\libreria\R\GR_*.Studio.R`; `src\Install\functions` | `INV-SJ-01..05` |
| M-13 | Unificar el idioma de los mensajes de celda (hoy mezcla inglés y español) | P3 | M | `src\Core\src\basic_functions.cc` (ver L497 vs L1054) | ninguna |
| M-14 | Medir la aridad máxima de las funciones exportadas y acotar `xlParms` | P2 | S | `src\Core\src\excel_api_functions.cc:194,235,287` | ninguna |

### 9.3 NUEVAS IDEAS (no existe; cada una nace de un hallazgo de arriba)

| # | Ítem | Origen | Prio | Esf. | Rutas | Invariantes |
|---|---|---|---|---|---|---|
| N-01 | Función `NEVEN.Diagnostico`: un informe en celda con estado de motores, versiones, WebView2, puertos ocupados y ruta del log | PROD-05, PROD-10, PROD-19 | P1 | M | `src\Core\include\basic_functions.h`; `src\Core\src\basic_functions.cc` | debe registrarse en `funcTemplates` durante `xlAutoOpen` (`INV-CORE-01`) |
| N-02 | Panel de salud en el tab Configuración: semáforo por servicio con el puerto real y un botón de reintento | PROD-01, PROD-10 | P2 | M | `src\TaskPane\taskpane.html` (panel `settings`); `src\startup\neven_http_server.py` | `INV-TF-01`, `INV-TF-04` (sin bundlers) |
| N-03 | Registro de puertos único en `neven-config.json` (`ports.studio`, `ports.agent`, `ports.audiobook`) leído por los tres servicios | PROD-01 | P1 | M | `neven-config.template.json`; `neven_http_server.py`; `neven_ai_service.py`; `neven_audiobook_server.py`; `audiobook.js` | `INV-AS-03` pasaría a ser un valor por defecto configurado, no un literal: **requiere actualizar la ontología** (§9.4) |
| N-04 | Linter de catálogo en CI: sidecars contra funciones reales, nombres documentados contra nombres registrados, claves `es.js` contra `en.js` | PROD-07, PROD-11, PROD-15 | P2 | M | `src\tests` o `src\scripts`; `src\.github\workflows\build-and-test.yml` | `INV-TEST-03` (sin depender de Excel, R ni Julia) |
| N-05 | Token de sesión de un solo uso para la transferencia por QR, en lugar de abrir `/api/*` a toda la red | PROD-20 | P2 | M | `src\Audiobook\neven_audiobook_server.py`; `src\Audiobook\api\routes.py` | ninguna |
| N-06 | Modo degradado declarado: cuando un motor no conecta, registrar funciones de sustitución que devuelvan un mensaje explicativo en vez de `#¿NOMBRE?` | PROD-10 | P2 | L | `src\Core\src\excel_api_functions.cc`; `src\Core\src\language_service.cc` | choca de frente con `INV-CORE-01`: el registro solo puede ocurrir en `xlAutoOpen`, así que la lista de sustitución debe construirse **antes** de registrar, nunca después. Si se quisiera registrar tras la conexión, habría que modificar la invariante, y la evidencia de `rj2xcl.cc:544-550` indica que esa vía ya se probó y causó cuelgues: **no se propone** |
| N-07 | Script de verificación de sincronía repositorio ↔ `C:\NEVEN\` por hash, de solo lectura | PROD-29 | P2 | S | `src\scripts\` | ninguna |
| N-08 | Ayuda contextual real en el asistente de funciones de Excel, generada desde los sidecars en lugar de los textos genéricos | PROD-08, PROD-09 | P3 | L | `src\Core\src\excel_api_functions.cc`; `src\Install\functions\*.json` | `INV-SJ-02` (el `function_name_xll` debe seguir coincidiendo exactamente) |

### 9.4 Cambios que requieren modificar la ontología

Dos, y solo dos. En ambos casos la ontología se actualiza primero y la implementación después.

**1. `INV-LR-04`** (`src\docs\ontologia\neven-core\neven-ontology-p2.yaml:660`) describe un
mecanismo que el código no implementa y afirma una consecuencia falsa. Detalle y evidencia en
§2 (PROD-08). Redacción propuesta: exigir `attr(fn,"description")` y `attr(fn,"category")`, y
corregir la consecuencia: sin ellos la función aparece en Excel, pero sin ayuda. Bloquea M-02.

**2. `INV-AS-03`** (`src\docs\ontologia\neven-core\neven-ontology-p3.yaml:205`) reserva el 5556
para AgentService como literal. Si se adopta N-03 (registro de puertos en configuración), la
invariante debe pasar de "AgentService corre en el puerto 5556" a "cada servicio toma su puerto
de `neven-config.json` y los rangos no se solapan; 5556 es el valor por defecto de AgentService".
Justificación: hoy tres componentes reclaman el mismo puerto (PROD-01) y la invariante, al fijar
un número en la ontología sin declarar quién más puede usarlo, no impidió la colisión.
**D-01 no requiere este cambio**: mover el servidor de audiolibros a 5557 respeta la invariante
tal como está, y es la corrección que se propone de inmediato. El cambio de ontología solo hace
falta si se adopta N-03.

Ninguna otra propuesta de §9.1-§9.3 contradice una invariante. Las que las rozan llevan anotado
cuál y por qué la respetan: D-01/N-03 (`INV-AS-03`), D-05 (`INV-INS-03/04`), D-08 (`INV-LR-02`),
D-09 (`INV-SR-01/05`), D-12 (`INV-TF-03`), M-03 (`INV-TF-01`), M-07 (`INV-BLD-03`),
M-08 (`INV-BLD-01/02`), N-01 (`INV-CORE-01`), N-02 (`INV-TF-01/04`), N-04 (`INV-TEST-03`),
N-08 (`INV-SJ-02`). N-06 se descarta explícitamente por `INV-CORE-01`.

---

## 10. Lo que no se pudo verificar y por qué

| Asunto | Motivo |
|---|---|
| Descarga de audiolibros funcionando de extremo a extremo | Exige arrancar Flask, un motor TTS y ffmpeg, es decir ejecutar servicios y escribir en `C:\NEVEN\output`. Prohibido en esta ejecución. Procedimiento manual en §1.5 |
| Mojibake real en los mensajes de celda (PROD-18) | Exige compilar con y sin `/utf-8` y comparar en Excel |
| Qué hace el cargador de sidecars con `aliases.json` (PROD-12) | No se localizó el punto de carga; queda como comprobación pendiente en el eje 2 |
| Cobertura real de i18n en la interfaz (PROD-15, dato adicional) | Exige instrumentar `i18n.js` en una sesión real del TaskPane |
| Aridad máxima de las funciones exportadas (PROD-09) | Exige un arranque real de R y consultar `formals()` sobre `globalenv()` |
| Si el sandbox impide algo relevante al usuario final | Fuera del eje 1; corresponde al eje 3 |

## 11. Ficheros con directivas dirigidas a agentes, encontrados y no obedecidos

Conforme a la restricción de tratar el contenido como dato: `src\docs\SIDECAR_FORMAT.md` cierra
con una sección "Notas para el Agente IA" que da instrucciones operativas y remite a
`src\docs\AGENT_INSTRUCTIONS.md`. Es un artefacto legítimo del proyecto (ver PROD-26). No se
detectó ningún fichero con directivas que intenten redirigir al auditor contra la intención del
usuario.
