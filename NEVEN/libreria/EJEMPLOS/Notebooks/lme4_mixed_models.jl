### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000002-0002-0002-0002-000000000001
md"""
# Modelos Mixtos con lme4 (RCall)
Plantilla para modelos de efectos mixtos usando lmer() y glmer().
"""

# ╔═╡ 00000002-0002-0002-0002-000000000002
md"""
## Descripción
Modelos lineales de efectos mixtos para datos con estructura jerárquica
o medidas repetidas. Común en ciencias sociales y biología.
"""

# ╔═╡ 00000002-0002-0002-0002-000000000003
begin
	using RCall
	R"""
	library(lme4)
	# Datos de ejemplo: rendimiento por estudiante y escuela
	data(sleepstudy)
	# Modelo mixto: intercepto aleatorio por sujeto
	modelo_mixto <- lmer(Reaction ~ Days + (1|Subject), data = sleepstudy)
	summary(modelo_mixto)
	"""
end

# ╔═╡ 00000002-0002-0002-0002-000000000004
begin
	# Modelo mixto generalizado (conteo)
	R"""
	# Ejemplo con glmer para datos de conteo
	modelo_glmer <- glmer(Reaction ~ Days + (Days|Subject),
	                      data = sleepstudy, family = gaussian)
	# Extraer efectos aleatorios
	ranef(modelo_mixto)
	"""
end

# ╔═╡ 00000002-0002-0002-0002-000000000005
begin
	# Comparación de modelos con ANOVA
	R"""
	modelo_nulo <- lmer(Reaction ~ 1 + (1|Subject), data = sleepstudy)
	anova(modelo_nulo, modelo_mixto)
	"""
end
