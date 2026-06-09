### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000010-0010-0010-0010-000000000001
md"""
# Modelos Jerárquicos Bayesianos con Turing.jl
Plantilla para inferencia bayesiana con modelos jerárquicos en Julia.
"""

# ╔═╡ 00000010-0010-0010-0010-000000000002
md"""
## Descripción
Modelos bayesianos jerárquicos (multinivel) usando Turing.jl.
Permite estimar parámetros con incertidumbre y compartir información
entre grupos. Ideal para datos agrupados por región o institución.
"""

# ╔═╡ 00000010-0010-0010-0010-000000000003
begin
	using Turing, Distributions, Random
	Random.seed!(42)
	# Modelo jerárquico: media por grupo con hiperprior
	@model function modelo_jerarquico(y, grupo, n_grupos)
		# Hiperparámetros
		μ_global ~ Normal(0, 10)
		σ_global ~ truncated(Normal(0, 5), 0, Inf)
		σ_obs ~ truncated(Normal(0, 5), 0, Inf)
		# Medias por grupo
		μ_grupo ~ filldist(Normal(μ_global, σ_global), n_grupos)
		# Verosimilitud
		for i in eachindex(y)
			y[i] ~ Normal(μ_grupo[grupo[i]], σ_obs)
		end
	end
	# Datos simulados: 3 grupos
	n_grupos = 3
	grupo = repeat(1:n_grupos, inner=10)
	y = [randn(10) .+ 2; randn(10) .+ 5; randn(10) .+ 3]
	# Muestreo NUTS
	cadena = sample(modelo_jerarquico(y, grupo, n_grupos), NUTS(), 1000)
	println("Resumen de la cadena:")
	println(cadena)
end
