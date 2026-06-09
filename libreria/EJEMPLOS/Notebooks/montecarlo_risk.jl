### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000011-0011-0011-0011-000000000001
md"""
# Simulación Monte Carlo para Análisis de Riesgo
Plantilla para simulación estocástica y cuantificación de riesgo en Julia.
"""

# ╔═╡ 00000011-0011-0011-0011-000000000002
md"""
## Descripción
Simulación Monte Carlo para evaluar riesgo financiero y operacional.
Incluye cálculo de VaR (Value at Risk) y simulación de flujos de caja.
Aplicable a gestión de riesgos en banca y seguros costarricenses.
"""

# ╔═╡ 00000011-0011-0011-0011-000000000003
begin
	using Random, Statistics, Distributions
	Random.seed!(123)
	# Simulación de retornos de portafolio
	n_simulaciones = 10_000
	μ_retorno = 0.08   # Retorno esperado anual
	σ_retorno = 0.15   # Volatilidad anual
	inversion = 1_000_000.0  # Inversión en colones
	# Simular retornos
	retornos = rand(Normal(μ_retorno, σ_retorno), n_simulaciones)
	valores_finales = inversion .* (1 .+ retornos)
	perdidas = inversion .- valores_finales
	# Value at Risk al 95%
	var_95 = quantile(perdidas, 0.95)
	println("VaR 95%: ₡$(round(var_95, digits=2))")
	println("Pérdida esperada (CVaR): ₡$(round(mean(perdidas[perdidas .> var_95]), digits=2))")
end

# ╔═╡ 00000011-0011-0011-0011-000000000004
begin
	# Simulación de flujo de caja con incertidumbre
	n_periodos = 12  # Meses
	n_sims = 5_000
	flujos = zeros(n_sims, n_periodos)
	for sim in 1:n_sims
		ingreso_base = 500_000.0
		for t in 1:n_periodos
			# Ingreso con variabilidad estacional
			variacion = rand(Normal(1.0, 0.1))
			flujos[sim, t] = ingreso_base * variacion * (1 + 0.02*t)
		end
	end
	# Probabilidad de flujo negativo acumulado
	flujo_total = sum(flujos, dims=2)
	prob_deficit = mean(flujo_total .< 5_000_000)
	println("Probabilidad de no alcanzar meta: $(round(prob_deficit*100, digits=1))%")
end
