### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000001-0001-0001-0001-000000000001
md"""
# Regresión Lineal y Logística con R (RCall)
Plantilla para modelos de regresión usando lm() y glm() desde Julia.
"""

# ╔═╡ 00000001-0001-0001-0001-000000000002
md"""
## Descripción
Este notebook demuestra cómo ejecutar regresiones lineales y logísticas
utilizando R a través de RCall.jl. Útil para análisis econométricos básicos.
"""

# ╔═╡ 00000001-0001-0001-0001-000000000003
begin
	using RCall
	# Cargar datos de ejemplo en R
	R"""
	data(mtcars)
	# Regresión lineal: consumo ~ peso + cilindros
	modelo_lineal <- lm(mpg ~ wt + cyl, data = mtcars)
	summary(modelo_lineal)
	"""
end

# ╔═╡ 00000001-0001-0001-0001-000000000004
begin
	# Regresión logística: variable binaria
	R"""
	mtcars$am_factor <- factor(mtcars$am)
	# Modelo logístico: transmisión ~ peso + caballos de fuerza
	modelo_logit <- glm(am_factor ~ wt + hp, data = mtcars, family = binomial)
	summary(modelo_logit)
	"""
end

# ╔═╡ 00000001-0001-0001-0001-000000000005
begin
	# Extraer coeficientes a Julia
	coefs = rcopy(R"coef(modelo_lineal)")
	println("Coeficientes del modelo lineal: ", coefs)
end
