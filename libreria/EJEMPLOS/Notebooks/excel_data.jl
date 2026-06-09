### A Pluto.jl notebook ###
# v0.20.4

using Markdown
using InteractiveUtils

# ╔═╡ a0000001-0000-0000-0000-000000000001
md"""
# 📊 RJ2XCL — Datos desde Excel

Notebook generico para trabajar con datos enviados desde Excel.

**Uso:**
1. En Excel: `=RJ2XCL.PLUTO.DATA(A1:Z100, "datos")`
2. Abre este notebook desde Excel o Pluto
3. Los datos se cargan automaticamente como DataFrame
4. Agrega tus propias celdas de analisis abajo
"""

# ╔═╡ a0000002-0000-0000-0000-000000000001
# Configuracion: nombre del dataset (cambiar si usaste otro nombre)
DATASET_NAME = "datos"

# ╔═╡ a0000003-0000-0000-0000-000000000001
# Leer datos del archivo compartido
function load_excel_data(name)
	filepath = joinpath("C:\\RJ2XCL\\data", "$(name).tsv")
	if !isfile(filepath)
		return nothing, String[], zeros(0,0)
	end
	lines = readlines(filepath)
	if isempty(lines)
		return nothing, String[], zeros(0,0)
	end
	rows = [split(line, "\t") for line in lines]
	ncols = length(rows[1])
	
	# Primera fila = encabezados
	headers = String[strip(string(rows[1][j])) for j in 1:ncols]
	
	# Resto = datos
	ndata = length(rows) - 1
	if ndata == 0
		return headers, headers, zeros(0, ncols)
	end
	
	# Detectar columnas numericas vs texto
	data = Matrix{Any}(nothing, ndata, ncols)
	for i in 1:ndata
		for j in 1:min(ncols, length(rows[i+1]))
			val = strip(string(rows[i+1][j]))
			parsed = tryparse(Float64, val)
			data[i,j] = parsed !== nothing ? parsed : val
		end
	end
	return headers, headers, data
end

# ╔═╡ a0000004-0000-0000-0000-000000000001
headers, _, raw_data = load_excel_data(DATASET_NAME)

# ╔═╡ a0000005-0000-0000-0000-000000000001
if headers === nothing
	md"""
	⏳ **Esperando datos...**
	
	Ejecuta en Excel:
	```
	=RJ2XCL.PLUTO.DATA(tu_rango, "datos")
	```
	Luego haz clic en ▶ en la celda de arriba para recargar.
	"""
else
	nrows = size(raw_data, 1)
	ncols = length(headers)
	header_str = join(headers, ", ")
	md"✅ **Dataset cargado:** $(nrows) registros × $(ncols) columnas: $(header_str)"
end

# ╔═╡ a0000006-0000-0000-0000-000000000001
md"## 📋 Vista previa de datos"

# ╔═╡ a0000007-0000-0000-0000-000000000001
# Mostrar tabla (primeras 20 filas)
if headers !== nothing && size(raw_data, 1) > 0
	preview_rows = min(20, size(raw_data, 1))
	header_line = "| " * join(headers, " | ") * " |"
	sep_line = "|" * join(fill("---", length(headers)), "|") * "|"
	data_lines = String[]
	for i in 1:preview_rows
		cells = [string(raw_data[i,j]) for j in 1:length(headers)]
		push!(data_lines, "| " * join(cells, " | ") * " |")
	end
	extra = size(raw_data,1) > 20 ? "\n\n*... y $(size(raw_data,1) - 20) filas mas*" : ""
	Markdown.parse(header_line * "\n" * sep_line * "\n" * join(data_lines, "\n") * extra)
end

# ╔═╡ a0000008-0000-0000-0000-000000000001
md"## 📈 Estadisticas descriptivas"

# ╔═╡ a0000009-0000-0000-0000-000000000001
# Estadisticas para columnas numericas
if headers !== nothing && size(raw_data, 1) > 0
	stats = String[]
	for j in 1:length(headers)
		vals = Float64[]
		for i in 1:size(raw_data, 1)
			if raw_data[i,j] isa Number
				push!(vals, Float64(raw_data[i,j]))
			end
		end
		if length(vals) > 0
			μ = round(sum(vals)/length(vals), digits=4)
			σ = length(vals) > 1 ? round(sqrt(sum((vals .- μ).^2)/(length(vals)-1)), digits=4) : 0.0
			push!(stats, "| **$(headers[j])** | $(length(vals)) | $(round(minimum(vals), digits=2)) | $(round(maximum(vals), digits=2)) | $(μ) | $(σ) |")
		end
	end
	if !isempty(stats)
		table = "| Columna | N | Min | Max | Media | Desv.Est |\n|---|---|---|---|---|---|\n" * join(stats, "\n")
		Markdown.parse(table)
	else
		md"*No se encontraron columnas numericas*"
	end
end

# ╔═╡ a0000010-0000-0000-0000-000000000001
md"""
## 🔬 Tu analisis

Agrega celdas debajo para tu propio analisis. Los datos estan en:
- `headers` — vector de nombres de columnas
- `raw_data` — matriz NxP con los datos (Any: numeros y texto)

**Ejemplo:** extraer una columna numerica:
```julia
col2 = Float64[raw_data[i,2] for i in 1:size(raw_data,1) if raw_data[i,2] isa Number]
```
"""

# ╔═╡ a0000011-0000-0000-0000-000000000001
md"""
---
*RJ2XCL v2.0 — Universidad de Costa Rica*
"""

# ╔═╡ Cell order:
# ╟─a0000001-0000-0000-0000-000000000001
# ╠═a0000002-0000-0000-0000-000000000001
# ╠═a0000003-0000-0000-0000-000000000001
# ╠═a0000004-0000-0000-0000-000000000001
# ╠═a0000005-0000-0000-0000-000000000001
# ╟─a0000006-0000-0000-0000-000000000001
# ╠═a0000007-0000-0000-0000-000000000001
# ╟─a0000008-0000-0000-0000-000000000001
# ╠═a0000009-0000-0000-0000-000000000001
# ╟─a0000010-0000-0000-0000-000000000001
# ╟─a0000011-0000-0000-0000-000000000001
