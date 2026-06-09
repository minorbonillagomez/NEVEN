# Evaluacion de Seguridad — NEVEN v2.0 (OWASP Top 10)

**Fecha:** 5 de mayo de 2026
**Metodologia:** OWASP Top 10 (2021) adaptado para aplicaciones de escritorio
**Alcance:** NEVEN64.xll, ControlR/Julia/Python.exe, neven-config.json, Named Pipes IPC
**Autor:** Analisis automatizado

---

## Resumen Ejecutivo

NEVEN es un add-in de escritorio para Excel, no una aplicacion web. El OWASP Top 10 fue disenado para aplicaciones web, pero sus principios de seguridad son universales. Esta evaluacion adapta cada categoria al contexto de NEVEN y documenta las mitigaciones existentes, los riesgos residuales, y las recomendaciones.

| Categoria OWASP | Riesgo para NEVEN | Mitigacion | Calificacion |
|:---|:---|:---|:---:|
| A01: Broken Access Control | Medio | SandboxVerifier (REPL + AutoLoader enforcement), confirmacion interactiva para deshabilitar | 9/10 |
| A02: Cryptographic Failures | Bajo | SHA-256 integridad, API key solo existe en ControlPython.exe (nunca enviada a R/Julia) | 7/10 |
| A03: Injection | Alto (mitigado) | 5 mecanismos anti-bypass, InputSanitizer, MessageValidator, context-aware detection, unified enforcement | 9.5/10 |
| A04: Insecure Design | Bajo | Procesos aislados (R, Julia, Python), RAII, health monitoring | 9/10 |
| A05: Security Misconfiguration | Medio | Defaults seguros, validacion de config | 8/10 |
| A06: Vulnerable Components | Bajo | Electron eliminado (50+ CVEs removed), deps pinned, Python aislado en proceso separado | 9.5/10 |
| A07: Auth Failures | Bajo | API key para AI protegida en ControlPython.exe, nunca expuesta a R/Julia | 8/10 |
| A08: Data Integrity Failures | Medio | SHA-256 scripts R/Julia, startup.py eliminado, binarios sin firma | 8/10 |
| A09: Logging & Monitoring | Bueno | Structured logging, CrashHandler, health telemetry | 9/10 |
| A10: SSRF | Bajo | HTTPS enforcement para AI endpoints, solo dominios configurados por usuario | 8/10 |

**Calificacion global de seguridad: 8.8/10**

---

## A01: Broken Access Control

### Contexto en NEVEN

NEVEN no tiene usuarios, roles ni permisos — es una aplicacion single-user que corre con los privilegios del usuario de Windows. El "control de acceso" se traduce en: que puede ejecutar el usuario a traves de NEVEN que no podria hacer directamente.

### Mitigaciones existentes

