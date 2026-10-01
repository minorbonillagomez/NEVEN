# Cómo Procesar Libros para Expandir la Ontología NEVEN

Este documento explica cómo agregar conocimiento de libros PDF a la ontología de NEVEN.

---

## Resumen rápido

```
1. Colocar el PDF en ONTOLOGIA/{DOMINIO}/
2. Desde NEVEN Studio: Settings → Base de Conocimiento → Agregar Libro
3. Seleccionar el PDF y el dominio destino
4. Clic en "Procesar"
5. Esperar 2-5 minutos (según tamaño del libro)
6. Verificar las funciones extraídas
```

---

## Estructura de directorios

```
ONTOLOGIA/
├── LIBROS EXCEL/              # Funciones y técnicas de Excel
│   └── memory/ontology/
│       ├── schema.yaml        # Define tipos de entidades
│       └── graph.jsonl        # Entidades extraídas (append-only)
│
├── LIBROS ECONOMETRIA/        # Conceptos econométricos
│   └── memory/ontology/
│       └── graph.jsonl
│
├── LIBROS ANALISIS DE DATOS/  # Estadística y análisis
│   └── memory/ontology/
│       └── graph.jsonl
│
├── NEVEN/                     # Funciones propias de NEVEN
│   └── memory/ontology/
│       └── graph.jsonl
│
└── VBA/                       # Macros y VBA
    └── memory/ontology/
        └── graph.jsonl
```

---

## Método 1: Desde la UI (recomendado)

### Paso 1: Abrir NEVEN Studio
- Doble clic en `C:\NEVEN\TaskPane\NEVEN Studio.vbs`
- O desde Excel: pestaña NEVEN → botón "Studio"

### Paso 2: Ir a Settings → Base de Conocimiento
- Clic en el tab "Settings" (⚙️)
- Clic en sub-tab "Base de Conocimiento"

### Paso 3: Agregar libro
- Clic en botón "Agregar Libro"
- Seleccionar el archivo PDF
- Elegir el dominio destino (Excel, Econometría, Análisis de Datos, etc.)
- Clic en "Procesar"

### Paso 4: Esperar y verificar
- El procesamiento toma 2-5 minutos según el tamaño
- Al terminar, se muestra el número de entidades extraídas
- Las nuevas entidades aparecen en la lista del dominio

---

## Método 2: Vía API REST

### Endpoint
```
POST /api/ontology/process-book
Content-Type: application/json

{
  "file_path": "C:/ruta/al/libro.pdf",
  "domain": "LIBROS EXCEL",
  "options": {
    "max_pages": null,        // null = todas las páginas
    "chunk_size": 4000,       // caracteres por chunk
    "extract_images": false   // no procesar imágenes (futuro)
  }
}
```

### Respuesta
```json
{
  "status": "ok",
  "entities_created": 45,
  "relations_created": 12,
  "domain": "LIBROS EXCEL",
  "processing_time_seconds": 187
}
```

### Ejemplo con curl
```bash
curl -X POST http://localhost:5555/api/ontology/process-book \
  -H "Content-Type: application/json" \
  -d '{"file_path": "C:/Books/Excel_Bible.pdf", "domain": "LIBROS EXCEL"}'
```

---

## Método 3: Vía Chat con el Agente AI

Puedes pedirle al agente AI de NEVEN que procese un libro:

```
Usuario: Procesa el libro "Curso Práctico de Excel" que está en 
         ONTOLOGIA/LIBROS EXCEL/ y agrégalo a la ontología.

Agente:  Procesando el libro...
         [Extrae texto con PyMuPDF]
         [Divide en chunks]
         [Llama al LLM con prompt de extracción]
         [Genera JSONL y hace append a graph.jsonl]
         
         ✓ Procesado: 38 funciones extraídas, 15 técnicas, 8 mejores prácticas.
```

El agente usa el prompt en `C:\NEVEN\prompts\ontology_extraction.txt`.

---

## Formato de entidades (JSONL)

