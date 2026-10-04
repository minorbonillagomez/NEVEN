# NEVEN — Checklist Obligatorio Antes de Cambios

> **REGLA:** Antes de modificar cualquier archivo de NEVEN, el agente DEBE consultar los documentos relevantes según el tipo de cambio.

---

## Documentos de consulta obligatoria

### 1. Siempre revisar primero

| Documento | Ubicación | Por qué |
|-----------|-----------|---------|
| **CHAT.md** | `.kiro/contexto/CHAT.md` | Historial de decisiones, problemas resueltos, y contexto de sesiones anteriores |
| **Ontología P1-P4** | `docs/ontologia/neven-core/*.yaml` | Invariantes técnicas que NUNCA deben violarse |

### 2. Según el tipo de cambio

| Si vas a modificar... | Consultar ANTES |
|-----------------------|-----------------|
| **Archivos R** (`.R`) | P2 `dispatcher_nevenx` — INV-NX-01 (ASCII sin BOM), INV-NX-02 (llaves balanceadas) |
| **Sidecars JSON** | `docs/SIDECAR_FORMAT.md` + P2 `sidecars_json` — INV-SJ-02 (`function_name_xll` exacto) |
| **Ontologías YAML** | `.kiro/steering/ontology-yaml-rules.md` — escapes, comillas, dominios |
| **Agregar funciones** | `C:\NEVEN\functions\COMO_AGREGAR_FUNCIONES.md` |
| **Agregar aliases** | `COMO_AGREGAR_FUNCIONES.md` sección "Aliases" — modificar R + Python |
| **TaskPane JS/HTML** | P3 `taskpane_frontend` — INV-TF-01..04, componentes reutilizables |
| **HTTP Server Python** | P2 `studio_backend` — INV-SB-01..05 |
| **C++ Core/Common** | P1 correspondiente + verificar tests |
| **CMake/Build** | P4 `build_cmake` — INV-BLD-01..04 |

---

## Checklist por área

### Cambios en archivos R

```
□ Verificar archivo es ASCII puro, sin BOM
□ Verificar llaves {} balanceadas
□ Si es función nueva: crear sidecar JSON correspondiente
□ Si modifica dispatcher: verificar tabla de aliases actualizada
□ Copiar a producción con: [System.IO.File]::Copy() (nunca Copy-Item)
```

**Verificar BOM:**
```powershell
$bytes = [System.IO.File]::ReadAllBytes('archivo.R')
$bytes[0..2]  # NO debe ser 239 187 191
```

### Cambios en sidecars JSON

```
□ Verificar JSON válido (sin errores de sintaxis)
□ Campo `function_name_xll` coincide EXACTAMENTE con nombre de función R
□ Campo `file` es solo basename (no ruta absoluta)
□ Campo `id` es único entre todos los sidecars
□ Si es XLL-callable: incluir `nevenx_positions`
```

### Cambios en ontologías YAML

> **CRÍTICO:** Errores de sintaxis YAML impiden que el RAG cargue entidades.

```
□ Usar comillas SIMPLES para paths Windows (contienen \)
□ Usar comillas SIMPLES para comandos shell (pueden tener |, &)
□ Espacio después de cada : en mappings ("key": "value", NO "key":"value")
□ Cada item de lista (-) en su propia línea con estructura anidada
□ Dominios en ESPAÑOL: econometria, estadistica (NO econometrics, statistics)
□ Validar ANTES de guardar: python -c "import yaml; yaml.safe_load(open('archivo.yaml'))"
□ Copiar a producción: C:\NEVEN\docs\ontologia\
```

**Errores comunes de escape:**
```yaml
# ❌ MAL - \p, \I, \| son escapes inválidos
nombre_pipe: "\\\\.\pipe\\..."      
comando: ".\Install-NEVEN.ps1"

# ✅ BIEN - comillas simples NO interpretan escapes
nombre_pipe: '\\\\.\\pipe\\...'
comando: '.\Install-NEVEN.ps1'
```

### Agregar aliases a una función

**Modificar DOS archivos:**

1. **Dispatcher R** (`C:\NEVEN\functions\R4XCL-0-NevenX.R`):
   - Buscar tabla `.neven_aliases` (~línea 205)
   - Agregar: `"MiAlias" = "NombreFuncionReal"`

2. **Servidor HTTP** (`C:\NEVEN\startup\neven_http_server.py`):
   - Buscar diccionario `_function_aliases` (~línea 1942)
   - Agregar: `"NombreFuncionReal": ["MiAlias", "OtroAlias"]`

**Después:**
- Reiniciar servidor HTTP
- Reiniciar Excel
- Verificar en Tab Ayuda que aparezcan los aliases

### Cambios en TaskPane (JS/HTML/CSS)

```
□ Reutilizar componentes existentes (ver tabla en neven-project-context.md)
□ buildSlotElement() para renderizar resultados
□ showToast() para notificaciones
□ NO duplicar parsers ni renderers
```

### Cambios en servidor HTTP Python

```
□ El servidor en producción es C:\NEVEN\startup\neven_http_server.py
□ NO es C:\NEVEN\TaskPane\neven_http_server.py (copia vieja)
□ Puerto actual: 5555 (no 5050)
□ Limpiar __pycache__ después de cambios
```

---

## Comandos de copia a producción

**Archivos R:**
```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$c = [System.IO.File]::ReadAllText($src, $utf8NoBom)
[System.IO.File]::WriteAllText('C:\NEVEN\functions\archivo.R', $c, $utf8NoBom)
```

**Archivos Python/JSON (UTF-8 normal):**
```powershell
[System.IO.File]::Copy($src, $dest, $true)
```

---

## Copia al repositorio

| Producción | Repositorio |
|------------|-------------|
| `C:\NEVEN\functions\R4XCL-*.R` | `NEVEN\libreria\R\R4XCL-*.R` |
| `C:\NEVEN\functions\*.json` | `NEVEN\Install\functions\*.json` |
| `C:\NEVEN\startup\neven_http_server.py` | `NEVEN\TaskPane\neven_http_server.py` |
| `C:\NEVEN\TaskPane\*.js` | `NEVEN\TaskPane\*.js` |

---

## Validación post-cambio

```
□ Build compila sin errores (si aplica)
□ Tests pasan (si aplica)
□ Funcionalidad probada manualmente en Excel
□ CHAT.md actualizado con el cambio
□ Archivos copiados al repositorio
```
