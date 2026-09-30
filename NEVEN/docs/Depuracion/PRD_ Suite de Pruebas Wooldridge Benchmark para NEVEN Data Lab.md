### PRD: Suite de Pruebas Wooldridge Benchmark para NEVEN Data Lab

#### 1\. Visión General y Objetivo del Benchmark

NEVEN v2.2 mandata la  **Wooldridge Benchmark Suite**  como el portal no negociable para la auditoría econométrica de grado de producción. En un ecosistema donde la integridad de los datos es suprema, este benchmark actúa como el estándar de validación de precisión estadística, garantizando que los motores de R (v4.4.1) y Julia (v1.12.6) alcancen la "Paridad Estadística" absoluta con los resultados de referencia del texto de Jeffrey Wooldridge,  *Introductory Econometrics* .El objetivo primordial es asegurar que la serialización mediante Named Pipes y la posterior visualización en el Data Lab mantengan una precisión decimal idéntica a los estándares académicos, eliminando cualquier deriva computacional entre el cálculo nativo y la interfaz de usuario.

##### Objetivos Estratégicos del Benchmark

Meta,Descripción,Métrica de Éxito  
Precisión Decimal Crítica,Garantizar la paridad absoluta entre los coeficientes del libro de texto y el output procesado por NEVEN.,Error Cuadrático Medio (MSE) \< 1e-7 en coeficientes.  
Integridad de Motores,Validar la consistencia de la comunicación vía Named Pipes bajo condiciones de carga masiva.,"1,000 iteraciones sin fallos de consistencia (Stress/Reliability)."  
Validación de Latencia,Mantener la eficiencia en el desglose de resultados para el Data Lab.,Latencia de serialización sub-milisegundo mediante r\_object\_to\_slots.R.

#### 2\. Alcance Funcional: El Playbook Interactivo

El Benchmark se despliega como un "Playbook Interactivo" dentro de NEVEN Studio. A diferencia de las funciones estándar, el Playbook no invoca directamente a R.DS\_Wooldridge desde la interfaz; en su lugar, orquesta la carga mediante el wrapper especializado  **Wooldridge\_Benchmark.Studio.R** . Este wrapper actúa como el controlador principal, utilizando internamente R4XCL\_INT\_DATOS para asegurar que el preprocesamiento de variables sea idéntico al motor de Excel.

##### Capacidades Requeridas del Playbook

* **Orquestación Automatizada:**  Carga inmediata de los 115 datasets de Wooldridge integrados en la librería R4XCL.  
* **Pre-configuración Estricta:**  Modelos pre-mapeados (Dependiente vs. Independiente) basados en ejemplos canónicos del texto.  
* **Panel de Resultados Dual:**  Visualización comparativa en tiempo real entre el cálculo  *live*  de NEVEN y los valores objetivo ( *Reference Targets* ).

#### 3\. Matriz de Casos de Prueba End-to-End (Benchmarks Wooldridge)

La siguiente matriz define los puntos de control obligatorios para la certificación del Data Lab, vinculando cada dataset con su función de motor y su referencia académica.| ID del Caso | Dataset | Modelo / Procedimiento | Función NEVEN (R/Julia) | Target de Referencia (Libro) || \------ | \------ | \------ | \------ | \------ || **W-BENCH-001** | WAGE1 | Regresión Lineal Múltiple | R.MR\_Lineal | Cap. 3, Ejemplo 3.2: OLS Coeffs || **W-BENCH-002** | 401K | Regresión Logística | R.MR\_Binario.C | Cap. 7, Ejemplo 7.12: Logit Estimates || **W-BENCH-003** | JTRAIN | Datos de Panel | R.MR\_PanelData.C | Cap. 14, Ejemplo 14.1: Efectos Fijos || **W-BENCH-004** | SMOKE | Regresión Tobit | R.MR\_Tobit.C | Cap. 17, Ejemplo 17.2: Censura en cero || **W-BENCH-005** | FERTIL1 | Series de Tiempo | R.ST\_SeriesTemporales | Cap. 18: Cointegración / Dickey-Fuller || **W-BENCH-006** | CEOSAL1 | Análisis de Outliers | J.Estadistica (Proc. 8\) | Detección IQR de valores atípicos salariales |

