# Guía de Usuario: NEVEN Toolkit 🚀

Bienvenido a **NEVEN**, la evolución moderna del Basic Excel R Toolkit. Esta guía te ayudará a instalar, configurar y utilizar R y Julia directamente desde Microsoft Excel.

------------------------------------------------------------------------

## 1. Requisitos del Sistema

| Componente            | Requisito Mínimo     | Recomendado             |
|-----------------------|----------------------|-------------------------|
| **Sistema Operativo** | Windows 10 (64 bits) | Windows 11              |
| **Microsoft Excel**   | 2013, 2016, 2019     | Microsoft 365 (64 bits) |
| **R**                 | 4.0.0                | 4.4.x                   |
| **Julia**             | 1.6.0 (LTS)          | 1.11.x                  |
| **RAM**               | 4 GB                 | 8 GB+                   |
| **Espacio en disco**  | 500 MB (sin R/Julia) | 2 GB (con R + Julia)    |

------------------------------------------------------------------------

## 2. Instalación Paso a Paso

### Opción A: Usando el Instalador

1.  Descarga `NEVEN_Setup.exe` desde la sección de [Releases](https://github.com/mboni/NEVEN/releases)
2.  Ejecuta el instalador. No necesitas permisos de administrador
3.  **Paso de Documentación**: El instalador te mostrará la documentación del proyecto para que la conozcas antes de instalar
4.  **Directorio**: Elige dónde instalar (por defecto: `Mis Documentos\NEVEN`)
5.  **Componentes opcionales**: Puedes elegir descargar R y/o Julia automáticamente, o instalarlos después desde el botón del Ribbon
6.  Haz clic en "Instalar" y espera a que termine

### Opción B: Instalación Manual (desde código fuente)

``` powershell
# 1. Clona el repositorio
git clone https://github.com/mboni/NEVEN.git
cd NEVEN

# 2. Compila
.\build.ps1 -Package

# 3. El XLL está en Build\Dist\NEVEN64.xll
# 4. Cópialo a tu directorio de instalación
# 5. Abre Excel --> Archivo --> Opciones --> Complementos --> Ir...
# 6. Haz clic en "Examinar" y selecciona NEVEN64.xll
```

### Verificación Post-Instalación

1.  Abre Excel
2.  Verifica que existe la pestaña **NEVEN** en la cinta de opciones (Ribbon)
3.  En cualquier celda, escribe `=NEVEN.Version()` — debe mostrar la versión actual

Si ves `#NAME?`, consulta la sección [Solución de Problemas](#9-solución-de-problemas).

------------------------------------------------------------------------

## 3. Tu Primera Función en R

### Paso 1: Crea un archivo de script

Crea un archivo llamado `mis_funciones.R` en:

```         
C:\Users\TuUsuario\Documents\NEVEN\functions\mis_funciones.R
```

### Paso 2: Define una función

``` r
# mis_funciones.R
mi_suma <- function(a, b) {
  return(a + b)
}

promedio_ponderado <- function(valores, pesos) {
  return(sum(valores * pesos) / sum(pesos))
}
```

### Paso 3: Usa la función en Excel

En cualquier celda de Excel:

```         
=NEVEN.r.mi_suma(10, 20)
```

Resultado: `30`

```         
=NEVEN.r.promedio_ponderado(A1:A5, B1:B5)
```

Pasa rangos de Excel directamente como vectores de R.

------------------------------------------------------------------------

## 4. Tu Primera Función en Julia

### Paso 1: Crea un archivo de script

```         
C:\Users\TuUsuario\Documents\NEVEN\functions\mis_funciones.jl
```

### Paso 2: Define una función con docstring

``` julia
"""
    JuliaSuma(a, b)

Suma dos números desde Julia. Esta descripción aparecerá
en el Asistente de Funciones de Excel.
"""
function JuliaSuma(a, b)
    return a + b
end

"""
    FibonacciN(n)

Calcula el n-ésimo número de Fibonacci.
"""
function FibonacciN(n)
    n <= 1 && return n
    a, b = 0, 1
    for _ in 2:n
        a, b = b, a + b
    end
    return b
end
```

### Paso 3: Usa la función en Excel

```         
=NEVEN.j.JuliaSuma(5, 8)        --> 13
=NEVEN.j.FibonacciN(10)         --> 55
```

> **Nota**: Los docstrings de Julia (entre `"""`) aparecerán automáticamente en el Asistente de Funciones de Excel (Shift+F3).

------------------------------------------------------------------------

## 5. La Consola Interactiva (REPL)

La consola te permite ejecutar código en tiempo real sin necesidad de crear archivos.

### Abrir la Consola

- Haz clic en **"Abrir Consola"** en la pestaña NEVEN del Ribbon
- O presiona el atajo de teclado configurado

### Funcionalidades

- **Ejecución interactiva**: Escribe código R o Julia y obtén resultados inmediatos
- **Soporte MIME**: Julia puede mostrar tablas HTML y gráficos PNG directamente
- **Historial**: Usa las flechas ↑↓ para navegar por comandos anteriores
- **Autocompletado**: Tab para completar nombres de funciones

### Ejemplo interactivo en R

``` r
> x <- rnorm(100)
> summary(x)
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max.
 -2.450  -0.640   0.050   0.023   0.680   2.310

> plot(x)
# El gráfico aparece en la consola o como shape en Excel
```

### Ejemplo interactivo en Julia

``` julia
julia> using Statistics
julia> data = randn(1000)
julia> mean(data), std(data)
(0.0023, 1.0012)
```

------------------------------------------------------------------------

## 6. Carga Automática de Scripts (AutoLoader)

NEVEN busca automáticamente archivos de script en el directorio:

```         
C:\Users\TuUsuario\Documents\NEVEN\functions\
```

### Comportamiento

- Al abrir Excel, todos los archivos `.R` y `.py` en este directorio se cargan automáticamente
- Las funciones definidas quedan disponibles inmediatamente como `=R.*` o `=P.*`
- NEVEN vigila el directorio: si modificas un archivo `.R` o `.py`, se recarga automáticamente (**Hot Reload**)
- **Julia**: Las funciones `.jl` se cargan cuando el usuario activa Julia (ver sección siguiente)

### Activación de Julia (Carga Bajo Demanda)

Julia utiliza compilación JIT (Just-In-Time) que requiere unos segundos la primera vez. Para evitar retrasos al abrir Excel, Julia se activa **bajo demanda**:

1. Abre Excel normalmente (R y Python se conectan instantáneamente)
2. Cuando necesites funciones Julia, haz clic en el botón **"Actualizar"** en la pestaña NEVEN del Ribbon (grupo Motores)
3. Espera ~30-60 segundos mientras Julia compila las funciones
4. Las funciones `=J.*` quedan disponibles para la sesión

> **Nota**: También puedes ejecutar código Julia directamente con `=NEVEN.j("código")` sin necesidad de activar las funciones registradas.

### Buenas prácticas para archivos Julia del usuario

- Mantenga sus archivos `.jl` personalizados **bajo 5KB** cada uno para carga rápida
- Las funciones base de NEVEN (70 funciones J.*) se cargan desde el startup — no las modifique
- Coloque sus funciones Julia personalizadas en archivos separados (ej: `mis_calculos.jl`)

------------------------------------------------------------------------

## 6.1. Auto-detección de Variables Categóricas

NEVEN detecta automáticamente si sus datos contienen variables categóricas (texto) al ejecutar modelos estadísticos. No necesita especificar manualmente cuáles variables son categóricas.

### Comportamiento automático

- Si una columna contiene texto (ej: "A11", "bueno", "soltero"), NEVEN la convierte a `factor` automáticamente
- Si una columna contiene solo números, se trata como numérica
- El modelo estima coeficientes para cada nivel de la variable categórica (dummies automáticas)

### Ejemplo con German Credit

```
=R.MR_Binario.C(Y, X, 0, Filtro, 0, 0, 0, 1)
```

Donde `X` contiene columnas mixtas (texto + números). NEVEN detecta automáticamente cuáles son categóricas.

### Parámetro Categorica

| Valor | Comportamiento |
|-------|---------------|
| `0` | Auto-detección silenciosa (recomendado) |
| `1` | Diálogo manual para seleccionar variables numéricas |

### Nuevas funciones de datos

| Función | Descripción |
|---------|-------------|
| `=R.DB_Unicos(rango)` | Retorna valores únicos de un rango |
| `=R.DB_Recodificar(datos, viejos, nuevos)` | Recodifica valores en un rango |

### Estructura recomendada

```         
Documents/
└── NEVEN/
    ├── functions/
    │   ├── estadisticas.R
    │   ├── machine_learning.R
    │   ├── optimizacion.jl
    │   └── simulacion.jl
    └── examples/
        ├── functions.r
        └── functions.jl
```

------------------------------------------------------------------------

## 7. Automatización COM desde Julia

Puedes manipular Excel programáticamente desde Julia usando el objeto global `EXCEL`:

### Leer y escribir celdas

``` julia
# Escribir un valor
EXCEL.ActiveSheet.Range("A1").Value = "Hola desde Julia"

# Leer un valor
valor = EXCEL.ActiveSheet.Range("B2").Value

# Escribir un rango
for i in 1:10
    EXCEL.ActiveSheet.Range("A$i").Value = i^2
end
```

### Formato de celdas

``` julia
rng = EXCEL.ActiveSheet.Range("A1:A10")
rng.Font.Bold = true
rng.Font.Color = 0xFF0000  # Rojo
rng.Interior.Color = 0xFFFF00  # Fondo amarillo
```

### Crear hojas

``` julia
EXCEL.Sheets.Add()
EXCEL.ActiveSheet.Name = "Resultados"
```

------------------------------------------------------------------------

## 8. Configuración Avanzada

### Archivo de configuración principal

```         
[directorio_instalación]/neven-config.json
```

``` json
{
  "NEVEN": { "home": "C:\\Users\\TuUsuario\\Documents\\NEVEN" },
  "R": { "home": "" },
  "Julia": { "home": "" },
  "languages": ["R", "Julia"],
  "installLater": false
}
```

### Archivo de lenguajes

```         
[directorio_instalación]/neven-languages.json
```

``` json
{
  "R": {
    "home": "C:\\Program Files\\R\\R-4.4.0",
    "bin": "bin\\x64\\R.dll"
  },
  "Julia": {
    "home": "C:\\Users\\TuUsuario\\AppData\\Local\\Programs\\Julia-1.11.2",
    "bin": "bin\\libjulia.dll"
  }
}
```

> Si los campos `home` están vacíos, NEVEN intenta detectar las instalaciones automáticamente usando el Registro de Windows (DiscoveryService).

------------------------------------------------------------------------

## 9. Solución de Problemas

### Error: `#NAME?` al escribir una fórmula

**Causa**: El complemento XLL no está cargado correctamente.

**Solución**: 1. Ve a `Archivo --> Opciones --> Complementos` 2. En la parte inferior, selecciona "Complementos de Excel" y haz clic en "Ir..." 3. Verifica que `NEVEN64.xll` esté marcado 4. Si no aparece, haz clic en "Examinar" y selecciona el archivo

### Error: R o Julia no detectados

**Causa**: DiscoveryService no encontró la instalación.

**Solución**: 1. Abre `neven-languages.json` en tu directorio de instalación 2. Configura manualmente la ruta `home` para R y/o Julia 3. Reinicia Excel

### Error: La consola no abre

**Causa**: La consola Electron no está instalada o su ruta es incorrecta.

**Solución**: 1. Verifica que existe la carpeta `console/win-unpacked/` en el directorio de instalación 2. Si no existe, reinstala NEVEN o copia la consola manualmente

### Error: Datos "basura" o caracteres extraños en los resultados

**Causa**: Problemas de codificación UTF-8 <--> UTF-16.

**Solución**: 1. Asegúrate de que tus scripts R/Julia estén guardados en codificación UTF-8 2. Si usas caracteres especiales (acentos, ñ), revisa que la conversión funcione correctamente 3. Verifica la versión de R (debe ser 4.0+, que usa UTF-8 por defecto)

### Error: Funciones no se recargan al modificar el script

**Causa**: FileWatchService puede no estar detectando los cambios.

**Solución**: 1. Haz clic en "Reiniciar Entornos" en el Ribbon de NEVEN 2. Verifica que los archivos estén en `Documents/NEVEN/functions/` 3. Verifica los permisos del directorio

------------------------------------------------------------------------

## 10. Scripts de Ejemplo Incluidos

NEVEN viene con scripts de ejemplo en `Examples/`:

| Archivo                | Descripción                                      |
|------------------------------|------------------------------------------|
| `functions.r`          | Funciones básicas de R (suma, estadísticas)      |
| `functions.jl`         | Funciones básicas de Julia                       |
| `excel-functions.r`    | Funciones avanzadas de R para Excel (14KB)       |
| `excel-scripting.r`    | Automatización COM desde R                       |
| `excel-scripting.jl`   | Automatización COM desde Julia                   |
| `julia-rich-output.jl` | Salida enriquecida MIME (HTML, tablas, gráficos) |

Para usar los ejemplos, copia los archivos a tu directorio de funciones:

``` powershell
Copy-Item "Examples\*" "$env:USERPROFILE\Documents\NEVEN\functions\"
```

------------------------------------------------------------------------

*NEVEN: Potenciando Excel con el poder de R y Julia.* *Guía de usuario v2.0.0*