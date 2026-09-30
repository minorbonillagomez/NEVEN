---
id: neven-studio
title: "Capitulo 13 - NEVEN Studio Standalone"
sidebar_label: 13. NEVEN Studio
sidebar_position: 13
---

# Capitulo 13: NEVEN Studio Standalone

**Disponible desde:** Julio 2026

NEVEN Studio Standalone es el modo de operación de NEVEN **sin Microsoft Excel**. Abre una interfaz web completa en el navegador del sistema que permite ejecutar análisis estadísticos, cargar datos y usar el catálogo de funciones Data Lab — todo sin necesitar una licencia de Excel.

---

## 13.1 Arranque rápido

```
1. Doble clic en:   C:\NEVEN\taskpane\NEVEN Studio.vbs
2. Se abre el navegador en:  http://localhost:5555
3. Listo.
```

---

## 13.2 Pestañas del Studio

| Pestaña | Función |
|:---|:---|
| **Data Lab** | Análisis punto-y-clic sin código (18 funciones) |
| **Run Script** | Editor de código R / Julia / Python con ejecución directa |
| **Data Studio** | Carga de archivos CSV, Parquet, JSON → tabla `dataset` |
| **AI** | Integración con LMStudio para interpretación de resultados |

---

## 13.3 Data Lab

El Data Lab expone el catálogo de funciones analíticas de NEVEN mediante una interfaz guiada.

### Flujo de uso

```
1. Cargar datos
   Data Studio → "Cargar archivo" → seleccionar CSV / Parquet / JSON
   (o enviar desde Excel via Bridge)

2. Seleccionar función
   Data Lab → dropdown "Familia" → lista de funciones

3. Asignar columnas a roles
   Panel de columnas: clic en columna → clic en rol (X, Y, T, ID)

4. Configurar parámetros
   Controles automáticos según tipo (spinner, checkbox, dropdown)

5. Ejecutar
   Clic en "Ejecutar análisis"

6. Ver resultados
   Slots tipificados: tablas, gráficos HTML, escalares, vectores
```

### Familias disponibles

| Familia | Código | Funciones |
|:---|:---|:---|
| Análisis de Datos | **AD** | K-Medias, Componentes Principales (PCA), Clustering Jerárquico |
| Regresión | **RG** | Lineal, Logística, Árbol de Decisión, Datos Panel, Poisson, Series de Tiempo, SVM, Tobit |
| Conjuntos de Datos | **DS** | Wooldridge (115 datasets de econometría) |
| Text Mining | **TM** | Análisis de texto (PDF, DOCX, TXT) |
| Mis Funciones | **UC** | Plantillas para funciones personalizadas |

### Resultados (Slots)

Los resultados se presentan en secciones tipificadas:

| Tipo | Presentación |
|:---|:---|
| `table` | Tabla HTML con scroll |
| `html` | Gráfico interactivo Plotly en iframe |
| `scalar` | Valor en `<pre>` |
| `vector` | Lista en `<pre>` |

Los resultados **Tier 1** aparecen expandidos por defecto.
Los resultados **Tier 2** aparecen en la sección "Detalles técnicos" colapsada.

---

## 13.4 Run Script

Ejecuta código directamente en los motores de lenguaje.

```
Pestaña "Run Script"
  → Seleccionar lenguaje: R | Julia | Python
  → Escribir código
  → Clic "Ejecutar"
  → Ver resultado
```

**Ejemplo R:**
```r
df <- data.frame(x = 1:5, y = c(2,4,5,4,5))
cor(df$x, df$y)
```

**Ejemplo Python:**
```python
import duckdb
conn = duckdb.connect()
conn.execute("SELECT COUNT(*) FROM dataset").fetchone()
```

---

## 13.5 Data Studio

Permite cargar datos al `dataset` activo que usa el Data Lab.

