# Evaluacion Comercial — Proyecto NEVEN

**Fecha:** 9 de mayo de 2026
**Proposito:** Analisis honesto del potencial comercial de NEVEN como producto de software.
**Autor del analisis:** Kiro (IA)

---

## 1. Veredicto Directo

NEVEN tiene un nucleo tecnico solido y resuelve un problema real. Pero **no esta listo para venderse hoy**. La distancia entre "funciona en mi maquina" y "producto comercial" es significativa, y hay brechas concretas que cerrar.

El potencial existe. El mercado existe. Pero requiere trabajo enfocado en areas que no son las que un ingeniero disfruta: instalacion, soporte, onboarding y modelo de negocio.

---

## 2. El Mercado

### Quien necesita esto

| Segmento | Dolor | Disposicion a pagar |
|:---|:---|:---|
| **Profesores de econometria/estadistica** | Ensenar R sin que los alumnos aprendan R | Media — presupuestos universitarios limitados |
| **Analistas financieros** | Modelos avanzados sin salir de Excel | Alta — Excel es su herramienta principal |
| **Departamentos de actuaria** | Regresion, series de tiempo, panel data en Excel | Alta — regulados, necesitan reproducibilidad |
| **Consultores de datos** | Entregar resultados en Excel al cliente | Media — valoran productividad |
| **Investigadores academicos** | Reproducibilidad con Quarto + Excel | Baja — prefieren herramientas gratuitas |

### Competencia directa

| Producto | Precio | Fortaleza | Debilidad vs NEVEN |
|:---|:---|:---|:---|
| **PyXLL** | $495/año | Python en Excel, maduro, soporte comercial | Solo Python, sin R/Julia, sin visualizacion embebida |
| **BERT** (original) | Gratis | Base de NEVEN, comunidad existente | Abandonado, R 3.4, sin Python, sin seguridad, sin tests |
| **xlwings** | $490/año (PRO) | Python en Excel, buena documentacion | Solo Python, sin R/Julia, sin sandbox, sin notebooks |
| **RExcel** | Gratis | R en Excel | Obsoleto, sin Julia/Python, sin mantenimiento activo |
| **Python in Excel** (Microsoft) | Incluido en 365 | Nativo, sin instalacion | Solo Python, ejecucion en la nube, sin R/Julia, sin control local |

### Posicionamiento

NEVEN no compite con Python in Excel de Microsoft (nube, masivo, gratuito). Compite en el nicho de **analisis estadistico avanzado local** donde R y Julia son superiores a Python para econometria, matematica aplicada y visualizacion interactiva.

La propuesta de valor unica es: **R + Julia + Python + visualizacion interactiva + notebooks + reportes, todo desde Excel, todo local, con seguridad**.

Ningun competidor ofrece los tres lenguajes juntos con visualizacion interactiva embebida.

---

## 3. Fortalezas Comerciales

### Lo que ya funciona y tiene valor

1. **Problema real resuelto.** "Quiero usar R en Excel sin aprender R" es un dolor genuino. Las ~90 funciones R4XCL con el patron `TipoOutput` lo resuelven elegantemente.

2. **Diferenciacion clara.** Nadie mas ofrece R + Julia + Python + Plotly + D3 + Leaflet + Pluto + Quarto en Excel. Es el unico add-in que integra R, Julia y Python con visualizacion interactiva embebida.

3. **Calidad tecnica.** 357 tests, sandbox de seguridad con 5 mecanismos anti-bypass + InputSanitizer + MessageValidator, RAII, Protocol Buffers. No es un script pegado con cinta — es ingenieria real.

4. **Visualizacion interactiva.** `=NEVEN.v(R.Dashboard(datos, 1))` genera un dashboard con 6 tabs interactivos. Esto es un demo que vende solo.

5. **Nombre memorable.** NEVEN es corto, pronunciable, palindromo, con significado. Mejor que cualquier acronimo tecnico.

6. **AI integrada.** `=P.ai_call(datos, "interpretar_regresion")` envia los resultados a un LLM y retorna una interpretacion en lenguaje natural. Ningun competidor de Excel ofrece interpretacion AI integrada con prompts editables por el usuario. Soporta OpenAI, Ollama (local/gratis), LM Studio, y cualquier endpoint compatible. Verificado funcionando con nvidia/nemotron-3-nano-4b (modelo local de 4B parametros). Los prompts son archivos `.txt` que el usuario puede editar, crear o compartir — no requiere programacion.

