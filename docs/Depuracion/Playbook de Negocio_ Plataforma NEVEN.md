# Playbook de Negocio: Plataforma NEVEN
**Estrategia de Adopción y Soluciones por Rol Académico y Profesional**

---

## 1. Propuesta de Valor Central

**NEVEN convierte Microsoft Excel en una plataforma de análisis de datos de grado corporativo.**

No es un add-in más. Es la única plataforma que integra R, Julia y Python directamente en el flujo de trabajo de Excel — con visualizaciones interactivas, análisis punto-y-clic, IA local y generación de presentaciones ejecutivas, todo desde un mismo entorno.

### El problema que resuelve

Los analistas, investigadores y científicos de datos viven atrapados entre dos mundos: Excel, que todos usan pero que es estadísticamente limitado, y R/Python/Julia, que son potentes pero requieren programación. Cada vez que necesitan un modelo avanzado, rompen el flujo: exportan datos, abren otro software, ejecutan el modelo, copian resultados de vuelta a Excel. Cada "copiar y pegar" es un punto de error. Cada cambio de herramienta es tiempo perdido.

NEVEN elimina ese salto. El analista escribe `=R.MR_Lineal(Y, X, 1)` en una celda y obtiene el modelo. Sin salir de Excel. Sin copiar datos. Sin riesgo de desincronización.

### Los tres pilares

| Pilar | Qué significa en la práctica |
|:---|:---|
| **Multilenguaje nativo** | R, Julia y Python como fórmulas de Excel. La herramienta correcta para cada problema, desde el mismo libro. |
| **Visualización interactiva** | Plotly, D3.js, Leaflet y dashboards embebidos en el flujo de trabajo. No imágenes estáticas — gráficos que el usuario puede explorar. |
| **Seguridad de grado corporativo** | Sandbox de 5 niveles, 357 tests automatizados con 100% de éxito, SHA-256 de integridad. Aprobable por el equipo de TI. |

### Arquitectura que no congela Excel

NEVEN corre cada motor de lenguaje como un proceso independiente. Si R o Julia fallan, Excel sigue funcionando. La comunicación usa **Named Pipes + Protocol Buffers** — el mismo patrón que usa Microsoft en VS Code para sus extensiones. Esto también permite que **NEVEN Studio** funcione completamente sin Excel instalado, abriendo la plataforma a entornos que no tienen licencia de Office.

---

## 2. Modelo de Precios

| Tier | Incluye | Precio |
|:---|:---|:---|
| **NEVEN Free** | Add-in XLL, R básico en Excel, sandbox de seguridad | **Gratis** (GPL v3) |
| **NEVEN Academic** | Todo Free + Julia + Python + Studio + Data Lab | **Gratis** para universidades |
| **NEVEN Studio** | Todo Academic + Data Lab completo + Creador de Presentaciones + catálogo extensible | **$299/año** por usuario |
| **NEVEN Studio Pro** | Todo Studio + soporte prioritario + funciones UC personalizadas + actualizaciones garantizadas | **$499/año** / **$1,499/año** equipo (5) |

### Por qué $299 es un precio conservador

| Producto | Precio | Lenguajes | Interfaz propia | Presentaciones |
|:---|:---|:---|:---|:---|
| PyXLL | $495/año | Solo Python | No | No |
| xlwings PRO | $490/año | Solo Python | No | No |
| **NEVEN Studio** | **$299/año** | R + Julia + Python | ✅ | ✅ |
| **NEVEN Studio Pro** | **$499/año** | R + Julia + Python | ✅ + soporte | ✅ + personalización |

NEVEN Studio cuesta el 60% de lo que cobra la competencia y entrega más del doble de capacidades.

---

## 3. Perfil 1: El Analista Financiero

**Dolor principal:** modelos avanzados atrapados fuera de Excel, riesgo de errores por copiar resultados manualmente, procesos que congelan el sistema.

### Cómo NEVEN resuelve cada fricción

| Situación | Sin NEVEN | Con NEVEN |
|:---|:---|:---|
| Modelado estadístico | Exportar CSV → software externo → copiar resultados | `=R.MR_Lineal(Y, X, 1)` directo en la celda |
| Consistencia de datos | Archivos desincronizados entre sesiones | Fuente única de verdad dentro del mismo `.xlsx` |
| Extraer outputs de modelos | Programación manual o consultor externo | `Extraer_outputs()` convierte cualquier modelo R en tabla estructurada |
| Estabilidad de sesión | Bloqueo manual — Task Manager | Auto-recuperación silenciosa (Zombie Process Killer) |

