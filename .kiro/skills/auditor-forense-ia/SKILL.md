# Auditor Forense IA

## Propósito

Evalúa documentos técnicos y académicos mediante análisis forense estructural, bibliográfico, sintáctico y de consistencia interna para detectar rastros de generación o procesamiento con modelos de lenguaje (LLMs) y emitir un dictamen fundamentado.

Este skill opera como **evaluador adversario** en un ciclo iterativo de mejora de documentos científicos.

---

## Restricciones de Salida

> **CRÍTICO:** Este skill tiene restricciones específicas sobre el formato de salida.

### ❌ NO usar artifacts

**El dictamen NO debe generarse como artifact.** Razones:

1. **Eficiencia:** Crear artifacts consume tiempo adicional innecesario
2. **Contexto:** El dictamen debe permanecer en el flujo de conversación para referencia inmediata
3. **Iteración:** En ciclos múltiples, los artifacts fragmentan el historial de auditoría
4. **Automatización:** El texto plano es más fácil de procesar programáticamente

### ✅ Formato correcto

El dictamen se emite como **texto markdown directo en la respuesta**, con la estructura definida en el Paso 6.

### Ejemplo

```
❌ INCORRECTO:
   [Crear artifact "Dictamen de Auditoría"]

✅ CORRECTO:
   # Dictamen de Auditoría Forense IA
   ## Veredicto Ejecutivo
   - **Estado:** APROBADO
   - **Confianza:** 97%
   ...
```

---

## Entrada del Auditor

> **IMPORTANTE:** El auditor trabaja directamente con archivos fuente (`.tex`, `.bib`), NO con PDFs compilados.

### Archivos requeridos

| Tipo | Archivo | Propósito |
|------|---------|-----------|
| **Obligatorio** | `*.tex` | Secciones del documento (abstract, intro, etc.) |
| **Obligatorio** | `references.bib` o `*.bib` | Referencias bibliográficas |
| **Opcional** | `main.tex` | Archivo principal (para verificar includes) |

### Ventajas de auditar código fuente vs PDF

| Aspecto | PDF | Archivos .tex/.bib |
|---------|-----|-------------------|
| **Tiempo** | Compilación + parseo | Instantáneo |
| **Precisión** | Puede perder info (ligatures) | Código exacto |
| **Patrones** | Difícil detectar `\paragraph{.}` | Visible directamente |
| **Correcciones** | Mapear de vuelta al .tex | Ya estás en el archivo |
| **Automatización** | Requiere OCR | Grep, regex directo |

### Comandos de verificación rápida

```powershell
# Contar em-dashes en archivos .tex
Get-Content "sections/*.tex" | Select-String -Pattern "---" -AllMatches | Measure-Object

# Buscar campos note en .bib
Select-String -Path "*.bib" -Pattern "note\s*="

# Buscar dobles puntos en \paragraph{}
Select-String -Path "sections/*.tex" -Pattern "\\paragraph\{[^}]*\.\}"

# Verificar consistencia numérica (ej: "four directions")
Select-String -Path "sections/*.tex" -Pattern "(three|four|five|six|seven) (directions|contributions|steps)"
```

---

## Cuándo Usar

- Cuando el usuario solicite evaluar si un documento, paper, tesis o reporte fue generado o procesado con IA.
- Antes de otorgar un "visto bueno" o aprobación a un entregable técnico o académico.
- Como paso final en el pipeline de escritura científica (después de `scientific-writing` y `unslop-academic-writing`).
- Cuando se requiera un reporte justificativo detallado para descartar o solicitar correcciones en un manuscrito sospechoso.

---

## Parámetros de Parada del Ciclo

El ciclo de revisión iterativa termina cuando se cumple **cualquiera** de estas condiciones:

| Condición | Valor | Resultado |
|-----------|-------|-----------|
| **Nivel de confianza** | ≥ 90% | ✅ APROBADO — Documento listo para publicación |
| **Máximo de iteraciones** | 10 | ⚠️ ESCALADO — Requiere revisión humana manual |
| **Evidencias críticas irresolubles** | Después de 3 intentos con misma evidencia | 🛑 BLOQUEADO — Problema estructural requiere reescritura |

### Fórmula de Confianza

```
Confianza = 100% - (Σ penalizaciones)

Penalizaciones:
- Evidencia crítica (bibliografía, conteo, código): -15% cada una
- Artefacto tipográfico (doble punto, em-dash excesivo): -5% cada uno
- Huella estilística (antítesis, tricolon): -3% cada una
- Inconsistencia menor: -2% cada una
```

### Umbrales de Decisión

| Confianza | Veredicto | Acción |
|-----------|-----------|--------|
| 90-100% | APROBADO | Publicar |
| 70-89% | SOSPECHA MEDIA | Otra iteración de corrección |
| 50-69% | SOSPECHA ALTA | Revisión profunda requerida |
| 0-49% | DESCARTADO | Reescritura completa o rechazo |

---

## Procedimiento de Auditoría

### Paso 0: Lectura de Archivos Fuente (NUEVO)

**Antes de cualquier análisis:**

