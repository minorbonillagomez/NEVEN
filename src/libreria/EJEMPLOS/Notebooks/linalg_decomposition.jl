### A Pluto.jl notebook ###
# v0.19.0

# ╔═╡ 00000012-0012-0012-0012-000000000001
md"""
# Descomposiciones de Álgebra Lineal en Julia
Plantilla para SVD, QR y eigendescomposición usando LinearAlgebra.
"""

# ╔═╡ 00000012-0012-0012-0012-000000000002
md"""
## Descripción
Operaciones fundamentales de álgebra lineal numérica.
Incluye descomposición en valores singulares (SVD), factorización QR
y cálculo de eigenvalores. Base para PCA, mínimos cuadrados y más.
"""

# ╔═╡ 00000012-0012-0012-0012-000000000003
begin
	using LinearAlgebra
	# Matriz de ejemplo (datos económicos simulados)
	A = [4.0 2.0 1.0;
	     2.0 5.0 3.0;
	     1.0 3.0 6.0]
	# Descomposición en Valores Singulares
	F_svd = svd(A)
	println("Valores singulares: ", F_svd.S)
	println("Rango numérico: ", sum(F_svd.S .> 1e-10))
	# Aproximación de rango bajo (compresión de datos)
	k = 2  # Rango de aproximación
	A_aprox = F_svd.U[:, 1:k] * Diagonal(F_svd.S[1:k]) * F_svd.Vt[1:k, :]
	println("Error de aproximación rango-$k: ", norm(A - A_aprox))
end

# ╔═╡ 00000012-0012-0012-0012-000000000004
begin
	# Factorización QR para mínimos cuadrados
	X = [ones(5) [1.0, 2.0, 3.0, 4.0, 5.0]]  # Diseño con intercepto
	y = [2.1, 3.9, 6.2, 7.8, 10.1]
	F_qr = qr(X)
	β = F_qr \ y  # Coeficientes por QR
	println("Coeficientes (intercepto, pendiente): ", β)
end

# ╔═╡ 00000012-0012-0012-0012-000000000005
begin
	# Eigendescomposición para análisis espectral
	eigen_result = eigen(A)
	println("Eigenvalores: ", eigen_result.values)
	println("Eigenvector dominante: ", eigen_result.vectors[:, end])
	# Verificar: A*v = λ*v
	λ_max = eigen_result.values[end]
	v_max = eigen_result.vectors[:, end]
	println("Error de verificación: ", norm(A*v_max - λ_max*v_max))
end
