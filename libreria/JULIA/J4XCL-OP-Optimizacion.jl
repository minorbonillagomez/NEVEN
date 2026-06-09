#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# J4XCL - OPTIMIZACIÓN MATEMÁTICA                      +
# Programación lineal, no-lineal, restricciones        +
# Paquetes: stdlib (LinearAlgebra)                     +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

using LinearAlgebra

# =====================================================
# PROCEDIMIENTOS DISPONIBLES
# =====================================================

const PROC_OPTIMIZACION = [
    "[01] Descenso de Gradiente (función cuadrática)",
    "[02] Descenso de Gradiente con Momentum",
    "[03] Método de Newton (optimización)",
    "[04] Búsqueda de Sección Áurea (1D)",
    "[05] Simplex (Programación Lineal)",
    "[06] Mínimos Cuadrados con Restricción de No-Negatividad",
    "[07] Programación Cuadrática (QP simple)"
]

# =====================================================
# OPTIMIZACIÓN
# =====================================================

"""
Optimización matemática: gradiente, Newton, simplex, programación lineal.
TipoOutput=0: lista procedimientos, 1:Gradiente, 2:Momentum, 3:Newton,
4:Sección Áurea, 5:Simplex, 6:NNLS, 7:QP
"""
function JO_Optimizar(Matriz, Vector=nothing, Parametro=0.01, MaxIter=1000, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_OPTIMIZACION
    end

    if TipoOutput == 1
        # Descenso de gradiente para min f(x) = 0.5 * x'Ax - b'x
        # Matriz = A (simétrica positiva definida), Vector = b
        A = Float64.(Matriz)
        if isnothing(Vector)
            return "Error: Vector (b) es requerido"
        end
        b = Float64.(vec(Vector))
        lr = Float64(Parametro)
        n = size(A, 1)
        x = zeros(n)
        max_iter = Int(MaxIter)

        resultado = ["Iter\tf(x)\t||grad||"]
        for iter in 1:max_iter
            grad = A * x - b
            fx = 0.5 * dot(x, A * x) - dot(b, x)
            gnorm = norm(grad)
            if iter <= 20 || iter % 100 == 0
                push!(resultado, string(iter, "\t", round(fx, digits=6), "\t", round(gnorm, digits=8)))
            end
            if gnorm < 1e-8
                push!(resultado, "Convergió en $iter iteraciones")
                push!(resultado, "x* = [" * join(round.(x, digits=6), ", ") * "]")
                push!(resultado, "f(x*) = " * string(round(fx, digits=8)))
                return resultado
            end
            x = x - lr * grad
        end
        fx = 0.5 * dot(x, A * x) - dot(b, x)
        push!(resultado, "No convergió en $max_iter iteraciones")
        push!(resultado, "x = [" * join(round.(x, digits=6), ", ") * "]")
        push!(resultado, "f(x) = " * string(round(fx, digits=8)))
        return resultado

    elseif TipoOutput == 2
        # Descenso de gradiente con momentum
        A = Float64.(Matriz)
        if isnothing(Vector)
            return "Error: Vector (b) es requerido"
        end
        b = Float64.(vec(Vector))
        lr = Float64(Parametro)
        beta = 0.9  # momentum coefficient
        n = size(A, 1)
        x = zeros(n)
        v = zeros(n)
        max_iter = Int(MaxIter)

        resultado = ["Iter\tf(x)\t||grad||"]
        for iter in 1:max_iter
            grad = A * x - b
            fx = 0.5 * dot(x, A * x) - dot(b, x)
            gnorm = norm(grad)
            if iter <= 20 || iter % 100 == 0
                push!(resultado, string(iter, "\t", round(fx, digits=6), "\t", round(gnorm, digits=8)))
            end
            if gnorm < 1e-8
                push!(resultado, "Convergió en $iter iteraciones")
                push!(resultado, "x* = [" * join(round.(x, digits=6), ", ") * "]")
                push!(resultado, "f(x*) = " * string(round(fx, digits=8)))
                return resultado
            end
            v = beta * v + lr * grad
            x = x - v
        end
        fx = 0.5 * dot(x, A * x) - dot(b, x)
        push!(resultado, "No convergió en $max_iter iteraciones")
        push!(resultado, "x = [" * join(round.(x, digits=6), ", ") * "]")
        return resultado

    elseif TipoOutput == 3
        # Método de Newton para min f(x) = 0.5 * x'Ax - b'x
        A = Float64.(Matriz)
        if isnothing(Vector)
            return "Error: Vector (b) es requerido"
        end
        b = Float64.(vec(Vector))
        n = size(A, 1)
        x = zeros(n)

        # Para cuadrática, Newton converge en 1 paso: x* = A⁻¹b
        grad = A * x - b
        # Hessiana = A
        dx = A \ grad
        x = x - dx
        fx = 0.5 * dot(x, A * x) - dot(b, x)

        resultado = [
            "=== MÉTODO DE NEWTON ===",
            "Convergió en 1 iteración (función cuadrática)",
            "x* = [" * join(round.(x, digits=8), ", ") * "]",
            "f(x*) = " * string(round(fx, digits=8)),
            "||grad|| = " * string(round(norm(A * x - b), digits=12))
        ]
        return resultado

    elseif TipoOutput == 4
        # Búsqueda de Sección Áurea (1D)
        # Matriz = [a, b] (intervalo), Vector = [f(a), f(b)] (evaluaciones)
        M = Float64.(vec(Matriz))
        if length(M) < 2
            return "Error: Matriz debe contener [a, b] (intervalo de búsqueda)"
        end
        a, b_val = M[1], M[2]
        tol = Float64(Parametro) > 0 ? Float64(Parametro) : 1e-6
        max_iter = Int(MaxIter)
        phi = (sqrt(5.0) - 1.0) / 2.0

        resultado = ["Iter\ta\tb\tAncho"]
        for iter in 1:max_iter
            if abs(b_val - a) < tol
                mid = (a + b_val) / 2.0
                push!(resultado, "Convergió en $iter iteraciones")
                push!(resultado, "Mínimo en x* ≈ " * string(round(mid, digits=10)))
                return resultado
            end
            x1 = b_val - phi * (b_val - a)
            x2 = a + phi * (b_val - a)
            # Evaluar f(x) = x² como demo (parábola)
            f1 = x1^2
            f2 = x2^2
            if iter <= 30
                push!(resultado, string(iter, "\t", round(a, digits=6), "\t", round(b_val, digits=6), "\t", round(b_val - a, digits=8)))
            end
            if f1 < f2
                b_val = x2
            else
                a = x1
            end
        end
        push!(resultado, "No convergió en $max_iter iteraciones")
        return resultado

    elseif TipoOutput == 5
        # Simplex para Programación Lineal
        # min c'x sujeto a Ax <= b, x >= 0
        # Matriz = [A | b] (restricciones), Vector = c (costos)
        A_full = Float64.(Matriz)
        if isnothing(Vector)
            return "Error: Vector (costos c) es requerido"
        end
        c = Float64.(vec(Vector))

        m, n_plus_1 = size(A_full)
        n = n_plus_1 - 1
        A_ineq = A_full[:, 1:n]
        b_rhs = A_full[:, end]

        # Verificar factibilidad básica
        if any(b_rhs .< 0)
            return "Error: Todos los valores del lado derecho (b) deben ser >= 0"
        end

        # Tabla simplex: [A | I | b] con fila objetivo
        tableau = zeros(m + 1, n + m + 1)
        tableau[1:m, 1:n] = A_ineq
        tableau[1:m, n+1:n+m] = I(m)
        tableau[1:m, end] = b_rhs
        tableau[end, 1:n] = -c  # fila objetivo (negada para maximización del dual)

        basis = collect(n+1:n+m)
        max_iter = Int(MaxIter)

        for iter in 1:max_iter
            # Encontrar columna pivote (más negativa en fila objetivo)
            obj_row = tableau[end, 1:end-1]
            pivot_col = argmin(obj_row)
            if obj_row[pivot_col] >= -1e-10
                # Óptimo encontrado
                x_opt = zeros(n)
                for i in 1:m
                    if basis[i] <= n
                        x_opt[basis[i]] = tableau[i, end]
                    end
                end
                z_opt = dot(c, x_opt)
                resultado = vcat(
                    ["=== SOLUCIÓN SIMPLEX ==="],
                    ["Estado: ÓPTIMO"],
                    ["z* = " * string(round(z_opt, digits=6))],
                    [string("x", i, " = ", round(x_opt[i], digits=6)) for i in 1:n]
                )
                return resultado
            end

            # Encontrar fila pivote (regla de razón mínima)
            ratios = fill(Inf, m)
            for i in 1:m
                if tableau[i, pivot_col] > 1e-10
                    ratios[i] = tableau[i, end] / tableau[i, pivot_col]
                end
            end
            pivot_row = argmin(ratios)
            if ratios[pivot_row] == Inf
                return ["Problema no acotado"]
            end

            # Pivotear
            pivot_val = tableau[pivot_row, pivot_col]
            tableau[pivot_row, :] ./= pivot_val
            for i in 1:m+1
                if i != pivot_row
                    tableau[i, :] -= tableau[i, pivot_col] * tableau[pivot_row, :]
                end
            end
            basis[pivot_row] = pivot_col
        end
        return ["No convergió en $max_iter iteraciones"]

    elseif TipoOutput == 6
        # Mínimos cuadrados no-negativos (NNLS)
        # min ||Ax - b||² sujeto a x >= 0
        A = Float64.(Matriz)
        if isnothing(Vector)
            return "Error: Vector (b) es requerido"
        end
        b = Float64.(vec(Vector))
        n = size(A, 2)
        x = zeros(n)
        max_iter = Int(MaxIter)

        # Algoritmo de proyección de gradiente
        lr = Float64(Parametro) > 0 ? Float64(Parametro) : 0.001
        for iter in 1:max_iter
            grad = A' * (A * x - b)
            x_new = max.(0.0, x - lr * grad)
            if norm(x_new - x) < 1e-10
                x = x_new
                break
            end
            x = x_new
        end

        residual = norm(A * x - b)
        resultado = vcat(
            ["=== MÍNIMOS CUADRADOS NO-NEGATIVOS ==="],
            ["||Ax - b|| = " * string(round(residual, digits=6))],
            [string("x", i, " = ", round(x[i], digits=6)) for i in 1:n]
        )
        return resultado

    elseif TipoOutput == 7
        # Programación Cuadrática simple
        # min 0.5 x'Qx + c'x sujeto a x >= 0
        Q = Float64.(Matriz)
        if isnothing(Vector)
            return "Error: Vector (c) es requerido"
        end
        c = Float64.(vec(Vector))
        n = size(Q, 1)
        x = zeros(n)
        lr = Float64(Parametro) > 0 ? Float64(Parametro) : 0.01
        max_iter = Int(MaxIter)

        for iter in 1:max_iter
            grad = Q * x + c
            x_new = max.(0.0, x - lr * grad)
            if norm(x_new - x) < 1e-10
                x = x_new
                break
            end
            x = x_new
        end

        fx = 0.5 * dot(x, Q * x) + dot(c, x)
        resultado = vcat(
            ["=== PROGRAMACIÓN CUADRÁTICA ==="],
            ["f(x*) = " * string(round(fx, digits=6))],
            [string("x", i, " = ", round(x[i], digits=6)) for i in 1:n]
        )
        return resultado

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# FIN DE J4XCL-OP-Optimizacion.jl                      +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
