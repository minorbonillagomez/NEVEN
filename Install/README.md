# NEVEN Installer — Directorio de Instalación

Este directorio contiene todo lo necesario para construir y distribuir el instalador de NEVEN v3.2.

## Contenido

| Archivo/Directorio | Descripción |
|-------------------|-------------|
| `Install-NEVEN.ps1` | Script principal de instalación (PowerShell) |
| `Install-NEVEN.exe` | Instalador ejecutable (generado con ps2exe) |
| `Install-NEVEN.cmd` | Wrapper para ejecutar el instalador |
| `Uninstall-NEVEN.ps1` | Script de desinstalación |
| `Uninstall-NEVEN.exe` | Desinstalador ejecutable |
| `Uninstall-NEVEN.cmd` | Wrapper para el desinstalador |
| `Build-Installers.ps1` | Genera los .exe a partir de los .ps1 |
| `Dist/` | Artefactos compilados para distribución |
| `neven-config.json` | Plantilla de configuración por defecto |
| `neven-languages.json` | Plantilla de rutas de lenguajes |
| `packages-manifest.json` | Manifiesto de paquetes R/Julia/Python |
| `functions/` | Sidecars JSON de funciones |
| `prompts/` | Plantillas de prompts para IA |
| `license.txt` | Licencia GPL v3 |

## Cómo Construir el Instalador

### Prerrequisitos
- Windows 10/11 64-bit
- PowerShell 5.1+
- Visual Studio 2022 (para compilar los binarios)
- ps2exe (se instala automáticamente)

### Paso 1: Compilar el proyecto principal
```powershell
# Desde la raíz del repositorio NEVEN/
cmake --build build --config Release
```

### Paso 2: Crear el directorio Dist
El directorio `Dist/` debe contener:
- Binarios: `NEVEN64.xll`, `ControlR.exe`, `ControlJulia.exe`, `ControlPython.exe`, `NEVENRibbon.dll`
- Configs: `neven-config.json`, `neven-languages.json`
- Carpetas: `startup/`, `taskpane/`, `examples/`, `docs/`, `functions/`, `libreria/`, `prompts/`

### Paso 3: Generar los ejecutables
```powershell
cd Install
.\Build-Installers.ps1
```

Esto genera `Install-NEVEN.exe` y `Uninstall-NEVEN.exe`.

## Contenido de Dist/

```
Dist/
├── NEVEN64.xll              # Add-in XLL principal
├── ControlR.exe             # Motor R embebido
├── ControlJulia.exe         # Motor Julia embebido
├── ControlPython.exe        # Motor Python embebido
├── NEVENRibbon.dll          # COM Add-in para Ribbon
├── neven-config.json        # Configuración
├── neven-languages.json     # Rutas de lenguajes
├── packages-manifest.json   # Paquetes requeridos
├── NEVEN Studio.vbs         # Launcher del Studio
├── NEVEN_studio.ico         # Icono
├── startup/                 # Scripts de inicio
│   ├── startup.r
│   ├── startup.jl
│   ├── startup.py
│   └── neven_http_server.py
├── taskpane/                # NEVEN Studio (TaskPane)
│   ├── taskpane.html
│   ├── taskpane.js
│   ├── taskpane.css
│   ├── datalab.js
│   ├── manifest.xml
│   ├── start_studio.py
│   └── presentaciones/
├── docs/                    # Documentación
│   └── neven-docs.html
├── examples/                # Ejemplos por lenguaje
├── functions/               # Sidecars JSON
├── libreria/                # Funciones R/Julia/Python
│   ├── R/
│   ├── JULIA/
│   └── PYTHON/
├── prompts/                 # Templates IA
└── notebooks/               # Notebooks Pluto
```

## Publicar una Release

1. Verificar que el proyecto compila: `cmake --build build --config Release`
2. Actualizar versión en:
   - `CMakeLists.txt` (project VERSION)
   - `Install/Build-Installers.ps1` (-version parameter)
   - `Install/Install-NEVEN.ps1` (banner)
3. Crear/actualizar `Dist/` con los artefactos
4. Generar ejecutables: `.\Build-Installers.ps1`
5. Probar el instalador en una máquina limpia
6. Crear ZIP de distribución

## Uso del Instalador

### Instalación interactiva
```powershell
.\Install-NEVEN.exe
```

### Instalación silenciosa
```powershell
.\Install-NEVEN.exe -Silent
```

### Instalación en directorio personalizado
```powershell
.\Install-NEVEN.ps1 -InstallDir "D:\MiNEVEN"
```

## Qué hace el Instalador

1. **Pre-flight checks**: Verifica Windows 64-bit, PowerShell 5.1+, detecta R/Julia/Python
2. **User choices**: Confirma directorio de instalación (default: C:\NEVEN)
3. **File deployment**: Copia binarios, configs, scripts, ejemplos
4. **Registration**: Registra XLL en Excel, registra Ribbon COM, configura TaskPane
5. **User setup**: Crea directorios de usuario, accesos directos opcionales
6. **Verification**: Genera desinstalador personalizado, muestra resumen

---
*NEVEN v3.2 — Universidad de Costa Rica — Minor Bonilla Gómez*
*Setiembre 2026*
