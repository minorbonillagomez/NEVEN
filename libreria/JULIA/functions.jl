# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# J4XCL Ã¢â‚¬â€ LibrerÃƒÂ­a de Funciones Julia para NEVEN
# MatemÃƒÂ¡ticas, EstadÃƒÂ­stica, OptimizaciÃƒÂ³n, Conectividad
# Universidad de Costa Rica Ã¢â‚¬â€ Tesis de MaestrÃƒÂ­a
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

using LinearAlgebra
using Statistics
using DelimitedFiles
using Dates
using Random

# Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ Patch ListFunctions: fix Base.Docs.doc() crash in Julia 1.12 Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
function NEVEN.ListFunctions()
    functions = Any[]
    for name in names(Main)
        if !isdefined(Main, name) continue end
        obj = getfield(Main, name)
        if obj isa Function && name != :NEVEN && name != :RJ && name != :include && name != :eval
            m = methods(obj)
            if length(m) > 0
                entry = String[]
                push!(entry, string(name))
                doc_str = try; strip(string(Base.Docs.doc(obj))); catch; ""; end
                push!(entry, doc_str)
                push!(entry, "Julia")
                arg_names = Base.method_argnames(m.ms[1])[2:end]
                for a in arg_names; push!(entry, string(a)); end
                push!(functions, entry)
            end
        end
    end
    return functions
end

# Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬ Funciones originales Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

function TestAdd(a...)
    sum(collect(Base.Iterators.flatten(a)))
end

