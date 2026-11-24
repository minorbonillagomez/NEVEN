# NEVEN Security Model

Este documento describe el modelo de seguridad de NEVEN, los riesgos conocidos y las mejores practicas para usuarios.

## Que hace NEVEN

NEVEN es un add-in de Excel que permite ejecutar codigo R, Julia y Python directamente desde celdas de Excel. Las funciones principales son:

- `=NEVEN.r("codigo R")` — Ejecuta codigo R
- `=NEVEN.j("codigo Julia")` — Ejecuta codigo Julia  
- `=NEVEN.p("codigo Python")` — Ejecuta codigo Python
- `=R.funcion()`, `=J.funcion()` — Funciones registradas

**Implicacion de seguridad:** Por diseno, NEVEN ejecuta codigo arbitrario en el sistema del usuario.

---

## Modelo de Amenazas

### Amenazas Mitigadas

| Amenaza | Mitigacion | Componente |
|:--------|:-----------|:-----------|
| Inyeccion de comandos OS | Blocklist de funciones peligrosas | SandboxVerifier |
| Path traversal | Validacion de rutas | InputSanitizer, ValidateConfig |
| Buffer overflow en IPC | Validacion de frames | MessageValidator |
| Race conditions | Mutex y RAII | SafePipeHandle |
| Ejecucion de codigo nativo | Bloqueo de ccall, system(), os.system() | SandboxVerifier |

### Amenazas Parcialmente Mitigadas

| Amenaza | Mitigacion | Limitacion |
|:--------|:-----------|:-----------|
| Codigo malicioso en Excel | SandboxVerifier bloquea ~90 patrones | Blocklist no es exhaustiva |
| Bypass por ofuscacion | 5 mecanismos anti-bypass | Atacante sofisticado podria evadir |
| Scripts maliciosos de usuario | Hot-reload valida sintaxis | No valida semantica |

### Amenazas NO Mitigadas (Riesgo Aceptado)

| Amenaza | Razon | Recomendacion |
|:--------|:------|:--------------|
| Archivos Excel maliciosos | Inherente al proposito de NEVEN | Solo abrir archivos de fuentes confiables |
| Vulnerabilidades en R/Julia/Python | Dependencias externas | Mantener motores actualizados |
| Codigo malicioso dentro de funciones permitidas | Imposible distinguir intent | Revisar codigo antes de ejecutar |

---

## Componentes de Seguridad

### 1. SandboxVerifier

Bloquea funciones peligrosas en R, Julia y Python:

**R (~30 patrones bloqueados):**
- `system()`, `shell()`, `shell.exec()`
- `file.remove()`, `unlink()`, `file.rename()`
- `download.file()`, `url()`, `socketConnection()`
- `eval(parse())`, `do.call()`, `get()`, `.Call()`
- `Sys.setenv()`, `setwd()`, `options()`

**Julia (~25 patrones bloqueados):**
- `ccall`, `@ccall`, `cglobal`
- `unsafe_load`, `unsafe_store!`, `unsafe_wrap`
- `run()`, `pipeline()`, backticks
- `include()`, `eval()`, `Meta.parse()`
- `cd()`, `rm()`, `mv()`

**Python (~30 patrones bloqueados):**
- `os.system()`, `subprocess.*`, `os.popen()`
- `eval()`, `exec()`, `compile()`
- `open()`, `__import__()`, `importlib`
- `shutil.*`, `pathlib`
- `getattr` (bypass detection)

### 2. InputSanitizer

Valida rutas de archivos antes de pasarlas a `CreateProcess`:
- Allowlist de caracteres permitidos
- Bloquea `..`, `|`, `&`, `;`, backticks, `<`, `>`
- Previene inyeccion de comandos via nombres de archivo

### 3. MessageValidator

Valida mensajes Protobuf entre el XLL y los procesos hijo:
- Verifica tamanio de frames antes de deserializar
- Previene buffer overflow por mensajes malformados

### 4. SafePipeHandle

RAII wrapper para Named Pipes:
- CRITICAL_SECTION para operaciones atomicas
- Previene condiciones de carrera (TOCTOU)
- Limpia recursos automaticamente

### 5. MSVC Security Flags

El codigo C++ se compila con:
- `/GS` — Buffer security check
- `/guard:cf` — Control Flow Guard
- `/sdl` — Security Development Lifecycle checks
- `/DYNAMICBASE` — ASLR
- `/NXCOMPAT` — DEP
- `/CETCOMPAT` — Control-flow Enforcement Technology

### 6. Permisos del directorio de instalacion

