### Especificación de Requerimientos de Software (SRS): Funciones Econométricas Avanzadas para NEVEN

#### 1\. Introducción y Objetivo del Proyecto

El propósito de este documento es definir las especificaciones técnicas para la expansión de las capacidades analíticas de NEVEN v2.2 mediante la implementación de modelos econométricos avanzados basados en la metodología de Wooldridge. El objetivo central es proporcionar una integración nativa en el "Data Lab" de NEVEN Studio y habilitar estas funciones como fórmulas de alto rendimiento en Microsoft Excel. Esta implementación debe garantizar la integridad estadística, la seguridad del sandbox y la eficiencia en la comunicación entre capas mediante el protocolo de serialización de la arquitectura NEVEN.

#### 2\. Alcance Funcional: Modelos Econométricos a Implementar

Se requiere la implementación de las siguientes familias de funciones econométricas. Cada método debe ser validado contra los resultados de referencia del paquete wooldridge en R 4.4.1.| Familia | Métodos Específicos | Descripción de Wooldridge / Aplicación || \------ | \------ | \------ || **Variables Instrumentales** | 2SLS (MCO en dos etapas) | Tratamiento de endogeneidad por omisión de variables o error de medición mediante instrumentos (Z) que satisfacen exogeneidad y relevancia. || **Sesgo de Selección** | Modelo de Heckman (Heckit) | Corrección del sesgo de selección muestral (truncamiento incidental) mediante la estimación de la razón de Mills inversa en la etapa de selección. || **Pruebas de Especificación** | RESET de Ramsey, Davidson-MacKinnon | Detección de errores en la forma funcional (RESET) y selección entre modelos no anidados (Davidson-MacKinnon J-test). || **Robustez** | Newey-West (HAC), FGLS | Estimación de matrices de varianza-covarianza consistentes ante heterocedasticidad y autocorrelación de forma desconocida. || **Series de Tiempo** | VAR (Vectores Autorregresivos), ECM | Modelado dinámico de sistemas endógenos y Modelos de Corrección de Error para capturar dinámicas de corto plazo en presencia de cointegración. |

#### 3\. Especificaciones de Integración Técnica en NEVEN

##### 3.1 Diseño de Wrappers en R (.Studio.R)

Los nuevos scripts se alojarán en libreria/R/. Para cumplir con los estándares de arquitectura y seguridad, se deben seguir estos pasos:

* **Construcción de Fórmulas Seguras (Mitigación SEC-SEV-006):**  Queda estrictamente prohibido el uso de eval(parse()). Las fórmulas deben construirse utilizando la función reformulate() o as.formula() a partir de los strings de columnas validados.  
* **Ejecución del Modelo:**  Llamada a librerías estándar (ej. AER::ivreg, sampleSelection::heckit).  
* **Captura de Estadísticos (Tiers):**  
* **Tier 1 (Slots Principales):**  Coeficientes, errores estándar, estadísticos t y p-valores.  
* **Tier 2 (Detalles Técnicos):**  Diagnósticos (R-squared, Log-Likelihood, AIC/BIC) y matrices de covarianza.  
* **Serialización:**  Uso obligatorio de r\_object\_to\_slots.R para convertir los objetos de modelo en la lista de slots requerida por la UI del Data Lab.

##### 3.2 Configuración de Sidecars JSON para el Data Lab

Cada función debe poseer un descriptor JSON en Install/functions/ (producción) para habilitar la interfaz "punto y clic". Durante el desarrollo, los archivos pueden residir en %USERPROFILE%\\Documents\\NEVEN\\functions\\.  
{  
  "id": "RG\_2SLS",  
  "family": "RG",  
  "function\_name": "R.RG\_2SLS.Studio",  
  "display\_name": "Regresión 2SLS (Wooldridge)",  
  "parameters": \[  
    { "name": "DepVar", "type": "column", "description": "Variable dependiente (Y)" },  
    { "name": "EndoVars", "type": "column", "description": "Variables endógenas (X)" },  
    { "name": "ExoVars", "type": "column", "description": "Variables exógenas control" },  
    { "name": "InstVars", "type": "range", "description": "Instrumentos externos (Z)" }  
  \],  
  "output\_slots": \[  
    { "id": "coef\_table", "type": "table", "tier": 1 },  
    { "id": "model\_summary", "type": "scalar", "tier": 1 },  
    { "id": "vcov\_matrix", "type": "table", "tier": 2 }  
  \]  
}

