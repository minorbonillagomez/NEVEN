---
inclusion: manual
---

# NEVEN — Diccionario Estándar de Símbolos Unicode → LaTeX

> **Propósito:** Referencia canónica de todos los mapeos Unicode→LaTeX usados en el pipeline de conversión.
>
> **Archivo fuente:** `C:\NEVEN\tools\unicode_to_latex.py`
>
> **Cuándo usar:** 
> - Al agregar nuevos símbolos al conversor
> - Para verificar que un símbolo está soportado
> - Como referencia para otros pipelines de conversión

---

## Letras Griegas Minúsculas

| Unicode | Char | LaTeX | Nombre |
|---------|------|-------|--------|
| U+03B1 | α | `\alpha` | alpha |
| U+03B2 | β | `\beta` | beta |
| U+03B3 | γ | `\gamma` | gamma |
| U+03B4 | δ | `\delta` | delta |
| U+03B5 | ε | `\varepsilon` | varepsilon |
| U+03F5 | ϵ | `\epsilon` | epsilon |
| U+03B6 | ζ | `\zeta` | zeta |
| U+03B7 | η | `\eta` | eta |
| U+03B8 | θ | `\theta` | theta |
| U+03D1 | ϑ | `\vartheta` | vartheta |
| U+03B9 | ι | `\iota` | iota |
| U+03BA | κ | `\kappa` | kappa |
| U+03BB | λ | `\lambda` | lambda |
| U+03BC | μ | `\mu` | mu |
| U+00B5 | µ | `\mu` | micro (alias) |
| U+03BD | ν | `\nu` | nu |
| U+03BE | ξ | `\xi` | xi |
| U+03C0 | π | `\pi` | pi |
| U+03C1 | ρ | `\rho` | rho |
| U+03F1 | ϱ | `\varrho` | varrho |
| U+03C3 | σ | `\sigma` | sigma |
| U+03C2 | ς | `\varsigma` | varsigma |
| U+03C4 | τ | `\tau` | tau |
| U+03C5 | υ | `\upsilon` | upsilon |
| U+03C6 | φ | `\varphi` | varphi |
| U+03D5 | ϕ | `\phi` | phi |
| U+03C7 | χ | `\chi` | chi |
| U+03C8 | ψ | `\psi` | psi |
| U+03C9 | ω | `\omega` | omega |

---

## Letras Griegas Mayúsculas

| Unicode | Char | LaTeX | Nombre |
|---------|------|-------|--------|
| U+0393 | Γ | `\Gamma` | Gamma |
| U+0394 | Δ | `\Delta` | Delta |
| U+0398 | Θ | `\Theta` | Theta |
| U+039B | Λ | `\Lambda` | Lambda |
| U+039E | Ξ | `\Xi` | Xi |
| U+03A0 | Π | `\Pi` | Pi |
| U+03A3 | Σ | `\Sigma` | Sigma |
| U+03A5 | Υ | `\Upsilon` | Upsilon |
| U+03A6 | Φ | `\Phi` | Phi |
| U+03A8 | Ψ | `\Psi` | Psi |
| U+03A9 | Ω | `\Omega` | Omega |

---

## Operadores Matemáticos

| Unicode | Char | LaTeX | Descripción |
|---------|------|-------|-------------|
| U+2211 | ∑ | `\sum` | Sumatoria |
| U+220F | ∏ | `\prod` | Productoria |
| U+222B | ∫ | `\int` | Integral |
| U+222C | ∬ | `\iint` | Integral doble |
| U+222D | ∭ | `\iiint` | Integral triple |
| U+222E | ∮ | `\oint` | Integral de contorno |
| U+2202 | ∂ | `\partial` | Derivada parcial |
| U+2207 | ∇ | `\nabla` | Nabla/gradiente |
| U+221A | √ | `\sqrt` | Raíz cuadrada |
| U+221B | ∛ | `\sqrt[3]` | Raíz cúbica |
| U+221C | ∜ | `\sqrt[4]` | Raíz cuarta |
| U+221E | ∞ | `\infty` | Infinito |
| U+00B1 | ± | `\pm` | Más-menos |
| U+2213 | ∓ | `\mp` | Menos-más |
| U+00D7 | × | `\times` | Multiplicación |
| U+00F7 | ÷ | `\div` | División |
| U+00B7 | · | `\cdot` | Punto medio |
| U+2217 | ∗ | `*` | Asterisco operador |
| U+2218 | ∘ | `\circ` | Composición |
| U+2297 | ⊗ | `\otimes` | Producto tensorial |
| U+2295 | ⊕ | `\oplus` | Suma directa |
| U+2296 | ⊖ | `\ominus` | Resta circular |
| U+2299 | ⊙ | `\odot` | Producto Hadamard |

