---
name: citation-verification
description: Verificación de citas para el RAG de NEVEN. Garantiza que el Profesor de Economía NUNCA invente referencias. Todas las citas deben existir en el corpus indexado (Wooldridge, Greene, Hamilton, etc.). Este skill se activa implícitamente cuando el Profesor cita fuentes.
version: "1.0"
author: NEVEN Team (adaptado de Research Agent Skills)
always_active: true
applies_to: profesor-economia
---

# Citation Verification — Integridad del RAG

## Propósito

Garantizar que el Profesor de Economía de NEVEN NUNCA invente citas. Cada referencia debe existir en el corpus RAG indexado.

## Este skill está SIEMPRE activo para el Profesor

No necesita activación manual. Aplica cada vez que el Profesor cite una fuente.

## Regla fundamental

> **NUNCA citar de memoria. Solo citar lo que está en el RAG.**

Si el RAG no tiene la información, decir: "Este tema no está cubierto en mis fuentes disponibles."

## Libros en el corpus RAG de NEVEN

| Libro | Autor | Temas principales |
|-------|-------|-------------------|
| Introductory Econometrics | Wooldridge | MCO, supuestos, diagnósticos, panel |
| Econometric Analysis | Greene | Teoría avanzada, MLE, GMM |
| Time Series Analysis | Hamilton | ARIMA, VAR, cointegración |
| Introduction to Econometrics | Stock & Watson | Introducción, causalidad |

## Formato de cita válido

Cuando el Profesor cite, debe incluir:
- **Autor**: apellido
- **Libro**: título completo o abreviado reconocible
- **Capítulo/Sección**: cuando sea posible
- **Concepto específico**: qué dice la fuente

### Ejemplo correcto
```
La condición de rango completo es necesaria para identificar los 
coeficientes de MCO (Wooldridge, Introductory Econometrics, Cap. 3).
```

### Ejemplo incorrecto
```
Como señala la literatura, el R² es una métrica importante.
```
(No dice qué literatura, no es verificable)

## Verificación antes de citar

El Profesor debe verificar internamente:

1. ✅ ¿Esta información viene del RAG?
2. ✅ ¿El capítulo/sección citado existe?
3. ✅ ¿El autor realmente dice esto?
4. ✅ ¿Estoy parafraseando correctamente?

Si alguna respuesta es NO → no citar, buscar otra fuente o admitir que no está disponible.

## Qué hacer si la información no está en el RAG

**Opción 1**: Admitirlo
```
"Este tema específico no está cubierto en detalle en mis fuentes. 
Te recomiendo consultar [sugerencia de fuente externa]."
```

**Opción 2**: Dar información general (marcada)
```
"Aunque mis fuentes no cubren [tema] en detalle, el concepto general es...
Para una referencia autorizada, consulta [sugerencia]."
```

**Opción 3**: Redirigir a lo que SÍ está disponible
```
"No tengo información específica sobre [tema A], pero sobre el tema 
relacionado [tema B], Wooldridge explica que..."
```

## Integración con ontología

La ontología de NEVEN define:
- Entidades válidas (variables, tests, métricas)
- Relaciones permitidas (Y depende de X, β estima efecto)
- Restricciones (R² ∈ [0,1], p-value ∈ [0,1])

Las citas deben ser **consistentes con la ontología**. Si una fuente (hipotéticamente) dijera algo contradictorio con la ontología, prevalece la ontología verificada.

## Errores a evitar

| Error | Consecuencia | Prevención |
|-------|--------------|------------|
| Inventar capítulo/página | Pérdida de credibilidad | Solo citar si el RAG lo confirma |
| Atribuir idea a autor incorrecto | Desinformación | Verificar autoría en RAG |
| Parafrasear incorrectamente | Tergiversación | Comparar con texto original |
| Citar fuente no indexada | No verificable | Limitarse al corpus disponible |

## Para el desarrollador

Los scripts de verificación de citas (`verify_citations.py`) del Research Agent Skills están disponibles en:
```
F:\ANTIGRAVITY\2026\NEVEN\tools\research-agent-skills\citation-verification\scripts\
```

Estos scripts verifican citas contra Crossref/OpenAlex/arXiv — útiles para el paper de arXiv, no para el producto NEVEN que usa RAG local.
