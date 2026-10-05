---
id: ontologias-excel-consultant
title: "Capitulo 14 - Ontologías y Excel Consultant"
sidebar_label: 14. Ontologías y Excel Consultant
sidebar_position: 14
---

# Capitulo 14: Sistema de Ontologías y Excel Consultant

**Disponible desde:** Setiembre 2026

NEVEN incluye un sistema de conocimiento estructurado basado en **ontologías dinámicas** y un modo especializado de IA llamado **Excel Consultant** que permite auditar, documentar y optimizar hojas de cálculo.

---

## 14.1 Arquitectura del conocimiento

```
┌─────────────────────────────────────────────────────────────┐
│                     ONTOLOGIA/                              │
│  ┌──────────────────┬──────────────────┬──────────────────┐ │
│  │  LIBROS EXCEL    │     NEVEN        │     LIBROS       │ │
│  │                  │                  │                  │ │
│  │ • 113 funciones  │ • 40+ funciones  │ • Econometría    │ │
│  │   nativas Excel  │   R/Julia/Python │   teórica        │ │
│  │ • CFI, Curso     │ • Dinámico       │ • Wooldridge     │ │
│  │   Práctico, etc. │                  │   Greene, etc.   │ │
│  └──────────────────┴──────────────────┴──────────────────┘ │
│                            │                                │
│                            ▼                                │
│                    graph.jsonl                              │
│                  (append-only)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 14.2 Ubicación de ontologías

Las ontologías viven **fuera del repositorio git** para permitir personalización por usuario:

| Dominio | Ubicación | Contenido |
|:---|:---|:---|
| Excel nativo | `ONTOLOGIA/LIBROS EXCEL/` | 113 funciones de Excel |
| NEVEN | `ONTOLOGIA/NEVEN/` | Funciones R/Julia/Python agregadas |
| Econometría | `ONTOLOGIA/LIBROS/` | Conceptos teóricos |

Cada dominio tiene:
- `memory/ontology/schema.yaml` — define tipos de entidades
- `memory/ontology/graph.jsonl` — grafo de conocimiento

---

## 14.3 Formato graph.jsonl

Una línea = una operación. Append-only, nunca modificar.

**Crear entidad:**
```json
{"op": "create", "entity": {"id": "func_vlookup", "type": "ExcelFunction", "properties": {"name": "BUSCARV", "category": "Búsqueda", "description": "Busca un valor en la primera columna..."}}}
```

**Crear relación:**
```json
{"op": "relate", "from": "func_vlookup", "rel": "part_of", "to": "domain_lookup"}
```

---

## 14.4 Excel Consultant

El Excel Consultant es un modo especializado de IA que analiza hojas de cálculo.

### Activación

1. En NEVEN Studio → pestaña **AI**
2. Clic en **"Analizar Hoja"**
3. El agente recibe metadatos de la hoja activa

### Capacidades

| Función | Descripción |
|:---|:---|
| **Auditoría** | Detecta errores, fórmulas frágiles, hardcoding |
| **Documentación** | Explica qué hace cada sección de la hoja |
| **Optimización** | Sugiere fórmulas más eficientes |
| **Educación** | Enseña sobre funciones desconocidas |
| **Creación** | Escribe funciones R/Julia/Python nuevas |

### Ejemplo de uso

```
Usuario: "¿Qué hace esta hoja?"

Excel Consultant:
Esta hoja calcula un presupuesto mensual con:
- Columna A: Categorías de gastos
- Columna B: Presupuesto estimado (SUMA de B2:B15)
- Columna C: Gasto real (SUMAR.SI.CONJUNTO...)
- Columna D: Varianza = B-C

Problemas detectados:
1. C5 tiene un valor fijo ($1500) en lugar de fórmula
2. D3 usa referencia absoluta incorrecta ($B$3 debería ser B3)

