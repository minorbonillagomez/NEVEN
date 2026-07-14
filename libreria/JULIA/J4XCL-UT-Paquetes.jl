# NEVEN: Gestor de Paquetes Julia

import Pkg

"""
    Instalar(paquetes)

Instala paquetes Julia. Uso: =J.Instalar("MultivariateStats Clustering")
"""
function Instalar(paquetes)
    nombre = strip(String(paquetes))
    lista = split(nombre)
    resultados = String[]

    for paquete in lista
        nom = String(paquete)
        try
            Pkg.add(nom)
            push!(resultados, "[OK] $nom instalado")
        catch e
            push!(resultados, "[ERROR] $nom: $(sprint(showerror, e))")
        end
    end
    return join(resultados, "; ")
end

"""
    Verificar(paquete)

Verifica si un paquete esta instalado. Uso: =J.Verificar("LinearAlgebra")
"""
function Verificar(paquete)
    nombre = strip(String(paquete))
    try
        pkgs = Pkg.installed()
        if haskey(pkgs, nombre)
            v = pkgs[nombre]
            return nombre * " v" * (isnothing(v) ? "stdlib" : string(v)) * " [instalado]"
        end
        return nombre * " [NO instalado]"
    catch e
        return "Error: " * sprint(showerror, e)
    end
end

"""
    Paquetes()

Lista paquetes Julia instalados. Uso: =J.Paquetes()
"""
function Paquetes()
    try
        pkgs = Pkg.installed()
        resultado = String["Paquete | Version"]
        for (name, ver) in sort(collect(pkgs), by=first)
            v_str = isnothing(ver) ? "stdlib" : string(ver)
            push!(resultado, name * " | " * v_str)
        end
        return resultado
    catch e
        return "Error: " * sprint(showerror, e)
    end
end