#### 4\. Arquitectura de Implementación: Wrappers y Sidecars

La suite utiliza la  **Sidecar JSON Convention**  de NEVEN v2.2 para definir la estructura de los resultados en el Panel de Datos.

##### Especificaciones de Integración

1. **Wrappers Studio:**  Los archivos .Studio.R deben encapsular la lógica del benchmark, invocando a R4XCL\_INT\_DATOS para el manejo de factores y filtros, garantizando que el entorno de ejecución sea indistinguible del add-in de Excel.  
2. **Sidecars JSON:**  Cada prueba debe registrar un archivo en Install/functions/. Se requiere el siguiente esquema para el manejo de Tiers:

{  
  "function": "R.MR\_Lineal\_Wooldridge",  
  "tier": 1,  
  "slots": \["coefficients", "r\_squared", "p\_values"\],  
  "visualizer": "rpivotTable",  
  "audit": {  
    "tier": 2,  
    "slots": \["residuals", "vcov\_matrix"\],  
    "visualizer": "D3\_Sankey"  
  }  
}

1. **Serialización Dinámica:**  Es imperativo el uso de r\_object\_to\_slots.R para la conversión de objetos list (R) o Dict (Julia) en los formatos específicos (Table/Scalar/HTML) requeridos por el visor WebView2.

#### 5\. Requerimientos de Precisión y Visualización

La validación de datos se realizará exclusivamente contra los binarios integrados de R 4.4.1 y Julia 1.12.6.

* **Renderizado de Datos:**  Los resultados deben presentarse en el  **Dark Mode Viewer (\#2D2D2D)** .  
* **Visualización por Tiers:**  
* **Tier 1 (Core):**  Tablas interactivas mediante rpivotTable.  
* **Tier 2 (Audit):**  Visualizaciones complejas mediante D3.js. Específicamente, los diagnósticos de modelos de panel y series de tiempo deben utilizar los visualizadores  **Treemap**  o  **Sankey**  según la naturaleza de la jerarquía de datos (Fuente: 05-funciones-r.md).

#### 6\. Seguridad y Restricciones del Sandbox

Siguiendo los hallazgos críticos de seguridad de la versión 2.2, el benchmark operará bajo el control estricto de SandboxVerifier.cc.

1. **Whitelist de Columnas SEC-SEV-006:**  Dado que los benchmarks construyen fórmulas dinámicamente (eval(parse)), el SandboxVerifier.cc debe aplicar una  **whitelist basada en regex**  (alfanumérico estricto) a todos los nombres de columnas de los datasets de Wooldridge antes de la ejecución.  
2. **Prevención de Inyecciones SEC-CRI-002:**  El sandbox debe ejecutar la lógica de "strip whitespace" para neutralizar intentos de bypass como sys tem() o concatenaciones maliciosas.  
3. **Aislamiento de Filesystem:**  El acceso a los datasets se limitará al path resuelto por el ConfigService, bloqueando cualquier intento de  *path traversal* .

#### 7\. Mantenimiento y Extensibilidad

Para mantener la vigencia del benchmark frente a la expansión de la librería R4XCL (\~90 funciones actuales), se establece el siguiente protocolo de mantenimiento.

##### Procedimiento de Actualización

* Cualquier nuevo benchmark que requiera una configuración de motor adicional debe ser registrado en neven-languages.json.  
* Los nuevos wrappers deben adherirse a la nomenclatura \*.Studio.R.

##### Archivos Clave para Mantenimiento

Módulo / Archivo,Responsabilidad Técnica  
libreria/R/R4XCL-DS-Wooldridge.R,Catálogo maestro de carga de los 115 datasets.  
startup/r\_object\_to\_slots.R,Serializador de modelos para la interfaz Data Lab.  
Common/SandboxVerifier.cc,Verificación de integridad y sanitización de nombres de variables.  
Common/ConfigService.cc,Resolución de rutas de instalación y acceso a datos locales.  
Install/neven-languages.json,Configuración de los motores R/Julia para el entorno Studio.  
