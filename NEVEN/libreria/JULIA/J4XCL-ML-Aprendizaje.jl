#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# J4XCL - APRENDIZAJE AUTOMÁTICO Y CIENCIA DE DATOS    +
# Clasificación, regresión, clustering, estadística    +
# Paquetes: stdlib (Statistics, Random)                +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

using Statistics
using Random

# =====================================================
# PROCEDIMIENTOS DISPONIBLES
# =====================================================

const PROC_CLASIFICACION = [
    "[01] K-Nearest Neighbors (KNN) — Clasificación",
    "[02] KNN — Predicción fuera de muestra",
    "[03] Regresión Lineal (mínimos cuadrados)",
    "[04] Predicción Regresión Lineal",
    "[05] Coeficientes y R²",
    "[06] Residuos del modelo",
    "[07] Matriz de Confusión",
    "[08] Métricas de Clasificación (Accuracy, Precision, Recall)"
]

const PROC_CLUSTERING = [
    "[01] K-Medias (Lloyd)",
    "[02] Centros de los Clusters",
    "[03] Asignación de Clusters",
    "[04] Variabilidad Intra-Cluster (WCSS)",
    "[05] Método del Codo (Elbow)",
    "[06] Estadísticas Descriptivas por Cluster"
]

const PROC_ESTADISTICA = [
    "[01] Estadística Descriptiva Completa",
    "[02] Matriz de Correlación",
    "[03] Covarianza",
    "[04] Test t de Student (dos muestras)",
    "[05] Normalización Min-Max",
    "[06] Estandarización Z-Score",
    "[07] Percentiles",
    "[08] Detección de Outliers (IQR)"
]

# =====================================================
# CLASIFICACIÓN Y REGRESIÓN
# =====================================================

