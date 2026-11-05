#!/usr/bin/env python3
# Script para procesar los 4 libros Wiley y extraer entidades a la ontologia Excel.
# Ejecutar desde C:\NEVEN\startup para tener acceso a los modulos.
#
# Uso:
#     cd C:\NEVEN\startup
#     python F:\ANTIGRAVITY\2026\NEVEN\scripts\process_wiley_ontology.py

import os
import sys

# Agregar path de startup al PYTHONPATH
sys.path.insert(0, r"C:\NEVEN\startup")

from ontology_manager import process_book_incremental, get_book_progress

WILEY_BOOKS = [
    (r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\VBAExcel-MNumericos.pdf", "VBA Métodos Numéricos"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\Wiley - Excel for scientists and engineers numerical methods.pdf", "Wiley Excel Scientists"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\Wiley - Credit Risk Modeling using Excel and VBA.pdf", "Wiley Credit Risk"),
    (r"F:\ANTIGRAVITY\2026\NEVEN\ontologia-fuentes\LIBROS EXCEL\Wiley - Advanced Modelling in Finance using Excel and VBA.pdf", "Wiley Advanced Finance"),
]

DOMAIN = "excel"
BATCH_SIZE = 10  # Páginas por batch

def main():
    print("=" * 60)
    print("Procesamiento de Ontología - Libros Wiley Excel")
    print("=" * 60)
    print()
    
    for pdf_path, book_name in WILEY_BOOKS:
        print(f"\n{'='*60}")
        print(f"📖 Procesando: {book_name}")
        print(f"   Archivo: {pdf_path}")
        print("=" * 60)
        
        if not os.path.isfile(pdf_path):
            print(f"❌ ERROR: Archivo no encontrado: {pdf_path}")
            continue
        
        # Verificar progreso actual
        progress = get_book_progress(pdf_path, DOMAIN)
        print(f"   Estado actual: {progress.get('status', 'unknown')}")
        
        if progress.get("status") == "completed":
            print(f"✅ Ya procesado completamente")
            continue
        
        # Procesar
        try:
            result = process_book_incremental(
                file_path=pdf_path,
                domain_id=DOMAIN,
                config_manager=None,  # Usará config por defecto
                batch_size=BATCH_SIZE
            )
            print(f"   Resultado: {result}")
            
            if result.get("is_complete"):
                print(f"✅ Completado: {result.get('total_entities', '?')} entidades")
            else:
                pages_done = result.get("pages_processed", 0)
                total_pages = result.get("total_pages", "?")
                print(f"⏳ Progreso: {pages_done}/{total_pages} páginas")
                print(f"   Ejecutar de nuevo para continuar...")
                
        except Exception as e:
            print(f"❌ Error procesando {book_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Procesamiento finalizado")
    print("=" * 60)

if __name__ == "__main__":
    main()
