# NEVEM Studio 🎧

**Generador de Audiolibros Local** - Convierte EPUB y PDF a M4B con síntesis de voz neural.

## ✨ Características

- 📖 Parseo inteligente de EPUB y PDF con detección de capítulos
- 🎤 TTS local usando voces de Windows (Sabina, Raul, David, Zira)
- 📦 Empaquetado M4B con capítulos navegables y portada
- 🔒 100% offline - sin dependencias de nube
- ⚡ Procesamiento paralelo por capítulos

## 🚀 Uso Rápido

```batch
# Convertir un EPUB
run.bat mi_libro.epub

# Convertir un PDF a una carpeta específica
run.bat documento.pdf C:\Mis_Audiolibros
```

## 📁 Estructura del Proyecto

```
NEVEM_STUDIO/
├── src/
│   ├── parser/        # Parsers EPUB y PDF
│   ├── tts/           # Motor TTS (Windows SAPI)
│   ├── muxer/         # FFmpeg wrapper para M4B
│   ├── server/        # Servidor HTTP + QR (próximamente)
│   ├── gui/           # Interfaz gráfica (próximamente)
│   └── pipeline.py    # Orquestador principal
├── models/            # Modelos TTS adicionales (Piper, Kokoro)
├── output/            # Audiolibros generados
├── temp/              # Archivos temporales
├── venv/              # Entorno virtual Python
└── run.bat            # Script de ejecución
```

## 🔧 Dependencias

- **Python 3.12+**
- **FFmpeg** (instalado vía `winget install FFmpeg`)
- **Windows 11** con voces TTS instaladas

### Paquetes Python

```
ebooklib      # Parser EPUB
PyMuPDF       # Parser PDF
pyttsx3       # Windows SAPI TTS
flask         # Servidor HTTP
qrcode        # Generador de QR
Pillow        # Procesamiento de imágenes
```

## 🎯 Roadmap

- [x] Parser EPUB con extracción de capítulos
- [x] Parser PDF con detección heurística
- [x] Motor TTS con Windows SAPI
- [x] Muxer FFmpeg para M4B
- [x] Pipeline CLI funcional
- [ ] Integración Piper TTS (voces neurales)
- [ ] Servidor HTTP con código QR
- [ ] GUI con PySide6/Tauri
- [ ] App Android (Nevem Player)

## 📱 Companion App

**Nevem Player** (Android) - Reproductor de audiolibros M4B con:
- Navegación por capítulos nativos
- Auto-rewind inteligente
- Sleep timer con shake-to-reset
- Biblioteca visual con portadas verticales

---

*Parte del ecosistema NEVEN*