##### 3.3 Flujo de Comunicación IPC

El flujo debe respetar la arquitectura de 4 capas de NEVEN:

1. **Capa 1 (Excel/Studio):**  Captura de parámetros y serialización del Payload JSON.  
2. **Capa 2 (ControlR.exe):**  Recepción via  **Named Pipes**  y despacho al motor R 4.4.1.  
3. **Capa 3 (R Script):**  Ejecución del wrapper, aplicación de lógica as.formula y serialización de slots.  
4. **Capa 4 (Protobuf Return):**  Conversión de slots a Variable (Protobuf) y retorno al host para visualización en WebView2.

#### 4\. Requerimientos de Software y Dependencias

El entorno debe configurarse mediante el script R4XCL-0-UT-InstalaPaqueterias.R.| Función Econométrica | Paquete R Sugerido | Propósito || \------ | \------ | \------ || MCO 2 Etapas / IV | **AER** | Función ivreg. || Heckman Selection | **sampleSelection** | Función heckit. || Pruebas de Diagnóstico | **lmtest** | Test RESET y BP. || VCE Robusta (HAC) | **sandwich** | Estimador Newey-West. || Modelos VAR/VECM | **vars / urca** | Análisis de cointegración (Johansen). || Datasets Benchmark | **wooldridge** | Validación de resultados. |

#### 5\. Seguridad y Validación (Sandbox)

La implementación debe alinearse estrictamente con los hallazgos de la auditoría de seguridad del proyecto.

* **Prevención de Inyección (SEC-SEV-006):**  Todo input de texto proveniente de Excel debe ser sanitizado. Se prohíbe el uso de system(), eval(), y shell().  
* **Verificación de Integridad:**  Cada nuevo script en libreria/R/ debe contar con un archivo .sha256 generado. El SecurityService.cc bloqueará la ejecución de cualquier script cuyo hash no coincida con el registro.  
* **Restricciones en**  **SandboxVerifier.cc**  **:**  Actualizar la whitelist para permitir la carga de los nuevos namespaces de las librerías mencionadas, manteniendo el bloqueo sobre llamadas a APIs de bajo nivel de OS.

#### 6\. Plan de Pruebas y Calidad (GTest & PBT)

Se implementará una suite de pruebas en tests/advanced\_econometrics\_tests.cc bajo el framework Google Test.

1. **Validación de Consistencia:**  Test unitario comparando los coeficientes de la función RG\_2SLS contra el dataset mroz de Wooldridge.  
2. **Stress Test de Named Pipes (PBT):**  Uso de  *Property-Based Testing*  para enviar matrices de instrumentos (Z) aleatorias que superen el buffer de 256KB, validando la estabilidad de la fragmentación en el transporte IPC (Hallazgo SEC-ALT-001).  
3. **Validación de Sidecars:**  Verificación de integridad del catálogo mediante GET /api/datalab/catalog.  
4. **Integridad de Scripts:**  Confirmar que el sistema bloquea la ejecución si se modifica un wrapper sin actualizar su .sha256.

#### 7\. Estructura de Directorios de Implementación

Para asegurar el autodescubrimiento por parte del orquestador, los archivos deben ubicarse en las siguientes rutas:  
C:/NEVEN/  
├── libreria/  
│   └── R/  
│       ├── R4XCL-RG-Wooldridge.Studio.R  \<-- Wrappers avanzados  
│       └── R4XCL-RG-Wooldridge.Studio.R.sha256  
├── Install/  
│   └── functions/  
│       ├── RG\_2SLS.json                 \<-- Descriptores de funciones  
│       ├── RG\_HECKIT.json  
│       └── ST\_VAR\_ECM.json  
├── startup/  
│   └── startup.r                        \<-- Modificar para incluir source() de nuevos scripts  
└── tests/  
    └── advanced\_econometrics\_tests.cc   \<-- Suite GTest/PBT

