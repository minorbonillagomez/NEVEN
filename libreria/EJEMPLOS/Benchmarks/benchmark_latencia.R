# NEVEN Benchmark — Latencia de Llamadas
# Ejecutar desde Excel: =NEVEN.R("source('benchmark_latencia.R')")
# O copiar y pegar cada bloque en celdas individuales.
#
# Este script mide el tiempo de ida y vuelta (round-trip) de llamadas
# desde Excel a R via Named Pipes + Protobuf.

# ─── 1. Latencia basica (operacion trivial) ─────────────────────────

NEVEN_Benchmark_Basico <- function(n_iteraciones = 100) {
  tiempos <- numeric(n_iteraciones)
  for (i in 1:n_iteraciones) {
    t0 <- proc.time()["elapsed"]
    resultado <- 1 + 1  # Operacion trivial
    t1 <- proc.time()["elapsed"]
    tiempos[i] <- (t1 - t0) * 1000  # milisegundos
  }
  
  data.frame(
    Metrica = c("N", "Media_ms", "Mediana_ms", "Min_ms", "Max_ms", "P95_ms", "P99_ms"),
    Valor = c(
      n_iteraciones,
      round(mean(tiempos), 4),
      round(median(tiempos), 4),
      round(min(tiempos), 4),
      round(max(tiempos), 4),
      round(quantile(tiempos, 0.95), 4),
      round(quantile(tiempos, 0.99), 4)
    )
  )
}

# ─── 2. Latencia con datos (regresion lineal) ───────────────────────

NEVEN_Benchmark_Regresion <- function(n_filas = 1000) {
  set.seed(42)
  x <- rnorm(n_filas)
  y <- 2 * x + rnorm(n_filas, sd = 0.5)
  
  t0 <- proc.time()["elapsed"]
  modelo <- lm(y ~ x)
  coefs <- coef(modelo)
  r2 <- summary(modelo)$r.squared
  t1 <- proc.time()["elapsed"]
  
  tiempo_ms <- (t1 - t0) * 1000
  
  data.frame(
    Metrica = c("N_filas", "Tiempo_ms", "R2", "Intercepto", "Pendiente"),
    Valor = c(n_filas, round(tiempo_ms, 2), round(r2, 6), round(coefs[1], 6), round(coefs[2], 6))
  )
}

# ─── 3. Benchmark de escalabilidad ──────────────────────────────────

NEVEN_Benchmark_Escalabilidad <- function() {
  tamanos <- c(100, 500, 1000, 5000, 10000, 50000, 100000)
  resultados <- data.frame(N_filas = integer(), Tiempo_ms = numeric())
  
  for (n in tamanos) {
    set.seed(42)
    x <- rnorm(n)
    y <- 2 * x + rnorm(n, sd = 0.5)
    
    t0 <- proc.time()["elapsed"]
    modelo <- lm(y ~ x)
    t1 <- proc.time()["elapsed"]
    
    resultados <- rbind(resultados, data.frame(
      N_filas = n,
      Tiempo_ms = round((t1 - t0) * 1000, 2)
    ))
  }
  
  resultados
}

attr(NEVEN_Benchmark_Basico, "description") <- list(
  "Benchmark: mide latencia basica de R (N iteraciones de 1+1)",
  n_iteraciones = "Numero de iteraciones (default: 100)"
)
attr(NEVEN_Benchmark_Basico, "category") <- "NEVEN Benchmarks"

attr(NEVEN_Benchmark_Regresion, "description") <- list(
  "Benchmark: mide tiempo de regresion lineal con N filas",
  n_filas = "Numero de filas de datos (default: 1000)"
)
attr(NEVEN_Benchmark_Regresion, "category") <- "NEVEN Benchmarks"

attr(NEVEN_Benchmark_Escalabilidad, "description") <- list(
  "Benchmark: mide escalabilidad de regresion lineal (100 a 100K filas)"
)
attr(NEVEN_Benchmark_Escalabilidad, "category") <- "NEVEN Benchmarks"
