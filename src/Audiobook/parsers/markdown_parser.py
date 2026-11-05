"""
NEVEM Studio - Markdown Parser
Convierte PDF/EPUB a Markdown usando MarkItDown de Microsoft
y procesa la estructura para TTS con pausas apropiadas
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple
from markitdown import MarkItDown


@dataclass
class Chapter:
    """Representa un capítulo del libro"""
    index: int
    title: str
    text: str  # Texto procesado para TTS (con pausas)
    raw_markdown: str  # Markdown original del capítulo
    start_page: int
    end_page: int


@dataclass
class BookMetadata:
    """Metadatos del libro"""
    title: str
    author: str
    cover_path: Optional[str] = None


class MarkdownParser:
    """
    Parser que convierte PDF/EPUB a Markdown usando MarkItDown
    y luego extrae capítulos con texto optimizado para TTS
    """
    
    # Pausas para diferentes niveles de encabezado (en texto)
    # Usamos puntos suspensivos que el TTS interpreta como pausas
    PAUSE_H1 = "\n\n...\n\n"  # Pausa larga para títulos principales
    PAUSE_H2 = "\n\n..\n\n"   # Pausa media para subtítulos
    PAUSE_H3 = "\n\n.\n\n"    # Pausa corta para secciones
    PAUSE_PARAGRAPH = "\n\n"   # Pausa normal entre párrafos
    
    def __init__(self, file_path: str, start_page: int = 1, exclude_pages: Optional[str] = None):
        """
        Initialize parser.
        
        Args:
            file_path: Path to PDF or EPUB file
            start_page: First page to include (1-indexed) - only for PDF
            exclude_pages: Pages to exclude (e.g., '1,2,5-10') - only for PDF
        """
        self.file_path = file_path
        self.start_page = max(1, start_page)
        self.exclude_pages_str = exclude_pages
        
        # Initialize MarkItDown
        self.md_converter = MarkItDown()
        
        # Storage
        self.raw_markdown: str = ""
        self.chapters: List[Chapter] = []
        self.metadata: Optional[BookMetadata] = None
        
        # Convert file to Markdown
        self._convert_to_markdown()
    
    def _convert_to_markdown(self):
        """Convert the input file to Markdown using MarkItDown or fallback"""
        print(f"[MarkItDown] Convirtiendo: {os.path.basename(self.file_path)}")
        
        # For PDFs with page filtering, we need to extract pages first
        if self.file_path.lower().endswith('.pdf') and (self.start_page > 1 or self.exclude_pages_str):
            self._convert_pdf_with_filtering()
        else:
            # Direct conversion for EPUBs or unfiltered PDFs
            result = self.md_converter.convert(self.file_path)
            self.raw_markdown = result.text_content if hasattr(result, 'text_content') else result.markdown
        
        print(f"[MarkItDown] Conversion completada: {len(self.raw_markdown):,} caracteres")
    
    def _convert_pdf_with_filtering(self):
        """Convert PDF with page filtering using PyMuPDF for extraction"""
        import fitz
        import tempfile
        
        # Parse exclusions
        exclude_set = set()
        if self.exclude_pages_str:
            for part in self.exclude_pages_str.split(','):
                part = part.strip()
                if '-' in part:
                    try:
                        start, end = part.split('-', 1)
                        exclude_set.update(range(int(start), int(end) + 1))
                    except ValueError:
                        pass
                elif part.isdigit():
                    exclude_set.add(int(part))
        
        # Open source PDF
        src_doc = fitz.open(self.file_path)
        total_pages = len(src_doc)
        
        # Calculate which pages to include
        pages_to_include = []
        for page_num in range(1, total_pages + 1):  # 1-indexed
            if page_num >= self.start_page and page_num not in exclude_set:
                pages_to_include.append(page_num - 1)  # Convert to 0-indexed
        
        print(f"[PDF] Filtrando: páginas {self.start_page}-{total_pages}, excluyendo {len(exclude_set)} páginas")
        print(f"[PDF] Páginas a incluir: {len(pages_to_include)}")
        
        if not pages_to_include:
            self.raw_markdown = "# Sin contenido\n\nNo hay páginas en el rango seleccionado."
            src_doc.close()
            return
        
        # Create a new PDF with only selected pages
        new_doc = fitz.open()
        for page_idx in pages_to_include:
            new_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
        
        # Save to temp file (use delete=False and handle cleanup manually)
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(temp_fd)  # Close the file descriptor
        
        new_doc.save(temp_path)
        new_doc.close()
        src_doc.close()
        
        # Convert the filtered PDF with MarkItDown
        try:
            result = self.md_converter.convert(temp_path)
            self.raw_markdown = result.text_content if hasattr(result, 'text_content') else result.markdown
        finally:
            # Cleanup temp file (with retry for Windows)
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except PermissionError:
                pass  # File might still be locked, will be cleaned up by OS
    
    def extract_metadata(self) -> BookMetadata:
        """Extract metadata from the document"""
        # Try to get title from first H1 or filename
        title_match = re.search(r'^#\s+(.+)$', self.raw_markdown, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = os.path.basename(self.file_path).rsplit('.', 1)[0]
        
        # Author is harder to detect - use placeholder
        author = "Autor desconocido"
        
        # Look for author patterns in the first part of the document
        author_patterns = [
            r'(?:por|by|author|autor)[:\s]+([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+)',
            r'^([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)+)\s*$',
        ]
        
        first_500_chars = self.raw_markdown[:500]
        for pattern in author_patterns:
            match = re.search(pattern, first_500_chars, re.IGNORECASE | re.MULTILINE)
            if match:
                author = match.group(1).strip()
                break
        
        self.metadata = BookMetadata(title=title, author=author)
        return self.metadata
    
    def extract_cover(self, output_dir: str) -> Optional[str]:
        """
        Extract cover image if available.
        For now, returns None - cover extraction would need PyMuPDF for PDF.
        """
        # If it's a PDF, try to extract cover using PyMuPDF
        if self.file_path.lower().endswith('.pdf'):
            try:
                import fitz
                doc = fitz.open(self.file_path)
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    cover_path = os.path.join(output_dir, "cover.png")
                    pix.save(cover_path)
                    doc.close()
                    
                    if self.metadata:
                        self.metadata.cover_path = cover_path
                    return cover_path
            except Exception as e:
                print(f"[Cover] No se pudo extraer portada: {e}")
        
        return None
    
    def extract_chapters(self) -> List[Chapter]:
        """
        Extract chapters from the Markdown content.
        Chapters are identified by H1 headers (# Title)
        """
        # Split by H1 headers
        # Pattern: line starting with single # followed by space and text
        chapter_pattern = r'^(#\s+.+)$'
        
        # Find all H1 headers and their positions
        headers: List[Tuple[int, str]] = []
        for match in re.finditer(chapter_pattern, self.raw_markdown, re.MULTILINE):
            headers.append((match.start(), match.group(1)))
        
        print(f"[Markdown] Encontrados {len(headers)} encabezados H1 (capítulos)")
        
        if not headers:
            # No H1 headers found - treat entire content as one chapter
            processed_text = self._process_markdown_for_tts(self.raw_markdown)
            self.chapters = [Chapter(
                index=0,
                title=self.metadata.title if self.metadata else "Contenido",
                text=processed_text,
                raw_markdown=self.raw_markdown,
                start_page=1,
                end_page=1
            )]
            return self.chapters
        
        # Extract each chapter
        chapters = []
        for i, (pos, header) in enumerate(headers):
            # Get chapter title (remove the # prefix)
            title = header.lstrip('#').strip()
            
            # Get chapter content (from this header to the next, or end)
            start_pos = pos
            if i + 1 < len(headers):
                end_pos = headers[i + 1][0]
            else:
                end_pos = len(self.raw_markdown)
            
            raw_content = self.raw_markdown[start_pos:end_pos].strip()
            
            # Process for TTS (add pauses for headers)
            processed_text = self._process_markdown_for_tts(raw_content)
            
            if len(processed_text.strip()) > 50:  # Skip very short chapters
                chapter = Chapter(
                    index=len(chapters),
                    title=title,
                    text=processed_text,
                    raw_markdown=raw_content,
                    start_page=i + 1,  # Approximate
                    end_page=i + 1
                )
                chapters.append(chapter)
                print(f"   Capítulo {len(chapters)}: {title[:50]}...")
        
        self.chapters = chapters
        return chapters
    
    def _process_markdown_for_tts(self, markdown_text: str) -> str:
        """
        Process Markdown text for TTS reading.
        - Add appropriate pauses for headers
        - Clean up formatting that doesn't translate to audio
        - Preserve natural reading flow
        """
        text = markdown_text
        
        # Process headers with pauses
        # H1: # Title -> PAUSE_H1 + "Capítulo: Title" + PAUSE_H1
        text = re.sub(
            r'^#\s+(.+)$',
            lambda m: f'{self.PAUSE_H1}{m.group(1)}{self.PAUSE_H1}',
            text,
            flags=re.MULTILINE
        )
        
        # H2: ## Subtitle -> PAUSE_H2 + "Subtitle" + PAUSE_H2
        text = re.sub(
            r'^##\s+(.+)$',
            lambda m: f'{self.PAUSE_H2}{m.group(1)}{self.PAUSE_H2}',
            text,
            flags=re.MULTILINE
        )
        
        # H3: ### Section -> PAUSE_H3 + "Section" + PAUSE_H3  
        text = re.sub(
            r'^###\s+(.+)$',
            lambda m: f'{self.PAUSE_H3}{m.group(1)}{self.PAUSE_H3}',
            text,
            flags=re.MULTILINE
        )
        
        # H4-H6: treat as minor sections with short pause
        text = re.sub(
            r'^#{4,6}\s+(.+)$',
            lambda m: f'\n\n{m.group(1)}.\n\n',
            text,
            flags=re.MULTILINE
        )
        
        # Remove bold/italic markers but keep the text
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # ***bold italic***
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # **bold**
        text = re.sub(r'\*(.+?)\*', r'\1', text)          # *italic*
        text = re.sub(r'___(.+?)___', r'\1', text)        # ___bold italic___
        text = re.sub(r'__(.+?)__', r'\1', text)          # __bold__
        text = re.sub(r'_(.+?)_', r'\1', text)            # _italic_
        
        # Convert bullet points to readable format
        text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
        
        # Convert numbered lists - keep the numbers
        text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
        
        # Remove links but keep the text: [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove images: ![alt](url) -> (remove completely or keep alt)
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
        
        # Remove inline code backticks
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove code blocks (they don't translate well to audio)
        text = re.sub(r'```[\s\S]*?```', '\n\n(código omitido)\n\n', text)
        
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}\s*$', '\n\n', text, flags=re.MULTILINE)
        
        # Clean up blockquotes - add "cita:" prefix
        text = re.sub(r'^>\s*(.+)$', r'Cita: \1', text, flags=re.MULTILINE)
        
        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r'[ \t]+', ' ', text)     # Normalize spaces
        
        # Clean up excessive pauses (dots)
        text = re.sub(r'\.{4,}', '...', text)
        
        return text.strip()
    
    def get_full_markdown(self) -> str:
        """Return the complete converted Markdown"""
        return self.raw_markdown
    
    def save_markdown(self, output_path: str) -> str:
        """Save the Markdown to a file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.raw_markdown)
        print(f"[Markdown] Guardado: {output_path}")
        return output_path
    
    def get_stats(self) -> dict:
        """Return statistics about the book"""
        total_chars = sum(len(ch.text) for ch in self.chapters)
        total_words = sum(len(ch.text.split()) for ch in self.chapters)
        
        return {
            'title': self.metadata.title if self.metadata else "N/A",
            'author': self.metadata.author if self.metadata else "N/A",
            'pages': len(self.chapters),  # Using chapters as proxy for pages
            'chapters': len(self.chapters),
            'total_characters': total_chars,
            'total_words': total_words,
            'estimated_audio_hours': total_words / 150 / 60,
            'markdown_size': len(self.raw_markdown)
        }
    
    def close(self):
        """Cleanup resources"""
        pass  # No resources to clean up for MarkItDown


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python markdown_parser.py <archivo.pdf|epub>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    parser = MarkdownParser(file_path)
    parser.extract_metadata()
    parser.extract_chapters()
    
    stats = parser.get_stats()
    print(f"\n📖 {stats['title']} - {stats['author']}")
    print(f"   Capítulos: {stats['chapters']}")
    print(f"   Palabras: {stats['total_words']:,}")
    print(f"   Markdown: {stats['markdown_size']:,} bytes")
    print(f"   Duración estimada: {stats['estimated_audio_hours']:.1f} horas")
    
    # Save markdown
    md_path = file_path.rsplit('.', 1)[0] + '.md'
    parser.save_markdown(md_path)
    
    print("\n📑 Capítulos:")
    for ch in parser.chapters[:5]:
        preview = ch.text[:100] + "..." if len(ch.text) > 100 else ch.text
        print(f"   {ch.index + 1}. {ch.title}")
        print(f"      {preview}\n")
