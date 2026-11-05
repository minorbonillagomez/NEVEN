#!/usr/bin/env python3
"""
add_book.py — Script para agregar un libro completo a NEVEN
══════════════════════════════════════════════════════════════════════════════

Este script automatiza el proceso completo de agregar un libro al sistema
de conocimiento de NEVEN:

1. Indexa el documento al RAG (ChromaDB) para búsqueda vectorial
2. Opcionalmente procesa entidades para la ontología (requiere tokens LLM)
3. Crea checkpoint para que la UI muestre páginas y estado

Uso:
    python add_book.py <path_to_pdf> <domain> [--ontology] [--max-pages N]

Argumentos:
    path_to_pdf     Ruta absoluta al archivo PDF
    domain          Dominio: econometria, excel, estadistica, algebra_lineal
    --ontology      Procesar también entidades (usa tokens LLM)
    --max-pages N   Limitar páginas para ontología (default: 100)

Ejemplos:
    # Solo RAG (rápido, no usa LLM)
    python add_book.py "F:\\libros\\MiLibro.pdf" econometria

    # RAG + Ontología (lento, usa tokens LLM)
    python add_book.py "F:\\libros\\MiLibro.pdf" econometria --ontology

    # RAG + Ontología limitada a 50 páginas
    python add_book.py "F:\\libros\\MiLibro.pdf" econometria --ontology --max-pages 50

Autor: NEVEN Team (Minor Bonilla Gómez)
Versión: 1.0 (2026-08-19)
"""
import sys
import os
import json
import hashlib
import argparse
from datetime import datetime

# Intentar importar requests, si no está disponible dar instrucciones
try:
    import requests
except ImportError:
    print("❌ El módulo 'requests' no está instalado.")
    print("   Ejecuta: pip install requests")
    sys.exit(1)

# Intentar importar PyPDF2 para contar páginas
try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("⚠️  PyPDF2 no instalado. No se podrá contar páginas automáticamente.")
    print("   Ejecuta: pip install PyPDF2")


BASE_URL = "http://localhost:5555"
CHECKPOINT_DIR = r"C:\NEVEN\docs\ontologia\checkpoints"


def get_page_count(pdf_path: str) -> int:
    """Obtiene el número de páginas de un PDF."""
    if not PYPDF2_AVAILABLE:
        return 0
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        print(f"⚠️  No se pudo leer páginas: {e}")
        return 0


def check_server_available() -> bool:
    """Verifica que el servidor HTTP esté corriendo."""
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return resp.status_code == 200
    except:
        return False


