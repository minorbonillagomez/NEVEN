# Prevención de Artefactos de IA en Escritura Científica

> **Propósito:** Complementa el skill `scientific-writing` con reglas específicas para evitar que el texto generado sea detectado como producido por IA.
> **Versión:** 2.0 — Actualizado tras segunda evaluación forense

---

## 1. Referencias Bibliográficas (BibTeX)

### ❌ NO hacer — Artefactos detectables

```bibtex
@misc{PackageCompiler2023,
  note = {Used to generate NEVEN's Julia sysimage}  % ← Explicación contextual
}

@misc{Dua2019,
  note = {German Credit dataset: 1000 instances, 20 attributes, binary classification}
}

@misc{Plotly2023,
  note = {MIT License}  % ← Información de licencia
}

@misc{BERT2018,
  note = {Unmaintained since 2018}  % ← Estado del proyecto
}
```

### ✅ SÍ hacer — Solo campos estándar

```bibtex
@misc{PackageCompiler2023,
  author = {...},
  title = {...},
  year = {...},
  howpublished = {\url{...}}
  % Sin campo note
}
```

### Regla absoluta para campos `note`:

**ELIMINAR TODOS los campos `note` de las referencias bibliográficas.**

El campo `note` en BibTeX es el artefacto de IA más fácil de detectar. Un autor humano NUNCA incluye:
- Explicaciones de por qué la referencia es relevante
- Descripciones del contenido (datasets, herramientas)
- Información de licencias (MIT, GPL, BSD)
- Estado del proyecto (unmaintained, deprecated)
- Fechas de acceso (Accessed: YYYY-MM-DD)

---

## 2. Conteo y Números Consistentes

### ❌ NO hacer — "Alucinación de conteo"

```latex
% Sección 5: "...while adding 13 significant innovations (Section 1)"
% Sección 1: Lista solo 7 contribuciones

% Sección 6: "We identify four directions..."
% Luego lista 5 párrafos con \paragraph{}
```

### ✅ SÍ hacer — Verificación cruzada obligatoria

1. **Contar manualmente** cada lista numerada antes de escribir la frase introductoria
2. **Usar referencias vagas** cuando el número puede cambiar: "the contributions described in Section X" en lugar de "13 innovations"
3. **Verificar DESPUÉS de editar**: si agregas un \paragraph{} a Future Work, actualiza "four directions" → "five directions"

### Comando de verificación:
```bash
# Buscar discrepancias numéricas
grep -E "(We identify|we present|we describe) (three|four|five|six|seven)" sections/*.tex
# Luego contar manualmente los items que siguen
```

---

## 3. Puntuación en \paragraph{} (LaTeX)

### ❌ NO hacer — Doble punto

```latex
\paragraph{Configuration Service.}  % ← Punto adentro
% elsarticle agrega punto automático → "Configuration Service.."
```

### ✅ SÍ hacer

```latex
\paragraph{Configuration Service}  % Sin punto, elsarticle lo agrega
```

### Comando de corrección masiva:
```powershell
# Eliminar puntos dentro de \paragraph{}
$content -replace '\\paragraph\{([^}]*)\.\}', '\paragraph{$1}'
```

---

## 4. Em-Dashes (—) — Uso Excesivo

### ❌ NO hacer — Firma de GPT-4/Claude

Los LLMs abusan del em-dash seguido de participio (-ing):
```latex
...exposed as native formulas---enabling domain-specific teams...
...cross-references---completing the pipeline...
...Excel cell execution---ensuring that the REPL cannot bypass...
```

**Densidad sospechosa:** Más de 20 em-dashes en un paper de 30 páginas.

### ✅ SÍ hacer — Convertir a oraciones separadas

```latex
% ANTES:
...formulas---enabling domain-specific teams to build...

% DESPUÉS:
...formulas. This enables domain-specific teams to build...
```

### Patrones a reemplazar:
| Patrón IA | Alternativa humana |
|-----------|-------------------|
| `---enabling` | `. This enables` |
| `---ensuring` | `. This ensures` |
| `---completing` | `. This completes` |
| `---making` | `. This makes` |
| `---eliminating` | `. This eliminates` |

### Meta: Reducir em-dashes a ≤15 por paper.

---

## 5. Antítesis Simétrica ("Marketing Técnico")

### ❌ NO hacer — Pares arquetípicos

```latex
% Patrón detectado por evaluadores:
"The same infrastructure that serves an economics student running a 
linear regression also serves an aerospace engineer solving coupled 
differential equations."

"a professor can craft pedagogically appropriate prompts for students, 
while a risk analyst can write prompts aligned with regulatory language"

"accessible tools lack computational rigor, while rigorous tools lack 
accessibility"
```

### ✅ SÍ hacer — Descripción técnica directa

```latex
% ANTES:
"The same infrastructure that serves an economics student...also serves 
an aerospace engineer..."

% DESPUÉS:
"The same infrastructure supports both basic statistical analyses and 
advanced numerical simulations."
```

### Regla: Máximo 1 antítesis arquetípica por paper. Preferir descripciones técnicas sin personajes.

---

## 6. Estructuras Tripartitas

### ❌ NO hacer — Tricolons paralelos

```latex
"no compilation, no configuration editing, no administrative privileges"
"all interactive (zoom, filter, hover, drag), all updating when..."
```

### ✅ SÍ hacer — Variar la estructura

```latex
"without requiring compilation, configuration changes, or administrative 
privileges"
```

---

## 7. Checklist Pre-Publicación (Versión 2.0)

Antes de declarar un paper "listo para arXiv/journal":

```
□ grep "note.*=" references.bib → CERO campos note
□ Verificar que números en frases ("four directions") coincidan con items listados
□ grep "\\paragraph\{.*\.\}" → sin puntos dentro de paragraph
□ Contar em-dashes (---) → máximo 15-20 en todo el paper
□ Buscar patrones "student...engineer", "professor...analyst" → máximo 1
□ Buscar tricolons "no X, no Y, no Z" → máximo 2 en todo el paper
□ Verificar pseudocódigo compila/ejecuta en el lenguaje declarado
```

---

## 8. Señales de Edición Iterativa con IA

**Síntomas de turnos de conversación diferentes:**
- Números inconsistentes entre secciones (generadas en prompts separados)
- Calidad de prosa variable (algunas secciones más pulidas que otras)
- Referencias a secciones con números incorrectos
- Dobles puntos después de corregir `\paragraph{}`

**Prevención:** Después de editar una sección, buscar todas las referencias a ella en el documento y verificar que sigan siendo correctas.

---

## Aplicación

Este steering se activa automáticamente cuando se trabaja con archivos `.tex`, `.bib`, o se menciona "paper", "manuscript", "arXiv", "journal submission".

---

## Integración con Ciclo de Auditoría

Este steering es parte del pipeline de escritura científica con auditoría adversaria:

```
scientific-writing → Documento → auditor-forense-ia → ¿Confianza ≥90%?
       ▲                                                      │
       └──── [aplicar correcciones] ◀─────── NO ◀─────────────┤
                                                              │
                                              SÍ (o iter=10) ─┴─▶ FIN
```

**Parámetros de parada:**
- Confianza ≥ 90% → APROBADO
- Máximo 10 iteraciones → ESCALAR a revisión humana

**Skill relacionado:** `auditor-forense-ia` (evaluador adversario del ciclo)
