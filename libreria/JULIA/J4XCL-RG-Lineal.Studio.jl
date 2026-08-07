# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio Julia: Regresión Lineal (MCO)
# Función: RG_Lineal_Studio
# Implementación: MCO via álgebra lineal (sin paquetes externos)
# ═══════════════════════════════════════════════════════════════════════════════

using Statistics, LinearAlgebra

"""
    RG_Lineal_Studio(data::Dict; Constante=true, Decimales=4, kwargs...) -> Vector{Dict}

Regresión Lineal MCO implementada con álgebra lineal.
Sin dependencia de paquetes R/Python.

data["Y"] = columna dependiente
data["X"] = columna(s) independientes
"""
function RG_Lineal_Studio(data::Dict;
                           Constante::Bool=true,
                           Decimales::Int=4,
                           kwargs...)

    r(x) = round(x, digits=Decimales)

    # ── Extraer Y ─────────────────────────────────────────────────────────────
    y_rows = get(data, "Y", nothing)
    if isnothing(y_rows) || isempty(y_rows)
        return [_error_slot("Asigne al menos una columna al rol Y")]
    end
    # Primera columna numérica de Y
    y_col = first(keys(first(y_rows)))
    y = Float64[]
    for row in y_rows
        v = get(row, y_col, nothing)
        if !isnothing(v) && isa(v, Number)
            push!(y, Float64(v))
        end
    end
    isempty(y) && return [_error_slot("La columna Y no tiene valores numéricos")]

    # ── Extraer X ─────────────────────────────────────────────────────────────
    x_rows = get(data, "X", nothing)
    x_cols = String[]
    X_mat  = Matrix{Float64}(undef, length(y), 0)

    if !isnothing(x_rows) && !isempty(x_rows)
        first_x = first(x_rows)
        x_cols = [k for (k, v) in first_x if isa(v, Number)]
        if !isempty(x_cols)
            X_mat = zeros(Float64, length(y), length(x_cols))
            for (j, col) in enumerate(x_cols)
                for (i, row) in enumerate(x_rows)
                    v = get(row, col, 0.0)
                    X_mat[i, j] = isa(v, Number) ? Float64(v) : 0.0
                end
            end
        end
    end

    if isempty(x_cols)
        return [_error_slot("Asigne al menos una columna al rol X")]
    end

    n = length(y)
    n < length(x_cols) + 2 && return [_error_slot("Observaciones insuficientes para el modelo")]

    # ── Construir matriz de diseño ────────────────────────────────────────────
    X = Constante ? hcat(ones(Float64, n), X_mat) : X_mat
    k = size(X, 2)

    # ── MCO: β = (X'X)⁻¹ X'y ─────────────────────────────────────────────────
    XtX = X' * X
    Xty = X' * y

    β = try
        XtX \ Xty
    catch
        return [_error_slot("La matriz X'X es singular. Verifique colinealidad.")]
    end

    # ── Diagnósticos ──────────────────────────────────────────────────────────
    ŷ     = X * β
    resid = y - ŷ
    sse   = sum(resid.^2)
    sst   = sum((y .- Statistics.mean(y)).^2)
    r2    = sst > 0 ? 1.0 - sse/sst : 0.0
    r2adj = 1.0 - (1.0 - r2) * (n - 1) / (n - k)
    s2    = sse / (n - k)                       # varianza del error
    se_β  = sqrt.(max.(s2 * diag(inv(XtX)), 0)) # errores estándar

    # Estadístico t y p-valores (distribución t con n-k g.l.)
    t_vals = β ./ se_β
    p_vals = [2.0 * _t_cdf_upper(abs(tv), n - k) for tv in t_vals]

    # F global
    ms_reg = (sst - sse) / (k - (Constante ? 1 : 0))
    ms_res = sse / (n - k)
    f_stat = ms_res > 0 ? ms_reg / ms_res : 0.0
    p_f    = _f_cdf_upper(f_stat, k - (Constante ? 1 : 0), n - k)

    # AIC, BIC
    log_lik = -0.5 * n * (log(2π * s2) + 1.0)
    aic = -2 * log_lik + 2k
    bic = -2 * log_lik + k * log(n)

    # ── Tabla de coeficientes ─────────────────────────────────────────────────
    var_names = Constante ? vcat(["(Constante)"], x_cols) : x_cols
    coef_rows = Vector{Dict{String,Any}}()
    for i in eachindex(β)
        push!(coef_rows, Dict{String,Any}(
            "Variable"  => var_names[i],
            "Estimado"  => r(β[i]),
            "Error_Std" => r(se_β[i]),
            "t_value"   => r(t_vals[i]),
            "p_value"   => r(p_vals[i]),
            "Signif"    => _signif_stars(p_vals[i])
        ))
    end

    # ── Tabla de métricas ─────────────────────────────────────────────────────
    metricas = [
        Dict("Métrica" => "R²",          "Valor" => r(r2)),
        Dict("Métrica" => "R² ajustado", "Valor" => r(r2adj)),
        Dict("Métrica" => "F estadístico","Valor" => r(f_stat)),
        Dict("Métrica" => "p-valor F",   "Valor" => r(p_f)),
        Dict("Métrica" => "RSE",         "Valor" => r(sqrt(s2))),
        Dict("Métrica" => "AIC",         "Valor" => r(aic)),
        Dict("Métrica" => "BIC",         "Valor" => r(bic)),
        Dict("Métrica" => "N",           "Valor" => n),
        Dict("Métrica" => "K (vars)",    "Valor" => length(x_cols)),
    ]

    # ── Tabla residuos vs ajustados (primeras 50 obs) ─────────────────────────
    n_show = min(50, n)
    resid_rows = [Dict{String,Any}(
        "ID"       => i,
        "Observado"=> r(y[i]),
        "Ajustado" => r(ŷ[i]),
        "Residuo"  => r(resid[i])
    ) for i in 1:n_show]

    return [
        Dict("name" => "coeficientes", "label" => "Coeficientes MCO",
             "type" => "table", "value" => coef_rows, "tier" => 1),
        Dict("name" => "metricas",     "label" => "Métricas del Modelo",
             "type" => "table", "value" => metricas,  "tier" => 1),
        Dict("name" => "residuos",     "label" => "Ajustados vs Residuos (primeras 50 obs)",
             "type" => "table", "value" => resid_rows,"tier" => 2),
        Dict("name" => "resumen",      "label" => "Resumen",
             "type" => "scalar",
             "value" => "Y=$(y_col) ~ $(join(x_cols, " + ")) | R²=$(r(r2)) | n=$(n) | Julia $(VERSION)",
             "tier" => 1),
    ]
