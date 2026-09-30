### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000009-0009-0009-0009-000000000001
md"""
# Simulación de EDOs con DifferentialEquations.jl
Plantilla para resolver ecuaciones diferenciales ordinarias en Julia.
"""

# ╔═╡ 00000009-0009-0009-0009-000000000002
md"""
## Descripción
Resolución numérica de sistemas de ecuaciones diferenciales ordinarias.
Incluye modelo SIR epidemiológico y oscilador armónico.
Útil para modelado de sistemas dinámicos en biología y física.
"""

# ╔═╡ 00000009-0009-0009-0009-000000000003
begin
	using DifferentialEquations
	# Modelo SIR epidemiológico
	function sir!(du, u, p, t)
		S, I, R = u
		β, γ = p  # Tasa de infección y recuperación
		du[1] = -β * S * I          # dS/dt
		du[2] = β * S * I - γ * I   # dI/dt
		du[3] = γ * I               # dR/dt
	end
	# Condiciones iniciales y parámetros
	u0 = [0.99, 0.01, 0.0]  # 99% susceptible, 1% infectado
	p = (0.3, 0.1)          # β=0.3, γ=0.1
	tspan = (0.0, 100.0)
	prob = ODEProblem(sir!, u0, tspan, p)
	sol = solve(prob, Tsit5())
	println("Pico de infectados: ", maximum(sol[2, :]))
end

# ╔═╡ 00000009-0009-0009-0009-000000000004
begin
	# Oscilador armónico amortiguado
	function oscilador!(du, u, p, t)
		x, v = u
		ω, ζ = p  # Frecuencia natural y amortiguamiento
		du[1] = v
		du[2] = -2ζ*ω*v - ω^2*x
	end
	u0_osc = [1.0, 0.0]  # Posición inicial, velocidad cero
	p_osc = (2π, 0.1)    # ω=2π, ζ=0.1
	prob_osc = ODEProblem(oscilador!, u0_osc, (0.0, 10.0), p_osc)
	sol_osc = solve(prob_osc)
	println("Posición final: ", sol_osc[1, end])
end
