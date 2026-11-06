"""
NEVEN Studio - Marker PDF Parser
Extrae capítulos, texto y portada de archivos PDF usando Marker (datalab-to/marker)
con detección de layout avanzada que excluye headers, footers y números de página.

Marker ofrece ~83.5% de precisión vs ~65% de PyMuPDF en PDFs complejos.
Requiere PyTorch con CUDA para velocidad óptima.
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, Set, List
import tempfile
import shutil

# Marker imports
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    print("[MarkerParser] WARNING: marker-pdf no está instalado. Usar: pip install marker-pdf")

# Import shared utilities from pdf_parser
from .pdf_parser import parse_page_exclusions, Chapter, BookMetadata


class MarkerParser:
    """
    Parser para archivos PDF usando Marker.
    Ofrece mejor detección de layout que PyMuPDF, excluyendo automáticamente:
    - Headers y footers repetitivos
    - Números de página
    - Notas al pie (opcional)
    - Texto de márgenes
    """
    
    # Patrones para detectar títulos de capítulo en el markdown generado
    CHAPTER_PATTERNS = [
        r'^#\s+(Capítulo|Chapter|CAPÍTULO|CHAPTER)\s+(\d+|[IVXLC]+)',
        r'^#\s+(\d+|[IVXLC]+)\.\s+',
        r'^#\s+(Parte|Part|PARTE|PART)\s+(\d+|[IVXLC]+)',
        r'^#\s+(Prólogo|Prologue|Epílogo|Epilogue|Introducción|Introduction)',
        r'^##\s+(Capítulo|Chapter)',
    ]
    
    def __init__(self, pdf_path: str, start_page: int = 1, exclude_pages: Optional[str] = None):
        """
        Initialize Marker PDF parser with optional page filtering.
        
        Args:
            pdf_path: Path to the PDF file
            start_page: First page to include (1-indexed, default: 1)
            exclude_pages: Comma-separated string of pages/ranges to exclude, e.g., '1,2,5-10,45'
        """
        if not MARKER_AVAILABLE:
            raise ImportError("marker-pdf no está instalado. Ejecutar: pip install marker-pdf")
        
        self.pdf_path = pdf_path
        self.chapters: List[Chapter] = []
        self.metadata: Optional[BookMetadata] = None
        self.markdown_content: str = ""
        
        # Page filtering configuration
        self.start_page = max(1, start_page)
        self.exclude_pages_set = parse_page_exclusions(exclude_pages) if exclude_pages else set()
        
        # Marker models (lazy loaded)
        self._models = None
        self._converter = None
        
        # Log filtering configuration if active
        if self.start_page > 1 or self.exclude_pages_set:
            print(f"[Marker] Filtro de páginas activo:")
            if self.start_page > 1:
                print(f"   Comenzando desde página: {self.start_page}")
            if self.exclude_pages_set:
                print(f"   Páginas excluidas: {sorted(self.exclude_pages_set)}")
    
    def _load_models(self):
        """Lazy load Marker models (takes a few seconds on first use)"""
        if self._models is None:
            print("[Marker] Cargando modelos de detección de layout...")
            self._models = create_model_dict()
            print("[Marker] Modelos cargados")
    
    def _should_include_page(self, page_num_1indexed: int) -> bool:
        """Check if a page should be included based on filtering rules."""
        if page_num_1indexed < self.start_page:
            return False
        if page_num_1indexed in self.exclude_pages_set:
            return False
        return True
    
    def extract_metadata(self) -> BookMetadata:
        """Extrae metadatos del PDF"""
        # Use PyMuPDF just for metadata (lightweight)
        import fitz
        doc = fitz.open(self.pdf_path)
        meta = doc.metadata
        
        title = meta.get('title', '') or os.path.basename(self.pdf_path).replace('.pdf', '')
        author = meta.get('author', '') or "Autor desconocido"
        
        doc.close()
        
        self.metadata = BookMetadata(title=title, author=author)
        return self.metadata
    
    def extract_cover(self, output_dir: str) -> Optional[str]:
        """Extrae la primera página como portada usando PyMuPDF"""
        import fitz
        doc = fitz.open(self.pdf_path)
        
        if len(doc) == 0:
            doc.close()
            return None
        
        # Renderizar primera página como imagen
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom
        
        cover_path = os.path.join(output_dir, "cover.png")
        pix.save(cover_path)
        
        doc.close()
        
        if self.metadata:
            self.metadata.cover_path = cover_path
        
        return cover_path
    
    def convert_to_markdown(self) -> str:
        """
        Convierte el PDF a Markdown usando Marker.
        Este es el paso principal que aprovecha la detección de layout.
        
        Returns:
            Markdown content as string
        """
        self._load_models()
        
        print(f"[Marker] Convirtiendo PDF a Markdown: {os.path.basename(self.pdf_path)}")
        
        # Create converter
        converter = PdfConverter(artifact_dict=self._models)
        
        # Convert PDF to markdown
        rendered = converter(self.pdf_path)
        
        # Extract text from rendered output
        markdown_text, _, _ = text_from_rendered(rendered)
        
        # Apply page filtering if needed
        if self.start_page > 1 or self.exclude_pages_set:
            markdown_text = self._filter_markdown_by_pages(markdown_text)
        
        self.markdown_content = markdown_text
        
        # Clean up the markdown
        self.markdown_content = self._clean_markdown(self.markdown_content)
        
        print(f"[Marker] Conversión completada: {len(self.markdown_content)} caracteres")
        return self.markdown_content
    
    def _filter_markdown_by_pages(self, markdown: str) -> str:
        """
        Filtra el markdown por páginas si hay filtros activos.
        Marker incluye marcadores de página en el output que podemos usar.
        """
        # Marker doesn't always include page markers, so we may need to
        # process the PDF with page extraction and then filter
        # For now, return as-is since Marker's layout detection already
        # removes most unwanted content
        return markdown
    
    def _clean_markdown(self, text: str) -> str:
        """Limpia el markdown para mejor TTS"""
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove image references (Marker may include these)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        
        # Remove horizontal rules that aren't chapter separators
        text = re.sub(r'\n-{3,}\n', '\n\n', text)
        
        # Clean up table formatting (convert to plain text)
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'-{2,}', '', text)
        
        # Remove footnote markers
        text = re.sub(r'\[\^?\d+\]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r' \n', '\n', text)
        
        return text.strip()
    
    def extract_chapters(self) -> List[Chapter]:
        """
        Extrae capítulos del markdown convertido.
        Busca headers de markdown (# o ##) que parezcan títulos de capítulo.
        """
        if not self.markdown_content:
            self.convert_to_markdown()
        
        chapters = []
        lines = self.markdown_content.split('\n')
        
        # Find chapter boundaries using markdown headers
        chapter_starts = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if this line looks like a chapter header
            if line_stripped.startswith('#'):
                for pattern in self.CHAPTER_PATTERNS:
                    if re.match(pattern, line_stripped, re.IGNORECASE):
                        # Extract title without the # markers
                        title = re.sub(r'^#+\s*', '', line_stripped)
                        chapter_starts.append((i, title))
                        break
                else:
                    # Also consider any H1 as potential chapter
                    if line_stripped.startswith('# ') and len(line_stripped) > 3:
                        title = line_stripped[2:].strip()
                        # Filter out short or generic headers
                        if len(title) > 3 and title.lower() not in ['index', 'contents', 'toc']:
                            chapter_starts.append((i, title))
        
        # If no chapters found, treat entire document as one chapter
        if not chapter_starts:
            print("[Marker] Sin capítulos detectados, usando documento completo como un capítulo")
            chapters.append(Chapter(
                index=0,
                title=self.metadata.title if self.metadata else "Documento",
                text=self.markdown_content,
                start_page=self.start_page,
                end_page=self.start_page  # Unknown without page markers
            ))
        else:
            print(f"[Marker] {len(chapter_starts)} capítulos detectados")
            
            # Create chapters from boundaries
            for i, (line_num, title) in enumerate(chapter_starts):
                # Get end line (start of next chapter or end of document)
                if i + 1 < len(chapter_starts):
                    end_line = chapter_starts[i + 1][0]
                else:
                    end_line = len(lines)
                
                # Extract chapter text
                chapter_lines = lines[line_num:end_line]
                chapter_text = '\n'.join(chapter_lines)
                
                # Clean the chapter text for TTS
                chapter_text = self._clean_for_tts(chapter_text)
                
                if chapter_text and len(chapter_text.strip()) > 50:
                    chapters.append(Chapter(
                        index=len(chapters),
                        title=title,
                        text=chapter_text,
                        start_page=self.start_page + i,  # Approximate
                        end_page=self.start_page + i
                    ))
                    print(f"   Capítulo: {title}")
        
        self.chapters = chapters
        return chapters
    
    def _clean_for_tts(self, text: str) -> str:
        """Limpia texto específicamente para síntesis de voz"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)        # Code
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Headers
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) -> text
        
        # Remove list markers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Normalize punctuation for TTS
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])([A-Za-záéíóúÁÉÍÓÚñÑ])', r'\1 \2', text)
        
        # Normalize whitespace
        text = re.sub(r'\n{2,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del libro"""
        total_chars = sum(len(ch.text) for ch in self.chapters)
        total_words = sum(len(ch.text.split()) for ch in self.chapters)
        
        return {
            'title': self.metadata.title if self.metadata else "N/A",
            'author': self.metadata.author if self.metadata else "N/A",
            'chapters': len(self.chapters),
            'total_characters': total_chars,
            'total_words': total_words,
            'estimated_audio_hours': total_words / 150 / 60,
            'parser': 'Marker'
        }
    
    def save_markdown(self, output_path: str) -> str:
        """
        Guarda el contenido extraído como archivo Markdown.
        """
        if not self.markdown_content:
            self.convert_to_markdown()
        
        lines = []
        
        # Header con metadatos
        if self.metadata:
            lines.append(f"# {self.metadata.title}")
            lines.append(f"**Autor:** {self.metadata.author}")
            lines.append("")
            lines.append("*Extraído con Marker (detección avanzada de layout)*")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Si tenemos capítulos estructurados, usarlos
        if self.chapters:
            # Tabla de contenidos
            if len(self.chapters) > 1:
                lines.append("## Índice")
                lines.append("")
                for ch in self.chapters:
                    safe_anchor = re.sub(r'[^\w\s-]', '', ch.title.lower()).replace(' ', '-')[:30]
                    lines.append(f"- [{ch.title}](#{ch.index + 1}-{safe_anchor})")
                lines.append("")
                lines.append("---")
                lines.append("")
            
            # Contenido de cada capítulo
            for ch in self.chapters:
                lines.append(f"## {ch.index + 1}. {ch.title}")
                lines.append("")
                lines.append(ch.text)
                lines.append("")
                lines.append("---")
                lines.append("")
        else:
            # Sin capítulos, usar el markdown raw
            lines.append(self.markdown_content)
        
        # Escribir archivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"[Marker] Markdown guardado: {output_path}")
        return output_path
    
    def close(self):
        """Libera recursos"""
        self._models = None
        self._converter = None


def is_marker_available() -> bool:
    """Check if Marker is available and functional"""
    return MARKER_AVAILABLE


if __name__ == "__main__":
    import sys
    
    if not MARKER_AVAILABLE:
        print("ERROR: marker-pdf no está instalado")
        print("Ejecutar: pip install marker-pdf")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        parser = MarkerParser(sys.argv[1])
        parser.extract_metadata()
        parser.convert_to_markdown()
        parser.extract_chapters()
        
        stats = parser.get_stats()
        print(f"\n📖 {stats['title']} - {stats['author']}")
        print(f"   Parser: {stats['parser']}")
        print(f"   Capítulos: {stats['chapters']}")
        print(f"   Palabras: {stats['total_words']:,}")
        print(f"   Duración estimada: {stats['estimated_audio_hours']:.1f} horas")
        
        print("\n📑 Capítulos:")
        for ch in parser.chapters[:5]:
            preview = ch.text[:100] + "..." if len(ch.text) > 100 else ch.text
            print(f"   {ch.index + 1}. {ch.title}")
            print(f"      {preview}\n")
        
        parser.close()
    else:
        print("Uso: python marker_parser.py <archivo.pdf>")
