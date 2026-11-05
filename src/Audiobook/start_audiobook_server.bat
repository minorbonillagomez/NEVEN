@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM NEVEN Audiobook Server - Script de inicio
REM Puerto: 5556
REM ═══════════════════════════════════════════════════════════════════════════

title NEVEN Audiobook Server

echo.
echo ========================================
echo   NEVEN Audiobook Server
echo   Puerto: 5556
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado en el PATH
    pause
    exit /b 1
)

REM Verificar dependencias básicas
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
)

REM Iniciar servidor
echo [INFO] Iniciando servidor en puerto 5556...
echo [INFO] Presiona Ctrl+C para detener
echo.

python neven_audiobook_server.py --port 5556

pause
