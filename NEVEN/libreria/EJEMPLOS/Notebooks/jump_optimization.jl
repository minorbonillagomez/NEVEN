### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000008-0008-0008-0008-000000000001
md"""
# Optimización con JuMP.jl
Plantilla para programación lineal y cuadrática en Julia nativo.
"""

# ╔═╡ 00000008-0008-0008-0008-000000000002
md"""
## Descripción
Formulación y resolución de problemas de optimización usando JuMP.
Incluye programación lineal (LP) y cuadrática (QP).
Aplicable a asignación de recursos, logística y finanzas.
"""

# ╔═╡ 00000008-0008-0008-0008-000000000003
begin
	using JuMP, HiGHS
	# Programación lineal: maximizar beneficio
	modelo = Model(HiGHS.Optimizer)
	set_silent(modelo)
	@variable(modelo, x >= 0)  # Producto A
	@variable(modelo, y >= 0)  # Producto B
	# Restricciones de recursos
	@constraint(modelo, 2x + y <= 100)   # Horas de trabajo
	@constraint(modelo, x + 3y <= 120)   # Material disponible
	# Función objetivo: maximizar ganancia
	@objective(modelo, Max, 5x + 4y)
	optimize!(modelo)
	println("Óptimo: x=$(value(x)), y=$(value(y)), Z=$(objective_value(modelo))")
end

# ╔═╡ 00000008-0008-0008-0008-000000000004
begin
	# Programación cuadrática: portafolio mínima varianza
	modelo_qp = Model(HiGHS.Optimizer)
	set_silent(modelo_qp)
	n_activos = 3
	retornos = [0.12, 0.10, 0.07]
	# Matriz de covarianza simplificada
	Σ = [0.04 0.01 0.005; 0.01 0.03 0.008; 0.005 0.008 0.02]
	@variable(modelo_qp, w[1:n_activos] >= 0)
	@constraint(modelo_qp, sum(w) == 1)
	@constraint(modelo_qp, sum(retornos .* w) >= 0.09)
	@objective(modelo_qp, Min, w' * Σ * w)
	optimize!(modelo_qp)
	println("Pesos óptimos: ", value.(w))
end
