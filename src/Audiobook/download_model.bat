@echo off
cd /d "C:\Users\Minor Bonilla G\Desktop\PHP\NEVEM_STUDIO\models"
echo Descargando modelo Piper es_MX-claude-high...
echo.

REM Descargar con curl (incluido en Windows 11)
curl -L -o es_MX-claude-high.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx"
curl -L -o es_MX-claude-high.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx.json"

echo.
echo Archivos descargados:
dir /b
pause
