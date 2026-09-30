# =========================================================================
# NEVEN Notebook: Demo Regression Analysis (R)
# =========================================================================
# This is a simple R script notebook to test dynamic discovery.
# Place .R, .jl, or .py files in C:\NEVEN\notebooks\ and they appear
# automatically in =NEVEN.notebook.list()
#
# Usage from Excel:
#   =NEVEN.notebook.open("demo_regression")
# =========================================================================

# Simple linear regression demo
set.seed(42)
n <- 100
x <- rnorm(n, mean=50, sd=10)
y <- 2.5 * x + rnorm(n, sd=5) + 10

modelo <- lm(y ~ x)
cat("=== Linear Regression Demo ===\n")
cat("Coefficients:\n")
print(coef(modelo))
cat("\nR-squared:", summary(modelo)$r.squared, "\n")
cat("F-statistic:", summary(modelo)$fstatistic[1], "\n")
