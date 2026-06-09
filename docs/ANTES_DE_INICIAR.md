# NEVEN — Antes de Iniciar

Guía rápida para una experiencia satisfactoria con NEVEN. Léala antes de abrir Excel por primera vez después de instalar.

---

## 1. Requisitos previos

### Runtimes de lenguaje

NEVEN necesita al menos un motor de lenguaje instalado en su máquina:

| Motor | Requerido | Descarga | Notas |
|:---|:---:|:---|:---|
| **R** | Sí (recomendado) | [https://cran.r-project.org](https://cran.r-project.org) | Versión 4.4.1 o superior. Instale desde CRAN. |
| **Julia** | Opcional | [https://julialang.org/downloads](https://julialang.org/downloads) | Versión 1.12.6 o superior. Si no la instala, las funciones `=J.func()` retornarán un mensaje indicando que Julia no está disponible. |
| **Python** | Opcional | [https://www.python.org/downloads](https://www.python.org/downloads) | Versión 3.10 o superior. Solo necesario para las funciones de inteligencia artificial (`=P.ai_call()`). |

**NEVEN funciona perfectamente solo con R instalado.** Julia y Python son opcionales y el sistema se adapta automáticamente a los motores disponibles.

### Sistema operativo

- Windows 10 o superior (64 bits)
- Microsoft Excel 2013 o superior (idealmente Microsoft 365)
- WebView2 Runtime (preinstalado en Windows 10/11)

---

## 2. Configuración de Excel (IMPORTANTE)

### Modo de cálculo

**Antes de trabajar con fórmulas NEVEN, cambie Excel a cálculo manual:**

1. Vaya a **Fórmulas → Opciones de cálculo → Manual**
2. O presione `Ctrl+F9` para recalcular manualmente cuando lo necesite

**¿Por qué?** En modo automático, Excel recalcula TODAS las fórmulas cada vez que cambia una celda. Si tiene 50 fórmulas NEVEN en una hoja, cada cambio dispararía 50 llamadas simultáneas a R/Julia, saturando la comunicación y potencialmente congelando Excel durante varios segundos.

**Recomendación:** Trabaje en modo manual y use `F9` o `Ctrl+Shift+F9` para recalcular cuando esté listo.

---

## 3. Primera vez que abre Excel después de instalar

### Tiempo de arranque

- **Con R:** Excel abre en 5-10 segundos (R conecta rápidamente)
- **Con Julia (sin sysimage):** La primera llamada a Julia puede tardar 1-5 minutos mientras compila (JIT). Esto es normal y solo ocurre una vez por sesión.
- **Con Julia (con sysimage):** Arranque instantáneo (~1 segundo).

### Generar la sysimage de Julia (recomendado)

**Durante la instalación**, NEVEN le preguntará si desea generar la sysimage de Julia. Esto tarda 5-10 minutos pero elimina el tiempo de espera en la primera llamada de cada sesión. **Se recomienda aceptar.**

Si declinó durante la instalación, puede generarla después ejecutando:

```powershell
julia C:\NEVEN\scripts\build-julia-sysimage.jl
```

Este proceso genera `C:\NEVEN\neven_julia.dll` (~415 MB). Solo necesita hacerlo una vez (o cuando actualice Julia).

**Nota:** Puede usar NEVEN con Julia sin la sysimage — simplemente la primera llamada de cada sesión tardará más. La sysimage es una optimización de rendimiento, no un requisito.

### Verificación rápida

Después de abrir Excel, pruebe en una celda:

```
=NEVEN.r("1+1")
```

Si retorna `2`, todo está funcionando. Si retorna `#NOMBRE?`, consulte la sección de solución de problemas más abajo.

---

## 4. Windows SmartScreen y antivirus

### SmartScreen bloquea el instalador o los ejecutables

Windows puede mostrar un aviso "Windows protegió su PC" al ejecutar NEVEN por primera vez. Esto ocurre porque los binarios no están firmados con un certificado comercial (es un proyecto académico open source).

**Solución:**
1. Haga clic en "Más información"
2. Haga clic en "Ejecutar de todas formas"

### Antivirus bloquea ControlR.exe / ControlJulia.exe

Algunos antivirus pueden marcar los procesos hijo de NEVEN como sospechosos porque:
- Son ejecutables que se comunican via Named Pipes
- Se lanzan automáticamente al abrir Excel

**Solución:** Agregue `C:\NEVEN\` como exclusión en su antivirus:
- **Windows Defender:** Configuración → Seguridad → Protección contra virus → Exclusiones → Agregar carpeta → `C:\NEVEN\`
- **Otros antivirus:** Busque "exclusiones" o "lista blanca" en la configuración

---

## 5. Paquetes R necesarios

Las funciones estadísticas de NEVEN dependen de paquetes R que deben estar instalados. El instalador intenta instalarlos automáticamente, pero si alguna función retorna un error de paquete faltante:

Abra R directamente (no desde Excel) y ejecute:

```r
install.packages(c("jsonlite", "rpivotTable", "htmlwidgets", "ggplot2", "plotly",
                   "lme4", "survival", "plm", "forecast", "psych"))
```

---

## 6. Al compartir archivos Excel con fórmulas NEVEN

### El destinatario NO tiene NEVEN instalado

Si comparte un archivo Excel que contiene fórmulas NEVEN (`=R.MR_Lineal(...)`, `=NEVEN.v(...)`, etc.) con alguien que no tiene NEVEN:
- Todas las fórmulas mostrarán `#NOMBRE?`
- Los datos en las celdas donde NEVEN ya calculó se perderán

**Recomendación antes de compartir:**
1. Seleccione las celdas con resultados de NEVEN
2. Copie (`Ctrl+C`)
3. Pegue como valores (`Ctrl+Shift+V` → Valores)
4. Ahora los resultados están fijos como texto/números y no dependen de NEVEN

### Seguridad al recibir archivos

Si recibe un archivo Excel de una fuente no confiable que contiene fórmulas NEVEN, el sandbox de seguridad bloqueará automáticamente cualquier intento de ejecutar comandos del sistema, acceder a archivos, o conectarse a la red. No necesita hacer nada — la protección es automática.

---

## 7. Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|:---|:---|:---|
| `#NOMBRE?` en todas las fórmulas | XLL no cargó | Cerrar Excel completamente, esperar 5 segundos, reabrir |
| Excel se congela al abrir | Proceso zombie en puerto 1234 | Abrir Task Manager → matar `julia.exe` → reabrir Excel |
| Julia tarda minutos | Primera compilación JIT (sin sysimage) | Esperar — solo ocurre una vez por sesión |
| "R service unavailable" | R no está instalado o no fue detectado | Verificar instalación de R. Reiniciar Excel |
| Sandbox bloquea código legítimo | El sandbox es conservador por diseño | Para desarrollo: editar `neven-config.json` → `"sandboxEnabled": false` |
| Gráficos no se abren | WebView2 no disponible | Verificar Windows 10+. Instalar Edge si fue removido |
| Ribbon "NEVEN" no aparece | COM Add-in no registrado | Ejecutar `Install-NEVEN.ps1 -RegisterOnly` como administrador |

---

## 8. Estructura de carpetas del usuario

Después de instalar, su carpeta de trabajo es:

```
Documents\NEVEN\
├── functions\     → Coloque aquí sus archivos .R, .jl, .py
│                    Se registran automáticamente como fórmulas Excel
├── notebooks\     → Coloque aquí notebooks .jl, .R, .py
│                    Aparecen en =NEVEN.notebook.list()
├── prompts\       → Templates de AI editables (.txt)
└── graphics\      → Salida de gráficos R
```

**Para agregar una función personalizada:**
1. Cree un archivo `mi_funcion.R` en `Documents\NEVEN\functions\`
2. Reinicie Excel
3. Use `=R.mi_funcion(...)` en cualquier celda

---

## 9. Rendimiento

| Operación | Tiempo esperado | Notas |
|:---|:---|:---|
| Abrir Excel (con R) | 5-10 segundos | Normal |
| Primera llamada Julia (sin sysimage) | 1-5 minutos | Solo la primera vez por sesión |
| Llamada típica R (regresión, ACP) | < 1 segundo | Depende del tamaño de datos |
| Llamada típica Julia (álgebra, EDO) | < 1 segundo | Después del JIT |
| Dashboard interactivo | 2-5 segundos | Genera HTML + abre visor |
| Quarto render | 5-30 segundos | Depende de la complejidad del documento |

---

## 10. Soporte

- **Documentación completa:** Botón "Documentación" en la pestaña NEVEN del Ribbon
- **Diccionario de funciones:** Botón "Diccionario" — 95 funciones con ejemplos
- **Diagnóstico:** `=NEVEN.status()` muestra el estado de todos los motores
- **Log del sistema:** `C:\NEVEN\neven.log` — registro detallado de operaciones
- **Código fuente:** [https://github.com/minor-bonilla/NEVEN](https://github.com/minor-bonilla/NEVEN)

---

*NEVEN v2.0 — Minor Bonilla Gómez*