function EigenValues(mat)
    eigvals(mat)
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 1: ÃƒÂLGEBRA LINEAL AVANZADA
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JM_Algebra(Matriz, VectorB=nothing, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Factorizacion LU","[02] Factorizacion QR","[03] Descomposicion SVD",
                "[04] Valores Propios","[05] Vectores Propios","[06] Determinante",
                "[07] Rango","[08] Normas","[09] Numero de Condicion",
                "[10] Pseudoinversa Moore-Penrose","[11] Traza","[12] Resolver Ax=b"]
    end
    A = Float64.(Matriz)
    if ndims(A)==1; n=isqrt(length(A)); A=reshape(A,n,n); end

    if TipoOutput == 1
        F=lu(A); return vcat(F.L, fill(NaN,1,size(A,2)), F.U)
    elseif TipoOutput == 2
        F=qr(A); return vcat(Matrix(F.Q), fill(NaN,1,size(A,2)), F.R)
    elseif TipoOutput == 3
        F=svd(A); return F.S
    elseif TipoOutput == 4
        return eigvals(A)
    elseif TipoOutput == 5
        return eigen(A).vectors
    elseif TipoOutput == 6
        return det(A)
    elseif TipoOutput == 7
        return rank(A)
    elseif TipoOutput == 8
        return [norm(A), opnorm(A,1), opnorm(A,2), opnorm(A,Inf)]
    elseif TipoOutput == 9
        return cond(A)
    elseif TipoOutput == 10
        return pinv(A)
    elseif TipoOutput == 11
        return tr(A)
    elseif TipoOutput == 12
        if VectorB === nothing || VectorB == 0; return "Error: VectorB requerido"; end
        return A \ Float64.(vec(VectorB))
    end
    return "TipoOutput no valido. Use 0 para ver procedimientos."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 2: CÃƒÂLCULO NUMÃƒâ€°RICO
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JM_Calculo(VectorX, VectorY=nothing, Parametro=0.0, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Derivada numerica","[02] Integral Trapecio","[03] Integral Simpson",
                "[04] Raiz Biseccion","[05] Interpolacion Lineal",
                "[06] Interpolacion Lagrange","[07] Serie de Taylor"]
    end
    x = Float64.(vec(VectorX))

    if TipoOutput == 1  # Derivada numÃƒÂ©rica
        if VectorY === nothing || VectorY == 0; return "Error: VectorY requerido"; end
        y = Float64.(vec(VectorY)); n = length(x)
        dy = zeros(n)
        dy[1] = (y[2]-y[1])/(x[2]-x[1])
        dy[n] = (y[n]-y[n-1])/(x[n]-x[n-1])
        for i in 2:n-1; dy[i] = (y[i+1]-y[i-1])/(x[i+1]-x[i-1]); end
        return dy
    elseif TipoOutput == 2  # Trapecio
        if VectorY === nothing || VectorY == 0; return "Error: VectorY requerido"; end
        y = Float64.(vec(VectorY)); n = length(x)
        s = 0.0; for i in 1:n-1; s += (x[i+1]-x[i])*(y[i]+y[i+1])/2; end
        return s
    elseif TipoOutput == 3  # Simpson
        if VectorY === nothing || VectorY == 0; return "Error: VectorY requerido"; end
        y = Float64.(vec(VectorY)); n = length(x)
        if n<3||(n-1)%2!=0; return "Error: Simpson requiere numero impar de puntos"; end
        h = (x[end]-x[1])/(n-1); s = y[1]+y[n]
        for i in 2:2:n-1; s += 4*y[i]; end
        for i in 3:2:n-2; s += 2*y[i]; end
        return s*h/3
    elseif TipoOutput == 4  # BisecciÃƒÂ³n
        if length(x)<2; return "Error: VectorX=[a,b]"; end
        if VectorY === nothing || VectorY == 0; return "Error: VectorY=[f(a),f(b)]"; end
        y = Float64.(vec(VectorY)); tol = Parametro>0 ? Float64(Parametro) : 1e-8
        a,b = x[1],x[2]; fa,fb = y[1],y[2]
        if fa*fb>0; return "Error: f(a)*f(b) debe ser < 0"; end
        for _ in 1:100
            mid = (a+b)/2; fmid = fa+(fb-fa)*(mid-a)/(b-a)
            if abs(b-a)<tol; return mid; end
            if fa*fmid<0; b=mid; fb=fmid; else; a=mid; fa=fmid; end
        end
        return (a+b)/2
    elseif TipoOutput == 5  # InterpolaciÃƒÂ³n lineal
        if VectorY === nothing || VectorY == 0; return "Error: VectorY requerido"; end
        y = Float64.(vec(VectorY)); xp = Float64(Parametro)
        for i in 1:length(x)-1
            if x[i]<=xp<=x[i+1]; t=(xp-x[i])/(x[i+1]-x[i]); return y[i]+t*(y[i+1]-y[i]); end
        end
        return "Error: punto fuera de rango"
    elseif TipoOutput == 6  # Lagrange
        if VectorY === nothing || VectorY == 0; return "Error: VectorY requerido"; end
        y = Float64.(vec(VectorY)); xp = Float64(Parametro); n = length(x)
        r = 0.0
        for i in 1:n; Li=1.0; for j in 1:n; if i!=j; Li*=(xp-x[j])/(x[i]-x[j]); end; end; r+=y[i]*Li; end
        return r
    elseif TipoOutput == 7  # Taylor
        if VectorY === nothing || VectorY == 0; return "Error: VectorY=coeficientes"; end
        c = Float64.(vec(VectorY)); a = x[1]; xp = Float64(Parametro)
        r = 0.0; for (k,ci) in enumerate(c); r += ci*(xp-a)^(k-1); end
        return r
    end
    return "TipoOutput no valido. Use 0 para ver procedimientos."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 3: ECUACIONES DIFERENCIALES ORDINARIAS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JM_EDO(VectorX, VectorY, Parametro=0.01, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Euler Explicito (dy/dt=-y)","[02] Runge-Kutta 4 (dy/dt=-y)",
                "[03] Sistema EDOs RK4 (oscilador)","[04] EDO 2do Orden RK4 (y''+y=0)"]
    end
    t0,tf = Float64(VectorX[1]),Float64(VectorX[2])
    y0 = Float64.(vec(VectorY))
    h = Float64(Parametro); if h<=0; h=0.01; end
    n = Int(ceil((tf-t0)/h))

    if TipoOutput == 1  # Euler
        t=zeros(n+1); y=zeros(n+1); t[1]=t0; y[1]=y0[1]
        for i in 1:n; t[i+1]=t[i]+h; y[i+1]=y[i]+h*(-y[i]); end
        return hcat(t, y)
    elseif TipoOutput == 2  # RK4
        f(t,y) = -y
        t=zeros(n+1); y=zeros(n+1); t[1]=t0; y[1]=y0[1]
        for i in 1:n
            k1=h*f(t[i],y[i]); k2=h*f(t[i]+h/2,y[i]+k1/2)
            k3=h*f(t[i]+h/2,y[i]+k2/2); k4=h*f(t[i]+h,y[i]+k3)
            y[i+1]=y[i]+(k1+2k2+2k3+k4)/6; t[i+1]=t[i]+h
        end
        return hcat(t, y)
    elseif TipoOutput == 3  # Sistema oscilador
        f(t,y) = [-y[2], y[1]]
        t=zeros(n+1); ya=zeros(n+1,2); t[1]=t0; ya[1,:]=y0[1:min(2,length(y0))]
        for i in 1:n
            yi=ya[i,:]; ti=t[i]
            k1=h.*f(ti,yi); k2=h.*f(ti+h/2,yi.+k1./2)
            k3=h.*f(ti+h/2,yi.+k2./2); k4=h.*f(ti+h,yi.+k3)
            ya[i+1,:]=yi.+(k1.+2 .*k2.+2 .*k3.+k4)./6; t[i+1]=ti+h
        end
        return hcat(t, ya)
    elseif TipoOutput == 4  # 2do orden y''+y=0
        f(t,y) = [y[2], -y[1]]
        t=zeros(n+1); ya=zeros(n+1,2); t[1]=t0; ya[1,:]=y0[1:min(2,length(y0))]
        for i in 1:n
            yi=ya[i,:]; ti=t[i]
            k1=h.*f(ti,yi); k2=h.*f(ti+h/2,yi.+k1./2)
            k3=h.*f(ti+h/2,yi.+k2./2); k4=h.*f(ti+h,yi.+k3)
            ya[i+1,:]=yi.+(k1.+2 .*k2.+2 .*k3.+k4)./6; t[i+1]=ti+h
        end
        return hcat(t, ya)
    end
    return "TipoOutput no valido. Use 0 para ver procedimientos."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 4: CLASIFICACIÃƒâ€œN Y REGRESIÃƒâ€œN
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function _modo(v)
    counts = Dict{eltype(v),Int}()
    for x in v; counts[x] = get(counts,x,0)+1; end
    return sort(collect(counts), by=x->x[2], rev=true)[1][1]
