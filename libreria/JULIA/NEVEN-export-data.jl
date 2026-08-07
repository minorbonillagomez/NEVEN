"""
    NEVEN.export_data — Exportar datos desde Pluto/Julia de vuelta a Excel

Carga este archivo desde un notebook Pluto:
    include(joinpath(ENV["NEVEN_HOME"], "startup", "NEVEN-export-data.jl"))

O agrégalo a tu notebook:
    using NEVEN  # si ya está cargado con la sysimage
    NEVEN.export_data("resultados", mi_dataframe)
"""

# Solo definir si el módulo NEVEN ya está cargado en el entorno
if isdefined(Main, :NEVEN) && isa(Main.NEVEN, Module)
    @eval Main.NEVEN begin

        export export_data

        """
            export_data(name, data; headers=nothing)

        Exporta datos desde Pluto de vuelta a Excel via TSV.
        Excel los lee con: =NEVEN.r("NEVEN.pluto_read(\\"nombre\\")")

        # Argumentos
        - `name`:    Nombre del dataset (letras, números, guiones)
        - `data`:    Matrix, DataFrame, Vector o cualquier iterable
        - `headers`: Vector de strings con nombres de columna (opcional)
        """
        function export_data(name::String, data; headers=nothing)
            using Statistics  # por si acaso

            safe_name = replace(name, r"[^A-Za-z0-9_\-]" => "_")
            isempty(safe_name) && return "Error: nombre inválido"

            dir = get(ENV, "NEVEN_HOME", "C:\\NEVEN")
            mkpath(joinpath(dir, "data"))
            filepath = joinpath(dir, "data", "$(safe_name).tsv")

            try
                # DataFrame-like (tiene propertynames y Matrix())
                local mat, col_headers
                if hasproperty(data, :columns) ||
                   (isdefined(Main, :DataFrames) && data isa Main.DataFrames.DataFrame)
                    col_headers = isnothing(headers) ? string.(propertynames(data)) : headers
                    mat = Matrix(data)
                elseif data isa AbstractMatrix
                    mat = data
                    col_headers = headers
                elseif data isa AbstractVector
                    mat = reshape(data, length(data), 1)
                    col_headers = headers
                else
                    mat = hcat(data)
                    col_headers = headers
                end

                open(filepath, "w") do io
                    if !isnothing(col_headers) && !isempty(col_headers)
                        println(io, join(string.(col_headers), "\t"))
                    end
                    for i in 1:size(mat, 1)
                        for j in 1:size(mat, 2)
                            j > 1 && print(io, "\t")
                            v = mat[i, j]
                            if v isa AbstractFloat && isfinite(v)
                                print(io, round(v, digits=10))
                            elseif v === missing || v === nothing
                                print(io, "")
                            else
                                print(io, v)
                            end
                        end
                        println(io)
                    end
                end

                nr = size(mat, 1); nc = size(mat, 2)
                return "OK: $(safe_name) exportado ($(nr)×$(nc)) → $(filepath)"
            catch e
                return "Error: $(sprint(showerror, e))"
            end
        end

    end  # @eval Main.NEVEN
else
    @warn "NEVEN-export-data.jl: módulo NEVEN no encontrado — carga startup.jl primero"
end
