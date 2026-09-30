### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000005-0005-0005-0005-000000000001
md"""
# Análisis Factorial y PCA con R (RCall)
Plantilla para análisis de componentes principales, análisis factorial
y alfa de Cronbach usando el paquete psych.
"""

# ╔═╡ 00000005-0005-0005-0005-000000000002
md"""
## Descripción
Reducción de dimensionalidad y validación de instrumentos psicométricos.
Incluye PCA, análisis factorial exploratorio y confiabilidad interna.
"""

# ╔═╡ 00000005-0005-0005-0005-000000000003
begin
	using RCall
	R"""
	library(psych)
	# Datos de ejemplo: actitudes
	data(bfi)
	datos <- bfi[, 1:10]  # Primeros 10 ítems
	datos <- na.omit(datos)
	# Análisis de Componentes Principales
	pca_resultado <- principal(datos, nfactors = 3, rotate = "varimax")
	print(pca_resultado$loadings, cutoff = 0.3)
	"""
end

# ╔═╡ 00000005-0005-0005-0005-000000000004
begin
	# Análisis factorial exploratorio
	R"""
	fa_resultado <- fa(datos, nfactors = 2, fm = "ml", rotate = "oblimin")
	print(fa_resultado)
	"""
end

# ╔═╡ 00000005-0005-0005-0005-000000000005
begin
	# Alfa de Cronbach para confiabilidad
	R"""
	alpha_resultado <- alpha(datos[, 1:5])
	print(alpha_resultado$total)
	"""
end