---

## Relaciones

| Unicode | Char | LaTeX | Descripción |
|---------|------|-------|-------------|
| U+2264 | ≤ | `\leq` | Menor o igual |
| U+2265 | ≥ | `\geq` | Mayor o igual |
| U+2260 | ≠ | `\neq` | No igual |
| U+2248 | ≈ | `\approx` | Aproximadamente |
| U+2245 | ≅ | `\cong` | Congruente |
| U+2261 | ≡ | `\equiv` | Idéntico |
| U+223C | ∼ | `\sim` | Similar |
| U+2243 | ≃ | `\simeq` | Similar o igual |
| U+221D | ∝ | `\propto` | Proporcional |
| U+226A | ≪ | `\ll` | Mucho menor |
| U+226B | ≫ | `\gg` | Mucho mayor |
| U+2282 | ⊂ | `\subset` | Subconjunto |
| U+2283 | ⊃ | `\supset` | Superconjunto |
| U+2286 | ⊆ | `\subseteq` | Subconjunto o igual |
| U+2287 | ⊇ | `\supseteq` | Superconjunto o igual |
| U+2208 | ∈ | `\in` | Pertenece |
| U+2209 | ∉ | `\notin` | No pertenece |
| U+220B | ∋ | `\ni` | Contiene |
| U+222A | ∪ | `\cup` | Unión |
| U+2229 | ∩ | `\cap` | Intersección |
| U+22A5 | ⊥ | `\perp` | Perpendicular |
| U+2225 | ∥ | `\parallel` | Paralelo |
| U+2220 | ∠ | `\angle` | Ángulo |
| U+2A7D | ⩽ | `\leqslant` | Menor o igual (slant) |
| U+2A7E | ⩾ | `\geqslant` | Mayor o igual (slant) |
| U+2272 | ≲ | `\lesssim` | Menor similar |
| U+2273 | ≳ | `\gtrsim` | Mayor similar |

---

## Flechas

| Unicode | Char | LaTeX | Descripción |
|---------|------|-------|-------------|
| U+2192 | → | `\to` | Flecha derecha |
| U+2190 | ← | `\leftarrow` | Flecha izquierda |
| U+2194 | ↔ | `\leftrightarrow` | Flecha bidireccional |
| U+21D2 | ⇒ | `\Rightarrow` | Implica |
| U+21D0 | ⇐ | `\Leftarrow` | Implicado por |
| U+21D4 | ⇔ | `\Leftrightarrow` | Si y solo si |
| U+2191 | ↑ | `\uparrow` | Flecha arriba |
| U+2193 | ↓ | `\downarrow` | Flecha abajo |
| U+2197 | ↗ | `\nearrow` | Flecha noreste |
| U+2198 | ↘ | `\searrow` | Flecha sureste |
| U+21A6 | ↦ | `\mapsto` | Mapea a |

---

## Lógica y Cuantificadores

| Unicode | Char | LaTeX | Descripción |
|---------|------|-------|-------------|
| U+2200 | ∀ | `\forall` | Para todo |
| U+2203 | ∃ | `\exists` | Existe |
| U+2204 | ∄ | `\nexists` | No existe |
| U+00AC | ¬ | `\neg` | Negación |
| U+2227 | ∧ | `\land` | Y lógico |
| U+2228 | ∨ | `\lor` | O lógico |
| U+22A4 | ⊤ | `\top` | Verdadero |
| U+22A5 | ⊥ | `\bot` | Falso |
| U+22A2 | ⊢ | `\vdash` | Deriva |
| U+22A8 | ⊨ | `\models` | Modela |

---

## Brackets y Delimitadores