| Formato | Soporte |
|:---|:---|
| CSV | ✅ Auto-detección de separador y encoding |
| Parquet | ✅ |
| JSON | ✅ (array de objetos) |
| Excel (via Bridge) | ✅ Desde NEVEN para Excel |

Los datos se almacenan en **DuckDB in-memory** como la tabla `dataset`.

---

## 13.6 Text Mining con IA

La función **TM → Text Analysis** produce:

1. **Estadísticas léxicas** — total palabras, vocabulario, riqueza léxica
2. **Análisis de sentimiento** — positivo / neutro / negativo
3. **Resumen contextual (IA)** — generado por LMStudio (si está activo)
4. **Resumen extractivo (TF-IDF)** — top N oraciones por relevancia
5. **Gráfico de frecuencias** — barras horizontales Plotly
6. **Nube de palabras** — espiral de Arquímedes con Plotly

### Configurar LMStudio

En `C:\NEVEN\neven-config.json`:

```json
"AI": {
  "enabled": true,
  "provider": "lmstudio",
  "model": "nvidia/nemotron-3-nano-4b",
  "endpoint": "http://localhost:1234/v1/chat/completions",
  "maxTokens": 1000,
  "temperature": 0.3,
  "timeout": 120
}
```

Si LMStudio no está corriendo, el slot de resumen IA simplemente no aparece — los demás resultados funcionan normalmente.

---

## 13.7 Agregar funciones propias

Cualquier usuario puede agregar sus propias funciones al catálogo Data Lab con dos archivos:

**Archivo 1: `MiFuncion.Studio.R`**
```r
MiFuncion.Studio <- function(data_X, Param1 = 3L) {
  resultado <- list(
    tabla = mi_analisis(data_X),
    valor = 42.5
  )
  tier_map <- c(tabla = 1L, valor = 2L)
  return(r_object_to_slots(resultado, tier_map = tier_map))
}
```

**Archivo 2: `MiFuncion.json`**
```json
{
  "id": "MiFuncion",
  "family": "UC",
  "family_label": "Mis Funciones",
  "name": "Mi Análisis",
  "description": "Descripción breve.",
  "languages": ["r"],
  "function_name": "MiFuncion.Studio",
  "file": "MiFuncion.Studio.R",
  "variable_roles": {
    "X": { "label": "Variables", "types": ["numeric"], "multiple": true, "required": true }
  },
  "parameters": [
    { "name": "Param1", "label": "Parámetro", "type": "integer", "default": 3, "tier": 1 }
  ]
}
```

