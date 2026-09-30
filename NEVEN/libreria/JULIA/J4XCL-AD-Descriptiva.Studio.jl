# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Data Lab — Wrapper Studio Julia: Estadísticas Descriptivas
# Función: AD_Descriptiva_Studio
# Requiere: JSON3 (incluido en la sysimage NEVEN)
# ═══════════════════════════════════════════════════════════════════════════════

using Statistics

"""
    AD_Descriptiva_Studio(data::Dict; kwargs...) -> Vector{Dict}

Calcula estadísticas descriptivas sobre las columnas numéricas del dataset.

Argumentos:
  data: Dict con clave "X" (columna(s) a analizar). Si "X" está vacío,
        analiza todas las columnas disponibles en el primer rol.
  Decimales: número de decimales en los resultados (default=4)

Retorna una lista de slots compatibles con el sistema NEVEN DataLab.
"""
function AD_Descriptiva_Studio(data::Dict; Decimales::Int=4, kwargs...)

    # ── Extraer columnas ─────────────────────────────────────────────────────
    # data es un Dict{String,Any} con claves = roleKeys (ej: "X", "Y")
    # Cada valor es un Array de Dict{String,Any} con los datos
    all_rows = Dict{String, Vector{Float64}}()

    for (role_key, rows) in data
        if !isa(rows, Vector) || isempty(rows)
            continue
        end
        # Cada row es un Dict{String,Any}
        first_row = rows[1]
        for (col_name, col_val) in first_row
            # Solo columnas numéricas
            if isa(col_val, Number)
                vals = Float64[]
                for row in rows
                    v = get(row, col_name, nothing)
                    if v !== nothing && isa(v, Number) && !isnan(Float64(v))
                        push!(vals, Float64(v))
                    end
                end
                if !isempty(vals)
                    all_rows[col_name] = vals
                end
            end
        end
    end

    if isempty(all_rows)
        return [Dict(
            "name"  => "error",
            "label" => "Sin datos numéricos",
            "type"  => "scalar",
            "value" => "No se encontraron columnas numéricas en el dataset.",
            "tier"  => 1
        )]
    end

    # ── Calcular estadísticas por columna ────────────────────────────────────
    r(x) = round(x, digits=Decimales)

    stats_rows = Vector{Dict{String,Any}}()
    for (col_name, vals) in sort(collect(all_rows))
        n    = length(vals)
        s    = sort(vals)
        q25  = s[max(1, round(Int, 0.25 * n))]
        q50  = Statistics.median(vals)
        q75  = s[min(n, round(Int, 0.75 * n))]
        iqr  = q75 - q25
        push!(stats_rows, Dict{String,Any}(
            "Columna"  => col_name,
            "N"        => n,
            "Media"    => r(Statistics.mean(vals)),
            "Mediana"  => r(q50),
            "DesvEst"  => r(Statistics.std(vals)),
            "Min"      => r(minimum(vals)),
            "Max"      => r(maximum(vals)),
            "Q25"      => r(q25),
            "Q75"      => r(q75),
            "IQR"      => r(iqr),
            "Asimetria"=> r(_skewness(vals)),
            "Curtosis" => r(_kurtosis(vals))
        ))
    end

    # ── Tabla de correlaciones (si hay ≥2 columnas) ──────────────────────────
    slots = Vector{Dict}()

    push!(slots, Dict(
        "name"  => "estadisticas",
        "label" => "Estadísticas Descriptivas",
        "type"  => "table",
        "value" => stats_rows,
        "tier"  => 1
    ))

    col_names = collect(keys(all_rows))
    if length(col_names) >= 2
        corr_rows = Vector{Dict{String,Any}}()
        sorted_cols = sort(col_names)
        for c1 in sorted_cols
            row_d = Dict{String,Any}("Variable" => c1)
            for c2 in sorted_cols
                v1 = all_rows[c1]; v2 = all_rows[c2]
                n_min = min(length(v1), length(v2))
                row_d[c2] = n_min >= 2 ? r(_correlation(v1[1:n_min], v2[1:n_min])) : 0.0
            end
            push!(corr_rows, row_d)
        end
        push!(slots, Dict(
            "name"  => "correlaciones",
            "label" => "Matriz de Correlaciones",
            "type"  => "table",
            "value" => corr_rows,
            "tier"  => 2
        ))
    end

    # ── Resumen general ───────────────────────────────────────────────────────
    n_rows = isempty(all_rows) ? 0 : length(first(values(all_rows)))
    push!(slots, Dict(
        "name"  => "resumen",
        "label" => "Resumen",
        "type"  => "scalar",
        "value" => "$(length(col_names)) columnas · $(n_rows) observaciones · Julia $(VERSION)",
        "tier"  => 1
    ))

    return slots
end

# ── Helpers estadísticos ──────────────────────────────────────────────────────

function _skewness(x::Vector{Float64})
    n  = length(x)
    n < 3 && return 0.0
    μ  = Statistics.mean(x)
    σ  = Statistics.std(x)
    σ == 0 && return 0.0
    sum((xi - μ)^3 for xi in x) / (n * σ^3)
end

function _kurtosis(x::Vector{Float64})
    n  = length(x)
    n < 4 && return 0.0
    μ  = Statistics.mean(x)
    σ  = Statistics.std(x)
    σ == 0 && return 0.0
    sum((xi - μ)^4 for xi in x) / (n * σ^4) - 3.0
end

function _correlation(x::Vector{Float64}, y::Vector{Float64})
    n = length(x)
    n < 2 && return 0.0
    μx = Statistics.mean(x); μy = Statistics.mean(y)
    num = sum((x[i] - μx) * (y[i] - μy) for i in 1:n)
    den = sqrt(sum((xi - μx)^2 for xi in x)) * sqrt(sum((yi - μy)^2 for yi in y))
    den == 0 ? 0.0 : num / den
end
