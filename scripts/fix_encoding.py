# -*- coding: utf-8 -*-
"""
fix_encoding.py - Fix corrupted UTF-8 encoding in JSON sidecar files.

Problem: When JSON files are saved multiple times with incorrect encoding
detection, UTF-8 characters can get double or triple encoded.

Examples of corruption:
  - "á" → "Ã¡" (double UTF-8)
  - "á" → "ÃƒÂ¡" (triple UTF-8)
  - "—" (em dash) → "â€"" (corrupted em dash)

Usage:
  python fix_encoding.py [path]
  
If no path provided, defaults to C:\NEVEN\functions\*.json

Created: 2026-08-19 during NEVEN Diccionario de Funciones implementation.
"""
import os
import glob
import sys

def fix_encoding(text):
    """Fix common UTF-8 encoding corruption patterns."""
    replacements = [
        # Em dash corruption patterns
        ('\u00e2\u20ac\u201c', '\u2014'),  # em dash
        ('\u00e2\u20ac\u201d', '\u2014'),  # em dash variant  
        ('\u00e2\u20ac\u2122', "'"),        # apostrophe
        
        # Triple UTF-8 (extremely corrupted)
        ('\u00c3\u0192\u00c2\u00a1', '\u00e1'),  # á
        ('\u00c3\u0192\u00c2\u00a9', '\u00e9'),  # é
        ('\u00c3\u0192\u00c2\u00ad', '\u00ed'),  # í
        ('\u00c3\u0192\u00c2\u00b3', '\u00f3'),  # ó
        ('\u00c3\u0192\u00c2\u00ba', '\u00fa'),  # ú
        ('\u00c3\u0192\u00c2\u00b1', '\u00f1'),  # ñ
        
        # Double UTF-8 - lowercase vowels with accents
        ('\u00c3\u00a1', '\u00e1'),  # á
        ('\u00c3\u00a9', '\u00e9'),  # é
        ('\u00c3\u00ad', '\u00ed'),  # í
        ('\u00c3\u00b3', '\u00f3'),  # ó
        ('\u00c3\u00ba', '\u00fa'),  # ú
        ('\u00c3\u00b1', '\u00f1'),  # ñ
        ('\u00c3\u00bc', '\u00fc'),  # ü
        
        # Double UTF-8 - uppercase vowels with accents
        ('\u00c3\u0081', '\u00c1'),  # Á
        ('\u00c3\u0089', '\u00c9'),  # É
        ('\u00c3\u008d', '\u00cd'),  # Í
        ('\u00c3\u0093', '\u00d3'),  # Ó
        ('\u00c3\u009a', '\u00da'),  # Ú
        ('\u00c3\u0091', '\u00d1'),  # Ñ
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def main():
    # Determine path
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
    else:
        pattern = r'C:\NEVEN\functions\*.json'
    
    print(f'Scanning: {pattern}')
    
    fixed_count = 0
    for filepath in glob.glob(pattern):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed = fix_encoding(content)
        
        if fixed != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f'  Fixed: {os.path.basename(filepath)}')
            fixed_count += 1
    
    print(f'Total fixed: {fixed_count}')


if __name__ == '__main__':
    main()
