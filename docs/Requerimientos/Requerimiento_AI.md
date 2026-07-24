# Documento de Especificación de Requerimientos Técnicos (SRS)

**Proyecto:** NEVEN (Next-Generation Econometric & Numerical Engine)  
**Módulo:** Interactive Edge Viewer & Econometric Intelligence Hub  
**Versión:** 1.0.0  
**Estado:** Propuesta de Arquitectura  
**Target Runtime:** Microsoft Edge (WebView2) + C# XLL Host + Native Kernels (Julia, R, Python) + LM Studio API  

---

## 1. Resumen Ejecutivo y Objetivos

El **Interactive Edge Viewer** de NEVEN es un componente de interfaz gráfica de usuario (GUI) embebido en Microsoft Excel mediante tecnología WebView2. Opera como un panel de control interactivo (*Interactive Dashboard*), motor de visualización avanzada (D3.js, Plotly, Canvas/WebGL) y hub de analítica prescriptiva impulsado por Inteligencia Artificial local a través de LM Studio.

El componente permite la interacción bidireccional a sub-milisegundo entre la hoja electrónica (rangos de celdas), los kernels de cómputo analítico (Julia, R, Python) y una interfaz basada en estándares web modernos, optimizada para tareas como manipulación dinámica de parámetros vía sliders, renderizado de objetos visuales no nativos de Excel e interpretación econométrica automatizada.

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de Componentes y Flujos de Datos

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 MICROSOFT EXCEL                                 │
│                                                                                 │
│   ┌───────────────────────────┐                ┌────────────────────────────┐   │
│   │   Excel Native Grid       │                │  NEVEN XLL Host (C#/C++)   │   │
│   │   (Ranges, Events, CAPI)  │◄──────────────►│  - Event Manager           │   │
│   └───────────────────────────┘                │  - Memory Buffer / Interop │   │
│                                                └──────────────┬─────────────┘   │
└───────────────────────────────────────────────────────────────┼─────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             PROCESS BOUNDARY (IPC)                              │
└──────┬────────────────────────────────────────┬───────────────────────────┬─────┘
│                                        │                           │
▼                                        ▼                           ▼
┌──────────────┐                       ┌──────────────────┐       ┌──────────────────┐
│ WebView2 UI  │                       │  Kernels Memory  │       │ LM Studio Engine │
│ (Edge Engine)│                       │ (Julia / R / Py) │       │ (Local REST API) │
└──────────────┘                       └──────────────────┘       └──────────────────┘

---

## 3. Requerimientos Funcionales (RF)

### RF-01: Interacción Bidireccional con Rangos de Excel
* **RF-01.1 (Excel $\rightarrow$ Viewer):** El Viewer debe capturar en tiempo real la selección de rangos en la hoja activa (`AppEvents_SheetSelectionChange`) y exponer la metadata (dirección, dimensiones, tipos de datos) a los componentes visuales del Viewer.
* **RF-01.2 (Viewer $\rightarrow$ Excel):** El Viewer debe incluir controles tipo *Range Picker* y botones de acción que permitan seleccionar, escribir o modificar valores y fórmulas en celdas de Excel de forma masiva (*vectorized bulk write*).
* **RF-01.3 (Rango Fijado / Lock Range):** El usuario podrá "fijar" un rango objetivo para evitar que el cambio accidental de selección en Excel invalide las visualizaciones o cómputos activos en el Viewer.

### RF-02: Reactividad mediante Controles de Parámetros (Sliders/Inputs)
* **RF-02.1:** El Viewer debe ofrecer componentes de UI (Sliders, Switches, Selectores) capaces de modificar celdas de la hoja o parámetros directos de las UDFs de NEVEN.
* **RF-02.2:** La modificación continua de un slider debe actualizar los modelos cuantitativos con una latencia total percebible por el usuario inferior a **50 ms**.
* **RF-02.3 (Throttling / Debouncing):** La UI debe pausar el refresco del Grid nativo de Excel (`ScreenUpdating = False`) durante el arrastre activo del slider para evitar cuellos de botella en la renderización de Excel, delegando el *feedback* visual directo al Viewer.

### RF-03: Renderizado de Objetos Cuantitativos Complejos (Visual Stream)
* **RF-03.1:** El Viewer debe incluir un motor de renderizado JS capaz de procesar e interpretar payloads enriquecidos generados por Julia, R o Python (specs de **D3.js, Plotly, Vega-Lite, ECharts, HTML/Canvas**).
* **RF-03.2 (Dual-Return UDF Pattern):** Cuando una UDF de NEVEN devuelva un objeto visualizable, la celda de Excel debe mostrar un identificador o resumen liviano (ej. `<NEVEN.D3Chart: id="8492">`), mientras que la estructura JSON/HTML completa del objeto se transmite al Viewer mediante la tubería secundaria de eventos.

### RF-04: Integración con LM Studio para Diagnóstico Econométrico
* **RF-04.1 (Payload Standardization):** El Host de NEVEN / Viewer debe empaquetar los resultados de modelos econométricos (OLS, VAR, VECM, ARIMA, Copulas) en un esquema JSON estandarizado (coeficientes, p-valores, $R^2$, Akaike, Durbin-Watson, Breusch-Pagan, VIF).
* **RF-04.2 (Inferencia Local Asíncrona):** El Viewer debe comunicarse mediante peticiones HTTP `POST` asíncronas (`fetch`) con la API local de LM Studio (`http://localhost:1234/v1/chat/completions`).
* **RF-04.3 (Interpretación Prescriptiva):** El Viewer debe renderizar en un panel dedicado el diagnóstico generado por el LLM (significancia estadística, validez teórica, alertas de autocorrelación/heterocedasticidad).
* **RF-04.4 (Inyección de Informe):** El Viewer debe proporcionar un mecanismo de un solo clic para exportar la interpretación del LLM directamente a Excel como un bloque de texto formateado o comentario en celda.

---

## 4. Requerimientos No Funcionales (RNF)

### RNF-01: Rendimiento y Latencia
* **RNF-01.1:** El tiempo de tránsito de mensajes desde eventos JS en el Viewer hacia el Host XLL debe ser inferior a **2 ms**.
* **RNF-01.2:** La tasa de refresco gráfica en el Viewer para animaciones o sliders debe sostener un mínimo de **30 a 60 FPS**.
* **RNF-01.3:** La transmisión de datos masivos entre los kernels (Julia/R/Python) y el Viewer debe realizarse mediante buffers en memoria compartida (*Shared Memory / Direct Memory Pointers*) para evitar la costo de conversión a JSON en grandes matrices.

### RNF-02: Disponibilidad y Aislamiento de Procesos
* **RNF-02.1:** El renderizado en WebView2 y las consultas a LM Studio no deben bloquear bajo ninguna circunstancia el hilo principal de Excel (*Main UI Thread*).
* **RNF-02.2:** La caída o desconexión del servidor local de LM Studio debe ser manejada de forma elegante con reintentos y alertas no intrusivas en la UI, sin colapsar el Viewer ni cerrar Excel.

### RNF-03: Seguridad y Privacidad
* **RNF-03.1:** Todo procesamiento por parte de LM Studio debe mantenerse **100% On-Premise / Localhost** sin llamadas externas a APIs en la nube.
* **RNF-03.2:** WebView2 debe configurarse deshabilitando el acceso a recursos web remotos no autorizados y cargando las librerías JavaScript (D3, Plotly, etc.) exclusivamente desde el paquete de recursos local (`SetVirtualHostNameToFolder`).

---

## 5. Especificación y Recomendaciones Técnicas de Implementación

### 5.1 Encapado del Host (Bridge WebView2 ↔ C# Host)

Se especifica el uso del método nativo `AddHostObjectToScript` de WebView2 en lugar de dependencias de red HTTP internas para llamadas de alta frecuencia:

```csharp
// C# Native Host Initialization (XLL TaskPane)
public void InitializeWebView(CoreWebView2AsyncInitializationCompletedEventArgs e) 
{
    var webView = taskPaneControl.WebViewElement;
    
    // Binding directo C# / JS (Baja latencia)
    var bridge = new NevenDirectBridge(this.ExcelApp, this.KernelManager);
    webView.CoreWebView2.AddHostObjectToScript("nevenHost", bridge);
    
    // Carga de paquete de recursos local (Seguridad/Offline)
    webView.CoreWebView2.SetVirtualHostNameToFolder(
        "neven.local", 
        System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "wwwroot"),
        CoreWebView2HostResourceAccessKind.Allow
    );
    
    webView.CoreWebView2.Navigate("[https://neven.local/index.html](https://neven.local/index.html)");
}

### 5.2 Estructura del Payload Econométrico para LM Studio (JSON Schema)
Los datos econométricos deben estructurarse bajo el siguiente esquema antes de ser enviados a la API de LM Studio:

{
  "$schema": "[http://json-schema.org/draft-07/schema#](http://json-schema.org/draft-07/schema#)",
  "type": "object",
  "properties": {
    "model_metadata": {
      "type": "object",
      "properties": {
        "model_type": { "type": "string" },
        "formula": { "type": "string" },
        "dependent_var": { "type": "string" },
        "n_obs": { "type": "integer" }
      },
      "required": ["model_type", "dependent_var", "n_obs"]
    },
    "fit_statistics": {
      "type": "object",
      "properties": {
        "r_squared": { "type": "number" },
        "adj_r_squared": { "type": "number" },
        "akaike_ic": { "type": "number" },
        "durbin_watson": { "type": "number" }
      }
    },
    "coefficients": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "variable": { "type": "string" },
          "estimate": { "type": "number" },
          "std_error": { "type": "number" },
          "t_stat": { "type": "number" },
          "p_value": { "type": "number" }
        },
        "required": ["variable", "estimate", "p_value"]
      }
    },
    "diagnostics": {
      "type": "object",
      "additionalProperties": { "type": "number" }
    }
  },
  "required": ["model_metadata", "fit_statistics", "coefficients"]
}

### 5.3 System Prompt Estandarizado para LM Studio

SYSTEM PROMPT:
Eres un econometrista sénior y científico de datos integrado en el motor NEVEN.
Analiza el payload JSON proporcionado con los resultados del modelo.

Estructura tu respuesta estrictamente en Markdown con los siguientes apartados:
1. Resumen Ejecutivo (2 frases explicativas).
2. Evaluación de Significancia Estadística (Análisis de p-valores y magnitudes de coeficientes).
3. Diagnóstico del Modelo (Evaluación de R², Durbin-Watson, heterocedasticidad y estabilidad).
4. Coherencia Económica y Advertencias (Verificación teórica de signos y sesgos potenciales).
5. Sugerencias de Ajuste (Indica si se requieren rezagos, transformaciones logarítmicas o cambios metodológicos).

Mantén un tono riguroso, directo, libre de divagaciones y enfocado en la toma de decisiones.

##  6. Matriz de Trazabilidad y Criterios de Aceptación (Definition of Done)
### CA-01
Criterio de Aceptación: Arrastre de slider fluido sin congelamiento de Excel.

Prueba de Verificación:Mover slider a 60Hz actualizando modelo en Julia; verificar que el lag sea < 50ms y Excel no presente estado "Not Responding".

### CA-02
Criterio de Aceptación: Renderizado de objeto D3.js generado en Python/R.
Prueba de Verificación: Invocación de UDF que retorna gráfico D3; verificar que el Viewer despliegue el gráfico dinámico correctamente.

### CA-03
Criterio de Aceptación: Sincronización de selección de rango.
Prueba de Verificación: Seleccionar rango B2:E50 en Excel; verificar actualización instantánea de la etiqueta "Active Target" en el Viewer.

### CA-04
Criterio de Aceptación: Diagnóstico en tiempo real vía LM Studio.
Prueba de Verificación: Enviar output de regresión OLS a localhost:1234; verificar recepción del reporte Markdown formateado en < 3 segundos.