1. Leer `references.bib` completo
2. Leer todos los archivos `sections/*.tex` 
3. Opcionalmente leer `main.tex` para entender la estructura

**NO compilar PDF** — La auditoría se hace sobre código fuente.

### Paso 1: Inspección Forense de Bibliografía (Alta Certeza)

Analiza directamente el archivo `.bib`:

**Buscar con grep/regex:**
```powershell
# Campos note (CRÍTICO)
Select-String -Path "*.bib" -Pattern "note\s*=\s*\{" 

# Fechas de acceso repetidas
Select-String -Path "*.bib" -Pattern "Accessed:"
```

**Patrones problemáticos:**
- `note = {Used to generate...}` — Explicación contextual
- `note = {MIT License}` — Información de licencia
- `note = {Commercial product}` — Descripción de herramienta
- `note = {Accessed: 2024-01-15}` — Fecha mecánica repetida

**Penalización:** -15% por cada hallazgo confirmado

### Paso 2: Análisis de Consistencia Numérica

Verifica coherencia entre texto y elementos enumerados:

**Buscar con grep/regex:**
```powershell
# Frases con números
Select-String -Path "sections/*.tex" -Pattern "(three|four|five|six|seven|eight|nine|ten) (directions|contributions|steps|findings|aspects)"

# Contar items en enumerate después de cada match
```

**Verificar manualmente:**
- "identificamos cuatro direcciones" → Contar `\paragraph{}` o `\item` que siguen
- "13 innovaciones en Sección 1" → Contar items en Sección 1
- Sumatorias en tablas vs totales declarados

**Penalización:** -15% por cada desajuste numérico

### Paso 3: Auditoría de Código y Pseudocódigo

Inspecciona bloques `lstlisting`, `algorithm`, y ecuaciones:

**Buscar en archivos .tex:**
```powershell
# Extraer bloques de código
Select-String -Path "sections/*.tex" -Pattern "\\begin\{lstlisting\}" -Context 0,20
```

**Verificar:**
- Sintaxis válida del lenguaje declarado (R, Julia, Python)
- Variables definidas antes de uso
- Funciones que realmente existen en el lenguaje
- Sin palabras reservadas inventadas (`define` en R, `set attr` en Julia)

**Penalización:** -15% por cada alucinación de código

### Paso 4: Detección de Artefactos Tipográficos

**Buscar con grep/regex:**
```powershell
# Doble punto en \paragraph{}
Select-String -Path "sections/*.tex" -Pattern "\\paragraph\{[^}]*\.\}"

# Contar em-dashes
(Get-Content "sections/*.tex" | Select-String -Pattern "---" -AllMatches).Matches.Count

# Patrones ---enabling, ---ensuring
Select-String -Path "sections/*.tex" -Pattern "---[a-z]+ing"
```

**Umbrales:**
- Em-dashes: ≤20 para paper de 30 páginas (normal)
- Em-dashes: >20 = sospechoso
- Dobles em-dashes (`text---parenthetical---text`): siempre sospechoso

**Penalización:** -5% por cada tipo de artefacto presente

### Paso 5: Evaluación de Patrones Retóricos

**Buscar con grep/regex:**
```powershell
# Antítesis arquetípicas
Select-String -Path "sections/*.tex" -Pattern "(student|professor|analyst|engineer).*\.\.\.(student|professor|analyst|engineer)"

# Aforismos de cierre
Select-String -Path "sections/*.tex" -Pattern "not the problem---"
Select-String -Path "sections/*.tex" -Pattern "is not X---Y is"

# Tricolons
Select-String -Path "sections/*.tex" -Pattern "all [^,]+, all [^,]+, all"
```

**Patrones problemáticos:**
- "economics student...aerospace engineer" — Antítesis arquetípica
- "The tool is not the problem—" — Aforismo de cierre
- "all interactive, all updating, all computed" — Tricolon paralelo

**Penalización:** -3% por cada patrón identificado

### Paso 6: Generación del Dictamen

Producir reporte estructurado con:

```markdown
# Dictamen de Auditoría Forense IA

## Datos del Documento
- **Directorio:** [ruta a archivos .tex]
- **Archivos analizados:** [lista de .tex y .bib]
- **Iteración:** [N de 10]
- **Fecha:** [YYYY-MM-DD]

## Veredicto Ejecutivo
- **Estado:** [APROBADO / SOSPECHA MEDIA / SOSPECHA ALTA / DESCARTADO]
- **Nivel de Confianza:** [X]%
- **Acción Requerida:** [Publicar / Corregir / Reescribir / Escalar a humano]

## Cálculo de Confianza
| Categoría | Hallazgos | Penalización |
|-----------|-----------|--------------|
| Bibliografía | [N] | -[X]% |
| Consistencia numérica | [N] | -[X]% |
| Código/pseudocódigo | [N] | -[X]% |
| Artefactos tipográficos | [N] | -[X]% |
| Patrones retóricos | [N] | -[X]% |
| **TOTAL** | | **[100-X]%** |

## Evidencias Detalladas
1. **[Archivo:línea]**: "[cita textual]" — [explicación]
2. ...

## Correcciones Requeridas para Siguiente Iteración
- [ ] [Corrección específica con archivo y línea]
- [ ] [Corrección específica con archivo y línea]
- ...

## Historial de Iteraciones
| Iter | Confianza | Hallazgos | Estado |
|------|-----------|-----------|--------|
| 1 | X% | N | [estado] |
| 2 | X% | N | [estado] |
| ... | | | |
```

