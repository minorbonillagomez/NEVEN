@echo off
title NEVEN Uninstaller v2.0
echo.
echo   ============================================
echo    NEVEN Uninstaller
echo   ============================================
echo.

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo   Requesting administrator privileges...
    echo.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

:: Set working directory to script location
cd /d "%~dp0"

:: Run the PowerShell uninstaller
if exist "%~dp0Uninstall-NEVEN.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-NEVEN.ps1"
) else (
    echo   ERROR: Uninstall-NEVEN.ps1 not found.
    echo   Expected at: %~dp0Uninstall-NEVEN.ps1
)

echo.
echo   Press any key to close...
pause >nul