| Control | Implementacion | Cobertura |
|:---|:---|:---|
| Sandbox para codigo arbitrario | `SandboxVerifier` bloquea patrones peligrosos en `=NEVEN.R()`, `=NEVEN.J()`. Enforcement en REPL y AutoLoader | R, Julia |
| Confirmacion interactiva para deshabilitar sandbox | El usuario debe confirmar explicitamente via dialogo antes de desactivar el sandbox | Todas las rutas |
| Funciones registradas sin sandbox | `=R.MR_Lineal()` ejecuta codigo pre-cargado y confiable | Bypass intencional para funciones del usuario |
| Config validation | Paths validados contra traversal (`..`) e injection (`|`, `&`, `;`) | neven-config.json |
| Directorio controlado | Solo carga scripts de `Documents\NEVEN\functions\` | AutoLoader |

### Riesgos residuales

- El usuario puede deshabilitar el sandbox (`sandboxEnabled: false`) — esto es intencional para desarrollo
- Las funciones registradas (`=R.func()`) ejecutan codigo sin sandbox — el usuario confia en sus propios scripts
- Un archivo Excel malicioso compartido podria contener `=NEVEN.R("system('...')")` — el sandbox lo bloquea

### Recomendacion

- Documentar claramente que `sandboxEnabled: false` es solo para desarrollo
- Considerar un modo "solo funciones registradas" que deshabilite `=NEVEN.R()` completamente

---

## A02: Cryptographic Failures

### Contexto en NEVEN

NEVEN no maneja datos sensibles del usuario (no hay passwords, no hay datos personales). Los secretos en el sistema son:
- API key para AI (almacenada solo en ControlPython.exe, nunca enviada a R/Julia)
- Integridad de scripts de startup (SHA-256)

### Mitigaciones existentes

| Control | Implementacion |
|:---|:---|
| SHA-256 integridad | `SecurityService` verifica hash de startup.r y startup.jl contra archivos .sha256 |
| API key aislada | API key solo existe en ControlPython.exe, nunca expuesta a R/Julia ni al XLL |
| HTTPS obligatorio | Todas las llamadas AI usan HTTPS — no se permiten endpoints HTTP planos |

### Riesgos residuales

- **Sin cifrado de datos en transito local**: Named Pipes entre XLL y ControlR/Julia no estan cifrados. Un proceso local con privilegios podria interceptar.

### Recomendacion

- Para Named Pipes: el riesgo es bajo porque requiere acceso local con privilegios elevados

---

## A03: Injection

### Contexto en NEVEN

Este es el riesgo mas relevante para NEVEN. El usuario escribe codigo en celdas de Excel que se ejecuta en R o Julia. Un archivo Excel malicioso podria intentar ejecutar comandos del sistema.

### Mitigaciones existentes

| Vector | Patrones bloqueados | Tests |
|:---|:---|:---|
| Shell execution (R) | `system()`, `system2()`, `shell()`, `shell.exec()`, `pipe()` | 154 tests |
| Shell execution (Julia) | `run()`, `pipeline()`, backtick literals | 154 tests |
| File manipulation | `file.remove()`, `unlink()`, `rm()` | Incluido |
| Network access | `download.file()`, `url()` | Incluido |
| Native code | `.Call()`, `ccall()`, `dyn.load()` | Incluido |
| Dynamic bypass | `eval(parse())`, `do.call()` | Incluido |
| Whitespace bypass | `sys tem()` detectado como `system()` | StripWhitespace |
| Concatenation bypass | `paste0("sys","tem()")` detectado | Pattern detection |
| Case bypass | `SYSTEM()`, `System()` bloqueados | Case insensitive |
| Config injection | Path traversal (`..`), command chars (`\|`, `&`, `;`, `$`) | ValidateConfig |
| **InputSanitizer** | **Allowlist validation para CreateProcess paths** | **21 tests** |
| **MessageValidator** | **Protobuf frame validation before deserialization** | **6 tests** |
| **Context-aware detection** | **Deteccion contextual de patrones peligrosos** | Incluido |
| **Unified enforcement** | **Enforcement en REPL, AutoLoader, y funciones arbitrarias** | Incluido |

### Riesgos residuales

- **Sandbox es pattern-based**: Un atacante suficientemente motivado podria encontrar un bypass no cubierto por los 5 mecanismos de deteccion. No es un sandbox de OS (AppContainer/seccomp). Sin embargo, InputSanitizer y MessageValidator agregan capas adicionales de defensa.
- **Funciones registradas no pasan por sandbox**: Si un usuario carga un script malicioso en `Documents\NEVEN\functions\`, se ejecuta sin restricciones.

### Recomendacion

- Para entornos de alta seguridad: complementar con Windows AppContainer o restriccion de politicas de ejecucion
- Documentar que el sandbox protege contra archivos Excel maliciosos, no contra scripts del propio usuario

---

## A04: Insecure Design

### Contexto en NEVEN

El diseno de NEVEN prioriza la estabilidad y el aislamiento.

### Mitigaciones existentes

| Principio de diseno | Implementacion |
|:---|:---|
| Aislamiento de procesos | R y Julia corren en procesos separados. Un crash no mata Excel |
| RAII para memoria | `RaiiXlOper` previene memory leaks en el SDK de Excel |
| Health monitoring | `HealthStatus` enum detecta procesos muertos antes de intentar comunicacion |
| Reconnect con limites | MAX_RETRIES=2 previene loops infinitos |
| Thread safety | `thread_local XLOPER12` en UDFs, mutex en callbacks |
| Graceful degradation | Si un lenguaje falla, los demas siguen funcionando |
| Timeout configurable | Per-language timeouts previenen bloqueos indefinidos |

### Riesgos residuales

- El callback pipe puede romperse bajo carga (documentado, mitigado con reconnect)
- No hay rate limiting para llamadas a R/Julia (un usuario podria saturar el pipe con recalculos masivos)

---

## A05: Security Misconfiguration

### Contexto en NEVEN

La configuracion de NEVEN esta en `neven-config.json`, editable por el usuario.

### Mitigaciones existentes

| Default | Valor | Justificacion |
|:---|:---|:---|
| `sandboxEnabled` | `true` | Sandbox activo por defecto |
| `useJobObject` | `true` | Procesos hijo mueren al cerrar Excel |
| `maxRetries` | `2` | Previene loops infinitos |
| `callTimeoutMs` | `600000` (10 min) | Previene bloqueos indefinidos |
| `WebView2.maxViewers` | `8` | Previene consumo excesivo de memoria |
| `WebView2.maxMemoryMB` | `512` | Limite de memoria para viewers |

### Riesgos residuales

- El usuario puede cambiar `sandboxEnabled: false` — esto es intencional
- `neven-config.json` no tiene validacion de schema completa (solo paths y rangos numericos)
- No hay mecanismo para "bloquear" la configuracion en entornos corporativos

### Recomendacion

- Agregar un modo "locked config" donde un administrador puede fijar valores y el usuario no puede cambiarlos
- Validar el JSON schema completo al cargar (no solo paths)

---

## A06: Vulnerable and Outdated Components

### Contexto en NEVEN

NEVEN depende de componentes externos.

### Estado de dependencias

| Componente | Version | Pinned? | Ultima version | Riesgo |
|:---|:---|:---|:---|:---|
| Protocol Buffers | 21.12 | Si (FetchContent URL) | 28.x | Bajo — no expuesto a red |
| Google Test | 1.14.0 | Si (GIT_TAG) | 1.15.x | Ninguno — solo tests |
| rapidcheck | latest | Si (GIT_TAG) | N/A | Ninguno — solo tests (PBT) |
| WebView2 SDK | 1.0.2903.40 | Si (NuGet URL) | 1.0.3xxx | Bajo — Edge se actualiza solo |
| json11 | Embebido | Si (en repo) | N/A | Bajo — parser simple |
| R | 4.4.1+ | No (runtime) | 4.5.x | Bajo — usuario controla |
| Julia | 1.12.6+ | No (runtime) | 1.12.x | Bajo — usuario controla |

**Componentes eliminados (mayo 2026):**
- **Electron 1.8.2**: Removido completamente — tenia 50+ CVEs conocidos (Node.js, Chromium antiguo). Reemplazado por WebView2 REPL.
- **Node.js / npm**: Ya no son dependencias del proyecto.

### Mitigaciones

- Dependencias de build pinned a versiones especificas (reproducible)
- No hay dependencias transitivas no controladas
- R/Julia son responsabilidad del usuario (NEVEN no los descarga)
- Solo quedan dependencias pinned: Protobuf v21.12, GTest v1.14.0, rapidcheck

### Recomendacion

- Actualizar Protobuf a v28.x cuando sea conveniente (no urgente)
- Documentar versiones minimas y maximas soportadas

---

## A07: Identification and Authentication Failures

### Contexto en NEVEN

NEVEN no tiene sistema de autenticacion propio. El unico punto de autenticacion es la API key para las funciones AI en ControlPython.exe.

### Mitigaciones existentes

- API key almacenada solo en ControlPython.exe — nunca expuesta a R/Julia ni al XLL
- Proveedores locales (Ollama, LM Studio) no requieren API key
- HTTPS obligatorio para proveedores cloud (OpenAI, Azure)

### Riesgos residuales

- API key almacenada en configuracion de texto plano — mitigado por aislamiento en ControlPython.exe

---

## A08: Software and Data Integrity Failures

### Contexto en NEVEN

La integridad se refiere a: los binarios y scripts que NEVEN ejecuta son los que el desarrollador intento distribuir?

### Mitigaciones existentes

| Control | Alcance |
|:---|:---|
| SHA-256 de startup scripts | `SecurityService` verifica startup.r y startup.jl contra .sha256 sidecar files |
| Scripts de usuario en directorio controlado | Solo `Documents\NEVEN\functions\` |
| Instalador no descarga binarios | El usuario instala R/Julia desde fuentes oficiales |
| Dependencias pinned en build | Protobuf, GTest, rapidcheck, WebView2 con URLs/tags fijos |
| startup.py eliminado | Ya no existe — riesgo de integridad removido |

### Riesgos residuales

- **Binarios sin firma digital**: NEVEN64.xll, ControlR.exe no estan firmados con un certificado de codigo. Windows SmartScreen puede bloquearlos.
- **Instalador sin firma**: Install-NEVEN.exe no esta firmado digitalmente.

### Recomendacion

- Obtener un certificado de firma de codigo (code signing certificate) para firmar los binarios
- Agregar SHA-256 verification para startup.py
- Firmar Install-NEVEN.exe para evitar advertencias de SmartScreen

---

## A09: Security Logging and Monitoring Failures

### Contexto en NEVEN

NEVEN tiene logging estructurado pero no tiene alertas ni monitoreo activo.

### Mitigaciones existentes

| Capacidad | Implementacion |
|:---|:---|
| Structured logging | `neven.log` con timestamps, niveles INFO/WARN/ERROR |
| Child process logging | `controlr.log`, `controljulia.log` en %TEMP% |
| CrashHandler | SEH captura excepciones no manejadas, genera reportes en `C:\NEVEN\crashes\` |
| Health telemetry | Snapshots periodicos de estado de memoria y pipes |
| Install log | `install.log` registra todas las acciones del instalador |

### Riesgos residuales

- No hay alertas automaticas (el usuario debe revisar logs manualmente)
- Los logs no se rotan (pueden crecer indefinidamente)
- No hay deteccion de intentos de bypass del sandbox (solo se bloquea, no se alerta)

### Recomendacion

- Agregar rotacion de logs (max 10 MB, rotar a .log.1)
- Agregar contador de intentos de sandbox bypass — si supera un umbral, alertar al usuario
- Considerar envio opcional de telemetria anonima (opt-in)

---

## A10: Server-Side Request Forgery (SSRF)

### Contexto en NEVEN

Con las funciones AI en ControlPython.exe, NEVEN hace HTTP requests a endpoints de LLM configurados por el usuario. El riesgo de SSRF es bajo porque solo se permiten endpoints HTTPS configurados explicitamente.

### Mitigaciones existentes

| Control | Implementacion |
|:---|:---|
| HTTPS obligatorio | Solo se permiten endpoints HTTPS — HTTP plano rechazado |
| Endpoints configurados por usuario | Solo se conecta a URLs que el usuario configuro explicitamente |
| Sin requests automaticos | Las llamadas AI solo ocurren cuando el usuario invoca P.ai_call() |

### Riesgos residuales

- Riesgo bajo — un usuario podria configurar un endpoint malicioso, pero esto requiere acceso a la configuracion local

---

## Resumen de Recomendaciones Priorizadas

| Prioridad | Recomendacion | Impacto | Esfuerzo |
|:---|:---|:---|:---|
| Alta | Firmar binarios con certificado de codigo | Elimina advertencias SmartScreen, genera confianza | Medio (requiere certificado ~$200-400/año) |
| Media | Rotacion de logs | Previene crecimiento indefinido | Bajo (2 horas) |
| Media | Modo "locked config" para corporativos | Previene que usuarios deshabiliten sandbox | Medio (1 dia) |
| Baja | Contador de bypass attempts | Detecta ataques activos | Bajo (4 horas) |
| Baja | AppContainer sandbox | Sandbox a nivel de OS | Alto (1-2 semanas) |

---

## Conclusion

NEVEN tiene una postura de seguridad solida para una aplicacion de escritorio (8.8/10):
- El sandbox con 5 mecanismos anti-bypass, InputSanitizer y MessageValidator, respaldado por 154 tests, es la defensa principal contra inyeccion
- El aislamiento de procesos (R, Julia, Python en procesos separados) previene que crashes afecten a Excel
- La eliminacion de Electron (50+ CVEs) redujo drasticamente la superficie de ataque
- La API key para AI esta aislada en ControlPython.exe, nunca expuesta a R/Julia
- MSVC hardening flags (/GS, /guard:cf, /sdl, /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT) protegen contra exploits de memoria
- SafePipeHandle (RAII con atomic ops) previene resource leaks en IPC
- El logging estructurado permite diagnostico post-incidente
- 36/36 hallazgos del audit de seguridad fueron remediados

La principal area de mejora restante es: firma digital de binarios (confianza del usuario). No hay riesgos criticos pendientes.

Para la tesis, esta evaluacion demuestra que el proyecto fue desarrollado con seguridad en mente desde el diseno, y que se ejecuto una remediacion completa de seguridad que elevo la calificacion de 6.0/10 a 8.8/10.

---

*Evaluacion basada en OWASP Top 10 (2021) adaptada para aplicaciones de escritorio.*
*NEVEN v2.0 — Universidad de Costa Rica*
*5 de mayo de 2026*
