# -*- coding: utf-8 -*-
"""
fix_dash.py - Fix specifically corrupted em dash characters in JSON files.

The em dash (—, U+2014) often gets corrupted to "â€"" when files are
read/written with incorrect encoding detection.

Usage:
  python fix_dash.py [path]
  
If no path provided, defaults to C:\NEVEN\functions\*.json

Created: 2026-08-19 during NEVEN Diccionario de Funciones implementation.
"""
import glob
import os
import sys


def main():
    # The corrupted pattern for em dash
    corrupted = '\u00e2\u20ac\u201d'  # â€"
    replacement = '\u2014'            # —
    
    # Determine path
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
    else:
        pattern = r'C:\NEVEN\functions\*.json'
    
    print(f'Scanning: {pattern}')
    print(f'Looking for: {repr(corrupted)} → {repr(replacement)}')
    
    fixed_count = 0
    for filepath in glob.glob(pattern):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if corrupted in content:
            content = content.replace(corrupted, replacement)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  Fixed: {os.path.basename(filepath)}')
            fixed_count += 1
    
    print(f'Total fixed: {fixed_count}')


if __name__ == '__main__':
    main()