Sugerencias:
- Considerar SUMIFS en lugar de múltiples SUMAR.SI
```

---

## 14.5 Expansión de ontologías

El usuario puede agregar libros PDF para expandir el conocimiento:

1. Colocar PDF en `ONTOLOGIA/{dominio}/`
2. En NEVEN Studio, escribir: *"procesa el libro CursoPractico.pdf"*
3. El agente extrae funciones y las agrega a `graph.jsonl`

### Libros procesados (Agosto 2026)

| Libro | Funciones extraídas |
|:---|:---|
| CFI Excel Book.pdf | 45 funciones |
| Curso Práctico Excel.pdf | 38 funciones |
| Excel Bible 2021.pdf | 30 funciones |

---

## 14.6 Ontología dinámica

Cuando el agente crea una nueva función para el usuario, automáticamente:

1. Guarda el archivo en `libreria/{R|JULIA|PYTHON}/`
2. Agrega la entidad a `ONTOLOGIA/NEVEN/memory/ontology/graph.jsonl`
3. Crea relaciones con categorías y conceptos relacionados

Esto significa que **la ontología crece con el uso**.

---

## 14.7 Visualizaciones Interactivas

NEVEN incluye visualizadores interactivos para explorar las ontologías de forma visual. Estas herramientas permiten entender las relaciones entre conceptos, funciones y métodos.

### Exploradores disponibles

| Visualización | Descripción | Ubicación |
|:---|:---|:---|
| **Grafo 2D** | Red interactiva con zoom, pan y búsqueda | `docs/ontologia/econometrics/graph_visualization.html` |
| **Grafo 3D** | Visualización tridimensional rotable | `docs/ontologia/econometrics/graph_visualization_3d.html` |

### Cómo abrir las visualizaciones

**Desde Windows Explorer:**
1. Navegar a `C:\NEVEN\docs\ontologia\econometrics\`
2. Doble clic en `graph_visualization.html`
3. Se abre en el navegador predeterminado

**Desde NEVEN Studio:**
1. Pestaña **Ayuda** → **Explorar Ontología**
2. Seleccionar dominio (Econometría, Excel, NEVEN)

### Características del explorador 2D

- **Búsqueda:** Filtrar nodos por nombre o tipo
- **Zoom:** Rueda del mouse o botones +/-
- **Pan:** Arrastrar el fondo
- **Selección:** Click en nodo muestra detalles
- **Colores por tipo:**
  - Azul: Métodos estadísticos
  - Naranja: Conceptos teóricos
  - Rojo: Supuestos
  - Verde: Paquetes R
  - Morado: Frameworks

### Características del explorador 3D

- **Rotación:** Arrastrar para rotar la vista
- **Zoom:** Rueda del mouse
- **Profundidad:** Las relaciones se ven en 3 dimensiones
- **Clusters:** Nodos relacionados se agrupan visualmente

### Ejemplo: Explorando regresión lineal

1. Abrir `graph_visualization.html`
2. Buscar "linear regression"
3. Ver conexiones a:
   - Supuestos (homoscedasticidad, normalidad)
   - Métodos relacionados (OLS, GLS, WLS)
   - Paquetes R que lo implementan (stats, lm)
   - Conceptos teóricos (MCO, estimadores)

---

## 14.8 Troubleshooting

**El Excel Consultant no reconoce funciones:**
- Verificar que `graph.jsonl` existe en el dominio correcto
- Ejecutar validación: cada línea debe ser JSON válido

**Error al procesar libros:**
- Solo se procesan PDFs (no DOCX, EPUB)
- El agente parafrasea contenido (compliance de derechos de autor)

**Funciones nuevas no aparecen en la ontología:**
- Verificar que el agente tenga acceso de escritura a `ONTOLOGIA/`
- Revisar si hay errores de JSON en la última línea de `graph.jsonl`

---

## 14.8 Tab Conocimiento — Gestión de Ontologías (UI)

**Disponible desde:** Agosto 2026

El Tab Conocimiento en Settings proporciona una interfaz visual para gestionar las ontologías de NEVEN sin necesidad de editar archivos manualmente.

### Acceso

```
NEVEN Studio → Settings → Conocimiento
```

### Funcionalidades

| Sección | Descripción |
|:---|:---|
| **Dominios** | Lista de dominios de conocimiento disponibles |
| **Libros procesados** | Libros PDF que alimentan cada dominio |
| **Procesar libro** | Formulario para agregar nuevos PDFs |
| **Crear dominio** | Crear un nuevo dominio personalizado |

### Lista de dominios

Muestra los dominios existentes con estadísticas:

| Dominio | Entidades | Libros |
|:---|:---:|:---:|
| excel | 183 | 6 |
| econometrics | 199 | 14 |
| neven | 45 | — |

Al seleccionar un dominio, se muestran los libros que lo alimentan.

### Procesar nuevo libro

Para agregar un libro PDF a la base de conocimiento:

```
1. Settings → Conocimiento
2. Seleccionar dominio destino (o crear uno nuevo)
3. Ingresar ruta del PDF
4. Clic "Procesar Libro"
5. Esperar extracción (barra de progreso)
6. Ver resumen: funciones extraídas, entidades creadas
```

El procesamiento:
1. Extrae texto del PDF con PyMuPDF
2. Divide en chunks manejables
3. Envía al LLM activo con prompt de extracción
4. Parsea respuesta → genera entidades JSONL
5. Hace append a `graph.jsonl` del dominio

### Crear dominio personalizado

Para crear un dominio nuevo (ej: `machine_learning`, `finance`):

```
1. Settings → Conocimiento
2. En selector de dominio, elegir "Crear nuevo..."
3. Ingresar ID del dominio (snake_case)
4. Ingresar nombre descriptivo
5. Clic "Crear Dominio"
```

Esto crea la estructura:

```
C:\NEVEN\ontology\{id}\
  └── memory\
      └── ontology\
          ├── schema.yaml
          └── graph.jsonl

ONTOLOGIA\LIBROS {NAME}\
  └── memory\
      └── ontology\
          ├── schema.yaml
          └── graph.jsonl
```

### Endpoints relacionados

| Método | Endpoint | Descripción |
|:---|:---|:---|
| GET | `/api/ontology/domains` | Lista dominios con estadísticas |
| GET | `/api/ontology/books?domain=X` | Lista libros de un dominio |
| POST | `/api/ontology/process-book` | Procesar PDF nuevo |
| POST | `/api/ontology/create-domain` | Crear dominio nuevo |

### Ejemplo de respuesta `/api/ontology/domains`

```json
{
  "domains": [
    {
      "id": "excel",
      "name": "Excel Functions",
      "entity_count": 183,
      "book_count": 6,
      "path": "C:\\NEVEN\\ontology\\excel"
    },
    {
      "id": "econometrics",
      "name": "Econometrics",
      "entity_count": 199,
      "book_count": 14,
      "path": "ONTOLOGIA\\LIBROS ECONOMETRICS"
    }
  ]
}
```

---

*Documentación actualizada: Agosto 2026*