### `Extraer_outputs` — el diferenciador para finanzas

Los modelos estadísticos en R devuelven objetos complejos (`lm`, `glm`, `arima`) con estructura interna variable. Extraer coeficientes, errores estándar y métricas de ajuste normalmente requiere código. `Extraer_outputs` hace eso automáticamente — una sola llamada retorna **todos** los resultados del modelo en una tabla estructurada en Excel, lista para auditoría o reporte.

Disponible en 11 funciones: regresión lineal, binaria, Poisson, Tobit, datos de panel, series de tiempo, SVM, árbol de decisión, ACP y K-Medias.

### Simulaciones Monte Carlo: NEVEN-SIM

Para equipos de riesgo y estructuración, **NEVEN-SIM** es un módulo XLL separado para simulación Monte Carlo. Se integra en el mismo entorno sin necesidad de software adicional.

---

## 4. Perfil 2: El Consultor de Datos y BI

**Dolor principal:** clientes que viven en Excel pero que necesitan análisis que Excel no puede hacer. El consultor tiene que elegir entre entregar algo limitado en Excel o entregar algo avanzado en una herramienta que el cliente no sabe usar.

### NEVEN Studio — análisis sin código

**NEVEN Studio** es una interfaz web accesible en `localhost:5555` que expone el poder de R, Julia y Python a través de una experiencia punto-y-clic. Sin programación. Sin líneas de código.

El consultor o el cliente selecciona la función, asigna las columnas, configura parámetros — y hace clic en Ejecutar. Los resultados aparecen como tablas interactivas y gráficos Plotly en el navegador.

**18 funciones disponibles en el catálogo:** K-Medias, ACP, Clustering Jerárquico, 7 modelos de regresión, Series de Tiempo, SVM, Text Mining con IA, y datasets Wooldridge.

### Visualizaciones que los clientes no olvidan

Más allá de los gráficos de barras y líneas que Excel ya ofrece, NEVEN expone visualizaciones de alto impacto:

- **Treemap D3.js** — distribución de mercado o portfolio en un solo gráfico
- **Sankey** — flujos de conversión, supply chain, presupuestos
- **Mapas de calor Leaflet** — inteligencia geoespacial con capas dinámicas
- **Sunburst** — estructuras jerárquicas y categóricas
- **Burbujas dinámicas** — análisis multivariado con dimensión de color continuo

### Snap Layout — flujo de trabajo optimizado

Cuando el consultor abre un gráfico, NEVEN reorganiza automáticamente el espacio de pantalla: Excel a la izquierda, visor interactivo a la derecha. Sin arrastrar ventanas. Sin Alt+Tab. El cliente ve los datos y la visualización al mismo tiempo.

### Del análisis a la presentación ejecutiva — sin salir de NEVEN

Con el **Creador de Presentaciones** integrado en Studio, el flujo completo ocurre en un solo entorno:

1. Cargar datos en Data Studio
2. Ejecutar análisis en Data Lab
3. Hacer clic en **"Enviar a Slide"** desde cualquier gráfico o tabla
4. Ajustar tamaño, posición y zoom del objeto en el slide
5. Exportar la presentación en HTML interactivo

El resultado es una presentación ejecutiva donde los gráficos son navegables — el cliente puede explorarlos durante la reunión, no solo verlos como imágenes estáticas.

---

## 5. Perfil 3: Profesores e Investigadores

**Dolor principal:** los estudiantes necesitan aprender econometría y estadística avanzada, pero la barrera de programación consume la mitad del tiempo de la clase. La reproducibilidad de los trabajos de investigación es difícil de garantizar.

### En el aula: de la teoría a la práctica en una celda

Un estudiante que nunca ha visto R puede estimar un modelo de Datos Panel con `=R.MR_PanelData(Y, X, 1)` en su primer día de clase. Sin instalar R. Sin aprender sintaxis. La fórmula es el modelo.

La librería incluye los **115 datasets del libro de Wooldridge** — el estándar en econometría aplicada. Los estudiantes pueden reproducir cualquier ejemplo del libro directamente en Excel.

### Para investigadores: reproducibilidad sin fricción