end

function JML_Clasificacion(SetDatosX, SetDatosY=nothing, K=3, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] KNN Clasificacion","[02] Regresion Lineal","[03] Prediccion RegLineal",
                "[04] Coeficientes y R2","[05] Residuos","[06] Matriz de Confusion"]
    end
    X = Float64.(SetDatosX)
    if SetDatosY !== nothing && SetDatosY != 0; Y = vec(SetDatosY); end

    if TipoOutput == 1  # KNN
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        k = Int(K); n = size(X,1); pred = similar(Y)
        for i in 1:n
            dists = [(sqrt(sum((X[i,:].-X[j,:]).^2)), j) for j in 1:n if j!=i]
            sort!(dists, by=x->x[1])
            vecinos = [Y[dists[v][2]] for v in 1:min(k,length(dists))]
            pred[i] = _modo(vecinos)
        end
        acc = sum(pred.==Y)/n
        return vcat(["Accuracy: $(round(acc*100,digits=2))%"], [string("Obs ",i,": real=",Y[i]," pred=",pred[i]) for i in 1:min(n,30)])
    elseif TipoOutput == 2  # RegresiÃƒÂ³n lineal
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        y = Float64.(vec(Y)); n = size(X,1)
        Xa = hcat(ones(n), X); beta = Xa\y
        yh = Xa*beta; ss_res = sum((y.-yh).^2); ss_tot = sum((y.-mean(y)).^2)
        r2 = 1-ss_res/ss_tot
        return vcat([r2], beta)
    elseif TipoOutput == 3  # PredicciÃƒÂ³n
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        y = Float64.(vec(Y)); n = size(X,1)
        Xa = hcat(ones(n), X); beta = Xa\y
        return Xa*beta
    elseif TipoOutput == 4  # Coeficientes + RÃ‚Â²
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        y = Float64.(vec(Y)); n = size(X,1)
        Xa = hcat(ones(n), X); beta = Xa\y
        yh = Xa*beta; r2 = 1-sum((y.-yh).^2)/sum((y.-mean(y)).^2)
        return vcat(["R2 = $(round(r2,digits=6))"], ["Intercepto = $(round(beta[1],digits=6))"],
               [string("B",i," = ",round(beta[i+1],digits=6)) for i in 1:length(beta)-1])
    elseif TipoOutput == 5  # Residuos
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        y = Float64.(vec(Y)); Xa = hcat(ones(size(X,1)), X)
        return y .- Xa*(Xa\y)
    elseif TipoOutput == 6  # Matriz de confusiÃƒÂ³n (Y=[real, predicho] en 2 columnas)
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        real = vec(X[:,1]); pred = vec(X[:,2])
        clases = sort(unique(vcat(real,pred))); nc = length(clases)
        cm = zeros(Int,nc,nc)
        for i in 1:length(real)
            ri = findfirst(==(real[i]),clases); pi = findfirst(==(pred[i]),clases)
            if ri!==nothing && pi!==nothing; cm[ri,pi]+=1; end
        end
        return Float64.(cm)
    end
    return "TipoOutput no valido. Use 0 para ver procedimientos."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 5: CLUSTERING (K-MEDIAS)
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function _kmeans(X, k, rng; max_iter=100)
    n,p = size(X); idx = randperm(rng,n)[1:k]
    centros = X[idx,:]; asig = zeros(Int,n)
    for _ in 1:max_iter
        na = [argmin([sum((X[i,:].-centros[j,:]).^2) for j in 1:k]) for i in 1:n]
        nc = zeros(k,p)
        for j in 1:k; mask=na.==j; s=sum(mask); nc[j,:] = s>0 ? mean(X[mask,:],dims=1) : centros[j,:]; end
        na==asig && (asig=na; centros=nc; break)
        asig=na; centros=nc
    end
    wcss = sum(sum((X[i,:].-centros[asig[i],:]).^2) for i in 1:n)
    return centros, asig, wcss
