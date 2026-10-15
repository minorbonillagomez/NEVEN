#!/usr/bin/env python3
"""
NEVEN Unicode-to-LaTeX Post-Processor v2.0
==========================================
Convierte símbolos matemáticos Unicode extraídos de PDFs a formato LaTeX
para renderizado con KaTeX en el sistema RAG.

Características:
- Letras griegas (α→\alpha, β→\beta, etc.)
- Operadores (∑→\sum, ∫→\int, ∂→\partial)
- Superíndices HTML (<sup>2</sup> → ^{2})
- Subíndices HTML (<sub>i</sub> → _{i})
- Estimadores/hats (_β_<sup>ˆ</sup> → \hat{\beta})
- Fracciones (_n_<sup><u>1</u></sup> → \frac{1}{n})
- Transpuestas (X<sup>T</sup> → X^T)
- Protección de productos internos (<x,y> → \langle x,y \rangle)
- Normas (||x|| → \|x\|)

Autor: NEVEN Project
Fecha: 2026-08-19
"""

import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

# =============================================================================
# MAPEOS UNICODE → LATEX
# =============================================================================

# Letras griegas minúsculas
GREEK_LOWER: Dict[str, str] = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\varepsilon', 'ϵ': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta',
    'θ': r'\theta', 'ϑ': r'\vartheta', 'ι': r'\iota', 'κ': r'\kappa',
    'λ': r'\lambda', 'μ': r'\mu', 'µ': r'\mu', 'ν': r'\nu',
    'ξ': r'\xi', 'π': r'\pi', 'ρ': r'\rho', 'ϱ': r'\varrho',
    'σ': r'\sigma', 'ς': r'\varsigma', 'τ': r'\tau', 'υ': r'\upsilon',
    'φ': r'\varphi', 'ϕ': r'\phi', 'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
}

# Letras griegas mayúsculas
GREEK_UPPER: Dict[str, str] = {
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Υ': r'\Upsilon',
    'Φ': r'\Phi', 'Ψ': r'\Psi', 'Ω': r'\Omega',
}

# Operadores matemáticos
MATH_OPERATORS: Dict[str, str] = {
    '∑': r'\sum', '∏': r'\prod', '∫': r'\int', '∬': r'\iint',
    '∭': r'\iiint', '∮': r'\oint', '∂': r'\partial', '∇': r'\nabla',
    '√': r'\sqrt', '∛': r'\sqrt[3]', '∜': r'\sqrt[4]',
    '∞': r'\infty', '±': r'\pm', '∓': r'\mp', '×': r'\times',
    '÷': r'\div', '·': r'\cdot', '∗': r'*', '∘': r'\circ',
    '⊗': r'\otimes', '⊕': r'\oplus', '⊖': r'\ominus', '⊙': r'\odot',
}

# Relaciones
MATH_RELATIONS: Dict[str, str] = {
    '≤': r'\leq', '≥': r'\geq', '≠': r'\neq', '≈': r'\approx',
    '≅': r'\cong', '≡': r'\equiv', '∼': r'\sim', '≃': r'\simeq',
    '∝': r'\propto', '≪': r'\ll', '≫': r'\gg',
    '⊂': r'\subset', '⊃': r'\supset', '⊆': r'\subseteq', '⊇': r'\supseteq',
    '∈': r'\in', '∉': r'\notin', '∋': r'\ni',
    '∪': r'\cup', '∩': r'\cap', '⊥': r'\perp', '∥': r'\parallel', '∠': r'\angle',
    # Variantes slanted (usadas en algunos PDFs)
    '⩽': r'\leqslant', '⩾': r'\geqslant',
    # Aproximaciones
    '≲': r'\lesssim', '≳': r'\gtrsim',
}

# Flechas
ARROWS: Dict[str, str] = {
    '→': r'\to', '←': r'\leftarrow', '↔': r'\leftrightarrow',
    '⇒': r'\Rightarrow', '⇐': r'\Leftarrow', '⇔': r'\Leftrightarrow',
    '↑': r'\uparrow', '↓': r'\downarrow', '↗': r'\nearrow',
    '↘': r'\searrow', '↦': r'\mapsto',
}

# Cuantificadores y lógica
LOGIC: Dict[str, str] = {
    '∀': r'\forall', '∃': r'\exists', '∄': r'\nexists',
    '¬': r'\neg', '∧': r'\land', '∨': r'\lor',
    '⊤': r'\top', '⊥': r'\bot', '⊢': r'\vdash', '⊨': r'\models',
}

