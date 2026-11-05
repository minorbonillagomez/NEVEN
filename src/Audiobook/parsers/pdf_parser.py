"""
NEVEM Studio - PDF Parser
Extrae capítulos, texto y portada de archivos PDF
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, Set
import fitz  # PyMuPDF


def parse_page_exclusions(exclude_str: str) -> Set[int]:
    """
    Parses a comma-separated string of page numbers and ranges into a set of page numbers.
    
    Args:
        exclude_str: String like '1,2,5-10,45' specifying pages to exclude
        
    Returns:
        Set of page numbers, e.g., {1, 2, 5, 6, 7, 8, 9, 10, 45}
        
    Examples:
        parse_page_exclusions('1,2,5-10,45') -> {1, 2, 5, 6, 7, 8, 9, 10, 45}
        parse_page_exclusions('3') -> {3}
        parse_page_exclusions('') -> set()
    """
    if not exclude_str or not exclude_str.strip():
        return set()
    
    result = set()
    
    for part in exclude_str.split(','):
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # Range like '5-10'
            try:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                if start <= end:
                    result.update(range(start, end + 1))
            except ValueError:
                # Skip invalid ranges
                continue
        else:
            # Single number
            try:
                result.add(int(part))
            except ValueError:
                # Skip invalid numbers
                continue
    
    return result


@dataclass
class Chapter:
    """Representa un capítulo del libro"""
    index: int
    title: str
    text: str
    start_page: int
    end_page: int
    
    def __post_init__(self):
        self.text = self._clean_text(self.text)
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto de caracteres no deseados para TTS natural"""
        # Eliminar números de página sueltos
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Eliminar guiones de separación silábica (palabra-\npalabra)
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
        
        # Reemplazar saltos de línea simples por espacios (párrafos continuos)
        # pero preservar dobles saltos (cambios de párrafo reales)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # Normalizar espacios múltiples
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Convertir múltiples saltos de línea en pausa de párrafo (un solo punto y espacio)
        text = re.sub(r'\n{2,}', '.\n\n', text)
        
        # Limpiar puntuación redundante
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\.\s*\.', '.', text)
        
        # Eliminar espacios antes de puntuación
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Asegurar espacio después de puntuación
        text = re.sub(r'([.,;:!?])([A-Za-záéíóúÁÉÍÓÚñÑ])', r'\1 \2', text)
        
        return text.strip()


@dataclass
class BookMetadata:
    """Metadatos del libro"""
    title: str
    author: str
    cover_path: Optional[str] = None


