#!/usr/bin/env python3
"""
fix_wooldridge.py - Preprocesador específico para PDFs de Wooldridge
====================================================================

El PDF de Wooldridge (Introductory Econometrics) usa una fuente matemática
con encoding no estándar donde ciertos caracteres Latin Extended se mapean
a símbolos matemáticos básicos:

| Caracter | Unicode | Ocurrencias | Significado Real |
|:--------:|---------|------------:|------------------|
| ð        | U+00F0  | 7,105       | `(` paréntesis izquierdo |
| Þ        | U+00DE  | 7,118       | `)` paréntesis derecho |
| þ        | U+00FE  | 2,002       | `+` signo más |
| ¼        | U+00BC  | 4,317       | `=` signo igual |
| ¤        | U+00A4  | 2,104       | `ff` ligature |

Ejemplo de texto corrupto vs corregido:
  ANTES:  y ¼ b0 þ b1x1 þ b2x2, where Eðu j x1; x2Þ ¼ 0
  DESPUÉS: y = b0 + b1x1 + b2x2, where E(u | x1; x2) = 0

IMPORTANTE: Este script solo debe usarse para archivos extraídos del PDF
de Wooldridge. En otros PDFs, estos caracteres pueden tener significados
completamente diferentes (ð = eth islandés, ¼ = fracción 1/4).

Uso:
    python fix_wooldridge.py input.md output.md
    python fix_wooldridge.py --batch input_dir/ output_dir/
    
Pipeline completo:
    1. Extraer PDF: pymupdf4llm wooldridge.pdf > wooldridge_raw.md
    2. Corregir encoding: python fix_wooldridge.py wooldridge_raw.md wooldridge_fixed.md
    3. Convertir Unicode→LaTeX: python unicode_to_latex.py wooldridge_fixed.md wooldridge_final.md

Autor: NEVEN Project
Fecha: 2026-08-19
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Tuple


# =============================================================================
# MAPEOS ESPECÍFICOS DE WOOLDRIDGE
# =============================================================================

WOOLDRIDGE_ENCODING: Dict[str, str] = {
    # Paréntesis mal codificados
    'ð': '(',   # U+00F0 LATIN SMALL LETTER ETH → paréntesis izquierdo
    'Þ': ')',   # U+00DE LATIN CAPITAL LETTER THORN → paréntesis derecho
    
    # Operadores mal codificados
    'þ': '+',   # U+00FE LATIN SMALL LETTER THORN → signo más
    '¼': '=',   # U+00BC VULGAR FRACTION ONE QUARTER → signo igual
    
    # Ligature
    '¤': 'ff',  # U+00A4 CURRENCY SIGN → ligature ff
}

# Contextos donde ¼ probablemente ES una fracción real (no =)
# Patrones donde ¼ aparece como fracción legítima en otros libros
FRACTION_CONTEXTS = [
    r'\b1/4\b',          # ya convertido
    r'\bquarter\b',      # texto "quarter"
    r'\bfourth\b',       # "fourth"
    r'25\s*%',           # porcentaje 25%
]


def is_wooldridge_file(content: str) -> Tuple[bool, float]:
    """
    Detecta si un archivo probablemente es de Wooldridge basado en
    la frecuencia de caracteres de encoding corrupto.
    
    Returns:
        (is_wooldridge, confidence): Tupla con bool y confianza 0-1
    """
    # Contar ocurrencias de caracteres sospechosos
    counts = {char: content.count(char) for char in WOOLDRIDGE_ENCODING.keys()}
    total_suspicious = sum(counts.values())
    
    # Si hay muy pocos caracteres sospechosos, probablemente no es Wooldridge
    if total_suspicious < 50:
        return (False, 0.0)
    
    # Verificar patrones característicos de ecuaciones corruptas
    # Patrón: variable ¼ expresión (ecuación con "=")
    eq_pattern = re.compile(r'[a-zA-Z_]\s*¼\s*[a-zA-Z0-9β]')
    eq_matches = len(eq_pattern.findall(content))
    
    # Patrón: función(argumentos) con paréntesis corruptos
    func_pattern = re.compile(r'[a-zA-Z]+ð[^Þ]+Þ')
    func_matches = len(func_pattern.findall(content))
    
    # Calcular confianza
    confidence = 0.0
    
    # Alta frecuencia de caracteres → alta probabilidad
    if total_suspicious > 1000:
        confidence += 0.4
    elif total_suspicious > 500:
        confidence += 0.3
    elif total_suspicious > 100:
        confidence += 0.2
    
    # Patrones de ecuaciones → muy alta probabilidad
    if eq_matches > 50:
        confidence += 0.4
    elif eq_matches > 20:
        confidence += 0.3
    
    # Patrones de funciones → alta probabilidad
    if func_matches > 20:
        confidence += 0.2
    elif func_matches > 5:
        confidence += 0.1
    
    return (confidence >= 0.5, min(confidence, 1.0))


def fix_wooldridge_encoding(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Corrige el encoding específico de Wooldridge.
    
    Returns:
        (texto_corregido, estadísticas)
    """
    result = text
    stats = {char: 0 for char in WOOLDRIDGE_ENCODING.keys()}
    
    for char, replacement in WOOLDRIDGE_ENCODING.items():
        count = result.count(char)
        if count > 0:
            stats[char] = count
            result = result.replace(char, replacement)
    
    return result, stats