| Unicode | Char | LaTeX | Descripción |
|---------|------|-------|-------------|
| U+27E8 | ⟨ | `\langle` | Ángulo izquierdo |
| U+27E9 | ⟩ | `\rangle` | Ángulo derecho |
| U+2308 | ⌈ | `\lceil` | Techo izquierdo |
| U+2309 | ⌉ | `\rceil` | Techo derecho |
| U+230A | ⌊ | `\lfloor` | Piso izquierdo |
| U+230B | ⌋ | `\rfloor` | Piso derecho |
| U+2016 | ‖ | `\|` | Doble barra (norma) |
| U+27E6 | ⟦ | `\llbracket` | Doble corchete izq |
| U+27E7 | ⟧ | `\rrbracket` | Doble corchete der |

---

## Superíndices Unicode

| Unicode | Char | Valor | Uso en LaTeX |
|---------|------|-------|--------------|
| U+2070 | ⁰ | 0 | `^{0}` |
| U+00B9 | ¹ | 1 | `^{1}` |
| U+00B2 | ² | 2 | `^{2}` |
| U+00B3 | ³ | 3 | `^{3}` |
| U+2074 | ⁴ | 4 | `^{4}` |
| U+2075 | ⁵ | 5 | `^{5}` |
| U+2076 | ⁶ | 6 | `^{6}` |
| U+2077 | ⁷ | 7 | `^{7}` |
| U+2078 | ⁸ | 8 | `^{8}` |
| U+2079 | ⁹ | 9 | `^{9}` |
| U+207A | ⁺ | + | `^{+}` |
| U+207B | ⁻ | - | `^{-}` |
| U+207C | ⁼ | = | `^{=}` |
| U+207D | ⁽ | ( | `^{(}` |
| U+207E | ⁾ | ) | `^{)}` |
| U+207F | ⁿ | n | `^{n}` |
| U+2071 | ⁱ | i | `^{i}` |

---

## Subíndices Unicode

| Unicode | Char | Valor | Uso en LaTeX |
|---------|------|-------|--------------|
| U+2080 | ₀ | 0 | `_{0}` |
| U+2081 | ₁ | 1 | `_{1}` |
| U+2082 | ₂ | 2 | `_{2}` |
| U+2083 | ₃ | 3 | `_{3}` |
| U+2084 | ₄ | 4 | `_{4}` |
| U+2085 | ₅ | 5 | `_{5}` |
| U+2086 | ₆ | 6 | `_{6}` |
| U+2087 | ₇ | 7 | `_{7}` |
| U+2088 | ₈ | 8 | `_{8}` |
| U+2089 | ₉ | 9 | `_{9}` |
| U+208A | ₊ | + | `_{+}` |
| U+208B | ₋ | - | `_{-}` |
| U+208C | ₌ | = | `_{=}` |
| U+208D | ₍ | ( | `_{(}` |
| U+208E | ₎ | ) | `_{)}` |
| U+2090 | ₐ | a | `_{a}` |
| U+2091 | ₑ | e | `_{e}` |
| U+2092 | ₒ | o | `_{o}` |
| U+2093 | ₓ | x | `_{x}` |
| U+2095 | ₕ | h | `_{h}` |
| U+2096 | ₖ | k | `_{k}` |
| U+2097 | ₗ | l | `_{l}` |
| U+2098 | ₘ | m | `_{m}` |
| U+2099 | ₙ | n | `_{n}` |
| U+209A | ₚ | p | `_{p}` |
| U+209B | ₛ | s | `_{s}` |
| U+209C | ₜ | t | `_{t}` |

---

## Fracciones Unicode

| Unicode | Char | LaTeX |
|---------|------|-------|
| U+00BD | ½ | `\frac{1}{2}` |
| U+2153 | ⅓ | `\frac{1}{3}` |
| U+2154 | ⅔ | `\frac{2}{3}` |
| U+00BE | ¾ | `\frac{3}{4}` |
| U+2155 | ⅕ | `\frac{1}{5}` |
| U+2156 | ⅖ | `\frac{2}{5}` |
| U+2157 | ⅗ | `\frac{3}{5}` |
| U+2158 | ⅘ | `\frac{4}{5}` |
| U+2159 | ⅙ | `\frac{1}{6}` |
| U+215A | ⅚ | `\frac{5}{6}` |
| U+215B | ⅛ | `\frac{1}{8}` |
| U+215C | ⅜ | `\frac{3}{8}` |
| U+215D | ⅝ | `\frac{5}{8}` |
| U+215E | ⅞ | `\frac{7}{8}` |

**⚠️ NOTA:** `¼` (U+00BC) está EXCLUIDO porque en Wooldridge significa `=`.

---

## Símbolos Especiales

