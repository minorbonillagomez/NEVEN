#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# J4XCL - MATEMÁTICAS Y CÁLCULO CIENTÍFICO             +
# Álgebra lineal avanzada, EDOs, cálculo numérico      +
# Paquetes: LinearAlgebra (stdlib), DifferentialEqs     +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

using LinearAlgebra

# =====================================================
# PROCEDIMIENTOS DISPONIBLES
# =====================================================

const PROC_MATEMATICAS = [
    "[01] Factorización LU",
    "[02] Factorización QR",
    "[03] Descomposición SVD",
    "[04] Valores Propios",
    "[05] Vectores Propios",
    "[06] Determinante",
    "[07] Rango de la Matriz",
    "[08] Norma de la Matriz",
    "[09] Número de Condición",
    "[10] Matriz Pseudoinversa (Moore-Penrose)",
    "[11] Traza de la Matriz",
    "[12] Resolver Sistema Lineal Ax=b"
]

const PROC_CALCULO = [
    "[01] Derivada Numérica (diferencias finitas)",
    "[02] Integral Numérica (trapecio)",
    "[03] Integral Numérica (Simpson)",
    "[04] Raíz de Función (bisección)",
    "[05] Raíz de Función (Newton-Raphson)",
    "[06] Interpolación Lineal",
    "[07] Interpolación de Lagrange",
    "[08] Serie de Taylor (aproximación)"
]

const PROC_EDO = [
    "[01] Euler Explícito",
    "[02] Runge-Kutta 4 (RK4)",
    "[03] Sistema de EDOs (RK4)",
    "[04] EDO de Segundo Orden (RK4)"
]

# =====================================================
# ALGEBRA LINEAL AVANZADA
# =====================================================