La integración con **Quarto** (`=NEVEN.q("reporte.qmd")`) permite generar reportes científicos reproducibles donde los rangos de Excel alimentan directamente la narrativa. Cambiar los datos actualiza el reporte completo. Un clic exporta a PDF, HTML o Word.

**Pluto.jl** amplía esto a notebooks reactivos — los resultados de Julia se actualizan en tiempo real cuando los datos de Excel cambian, vía el pipeline `PLUTO.DATA`.

### Caso de uso concreto

Un docente de la Escuela de Economía de la UCR puede:
- Abrir un dataset de Wooldridge con `=R.DS_Wooldridge("wage2", 1)`
- Estimar el modelo con `=R.MR_Lineal(salario, educacion, 3)` (tabla ANOVA completa)
- Visualizar los residuos con `=R.GR_Histograma(residuos, 1)`

Todo en la misma hoja, en 10 minutos, sin escribir una línea de código R.

---

## 6. Perfil 4: Científicos de Datos

**Dolor principal:** los modelos avanzados viven en Jupyter o scripts Python/R que el resto de la organización no puede usar. El científico de datos se convierte en un cuello de botella para cada análisis.

### IA local — soberanía de datos sin compromiso

`=P.ai_call(datos, "interpretar_regresion")` envía los resultados de cualquier modelo al LLM configurado y retorna una interpretación en lenguaje natural directamente en la celda.

La diferencia crítica frente a los competidores: **los datos nunca salen de la organización**. NEVEN se conecta a **Ollama** o **LM Studio** corriendo localmente. Para empresas con datos financieros, médicos o legales, esto no es un feature opcional — es un requisito de compliance.

Los prompts son archivos `.txt` editables que el equipo puede personalizar sin modificar el código. Siete prompts predefinidos cubren los casos más comunes: interpretar regresión, describir distribución, resumir correlaciones, evaluar supuestos del modelo.

### Julia para cómputo de alto rendimiento

Para algoritmos que necesitan velocidad real — optimización, álgebra lineal de gran escala, simulaciones — Julia 1.12.6 con **sysimage precompilada** arranca en ~1 segundo (vs. 1-5 minutos de cold start). El científico accede vía `=J.Algebra()`, `=J.Optimizar()` o cualquiera de los 70 procedimientos del catálogo Julia, con la misma sintaxis de fórmula Excel que conoce.

### Catálogo extensible — sin tocar el core

La **convención Sidecar JSON** permite al equipo de data science agregar sus propios modelos al catálogo de NEVEN Studio sin modificar el código C++ ni necesitar acceso al repositorio. Dos archivos — el código R y un JSON de descripción — son suficientes para que cualquier función aparezca en la interfaz punto-y-clic con parámetros configurables y resultados tipificados.

---

## 7. Seguridad y Cumplimiento para TI

Para que el área de TI apruebe la instalación, NEVEN tiene respuestas concretas a cada pregunta de seguridad.

### Sandbox de 5 niveles

El código que el usuario escribe en una celda pasa por cinco capas de validación antes de ejecutarse:

| Nivel | Qué bloquea | Ejemplo |
|:---|:---|:---|
| Shell | Comandos del sistema operativo | `system()`, `run()`, `subprocess.*` |
| Archivos | Modificación no autorizada del filesystem | `file.remove()`, `unlink()`, `os.remove()` |
| Red | Conexiones salientes no supervisadas | `download.file()`, `url()` |
| Código dinámico | Patrones de bypass de sandbox | `eval(parse())`, `do.call()`, `exec()` |
| Entorno | Variables de sistema y configuración | `Sys.setenv()`, `os.environ` |

Cada nivel tiene cobertura de tests: 154 tests automatizados cubren el sandbox, incluyendo intentos de bypass por whitespace, concatenación de strings y case insensitivo.

### Checklist para el equipo de TI

- ✅ **Integridad de scripts:** SHA-256 verifica `startup.r` y `startup.jl` en cada arranque
- ✅ **Validación de protocolo:** frames Protobuf validados antes de deserialización (MessageValidator)
- ✅ **Aislamiento de procesos:** R, Julia y Python en procesos independientes — un crash no afecta a Excel
- ✅ **Allowlist de ejecutables:** InputSanitizer permite solo binarios conocidos en CreateProcess
- ✅ **Protección de configuración:** path traversal y command injection bloqueados en el JSON de config
- ✅ **Sin dependencias de red en runtime:** la comunicación es 100% local (Named Pipes)
- ✅ **IA 100% local:** `P.ai_call` nunca envía datos a servidores externos si se usa Ollama/LM Studio
- ✅ **Compilación hardened:** MSVC con /GS, /guard:cf, /DYNAMICBASE, /NXCOMPAT, /CETCOMPAT

