# NEVEN v2.0: Manual de Primeros Pasos

**Universidad de Costa Rica — Tesis de Maestria**

------------------------------------------------------------------------

## 1. Requisitos

| Componente | Version | Descarga |
|:---|:---|:---|
| Windows | 10/11 (64 bits) | — |
| Microsoft Excel | 2016+ o Microsoft 365 | — |
| R | 4.4.1+ | https://cran.r-project.org |
| Julia | 1.12.6+ | https://julialang.org |
| Python | 3.13+ | https://python.org |
| Pandoc | 3.6+ | https://github.com/jgm/pandoc/releases |
| Quarto | 1.9.18+ | https://quarto.org/docs/download |

------------------------------------------------------------------------

## 2. Instalacion

1. Copiar los archivos de NEVEN a `C:\NEVEN\`
2. Crear junction para Quarto: `mklink /J C:\Quarto "C:\Program Files\Quarto"`
3. Registrar el Ribbon: `regsvr32 C:\NEVEN\NEVENRibbon.dll`
4. Abrir Excel --> Archivo --> Opciones --> Complementos --> Examinar --> `C:\NEVEN\NEVEN64.xll`

------------------------------------------------------------------------

## 3. Verificacion Rapida

Al abrir Excel deberia aparecer la pestana **NEVEN** en la cinta de opciones.

Prueba en celdas:

```
=NEVEN.R("1+1")        --> 2
=NEVEN.J("sqrt(144)")  --> 12
=NEVEN.P("1+1")        --> 2
=NEVEN.about()         --> Informacion del proyecto
```

Si retorna `#NOMBRE?`, el XLL no se cargo. Ver seccion 7 (Solucion de Problemas).

> **Nota:** Python es el tercer lenguaje junto a R y Julia. Si Python no esta instalado, NEVEN arranca limpiamente solo con R y Julia.

------------------------------------------------------------------------

## 4. Funciones Basicas

### R — Estadistica
```
=NEVEN.r("mean(c(10,20,30))")     --> 20
=NEVEN.r("sd(c(10,20,30))")       --> 10
```

### Julia — Matematica
```
=NEVEN.j("pi")                    --> 3.14159...
=NEVEN.j("factorial(10)")         --> 3628800
```

### Python — Proposito General
```
=NEVEN.P("1+1")                   --> 2
=NEVEN.P("sum([10,20,30])")       --> 60
=NEVEN.P("round(3.14159, 2)")     --> 3.14
```

### Funciones con rangos de Excel

Con una matriz 2x2 en A1:B2 (ej: 1,2,3,4):
```
=J.Algebra(A1:B2,0,0)              --> Lista de 12 procedimientos
=J.Algebra(A1:B2,0,6)              --> Determinante (-2)
=J.Algebra(A1:B2,0,4)              --> Valores propios
```

Con datos en A1:C10 (3 columnas numericas):
```
=J.Estadistica(A1:C10,0,0)         --> Lista de 8 procedimientos
=J.Estadistica(A1:C10,0,1)         --> Descriptiva (N, Media, Std, Min, Q1, Med, Q3, Max)
=J.Estadistica(A1:C10,0,2)         --> Matriz de correlacion
```

**Patron TipoOutput:** Todas las funciones usan el ultimo argumento como selector:
- `0` = ver lista de procedimientos disponibles
- `1, 2, 3...` = ejecutar el procedimiento correspondiente

------------------------------------------------------------------------

## 5. Graficos Interactivos

### Plotly desde rango de Excel

Con datos en A1:C4 (encabezados + 3 filas):
```
=NEVEN.v(R.GR_PlotlyView(A1:C4,0,0,"Mi Grafico",5))
```

### QuickPlot (9 tipos)
```
=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",1))   --> Barras
=NEVEN.v(R.GR_QuickPlot(A1:C4,0,0,"Titulo",7))   --> ggplot2 interactivo
```

------------------------------------------------------------------------

## 6. Pluto.jl y Quarto

