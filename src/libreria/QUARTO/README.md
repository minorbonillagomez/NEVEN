# Librería Quarto — NEVEN

Este directorio contiene ejemplos y documentación para la integración de Quarto con NEVEN.

## ¿Qué es Quarto?

[Quarto](https://quarto.org) es un sistema de publicación científica que permite crear documentos reproducibles combinando texto, código y resultados. NEVEN permite renderizar documentos `.qmd` directamente desde Excel.

## Uso desde Excel

```
=P.quarto_render("C:\Users\usuario\Documents\reporte.qmd", "html")
=P.quarto_render("C:\Users\usuario\Documents\reporte.qmd", "pdf")
=P.quarto_render("C:\Users\usuario\Documents\reporte.qmd", "docx")
```

## Formatos soportados

| Formato | Extensión | Requisitos adicionales |
|---------|-----------|----------------------|
| HTML | `.html` | Ninguno |
| PDF | `.pdf` | LaTeX instalado (TinyTeX recomendado) |
| Word | `.docx` | Ninguno |

## Archivos en este directorio

| Archivo | Descripción |
|---------|-------------|
| `ejemplo_basico.qmd` | Ejemplo mínimo con Python, tabla y gráfico |

## Prerrequisitos

1. **Quarto CLI** instalado: [https://quarto.org/docs/get-started/](https://quarto.org/docs/get-started/)
2. **Python** con paquetes `pandas` y `matplotlib` (para los ejemplos)
3. Para PDF: instalar TinyTeX con `quarto install tinytex`

## Flujo de trabajo

1. Crear un archivo `.qmd` con texto y bloques de código
2. Desde Excel, ejecutar `=P.quarto_render("ruta/archivo.qmd", "html")`
3. El documento se renderiza y se abre automáticamente
4. La celda de Excel muestra la ruta al archivo generado
