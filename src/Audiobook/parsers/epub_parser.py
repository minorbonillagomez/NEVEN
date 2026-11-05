"""
NEVEM Studio - EPUB Parser
Extrae capítulos, texto y portada de archivos EPUB
"""

import os
import re
from dataclasses import dataclass
from typing import Optional
from ebooklib import epub
from lxml import etree


@dataclass
class Chapter:
    """Representa un capítulo del libro"""
    index: int
    title: str
    text: str
    
    def __post_init__(self):
        # Limpiar el texto
        self.text = self._clean_text(self.text)
    
    def _clean_text(self, text: str) -> str:
        """Limpia el texto de caracteres no deseados para TTS natural"""
        # Eliminar guiones de separación silábica
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # Reemplazar saltos de línea simples por espacios
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # Normalizar espacios múltiples
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Convertir múltiples saltos de línea en pausa natural
        text = re.sub(r'\n{2,}', '. ', text)
        
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
    language: str
    cover_path: Optional[str] = None


class EpubParser:
    """Parser para archivos EPUB"""
    
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.book = epub.read_epub(epub_path)
        self.chapters: list[Chapter] = []
        self.metadata: Optional[BookMetadata] = None
        
    def extract_metadata(self) -> BookMetadata:
        """Extrae metadatos del libro"""
        title = self.book.get_metadata('DC', 'title')
        title = title[0][0] if title else "Sin título"
        
        author = self.book.get_metadata('DC', 'creator')
        author = author[0][0] if author else "Autor desconocido"
        
        language = self.book.get_metadata('DC', 'language')
        language = language[0][0] if language else "es"
        
        self.metadata = BookMetadata(
            title=title,
            author=author,
            language=language
        )
        return self.metadata
    
    def extract_cover(self, output_dir: str) -> Optional[str]:
        """Extrae la portada del libro y la guarda"""
        cover_path = None
        
        # Buscar la imagen de portada
        for item in self.book.get_items():
            if item.get_type() == epub.ITEM_COVER:
                cover_path = os.path.join(output_dir, "cover.jpg")
                with open(cover_path, 'wb') as f:
                    f.write(item.get_content())
                break
        
        # Si no se encontró como ITEM_COVER, buscar por nombre
        if not cover_path:
            for item in self.book.get_items():
                name = item.get_name().lower()
                if 'cover' in name and item.media_type.startswith('image/'):
                    ext = item.media_type.split('/')[-1]
                    cover_path = os.path.join(output_dir, f"cover.{ext}")
                    with open(cover_path, 'wb') as f:
                        f.write(item.get_content())
                    break
        
        if self.metadata:
            self.metadata.cover_path = cover_path
        return cover_path
    
    def extract_chapters(self) -> list[Chapter]:
        """Extrae todos los capítulos del libro"""
        chapters = []
        chapter_index = 0
        
        # Obtener items de documento (HTML/XHTML)
        for item in self.book.get_items_of_type(epub.ITEM_DOCUMENT):
            content = item.get_content()
            
            try:
                # Parsear HTML
                tree = etree.HTML(content)
                
                # Extraer título del capítulo
                title = self._extract_chapter_title(tree, chapter_index)
                
                # Extraer texto
                text = self._extract_text(tree)
                
                # Solo añadir si hay contenido significativo
                if text and len(text) > 100:
                    chapter = Chapter(
                        index=chapter_index,
                        title=title,
                        text=text
                    )
                    chapters.append(chapter)
                    chapter_index += 1
                    
            except Exception as e:
                print(f"Error parseando capítulo: {e}")
                continue
        
        self.chapters = chapters
        return chapters
    
    def _extract_chapter_title(self, tree, default_index: int) -> str:
        """Extrae el título de un capítulo del HTML"""
        # Buscar en headers h1, h2, h3
        for tag in ['h1', 'h2', 'h3', 'title']:
            elements = tree.xpath(f'//{tag}')
            if elements:
                title = elements[0].text_content().strip()
                if title and len(title) < 200:
                    return title
        
        return f"Capítulo {default_index + 1}"
    
    def _extract_text(self, tree) -> str:
        """Extrae todo el texto de un documento HTML"""
        # Eliminar scripts, styles, etc.
        for element in tree.xpath('//script | //style | //head'):
            element.getparent().remove(element)
        
        # Extraer texto de párrafos
        paragraphs = tree.xpath('//p | //div[@class="p"] | //span[@class="p"]')
        
        if paragraphs:
            text_parts = []
            for p in paragraphs:
                text = p.text_content().strip()
                if text:
                    text_parts.append(text)
            return ' '.join(text_parts)
        
        # Fallback: todo el texto del body
        body = tree.xpath('//body')
        if body:
            return body[0].text_content().strip()
        
        return ""
    
    def get_total_text(self) -> str:
        """Retorna todo el texto del libro concatenado"""
        return '\n\n'.join(ch.text for ch in self.chapters)
    
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
            'estimated_audio_hours': total_words / 150 / 60  # ~150 palabras/min
        }


if __name__ == "__main__":
    # Test básico
    import sys
    if len(sys.argv) > 1:
        parser = EpubParser(sys.argv[1])
        parser.extract_metadata()
        parser.extract_chapters()
        
        stats = parser.get_stats()
        print(f"\n📖 {stats['title']} - {stats['author']}")
        print(f"   Capítulos: {stats['chapters']}")
        print(f"   Palabras: {stats['total_words']:,}")
        print(f"   Duración estimada: {stats['estimated_audio_hours']:.1f} horas")
        
        print("\n📑 Capítulos:")
        for ch in parser.chapters[:5]:
            preview = ch.text[:100] + "..." if len(ch.text) > 100 else ch.text
            print(f"   {ch.index + 1}. {ch.title}")
            print(f"      {preview}\n")