7. **Privacidad total con modelos locales.** A diferencia de Python in Excel de Microsoft (que ejecuta en la nube), NEVEN con Ollama o LM Studio procesa datos localmente. Los datos nunca salen de la maquina del usuario. Esto es critico para empresas con datos sensibles (financieros, medicos, legales).

8. **Consola REPL interactiva.** `=NEVEN.Console()` abre una consola embebida con tabs para R, Julia y Python. Dark theme profesional, historial de 500 comandos, multi-línea con Shift+Enter, gráficos inline. Implementada como HTML autocontenido en WebView2 (0 dependencias extra, sin Electron). Esto es un demo que impresiona en presentaciones y facilita la exploración interactiva de datos.

9. **Diccionario de funciones integrado.** 95 funciones documentadas con ejemplos ejecutables, accesible desde el botón "Diccionario" del Ribbon o desde la documentación embebida (capítulo 11). El usuario puede consultar parámetros, TipoOutput y ejemplos con datos dummy sin salir de Excel. Esto resuelve el problema de onboarding: el usuario tiene una referencia completa a un clic de distancia.

10. **Viewer Snap Layout (lado a lado).** Cuando `=NEVEN.v()` abre un visor, Excel se ajusta automáticamente a la mitad izquierda de la pantalla y el visor se abre en la mitad derecha. Esto proporciona un flujo de trabajo óptimo lado a lado sin que el usuario necesite organizar ventanas manualmente. Usa `SetWindowPos()` con `SystemParametersInfo(SPI_GETWORKAREA)` para respetar la barra de tareas. Es un diferenciador UX que ningún competidor ofrece: el usuario ve datos y visualización simultáneamente sin esfuerzo.

11. **Función de diagnóstico `=NEVEN.status()`.** Muestra el estado de conexión de los motores de lenguaje (R, Julia, Python), su estado de salud, prefijo y conteo total de funciones registradas. Herramienta esencial para soporte técnico y troubleshooting: el usuario puede verificar instantáneamente qué motores están activos sin revisar logs.

12. **Tabla Completa de Outputs (`Extraer_outputs`).** El usuario ejecuta cualquier función R4XCL con el TipoOutput más alto y obtiene TODOS los outputs del modelo en una sola tabla estructurada [Modelo, Seccion, Parametro, Metrica, Valor]. Esto elimina la necesidad de ejecutar múltiples TipoOutput para explorar un modelo — una sola llamada retorna todo. Disponible en 11 funciones (MR_Lineal, MR_Binario, MR_Poisson, MR_PanelData, ST_SeriesTemporales, MR_SVM, MR_Tobit, AD_ArbolDeDecision, AD_ACP, AD_KMedias). Ningun competidor ofrece extraccion universal de outputs de modelos estadisticos en una sola celda de Excel.

13. **Zombie Process Killer (fiabilidad de arranque).** Al iniciar, NEVEN mata automaticamente procesos huerfanos de sesiones anteriores (ControlR.exe, ControlJulia.exe, ControlPython.exe) que podrian bloquear los Named Pipes. Esto resuelve el problema de "Excel fue cerrado forzosamente y al reabrir no conecta". El usuario no necesita abrir Task Manager manualmente — NEVEN se auto-repara al arrancar.

---

## 4. Debilidades Comerciales

### Lo que impide venderlo hoy

**4.1 Instalacion — RESUELTO**

El instalador `Install-NEVEN.exe` (78 KB) automatiza todo el proceso en 6 fases:
1. Detecta R, Julia, Python y Excel automaticamente
2. Pregunta directorio de instalacion y opciones
3. Copia todos los binarios y configs
4. Registra XLL en Excel y Ribbon COM (con elevacion automatica)
5. Crea directorios del usuario, copia ejemplos, instala paquetes R
6. Verifica la instalacion y muestra instruccion de prueba

El usuario hace doble clic en `Install-NEVEN.exe` y en ~2 minutos tiene `=NEVEN.R("1+1")` funcionando.

Tambien disponible como script PowerShell (`Install-NEVEN.ps1`) para usuarios avanzados y automatizacion (`-Silent`).

**4.2 Primer contacto — RESUELTO PARCIALMENTE**

El diccionario de funciones integrado (95 funciones con ejemplos) y la documentación de 12 capítulos accesible desde el Ribbon resuelven el problema de "no sé qué funciones hay". El usuario puede:
- Clic en "Diccionario" → catálogo completo con ejemplos pegables
- Clic en "Documentación" → guía de 12 capítulos con tutoriales
- Usar `TipoOutput=0` en cualquier función → lista de procedimientos disponibles

