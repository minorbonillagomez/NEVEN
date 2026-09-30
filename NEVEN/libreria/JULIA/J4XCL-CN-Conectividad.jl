#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# J4XCL - CONECTIVIDAD Y MANEJO DE DATOS               +
# CSV, JSON, transformaciones, utilidades              +
# Paquetes: stdlib (DelimitedFiles, Dates)             +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

using DelimitedFiles
using Dates

# =====================================================
# PROCEDIMIENTOS DISPONIBLES
# =====================================================

const PROC_ARCHIVOS = [
    "[01] Leer archivo CSV",
    "[02] Escribir datos a CSV",
    "[03] Leer archivo de texto delimitado",
    "[04] Información del archivo",
    "[05] Listar archivos en directorio"
]

const PROC_TRANSFORMACION = [
    "[01] Transponer datos",
    "[02] Ordenar por columna",
    "[03] Filtrar filas por condición",
    "[04] Seleccionar columnas",
    "[05] Agregar columna calculada",
    "[06] Valores únicos de columna",
    "[07] Frecuencias (tabla de conteo)",
    "[08] Unir dos tablas (horizontal)",
    "[09] Pivotar datos (reshape)"
]

const PROC_UTILIDADES = [
    "[01] Fecha y hora actual",
    "[02] Generar secuencia numérica",
    "[03] Generar datos aleatorios (Normal)",
    "[04] Generar datos aleatorios (Uniforme)",
    "[05] Tabla de frecuencias cruzadas",
    "[06] Buscar y reemplazar en datos",
    "[07] Redondear datos",
    "[08] Convertir tipos de datos"
]

# =====================================================
# ARCHIVOS Y DATOS
# =====================================================

