### A Pluto.jl notebook ###
# v0.20.4

using Markdown
using InteractiveUtils

# ╔═╡ a1b2c3d4-e5f6-7890-abcd-ef1234567801
md"""
# 📊 Dashboard desde Excel

Lee datos enviados desde Excel via `=RJ2XCL.PLUTO.DATA(rango, "ventas")`.

**Instrucciones:**
1. En Excel, coloca datos en un rango (ej: A1:C4)
2. Ejecuta `=RJ2XCL.PLUTO.DATA(A1:C4, "ventas")`
3. Haz clic en ▶ abajo para actualizar los datos
"""

# ╔═╡ a1b2c3d4-e5f6-7890-abcd-ef1234567802
function read_excel_data(name="ventas")
	filepath = joinpath("C:\\RJ2XCL\\data", "$(name).tsv")
	if !isfile(filepath)
		return nothing
	end
	lines = readlines(filepath)
	if isempty(lines)
		return nothing
	end
	rows = [split(line, "\t") for line in lines]
	ncols = length(rows[1])
	nrows = length(rows)
	data = Matrix{Any}(nothing, nrows, ncols)
	for i in 1:nrows
		for j in 1:min(ncols, length(rows[i]))
			val = rows[i][j]
			parsed = tryparse(Float64, val)
			data[i,j] = parsed !== nothing ? parsed : val
		end
	end
	return data
end

# ╔═╡ a1b2c3d4-e5f6-7890-abcd-ef1234567803
raw = read_excel_data("ventas")

# ╔═╡ a1b2c3d4-e5f6-7890-abcd-ef1234567804
if raw !== nothing
	headers = [string(raw[1,j]) for j in 1:size(raw,2)]
	nrows = size(raw,1) - 1
	header_str = join(headers, ", ")
	md"✅ **Datos recibidos:** $(nrows) filas — $(header_str)"
else
	md"⏳ **Esperando datos...** Ejecuta =RJ2XCL.PLUTO.DATA(rango, ventas) en Excel"
end

# ╔═╡ a1b2c3d4-e5f6-7890-abcd-ef1234567805
if raw !== nothing && size(raw,1) > 1
	results = String[]
	for j in 2:size(raw,2)
		col = string(raw[1,j])
		vals = Float64[raw[i,j] for i in 2:size(raw,1) if raw[i,j] isa Number]
		if !isempty(vals)
			μ = round(sum(vals)/length(vals), digits=2)
			push!(results, "**$(col):** media=$(μ), min=$(minimum(vals)), max=$(maximum(vals))")
		end
	end
	Markdown.parse("## 📈 Estadisticas\n\n" * join(results, "\n\n"))
end

# ╔═╡ a1b2c3d4-e5f6-7890-abcd-ef1234567806
md"""
---
*RJ2XCL v2.0 — Universidad de Costa Rica*
"""

# ╔═╡ Cell order:
# ╟─a1b2c3d4-e5f6-7890-abcd-ef1234567801
# ╠═a1b2c3d4-e5f6-7890-abcd-ef1234567802
# ╠═a1b2c3d4-e5f6-7890-abcd-ef1234567803
# ╠═a1b2c3d4-e5f6-7890-abcd-ef1234567804
# ╠═a1b2c3d4-e5f6-7890-abcd-ef1234567805
# ╟─a1b2c3d4-e5f6-7890-abcd-ef1234567806
