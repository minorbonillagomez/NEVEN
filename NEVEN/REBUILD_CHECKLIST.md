# NEVEN — Recompilación Completa
## Fecha: 18 de mayo de 2026

## Prerequisitos
- [x] Visual Studio 2022 con C++ workload
- [x] Julia 1.12.6
- [x] R 4.4.1
- [x] Python 3.13
- [x] PackageCompiler.jl v2.2.5

## Paso 1: Verificar código fuente
- [x] `rj2xcl.cc` — zombie killer ANTES del file watcher Start()
- [x] `julia_interface.cc` — código original de julia_bindir
- [x] `R4XCL-0-Interno-1.R` — auto-detección + DTY.F + Categorica==2

## Paso 2: Regenerar libjulia.lib
- [x] dumpbin /exports
- [x] Generar .def
- [x] Generar .lib (154,878 bytes)

## Paso 3: Build completo limpio
- [x] NEVEN64.dll (2,450,944 bytes, 18/05 08:45)
- [x] ControlR.exe (1,528,320 bytes, 18/05 08:44)
- [x] ControlJulia.exe (1,298,432 bytes, 18/05 08:44)
- [x] ControlPython.exe (1,298,944 bytes, 18/05 08:44)
- [x] Todos del mismo build tree

## Paso 4: Generar sysimage
- [x] Test standalone de ControlJulia — OK (no crashea)
- [x] Crear sysimage_init.jl (módulo NEVEN + functions.jl sin using)
- [x] Ejecutar PackageCompiler (script only, sin precompile_execution_file)
- [x] Verificar sysimage: 414.4 MB
- [x] Verificar: NEVEN module presente
- [x] Verificar: 7 funciones J.* en Main (JM_Algebra, JM_Calculo, JM_EDO, JO_Optimizar, JC_Transformar, JC_Utilidades, TestAdd)

## Paso 5: Configurar entorno
- [x] RJ2XCL_HOME=C:\NEVEN\
- [x] neven-config.json (Julia=true, WebView2=true, Python=true, sin BOM)
- [x] neven-languages.json (UTF-8 sin BOM, nombres originales)
- [x] startup.jl (mínimo, sin BOM)
- [x] startup.r (con Extraer_outputs)
- [x] Office WebView2 PreWarm disabled
- [x] Directorio funciones: sin .jl, con .R actualizados

## Paso 6: Deploy
- [x] NEVEN64.xll (18/05 08:45)
- [x] ControlR.exe (18/05 08:44)
- [x] ControlJulia.exe (18/05 08:44)
- [x] ControlPython.exe (18/05 08:44)
- [x] neven_julia.dll (18/05 09:16, 414MB)
- [x] neven-config.json (sin BOM)
- [x] neven-languages.json (sin BOM)
- [x] startup.jl (mínimo, sin BOM)
- [x] startup.r, startup.py
- [x] Registry limpio, OPEN configurado
- [x] Procesos zombie eliminados

## Paso 7: Test
- [x] Excel abre rápido (< 3 segundos)
- [x] R funciona (TestAdd, MR_Lineal, MR_Binario.C con categóricas)
- [x] Python funciona (=NEVEN.P("1+1"))
- [x] WebView2 funciona (RPivot, Mapas)
- [x] German Credit funciona
- [ ] Julia: pendiente (lazyLoad activo, requiere fix libjulia.lib)
- [x] Cerrar/reabrir sin problemas

## Paso 8: Backup
- [x] Backup creado: Dist_STABLE_NEVEN_20260518
