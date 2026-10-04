---
inclusion: fileMatch
fileMatchPattern: "**/ontologia/**/*.yaml"
---

# Reglas para archivos YAML de Ontología NEVEN

> **CRÍTICO:** Los errores de sintaxis YAML impiden que el RAG cargue entidades correctamente.
> Un archivo con errores resulta en `0 entidades` cargadas de ese archivo.

## Errores comunes y cómo evitarlos

### 1. Escapes inválidos en comillas dobles

YAML interpreta `\` seguido de ciertos caracteres como secuencias de escape.

**❌ MAL — Escapes inválidos:**
```yaml
# \p, \I, \| no son escapes válidos en YAML
nombre_pipe: "\\\\.\pipe\\RJ2XCL2"        # \p = error
comando: ".\Install-NEVEN.ps1"            # \I = error  
verificar: "grep 'Build/\|Dist/'"         # \| = error
```

**✅ BIEN — Usar comillas simples:**
```yaml
# Las comillas simples NO interpretan escapes
nombre_pipe: '\\\\.\\pipe\\RJ2XCL2'
comando: '.\Install-NEVEN.ps1'
verificar: 'grep "Build/\|Dist/"'
```

**✅ ALTERNATIVA — Bloque literal:**
```yaml
verificar: |
  grep 'Build/\|Dist/'
```

### 2. Falta de espacio después de dos puntos

**❌ MAL:**
```yaml
"/api/endpoint":"descripcion"     # Falta espacio después de :
```

**✅ BIEN:**
```yaml
"/api/endpoint": "descripcion"    # Espacio después de :
```

### 3. Items de lista mal formateados

**❌ MAL — Múltiples claves en una línea:**
```yaml
pipes:
  - nombre: "primario"   descripcion: "canal principal"
```

**✅ BIEN — Estructura anidada:**
```yaml
pipes:
  - nombre: "primario"
    descripcion: "canal principal"
```

### 4. Bloques huérfanos

**❌ MAL — Contenido sin contexto:**
```yaml
    version: "2010"

        tipo: integer          # ¿A qué pertenece esto?
        requerido: true
```

**✅ BIEN — Todo contenido debe estar anidado correctamente:**
```yaml
    version: "2010"

  - id: NUEVA_FUNCION
    parametros:
      - nombre: "param1"
        tipo: integer
        requerido: true
```

### 5. Caracteres especiales en valores

**Caracteres que requieren comillas:**
- `:` dos puntos
- `#` hash (comentario)
- `[` `]` corchetes
- `{` `}` llaves
- `&` `*` anclas
- `!` tag
- `|` `>` bloques literales
- `'` `"` comillas
- `%` directiva
- `@` `` ` `` reservados

**✅ REGLA:** Si el valor contiene cualquiera de estos, usar comillas simples.

## Regla de dominios

Los dominios en ontologías deben coincidir **exactamente** con los usados en la base de datos RAG.

**Dominios válidos (español):**
- `econometria` (NO `econometrics`)
- `estadistica` (NO `statistics`)
- `excel`
- `r`
- `python`
- `julia`
- `machine_learning`
- `series_tiempo`

## Validación obligatoria

**Antes de guardar cualquier archivo YAML de ontología:**

```powershell
python -c "import yaml; yaml.safe_load(open('archivo.yaml', encoding='utf-8')); print('OK')"
```

Si da error, **NO guardar** hasta corregirlo.

## Checklist para nuevas ontologías

```
□ Usar comillas simples para paths de Windows (contienen \)
□ Usar comillas simples para comandos shell (pueden tener |, &, etc.)
□ Espacio después de cada : en mappings
□ Cada item de lista (-) en su propia línea
□ Indentación consistente (2 espacios)
□ Dominios en español (econometria, estadistica)
□ Validar con yaml.safe_load() antes de guardar
□ Copiar a producción: C:\NEVEN\docs\ontologia\
```
