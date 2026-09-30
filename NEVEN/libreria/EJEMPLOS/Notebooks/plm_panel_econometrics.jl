### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000006-0006-0006-0006-000000000001
md"""
# Econometría de Panel con plm (RCall)
Plantilla para modelos de datos de panel: efectos fijos, aleatorios y prueba de Hausman.
"""

# ╔═╡ 00000006-0006-0006-0006-000000000002
md"""
## Descripción
Modelos de datos de panel para análisis económico con múltiples entidades
observadas a lo largo del tiempo. Incluye estimadores FE/RE y diagnósticos.
Aplicable a datos macroeconómicos de países centroamericanos.
"""

# ╔═╡ 00000006-0006-0006-0006-000000000003
begin
	using RCall
	R"""
	library(plm)
	# Datos de ejemplo: inversión de Grunfeld
	data("Grunfeld", package = "plm")
	# Modelo de efectos fijos
	modelo_fe <- plm(inv ~ value + capital, data = Grunfeld,
	                 index = c("firm", "year"), model = "within")
	summary(modelo_fe)
	"""
end

# ╔═╡ 00000006-0006-0006-0006-000000000004
begin
	# Modelo de efectos aleatorios
	R"""
	modelo_re <- plm(inv ~ value + capital, data = Grunfeld,
	                 index = c("firm", "year"), model = "random")
	summary(modelo_re)
	"""
end

# ╔═╡ 00000006-0006-0006-0006-000000000005
begin
	# Prueba de Hausman: FE vs RE
	R"""
	hausman_test <- phtest(modelo_fe, modelo_re)
	print(hausman_test)
	# Si p < 0.05, se prefiere efectos fijos
	"""
end