def index_to_rag(pdf_path: str, domain: str) -> dict:
    """Indexa el documento al RAG."""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/rag/upload",
            json={"file_path": pdf_path, "domain": domain},
            timeout=600  # 10 minutos para libros grandes
        )
        return resp.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Timeout - el libro es muy grande"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def process_ontology(pdf_path: str, domain: str, max_pages: int) -> dict:
    """Procesa el documento para extraer entidades a la ontología."""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/ontology/process",
            json={
                "file_path": pdf_path,
                "domain": domain,
                "max_pages": max_pages
            },
            timeout=3600  # 1 hora para procesamiento LLM
        )
        return resp.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "Timeout - procesamiento muy largo"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def create_checkpoint(
    pdf_path: str,
    domain: str,
    total_pages: int,
    entities_created: int = 0,
    relations_created: int = 0
) -> str:
    """Crea un archivo checkpoint para la UI."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    # Calcular hash del archivo
    with open(pdf_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()[:12]
    
    # Nombre del checkpoint
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    checkpoint_filename = f"{book_name}_{domain}_{file_hash}.json"
    checkpoint_path = os.path.join(CHECKPOINT_DIR, checkpoint_filename)
    
    # Datos del checkpoint
    checkpoint_data = {
        "file_path": pdf_path,
        "book_name": book_name,
        "domain": domain,
        "total_pages": total_pages,
        "processed_pages": total_pages,
        "status": "completed",
        "entities_created": entities_created,
        "relations_created": relations_created,
        "created_at": datetime.now().isoformat(),
        "source": "add_book.py"
    }
    
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
    
    return checkpoint_path


def check_already_indexed(pdf_path: str, domain: str) -> bool:
    """Verifica si el libro ya está indexado en RAG."""
    try:
        resp = requests.get(f"{BASE_URL}/api/rag/list", timeout=10)
        if resp.status_code != 200:
            return False
        
        data = resp.json()
        docs = data.get("documents", [])
        
        book_name = os.path.basename(pdf_path)
        for doc in docs:
            if doc.get("name") == book_name and doc.get("domain") == domain:
                return True
        return False
    except:
        return False


def add_book(pdf_path: str, domain: str, process_ont: bool = False, max_pages: int = 100):
    """
    Agrega un libro al sistema de conocimiento de NEVEN.
    
    Args:
        pdf_path: Ruta absoluta al PDF
        domain: Dominio (econometria, excel, estadistica, algebra_lineal)
        process_ont: Si True, también procesa entidades (usa tokens LLM)
        max_pages: Máximo de páginas para ontología
    """
    print()
    print("═" * 60)
    print("  NEVEN — Agregar Libro al Sistema de Conocimiento")
    print("═" * 60)
    print()
    
    # 1. Verificar archivo
    if not os.path.isfile(pdf_path):
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return False
    
    book_name = os.path.basename(pdf_path)
    print(f"📚 Libro: {book_name}")
    print(f"   Dominio: {domain}")
    print()
    
    # 2. Verificar servidor
    print("🔍 Verificando servidor HTTP...")
    if not check_server_available():
        print("❌ El servidor HTTP no está disponible en localhost:5555")
        print("   Asegúrate de que Excel esté abierto con NEVEN cargado.")
        return False
    print("   ✅ Servidor disponible")
    
    # 3. Verificar si ya está indexado
    print("🔍 Verificando duplicados...")
    if check_already_indexed(pdf_path, domain):
        print(f"⚠️  El libro ya está indexado en RAG con dominio '{domain}'")
        response = input("   ¿Continuar de todas formas? (s/N): ")
        if response.lower() != 's':
            print("   Cancelado.")
            return False
    else:
        print("   ✅ No hay duplicados")
    
    # 4. Obtener número de páginas
    print("🔍 Contando páginas...")
    total_pages = get_page_count(pdf_path)
    if total_pages > 0:
        print(f"   ✅ {total_pages} páginas")
    else:
        print("   ⚠️  No se pudo determinar el número de páginas")
    print()
    
    # 5. Indexar al RAG
    print("🔄 Paso 1/3: Indexando al RAG (búsqueda vectorial)...")
    rag_result = index_to_rag(pdf_path, domain)
    
    if rag_result.get("status") == "ok":
        print(f"   ✅ {rag_result.get('message', 'Indexado correctamente')}")
    else:
        print(f"   ❌ Error: {rag_result.get('error')}")
        return False
    
    # 6. Procesar ontología (opcional)
    entities_created = 0
    relations_created = 0
    
    if process_ont:
        print()
        print(f"🔄 Paso 2/3: Procesando ontología (máx {max_pages} páginas)...")
        print("   ⏳ Esto puede tardar varios minutos. Usa tokens del LLM.")
        
        ont_result = process_ontology(pdf_path, domain, max_pages)
        
        if ont_result.get("status") == "ok":
            entities_created = ont_result.get("entities_created", 0)
            relations_created = ont_result.get("relations_created", 0)
            print(f"   ✅ {entities_created} entidades, {relations_created} relaciones")
        else:
            print(f"   ⚠️  Error: {ont_result.get('error')}")
            print("   El libro queda indexado en RAG pero sin ontología.")
    else:
        print()
        print("⏭️  Paso 2/3: Ontología omitida (usa --ontology para procesar)")
    
    # 7. Crear checkpoint
    print()
    print("🔄 Paso 3/3: Creando checkpoint para UI...")
    checkpoint_path = create_checkpoint(
        pdf_path, domain, total_pages,
        entities_created, relations_created
    )
    print(f"   ✅ {os.path.basename(checkpoint_path)}")
    
    # 8. Resumen final
    print()
    print("═" * 60)
    print("  ✅ LIBRO AGREGADO EXITOSAMENTE")
    print("═" * 60)
    print()
    print(f"  Libro:     {book_name}")
    print(f"  Dominio:   {domain}")
    print(f"  Páginas:   {total_pages if total_pages > 0 else 'Desconocido'}")
    print()
    print("  Componentes actualizados:")
    print("  ├─ RAG (ChromaDB):  ✅ Indexado")
    if process_ont:
        print(f"  ├─ Ontología:       ✅ {entities_created} entidades")
    else:
        print("  ├─ Ontología:       ⏭️  No procesado")
    print("  └─ UI Checkpoint:   ✅ Creado")
    print()
    print("  Para verificar:")
    print(f"  GET http://localhost:5555/api/rag/list")
    print(f"  GET http://localhost:5555/api/ontology/books?domain={domain}")
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Agregar un libro al sistema de conocimiento de NEVEN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python add_book.py "F:\\libros\\MiLibro.pdf" econometria
  python add_book.py "F:\\libros\\MiLibro.pdf" econometria --ontology
  python add_book.py "F:\\libros\\MiLibro.pdf" excel --ontology --max-pages 50

Dominios disponibles:
  econometria     Econometría, series de tiempo, panel data
  excel           Funciones, fórmulas, técnicas de Excel
  estadistica     Pruebas estadísticas, métodos
  algebra_lineal  Matrices, vectores, transformaciones
        """
    )
    
    parser.add_argument("pdf_path", help="Ruta absoluta al archivo PDF")
    parser.add_argument("domain", help="Dominio del libro",
                       choices=["econometria", "excel", "estadistica", "algebra_lineal"])
    parser.add_argument("--ontology", action="store_true",
                       help="También procesar entidades para ontología (usa tokens LLM)")
    parser.add_argument("--max-pages", type=int, default=100,
                       help="Máximo de páginas para ontología (default: 100)")
    
    args = parser.parse_args()
    
    # Normalizar ruta
    pdf_path = os.path.abspath(args.pdf_path)
    
    success = add_book(
        pdf_path=pdf_path,
        domain=args.domain,
        process_ont=args.ontology,
        max_pages=args.max_pages
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
