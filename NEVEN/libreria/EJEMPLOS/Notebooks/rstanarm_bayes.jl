### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000007-0007-0007-0007-000000000001
md"""
# Regresión Bayesiana con rstanarm (RCall)
Plantilla para modelos bayesianos usando stan_lm() y stan_glm().
"""

# ╔═╡ 00000007-0007-0007-0007-000000000002
md"""
## Descripción
Inferencia bayesiana con priors informativos usando rstanarm.
Permite cuantificar incertidumbre en los parámetros y hacer
predicciones probabilísticas. Alternativa robusta a MLE.
"""

# ╔═╡ 00000007-0007-0007-0007-000000000003
begin
	using RCall
	R"""
	library(rstanarm)
	# Regresión lineal bayesiana
	data(mtcars)
	modelo_bayes <- stan_lm(mpg ~ wt + cyl, data = mtcars,
	                        prior = R2(location = 0.5),
	                        seed = 42, refresh = 0)
	summary(modelo_bayes)
	"""
end

# ╔═╡ 00000007-0007-0007-0007-000000000004
begin
	# Modelo logístico bayesiano
	R"""
	modelo_logit_bayes <- stan_glm(am ~ wt + hp, data = mtcars,
	                               family = binomial,
	                               seed = 42, refresh = 0)
	# Intervalos de credibilidad al 95%
	posterior_interval(modelo_logit_bayes, prob = 0.95)
	"""
end

# ╔═╡ 00000007-0007-0007-0007-000000000005
begin
	# Diagnóstico de convergencia
	R"""
	# Verificar R-hat y tamaño efectivo de muestra
	print(summary(modelo_bayes)[, c("Rhat", "n_eff")])
	"""
end