# Símbolos especiales
SPECIAL: Dict[str, str] = {
    '′': "'", '″': "''", '‴': "'''",
    '°': r'^\circ', '∅': r'\emptyset',
    'ℕ': r'\mathbb{N}', 'ℤ': r'\mathbb{Z}', 'ℚ': r'\mathbb{Q}',
    'ℝ': r'\mathbb{R}', 'ℂ': r'\mathbb{C}',
    'ℑ': r'\Im', 'ℜ': r'\Re', 'ℓ': r'\ell', 'ℏ': r'\hbar',
    '†': r'\dagger', '‡': r'\ddagger',
    '…': r'\ldots', '⋯': r'\cdots', '⋮': r'\vdots', '⋱': r'\ddots',
    '−': '-',  # Unicode minus to ASCII minus
    # Letras especiales para math
    'ı': r'\imath',  # i sin punto (para vectores)
    'ȷ': r'\jmath',  # j sin punto
    # Delta incremental (diferente de Δ griego)
    '∆': r'\Delta',  # U+2206 INCREMENT
    # Coproducto/amalgama
    '⨿': r'\amalg',
    # Dashes
    '–': '--',  # en-dash
    '—': '---',  # em-dash
    # Per mille
    '‰': r'\permil',
    # Acute accent suelto
    '´': "'",
    # NOTA: ð/Þ/þ (eth/thorn) NO se convierten aquí porque:
    # - En Wooldridge representan paréntesis/+ (pre-procesados por fix_wooldridge.py)
    # - En otros PDFs, si aparecen como LaTeX real, se dejan como están
}

# Brackets Unicode
BRACKETS: Dict[str, str] = {
    '⟨': r'\langle', '⟩': r'\rangle',
    '⌈': r'\lceil', '⌉': r'\rceil',
    '⌊': r'\lfloor', '⌋': r'\rfloor',
    '‖': r'\|',
    '⟦': r'\llbracket', '⟧': r'\rrbracket',
}

# Superíndices Unicode
SUPERSCRIPTS: Dict[str, str] = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
    '⁺': '+', '⁻': '-', '⁼': '=', '⁽': '(', '⁾': ')',
    'ⁿ': 'n', 'ⁱ': 'i',
}

# Subíndices Unicode
SUBSCRIPTS: Dict[str, str] = {
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
    '₊': '+', '₋': '-', '₌': '=', '₍': '(', '₎': ')',
    'ₐ': 'a', 'ₑ': 'e', 'ₒ': 'o', 'ₓ': 'x', 'ₕ': 'h',
    'ₖ': 'k', 'ₗ': 'l', 'ₘ': 'm', 'ₙ': 'n', 'ₚ': 'p',
    'ₛ': 's', 'ₜ': 't',
}

# Fracciones Unicode
# NOTA: ¼ se omite porque en Wooldridge significa = (pre-procesado por fix_wooldridge.py)
# y en otros PDFs es muy raro que sea una fracción real extraída correctamente
FRACTIONS: Dict[str, str] = {
    '½': r'\frac{1}{2}', '⅓': r'\frac{1}{3}', '⅔': r'\frac{2}{3}',
    '¾': r'\frac{3}{4}',
    '⅕': r'\frac{1}{5}', '⅖': r'\frac{2}{5}', '⅗': r'\frac{3}{5}', '⅘': r'\frac{4}{5}',
    '⅙': r'\frac{1}{6}', '⅚': r'\frac{5}{6}',
    '⅛': r'\frac{1}{8}', '⅜': r'\frac{3}{8}', '⅝': r'\frac{5}{8}', '⅞': r'\frac{7}{8}',
}

# Combinar todos los mapeos simples
ALL_SYMBOLS: Dict[str, str] = {
    **GREEK_LOWER, **GREEK_UPPER, **MATH_OPERATORS, **MATH_RELATIONS,
    **ARROWS, **LOGIC, **SPECIAL, **BRACKETS, **FRACTIONS,
}


# =============================================================================
# CLASE PRINCIPAL DEL CONVERTIDOR
# =============================================================================