### Enviar datos a Pluto
```
=NEVEN.pluto.data(A1:D20, "datos")    --> Envia rango a Julia
=NEVEN.pluto.start()                   --> Inicia servidor
=NEVEN.notebook.open("excel_data")     --> Abre dashboard con datos
```

### Renderizar documento Quarto
```
=NEVEN.q("C:/NEVEN/quarto/analisis_ventas.qmd")
```

------------------------------------------------------------------------

## 7. Solucion de Problemas

### Las funciones retornan #NOMBRE?
1. Verificar que el XLL esta cargado: Archivo --> Opciones --> Complementos
2. Si no aparece, Examinar --> `C:\NEVEN\NEVEN64.xll`

### El Ribbon no aparece
```powershell
# En PowerShell como administrador:
regsvr32 "C:\NEVEN\NEVENRibbon.dll"
# Si Excel lo deshabilito por un crash:
Remove-Item "HKCU:\Software\Microsoft\Office\16.0\Excel\Resiliency\DisabledItems" -Force
```

### Excel se congela al abrir
```powershell
Stop-Process -Name "EXCEL","ControlR","ControlJulia","ControlPython" -Force
```

### Paquetes R faltantes
```
=NEVEN.r("install.packages('plotly', repos='https://cran.r-project.org')")
```

------------------------------------------------------------------------

## 8. Ribbon — Botones Disponibles

| Grupo | Boton | Accion |
|:---|:---|:---|
| Motores | Consola R | Abre Rgui.exe |
| Motores | Consola Julia | Abre terminal Julia |
| Motores | Consola Python | Abre terminal Python |
| Motores | Actualizar | Re-registra funciones |
| Visualizacion | Abrir HTML | Seleccionar archivo HTML |
| Visualizacion | Presentaciones | Editor Impress.js |
| Visualizacion | Cerrar Visores | Cierra ventanas WebView2 |
| Pluto.jl | Iniciar Pluto | Arranca servidor |
| Pluto.jl | Notebooks | Lista de notebooks |
| Pluto.jl | Detener Pluto | Detiene servidor |
| Quarto | Renderizar QMD | Seleccionar .qmd |
| Configuracion | Carpeta Scripts | Abre C:\NEVEN |
| Configuracion | Config JSON | Abre configuracion |
| Configuracion | Acerca de | Info del proyecto |

------------------------------------------------------------------------

## 9. Crear Funciones Propias

### Funcion R
Crear archivo en `C:\Users\<usuario>\Documents\NEVEN\functions\mi_funcion.R`:

```r
CalcularMargen <- function(ingresos, costos) {
  return((ingresos - costos) / ingresos * 100)
}
attr(CalcularMargen, "description") <- list(
  "Calcula margen de beneficio en porcentaje",
  ingresos = "Ingresos totales",
  costos = "Costos totales"
)
```

Usar en Excel: `=R.CalcularMargen(A1, B1)`

### Funcion Julia
Agregar al archivo `functions.jl`:

```julia
function MiCalculo(datos, parametro=0)
    return sum(Float64.(datos)) * parametro
end
```

Usar en Excel: `=J.MiCalculo(A1:A10, 5)`

### Funcion Python
Crear archivo en `C:\Users\<usuario>\Documents\NEVEN\functions\mi_funcion.py`:

```python
def CalcularIVA(monto, tasa=13.0):
    """Calcula el IVA de un monto.

    Args:
        monto: Monto base
        tasa: Porcentaje de IVA (default: 13%)
    """
    return monto * (tasa / 100)
```

Usar en Excel: `=P.CalcularIVA(A1, 13)`

> **Nota:** El prefijo para funciones Python registradas es `P` (mayuscula), consistente con `R.` y `J.` para funciones de usuario.

------------------------------------------------------------------------

## 10. Mas Ejemplos

Ver la carpeta `Ejemplos/` del proyecto con subcarpetas organizadas por lenguaje (R, Julia, Python, Quarto) y 80+ formulas listas para copiar y pegar.

------------------------------------------------------------------------

*NEVEN v2.0 — Universidad de Costa Rica*