Cada línea en `graph.jsonl` es un JSON independiente:

### Crear entidad
```json
{"op": "create", "entity": {"id": "func_vlookup", "type": "ExcelFunction", "properties": {"name": "VLOOKUP", "category": "Lookup", "description": "Busca un valor en la primera columna..."}}}
```

### Crear relación
```json
{"op": "relate", "relation": {"type": "alternative_to", "from": "pattern_index_match", "to": "func_vlookup"}}
```

---

## Tipos de entidades por dominio

### Excel / Finanzas
| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `ExcelFunction` | Función de Excel | VLOOKUP, SUMIF |
| `Technique` | Técnica específica | Tablas Dinámicas |
| `Pattern` | Patrón de fórmulas | INDEX-MATCH |
| `BestPractice` | Mejor práctica | Evitar referencias circulares |
| `Shortcut` | Atajo de teclado | Ctrl+C |
| `CommonError` | Error frecuente | #N/A en VLOOKUP |

### Econometría / Estadística
| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `Concept` | Concepto teórico | Heteroscedasticidad |
| `Model` | Modelo econométrico | MCO, Panel Data |
| `Test` | Prueba estadística | Durbin-Watson |
| `Estimator` | Estimador | OLS, GLS |

### Programación (R/Python/Julia)
| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `Function` | Función del lenguaje | lm(), pd.read_csv() |
| `Package` | Paquete/librería | dplyr, pandas |
| `Pattern` | Patrón de código | Pipe operator |

---

## Convenciones de IDs

| Prefijo | Tipo | Ejemplo |
|---------|------|---------|
| `func_` | ExcelFunction, Function | `func_vlookup` |
| `tech_` | Technique | `tech_pivot_tables` |
| `pattern_` | Pattern | `pattern_index_match` |
| `bp_` | BestPractice | `bp_avoid_circular_refs` |
| `shortcut_` | Shortcut | `shortcut_copy` |
| `concept_` | Concept | `concept_heteroscedasticity` |
| `model_` | Model | `model_ols` |
| `test_` | Test | `test_durbin_watson` |

---

## Crear un nuevo dominio

Si el libro es de un tema nuevo (ej: Machine Learning):

### 1. Crear la estructura de directorios
```
ONTOLOGIA/
└── MACHINE LEARNING/
    └── memory/
        └── ontology/
            ├── schema.yaml    # Definir tipos de entidades
            └── graph.jsonl    # Vacío inicialmente
```

### 2. Crear el schema.yaml
Copiar de un dominio existente y adaptar los tipos de entidades.

### 3. Procesar el libro
Usar cualquiera de los métodos anteriores.

---

## Solución de problemas

### El procesamiento es muy lento
- Libros grandes (500+ páginas) pueden tomar 10+ minutos
- Considera procesar por capítulos si es posible
- Verifica que el perfil AI activo tenga suficiente cuota

### No se extraen entidades
- Verifica que el PDF tenga texto seleccionable (no escaneado)
- PDFs escaneados requieren OCR primero
- El LLM puede no entender el formato del libro

### Entidades duplicadas
- El sistema intenta evitar duplicados por ID
- Si hay duplicados, edita manualmente `graph.jsonl`
- Los IDs deben ser únicos dentro del dominio

### Error de conexión al LLM
- Verifica que el perfil AI esté activo en Settings → Motor IA
- Prueba la conexión con el botón "Probar Conexión"
- Si usas Ollama/LM Studio, verifica que estén corriendo

---

## Notas importantes

1. **Los libros deben ser tuyos** — Solo procesa libros que hayas comprado legalmente.

2. **Append-only** — El archivo `graph.jsonl` solo crece, no se modifica lo existente.

3. **Backup automático** — Antes de cada procesamiento se crea un backup del `graph.jsonl` actual.

4. **Sin conexión a internet para libros locales** — Si usas Ollama o LM Studio, todo el procesamiento es local.

---

*Documentación NEVEN v2.4+ — Sistema de Ontologías*
*Última actualización: Agosto 2026*
