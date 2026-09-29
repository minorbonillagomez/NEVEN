# Invariantes Técnicos — NEVEN

> **DEFINICIÓN:** Una invariante es una regla técnica que NUNCA debe violarse.
> Violar una invariante causa errores difíciles de diagnosticar.

---

## Archivos R

### INV-R-01: ASCII puro, sin BOM

**Regla:** Los archivos `.R` en `C:\NEVEN\functions\` DEBEN ser ASCII puro, sin BOM (Byte Order Mark).

**Por qué:** ControlR carga los archivos con `ReadSourceFile()` que envía líneas por Named Pipe. 
Un BOM (bytes `EF BB BF` = `239 187 191`) causa error: `unexpected invalid token en línea 1: ï»¿`

**Cómo verificar:**
```powershell
$bytes = [System.IO.File]::ReadAllBytes('C:\NEVEN\functions\archivo.R')
$bytes[0..2]  # NO debe ser 239 187 191
($bytes | Where-Object { $_ -gt 127 }).Count  # debe ser 0
```

**Cómo escribir sin BOM:**
```powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
```

---

### INV-R-02: Llaves balanceadas

**Regla:** Todo archivo `.R` debe tener llaves `{` y `}` balanceadas.

**Por qué:** Un error de parsing hace que ControlR retorne error en la celda Excel.

**Cómo verificar:**
```powershell
$c = Get-Content 'archivo.R' -Raw
$open = ([regex]::Matches($c, '\{')).Count
$close = ([regex]::Matches($c, '\}')).Count
$open -eq $close  # debe ser True
```

---

## Sidecars JSON

### INV-JSON-01: function_name_xll exacto

**Regla:** El campo `function_name_xll` en un sidecar JSON DEBE coincidir EXACTAMENTE con el nombre de la función R en `globalenv()`.

**Por qué:** El dispatcher hace `exists(proceso, envir=env)`. Si el nombre no coincide, la función no se encuentra.

**Ejemplo correcto:**
```json
{
  "function_name_xll": "MR_Lineal"
}
```
Y en R existe: `MR_Lineal <- function(...)`

**Ejemplo incorrecto:**
```json
{
  "function_name_xll": "MR_Lineal.C"  // ← .C extra que no existe en R
}
```

---

### INV-JSON-02: Campo file es basename

**Regla:** El campo `file` debe ser solo el nombre del archivo, no una ruta absoluta.

**Por qué:** El sistema resuelve: `os.path.join(functions_dir, file_basename)`. Una ruta absoluta no funcionará en otro sistema.

**Correcto:** `"file": "R4XCL-RG-Lineal.Studio.R"`
**Incorrecto:** `"file": "C:/NEVEN/functions/R4XCL-RG-Lineal.Studio.R"`

---

### INV-JSON-03: ID único

**Regla:** El campo `id` debe ser único entre todos los sidecars.

**Por qué:** DataLabHandler busca por `id==function_id`. Duplicados causan comportamiento impredecible.

**Verificar:**
```powershell
Get-ChildItem 'C:\NEVEN\functions\*.json' | ForEach-Object {
  (Get-Content $_ | ConvertFrom-Json).id
} | Group-Object | Where-Object { $_.Count -gt 1 }
# No debe retornar nada
```

---

## Aliases

### INV-ALIAS-01: Modificar DOS archivos

**Regla:** Al agregar un alias, SIEMPRE modificar ambos:
1. `C:\NEVEN\functions\R4XCL-0-NevenX.R` — tabla `.neven_aliases`
2. `C:\NEVEN\startup\neven_http_server.py` — diccionario `_function_aliases`

**Por qué:**
- El dispatcher R resuelve el alias para que Excel funcione
- El servidor Python muestra el alias en Tab Ayuda

**Si solo modificas uno:** El alias funciona en Excel pero no aparece en Ayuda (o viceversa).

---

### INV-ALIAS-02: Formato inverso R vs Python

**Regla:** El formato de la tabla de aliases es diferente en R y Python.

**En R (alias → función):**
```r
.neven_aliases <- list(
  "ACP" = "AD_ACP.C",
  "PCA" = "AD_ACP.C"
)
```

**En Python (función → [aliases]):**
```python
_function_aliases = {
  "AD_ACP.C": ["ACP", "PCA"]
}
```

---

## Servidor HTTP

### INV-HTTP-01: Archivo correcto

**Regla:** El servidor en producción es `C:\NEVEN\startup\neven_http_server.py`.

**Por qué:** Existe una copia vieja en `C:\NEVEN\TaskPane\neven_http_server.py` que NO se usa.

---

### INV-HTTP-02: Puerto 5555

**Regla:** El servidor escucha en puerto 5555, no 5050.

**Verificar:**
```powershell
netstat -ano | Select-String "5555"
```

---

## Copiar archivos

### INV-COPY-01: Usar [System.IO.File]::Copy()

**Regla:** SIEMPRE usar `[System.IO.File]::Copy()` para copiar archivos. NUNCA `Copy-Item`.

**Por qué:** `Copy-Item` en PowerShell puede corromper la codificación UTF-8 en ciertos escenarios.

**Correcto:**
```powershell
[System.IO.File]::Copy($src, $dest, $true)
```

**Incorrecto:**
```powershell
Copy-Item $src $dest -Force  # ← puede corromper UTF-8
```
