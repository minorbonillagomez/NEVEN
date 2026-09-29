# Checklist Obligatorio Antes de Cambios — NEVEN

> **REGLA:** Antes de modificar cualquier archivo de NEVEN, verificar los items correspondientes.

---

## Checklist por tipo de archivo

### Archivos R (`.R`)

```
□ Verificar archivo es ASCII puro, sin BOM (bytes 239 187 191)
□ Verificar llaves {} balanceadas
□ Si es función nueva: crear sidecar JSON correspondiente
□ Si modifica dispatcher: verificar tabla de aliases
□ Copiar a producción con [System.IO.File]::Copy() (nunca Copy-Item)
```

**Verificar BOM:**
```powershell
$bytes = [System.IO.File]::ReadAllBytes('archivo.R')
$bytes[0..2]  # NO debe ser 239 187 191
```

**Verificar llaves balanceadas:**
```powershell
$c = Get-Content 'archivo.R' -Raw
$open = ([regex]::Matches($c, '\{')).Count
$close = ([regex]::Matches($c, '\}')).Count
$open -eq $close  # debe ser True
```

---

### Sidecars JSON (`.json`)

```
□ Verificar JSON válido (sin errores de sintaxis)
□ Campo `function_name_xll` coincide EXACTAMENTE con nombre de función R
□ Campo `file` es solo basename (no ruta absoluta)
□ Campo `id` es único entre todos los sidecars
□ Si es XLL-callable: incluir `nevenx_positions`
□ Incluir `tipo_outputs` con id=0 para ayuda
```

**Verificar JSON válido:**
```powershell
Get-Content 'archivo.json' | ConvertFrom-Json  # no debe dar error
```

---

### Agregar aliases a una función

**IMPORTANTE: Modificar DOS archivos:**

1. **Dispatcher R** (`C:\NEVEN\functions\R4XCL-0-NevenX.R`):
   - Buscar tabla `.neven_aliases` (~línea 205)
   - Agregar: `"MiAlias" = "NombreFuncionReal"`

2. **Servidor HTTP** (`C:\NEVEN\startup\neven_http_server.py`):
   - Buscar diccionario `_function_aliases` (~línea 1942)
   - Agregar: `"NombreFuncionReal": ["MiAlias", "OtroAlias"]`

```
□ Alias agregado en R dispatcher
□ Alias agregado en Python server
□ Reiniciar servidor HTTP
□ Reiniciar Excel
□ Verificar en Tab Ayuda que aparezca el alias
```

---

### TaskPane (JS/HTML/CSS)

```
□ Reutilizar componentes existentes:
  - buildSlotElement() para renderizar resultados
  - showToast() para notificaciones
  - renderSlotTable() para tablas
□ NO duplicar parsers ni renderers
□ Usar tema oscuro consistente (#373434 fondo, #e0e0e0 texto)
```

---

### Servidor HTTP Python

```
□ El servidor en producción es: C:\NEVEN\startup\neven_http_server.py
□ NO es: C:\NEVEN\TaskPane\neven_http_server.py (copia vieja)
□ Puerto actual: 5555
□ Limpiar __pycache__ después de cambios
```

---

## Comandos de copia a producción

**Archivos R (UTF-8 sin BOM):**
```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$c = [System.IO.File]::ReadAllText($src, $utf8NoBom)
[System.IO.File]::WriteAllText('C:\NEVEN\functions\archivo.R', $c, $utf8NoBom)
```

**Archivos Python/JSON/JS (UTF-8 normal):**
```powershell
[System.IO.File]::Copy($src, $dest, $true)
```

---

## Mapeo producción → repositorio

| Producción | Repositorio |
|------------|-------------|
| `C:\NEVEN\functions\R4XCL-*.R` | `NEVEN\libreria\R\R4XCL-*.R` |
| `C:\NEVEN\functions\*.json` | `NEVEN\Install\functions\*.json` |
| `C:\NEVEN\startup\neven_http_server.py` | `NEVEN\TaskPane\neven_http_server.py` |
| `C:\NEVEN\TaskPane\*.js` | `NEVEN\TaskPane\*.js` |

---

## Validación post-cambio

```
□ Funcionalidad probada manualmente en Excel
□ No hay errores en consola R ni Python
□ Tab Ayuda muestra información correcta
□ Archivos copiados al repositorio
```