### Sin riesgo de instalación masiva

NEVEN no modifica el registro de Windows más allá del registro del XLL en Excel. Se puede desinstalar completamente con el `Uninstall-NEVEN.exe` incluido. No hay servicios de Windows corriendo en background cuando Excel está cerrado.

---

## 8. Comparativa de Mercado

| Capacidad | BERT (abandonado) | PyXLL $495/año | xlwings $490/año | Python in Excel | **NEVEN Studio $299/año** |
|:---|:---:|:---:|:---:|:---:|:---:|
| R en Excel | R 3.4 ❌ | ❌ | ❌ | ❌ | ✅ R 4.4.1 |
| Julia en Excel | Julia 0.6 ❌ | ❌ | ❌ | ❌ | ✅ Julia 1.12.6 |
| Python en Excel | ❌ | ✅ | ✅ | ✅ (nube) | ✅ local |
| Sin Excel requerido | ❌ | ❌ | ❌ | ❌ | ✅ NEVEN Studio |
| Interfaz punto-y-clic | ❌ | ❌ | ❌ | ❌ | ✅ Data Lab |
| Visualizaciones interactivas | PNG ❌ | ❌ | ❌ | ❌ | ✅ Plotly/D3/Leaflet |
| IA local (Ollama/LM Studio) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Creador de presentaciones | ❌ | ❌ | ❌ | ❌ | ✅ |
| Datos en la nube | ❌ | ❌ | ❌ | **Obligatorio** | ✅ 100% local |
| Tests automatizados | 0 | N/D | N/D | N/D | **357 tests** |
| Precio | Gratis | $495/año | $490/año | Incluido en 365 | **$299/año** |

> Python in Excel de Microsoft ejecuta en la nube de Azure — los datos del usuario salen de su organización. NEVEN con Ollama o LM Studio procesa localmente. Para datos financieros, médicos o legales, esta diferencia es crítica.

---

## 9. Rutas de Adopción

### Adopción individual (bottom-up)

1. Descarga **NEVEN Free** — sin tarjeta de crédito, sin formulario
2. Ejecuta `=NEVEN.r("1+1")` — si devuelve 2, la instalación fue exitosa
3. Carga un dataset propio en Data Studio y ejecuta un análisis en Data Lab
4. Cuando el valor es evidente, upgrade a Studio para el Creador de Presentaciones y el catálogo completo

### Adopción institucional (top-down)

1. Piloto con 2-3 usuarios técnicos durante 30 días — **NEVEN Academic** para universidades, **NEVEN Free** para empresas
2. Presentación al equipo de TI con el checklist de seguridad de la Sección 7
3. Licencia de equipo **Studio Pro** ($1,499/año, 5 usuarios) para el grupo piloto
4. Expansión por departamento con la **familia UC** — el equipo técnico agrega sus propias funciones sin modificar el core

### Para universidades: siempre gratuito

**NEVEN Academic** es completamente gratuito para instituciones educativas. Incluye R, Julia, Python, NEVEN Studio y Data Lab. La única condición es uso no comercial.

La ruta natural: los estudiantes aprenden NEVEN en la universidad, lo llevan a sus empleos, generan demanda corporativa desde adentro.

---

## 10. El Flujo Completo: Datos → Análisis → Presentación

Este es el diferenciador que ningún competidor puede replicar hoy:

```
1. DATOS        Cargar CSV/Excel/BD externa en Data Studio
                                    ↓
2. ANÁLISIS     Ejecutar ACP, regresión, K-Medias en Data Lab (sin código)
                                    ↓
3. VISUALIZAR   Gráfico Plotly interactivo generado automáticamente
                                    ↓
4. PRESENTAR    "Enviar a Slide" → objeto escala y posiciona en la presentación
                                    ↓
5. EXPORTAR     HTML interactivo listo para reunión con la dirección
```

Todo en un solo entorno. Sin copiar datos. Sin cambiar de herramienta. Sin perder la trazabilidad.

---

*NEVEN v2.2 — Plataforma de Análisis Multilenguaje*
*Universidad de Costa Rica — agosto 2026*
*Repositorio: https://github.com/minorbonillagomez/NEVEN.git*