end

function JML_Clustering(SetDatosX, K=3, Semilla=12345, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] K-Medias completo","[02] Centros","[03] Asignacion",
                "[04] WCSS","[05] Metodo del Codo","[06] Descriptivas por cluster"]
    end
    X = Float64.(SetDatosX); k = Int(K); rng = MersenneTwister(Int(Semilla))

    if TipoOutput in [1,2,3,4,6]
        centros, asig, wcss = _kmeans(X, k, rng)
        TipoOutput==1 && return Float64.(asig)
        TipoOutput==2 && return centros
        TipoOutput==3 && return Float64.(asig)
        TipoOutput==4 && return wcss
        if TipoOutput==6
            r = String[]
            for c in 1:k
                mask=asig.==c; nc=sum(mask)
                nc>0 && for j in 1:size(X,2)
                    col=X[mask,j]; push!(r, "C$c V$j: mu=$(round(mean(col),digits=3)) sd=$(round(std(col),digits=3))")
                end
            end
            return r
        end
    elseif TipoOutput == 5  # Codo
        mk = min(k, size(X,1)-1)
        return [_kmeans(X, ki, MersenneTwister(Int(Semilla)))[3] for ki in 1:mk]
    end
    return "TipoOutput no valido."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 6: ESTADÃƒÂSTICA DESCRIPTIVA Y TESTS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JML_Estadistica(SetDatosX, SetDatosY=nothing, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Descriptiva completa","[02] Correlacion","[03] Covarianza",
                "[04] Test t Student","[05] Normalizacion MinMax","[06] Estandarizacion ZScore",
                "[07] Percentiles","[08] Deteccion Outliers IQR"]
    end
    X = Float64.(SetDatosX)

    if TipoOutput == 1  # Descriptiva
        if ndims(X)==1; X=reshape(X,:,1); end
        p = size(X,2); r = zeros(p, 8)
        for j in 1:p
            c=sort(X[:,j]); n=length(c)
            r[j,:] = [n, mean(c), std(c), minimum(c),
                       c[max(1,Int(ceil(n*0.25)))], c[max(1,Int(ceil(n*0.5)))],
                       c[max(1,Int(ceil(n*0.75)))], maximum(c)]
        end
        return r  # cols: N, Media, Std, Min, Q1, Mediana, Q3, Max
    elseif TipoOutput == 2; return cor(X)
    elseif TipoOutput == 3; return cov(X)
    elseif TipoOutput == 4  # Test t
        if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
        x=vec(X); y=Float64.(vec(SetDatosY))
        mx,my = mean(x),mean(y); sx,sy = var(x),var(y)
        nx,ny = length(x),length(y); se = sqrt(sx/nx+sy/ny)
        t_stat = (mx-my)/se; df = (sx/nx+sy/ny)^2/((sx/nx)^2/(nx-1)+(sy/ny)^2/(ny-1))
        return [mx-my, t_stat, df, se]  # diferencia, t, gl, error estÃƒÂ¡ndar
    elseif TipoOutput == 5  # MinMax
        if ndims(X)==1; mn,mx=minimum(X),maximum(X); return mx>mn ? (X.-mn)./(mx-mn) : zeros(length(X)); end
        r=similar(X); for j in 1:size(X,2); mn,mx=minimum(X[:,j]),maximum(X[:,j]); r[:,j]=mx>mn ? (X[:,j].-mn)./(mx-mn) : zeros(size(X,1)); end; return r
    elseif TipoOutput == 6  # ZScore
        if ndims(X)==1; m,s=mean(X),std(X); return s>0 ? (X.-m)./s : zeros(length(X)); end
        r=similar(X); for j in 1:size(X,2); m,s=mean(X[:,j]),std(X[:,j]); r[:,j]=s>0 ? (X[:,j].-m)./s : zeros(size(X,1)); end; return r
    elseif TipoOutput == 7  # Percentiles
        x=sort(vec(X)); n=length(x)
        percs = [1,5,10,25,50,75,90,95,99]
        return [x[max(1,Int(ceil(n*p/100)))] for p in percs]
    elseif TipoOutput == 8  # Outliers IQR
        if ndims(X)==1; X=reshape(X,:,1); end
        r = zeros(size(X,2), 4)  # Q1, Q3, IQR, #outliers
        for j in 1:size(X,2)
            c=sort(X[:,j]); n=length(c)
            q1=c[max(1,Int(ceil(n*0.25)))]; q3=c[max(1,Int(ceil(n*0.75)))]
            iqr=q3-q1; lo=q1-1.5*iqr; hi=q3+1.5*iqr
            nout = count(x->x<lo||x>hi, X[:,j])
            r[j,:] = [q1, q3, iqr, nout]
        end
        return r
    end
    return "TipoOutput no valido."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 7: OPTIMIZACIÃƒâ€œN
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JO_Optimizar(Matriz, Vector=nothing, Parametro=0.01, MaxIter=1000, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Descenso Gradiente","[02] Gradiente con Momentum","[03] Metodo Newton",
                "[04] Seccion Aurea 1D","[05] Simplex (Prog. Lineal)",
                "[06] Minimos Cuadrados No-Negativos","[07] Prog. Cuadratica"]
    end
    A = Float64.(Matriz)

    if TipoOutput == 1  # Gradiente: min 0.5x'Ax - b'x
        if Vector === nothing || Vector == 0; return "Error: Vector (b) requerido"; end
        b=Float64.(vec(Vector)); lr=Float64(Parametro); mi=Int(MaxIter); n=size(A,1); x=zeros(n)
        for _ in 1:mi; g=A*x-b; norm(g)<1e-8 && break; x=x-lr*g; end
        return x
    elseif TipoOutput == 2  # Momentum
        if Vector === nothing || Vector == 0; return "Error: Vector (b) requerido"; end
        b=Float64.(vec(Vector)); lr=Float64(Parametro); mi=Int(MaxIter); n=size(A,1); x=zeros(n); v=zeros(n)
        for _ in 1:mi; g=A*x-b; norm(g)<1e-8 && break; v=0.9*v+lr*g; x=x-v; end
        return x
    elseif TipoOutput == 3  # Newton (cuadrÃƒÂ¡tica: 1 paso)
        if Vector === nothing || Vector == 0; return "Error: Vector (b) requerido"; end
        b=Float64.(vec(Vector)); return A\b
    elseif TipoOutput == 4  # SecciÃƒÂ³n ÃƒÂ¡urea
        M=Float64.(vec(Matriz)); a,b=M[1],M[2]; tol=Float64(Parametro)>0 ? Float64(Parametro) : 1e-6
        phi=(sqrt(5)-1)/2
        for _ in 1:Int(MaxIter)
            abs(b-a)<tol && return (a+b)/2
            x1=b-phi*(b-a); x2=a+phi*(b-a)
            x1^2<x2^2 ? (b=x2) : (a=x1)
        end
        return (a+b)/2
    elseif TipoOutput == 5  # Simplex
        if Vector === nothing || Vector == 0; return "Error: Vector (costos) requerido"; end
        c=Float64.(vec(Vector)); m,np1=size(A); n=np1-1
        Ai=A[:,1:n]; bi=A[:,end]
        any(bi.<0) && return "Error: b debe ser >= 0"
        tab=zeros(m+1,n+m+1); tab[1:m,1:n]=Ai; tab[1:m,n+1:n+m]=I(m); tab[1:m,end]=bi; tab[end,1:n]=-c
        basis=collect(n+1:n+m)
        for _ in 1:Int(MaxIter)
            obj=tab[end,1:end-1]; pc=argmin(obj); obj[pc]>=-1e-10 && break
            rats=fill(Inf,m); for i in 1:m; tab[i,pc]>1e-10 && (rats[i]=tab[i,end]/tab[i,pc]); end
            pr=argmin(rats); rats[pr]==Inf && return "No acotado"
            tab[pr,:]./=tab[pr,pc]
            for i in 1:m+1; i!=pr && (tab[i,:]-=tab[i,pc]*tab[pr,:]); end
            basis[pr]=pc
        end
        x=zeros(n); for i in 1:m; basis[i]<=n && (x[basis[i]]=tab[i,end]); end
        return x
    elseif TipoOutput == 6  # NNLS
        if Vector === nothing || Vector == 0; return "Error: Vector (b) requerido"; end
        b=Float64.(vec(Vector)); n=size(A,2); x=zeros(n); lr=Float64(Parametro)>0 ? Float64(Parametro) : 0.001
        for _ in 1:Int(MaxIter); xn=max.(0,x-lr*(A'*(A*x-b))); norm(xn-x)<1e-10 && (x=xn; break); x=xn; end
        return x
    elseif TipoOutput == 7  # QP: min 0.5x'Qx + c'x, x>=0
        if Vector === nothing || Vector == 0; return "Error: Vector (c) requerido"; end
        c=Float64.(vec(Vector)); n=size(A,1); x=zeros(n); lr=Float64(Parametro)>0 ? Float64(Parametro) : 0.01
        for _ in 1:Int(MaxIter); xn=max.(0,x-lr*(A*x+c)); norm(xn-x)<1e-10 && (x=xn; break); x=xn; end
        return x
    end
    return "TipoOutput no valido."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 8: TRANSFORMACIÃƒâ€œN DE DATOS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JC_Transformar(Datos, Columna=1, Valor=nothing, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Transponer","[02] Ordenar por columna","[03] Filtrar filas",
                "[04] Seleccionar columnas","[05] Valores unicos","[06] Frecuencias"]
    end
    D = Datos
    if TipoOutput == 1; return isa(D,AbstractMatrix) ? permutedims(D) : reshape(D,1,:); end
    if TipoOutput == 2  # Ordenar
        if !isa(D,AbstractMatrix); return sort(vec(D)); end
        col=Int(Columna); return D[sortperm(D[:,col]),:]
    end
    if TipoOutput == 3  # Filtrar
        if !isa(D,AbstractMatrix); return "Error: Datos debe ser matriz"; end
        col=Int(Columna); mask=D[:,col].==Valor; return D[mask,:]
    end
    if TipoOutput == 4  # Seleccionar columnas
        if !isa(D,AbstractMatrix); return D; end
        cols = isa(Columna,AbstractArray) ? Int.(vec(Columna)) : [Int(Columna)]
        return D[:,cols]
    end
    if TipoOutput == 5  # ÃƒÅ¡nicos
        return isa(D,AbstractMatrix) ? unique(D[:,Int(Columna)]) : unique(vec(D))
    end
    if TipoOutput == 6  # Frecuencias
        vals = isa(D,AbstractMatrix) ? D[:,Int(Columna)] : vec(D)
        u = sort(unique(vals)); return hcat(u, [count(==(v),vals) for v in u])
    end
    return "TipoOutput no valido."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MÃƒâ€œDULO 9: UTILIDADES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

function JC_Utilidades(P1=0, P2=0, P3=0, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Fecha y hora","[02] Secuencia numerica","[03] Aleatorios Normal",
                "[04] Aleatorios Uniforme","[05] Redondear datos"]
    end
    if TipoOutput == 1; return string(Dates.now()); end
    if TipoOutput == 2; paso=Float64(P3)==0 ? 1.0 : Float64(P3); return collect(Float64(P1):paso:Float64(P2)); end
    if TipoOutput == 3; n=Int(P1)>0 ? Int(P1) : 100; return Float64(P2).+Float64(P3>0 ? P3 : 1).*randn(n); end
    if TipoOutput == 4; n=Int(P1)>0 ? Int(P1) : 100; a=Float64(P2); b=Float64(P3)>a ? Float64(P3) : a+1; return a.+(b-a).*rand(n); end
    if TipoOutput == 5  # Redondear
        if !isa(P1,AbstractArray); return round(Float64(P1),digits=Int(P2)); end
        return round.(Float64.(P1),digits=Int(P2)>=0 ? Int(P2) : 2)
    end
    return "TipoOutput no valido."
end

# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# FIN DE J4XCL Ã¢â‚¬â€ LibrerÃƒÂ­a Julia para NEVEN
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FUNCIONES SEPARADAS: KNN y Regresion
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

function JML_KNN(SetDatosX, SetDatosY, K=3, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Clasificacion KNN","[02] Precision por clase",
                "[03] Matriz de confusion","[04] Prediccion leave-one-out",
                "[05] Distancias al vecino mas cercano"]
    end
    X = Float64.(SetDatosX)
    if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
    Y = vec(SetDatosY)
    k = Int(K); n = size(X,1)

    # Calcular predicciones leave-one-out
    pred = similar(Y)
    dists_nearest = zeros(n)
    for i in 1:n
        d = [(sqrt(sum((X[i,:].-X[j,:]).^2)), j) for j in 1:n if j!=i]
        sort!(d, by=x->x[1])
        vecinos = [Y[d[v][2]] for v in 1:min(k,length(d))]
        pred[i] = _modo(vecinos)
        dists_nearest[i] = d[1][1]
    end

    if TipoOutput == 1  # Clasificacion con accuracy
        acc = sum(pred.==Y)/n
        return vcat(["Accuracy: $(round(acc*100,digits=2))%"],
                    [string("Obs ",i,": real=",Y[i]," pred=",pred[i],
                            pred[i]==Y[i] ? " OK" : " MISS") for i in 1:min(n,30)])
    elseif TipoOutput == 2  # Precision por clase
        clases = sort(unique(Y))
        result = String[]
        for c in clases
            tp = sum((pred.==c) .& (Y.==c))
            fp = sum((pred.==c) .& (Y.!=c))
            fn = sum((pred.!=c) .& (Y.==c))
            prec = tp+fp>0 ? tp/(tp+fp) : 0.0
            rec = tp+fn>0 ? tp/(tp+fn) : 0.0
            f1 = prec+rec>0 ? 2*prec*rec/(prec+rec) : 0.0
            push!(result, "Clase $c: Precision=$(round(prec,digits=3)) Recall=$(round(rec,digits=3)) F1=$(round(f1,digits=3))")
        end
        return result
    elseif TipoOutput == 3  # Matriz de confusion
        clases = sort(unique(vcat(Y, pred))); nc = length(clases)
        cm = zeros(Int, nc, nc)
        for i in 1:n
            ri = findfirst(==(Y[i]), clases)
            pi = findfirst(==(pred[i]), clases)
            if ri !== nothing && pi !== nothing; cm[ri,pi] += 1; end
        end
        return Float64.(cm)
    elseif TipoOutput == 4  # Predicciones
        return hcat(Y, pred)
    elseif TipoOutput == 5  # Distancias
        return dists_nearest
    end
    return "TipoOutput no valido."
end

function JML_Regresion(SetDatosX, SetDatosY, Parametro=0, TipoOutput=0)
    TipoOutput = Int(TipoOutput)
    if TipoOutput == 0
        return ["[01] Regresion lineal (coeficientes + R2)",
                "[02] Prediccion (valores ajustados)",
                "[03] Residuos",
                "[04] Resumen completo",
                "[05] Intervalos de confianza (95%)"]
    end
    X = Float64.(SetDatosX)
    if SetDatosY === nothing || SetDatosY == 0; return "Error: SetDatosY requerido"; end
    y = Float64.(vec(SetDatosY))
    n = size(X,1)
    Xa = hcat(ones(n), X)
    beta = Xa \ y
    yhat = Xa * beta
    resid = y .- yhat
    ss_res = sum(resid.^2)
    ss_tot = sum((y .- mean(y)).^2)
    r2 = 1 - ss_res/ss_tot
    p = size(Xa,2)

    if TipoOutput == 1  # Coeficientes + R2
        result = ["R2 = $(round(r2, digits=6))"]
        push!(result, "Intercepto = $(round(beta[1], digits=6))")
        for i in 2:length(beta)
            push!(result, "B$(i-1) = $(round(beta[i], digits=6))")
        end
        return result
    elseif TipoOutput == 2  # Prediccion
        return yhat
    elseif TipoOutput == 3  # Residuos
        return resid
    elseif TipoOutput == 4  # Resumen completo
        mse = ss_res / (n-p)
        se_beta = sqrt.(diag(mse .* inv(Xa'*Xa)))
        t_stats = beta ./ se_beta
        result = ["R2 = $(round(r2, digits=6)), R2adj = $(round(1-(1-r2)*(n-1)/(n-p), digits=6))"]
        push!(result, "MSE = $(round(mse, digits=4)), RMSE = $(round(sqrt(mse), digits=4))")
        push!(result, "--- Coeficientes ---")
        names = vcat(["Intercepto"], ["B$i" for i in 1:length(beta)-1])
        for i in 1:length(beta)
            push!(result, "$(names[i]): $(round(beta[i],digits=4)) (SE=$(round(se_beta[i],digits=4)), t=$(round(t_stats[i],digits=3)))")
        end
        return result
    elseif TipoOutput == 5  # Intervalos de confianza 95%
        mse = ss_res / (n-p)
        se_beta = sqrt.(diag(mse .* inv(Xa'*Xa)))
        t_crit = 1.96  # aprox para n grande
        result = String[]
        names = vcat(["Intercepto"], ["B$i" for i in 1:length(beta)-1])
        for i in 1:length(beta)
            lo = beta[i] - t_crit*se_beta[i]
            hi = beta[i] + t_crit*se_beta[i]
            push!(result, "$(names[i]): [$(round(lo,digits=4)), $(round(hi,digits=4))]")
        end
        return result
    end
    return "TipoOutput no valido."
end

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# ALIASES â€” Nombres cortos para el usuario
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Algebra(a...) = JM_Algebra(a...)
Calculo(a...) = JM_Calculo(a...)
EDO(a...) = JM_EDO(a...)
Estadistica(a...) = JML_Estadistica(a...)
Clasificacion(a...) = JML_Clasificacion(a...)
Clustering(a...) = JML_Clustering(a...)
Optimizar(a...) = JO_Optimizar(a...)
Transformar(a...) = JC_Transformar(a...)
Utilidades(a...) = JC_Utilidades(a...)
KNN(a...) = JML_KNN(a...)
Regresion(a...) = JML_Regresion(a...)
Utilidades(a...) = JC_Utilidades(a...)