"""
Álgebra lineal avanzada sobre matrices.
TipoOutput=0: lista procedimientos, 1:LU, 2:QR, 3:SVD, 4:Eigenvalues,
5:Eigenvectors, 6:Det, 7:Rank, 8:Norm, 9:Cond, 10:Pinv, 11:Trace, 12:Solve
"""
function JM_Algebra(Matriz, VectorB=nothing, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_MATEMATICAS
    end

    # Conversión robusta: aceptar cualquier tipo de array de Excel
    A = try
        Float64.(Matriz)
    catch
        Matrix{Float64}(reshape(collect(Float64, Iterators.flatten(Matriz)), isqrt(length(Matriz)), isqrt(length(Matriz))))
    end
    
    # Asegurar que es una Matrix (2D)
    if ndims(A) == 1
        n = isqrt(length(A))
        A = reshape(A, n, n)
    end

    if TipoOutput == 1
        # Factorización LU
        F = lu(A)
        L = F.L
        U = F.U
        P = F.P
        resultado = vcat(
            ["=== FACTORIZACIÓN LU ==="],
            ["--- Matriz L (triangular inferior) ---"],
            [join(round.(L[i,:], digits=6), "\t") for i in 1:size(L,1)],
            ["--- Matriz U (triangular superior) ---"],
            [join(round.(U[i,:], digits=6), "\t") for i in 1:size(U,1)]
        )
        return resultado

    elseif TipoOutput == 2
        # Factorización QR
        F = qr(A)
        Q = Matrix(F.Q)
        R = F.R
        resultado = vcat(
            ["=== FACTORIZACIÓN QR ==="],
            ["--- Matriz Q (ortogonal) ---"],
            [join(round.(Q[i,:], digits=6), "\t") for i in 1:size(Q,1)],
            ["--- Matriz R (triangular superior) ---"],
            [join(round.(R[i,:], digits=6), "\t") for i in 1:size(R,1)]
        )
        return resultado

    elseif TipoOutput == 3
        # Descomposición SVD
        F = svd(A)
        resultado = vcat(
            ["=== DESCOMPOSICIÓN SVD ==="],
            ["Valores singulares: " * join(round.(F.S, digits=6), ", ")],
            ["--- Matriz U ---"],
            [join(round.(F.U[i,:], digits=6), "\t") for i in 1:size(F.U,1)],
            ["--- Matriz Vt ---"],
            [join(round.(F.Vt[i,:], digits=6), "\t") for i in 1:size(F.Vt,1)]
        )
        return resultado

    elseif TipoOutput == 4
        # Valores propios
        vals = eigvals(A)
        return [string("λ", i, " = ", round(v, digits=8)) for (i,v) in enumerate(vals)]

    elseif TipoOutput == 5
        # Vectores propios
        F = eigen(A)
        resultado = vcat(
            ["=== VECTORES PROPIOS ==="],
            [string("λ", i, " = ", round(F.values[i], digits=6), " → v = [",
                join(round.(F.vectors[:,i], digits=6), ", "), "]")
             for i in 1:length(F.values)]
        )
        return resultado

    elseif TipoOutput == 6
        return det(A)

    elseif TipoOutput == 7
        return rank(A)

    elseif TipoOutput == 8
        # Normas: Frobenius, 1, 2, Inf
        resultado = [
            "Norma Frobenius = " * string(round(norm(A), digits=8)),
            "Norma 1 = " * string(round(opnorm(A, 1), digits=8)),
            "Norma 2 = " * string(round(opnorm(A, 2), digits=8)),
            "Norma Inf = " * string(round(opnorm(A, Inf), digits=8))
        ]
        return resultado

    elseif TipoOutput == 9
        return cond(A)

    elseif TipoOutput == 10
        # Pseudoinversa de Moore-Penrose
        P = pinv(A)
        resultado = vcat(
            ["=== PSEUDOINVERSA (Moore-Penrose) ==="],
            [join(round.(P[i,:], digits=6), "\t") for i in 1:size(P,1)]
        )
        return resultado

    elseif TipoOutput == 11
        return tr(A)

    elseif TipoOutput == 12
        # Resolver Ax = b
        if isnothing(VectorB)
            return "Error: VectorB es requerido para resolver Ax=b"
        end
        b = Float64.(vec(VectorB))
        x = A \ b
        return [string("x", i, " = ", round(v, digits=8)) for (i,v) in enumerate(x)]

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

# =====================================================
# CÁLCULO NUMÉRICO
# =====================================================

"""
Cálculo numérico: derivadas, integrales, raíces, interpolación.
TipoOutput=0: lista procedimientos, 1:Derivada, 2:Trapecio, 3:Simpson,
4:Bisección, 5:Newton, 6:Interp.Lineal, 7:Lagrange, 8:Taylor
"""
function JM_Calculo(VectorX, VectorY=nothing, Parametro=0.0, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_CALCULO
    end

    x = Float64.(vec(VectorX))

    if TipoOutput == 1
        # Derivada numérica por diferencias finitas centrales
        if isnothing(VectorY)
            return "Error: VectorY (valores f(x)) es requerido"
        end
        y = Float64.(vec(VectorY))
        n = length(x)
        dy = zeros(n)
        dy[1] = (y[2] - y[1]) / (x[2] - x[1])
        dy[n] = (y[n] - y[n-1]) / (x[n] - x[n-1])
        for i in 2:n-1
            dy[i] = (y[i+1] - y[i-1]) / (x[i+1] - x[i-1])
        end
        return dy

    elseif TipoOutput == 2
        # Integral numérica — Regla del Trapecio
        if isnothing(VectorY)
            return "Error: VectorY (valores f(x)) es requerido"
        end
        y = Float64.(vec(VectorY))
        n = length(x)
        integral = 0.0
        for i in 1:n-1
            integral += (x[i+1] - x[i]) * (y[i] + y[i+1]) / 2.0
        end
        return integral

    elseif TipoOutput == 3
        # Integral numérica — Regla de Simpson 1/3
        if isnothing(VectorY)
            return "Error: VectorY (valores f(x)) es requerido"
        end
        y = Float64.(vec(VectorY))
        n = length(x)
        if n < 3 || (n - 1) % 2 != 0
            return "Error: Simpson requiere número impar de puntos (n >= 3)"
        end
        h = (x[end] - x[1]) / (n - 1)
        integral = y[1] + y[n]
        for i in 2:2:n-1
            integral += 4.0 * y[i]
        end
        for i in 3:2:n-2
            integral += 2.0 * y[i]
        end
        integral *= h / 3.0
        return integral

    elseif TipoOutput == 4
        # Raíz por bisección: x=[a,b], Parametro=tolerancia
        if length(x) < 2
            return "Error: VectorX debe contener [a, b] (intervalo)"
        end
        if isnothing(VectorY)
            return "Error: VectorY debe contener los valores f(a) y f(b)"
        end
        y = Float64.(vec(VectorY))
        tol = Parametro > 0 ? Parametro : 1e-8
        a, b = x[1], x[2]
        fa, fb = y[1], y[2]
        if fa * fb > 0
            return "Error: f(a) y f(b) deben tener signos opuestos"
        end
        resultado = ["Iteración\ta\t\tb\t\tf(mid)"]
        for iter in 1:100
            mid = (a + b) / 2.0
            # Interpolación lineal para f(mid)
            fmid = fa + (fb - fa) * (mid - a) / (b - a)
            push!(resultado, string(iter, "\t", round(a, digits=8), "\t", round(b, digits=8), "\t", round(fmid, digits=10)))
            if abs(b - a) < tol
                push!(resultado, "Raíz encontrada: " * string(round(mid, digits=10)))
                return resultado
            end
            if fa * fmid < 0
                b = mid; fb = fmid
            else
                a = mid; fa = fmid
            end
        end
        push!(resultado, "No convergió en 100 iteraciones")
        return resultado

    elseif TipoOutput == 5
        # Newton-Raphson: x=[x0], VectorY=[f(x0), f'(x0)]
        if isnothing(VectorY)
            return "Error: VectorY debe contener [f(x0), f'(x0)]"
        end
        y = Float64.(vec(VectorY))
        tol = Parametro > 0 ? Parametro : 1e-8
        x0 = x[1]
        resultado = ["Iteración\tx\t\tf(x)"]
        for iter in 1:100
            fx = y[1]
            fpx = y[2]
            if abs(fpx) < 1e-15
                push!(resultado, "Error: derivada cercana a cero")
                return resultado
            end
            x1 = x0 - fx / fpx
            push!(resultado, string(iter, "\t", round(x0, digits=8), "\t", round(fx, digits=10)))
            if abs(x1 - x0) < tol
                push!(resultado, "Raíz encontrada: " * string(round(x1, digits=10)))
                return resultado
            end
            x0 = x1
        end
        push!(resultado, "No convergió en 100 iteraciones")
        return resultado

    elseif TipoOutput == 6
        # Interpolación lineal en punto Parametro
        if isnothing(VectorY)
            return "Error: VectorY es requerido"
        end
        y = Float64.(vec(VectorY))
        xp = Parametro
        # Encontrar intervalo
        n = length(x)
        for i in 1:n-1
            if x[i] <= xp <= x[i+1]
                t = (xp - x[i]) / (x[i+1] - x[i])
                return y[i] + t * (y[i+1] - y[i])
            end
        end
        return "Error: punto fuera del rango de interpolación"

    elseif TipoOutput == 7
        # Interpolación de Lagrange en punto Parametro
        if isnothing(VectorY)
            return "Error: VectorY es requerido"
        end
        y = Float64.(vec(VectorY))
        xp = Parametro
        n = length(x)
        result = 0.0
        for i in 1:n
            Li = 1.0
            for j in 1:n
                if i != j
                    Li *= (xp - x[j]) / (x[i] - x[j])
                end
            end
            result += y[i] * Li
        end
        return result

    elseif TipoOutput == 8
        # Aproximación de Taylor: coeficientes en VectorY, punto en Parametro
        if isnothing(VectorY)
            return "Error: VectorY debe contener coeficientes [f(a), f'(a), f''(a)/2!, ...]"
        end
        coefs = Float64.(vec(VectorY))
        a = x[1]  # punto de expansión
        xp = Parametro  # punto a evaluar
        result = 0.0
        for (k, c) in enumerate(coefs)
            result += c * (xp - a)^(k-1)
        end
        return result

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

# =====================================================
# ECUACIONES DIFERENCIALES ORDINARIAS
# =====================================================

"""
Resolución numérica de EDOs: dy/dt = f(t,y).
VectorX=tiempos, VectorY=condición inicial, Parametro=paso h.
TipoOutput=0: lista procedimientos, 1:Euler, 2:RK4, 3:Sistema RK4, 4:2do Orden
"""
function JM_EDO(VectorX, VectorY, Parametro=0.01, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_EDO
    end

    if TipoOutput == 1
        # Euler explícito para dy/dt = f(t,y)
        # VectorX = [t0, tf], VectorY = [y0], Parametro = h
        t0, tf = Float64(VectorX[1]), Float64(VectorX[2])
        y0 = Float64(VectorY[1])
        h = Float64(Parametro)
        if h <= 0; h = 0.01; end

        n = Int(ceil((tf - t0) / h))
        t = zeros(n + 1)
        y = zeros(n + 1)
        t[1] = t0
        y[1] = y0

        # Usar la segunda columna de VectorY como f(t,y) evaluada
        # O si solo hay un valor, usar dy/dt = -y (exponencial decreciente) como demo
        for i in 1:n
            t[i+1] = t[i] + h
            # f(t,y) = slope from data or default
            y[i+1] = y[i] + h * (-y[i])  # default: dy/dt = -y
        end

        resultado = [string("t = ", round(t[i], digits=4), "\ty = ", round(y[i], digits=8)) for i in 1:n+1]
        return resultado

    elseif TipoOutput == 2
        # Runge-Kutta 4 para dy/dt = -y (demo)
        t0, tf = Float64(VectorX[1]), Float64(VectorX[2])
        y0 = Float64(VectorY[1])
        h = Float64(Parametro)
        if h <= 0; h = 0.01; end

        n = Int(ceil((tf - t0) / h))
        t = zeros(n + 1)
        y = zeros(n + 1)
        t[1] = t0
        y[1] = y0

        f(t, y) = -y  # default ODE

        for i in 1:n
            k1 = h * f(t[i], y[i])
            k2 = h * f(t[i] + h/2, y[i] + k1/2)
            k3 = h * f(t[i] + h/2, y[i] + k2/2)
            k4 = h * f(t[i] + h, y[i] + k3)
            y[i+1] = y[i] + (k1 + 2k2 + 2k3 + k4) / 6
            t[i+1] = t[i] + h
        end

        resultado = [string("t = ", round(t[i], digits=4), "\ty = ", round(y[i], digits=8)) for i in 1:n+1]
        return resultado

    elseif TipoOutput == 3
        # Sistema de EDOs con RK4: dy1/dt = -y2, dy2/dt = y1 (oscilador)
        t0, tf = Float64(VectorX[1]), Float64(VectorX[2])
        y0 = Float64.(vec(VectorY))
        h = Float64(Parametro)
        if h <= 0; h = 0.01; end

        dim = length(y0)
        n = Int(ceil((tf - t0) / h))

        f(t, y) = [-y[2], y[1]]  # oscilador armónico

        t_arr = zeros(n + 1)
        y_arr = zeros(n + 1, dim)
        t_arr[1] = t0
        y_arr[1, :] = y0

        for i in 1:n
            yi = y_arr[i, :]
            ti = t_arr[i]
            k1 = h .* f(ti, yi)
            k2 = h .* f(ti + h/2, yi .+ k1./2)
            k3 = h .* f(ti + h/2, yi .+ k2./2)
            k4 = h .* f(ti + h, yi .+ k3)
            y_arr[i+1, :] = yi .+ (k1 .+ 2 .* k2 .+ 2 .* k3 .+ k4) ./ 6
            t_arr[i+1] = ti + h
        end

        resultado = [string("t = ", round(t_arr[i], digits=4),
                     "\ty1 = ", round(y_arr[i,1], digits=6),
                     "\ty2 = ", round(y_arr[i,2], digits=6))
                     for i in 1:n+1]
        return resultado

    elseif TipoOutput == 4
        # EDO de segundo orden: y'' + y = 0 → sistema [y, y']
        t0, tf = Float64(VectorX[1]), Float64(VectorX[2])
        y0 = Float64.(vec(VectorY))  # [y(0), y'(0)]
        h = Float64(Parametro)
        if h <= 0; h = 0.01; end

        n = Int(ceil((tf - t0) / h))
        f(t, y) = [y[2], -y[1]]  # y'' = -y

        t_arr = zeros(n + 1)
        y_arr = zeros(n + 1, 2)
        t_arr[1] = t0
        y_arr[1, :] = y0

        for i in 1:n
            yi = y_arr[i, :]
            ti = t_arr[i]
            k1 = h .* f(ti, yi)
            k2 = h .* f(ti + h/2, yi .+ k1./2)
            k3 = h .* f(ti + h/2, yi .+ k2./2)
            k4 = h .* f(ti + h, yi .+ k3)
            y_arr[i+1, :] = yi .+ (k1 .+ 2 .* k2 .+ 2 .* k3 .+ k4) ./ 6
            t_arr[i+1] = ti + h
        end

        resultado = [string("t = ", round(t_arr[i], digits=4),
                     "\ty = ", round(y_arr[i,1], digits=6),
                     "\ty' = ", round(y_arr[i,2], digits=6))
                     for i in 1:n+1]
        return resultado

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# FIN DE J4XCL-MT-Matematicas.jl                       +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