Lo que aún falta:
- Video de 3 minutos mostrando el flujo completo
- Archivo Excel de ejemplo que se abra automáticamente al instalar
- Wizard de bienvenida en el primer uso

**4.3 Documentacion orientada a usuarios — RESUELTO**

La documentación ahora incluye:
- **Diccionario de funciones** (95 funciones con ejemplos pegables en Excel)
- **12 capítulos Docusaurus** accesibles desde el botón "Documentación" del Ribbon
- **Archivos Excel de ejemplo** en `libreria/EJEMPLOS/Excel/` para probar la herramienta
- **15 notebooks Pluto** en `libreria/EJEMPLOS/Notebooks/` para análisis interactivo

Lo que aún falta:
- Video demo de 3 minutos
- Capturas de pantalla paso a paso

**4.4 Dependencia de R, Julia y Python instalados — MITIGADO**

El usuario necesita instalar R, Julia y Python por separado. Sin embargo, el instalador de NEVEN detecta automaticamente que runtimes faltan y ofrece abrir la pagina de descarga oficial en el navegador del usuario. Este enfoque:

- **Delega la responsabilidad al usuario**: El usuario descarga e instala desde las paginas oficiales (cran.r-project.org, julialang.org, python.org). NEVEN no descarga ni ejecuta nada sin consentimiento explicito.
- **Elimina riesgos de inyeccion de codigo**: En entornos corporativos, descargar e instalar software automaticamente puede violar politicas de seguridad. Al abrir solo el navegador, NEVEN no introduce binarios no auditados.
- **Julia y Python son opcionales**: Si el usuario solo necesita R, NEVEN funciona perfectamente sin Julia ni Python. El instalador lo indica claramente.
- **Graceful degradation**: Si un runtime no esta instalado, NEVEN arranca limpiamente con los que si estan disponibles. No hay errores ni hangs.

**4.5 Solo Windows**

Excel existe en macOS, pero NEVEN usa Named Pipes, COM, WebView2, GDI+ — todo especifico de Windows. No hay camino facil a macOS o web.

Esto limita el mercado pero no lo elimina. La mayoria de usuarios corporativos de Excel estan en Windows.

**4.6 Sin telemetria de uso**

No hay forma de saber:
- Cuantos usuarios tiene
- Que funciones usan mas
- Donde se atascan
- Que errores encuentran

Sin estos datos, las decisiones de producto son a ciegas.

---

## 5. Modelo de Negocio

### Opciones viables

| Modelo | Precio sugerido | Pros | Contras |
|:---|:---|:---|:---|
| **Freemium** | Gratis (R basico) + $199/año (Julia + Python + WebView2 + Pluto + AI) | Baja barrera de entrada, upsell natural | Requiere sistema de licencias |
| **Licencia academica** | Gratis para universidades, $299/año corporativo | Adopcion en universidades → pipeline corporativo | Ingresos lentos al inicio |
| **Open source + soporte** | Gratis (GPL v3) + $99/hora de soporte | Comunidad, contribuciones, credibilidad | Dificil monetizar sin volumen |
| **SaaS (futuro)** | $29/mes | Recurrente, sin instalacion | Requiere reescritura para la nube |

### Recomendacion

**Licencia academica** es el camino mas natural dado el origen del proyecto. Liberar como open source con licencia GPL v3 (ya la tiene), construir comunidad en universidades latinoamericanas, y ofrecer licencia comercial para empresas.

El primer mercado objetivo deberia ser: **profesores de econometria en universidades de habla hispana que usan el libro de Wooldridge**. NEVEN ya tiene las funciones validadas contra ese texto.

---

## 6. Hoja de Ruta Comercial

### Fase 1 — Producto Minimo Viable (4-6 semanas)

| Tarea | Prioridad | Esfuerzo |
|:---|:---|:---|
| Instalador MSI con deteccion de R/Julia/Python | Completado | `Install-NEVEN.exe` (78 KB) — 6 fases automatizadas |
| Archivo Excel de ejemplo que se abre al instalar | Critica | 2 dias |
| Guia de inicio rapido (PDF, 5 paginas, con capturas) | Critica | 3 dias |
| Video demo de 3 minutos | Alta | 1 dia |
| Landing page basica (GitHub Pages) | Alta | 2 dias |
| Julia como componente opcional (no requerido) | Alta | 1 semana |