Un directorio creado bajo `C:\` hereda de la raiz del disco el ACE
`NT AUTHORITY\Authenticated Users:(OI)(CI)(IO)(M)`. Sin endurecer, cualquier
usuario autenticado de la maquina puede sustituir un fichero que NEVEN ejecuta
por su cuenta (`startup\*.py`, `functions\*.R`, `TaskPane\*`, los ejecutables de
los motores) y esperar a que NEVEN lo ejecute. `Set-InstallPermissions.ps1`
declara dos clases de ruta y las aplica con SIDs conocidos, porque los nombres de
grupo estan localizados:

| Clase | Que cubre | Permisos de los usuarios autenticados |
|-------|-----------|----------------------------------------|
| Codigo | La raiz y, por herencia, lo que NEVEN ejecuta o carga | Leer y ejecutar. Crear subdirectorios en la raiz, no ficheros |
| Datos | `functions\`, `prompts\`, `logs\`, `temp\`, `graphics\`, `notebooks\`, `data\`, `workspace\`, `webview2-data\`, `crashes\`, `user-charts\`, `bridge\` | Modificar: ahi escriben el servidor HTTP y el FileWatchService sin elevar |
| Datos | `neven-config.json`, `neven-config.json.bak`, `install.log`, `packages-status-cache.json`, `neven.log` | Leer, ejecutar y escribir; sin borrar |

La clase datos conserva la escritura, pero no la crea. El destino lo elige el
usuario, y una carpeta protegida como `C:\Program Files\NEVEN` no concede
escritura a ningun usuario sin privilegios: conceder ahi la tabla abriria el mismo
vector que el script cierra. Por eso el script mide el destino antes de tocarlo,
por ruta y contando solo los grupos a los que pertenece cualquier usuario de la
maquina, y emite cada concesion solo si todos sus permisos ya estaban ahi. Donde
no estaban, la ruta queda en lectura y ejecucion, el informe lo dice y avisa de lo
que implica: guardar funciones o prompts y reconfigurar los motores en ese destino
exigira una consola elevada.

Los dos instaladores llaman al script en dos puntos: un sondeo antes de copiar el
primer fichero y la aplicacion cuando ya no queda nada por escribir. Cada
operacion comprueba su codigo de salida, y un endurecimiento que no se pudo
aplicar se dice con su motivo y queda en `install.log`: solo se continua con una
aceptacion explicita del usuario, y en modo desatendido se aborta.

Para medir la DACL de una instalacion cuando quiera:

```powershell
powershell -NoProfile -File C:\NEVEN\Set-InstallPermissions.ps1 -InstallDir C:\NEVEN -AuditOnly
# exit 0 sin hallazgos, 1 con hallazgos de ACL, 2 si alguna operacion fallo
```

Exposicion residual, que el propio script imprime a partir de lo que mide: en una
instalacion bajo `C:\`, `functions\` y `prompts\` son escribibles y NEVEN carga
`functions\*.R` en R dentro de Excel, y `neven-config.json` es escribible y es el
fichero por el que se puede apagar el sandbox; `certs\localhost.key` deja de ser
escribible pero sigue siendo legible; y desinstalar sin elevacion ya no borra los
ficheros endurecidos.

---

## Mejores Practicas para Usuarios

### DO (Hacer)

1. **Solo abrir archivos Excel de fuentes confiables**
   - Tratar archivos con formulas NEVEN como ejecutables
   - Verificar el origen antes de habilitar macros/add-ins

2. **Mantener los motores actualizados**
   - R, Julia y Python reciben parches de seguridad
   - Actualizar periodicamente

3. **Revisar codigo antes de ejecutar**
   - Especialmente codigo copiado de internet
   - Verificar que no contenga funciones peligrosas

4. **Usar funciones registradas cuando sea posible**
   - `=R.MR_Lineal()` es mas seguro que `=NEVEN.r("lm(...)")`
   - Las funciones registradas estan pre-validadas

### DON'T (No hacer)

1. **No abrir archivos Excel de correos sospechosos**
   - Phishing con archivos Excel es comun
   - Las formulas NEVEN se ejecutan al recalcular

2. **No ejecutar codigo sin entenderlo**
   - `=NEVEN.r("...")` ejecuta lo que sea que este entre comillas
   - El sandbox no es perfecto

3. **No deshabilitar el sandbox**
   - `sandboxEnabled: false` en config elimina toda proteccion
   - Solo para desarrollo/debugging

4. **No compartir archivos con credenciales hardcodeadas**
   - `=NEVEN.r("dbConnect(password='...')")`  
   - Usar variables de entorno o archivos de config externos

---

## Reportar Vulnerabilidades

Si encuentras una vulnerabilidad de seguridad en NEVEN:

1. **No publicar en issues publicos**
2. Contactar a: minor.bonilla@ucr.ac.cr
3. Incluir:
   - Descripcion del problema
   - Pasos para reproducir
   - Impacto potencial
   - Sugerencia de fix (opcional)

Tiempo de respuesta esperado: 48-72 horas.

---

## Auditoria y Tests

NEVEN tiene 357 tests automatizados, incluyendo:

| Categoria | Tests |
|:----------|------:|
| Sandbox (R + Julia + Python) | 154 |
| Property-based (rapidcheck) | 24 |
| InputSanitizer | 21 |
| IPC/Protobuf | 6 |
| Pipe Lifecycle | 8 |

La auditoria de mayo 2026 identifico 36 hallazgos de seguridad. **Todos fueron remediados.**

---

## Historial de Seguridad

| Fecha | Evento |
|:------|:-------|
| Abril 2026 | Auditoria inicial: 36 hallazgos identificados |
| Mayo 2026 | Remediacion completa: 36/36 cerrados |
| Agosto 2026 | Revision de riesgos residuales |

---

*Documento actualizado: 19 de agosto de 2026*
*NEVEN v2.3 — Universidad de Costa Rica*