"""
Clasificación y regresión: KNN, regresión lineal, métricas.
TipoOutput=0: lista procedimientos, 1:KNN, 2:KNN predict, 3:RegLineal,
4:Predicción, 5:Coefs+R², 6:Residuos, 7:Confusión, 8:Métricas
"""
function JML_Clasificacion(SetDatosX, SetDatosY=nothing, K=3, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_CLASIFICACION
    end

    X = Float64.(SetDatosX)
    if !isnothing(SetDatosY)
        Y = vec(SetDatosY)
    end

    if TipoOutput == 1
        # KNN Clasificación — entrenamiento + clasificación in-sample
        if isnothing(SetDatosY)
            return "Error: SetDatosY (etiquetas) es requerido"
        end
        k = Int(K)
        n = size(X, 1)
        predicciones = similar(Y)

        for i in 1:n
            distancias = [sqrt(sum((X[i,:] .- X[j,:]).^2)) for j in 1:n if j != i]
            indices = sortperm(distancias)[1:min(k, length(distancias))]
            # Ajustar índices (saltamos i)
            adj_indices = Int[]
            count = 0
            for j in 1:n
                if j != i
                    count += 1
                    if count in indices
                        push!(adj_indices, j)
                    end
                end
            end
            # Voto mayoritario
            votos = Y[adj_indices]
            predicciones[i] = _modo(votos)
        end

        accuracy = sum(predicciones .== Y) / n
        resultado = vcat(
            ["=== KNN Clasificación (K=$k) ==="],
            ["Accuracy in-sample: " * string(round(accuracy * 100, digits=2)) * "%"],
            ["Obs\tReal\tPredicho"],
            [string(i, "\t", Y[i], "\t", predicciones[i]) for i in 1:min(n, 50)]
        )
        return resultado

    elseif TipoOutput == 2
        # KNN Predicción fuera de muestra
        # X = datos de entrenamiento, Y = etiquetas, K = k
        # SetDatosX debe tener los datos nuevos como últimas filas
        return "Use JML_Clasificacion con datos de entrenamiento. Predicción OOS requiere datos separados."

    elseif TipoOutput == 3
        # Regresión Lineal por mínimos cuadrados: Y = Xβ + ε
        if isnothing(SetDatosY)
            return "Error: SetDatosY es requerido"
        end
        y = Float64.(vec(Y))
        n = size(X, 1)
        # Agregar columna de unos (intercepto)
        X_aug = hcat(ones(n), X)
        # β = (X'X)⁻¹X'y
        beta = X_aug \ y
        y_hat = X_aug * beta
        residuos = y .- y_hat
        ss_res = sum(residuos.^2)
        ss_tot = sum((y .- mean(y)).^2)
        r2 = 1.0 - ss_res / ss_tot

        resultado = vcat(
            ["=== REGRESIÓN LINEAL ==="],
            ["R² = " * string(round(r2, digits=6))],
            ["R² ajustado = " * string(round(1.0 - (1.0 - r2) * (n - 1) / (n - size(X_aug, 2)), digits=6))],
            ["Error estándar = " * string(round(sqrt(ss_res / (n - size(X_aug, 2))), digits=6))],
            [""],
            ["Coeficiente\tValor"],
            ["Intercepto\t" * string(round(beta[1], digits=6))],
            [string("β", i, "\t", round(beta[i+1], digits=6)) for i in 1:length(beta)-1]
        )
        return resultado

    elseif TipoOutput == 4
        # Predicción con regresión lineal
        if isnothing(SetDatosY)
            return "Error: SetDatosY es requerido para estimar coeficientes"
        end
        y = Float64.(vec(Y))
        n = size(X, 1)
        X_aug = hcat(ones(n), X)
        beta = X_aug \ y
        y_hat = X_aug * beta
        return y_hat

    elseif TipoOutput == 5
        # Coeficientes y R²
        if isnothing(SetDatosY)
            return "Error: SetDatosY es requerido"
        end
        y = Float64.(vec(Y))
        n = size(X, 1)
        X_aug = hcat(ones(n), X)
        beta = X_aug \ y
        y_hat = X_aug * beta
        ss_res = sum((y .- y_hat).^2)
        ss_tot = sum((y .- mean(y)).^2)
        r2 = 1.0 - ss_res / ss_tot
        return vcat([r2], beta)

    elseif TipoOutput == 6
        # Residuos
        if isnothing(SetDatosY)
            return "Error: SetDatosY es requerido"
        end
        y = Float64.(vec(Y))
        n = size(X, 1)
        X_aug = hcat(ones(n), X)
        beta = X_aug \ y
        return y .- X_aug * beta

    elseif TipoOutput == 7
        # Matriz de confusión
        if isnothing(SetDatosY)
            return "Error: SetDatosY es requerido (formato: [real, predicho])"
        end
        real = Y
        # Usar K como columna de predicciones si es vector
        if isa(K, AbstractArray)
            pred = vec(K)
        else
            return "Error: Pase las predicciones en el parámetro K"
        end
        clases = sort(unique(vcat(real, pred)))
        nc = length(clases)
        cm = zeros(Int, nc, nc)
        for i in 1:length(real)
            ri = findfirst(==(real[i]), clases)
            pi = findfirst(==(pred[i]), clases)
            if !isnothing(ri) && !isnothing(pi)
                cm[ri, pi] += 1
            end
        end
        resultado = vcat(
            ["=== MATRIZ DE CONFUSIÓN ==="],
            ["Real\\Pred\t" * join(string.(clases), "\t")],
            [string(clases[i], "\t", join(cm[i,:], "\t")) for i in 1:nc]
        )
        return resultado

    elseif TipoOutput == 8
        # Métricas de clasificación
        if isnothing(SetDatosY)
            return "Error: SetDatosY es requerido"
        end
        real = Y
        if isa(K, AbstractArray)
            pred = vec(K)
        else
            return "Error: Pase las predicciones en el parámetro K"
        end
        n = length(real)
        accuracy = sum(real .== pred) / n
        resultado = [
            "Accuracy = " * string(round(accuracy * 100, digits=2)) * "%",
            "N = " * string(n),
            "Correctos = " * string(sum(real .== pred)),
            "Incorrectos = " * string(sum(real .!= pred))
        ]
        return resultado

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

# Helper: moda de un vector
function _modo(v)
    counts = Dict{eltype(v), Int}()
    for x in v
        counts[x] = get(counts, x, 0) + 1
    end
    return sort(collect(counts), by=x->x[2], rev=true)[1][1]
end

# =====================================================
# CLUSTERING
# =====================================================

"""
Análisis de Clustering: K-Medias.
TipoOutput=0: lista procedimientos, 1:KMedias, 2:Centros, 3:Asignación,
4:WCSS, 5:Codo, 6:Descriptivas por cluster
"""
function JML_Clustering(SetDatosX, K=3, Semilla=12345, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_CLUSTERING
    end

    X = Float64.(SetDatosX)
    k = Int(K)
    rng = MersenneTwister(Int(Semilla))

    if TipoOutput in [1, 2, 3, 4, 6]
        # Ejecutar K-Medias
        centros, asignacion, wcss = _kmeans(X, k, rng)

        if TipoOutput == 1
            # Resultado completo
            n = size(X, 1)
            resultado = vcat(
                ["=== K-MEDIAS (K=$k) ==="],
                ["WCSS Total = " * string(round(wcss, digits=4))],
                [""],
                ["Obs\tCluster"],
                [string(i, "\t", asignacion[i]) for i in 1:min(n, 100)]
            )
            return resultado

        elseif TipoOutput == 2
            # Centros
            resultado = vcat(
                ["=== CENTROS DE CLUSTERS ==="],
                ["Cluster\t" * join(["Var$j" for j in 1:size(centros,2)], "\t")],
                [string(i, "\t", join(round.(centros[i,:], digits=4), "\t")) for i in 1:k]
            )
            return resultado

        elseif TipoOutput == 3
            return asignacion

        elseif TipoOutput == 4
            return wcss

        elseif TipoOutput == 6
            # Estadísticas por cluster
            resultado = ["=== ESTADÍSTICAS POR CLUSTER ==="]
            for c in 1:k
                mask = asignacion .== c
                nc = sum(mask)
                if nc > 0
                    Xc = X[mask, :]
                    push!(resultado, "--- Cluster $c (n=$nc) ---")
                    for j in 1:size(Xc, 2)
                        col = Xc[:, j]
                        push!(resultado, string("  Var$j: media=", round(mean(col), digits=4),
                              " std=", round(std(col), digits=4),
                              " min=", round(minimum(col), digits=4),
                              " max=", round(maximum(col), digits=4)))
                    end
                end
            end
            return resultado
        end

    elseif TipoOutput == 5
        # Método del Codo
        max_k = min(k, size(X, 1) - 1)
        resultado = ["K\tWCSS"]
        for ki in 1:max_k
            _, _, wcss_i = _kmeans(X, ki, MersenneTwister(Int(Semilla)))
            push!(resultado, string(ki, "\t", round(wcss_i, digits=4)))
        end
        return resultado

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

# K-Medias implementación interna
function _kmeans(X, k, rng; max_iter=100)
    n, p = size(X)
    # Inicialización aleatoria
    idx = randperm(rng, n)[1:k]
    centros = X[idx, :]
    asignacion = zeros(Int, n)

    for iter in 1:max_iter
        # Asignar
        nueva_asig = zeros(Int, n)
        for i in 1:n
            dists = [sum((X[i,:] .- centros[j,:]).^2) for j in 1:k]
            nueva_asig[i] = argmin(dists)
        end

        # Actualizar centros
        nuevos_centros = zeros(k, p)
        for j in 1:k
            mask = nueva_asig .== j
            if sum(mask) > 0
                nuevos_centros[j, :] = mean(X[mask, :], dims=1)
            else
                nuevos_centros[j, :] = centros[j, :]
            end
        end

        if nueva_asig == asignacion
            asignacion = nueva_asig
            centros = nuevos_centros
            break
        end
        asignacion = nueva_asig
        centros = nuevos_centros
    end

    # WCSS
    wcss = 0.0
    for i in 1:n
        wcss += sum((X[i,:] .- centros[asignacion[i],:]).^2)
    end

    return centros, asignacion, wcss
end

# =====================================================
# ESTADÍSTICA DESCRIPTIVA Y TESTS
# =====================================================

"""
Estadística descriptiva y tests.
TipoOutput=0: lista procedimientos, 1:Descriptiva, 2:Correlación, 3:Covarianza,
4:Test t, 5:MinMax, 6:ZScore, 7:Percentiles, 8:Outliers
"""
function JML_Estadistica(SetDatosX, SetDatosY=nothing, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_ESTADISTICA
    end

    X = Float64.(SetDatosX)

    if TipoOutput == 1
        # Estadística descriptiva completa
        if ndims(X) == 1
            X = reshape(X, :, 1)
        end
        p = size(X, 2)
        resultado = vcat(
            ["=== ESTADÍSTICA DESCRIPTIVA ==="],
            ["Variable\tN\tMedia\tStd\tMin\tQ1\tMediana\tQ3\tMax\tSkew\tKurt"]
        )
        for j in 1:p
            col = X[:, j]
            n = length(col)
            sorted = sort(col)
            q1 = sorted[max(1, Int(ceil(n * 0.25)))]
            q3 = sorted[max(1, Int(ceil(n * 0.75)))]
            med = sorted[max(1, Int(ceil(n * 0.5)))]
            m = mean(col)
            s = std(col)
            skew = n > 2 ? sum(((col .- m) ./ s).^3) * n / ((n-1)*(n-2)) : 0.0
            kurt = n > 3 ? sum(((col .- m) ./ s).^4) * n * (n+1) / ((n-1)*(n-2)*(n-3)) - 3*(n-1)^2/((n-2)*(n-3)) : 0.0
            push!(resultado, string("Var$j\t", n, "\t",
                round(m, digits=4), "\t", round(s, digits=4), "\t",
                round(minimum(col), digits=4), "\t", round(q1, digits=4), "\t",
                round(med, digits=4), "\t", round(q3, digits=4), "\t",
                round(maximum(col), digits=4), "\t",
                round(skew, digits=4), "\t", round(kurt, digits=4)))
        end
        return resultado

    elseif TipoOutput == 2
        # Matriz de correlación
        if ndims(X) == 1
            return "Error: Se requiere una matriz con al menos 2 columnas"
        end
        C = cor(X)
        p = size(C, 1)
        resultado = vcat(
            ["=== MATRIZ DE CORRELACIÓN ==="],
            ["\t" * join(["Var$j" for j in 1:p], "\t")],
            [string("Var$i\t", join(round.(C[i,:], digits=4), "\t")) for i in 1:p]
        )
        return resultado

    elseif TipoOutput == 3
        # Covarianza
        if ndims(X) == 1
            return var(X)
        end
        C = cov(X)
        p = size(C, 1)
        resultado = vcat(
            ["=== MATRIZ DE COVARIANZA ==="],
            ["\t" * join(["Var$j" for j in 1:p], "\t")],
            [string("Var$i\t", join(round.(C[i,:], digits=4), "\t")) for i in 1:p]
        )
        return resultado

    elseif TipoOutput == 4
        # Test t de Student (dos muestras independientes)
        if isnothing(SetDatosY)
            return "Error: SetDatosY (segunda muestra) es requerido"
        end
        x = vec(X)
        y = Float64.(vec(SetDatosY))
        nx, ny = length(x), length(y)
        mx, my = mean(x), mean(y)
        sx, sy = var(x), var(y)
        se = sqrt(sx/nx + sy/ny)
        t_stat = (mx - my) / se
        # Grados de libertad (Welch)
        df = (sx/nx + sy/ny)^2 / ((sx/nx)^2/(nx-1) + (sy/ny)^2/(ny-1))
        resultado = [
            "=== TEST t DE STUDENT (dos muestras) ===",
            "Media X = " * string(round(mx, digits=6)),
            "Media Y = " * string(round(my, digits=6)),
            "Diferencia = " * string(round(mx - my, digits=6)),
            "t-estadístico = " * string(round(t_stat, digits=6)),
            "Grados de libertad (Welch) = " * string(round(df, digits=2)),
            "Error estándar = " * string(round(se, digits=6)),
            "N_x = $nx, N_y = $ny"
        ]
        return resultado

    elseif TipoOutput == 5
        # Normalización Min-Max [0,1]
        if ndims(X) == 1
            mn, mx = minimum(X), maximum(X)
            return mx > mn ? (X .- mn) ./ (mx - mn) : zeros(length(X))
        end
        result = similar(X)
        for j in 1:size(X, 2)
            mn, mx = minimum(X[:,j]), maximum(X[:,j])
            result[:,j] = mx > mn ? (X[:,j] .- mn) ./ (mx - mn) : zeros(size(X,1))
        end
        return result

    elseif TipoOutput == 6
        # Estandarización Z-Score
        if ndims(X) == 1
            m, s = mean(X), std(X)
            return s > 0 ? (X .- m) ./ s : zeros(length(X))
        end
        result = similar(X)
        for j in 1:size(X, 2)
            m, s = mean(X[:,j]), std(X[:,j])
            result[:,j] = s > 0 ? (X[:,j] .- m) ./ s : zeros(size(X,1))
        end
        return result

    elseif TipoOutput == 7
        # Percentiles
        x = vec(X)
        sorted = sort(x)
        n = length(sorted)
        percs = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        resultado = ["Percentil\tValor"]
        for p in percs
            idx = max(1, Int(ceil(n * p / 100)))
            push!(resultado, string("P$p\t", round(sorted[idx], digits=4)))
        end
        return resultado

    elseif TipoOutput == 8
        # Detección de outliers por IQR
        if ndims(X) == 1
            X = reshape(X, :, 1)
        end
        resultado = ["=== DETECCIÓN DE OUTLIERS (IQR) ==="]
        for j in 1:size(X, 2)
            col = sort(X[:, j])
            n = length(col)
            q1 = col[max(1, Int(ceil(n * 0.25)))]
            q3 = col[max(1, Int(ceil(n * 0.75)))]
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = findall(x -> x < lower || x > upper, X[:, j])
            push!(resultado, "Var$j: Q1=$q1, Q3=$q3, IQR=$iqr, Límites=[$lower, $upper], Outliers=$(length(outliers))")
            if length(outliers) > 0
                push!(resultado, "  Índices: " * join(string.(outliers[1:min(20, length(outliers))]), ", "))
            end
        end
        return resultado

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# FIN DE J4XCL-ML-Aprendizaje.jl                       +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