Copiar ambos archivos a `C:\NEVEN\functions\` y reiniciar NEVEN Studio.

Ver guía completa: `C:\NEVEN\functions\COMO_AGREGAR_FUNCIONES.md`

---

## 13.8 Diferencias con NEVEN para Excel

| Característica | NEVEN Excel | NEVEN Studio |
|:---|:---:|:---:|
| Requiere Excel | ✅ | ❌ |
| Funciones como fórmulas `=R.func()` | ✅ | ❌ |
| Data Lab punto-y-clic | ❌ | ✅ |
| Run Script (R/Julia/Python) | Parcial | ✅ |
| Carga de archivos CSV/Parquet | ❌ | ✅ |
| AI / LMStudio integration | Parcial | ✅ |
| WebView2 Viewer | ✅ | ❌ |
| Pluto.jl Notebooks | ✅ | ❌ |
| Quarto Reportes | ✅ | ❌ |
| Ribbon COM nativo | ✅ | ❌ |
| Mismos motores R/Julia/Python | ✅ | ✅ |
| Mismos binarios C++ | ✅ | ✅ |

Ambos modos se instalan juntos — la misma instalación en `C:\NEVEN\` sirve para los dos.

---

## 13.9 Sistema de Aliases

NEVEN permite invocar funciones usando nombres cortos (aliases) en lugar del nombre completo. Esto simplifica el uso desde Excel y el Studio.

### Ejemplos de aliases

| Alias | Funcion real | Uso |
|:---|:---|:---|
| `ACP` | `AD_ACP.C` | Analisis de Componentes Principales |
| `KMeans` | `AD_KMeans.C` | Clustering K-Medias |
| `RegLineal` | `RG_Lineal.C` | Regresion Lineal |
| `Logistica` | `RG_Logistica.C` | Regresion Logistica |
| `PanelData` | `RG_Panel.C` | Datos de Panel |

### Uso en Excel

```
=NEVEN.R("ACP", A1:D20)           Equivale a =NEVEN.R("AD_ACP.C", A1:D20)
=NevenX.R("KMeans", A1:D20, 3)    Equivale a =NevenX.R("AD_KMeans.C", A1:D20, 3)
```

### Uso en NEVEN Studio

En el Data Lab, el dropdown de funciones muestra tanto el nombre completo como los aliases disponibles.

### Donde se definen los aliases

Los aliases se definen en dos lugares:

1. **Dispatcher R:** `C:\NEVEN\functions\R4XCL-0-NevenX.R` → tabla `.neven_aliases`
2. **Servidor HTTP:** `C:\NEVEN\startup\neven_http_server.py` → diccionario `_function_aliases`

Para agregar un nuevo alias, modificar ambos archivos. Ver guia completa en:
`C:\NEVEN\docs\agent-context\ALIASES.md`

---

## 13.10 Troubleshooting

**El Studio no carga:**
- Verificar que Python este instalado
- Usar el boton "Iniciar Servidor" en el Ribbon (grupo Studio)

**Data Lab no muestra funciones:**
- Verificar que los archivos .json esten en `C:\NEVEN\functions\`
- Reiniciar el servidor HTTP

**Run Script no ejecuta:**
- Verificar que el motor correspondiente este activo en `neven-config.json`

---

## 13.11 Tab Settings — Configurador de Perfiles AI y Conexiones DB

**Disponible desde:** Agosto 2026

El Tab Settings permite configurar NEVEN sin editar archivos JSON manualmente. Es accesible desde la pestaña "Settings" en NEVEN Studio.

### Sub-tabs disponibles

| Sub-tab | Función |
|:---|:---|
| **Motor IA** | Gestionar perfiles de proveedores AI (OpenAI, Claude, Azure, Ollama, LM Studio) |
| **Conexiones DB** | Gestionar conexiones a bases de datos (PostgreSQL, MySQL, SQL Server, SQLite, DuckDB) |
| **Prompts** | Editar prompts de IA por categoría |

### Motor IA — Perfiles múltiples

NEVEN soporta múltiples perfiles de IA. Solo uno puede estar activo a la vez.

**Proveedores soportados:**

| Proveedor | Modelos | Notas |
|:---|:---|:---|
| OpenAI | gpt-4o, gpt-4-turbo, gpt-3.5-turbo | Requiere API key |
| Azure OpenAI | Configurable | Requiere endpoint + API key |
| Anthropic | claude-3-5-sonnet, claude-3-opus | Requiere API key |
| Ollama | Modelos locales | Gratis, local, sin API key |
| LM Studio | Modelos locales | Gratis, local, sin API key |

**Flujo de uso:**

```
1. Settings → Motor IA
2. Clic "Nuevo Perfil"
3. Seleccionar proveedor
4. Completar credenciales
5. Clic "Probar Conexión" (verificar)
6. Clic "Guardar"
7. Seleccionar perfil → radio button para activarlo
```

### Conexiones DB — Múltiples conexiones

Gestiona conexiones a bases de datos para el Data Studio y consultas SQL.

**Bases de datos soportadas:**

| Tipo | Puerto default | Notas |
|:---|:---|:---|
| PostgreSQL | 5432 | Requiere host/user/password |
| MySQL | 3306 | Requiere host/user/password |
| SQL Server | 1433 | Windows Auth o SQL Auth |
| SQLite | — | Solo ruta al archivo .db |
| DuckDB | — | Solo ruta al archivo .duckdb |

**Flujo de uso:**

```
1. Settings → Conexiones DB
2. Clic "Nueva Conexión"
3. Seleccionar tipo de BD
4. Completar datos de conexión
5. Clic "Probar Conexión"
6. Clic "Guardar"
```

### Seguridad de credenciales

Las credenciales sensibles (API keys, passwords de BD) se almacenan en **Windows Credential Manager**, no en el archivo JSON. Esto significa:

- Las credenciales están encriptadas por Windows
- El archivo `neven-config.json` solo contiene referencias (IDs)
- Si alguien copia el JSON, no obtiene las credenciales

### Migración automática

Si tienes un `neven-config.json` del formato anterior (v1), NEVEN lo migra automáticamente:

1. Detecta el formato v1
2. Mueve la API key al Credential Manager
3. Crea un perfil "migrated" con los datos existentes
4. Preserva las secciones legacy (WebView2, TaskPane)

### Archivos de configuración

| Archivo | Contenido |
|:---|:---|
| `C:\NEVEN\neven-config.json` | Perfiles AI/DB (sin credenciales) |
| `C:\NEVEN\prompts\*.txt` | Prompts editables |
| `C:\NEVEN\prompts\prompts_config.json` | Categorías de prompts |
| Windows Credential Manager | API keys y passwords |

---

## 13.12 API de Configuración (Endpoints HTTP)

El servidor HTTP expone endpoints para gestionar la configuración programáticamente.

### Perfiles de IA

| Método | Endpoint | Descripción |
|:---|:---|:---|
| GET | `/api/config/ai-profiles` | Lista todos los perfiles |
| GET | `/api/config/ai-profiles/{id}` | Obtener perfil específico |
| POST | `/api/config/ai-profiles` | Crear nuevo perfil |
| POST | `/api/config/ai-profiles/{id}` | Actualizar perfil |
| POST | `/api/config/ai-profiles/{id}/delete` | Eliminar perfil |
| POST | `/api/config/ai-profiles/{id}/activate` | Activar perfil |
| POST | `/api/config/ai-profiles/{id}/test` | Probar conexión |

### Conexiones de BD

| Método | Endpoint | Descripción |
|:---|:---|:---|
| GET | `/api/config/db-connections` | Lista todas las conexiones |
| GET | `/api/config/db-connections/{id}` | Obtener conexión específica |
| POST | `/api/config/db-connections` | Crear nueva conexión |
| POST | `/api/config/db-connections/{id}` | Actualizar conexión |
| POST | `/api/config/db-connections/{id}/delete` | Eliminar conexión |
| POST | `/api/config/db-connections/{id}/activate` | Activar conexión |
| POST | `/api/config/db-connections/{id}/test` | Probar conexión |

### Metadata y utilidades

| Método | Endpoint | Descripción |
|:---|:---|:---|
| GET | `/api/config/providers` | Lista proveedores AI y modelos |
| GET | `/api/config/db-types` | Lista tipos de BD y puertos default |
| GET | `/api/config/prompts` | Lista prompts por categoría |
| GET | `/api/config/prompts/{id}` | Obtener contenido de prompt |
| POST | `/api/config/prompts` | Guardar prompt (backup automático) |
| POST | `/api/config/reload` | Recargar configuración desde archivo |

### Ejemplo de uso con curl

```bash
# Listar perfiles de IA
curl http://localhost:5555/api/config/ai-profiles

# Activar un perfil
curl -X POST http://localhost:5555/api/config/ai-profiles/openai-default/activate

# Probar conexión de BD
curl -X POST http://localhost:5555/api/config/db-connections/postgres-local/test
```

---

*Documentacion actualizada: Agosto 2026*

*NEVEN Studio Standalone — Julio 2026*
*Universidad de Costa Rica — Tesis de Maestría*
