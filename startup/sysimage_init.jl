# sysimage_init.jl -- Script minimo para PackageCompiler
# LECCION APRENDIDA: el sub-proceso de PackageCompiler tiene restricciones.
# Mantenemos este script MINIMO -- solo lo que funciono en la sysimage estable.
# functions.jl NO se incluye aqui -- se carga normalmente al iniciar Excel.

# Solo stdlib que sabemos que funciona en el contexto de PackageCompiler
using LinearAlgebra
using Statistics

# Operaciones base
sqrt(144.0)
1 + 1
string(1)
collect(1:10)
norm([3.0, 4.0])
mean([1.0, 2.0, 3.0])

println("Precompilacion completada exitosamente")