### Paso 7: Compilación de Verificación (OPCIONAL)

**Solo después de que el dictamen indique APROBADO:**

```powershell
# Compilar para verificar que no hay errores de sintaxis LaTeX
pdflatex -interaction=nonstopmode main.tex
```

La compilación NO es parte de la auditoría, solo verifica que las correcciones no introdujeron errores de sintaxis.

---

## Flujo Optimizado (sin PDF)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ITERACIÓN N (max 10)                        │
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │ Archivos .tex    │───▶│ auditor-         │───▶│ Dictamen     │  │
│  │ + .bib           │    │ forense-ia       │    │ con %        │  │
│  │ (código fuente)  │    │ (análisis regex) │    │ confianza    │  │
│  └──────────────────┘    └──────────────────┘    └──────┬───────┘  │
│           ▲                                             │          │
│           │                                             ▼          │
│           │         ┌─────────────────────────────────────┐        │
│           │         │  Confianza ≥ 90%?                   │        │
│           │         │  O iteración = 10?                  │        │
│           │         └──────────────┬──────────────────────┘        │
│           │                        │                               │
│           │         NO (conf<90%)  │  SÍ (conf≥90%)                │
│           │         iter<10        │  O iter=10                    │
│           │◀───────────────────────┘         │                     │
│           │                                  ▼                     │
│  ┌────────┴─────────┐              ┌─────────────────────┐         │
│  │ Aplicar          │              │ pdflatex (opcional) │         │
│  │ correcciones     │              │ + PUBLICAR          │         │
│  │ a archivos .tex  │              └─────────────────────┘         │
│  └──────────────────┘                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Ganancia de tiempo:** ~30-60 segundos por iteración (sin compilación PDF)

---

## Reglas de Operación

### Gotchas

1. **No compilar PDF durante la auditoría**: Solo al final, como verificación opcional.

2. **Evitar acusaciones sin cita textual**: Cada hallazgo debe incluir archivo, línea, y cita literal.

3. **El auditor no corrige, solo reporta**: La corrección la hace el skill de escritura en la siguiente iteración.

4. **Severidad progresiva**: En iteraciones tempranas, ser más tolerante con huellas estilísticas; en iteraciones tardías (>5), ser estricto.

5. **Usar grep/regex para búsquedas**: Más rápido y preciso que lectura manual.

### Límites de Competencia

Este skill **NO**:
- Evalúa la calidad científica del contenido
- Verifica la veracidad de los datos o resultados
- Reemplaza la revisión por pares
- Garantiza aceptación en una revista
- Compila PDFs (solo verifica código fuente)

Este skill **SÍ**:
- Detecta rastros de generación/procesamiento por IA
- Identifica inconsistencias estructurales
- Proporciona criterios objetivos de limpieza
- Documenta el proceso de auditoría
- Trabaja directamente con archivos .tex/.bib

---

## Ejemplo de Uso

```
Usuario: Evalúa este paper para detectar si fue procesado con IA
         [proporciona ruta a directorio con .tex y .bib]

Auditor: [Lee archivos .tex y .bib directamente]
         [Ejecuta pasos 1-6 con grep/regex]

         # Dictamen de Auditoría Forense IA
         
         ## Datos del Documento
         - **Directorio:** src/docs/Paper/
         - **Archivos:** references.bib, sections/*.tex (7 archivos)
         
         ## Veredicto Ejecutivo
         - **Estado:** SOSPECHA MEDIA
         - **Nivel de Confianza:** 72%
         - **Iteración:** 1 de 10
         
         ## Hallazgos
         - references.bib:45: `note = {MIT License}` (-15%)
         - 06_conclusion.tex:23: "four directions" pero hay 5 \paragraph{} (-15%)
         - Em-dashes: 45 encontrados (>20 límite) (-5%)
         
         ## Correcciones Requeridas
         1. references.bib:45 — Eliminar campo `note`
         2. 06_conclusion.tex:23 — Cambiar "four" → "five"
         3. Reducir em-dashes a ≤20

Usuario: [Aplica correcciones a los archivos .tex]
         Evalúa nuevamente

Auditor: [Re-lee archivos .tex modificados]
         [Ejecuta pasos 1-6]

         ## Veredicto Ejecutivo
         - **Estado:** APROBADO
         - **Nivel de Confianza:** 94%
         - **Iteración:** 2 de 10
         
         ✅ Documento listo para publicación
         
         [Opcional: pdflatex main.tex para verificar sintaxis]
```

---

## Skills Relacionados

- `scientific-writing`: Redacción de manuscritos científicos con trazabilidad de evidencia
- `unslop-academic-writing`: Eliminación de patrones de IA ("slop") en prosa académica
- `citation-verification`: Verificación de referencias bibliográficas
- `ai-artifact-prevention` (steering): Reglas preventivas para evitar artefactos de IA
