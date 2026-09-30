# NEVEN Benchmark — Latencia de Llamadas Python
# Ejecutar desde Excel: =NEVEN.P("exec(open('benchmark_latencia.py').read())")
# O usar las funciones individuales via =P.func()

import time
import random
import math

def NEVEN_Benchmark_Basico_Py(n_iteraciones=100):
    """Benchmark: mide latencia basica de Python (N iteraciones de 1+1).
    
    Args:
        n_iteraciones: Numero de iteraciones (default: 100)
    """
    tiempos = []
    for _ in range(int(n_iteraciones)):
        t0 = time.perf_counter()
        resultado = 1 + 1
        t1 = time.perf_counter()
        tiempos.append((t1 - t0) * 1000)  # milisegundos
    
    tiempos.sort()
    n = len(tiempos)
    media = sum(tiempos) / n
    mediana = tiempos[n // 2]
    p95 = tiempos[int(n * 0.95)]
    p99 = tiempos[int(n * 0.99)]
    
    return [
        ["Metrica", "Valor"],
        ["N", n],
        ["Media_ms", round(media, 6)],
        ["Mediana_ms", round(mediana, 6)],
        ["Min_ms", round(min(tiempos), 6)],
        ["Max_ms", round(max(tiempos), 6)],
        ["P95_ms", round(p95, 6)],
        ["P99_ms", round(p99, 6)]
    ]


def NEVEN_Benchmark_Regresion_Py(n_filas=1000):
    """Benchmark: regresion lineal simple en Python puro (sin numpy).
    
    Args:
        n_filas: Numero de filas de datos (default: 1000)
    """
    random.seed(42)
    n = int(n_filas)
    x = [random.gauss(0, 1) for _ in range(n)]
    y = [2 * xi + random.gauss(0, 0.5) for xi in x]
    
    t0 = time.perf_counter()
    
    # Regresion lineal por minimos cuadrados
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    
    pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    intercepto = (sum_y - pendiente * sum_x) / n
    
    # R-cuadrado
    y_pred = [intercepto + pendiente * xi for xi in x]
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    y_mean = sum_y / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    r2 = 1 - ss_res / ss_tot
    
    t1 = time.perf_counter()
    tiempo_ms = (t1 - t0) * 1000
    
    return [
        ["Metrica", "Valor"],
        ["N_filas", n],
        ["Tiempo_ms", round(tiempo_ms, 2)],
        ["R2", round(r2, 6)],
        ["Intercepto", round(intercepto, 6)],
        ["Pendiente", round(pendiente, 6)]
    ]


def NEVEN_Benchmark_Escalabilidad_Py():
    """Benchmark: escalabilidad de regresion lineal Python (100 a 100K filas)."""
    tamanos = [100, 500, 1000, 5000, 10000, 50000, 100000]
    resultados = [["N_filas", "Tiempo_ms"]]
    
    for n in tamanos:
        random.seed(42)
        x = [random.gauss(0, 1) for _ in range(n)]
        y = [2 * xi + random.gauss(0, 0.5) for xi in x]
        
        t0 = time.perf_counter()
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercepto = (sum_y - pendiente * sum_x) / n
        
        t1 = time.perf_counter()
        resultados.append([n, round((t1 - t0) * 1000, 2)])
    
    return resultados
