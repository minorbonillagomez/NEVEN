@echo off
title NEVEN Installer v2.0
echo.
echo   ============================================
echo    NEVEN Installer
echo    R, Julia ^& Python to Excel
echo   ============================================
echo.

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo   Requesting administrator privileges...
    echo.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs -ArgumentList '%~dp0'"
    exit /b 0
)

:: Set working directory to script location
cd /d "%~dp0"

:: Run the PowerShell installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-NEVEN.ps1" -DistDir "%~dp0Dist"

echo.
echo   ============================================
echo   Press any key to close...
echo   ============================================
pause >nul