class PdfParser:
    """Parser para archivos PDF"""
    
    # Patrones para detectar títulos de capítulo
    CHAPTER_PATTERNS = [
        r'^(Capítulo|Chapter|CAPÍTULO|CHAPTER)\s+(\d+|[IVXLC]+)',
        r'^(\d+|[IVXLC]+)\.\s+[A-ZÁÉÍÓÚ]',
        r'^(Parte|Part|PARTE|PART)\s+(\d+|[IVXLC]+)',
        r'^(Prólogo|Prologue|Epílogo|Epilogue|Introducción|Introduction)',
    ]
    
    def __init__(self, pdf_path: str, start_page: int = 1, exclude_pages: Optional[str] = None):
        """
        Initialize PDF parser with optional page filtering.
        
        Args:
            pdf_path: Path to the PDF file
            start_page: First page to include (1-indexed, default: 1)
            exclude_pages: Comma-separated string of pages/ranges to exclude, e.g., '1,2,5-10,45'
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.chapters: list[Chapter] = []
        self.metadata: Optional[BookMetadata] = None
        
        # Page filtering configuration
        self.start_page = max(1, start_page)  # Ensure at least 1
        self.exclude_pages_set = parse_page_exclusions(exclude_pages) if exclude_pages else set()
        
        # Log filtering configuration if active
        if self.start_page > 1 or self.exclude_pages_set:
            print(f"[PDF] Filtro de paginas activo:")
            if self.start_page > 1:
                print(f"   Comenzando desde pagina: {self.start_page}")
            if self.exclude_pages_set:
                print(f"   Paginas excluidas: {sorted(self.exclude_pages_set)}")
    
    def _should_include_page(self, page_num_1indexed: int) -> bool:
        """
        Check if a page should be included based on filtering rules.
        
        Args:
            page_num_1indexed: Page number (1-indexed)
            
        Returns:
            True if the page should be included, False otherwise
        """
        # Skip pages before start_page
        if page_num_1indexed < self.start_page:
            return False
        
        # Skip excluded pages
        if page_num_1indexed in self.exclude_pages_set:
            return False
        
        return True
        
    def extract_metadata(self) -> BookMetadata:
        """Extrae metadatos del PDF"""
        meta = self.doc.metadata
        
        title = meta.get('title', '') or os.path.basename(self.pdf_path).replace('.pdf', '')
        author = meta.get('author', '') or "Autor desconocido"
        
        self.metadata = BookMetadata(title=title, author=author)
        return self.metadata
    
    def extract_cover(self, output_dir: str) -> Optional[str]:
        """Extrae la primera página como portada"""
        if len(self.doc) == 0:
            return None
        
        # Renderizar primera página como imagen
        page = self.doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        
        cover_path = os.path.join(output_dir, "cover.png")
        pix.save(cover_path)
        
        if self.metadata:
            self.metadata.cover_path = cover_path
        
        return cover_path
    
    def extract_chapters(self) -> list[Chapter]:
        """Extrae capítulos del PDF usando TOC o detección heurística"""
        # Intentar usar tabla de contenidos del PDF
        toc = self.doc.get_toc()
        
        if toc:
            print(f"[PDF] TOC encontrado con {len(toc)} entradas")
            # Mostrar estructura del TOC
            level1_count = sum(1 for entry in toc if entry[0] == 1)
            print(f"   Capitulos nivel 1: {level1_count}")
            
            if level1_count >= 1:
                return self._extract_from_toc(toc)
        
        print("[PDF] Sin TOC valido, usando deteccion heuristica")
        return self._extract_heuristic()
    
    def _extract_from_toc(self, toc: list) -> list[Chapter]:
        """Extrae capítulos usando la tabla de contenidos del PDF, respetando filtros de página"""
        chapters = []
        total_pages = len(self.doc)
        
        # Calculate the effective range of pages we're including
        effective_end_page = total_pages
        if self.exclude_pages_set:
            # Find the lowest excluded page that's >= start_page
            excluded_above_start = [p for p in self.exclude_pages_set if p >= self.start_page]
            if excluded_above_start:
                # Find continuous exclusion range from some point
                excluded_above_start = sorted(excluded_above_start)
                for i, p in enumerate(excluded_above_start):
                    # Check if this starts a continuous range to the end
                    if p == self.start_page + i or (i > 0 and p == excluded_above_start[i-1] + 1):
                        continue
                    else:
                        # There's a gap, so find where continuous exclusion starts
                        pass
                
                # Simpler: find the first page that starts continuous exclusion to end
                for test_page in range(self.start_page, total_pages + 1):
                    all_excluded_from_here = all(
                        p in self.exclude_pages_set 
                        for p in range(test_page, total_pages + 1)
                    )
                    if all_excluded_from_here:
                        effective_end_page = test_page - 1
                        break
        
        print(f"[PDF] Rango efectivo de paginas: {self.start_page} - {effective_end_page}")
        
        for i, entry in enumerate(toc):
            level, title, page_num = entry
            
            # Solo capítulos de nivel 1
            if level != 1:
                continue
            
            # Determinar página final del capítulo
            chapter_end_page = total_pages
            for j in range(i + 1, len(toc)):
                if toc[j][0] == 1:  # Siguiente capítulo nivel 1
                    chapter_end_page = toc[j][2] - 1
                    break
            
            # Skip chapters that end before our start_page
            if chapter_end_page < self.start_page:
                continue
            
            # Skip chapters that start after our effective end
            if page_num > effective_end_page:
                continue
            
            # Adjust chapter range to our effective range
            effective_chapter_start = max(page_num, self.start_page)
            effective_chapter_end = min(chapter_end_page, effective_end_page)
            
            # Extract text from the effective range (filtering applied in _extract_pages_text)
            text = self._extract_pages_text(effective_chapter_start - 1, effective_chapter_end - 1)
            
            if text and len(text.strip()) > 50:  # Reduced threshold for filtered content
                chapter = Chapter(
                    index=len(chapters),
                    title=title,
                    text=text,
                    start_page=effective_chapter_start,
                    end_page=effective_chapter_end
                )
                chapters.append(chapter)
                print(f"   Capitulo: {title} (p.{effective_chapter_start}-{effective_chapter_end})")
        
        # If TOC-based extraction yielded no chapters, fall back to treating 
        # the entire filtered range as one chapter
        if not chapters:
            print(f"[PDF] TOC no produjo capitulos, usando rango filtrado como capitulo unico")
            text = self._extract_pages_text(self.start_page - 1, effective_end_page - 1)
            if text and len(text.strip()) > 50:
                chapters.append(Chapter(
                    index=0,
                    title="Contenido seleccionado",
                    text=text,
                    start_page=self.start_page,
                    end_page=effective_end_page
                ))
        
        self.chapters = chapters
        return chapters
    
    def _extract_heuristic(self) -> list[Chapter]:
        """Detección heurística de capítulos por patrones de texto, respetando filtros de página"""
        chapters = []
        chapter_boundaries = []
        total_pages = len(self.doc)
        
        # Calculate effective end page considering exclusions
        effective_end_page = total_pages
        if self.exclude_pages_set:
            for test_page in range(self.start_page, total_pages + 1):
                all_excluded_from_here = all(
                    p in self.exclude_pages_set 
                    for p in range(test_page, total_pages + 1)
                )
                if all_excluded_from_here:
                    effective_end_page = test_page - 1
                    break
        
        # Buscar patrones de título de capítulo (only in included pages)
        for page_num in range(len(self.doc)):
            page_num_1indexed = page_num + 1
            
            # Skip pages that should be excluded
            if not self._should_include_page(page_num_1indexed):
                continue
            
            # Skip pages beyond effective end
            if page_num_1indexed > effective_end_page:
                break
            
            page = self.doc[page_num]
            text = page.get_text("text")
            lines = text.split('\n')[:10]  # Solo primeras líneas
            
            for line in lines:
                line = line.strip()
                for pattern in self.CHAPTER_PATTERNS:
                    if re.match(pattern, line, re.IGNORECASE):
                        chapter_boundaries.append((page_num, line))
                        break
        
        # Si no encontramos capítulos, tratar todo el rango filtrado como un capítulo
        if not chapter_boundaries:
            full_text = self._extract_pages_text(self.start_page - 1, effective_end_page - 1)
            if full_text and len(full_text.strip()) > 50:
                chapters.append(Chapter(
                    index=0,
                    title="Contenido seleccionado",
                    text=full_text,
                    start_page=self.start_page,
                    end_page=effective_end_page
                ))
        else:
            # Crear capítulos basados en las fronteras encontradas
            for i, (page_num, title) in enumerate(chapter_boundaries):
                # End at next chapter boundary or effective end
                if i + 1 < len(chapter_boundaries):
                    end_page = chapter_boundaries[i + 1][0]
                else:
                    end_page = effective_end_page - 1  # Convert to 0-indexed
                
                text = self._extract_pages_text(page_num, end_page)
                
                if text and len(text.strip()) > 50:
                    chapters.append(Chapter(
                        index=len(chapters),
                        title=title,
                        text=text,
                        start_page=page_num + 1,
                        end_page=end_page + 1
                    ))
        
        self.chapters = chapters
        return chapters
    
    def _extract_pages_text(self, start: int, end: int) -> str:
        """
        Extrae texto de un rango de páginas, respetando filtros de página.
        
        Args:
            start: Start page index (0-indexed)
            end: End page index (0-indexed, inclusive)
            
        Returns:
            Combined text from all included pages
        """
        text_parts = []
        
        for page_num in range(start, min(end + 1, len(self.doc))):
            # Convert to 1-indexed for filtering check
            page_num_1indexed = page_num + 1
            
            # Skip if page should be excluded
            if not self._should_include_page(page_num_1indexed):
                continue
            
            page = self.doc[page_num]
            text = page.get_text("text")
            text_parts.append(text)
        
        return '\n'.join(text_parts)
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del libro"""
        total_chars = sum(len(ch.text) for ch in self.chapters)
        total_words = sum(len(ch.text.split()) for ch in self.chapters)
        
        return {
            'title': self.metadata.title if self.metadata else "N/A",
            'author': self.metadata.author if self.metadata else "N/A",
            'pages': len(self.doc),
            'chapters': len(self.chapters),
            'total_characters': total_chars,
            'total_words': total_words,
            'estimated_audio_hours': total_words / 150 / 60
        }
    
    def save_markdown(self, output_path: str) -> str:
        """
        Guarda el contenido extraído como archivo Markdown.
        Genera un .md con estructura de capítulos para referencia.
        """
        lines = []
        
        # Header con metadatos
        if self.metadata:
            lines.append(f"# {self.metadata.title}")
            lines.append(f"**Autor:** {self.metadata.author}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Tabla de contenidos
        if len(self.chapters) > 1:
            lines.append("## Índice")
            lines.append("")
            for ch in self.chapters:
                lines.append(f"- [{ch.title}](#{ch.index + 1}-{ch.title.lower().replace(' ', '-')[:30]})")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Contenido de cada capítulo
        for ch in self.chapters:
            lines.append(f"## {ch.index + 1}. {ch.title}")
            lines.append(f"*Páginas {ch.start_page}-{ch.end_page}*")
            lines.append("")
            lines.append(ch.text)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Escribir archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"[Markdown] Guardado: {output_path}")
        return output_path
    
    def close(self):
        """Cierra el documento PDF"""
        self.doc.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        parser = PdfParser(sys.argv[1])
        parser.extract_metadata()
        parser.extract_chapters()
        
        stats = parser.get_stats()
        print(f"\n📖 {stats['title']} - {stats['author']}")
        print(f"   Páginas: {stats['pages']}")
        print(f"   Capítulos: {stats['chapters']}")
        print(f"   Palabras: {stats['total_words']:,}")
        print(f"   Duración estimada: {stats['estimated_audio_hours']:.1f} horas")
        
        print("\n📑 Capítulos:")
        for ch in parser.chapters[:5]:
            preview = ch.text[:100] + "..." if len(ch.text) > 100 else ch.text
            print(f"   {ch.index + 1}. {ch.title} (p.{ch.start_page}-{ch.end_page})")
            print(f"      {preview}\n")
        
        parser.close()
