# NEVEN Enterprise — Requisitos

## Introducción

NEVEN comenzó como un add-in XLL de C++17 para Windows que embebe R y Julia directamente en Excel. Su propuesta de valor central — funciones de hoja de cálculo que ejecutan código estadístico con recálculo automático — está probada y funcional.

Esta especificación define la evolución de NEVEN hacia un producto corporativo multi-plataforma. El objetivo no es reemplazar lo que funciona, sino construir sobre esa base para eliminar las barreras de adopción en entornos empresariales: dependencia de Windows, instalación manual por máquina, ausencia de gestión centralizada, y falta de controles de seguridad empresarial.

La arquitectura resultante mantiene el XLL de Windows como experiencia premium local, y agrega una capa cloud que habilita macOS, Excel Web, y despliegue corporativo sin fricción.

---

## Requisitos

### R1 — Soporte multi-plataforma

**R1.1** El sistema debe proveer funcionalidad de análisis estadístico (equivalente a `=NEVEN.R()` y `=NEVEN.J()`) en Excel para macOS sin requerir instalación local de R o Julia en la máquina del usuario.

**R1.2** El sistema debe proveer un task pane funcional (DataLab, Run Script, Agente IA) en Excel para macOS mediante un Office Add-in basado en Office.js.

**R1.3** El sistema debe funcionar en Excel Web (browser) con las mismas capacidades que el task pane de escritorio, con la excepción del recálculo automático nativo.

**R1.4** En Windows, el XLL existente debe continuar funcionando sin cambios para usuarios que lo tengan instalado. La experiencia XLL es la experiencia premium y no se degrada.

---

### R2 — Despliegue corporativo centralizado

**R2.1** Un administrador de IT debe poder desplegar NEVEN a todos los usuarios de una organización Microsoft 365 desde el Admin Center, sin intervención en cada máquina individual.

**R2.2** El despliegue debe funcionar mediante un manifest de Office Add-in (XML o Unified Manifest) que apunte al servidor NEVEN Enterprise de la organización.

**R2.3** El sistema debe soportar despliegue on-premise (servidor en la infraestructura del cliente) como alternativa al cloud público, para organizaciones con políticas de datos restrictivas.

**R2.4** Las actualizaciones de NEVEN deben propagarse automáticamente a todos los usuarios al actualizar el servidor, sin redistribuir el manifest ni intervenir en las máquinas.

---

### R3 — Motor de cómputo en servidor

**R3.1** El servidor debe exponer una API HTTP(S) que acepte código R, Julia y Python, lo ejecute en un entorno aislado por sesión, y retorne resultados en el formato de slots de NEVEN (compatible con el sistema actual).

**R3.2** Cada sesión de usuario debe tener su propio proceso R y Python aislado. Las variables definidas en una sesión no deben ser visibles en otras sesiones.

**R3.3** El servidor debe soportar al menos 20 sesiones concurrentes activas sin degradación de latencia por encima de 2 segundos para operaciones estándar (regresión OLS sobre 10,000 filas).

**R3.4** El servidor debe proveer el mismo catálogo de funciones que el XLL local: todas las funciones de `libreria/R/` deben estar disponibles en el entorno de servidor sin modificación.

**R3.5** Julia debe estar disponible en el servidor con sysimage precompilada para eliminar el cold start. La sysimage se compila una vez al iniciar el servidor y se comparte entre sesiones de solo lectura.

**R3.6** El servidor debe soportar operaciones de hasta 10 minutos de duración para análisis complejos (VAR, GARCH, modelos de datos panel grandes), con streaming de progreso al cliente.

---

### R4 — Custom Functions para recálculo automático cross-plataforma

**R4.1** El sistema debe registrar funciones personalizadas de Excel mediante la Custom Functions API de Office.js, de modo que `=NEVEN.R()` y `=NEVEN.J()` aparezcan en el IntelliSense de Excel en macOS y Windows.

**R4.2** Las Custom Functions deben recalcular automáticamente cuando cambian las celdas de las que dependen, equivalente al comportamiento del XLL en Windows.

**R4.3** La latencia de una Custom Function en modo servidor no debe superar 3 segundos para operaciones estándar en condiciones normales de red.

**R4.4** En Windows con XLL instalado, el sistema debe preferir la ejecución local (XLL) sobre la remota (Custom Function) para mantener la latencia de 200ms del modo nativo.

**R4.5** Las Custom Functions deben manejar timeouts y retornar `#TIMEOUT!` en lugar de bloquear la hoja cuando el servidor no responde en el tiempo configurado.

---

### R5 — Autenticación y autorización

**R5.1** El sistema debe soportar autenticación mediante Microsoft Entra ID (Azure AD) con SSO, de modo que el usuario no necesite credenciales separadas para NEVEN si ya está autenticado en Microsoft 365.

