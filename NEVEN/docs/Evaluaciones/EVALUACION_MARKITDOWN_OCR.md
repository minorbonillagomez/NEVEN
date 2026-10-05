# Evaluación: markitdown-ocr para NEVEN RAG

**Fecha:** 2026-08-19
**Evaluador:** Kiro

## Resumen

`markitdown-ocr` es un plugin para MarkItDown que extrae texto de imágenes embebidas en PDFs, DOCX, PPTX y XLSX usando LLM Vision (GPT-4o o compatible).

## Características

| Característica | Detalle |
|----------------|---------|
| **Instalación** | `pip install markitdown-ocr` |
| **Dependencia** | markitdown>=0.1.8,<0.2.0 |
| **Requiere** | Cliente OpenAI-compatible (openai, AzureOpenAI, etc.) |
| **Formatos** | PDF, DOCX, PPTX, XLSX con imágenes embebidas |

## Funcionamiento

1. El plugin se registra automáticamente con `enable_plugins=True`
2. Detecta imágenes embebidas en documentos
3. Envía cada imagen al LLM Vision con prompt de extracción
4. Inserta el texto extraído en el Markdown resultante
5. Para PDFs escaneados: renderiza página completa a 300 DPI y la envía al LLM

## Ventajas para NEVEN

| Ventaja | Impacto |
|---------|---------|
| PDFs escaneados | Libros antiguos, papers escaneados serían indexables |
| Diagramas con texto | Fórmulas en imágenes, diagramas de flujo |
| Capturas de pantalla | Documentación con screenshots de Excel |
| Sin dependencias binarias | No requiere Tesseract ni otras libs OCR locales |

## Desventajas / Consideraciones

| Desventaja | Impacto |
|------------|---------|
| **Requiere API LLM** | No funciona offline |
| **Costo** | Cada imagen = llamada a GPT-4o (~$0.01-0.03) |
| **Latencia** | Segundos por imagen (vs milisegundos con OCR local) |
| **Privacidad** | Imágenes enviadas a servidor externo |

## Compatibilidad con LMStudio

LMStudio puede exponer una API OpenAI-compatible, pero:

1. **Vision models locales son grandes** — LLaVA 13B+ requiere mucha VRAM
2. **Calidad variable** — modelos locales menos precisos que GPT-4o
3. **No todos los modelos locales soportan vision**

### Configuración teórica con LMStudio

```python
from openai import OpenAI

# LMStudio expone API en localhost:1234
lm_client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"  # No se valida
)

md = MarkItDown(
    enable_plugins=True,
    llm_client=lm_client,
    llm_model="local-model-with-vision",  # Debe soportar vision
)
```

## Alternativas locales (sin LLM)

| Alternativa | Pros | Contras |
|-------------|------|---------|
| **Tesseract OCR** | Gratis, local, rápido | Requiere instalación binaria |
| **EasyOCR** | Python puro, GPU opcional | Modelos grandes (~1GB) |
| **PaddleOCR** | Alta precisión | Dependencias complejas |
| **docTR** | Moderno, GPU | Menos probado |

## Recomendación para NEVEN

### Corto plazo: NO integrar

**Razón:** NEVEN prioriza funcionamiento offline. Los libros académicos que usamos tienen texto extraíble (no son escaneados).

### Mediano plazo: Integración opcional

**Cuándo:** Si el usuario tiene:
1. API key de OpenAI/Azure configurada, O
2. LMStudio con modelo vision corriendo

**Implementación sugerida:**
```python
# En neven-config.json
{
  "RAG": {
    "enableOCR": false,
    "ocrProvider": "openai",  // o "lmstudio"
    "ocrModel": "gpt-4o"
  }
}

# En rag_engine.py
if config.get("enableOCR") and llm_client:
    md = MarkItDown(
        enable_plugins=True,
        llm_client=llm_client,
        llm_model=config.get("ocrModel")
    )
else:
    md = MarkItDown()  # Sin OCR
```

## Conclusión

| Aspecto | Decisión |
|---------|----------|
| **Integrar ahora** | No |
| **Documentar opción** | Si |
| **Prioridad futura** | BAJA |
| **Trigger para reconsiderar** | Usuario reporta PDFs escaneados que no se indexan |

---

**Nota:** Los 9 libros actualmente indexados en NEVEN funcionan correctamente sin OCR porque tienen texto embebido.