end

# ── Helpers estadísticos ──────────────────────────────────────────────────────

_error_slot(msg) = Dict("name" => "error", "label" => "Error",
                        "type" => "scalar", "value" => msg, "tier" => 1)

function _signif_stars(p)
    p < 0.001 ? "***" : p < 0.01 ? "**" : p < 0.05 ? "*" : p < 0.1 ? "." : ""
end

# Aproximación a la CDF superior de la distribución t (cola derecha)
# Usa la aproximación de Cornish-Fisher para grados de libertad grandes
function _t_cdf_upper(t::Float64, df::Int)
    df <= 0 && return 0.5
    # Aproximación normal para df grande
    df >= 100 && return _normal_cdf_upper(t)
    # Para df pequeños usamos la aproximación de Abramowitz & Stegun 26.7.8
    x = df / (df + t^2)
    # Incomplete beta approximation (simplified)
    p_beta = _ibeta_half(x, df/2.0, 0.5)
    return p_beta / 2.0
end

function _normal_cdf_upper(z::Float64)
    # Approximation (Horner's method, max error 7.5e-8)
    z < 0 && return 1.0 - _normal_cdf_upper(-z)
    t = 1.0 / (1.0 + 0.2316419 * z)
    poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 +
           t * (-1.821255978 + t * 1.330274429))))
    return poly * exp(-z^2 / 2.0) / sqrt(2π)
end

function _f_cdf_upper(f::Float64, df1::Int, df2::Int)
    f <= 0 && return 1.0
    # Approx via Beta distribution
    x = df2 / (df2 + df1 * f)
    return _ibeta_half(x, df2/2.0, df1/2.0)
end

function _ibeta_half(x::Float64, a::Float64, b::Float64)
    # Regularized incomplete beta via continued fraction (Lentz, simplified)
    (x <= 0 || x >= 1) && return x <= 0 ? 0.0 : 1.0
    lbeta_ab = lgamma(a) + lgamma(b) - lgamma(a + b)
    front    = exp(a * log(x) + b * log(1 - x) - lbeta_ab) / a
    # 20 iterations of Lentz CF
    d  = 1.0 - (a + b) * x / (a + 1)
    abs(d) < 1e-30 && (d = 1e-30)
    c  = 1.0; d = 1.0 / d; frac = d
    for m in 1:20
        for pm in (0, 1)
            m2 = 2 * m
            nm = pm == 0 ? -m * (b - m) * x / ((a + m2 - 1) * (a + m2)) :
                            m * (a + b + m - 1) * x / ((a + m2) * (a + m2 + 1))
            d = 1.0 + nm * d
            abs(d) < 1e-30 && (d = 1e-30)
            c = 1.0 + nm / c
            abs(c) < 1e-30 && (c = 1e-30)
            d = 1.0 / d
            frac *= c * d
        end
    end
    return min(1.0, front * frac)
end
