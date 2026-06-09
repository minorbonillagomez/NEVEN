# NEVEN Benchmark — Latencia de Llamadas Julia
# Las funciones se registran automaticamente como J.func() en Excel

using Statistics
using Random
using LinearAlgebra

"""
Benchmark: mide latencia basica de Julia (N iteraciones de 1+1).
"""
function NEVEN_Benchmark_Basico_Jl(n_iteraciones=100)
    n = Int(n_iteraciones)
    tiempos = zeros(n)
    for i in 1:n
        t0 = time_ns()
        resultado = 1 + 1
        t1 = time_ns()
        tiempos[i] = (t1 - t0) / 1e6  # nanosegundos a milisegundos
    end
    
    return [
        n,
        round(mean(tiempos), digits=6),
        round(median(tiempos), digits=6),
        round(minimum(tiempos), digits=6),
        round(maximum(tiempos), digits=6),
        round(quantile(tiempos, 0.95), digits=6),
        round(quantile(tiempos, 0.99), digits=6)
    ]
end

"""
Benchmark: regresion lineal con N filas usando algebra lineal de Julia.
"""
function NEVEN_Benchmark_Regresion_Jl(n_filas=1000)
    n = Int(n_filas)
    Random.seed!(42)
    x = randn(n)
    y = 2.0 .* x .+ randn(n) .* 0.5
    
    t0 = time_ns()
    X = hcat(ones(n), x)
    beta = X \ y
    y_pred = X * beta
    ss_res = sum((y .- y_pred).^2)
    ss_tot = sum((y .- mean(y)).^2)
    r2 = 1.0 - ss_res / ss_tot
    t1 = time_ns()
    
    tiempo_ms = (t1 - t0) / 1e6
    
    return [n, round(tiempo_ms, digits=2), round(r2, digits=6), round(beta[1], digits=6), round(beta[2], digits=6)]
end

"""
Benchmark: escalabilidad de regresion lineal Julia (100 a 100K filas).
"""
function NEVEN_Benchmark_Escalabilidad_Jl()
    tamanos = [100, 500, 1000, 5000, 10000, 50000, 100000]
    resultados = zeros(length(tamanos), 2)
    
    for (idx, n) in enumerate(tamanos)
        Random.seed!(42)
        x = randn(n)
        y = 2.0 .* x .+ randn(n) .* 0.5
        
        t0 = time_ns()
        X = hcat(ones(n), x)
        beta = X \ y
        t1 = time_ns()
        
        resultados[idx, 1] = n
        resultados[idx, 2] = round((t1 - t0) / 1e6, digits=2)
    end
    
    return resultados
end
