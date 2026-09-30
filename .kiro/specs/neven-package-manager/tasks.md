# Plan de Tareas — NEVEN Package Manager

## Resumen de implementación

6 archivos a crear/modificar. Orden: servicio central → endpoints HTTP → hook DataLab → UI → tests.

---

## Tarea 1: Manifiesto predeterminado y estructura de datos

- [ ] 1.1 Crear `Install/packages-manifest.json` con los paquetes predeterminados de R, Julia y Python
  - R: `jsonlite`, `plm`, `stargazer`, `e1071`, `rpart`, `wooldridge`, `AER`, `sandwich`, `vars`, `urca`, `sampleSelection`, `lmtest`, `forecast`, `FactoMineR`, `plotly`, `htmlwidgets`
  - Julia: `DataFrames`, `Statistics`, `JSON3`
  - Python: `nltk`, `scikit-learn`, `pandas`, `numpy`
- [ ] 1.2 Copiar `packages-manifest.json` a `C:\NEVEN\` como parte del despliegue
- [ ] 1.3 Agregar campo opcional `"dependencies"` a un sidecar de ejemplo (`R4XCL-RG-Lineal.json`)
  - Formato: `{"dependencies": {"R": ["plm","stargazer"], "Julia": [], "Python": []}}`
  - Backward-compatible: si no existe el campo, la función funciona igual

**Archivos:** `Install/packages-manifest.json`, `Install/functions/R4XCL-RG-Lineal.json`

---

## Tarea 2: PackageManagerService — núcleo del subsistema

- [ ] 2.1 Crear `ControlPython/startup/package_manager_service.py` con la clase `PackageManagerService`
- [ ] 2.2 Implementar `load_manifest()` y `generate_manifest()` con fallback a valores predeterminados
- [ ] 2.3 Implementar `save_manifest()` y `save_cache()` / `load_cache()`
- [ ] 2.4 Implementar `_verificar_r(paquete)` — envía `requireNamespace('X', quietly=TRUE)` por pipe R
- [ ] 2.5 Implementar `_verificar_julia(paquete)` — envía `Base.find_package("X") !== nothing` por pipe Julia
- [ ] 2.6 Implementar `_verificar_python(paquete)` — usa `pip show` via `_get_python_exe()` de `package_manager.py`
- [ ] 2.7 Implementar `verificar_motor(motor)` — agrega los resultados de _verificar_* en lista de dicts
- [ ] 2.8 Implementar `verificar_todos(timeout_s=30)` en hilo de fondo — escribe caché al terminar
- [ ] 2.9 Implementar `verificar_funcion(function_id)` — filtra manifiesto por function_id (max 5s)
- [ ] 2.10 Implementar `encolar_instalacion(items)` y thread secuencial de instalación
- [ ] 2.11 Implementar `_instalar_r(paquete, repo)` — `install.packages('X', dependencies=TRUE, repos='...')`
- [ ] 2.12 Implementar `_instalar_julia(paquete)` — `import Pkg; Pkg.add("X")` por pipe Julia
- [ ] 2.13 Implementar `_instalar_python(paquete)` — `pip install X` via `_get_python_exe()`
- [ ] 2.14 Implementar `get_progress()` — retorna estado actual de la Cola_de_Instalación
- [ ] 2.15 Implementar `_log(level, message)` — escribe al log de NEVEN con prefijo `[PKG]`
- [ ] 2.16 Implementar `start()` — carga manifiesto, lanza thread daemon de verificación al inicio
- [ ] 2.17 Implementar `stop()` — señaliza al thread de instalación que termine limpiamente

**Archivo:** `ControlPython/startup/package_manager_service.py`

---

## Tarea 3: Endpoints HTTP en neven_http_server.py

- [ ] 3.1 Instanciar `PackageManagerService` como `_pkg_service` en `neven_http_server.py`
  - Inyectar `_get_pipe_client` igual que con `_datalab_handler`
  - Llamar `_pkg_service.start()` al iniciar el servidor
- [ ] 3.2 Agregar `GET /api/packages/status` — lee caché y retorna JSON con todos los paquetes
- [ ] 3.3 Agregar `GET /api/packages/status/{motor}` — filtra por motor (r/julia/python)
- [ ] 3.4 Agregar `POST /api/packages/install` — recibe lista `{"paquetes":[...]}` y encola
- [ ] 3.5 Agregar `GET /api/packages/progress` — retorna estado de cola (polling ~2s)
- [ ] 3.6 Agregar `GET /api/packages/function/{id}` — llama `verificar_funcion(id)` con caché de 5s
- [ ] 3.7 Manejar motor no disponible con `motor_disponible: false` en lugar de HTTP 500

**Archivo:** `ControlPython/startup/neven_http_server.py`

---

## Tarea 4: Hook en DataLab — advertencia al ejecutar

- [ ] 4.1 En `datalab_handler.handle_run()`, después de resolver `function_id` y **antes** de construir el script R:
  ```python
  if _PKG_SERVICE_AVAILABLE:
      faltantes = [p for p in _pkg_service.verificar_funcion(function_id) if not p["instalado"]]
      if faltantes:
          # inyectar slot de advertencia — NO bloquear ejecución
  ```
- [ ] 4.2 El slot de advertencia tiene `type="scalar"`, `tier=1`, con lista de paquetes faltantes y enlace de instalación
- [ ] 4.3 La verificación tiene timeout de 3s para no degradar el DataLab — si timeout, omitir slot

**Archivo:** `ControlPython/startup/datalab_handler.py`

---

## Tarea 5: UI en NEVEN Studio — botón y panel de advertencia

- [ ] 5.1 Agregar `<div id="dl-pkg-warning">` entre `#dl-selector-card` y `#dl-column-panel` en el tab Data Lab
  - Visible solo cuando hay paquetes faltantes en la función seleccionada
  - Contiene: nombre de paquetes faltantes + botón "Instalar paquetes faltantes"
