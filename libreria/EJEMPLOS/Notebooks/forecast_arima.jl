### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000004-0004-0004-0004-000000000001
md"""
# Series de Tiempo y Pronóstico ARIMA (RCall)
Plantilla para auto.arima() y forecast() desde Julia.
"""

# ╔═╡ 00000004-0004-0004-0004-000000000002
md"""
## Descripción
Modelado de series de tiempo con selección automática de parámetros ARIMA.
Incluye pronóstico e intervalos de confianza. Útil para datos económicos
y financieros de Costa Rica.
"""

# ╔═╡ 00000004-0004-0004-0004-000000000003
begin
	using RCall
	R"""
	library(forecast)
	# Serie de ejemplo: pasajeros aéreos
	datos_ts <- AirPassengers
	# Selección automática del modelo ARIMA
	modelo_arima <- auto.arima(datos_ts)
	summary(modelo_arima)
	"""
end

# ╔═╡ 00000004-0004-0004-0004-000000000004
begin
	# Pronóstico a 12 períodos
	R"""
	pronostico <- forecast(modelo_arima, h = 12)
	print(pronostico)
	"""
end

# ╔═╡ 00000004-0004-0004-0004-000000000005
begin
	# Extraer valores pronosticados a Julia
	forecast_vals = rcopy(R"as.numeric(pronostico$mean)")
	println("Pronóstico 12 períodos: ", forecast_vals)
end