"""
Lectura y escritura de archivos CSV y texto.
TipoOutput=0: lista procedimientos, 1:LeerCSV, 2:EscribirCSV,
3:LeerDelimitado, 4:InfoArchivo, 5:ListarArchivos
"""
function JC_Archivos(Ruta="", Datos=nothing, Delimitador=",", TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_ARCHIVOS
    end

    ruta = string(Ruta)

    if TipoOutput == 1
        # Leer CSV
        if !isfile(ruta)
            return "Error: Archivo no encontrado: $ruta"
        end
        try
            data = readdlm(ruta, ',')
            return data
        catch e
            return "Error leyendo CSV: " * string(e)
        end

    elseif TipoOutput == 2
        # Escribir CSV
        if isnothing(Datos)
            return "Error: Datos es requerido para escribir"
        end
        try
            writedlm(ruta, Datos, ',')
            return "Archivo escrito: $ruta"
        catch e
            return "Error escribiendo CSV: " * string(e)
        end

    elseif TipoOutput == 3
        # Leer archivo delimitado
        if !isfile(ruta)
            return "Error: Archivo no encontrado: $ruta"
        end
        delim = length(string(Delimitador)) > 0 ? string(Delimitador)[1] : ','
        try
            data = readdlm(ruta, delim)
            return data
        catch e
            return "Error leyendo archivo: " * string(e)
        end

    elseif TipoOutput == 4
        # Información del archivo
        if !isfile(ruta)
            return "Error: Archivo no encontrado: $ruta"
        end
        info = stat(ruta)
        resultado = [
            "=== INFORMACIÓN DEL ARCHIVO ===",
            "Ruta: $ruta",
            "Tamaño: " * string(info.size) * " bytes",
            "Modificado: " * string(Dates.unix2datetime(info.mtime)),
            "Creado: " * string(Dates.unix2datetime(info.ctime))
        ]
        return resultado

    elseif TipoOutput == 5
        # Listar archivos en directorio
        if !isdir(ruta)
            return "Error: Directorio no encontrado: $ruta"
        end
        archivos = readdir(ruta)
        resultado = vcat(
            ["=== ARCHIVOS EN $ruta ==="],
            ["Total: $(length(archivos)) archivos"],
            archivos
        )
        return resultado

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

# =====================================================
# TRANSFORMACIÓN DE DATOS
# =====================================================

"""
Transformación y manipulación de datos tabulares.
TipoOutput=0: lista procedimientos, 1:Transponer, 2:Ordenar, 3:Filtrar,
4:Seleccionar, 5:Columna calculada, 6:Únicos, 7:Frecuencias, 8:Unir, 9:Pivotar
"""
function JC_Transformar(Datos, Columna=1, Valor=nothing, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_TRANSFORMACION
    end

    D = Datos

    if TipoOutput == 1
        # Transponer
        if isa(D, AbstractMatrix)
            return permutedims(D)
        elseif isa(D, AbstractVector)
            return reshape(D, 1, :)
        else
            return "Error: Datos debe ser una matriz o vector"
        end

    elseif TipoOutput == 2
        # Ordenar por columna
        if !isa(D, AbstractMatrix)
            return sort(vec(D))
        end
        col = Int(Columna)
        if col < 1 || col > size(D, 2)
            return "Error: Columna $col fuera de rango (1-$(size(D,2)))"
        end
        idx = sortperm(D[:, col])
        return D[idx, :]

    elseif TipoOutput == 3
        # Filtrar filas donde columna == valor
        if !isa(D, AbstractMatrix)
            return "Error: Datos debe ser una matriz"
        end
        col = Int(Columna)
        if isnothing(Valor)
            return "Error: Valor de filtro es requerido"
        end
        mask = D[:, col] .== Valor
        return D[mask, :]

    elseif TipoOutput == 4
        # Seleccionar columnas
        if !isa(D, AbstractMatrix)
            return D
        end
        if isa(Columna, AbstractArray)
            cols = Int.(vec(Columna))
        else
            cols = [Int(Columna)]
        end
        return D[:, cols]

    elseif TipoOutput == 5
        # Agregar columna calculada (suma de todas las columnas numéricas)
        if !isa(D, AbstractMatrix)
            return "Error: Datos debe ser una matriz"
        end
        D_float = try
            Float64.(D)
        catch
            return "Error: Los datos deben ser numéricos"
        end
        nueva_col = sum(D_float, dims=2)
        return hcat(D, nueva_col)

    elseif TipoOutput == 6
        # Valores únicos
        if isa(D, AbstractMatrix)
            col = Int(Columna)
            return unique(D[:, col])
        else
            return unique(vec(D))
        end

    elseif TipoOutput == 7
        # Tabla de frecuencias
        if isa(D, AbstractMatrix)
            col = Int(Columna)
            vals = D[:, col]
        else
            vals = vec(D)
        end
        unicos = unique(vals)
        resultado = vcat(
            ["Valor\tFrecuencia\t%"],
            [string(v, "\t", count(==(v), vals), "\t",
                round(count(==(v), vals) / length(vals) * 100, digits=1), "%")
             for v in sort(unicos)]
        )
        return resultado

    elseif TipoOutput == 8
        # Unir dos tablas horizontalmente
        if isnothing(Valor)
            return "Error: Pase la segunda tabla en el parámetro Valor"
        end
        D2 = Valor
        if size(D, 1) != size(D2, 1)
            return "Error: Las tablas deben tener el mismo número de filas"
        end
        return hcat(D, D2)

    elseif TipoOutput == 9
        # Pivotar (reshape): de largo a ancho
        if !isa(D, AbstractMatrix)
            return "Error: Datos debe ser una matriz"
        end
        n = size(D, 1)
        p = size(D, 2)
        new_cols = Int(Columna) > 0 ? Int(Columna) : p
        new_rows = Int(ceil(n * p / new_cols))
        flat = vec(permutedims(D))
        # Pad si es necesario
        while length(flat) < new_rows * new_cols
            push!(flat, 0)
        end
        return reshape(flat[1:new_rows*new_cols], new_rows, new_cols)

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

# =====================================================
# UTILIDADES
# =====================================================

"""
Utilidades generales: fechas, secuencias, aleatorios, búsqueda.
TipoOutput=0: lista procedimientos, 1:Fecha, 2:Secuencia, 3:Normal,
4:Uniforme, 5:Cruzada, 6:Reemplazar, 7:Redondear, 8:Convertir
"""
function JC_Utilidades(Parametro1=0, Parametro2=0, Parametro3=0, TipoOutput=0)

    TipoOutput = Int(TipoOutput)

    if TipoOutput == 0
        return PROC_UTILIDADES
    end

    if TipoOutput == 1
        # Fecha y hora actual
        ahora = now()
        resultado = [
            "Fecha: " * Dates.format(ahora, "yyyy-mm-dd"),
            "Hora: " * Dates.format(ahora, "HH:MM:SS"),
            "Día de semana: " * string(dayofweek(ahora)),
            "Día del año: " * string(dayofyear(ahora)),
            "Semana del año: " * string(week(ahora)),
            "Timestamp: " * string(datetime2unix(ahora))
        ]
        return resultado

    elseif TipoOutput == 2
        # Generar secuencia numérica
        inicio = Float64(Parametro1)
        fin_val = Float64(Parametro2)
        paso = Float64(Parametro3)
        if paso == 0; paso = 1.0; end
        return collect(inicio:paso:fin_val)

    elseif TipoOutput == 3
        # Datos aleatorios Normal(μ, σ)
        n = Int(Parametro1) > 0 ? Int(Parametro1) : 100
        mu = Float64(Parametro2)
        sigma = Float64(Parametro3) > 0 ? Float64(Parametro3) : 1.0
        return mu .+ sigma .* randn(n)

    elseif TipoOutput == 4
        # Datos aleatorios Uniforme(a, b)
        n = Int(Parametro1) > 0 ? Int(Parametro1) : 100
        a = Float64(Parametro2)
        b = Float64(Parametro3) > a ? Float64(Parametro3) : a + 1.0
        return a .+ (b - a) .* rand(n)

    elseif TipoOutput == 5
        # Tabla de frecuencias cruzadas
        # Parametro1 y Parametro2 son vectores
        if !isa(Parametro1, AbstractArray) || !isa(Parametro2, AbstractArray)
            return "Error: Parametro1 y Parametro2 deben ser vectores"
        end
        v1 = vec(Parametro1)
        v2 = vec(Parametro2)
        u1 = sort(unique(v1))
        u2 = sort(unique(v2))
        resultado = ["\t" * join(string.(u2), "\t")]
        for val1 in u1
            counts = [count(i -> v1[i] == val1 && v2[i] == val2, 1:length(v1)) for val2 in u2]
            push!(resultado, string(val1, "\t", join(string.(counts), "\t")))
        end
        return resultado

    elseif TipoOutput == 6
        # Buscar y reemplazar
        if !isa(Parametro1, AbstractArray)
            return "Error: Parametro1 debe ser los datos"
        end
        D = Parametro1
        buscar = Parametro2
        reemplazar = Parametro3
        return replace(D, buscar => reemplazar)

    elseif TipoOutput == 7
        # Redondear datos
        if !isa(Parametro1, AbstractArray)
            return round(Float64(Parametro1), digits=Int(Parametro2))
        end
        decimales = Int(Parametro2) >= 0 ? Int(Parametro2) : 2
        return round.(Float64.(Parametro1), digits=decimales)

    elseif TipoOutput == 8
        # Convertir tipos
        if !isa(Parametro1, AbstractArray)
            return "Error: Parametro1 debe ser los datos"
        end
        try
            return Float64.(Parametro1)
        catch
            return string.(Parametro1)
        end

    else
        return "TipoOutput no válido. Use 0 para ver procedimientos disponibles."
    end
end

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# FIN DE J4XCL-CN-Conectividad.jl                      +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