- [ ] 5.2 Agregar botón "🔍 Verificar paquetes" al final de `#dl-selector-card`
  - Al hacer clic llama `GET /api/packages/status` y muestra reporte con `renderSlotTable`
- [ ] 5.3 Al hacer clic en "Instalar paquetes faltantes" → `POST /api/packages/install` → polling `GET /api/packages/progress`
- [ ] 5.4 Mostrar progreso de instalación: nombre del paquete en curso, N de M completados
- [ ] 5.5 Desplegar `taskpane.html` actualizado a `C:\NEVEN\taskpane\taskpane.html` sin BOM

**Archivo:** `TaskPane/taskpane.html`

---

## Tarea 6: Tests

- [ ] 6.1 Crear `tests/test_package_manager_service.py` con tests unitarios:
  - `test_load_manifest_creates_default_when_missing` (Req 1.3)
  - `test_manifest_skips_invalid_entries` (Req 1.5)
  - `test_verificar_todos_timeout_returns_partial` (Req 2.5)
  - `test_verificar_funcion_filters_by_id` (Req 3.1)
  - `test_install_requires_explicit_authorization` (Req 5.1)
  - `test_install_failure_continues_queue` (Req 5.5)
  - `test_endpoint_unavailable_motor_returns_flag` (Req 9.5)
- [ ] 6.2 Agregar pruebas de propiedad con hypothesis (11 propiedades del diseño):
  - Property 1: integridad del manifiesto generado
  - Property 3: tolerancia a entradas inválidas
  - Property 4: filtrado exacto por función
  - Property 5: sin instalación sin autorización
  - Property 9: reutilización del ejecutable Python correcto
  - Property 10: completitud del esquema HTTP
- [ ] 6.3 Ejecutar `tests/run_studio_tests.R` para verificar que no hay regresión en tests R existentes

**Archivo:** `tests/test_package_manager_service.py`

---

## Tarea 7: Despliegue y verificación

- [ ] 7.1 Copiar archivos nuevos/modificados a `C:\NEVEN\`:
  ```powershell
  # Usar [System.IO.File]::Copy() — nunca Copy-Item
  [System.IO.File]::Copy("...\package_manager_service.py", "C:\NEVEN\startup\package_manager_service.py", $true)
  [System.IO.File]::Copy("...\neven_http_server.py", "C:\NEVEN\startup\neven_http_server.py", $true)
  [System.IO.File]::Copy("...\datalab_handler.py", "C:\NEVEN\startup\datalab_handler.py", $true)
  [System.IO.File]::Copy("...\taskpane.html", "C:\NEVEN\taskpane\taskpane.html", $true)
  [System.IO.File]::Copy("...\packages-manifest.json", "C:\NEVEN\packages-manifest.json", $true)
  ```
- [ ] 7.2 Reiniciar NEVEN Studio y verificar que el servidor arranca sin error
- [ ] 7.3 Abrir `https://localhost:5555/api/packages/status` — debe retornar JSON con paquetes
- [ ] 7.4 Probar con un paquete intencionalmente faltante: verificar que aparece advertencia en DataLab
- [ ] 7.5 Autorizar instalación desde UI y verificar progreso
- [ ] 7.6 Verificar que `C:\NEVEN\packages-status-cache.json` se actualiza después de la verificación
- [ ] 7.7 Actualizar `Estado_del_arte.md` con la nueva funcionalidad

---

## Orden de ejecución recomendado

```
Tarea 1 → Tarea 2 → Tarea 3 → Tarea 4 → Tarea 5 → Tarea 6 → Tarea 7
(datos)  (servicio) (HTTP)   (DataLab) (UI)      (tests)  (deploy)
```

Cada tarea es independiente y testeable sin la siguiente excepto Tarea 3 que depende de Tarea 2.
