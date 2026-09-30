### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000013-0013-0013-0013-000000000001
md"""
# Pipeline Multilenguaje: Julia + R
Plantilla que combina preprocesamiento en Julia, regresión en R
y optimización final en Julia.
"""

# ╔═╡ 00000013-0013-0013-0013-000000000002
md"""
## Descripción
Demuestra la integración fluida entre Julia y R en un flujo de trabajo
completo: limpieza de datos en Julia → modelado estadístico en R →
optimización de decisiones en Julia. Patrón común en investigación aplicada.
"""

# ╔═╡ 00000013-0013-0013-0013-000000000003
begin
	using Statistics, Random
	Random.seed!(42)
	# Paso 1: Preprocesamiento en Julia (más rápido para datos grandes)
	n = 100
	datos_raw = Dict(
		"x1" => randn(n) .* 10 .+ 50,
		"x2" => randn(n) .* 5 .+ 20,
		"ruido" => randn(n)
	)
	# Variable dependiente con relación conocida
	datos_raw["y"] = 3.0 .* datos_raw["x1"] .+ 1.5 .* datos_raw["x2"] .+ datos_raw["ruido"] .* 2
	# Estandarización en Julia
	for col in ["x1", "x2"]
		μ = mean(datos_raw[col])
		σ = std(datos_raw[col])
		datos_raw[col] = (datos_raw[col] .- μ) ./ σ
	end
	println("Datos preprocesados: $(n) observaciones, variables estandarizadas")
end

# ╔═╡ 00000013-0013-0013-0013-000000000004
begin
	using RCall
	# Paso 2: Regresión en R (ecosistema estadístico maduro)
	@rput datos_raw
	R"""
	df <- data.frame(
		y = datos_raw$y,
		x1 = datos_raw$x1,
		x2 = datos_raw$x2
	)
	modelo <- lm(y ~ x1 + x2, data = df)
	coeficientes <- coef(modelo)
	r_cuadrado <- summary(modelo)$r.squared
	"""
	coefs_r = rcopy(R"coeficientes")
	r2 = rcopy(R"r_cuadrado")
	println("R²: $(round(r2, digits=4))")
	println("Coeficientes estimados: ", coefs_r)
end

# ╔═╡ 00000013-0013-0013-0013-000000000005
begin
	using JuMP, HiGHS
	# Paso 3: Optimización en Julia usando coeficientes de R
	modelo_opt = Model(HiGHS.Optimizer)
	set_silent(modelo_opt)
	@variable(modelo_opt, -2 <= z1 <= 2)  # x1 estandarizado
	@variable(modelo_opt, -2 <= z2 <= 2)  # x2 estandarizado
	# Maximizar predicción del modelo de R
	β0, β1, β2 = coefs_r[1], coefs_r[2], coefs_r[3]
	@objective(modelo_opt, Max, β0 + β1*z1 + β2*z2)
	# Restricción de presupuesto
	@constraint(modelo_opt, z1 + z2 <= 3)
	optimize!(modelo_opt)
	println("Asignación óptima: x1=$(round(value(z1),digits=2)), x2=$(round(value(z2),digits=2))")
	println("Valor predicho máximo: $(round(objective_value(modelo_opt), digits=2))")
end