### Fase 2 — Traccion (2-3 meses)

| Tarea | Prioridad | Esfuerzo |
|:---|:---|:---|
| Piloto con 1-2 profesores de la UCR | Critica | Coordinacion |
| Feedback loop: que funciona, que no, que falta | Critica | Continuo |
| 10 tutoriales paso a paso (regresion, ACP, series de tiempo, etc.) | Alta | 2 semanas |
| Telemetria basica (opt-in, anonima) | Media | 1 semana |
| Publicacion en CRAN Task View o Julia packages | Media | 1 semana |

### Fase 3 — Escala (6+ meses)

| Tarea | Prioridad | Esfuerzo |
|:---|:---|:---|
| Comunidad: foro, Discord o GitHub Discussions | Alta | Setup + moderacion |
| Licencia comercial para empresas | Alta | Legal + sistema de licencias |
| Integracion con Python in Excel de Microsoft | Media | Investigacion — NEVEN ya tiene Python local, podria complementar la version nube |
| Soporte para Office.js (web/macOS) | Baja | Reescritura significativa |

---

## 7. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigacion |
|:---|:---|:---|:---|
| Microsoft mejora Python in Excel y cubre R/Julia | Media | Alto | NEVEN es local y privado; Python in Excel es nube. Diferente propuesta de valor |
| R pierde relevancia frente a Python | Baja (en estadistica/econometria) | Medio | Julia cubre matematica avanzada; Python integrado como tercer lenguaje; R sigue siendo el estandar en econometria y estadistica aplicada |
| Mantenimiento de un solo desarrollador | Alta | Alto | Open source + comunidad. Documentacion ya es excelente |
| Cambios en la API de Excel (deprecar XLL) | Baja | Critico | Microsoft mantiene backward compatibility por decadas |
| Usuarios no quieren instalar R/Julia/Python | Alta | Alto | R portable empaquetado; Julia y Python opcionales; Python embeddable package (15 MB) |

---

## 8. Estrategias de Monetizacion Alternativas

Mas alla de vender licencias directamente, hay rutas que no requieren construir una operacion comercial completa.

### 8.1 Venta de derechos o licenciamiento a un distribuidor

| Opcion | Descripcion | Valoracion estimada | Pros | Contras |
|:---|:---|:---|:---|:---|
| **Venta total de derechos** | Vender el codigo fuente, marca y derechos a una empresa que lo comercialice | $50K-$200K (dependiendo del comprador) | Ingreso inmediato, sin responsabilidad de mantenimiento | Pierdes control total, el comprador puede abandonarlo |
| **Licencia exclusiva** | Otorgar derechos exclusivos de comercializacion a un distribuidor por X años | $30K-$100K + royalties (10-20% de ventas) | Ingreso + participacion continua, el distribuidor pone el esfuerzo comercial | Dependes de que el distribuidor ejecute bien |
| **Licencia no-exclusiva** | Permitir que multiples distribuidores vendan NEVEN en diferentes mercados | Royalties (15-25% de ventas) | Multiples canales, conservas derechos | Menor control de precio y marca |
| **Adquisicion parcial** | Vender un % de la propiedad intelectual a un socio estrategico | Negociable | Capital + expertise del socio | Complejidad legal, posibles conflictos de vision |

**Compradores potenciales:**
- Empresas de add-ins de Excel (Solver.com, Frontline Systems, Palisade/Lumivero)
- Distribuidores de software estadistico (StataCorp, Minitab, TIBCO)
- Empresas de EdTech enfocadas en universidades latinoamericanas
- Consultoras de datos que quieran un producto propio

### 8.2 Microsoft como comprador o socio

Esta es la opcion mas ambiciosa pero tiene logica:

**Por que le serviria a Microsoft:**
- Microsoft ya tiene "Python in Excel" pero es solo Python, solo en la nube, y sin R ni Julia
- NEVEN demuestra que R y Julia pueden integrarse de forma estable en Excel local
- La arquitectura de procesos aislados (Named Pipes + Protobuf) es exactamente el patron que Microsoft usa en VS Code (Extension Host)
- El sandbox de seguridad resuelve un problema real que Microsoft enfrenta con Python in Excel
- La integracion con WebView2 (tecnologia de Microsoft) es un caso de uso que les interesa promover

