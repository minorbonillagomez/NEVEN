# NEVEN — Benchmarks de Latencia

## Proposito

Medir el rendimiento de NEVEN para demostrar que la arquitectura de procesos aislados
(Named Pipes + Protobuf) no introduce overhead inaceptable para uso interactivo.

## Preparacion

1. Copiar los archivos de benchmark a la carpeta de funciones:
   ```
   copy benchmark_latencia.R "%USERPROFILE%\Documents\NEVEN\functions\"
   copy benchmark_latencia.py "%USERPROFILE%\Documents\NEVEN\functions\"
   copy benchmark_latencia.jl "%USERPROFILE%\Documents\NEVEN\functions\"
   ```

2. Reiniciar Excel para que NEVEN cargue las funciones de benchmark.

3. Verificar que las funciones aparecen en el Asistente de Funciones (Shift+F3)
   bajo la categoria "NEVEN Benchmarks".

## Benchmark 1: Latencia Basica (Round-Trip)

Mide el tiempo de una operacion trivial (1+1) para aislar el overhead del pipe.

### Desde Excel

| Celda | Formula | Que mide |
|:---|:---|:---|
| A1 | `=R.NEVEN_Benchmark_Basico(100)` | 100 iteraciones de 1+1 en R |
| B1 | `=P.NEVEN_Benchmark_Basico_Py(100)` | 100 iteraciones de 1+1 en Python |
| C1 | `=J.NEVEN_Benchmark_Basico_Jl(100)` | 100 iteraciones de 1+1 en Julia |

### Resultado esperado

Tabla con: N, Media_ms, Mediana_ms, Min_ms, Max_ms, P95_ms, P99_ms

**Nota:** Estos tiempos miden la ejecucion DENTRO del motor (R/Julia/Python),
no el round-trip completo Excel→Pipe→Motor→Pipe→Excel. El round-trip agrega
~1-5ms adicionales por la serializacion Protobuf y el Named Pipe.

## Benchmark 2: Regresion Lineal

Mide el tiempo de una operacion estadistica real con datos sinteticos.

| Celda | Formula | Que mide |
|:---|:---|:---|
| A1 | `=R.NEVEN_Benchmark_Regresion(1000)` | Regresion con 1000 filas en R |
| B1 | `=P.NEVEN_Benchmark_Regresion_Py(1000)` | Regresion con 1000 filas en Python |
| C1 | `=J.NEVEN_Benchmark_Regresion_Jl(1000)` | Regresion con 1000 filas en Julia |

### Resultado esperado

Tabla con: N_filas, Tiempo_ms, R2, Intercepto, Pendiente

## Benchmark 3: Escalabilidad

Mide como escala el tiempo con el tamano de los datos (100 a 100K filas).

| Celda | Formula | Que mide |
|:---|:---|:---|
| A1 | `=R.NEVEN_Benchmark_Escalabilidad()` | Escalabilidad R (7 tamanos) |
| B1 | `=P.NEVEN_Benchmark_Escalabilidad_Py()` | Escalabilidad Python (7 tamanos) |
| C1 | `=J.NEVEN_Benchmark_Escalabilidad_Jl()` | Escalabilidad Julia (7 tamanos) |

### Resultado esperado

Tabla con: N_filas, Tiempo_ms para cada tamano (100, 500, 1K, 5K, 10K, 50K, 100K)

## Benchmark 4: Round-Trip Completo (Manual)

Para medir el round-trip completo Excel→Pipe→Motor→Pipe→Excel, usar este
procedimiento manual con cronometro:

1. Escribir `=NEVEN.R("Sys.sleep(0); 1+1")` en una celda
2. Presionar Enter y medir el tiempo hasta que aparece el resultado
3. Repetir 10 veces y promediar
4. Hacer lo mismo con `=NEVEN.J("sleep(0); 1+1")` y `=NEVEN.P("import time; time.sleep(0); 1+1")`

**Alternativa VBA:**
```vba
Sub BenchmarkRoundTrip()
    Dim t0 As Double, t1 As Double
    Dim i As Integer
    Dim total_r As Double, total_j As Double, total_p As Double
    
    ' R round-trip
    For i = 1 To 10
        t0 = Timer
        Range("Z1").Formula = "=NEVEN.R(""1+1"")"
        Application.Calculate
        t1 = Timer
        total_r = total_r + (t1 - t0)
    Next i
    
    ' Julia round-trip
    For i = 1 To 10
        t0 = Timer
        Range("Z1").Formula = "=NEVEN.J(""1+1"")"
        Application.Calculate
        t1 = Timer
        total_j = total_j + (t1 - t0)
    Next i
    
    ' Python round-trip
    For i = 1 To 10
        t0 = Timer
        Range("Z1").Formula = "=NEVEN.P(""1+1"")"
        Application.Calculate
        t1 = Timer
        total_p = total_p + (t1 - t0)
    Next i
    
    MsgBox "Round-trip promedio (10 iteraciones):" & vbCrLf & _
           "R: " & Format(total_r / 10 * 1000, "0.0") & " ms" & vbCrLf & _
           "Julia: " & Format(total_j / 10 * 1000, "0.0") & " ms" & vbCrLf & _
           "Python: " & Format(total_p / 10 * 1000, "0.0") & " ms"
End Sub
```

## Interpretacion de Resultados

### Latencia aceptable para uso interactivo

| Operacion | Aceptable | Bueno | Excelente |
|:---|:---|:---|:---|
| Round-trip trivial (1+1) | < 50 ms | < 20 ms | < 5 ms |
| Regresion 1K filas | < 500 ms | < 100 ms | < 20 ms |
| Regresion 100K filas | < 5 s | < 1 s | < 200 ms |

### Contexto

- VBA nativo: ~0.001 ms (sin overhead de pipe)
- Python in Excel (Microsoft, nube): ~500-2000 ms (latencia de red)
- NEVEN (local, pipe): ~5-20 ms para operaciones triviales

La ventaja de NEVEN sobre Python in Excel de Microsoft es que todo es local —
no hay latencia de red. La desventaja vs VBA es el overhead del pipe (~5 ms),
que es imperceptible para el usuario.

## Notas

- La primera llamada a Julia puede ser mas lenta (JIT compilation, ~15s sin sysimage)
- Las mediciones de Python son con CPython puro (sin numpy). Con numpy serian mas rapidas
- Los tiempos varian segun la maquina. Documentar specs del hardware al reportar