| Unicode | Char | LaTeX | Descripción |
|---------|------|-------|-------------|
| U+2032 | ′ | `'` | Prima |
| U+2033 | ″ | `''` | Doble prima |
| U+2034 | ‴ | `'''` | Triple prima |
| U+00B0 | ° | `^\circ` | Grado |
| U+2205 | ∅ | `\emptyset` | Conjunto vacío |
| U+2115 | ℕ | `\mathbb{N}` | Naturales |
| U+2124 | ℤ | `\mathbb{Z}` | Enteros |
| U+211A | ℚ | `\mathbb{Q}` | Racionales |
| U+211D | ℝ | `\mathbb{R}` | Reales |
| U+2102 | ℂ | `\mathbb{C}` | Complejos |
| U+2111 | ℑ | `\Im` | Parte imaginaria |
| U+211C | ℜ | `\Re` | Parte real |
| U+2113 | ℓ | `\ell` | Ell cursiva |
| U+210F | ℏ | `\hbar` | h-barra (Planck) |
| U+2020 | † | `\dagger` | Daga |
| U+2021 | ‡ | `\ddagger` | Doble daga |
| U+2026 | … | `\ldots` | Puntos horizontales |
| U+22EF | ⋯ | `\cdots` | Puntos centrados |
| U+22EE | ⋮ | `\vdots` | Puntos verticales |
| U+22F1 | ⋱ | `\ddots` | Puntos diagonales |
| U+2212 | − | `-` | Menos Unicode → ASCII |
| U+0131 | ı | `\imath` | i sin punto |
| U+0237 | ȷ | `\jmath` | j sin punto |
| U+2206 | ∆ | `\Delta` | Incremento |
| U+2A3F | ⨿ | `\amalg` | Amalgama |
| U+2013 | – | `--` | En-dash |
| U+2014 | — | `---` | Em-dash |
| U+2030 | ‰ | `\permil` | Por mil |
| U+00B4 | ´ | `'` | Acento agudo suelto |

---

## Diacríticos (Patrones de Conversión)

Estos no son mapeos directos sino patrones que el conversor detecta:

| Patrón de entrada | LaTeX resultante | Descripción |
|-------------------|------------------|-------------|
| `_β_<sup>ˆ</sup>` | `\hat{\beta}` | Estimador (pymupdf) |
| `βˆ` | `\hat{\beta}` | Hat directo |
| `_x_ ˆ` | `\hat{x}` | Hat después de italic |
| `x˜` | `\tilde{x}` | Tilde |
| `x¯` | `\bar{x}` | Barra/macron |
| `xˇ` | `\check{x}` | Caron/háček |
| `<sup>T</sup>` | `^{T}` | Transpuesta |
| `||x||` | `\|x\|` | Norma |
| `<x,y>` | `\langle x,y \rangle` | Producto interno |

---

## Caracteres EXCLUIDOS (No se convierten)

Estos caracteres tienen significados ambiguos y se manejan por separado:

| Unicode | Char | Razón de exclusión |
|---------|------|-------------------|
| U+00F0 | ð | En Wooldridge = `(`. Ver `fix_wooldridge.py` |
| U+00DE | Þ | En Wooldridge = `)`. Ver `fix_wooldridge.py` |
| U+00FE | þ | En Wooldridge = `+`. Ver `fix_wooldridge.py` |
| U+00BC | ¼ | En Wooldridge = `=`. Ver `fix_wooldridge.py` |
| U+00A4 | ¤ | En Wooldridge = `ff`. Ver `fix_wooldridge.py` |

---

## Cómo Agregar Nuevos Símbolos

1. **Identificar** el código Unicode del símbolo
2. **Verificar** que no esté ya en el diccionario
3. **Editar** `C:\NEVEN\tools\unicode_to_latex.py`
4. **Agregar** al diccionario correspondiente:
   ```python
   # En la sección apropiada
   MATH_OPERATORS['⊛'] = r'\circledast'
   ```
5. **Actualizar** este documento de referencia
6. **Re-procesar** los archivos MD afectados

---

## Compatibilidad con KaTeX

Todos los comandos LaTeX en este diccionario son compatibles con KaTeX.
Para verificar compatibilidad de nuevos símbolos: https://katex.org/docs/supported.html

---

## Historial de Cambios

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2026-08-19 | v2.0 | Versión inicial con 100+ símbolos |