class UnicodeToLatexConverter:
    """Convierte texto con símbolos Unicode matemáticos a LaTeX."""
    
    def __init__(self, wrap_math: bool = False, inline_delim: str = '$'):
        self.wrap_math = wrap_math
        self.inline_delim = inline_delim
        self.stats = {
            'symbols_converted': 0,
            'superscripts_converted': 0,
            'subscripts_converted': 0,
            'fractions_detected': 0,
            'hats_converted': 0,
            'transposes_converted': 0,
            'inner_products_converted': 0,
            'norms_converted': 0,
        }
    
    def protect_inner_products(self, text: str) -> str:
        """
        Protege productos internos <x,y> convirtiéndolos a formato LaTeX limpio.
        Debe ejecutarse ANTES de otras conversiones para evitar confusión con HTML.
        
        NOTA: Usamos ⟨ y ⟩ (Unicode math brackets) que luego se convierten
        a $\langle$ y $\rangle$ en convert_simple_symbols si están en modo math.
        Para texto plano en RAG, simplemente dejamos < > porque el contenido
        ya está contextualizado.
        """
        result = text
        
        # Patrón: <letra(s),letra(s)> que NO es HTML
        # Excluir si empieza con < seguido de / o letras HTML conocidas
        def is_math_bracket(content: str) -> bool:
            """Determina si el contenido dentro de <> es matemático."""
            html_tags = ['sup', 'sub', 'br', 'p', 'div', 'span', 'table', 'tr', 'td', 
                        'th', 'img', 'a', 'strong', 'em', 'code', 'pre', 'h1', 'h2', 
                        'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'u']
            content_lower = content.lower().strip()
            
            # Si es un tag HTML
            if any(content_lower.startswith(tag) for tag in html_tags):
                return False
            if content_lower.startswith('/'):
                return False
            if content_lower.startswith('!'):
                return False
            
            # Si contiene coma, probablemente es producto interno
            if ',' in content:
                return True
            
            # Si contiene |, probablemente es bra-ket
            if '|' in content:
                return True
            
            return False
        
        # Buscar <...> que parecen matemáticos
        # NOTA: Dejamos como < > sin escape para texto plano en RAG
        def replace_math_bracket(m):
            content = m.group(1)
            if is_math_bracket(content):
                self.stats['inner_products_converted'] += 1
                # Usar < > ASCII - serán interpretados por KaTeX si están en modo math
                return f'<{content}>'
            return m.group(0)  # Dejar como está si es HTML
        
        result = re.sub(r'<([^>]+)>', replace_math_bracket, result)
        
        # Manejar brackets Unicode ⟨⟩ - convertir a < > para consistencia
        def replace_unicode_angle(m):
            content = m.group(1)
            self.stats['inner_products_converted'] += 1
            return f'<{content}>'
        
        result = re.sub(r'⟨([^⟩]+)⟩', replace_unicode_angle, result)
        
        return result
    
    def convert_norms(self, text: str) -> str:
        """Convierte normas ||x|| a \|x\| y |x| a |x| (valor absoluto)."""
        result = text
        
        # Doble barra ||x|| → \|x\|
        def replace_norm(m):
            content = m.group(1)
            self.stats['norms_converted'] += 1
            return rf'\|{content}\|'
        
        # Patrón para ||...|| evitando tablas markdown
        result = re.sub(r'\|\|([^|]+)\|\|', replace_norm, result)
        
        # Unicode ‖x‖
        result = re.sub(r'‖([^‖]+)‖', replace_norm, result)
        
        return result
    
    def convert_fractions(self, text: str) -> str:
        """Detecta y convierte patrones de fracciones."""
        result = text
        
        # Patrón común de pymupdf: _n_<sup><u>1</u></sup> → \frac{1}{n}
        def replace_frac_pattern(m):
            denom = m.group(1)
            numer = m.group(2)
            self.stats['fractions_detected'] += 1
            return rf'\frac{{{numer}}}{{{denom}}}'
        
        result = re.sub(
            r'_([a-zA-Z0-9]+)_<sup><u>([^<]+)</u></sup>',
            replace_frac_pattern,
            result
        )
        
        # Fracciones Unicode
        for uni, latex in FRACTIONS.items():
            if uni in result:
                self.stats['fractions_detected'] += result.count(uni)
                result = result.replace(uni, latex)
        
        return result
    
    def convert_hats_and_diacritics(self, text: str) -> str:
        """Convierte estimadores y diacríticos a LaTeX."""
        result = text
        
        # Patrón principal de pymupdf: _letra_<sup>ˆ</sup> → \hat{letra}
        def replace_hat_pattern(m):
            letter = m.group(1)
            self.stats['hats_converted'] += 1
            latex_letter = ALL_SYMBOLS.get(letter, letter)
            return rf'\hat{{{latex_letter}}}'
        
        # _β_<sup>ˆ</sup> → \hat{\beta}
        result = re.sub(r'_([α-ωΑ-Ωa-zA-Z])_<sup>ˆ</sup>', replace_hat_pattern, result)
        
        # letra<sup>ˆ</sup> (sin underscores) - con variantes
        result = re.sub(r'([α-ωΑ-Ωa-zA-Z])_?<sup>ˆ</sup>', replace_hat_pattern, result)
        
        # _letra_ ˆ (espacio entre markdown italic y caret) → \hat{letra}
        result = re.sub(r'_([α-ωΑ-Ωa-zA-Z])_\s*ˆ', replace_hat_pattern, result)
        
        # Letras griegas con ˆ directo: βˆ → \hat{\beta}
        def replace_greek_hat(m):
            letter = m.group(1)
            self.stats['hats_converted'] += 1
            latex_letter = ALL_SYMBOLS.get(letter, letter)
            return rf'\hat{{{latex_letter}}}'
        
        result = re.sub(r'([α-ωΑ-Ω])ˆ', replace_greek_hat, result)
        
        # Letras ASCII con ˆ: xˆ, yˆ
        result = re.sub(r'([a-zA-Z])ˆ', replace_greek_hat, result)
        
        # _letra_ ˜ (tilde después de markdown italic)
        result = re.sub(r'_([α-ωΑ-Ωa-zA-Z])_\s*˜', lambda m: rf'\tilde{{{m.group(1)}}}', result)
        
        # Tildes: x̃ → \tilde{x} (varios formatos)
        result = re.sub(r'([a-zA-Zα-ω])˜', lambda m: rf'\tilde{{{m.group(1)}}}', result)
        result = re.sub(r'([a-zA-Zα-ω])\u02DC', lambda m: rf'\tilde{{{m.group(1)}}}', result)  # small tilde
        
        # _letra_ ¯ (macron después de markdown italic)
        result = re.sub(r'_([α-ωΑ-Ωa-zA-Z])_\s*¯', lambda m: rf'\bar{{{m.group(1)}}}', result)
        
        # Barras: x̄ → \bar{x}
        result = re.sub(r'([a-zA-Zα-ω])¯', lambda m: rf'\bar{{{m.group(1)}}}', result)
        result = re.sub(r'([a-zA-Zα-ω])\u00AF', lambda m: rf'\bar{{{m.group(1)}}}', result)  # macron
        
        # Check: ˇ → \check{} (caron/háček)
        result = re.sub(r'([a-zA-Zα-ω])ˇ', lambda m: rf'\check{{{m.group(1)}}}', result)
        # También el combining caron U+030C
        result = re.sub(r'([a-zA-Z])\u030C', r'\\check{\1}', result)
        
        # Caret suelto ˆ (U+02C6) después de cualquier caracter alfanumérico
        result = re.sub(r'(\w)\u02C6', lambda m: rf'\hat{{{m.group(1)}}}', result)
        
        # Combining diacritical marks
        result = re.sub(r'([a-zA-Z])\u0302', r'\\hat{\1}', result)  # circumflex
        result = re.sub(r'([a-zA-Z])\u0303', r'\\tilde{\1}', result)  # tilde
        result = re.sub(r'([a-zA-Z])\u0304', r'\\bar{\1}', result)  # macron
        result = re.sub(r'([a-zA-Z])\u0307', r'\\dot{\1}', result)  # dot
        result = re.sub(r'([a-zA-Z])\u0308', r'\\ddot{\1}', result)  # diaeresis
        
        return result
    
    def convert_transposes(self, text: str) -> str:
        """Convierte transpuestas X^T, X', X⊤."""
        result = text
        
        # <sup>T</sup> o <sup>_T_</sup>
        def replace_transpose(m):
            self.stats['transposes_converted'] += 1
            return "^{T}"
        
        result = re.sub(r'<sup>_?T_?</sup>', replace_transpose, result)
        result = re.sub(r'<sup>_?′_?</sup>', lambda m: "^{\\prime}", result)
        
        # Unicode transpose ⊤
        result = result.replace('⊤', '^{T}')
        
        return result
    
    def convert_superscripts(self, text: str) -> str:
        """Convierte superíndices a notación LaTeX ^{}."""
        result = text
        
        # Superíndices Unicode
        for uni, val in SUPERSCRIPTS.items():
            if uni in result:
                self.stats['superscripts_converted'] += result.count(uni)
                result = result.replace(uni, f'^{{{val}}}')
        
        # HTML <sup>...</sup>
        def replace_sup(m):
            content = m.group(1)
            self.stats['superscripts_converted'] += 1
            # Limpiar contenido
            content = content.replace('<u>', '').replace('</u>', '')
            content = content.strip('_')
            # No convertir si es hat (ya manejado)
            if content == 'ˆ':
                return m.group(0)
            return f'^{{{content}}}'
        
        result = re.sub(r'<sup>([^<]+)</sup>', replace_sup, result)
        
        return result
    
    def convert_subscripts(self, text: str) -> str:
        """Convierte subíndices a notación LaTeX _{}."""
        result = text
        
        # Subíndices Unicode
        for uni, val in SUBSCRIPTS.items():
            if uni in result:
                self.stats['subscripts_converted'] += result.count(uni)
                result = result.replace(uni, f'_{{{val}}}')
        
        # HTML <sub>...</sub>
        def replace_sub(m):
            content = m.group(1)
            self.stats['subscripts_converted'] += 1
            return f'_{{{content}}}'
        
        result = re.sub(r'<sub>([^<]+)</sub>', replace_sub, result)
        
        return result
    
    def convert_simple_symbols(self, text: str) -> str:
        """Convierte símbolos Unicode simples a LaTeX."""
        result = text
        
        for uni, latex in ALL_SYMBOLS.items():
            if uni in result:
                count = result.count(uni)
                self.stats['symbols_converted'] += count
                result = result.replace(uni, latex)
        
        return result
    
    def convert_sqrt_patterns(self, text: str) -> str:
        """Convierte patrones de raíz cuadrada."""
        result = text
        
        # Patrón ~~√~~ que aparece en algunos PDFs
        result = re.sub(r'~~√~~', r'\\sqrt', result)
        result = re.sub(r'~~\\sqrt~~', r'\\sqrt', result)
        
        return result
    
    def normalize_quotes(self, text: str) -> str:
        """Normaliza comillas tipográficas a comillas ASCII."""
        result = text
        # Comillas simples tipográficas → '
        result = result.replace('\u2018', "'")  # LEFT SINGLE QUOTATION MARK
        result = result.replace('\u2019', "'")  # RIGHT SINGLE QUOTATION MARK
        # Comillas dobles tipográficas → "
        result = result.replace('\u201C', '"')  # LEFT DOUBLE QUOTATION MARK
        result = result.replace('\u201D', '"')  # RIGHT DOUBLE QUOTATION MARK
        return result
    
    def clean_artifacts(self, text: str) -> str:
        """Limpia artefactos de extracción de PDF."""
        result = text
        
        # ═══════════════════════════════════════════════════════════════════════
        # ARTEFACTOS DE pymupdf4llm (CRÍTICO - limpiar primero)
        # ═══════════════════════════════════════════════════════════════════════
        
        # Eliminar <br>, <br/>, <br /> (line breaks HTML literales)
        result = re.sub(r'<br\s*/?>', ' ', result)
        
        # Convertir \langle y \rangle literales a < y > 
        # (si queremos LaTeX real, los convertimos arriba; aquí vienen literales de pymupdf)
        result = result.replace('\\langle', '<')
        result = result.replace('\\rangle', '>')
        
        # Limpiar pipes dobles || que son artefactos de tablas markdown rotas
        # pero NO dentro de contexto matemático (normas ya procesadas)
        result = re.sub(r'\|\s*\|(?!\s*[a-zA-Z0-9])', ' ', result)  # || seguido de espacios
        
        # Backticks sueltos de código inline roto
        result = re.sub(r'`{2,}', '`', result)  # Múltiples backticks a uno
        result = re.sub(r'`\s+`', ' ', result)  # ` ` espacio entre backticks
        
        # Guiones bajos repetidos (separadores de tabla)
        result = re.sub(r'_{3,}', '', result)
        
        # Puntos suspensivos repetidos (artefactos de gráficos)
        result = re.sub(r'\.{4,}', '...', result)
        
        # ═══════════════════════════════════════════════════════════════════════
        # LIMPIEZA GENERAL
        # ═══════════════════════════════════════════════════════════════════════
        
        # Múltiples espacios
        result = re.sub(r' {2,}', ' ', result)
        
        # Múltiples newlines (más de 2)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Underscores markdown sueltos alrededor de símbolos LaTeX
        # _\beta_ → \beta
        result = re.sub(r'_\\([a-zA-Z]+)_', r'\\\1', result)
        
        # ~~...~~ strikethrough mal interpretado
        result = re.sub(r'~~([^~]+)~~', r'\1', result)
        
        return result
    
    def convert(self, text: str) -> str:
        """
        Pipeline completo de conversión.
        
        Orden de operaciones (importante):
        1. Proteger productos internos <x,y> antes de que se confundan con HTML
        2. Convertir normas ||x||
        3. Convertir fracciones (usan <sup><u>)
        4. Convertir transpuestas (usan <sup>T)
        5. Convertir hats/estimadores (usan <sup>ˆ)
        6. Convertir superíndices restantes
        7. Convertir subíndices
        8. Convertir raíces cuadradas
        9. Convertir símbolos simples (letras griegas, operadores)
        10. Limpiar artefactos
        """
        result = text
        
        # 1. Proteger productos internos
        result = self.protect_inner_products(result)
        
        # 2. Normas
        result = self.convert_norms(result)
        
        # 3. Fracciones
        result = self.convert_fractions(result)
        
        # 4. Transpuestas
        result = self.convert_transposes(result)
        
        # 5. Hats/diacríticos
        result = self.convert_hats_and_diacritics(result)
        
        # 6-7. Super/subíndices
        result = self.convert_superscripts(result)
        result = self.convert_subscripts(result)
        
        # 8. Raíces
        result = self.convert_sqrt_patterns(result)
        
        # 9. Símbolos simples
        result = self.convert_simple_symbols(result)
        
        # 10. Normalizar comillas tipográficas
        result = self.normalize_quotes(result)
        
        # 11. Limpieza
        result = self.clean_artifacts(result)
        
        return result
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de conversión."""
        return self.stats.copy()


# =============================================================================
# FUNCIONES DE ARCHIVO
# =============================================================================

def convert_file(input_path: str, output_path: str, wrap_math: bool = False) -> Dict[str, int]:
    """Convierte un archivo MD de Unicode a LaTeX."""
    converter = UnicodeToLatexConverter(wrap_math=wrap_math)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    converted = converter.convert(content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(converted)
    
    return converter.get_stats()


def convert_batch(input_dir: str, output_dir: str, wrap_math: bool = False) -> Dict[str, Dict]:
    """Convierte todos los archivos .md en un directorio."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for md_file in sorted(input_path.glob('*.md')):
        out_file = output_path / md_file.name
        print(f"Procesando: {md_file.name}...", end=' ', flush=True)
        
        try:
            stats = convert_file(str(md_file), str(out_file), wrap_math)
            total = sum(stats.values())
            print(f"OK ({total} conversiones)")
            results[md_file.name] = {'status': 'success', 'stats': stats}
        except Exception as e:
            print(f"ERROR: {e}")
            results[md_file.name] = {'status': 'error', 'error': str(e)}
    
    return results


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Convierte símbolos Unicode matemáticos a LaTeX (NEVEN Project)'
    )
    parser.add_argument('input', help='Archivo o directorio de entrada')
    parser.add_argument('output', help='Archivo o directorio de salida')
    parser.add_argument('--batch', action='store_true', 
                       help='Procesar directorio completo')
    parser.add_argument('--wrap', action='store_true',
                       help='Envolver expresiones en delimitadores $')
    parser.add_argument('--stats', action='store_true',
                       help='Mostrar estadísticas detalladas')
    
    args = parser.parse_args()
    
    if args.batch:
        results = convert_batch(args.input, args.output, args.wrap)
        
        # Resumen
        success = sum(1 for r in results.values() if r['status'] == 'success')
        print(f"\n{'='*60}")
        print(f"Completado: {success}/{len(results)} archivos")
        
        if args.stats:
            total_stats = {}
            for name, r in results.items():
                if r['status'] == 'success':
                    for k, v in r['stats'].items():
                        total_stats[k] = total_stats.get(k, 0) + v
            print("\nEstadísticas totales:")
            for k, v in sorted(total_stats.items()):
                print(f"  {k}: {v:,}")
    else:
        stats = convert_file(args.input, args.output, args.wrap)
        print(f"Conversión completada: {args.output}")
        
        if args.stats:
            print("\nEstadísticas:")
            for k, v in sorted(stats.items()):
                print(f"  {k}: {v:,}")


if __name__ == '__main__':
    main()