def fix_wooldridge_file(input_path: str, output_path: str, 
                        force: bool = False, 
                        detect: bool = True) -> Dict[str, any]:
    """
    Procesa un archivo aplicando correcciones de Wooldridge.
    
    Args:
        input_path: Ruta del archivo de entrada
        output_path: Ruta del archivo de salida
        force: Si True, aplica correcciones sin verificar si es Wooldridge
        detect: Si True, intenta detectar si el archivo es de Wooldridge
    
    Returns:
        Diccionario con estadísticas y metadata
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {
        'input': input_path,
        'output': output_path,
        'original_length': len(content),
        'is_wooldridge': None,
        'confidence': None,
        'stats': {},
        'total_fixes': 0,
    }
    
    # Detectar si es Wooldridge
    if detect and not force:
        is_wooldridge, confidence = is_wooldridge_file(content)
        result['is_wooldridge'] = is_wooldridge
        result['confidence'] = confidence
        
        if not is_wooldridge:
            print(f"ADVERTENCIA: {input_path} no parece ser de Wooldridge "
                  f"(confianza: {confidence:.1%})")
            if not force:
                print("  Use --force para aplicar correcciones de todas formas.")
                # Copiar sin cambios
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return result
    
    # Aplicar correcciones
    fixed_content, stats = fix_wooldridge_encoding(content)
    
    result['stats'] = stats
    result['total_fixes'] = sum(stats.values())
    result['final_length'] = len(fixed_content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    return result


def fix_wooldridge_batch(input_dir: str, output_dir: str,
                         force: bool = False) -> Dict[str, Dict]:
    """
    Procesa todos los archivos .md en un directorio.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for md_file in sorted(input_path.glob('*.md')):
        out_file = output_path / md_file.name
        print(f"Procesando: {md_file.name}...", end=' ', flush=True)
        
        try:
            result = fix_wooldridge_file(str(md_file), str(out_file), force=force)
            
            if result['total_fixes'] > 0:
                print(f"OK ({result['total_fixes']:,} correcciones)")
            else:
                print("OK (sin cambios)")
            
            results[md_file.name] = result
        except Exception as e:
            print(f"ERROR: {e}")
            results[md_file.name] = {'status': 'error', 'error': str(e)}
    
    return results


def print_stats(stats: Dict[str, int]) -> None:
    """Imprime estadísticas de corrección de forma legible."""
    print("\nEstadísticas de corrección:")
    print("-" * 40)
    
    char_names = {
        'ð': 'ð → ( (paréntesis izq)',
        'Þ': 'Þ → ) (paréntesis der)',
        'þ': 'þ → + (signo más)',
        '¼': '¼ → = (signo igual)',
        '¤': '¤ → ff (ligature)',
    }
    
    for char, count in sorted(stats.items(), key=lambda x: -x[1]):
        if count > 0:
            name = char_names.get(char, char)
            print(f"  {name}: {count:,}")
    
    total = sum(stats.values())
    print("-" * 40)
    print(f"  TOTAL: {total:,} correcciones")


def main():
    parser = argparse.ArgumentParser(
        description='Corrige encoding específico de PDFs de Wooldridge (NEVEN Project)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s wooldridge_raw.md wooldridge_fixed.md
  %(prog)s --batch raw_chapters/ fixed_chapters/
  %(prog)s --force --stats input.md output.md

Pipeline completo:
  1. pymupdf4llm wooldridge.pdf > raw.md
  2. python %(prog)s raw.md fixed.md
  3. python unicode_to_latex.py fixed.md final.md
"""
    )
    parser.add_argument('input', help='Archivo o directorio de entrada')
    parser.add_argument('output', help='Archivo o directorio de salida')
    parser.add_argument('--batch', action='store_true',
                       help='Procesar directorio completo')
    parser.add_argument('--force', action='store_true',
                       help='Aplicar correcciones sin verificar si es Wooldridge')
    parser.add_argument('--stats', action='store_true',
                       help='Mostrar estadísticas detalladas')
    parser.add_argument('--detect-only', action='store_true',
                       help='Solo detectar si es Wooldridge, sin modificar')
    
    args = parser.parse_args()
    
    if args.detect_only:
        # Modo detección
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
        
        is_wooldridge, confidence = is_wooldridge_file(content)
        
        print(f"Archivo: {args.input}")
        print(f"¿Es Wooldridge?: {'Sí' if is_wooldridge else 'No'}")
        print(f"Confianza: {confidence:.1%}")
        
        if args.stats:
            counts = {char: content.count(char) for char in WOOLDRIDGE_ENCODING.keys()}
            print_stats(counts)
        
        sys.exit(0 if is_wooldridge else 1)
    
    if args.batch:
        results = fix_wooldridge_batch(args.input, args.output, force=args.force)
        
        # Resumen
        total_fixes = sum(r.get('total_fixes', 0) for r in results.values())
        processed = len([r for r in results.values() if r.get('total_fixes', 0) > 0])
        
        print(f"\n{'='*60}")
        print(f"Completado: {len(results)} archivos")
        print(f"Con correcciones: {processed} archivos")
        print(f"Total de correcciones: {total_fixes:,}")
        
        if args.stats:
            # Agregar estadísticas de todos los archivos
            total_stats = {}
            for r in results.values():
                for char, count in r.get('stats', {}).items():
                    total_stats[char] = total_stats.get(char, 0) + count
            print_stats(total_stats)
    else:
        result = fix_wooldridge_file(args.input, args.output, force=args.force)
        
        if result['total_fixes'] > 0:
            print(f"Corrección completada: {args.output}")
            print(f"Total de correcciones: {result['total_fixes']:,}")
            
            if args.stats:
                print_stats(result['stats'])
        else:
            print(f"Sin cambios necesarios: {args.output}")


if __name__ == '__main__':
    main()