**R5.2** Un administrador debe poder definir roles: `viewer` (solo puede ejecutar funciones predefinidas), `analyst` (puede ejecutar código arbitrario), y `admin` (puede gestionar usuarios y configuración).

**R5.3** El rol `viewer` no debe tener acceso a `Run Script` ni a la ejecución de código arbitrario. Solo puede usar las funciones del catálogo de DataLab.

**R5.4** El sistema debe registrar en un log de auditoría todas las ejecuciones de código con: usuario, timestamp, tipo de operación, función ejecutada, y resultado (éxito/error). El log debe ser exportable.

**R5.5** Las API keys de LLM (Azure OpenAI, OpenRouter, etc.) deben estar almacenadas en el servidor y nunca exponerse al cliente. El cliente no debe tener acceso directo al proveedor LLM.

---

### R6 — Seguridad de ejecución

**R6.1** La ejecución de código en el servidor debe ocurrir en entornos aislados (contenedores o procesos con restricciones de sistema de archivos y red) para prevenir que un usuario acceda a datos de otro.

**R6.2** El sistema debe mantener la sandbox de R existente (`sandboxEnabled: true` en `neven-config.json`) en modo servidor, con las mismas restricciones que el modo local.

**R6.3** El acceso a paquetes R y Julia debe ser controlado por el administrador. La instalación de nuevos paquetes debe requerir aprobación explícita del rol `admin`.

**R6.4** Todas las comunicaciones entre el cliente (add-in) y el servidor deben ser HTTPS con TLS 1.2 o superior.

**R6.5** El servidor debe implementar rate limiting por usuario: máximo 60 ejecuciones por minuto para el rol `analyst`, 10 para el rol `viewer`.

---

### R7 — Gestión de datos y privacidad

**R7.1** Los datos del usuario (datasets cargados, resultados de análisis) deben almacenarse en el servidor solo durante la sesión activa. Al cerrar la sesión, los datos deben eliminarse del servidor.

**R7.2** El sistema debe soportar la opción de modo híbrido: los datos permanecen en la máquina del usuario (procesados por el servidor local si está disponible) y solo los resultados se envían al servidor cloud.

**R7.3** El formato `.buklo` debe evolucionar para soportar almacenamiento en la nube (Azure Blob Storage, S3) como alternativa al filesystem local, con cifrado en reposo.

**R7.4** El sistema debe ser compatible con GDPR: el administrador puede solicitar la eliminación completa de todos los datos de un usuario, y el sistema debe ejecutarla en menos de 72 horas.

---

### R8 — Agente IA como servicio independiente

**R8.1** El Agente IA debe ser desplegable como un microservicio independiente del servidor de cómputo, con su propia URL y ciclo de despliegue.

**R8.2** El Agente IA debe funcionar como un Office Add-in web autónomo — sin requerir la instalación local de NEVEN — que se integra en el task pane de Excel mediante Office.js.

**R8.3** El Agente IA debe poder leer el rango seleccionado por el usuario directamente mediante `Excel.run()` de Office.js, sin necesidad de la función `=NEVEN.IA.Contexto()`.

**R8.4** El Agente IA debe mantener el historial de conversación asociado a una sesión identificada por `session_id`, permitiendo que múltiples usuarios compartan el contexto de un análisis.

**R8.5** El Agente IA debe soportar los mismos proveedores LLM que el sistema actual: Azure OpenAI, OpenRouter, LM Studio local, Ollama local.

**R8.6** Cuando el servidor local de NEVEN esté disponible (`localhost:5555`), el Agente IA debe preferir conectarse localmente para reducir latencia y mantener privacidad de datos.

---

### R9 — Observabilidad y operaciones

**R9.1** El servidor debe exponer métricas en formato Prometheus: sesiones activas, latencia por operación, tasa de errores, uso de memoria por motor (R, Julia, Python).

**R9.2** El sistema debe proveer un panel de administración web con: lista de usuarios activos, uso por usuario, estado de los motores, y log de auditoría filtrable.

**R9.3** El servidor debe implementar health checks en `/health` y `/ready` para integración con orquestadores (Kubernetes, Docker Compose con health checks).

**R9.4** Los errores de ejecución deben retornar mensajes descriptivos al usuario sin exponer stack traces internos del servidor.

---

### R10 — Compatibilidad y migración

**R10.1** Las funciones XLL existentes (`=NEVEN.R()`, `=NEVEN.J()`, `=NEVEN.r()`, etc.) deben continuar funcionando sin cambios en Windows con XLL instalado.

**R10.2** Los archivos `.buklo` existentes deben ser cargables en el sistema Enterprise sin migración manual.

**R10.3** La configuración `neven-config.json` existente debe ser compatible con el sistema Enterprise, con nuevas secciones opcionales (`Enterprise`, `Auth`, `Server`) que no afectan el comportamiento local si están ausentes.

**R10.4** El catálogo de funciones de DataLab (sidecars JSON + funciones `.Studio.R`) debe ser portable al servidor sin modificación.
