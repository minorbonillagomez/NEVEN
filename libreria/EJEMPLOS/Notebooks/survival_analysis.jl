### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000003-0003-0003-0003-000000000001
md"""
# Análisis de Supervivencia con R (RCall)
Plantilla para Kaplan-Meier y modelos de Cox.
"""

# ╔═╡ 00000003-0003-0003-0003-000000000002
md"""
## Descripción
Análisis de tiempo hasta un evento usando curvas de Kaplan-Meier
y el modelo de riesgos proporcionales de Cox. Aplicable en medicina,
ingeniería de confiabilidad y análisis de deserción.
"""

# ╔═╡ 00000003-0003-0003-0003-000000000003
begin
	using RCall
	R"""
	library(survival)
	# Datos de ejemplo: cáncer de pulmón
	data(lung)
	# Curva de Kaplan-Meier por sexo
	km_fit <- survfit(Surv(time, status) ~ sex, data = lung)
	summary(km_fit)
	"""
end

# ╔═╡ 00000003-0003-0003-0003-000000000004
begin
	# Modelo de Cox: riesgos proporcionales
	R"""
	# Modelo Cox con covariables
	cox_modelo <- coxph(Surv(time, status) ~ age + sex + ph.ecog, data = lung)
	summary(cox_modelo)
	"""
end

# ╔═╡ 00000003-0003-0003-0003-000000000005
begin
	# Prueba de log-rank para comparar grupos
	R"""
	logrank_test <- survdiff(Surv(time, status) ~ sex, data = lung)
	print(logrank_test)
	"""
end