**Formas de acercarse:**
1. **Microsoft for Startups** — programa que da creditos Azure, mentorias y acceso a equipos de producto. No requiere tener empresa constituida
2. **Publicar en Microsoft AppSource** — marketplace oficial de add-ins de Office. Da visibilidad y credibilidad
3. **Contactar al equipo de Excel extensibility** — via Twitter/LinkedIn de los PMs de Excel (hay varios activos). Mostrar el demo de `=NEVEN.r("1+1")` + WebView2 + Pluto
4. **Paper tecnico + demo** — publicar un paper en un journal de software cientifico y enviarlo al equipo de Excel como "mira lo que se puede hacer con tu plataforma"

**Realismo:** Microsoft no compra proyectos de un solo desarrollador facilmente. Pero si les interesa la tecnologia, podrian: (a) contratar al autor, (b) licenciar la tecnologia, o (c) inspirarse en la arquitectura para mejorar Python in Excel. La opcion (c) es la mas probable y no genera ingresos directos, pero si credibilidad academica y profesional.

### 8.3 Acqui-hire (contratacion por adquisicion)

Una empresa contrata al autor y adquiere el proyecto como parte del paquete. Esto es comun en startups de una persona con tecnologia solida.

**Candidatos:**
- Empresas que venden add-ins de Excel y quieren agregar R/Julia/Python a su oferta
- Consultoras de datos que quieren un producto propio para diferenciarse
- Empresas de EdTech que necesitan herramientas para ensenar estadistica

**Ventaja:** No necesitas construir una empresa. Alguien mas se encarga de ventas, soporte y marketing. Tu aportas la tecnologia y el conocimiento.

**Desventaja:** Pierdes autonomia. El proyecto puede tomar una direccion diferente a tu vision.

### 8.4 Modelo hibrido: Open Source + Enterprise

El modelo mas sostenible a largo plazo:

1. **Core open source (GPL v3)** — R + Julia + Python basico, sandbox, tests. Cualquiera puede usarlo gratis
2. **Enterprise edition (licencia comercial)** — WebView2 viewer, Pluto notebooks, Quarto reportes, Ribbon COM, soporte prioritario
3. **Precio:** $299/año por usuario, $999/año por equipo (5 usuarios)

Este modelo funciona porque:
- La version gratuita genera adopcion y comunidad
- Las funciones avanzadas (visualizacion, notebooks, reportes) son las que las empresas necesitan y estan dispuestas a pagar
- No requiere un equipo grande — un desarrollador puede mantener ambas versiones

### 8.5 Evaluacion honesta de cada ruta

| Ruta | Probabilidad de exito | Ingreso potencial | Esfuerzo requerido |
|:---|:---|:---|:---|
| Venta directa de licencias | Baja (sin equipo comercial) | $10K-$50K/año | Alto — ventas, soporte, marketing |
| Venta de derechos a distribuidor | Media | $50K-$200K (una vez) | Bajo — negociacion legal |
| Microsoft (cualquier forma) | Baja | Variable | Medio — networking, demo, paper |
| Acqui-hire | Media | Salario + bonus | Bajo — buscar la empresa correcta |
| Open Source + Enterprise | Media-Alta (largo plazo) | $20K-$100K/año | Medio — comunidad + producto |
| Licencia academica gratuita + corporativa | Media | $10K-$30K/año | Medio — ventas a empresas |

**Recomendacion:** Empezar con **Open Source + Enterprise** (8.4) porque no requiere inversion inicial, genera credibilidad, y deja abiertas todas las demas opciones. Si una empresa se acerca para comprar derechos o hacer acqui-hire, la base open source demuestra traccion y calidad.

---

## 9. Conclusion

NEVEN tiene las bases tecnicas de un producto comercial viable. Lo que le falta no es ingenieria — es **empaquetado, onboarding y distribucion**.

El camino mas corto a validacion comercial es:

1. Hacer un instalador que funcione en un click
2. Crear un Excel de ejemplo que demuestre valor en 5 minutos
3. Ponerlo en manos de 5 profesores de econometria
4. Escuchar que dicen

Si 3 de 5 lo adoptan para su curso, hay producto. Si no, hay que pivotar la propuesta de valor antes de invertir mas.

El nucleo tecnico esta. La pregunta no es "¿funciona?" — funciona. La pregunta es "¿alguien pagaria por esto?" y eso solo se responde poniendolo frente a usuarios reales.

---

*Documento interno de orientacion comercial.*
*NEVEN v2.0 — Universidad de Costa Rica*
*9 de mayo de 2026*
