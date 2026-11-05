#!/usr/bin/env python3
"""
NEVEN Full Pipeline: Convertir todos los MDs de econometría a LaTeX
===================================================================
Este script aplica el pipeline completo:
1. Para Wooldridge: fix_wooldridge.py primero, luego unicode_to_latex.py
2. Para otros: solo unicode_to_latex.py

Uso:
    python convert_all_md.py

Autor: NEVEN Project
Fecha: 2026-08-19
"""

import os
import shutil
from pathlib import Path

# Importar los convertidores
import sys
sys.path.insert(0, str(Path(__file__).parent))

from fix_wooldridge import fix_wooldridge_encoding
from unicode_to_latex import UnicodeToLatexConverter


def process_all():
    """Procesa todos los archivos MD aplicando el pipeline correcto."""
    
    input_dir = Path(r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS ECONOMETRIA\markdown")
    output_dir = Path(r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS ECONOMETRIA\markdown_latex")
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Identificar archivo de Wooldridge
    wooldridge_file = "wooldridge_j-_2002_econometric_analysis_of_cross_section_and_panel_data.md"
    
    total_stats = {
        'symbols_converted': 0,
        'superscripts_converted': 0,
        'subscripts_converted': 0,
        'fractions_detected': 0,
        'hats_converted': 0,
        'transposes_converted': 0,
        'inner_products_converted': 0,
        'norms_converted': 0,
        'wooldridge_fixes': 0,
    }
    
    for md_file in sorted(input_dir.glob("*.md")):
        print(f"Procesando: {md_file.name}...", end=" ", flush=True)
        
        # Leer contenido original
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Si es Wooldridge, aplicar fix primero
        if md_file.name == wooldridge_file:
            content, w_stats = fix_wooldridge_encoding(content)
            total_stats['wooldridge_fixes'] = sum(w_stats.values())
            print(f"(Wooldridge fix: {total_stats['wooldridge_fixes']:,}) ", end="")
        
        # Aplicar conversión Unicode → LaTeX
        converter = UnicodeToLatexConverter()
        converted = converter.convert(content)
        stats = converter.get_stats()
        
        # Acumular estadísticas
        for k, v in stats.items():
            total_stats[k] = total_stats.get(k, 0) + v
        
        # Guardar
        out_file = output_dir / md_file.name
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(converted)
        
        total = sum(stats.values())
        print(f"OK ({total:,} conversiones)")
    
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS TOTALES:")
    print("=" * 60)
    for k, v in sorted(total_stats.items()):
        if v > 0:
            print(f"  {k}: {v:,}")
    
    grand_total = sum(total_stats.values())
    print(f"\nTOTAL CONVERSIONES: {grand_total:,}")


if __name__ == '__main__':
    process_all()
