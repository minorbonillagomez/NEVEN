"""
NEVEM Studio - Main Pipeline
Orquesta el flujo completo: Parse → TTS → Mux → Output
"""

import os
import sys
import time
import shutil
from dataclasses import dataclass
from typing import Optional, Callable

# Asegurar que src está en el path para importaciones relativas
import os
import sys
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from parsers.epub_parser import EpubParser
from parsers.pdf_parser import PdfParser
from parsers.markdown_parser import MarkdownParser
from tts.windows_tts import WindowsTTS
from tts.edge_tts_engine import EdgeTTS
from muxer.ffmpeg_muxer import FFmpegMuxer, ChapterMarker


@dataclass
class PipelineConfig:
    """Configuracion del pipeline"""
    input_file: str
    output_dir: str
    voice_id: Optional[str] = None
    speech_rate: int = 0  # -100 a +100 para Edge TTS
    audio_bitrate: str = "64k"
    keep_temp_files: bool = False
    use_edge_tts: bool = True  # Usar Edge TTS (neural) por defecto
    # Translation options
    translate: bool = False
    source_lang: Optional[str] = None  # Auto-detect if None
    target_lang: str = "es"
    translation_engine: str = "deepl"  # "deepl" or "argos"
    # Page filtering options (PDF only)
    start_page: int = 1  # 1-indexed, first page to include
    exclude_pages: Optional[str] = None  # Comma-separated ranges like '1,2,5-10,45'
    # Parser options
    use_markitdown: bool = False  # MarkItDown genera tablas en PDFs complejos, mejor usar PyMuPDF
    save_markdown: bool = True  # Save .md file alongside .m4b


@dataclass
class PipelineResult:
    """Resultado del pipeline"""
    success: bool
    output_path: Optional[str]
    title: str
    author: str
    chapters_count: int
    total_words: int
    duration_seconds: float
    error_message: Optional[str] = None
    markdown_path: Optional[str] = None  # Path to saved .md file


class NevemPipeline:
    """Pipeline completo para crear audiolibros"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        
        # Seleccionar motor TTS
        if config.use_edge_tts:
            self.tts = EdgeTTS()
            print("[TTS] Usando Edge TTS (voces neurales)")
        else:
            self.tts = WindowsTTS()
            print("[TTS] Usando Windows SAPI")
        
        self.muxer = FFmpegMuxer()
        self.translator = None
        
        # Initialize translator if needed
        if config.translate:
            from translator import UnifiedTranslator, TranslationEngine
            self.translator = UnifiedTranslator()
            self.translation_engine = (
                TranslationEngine.ARGOS if config.translation_engine == "argos" 
                else TranslationEngine.DEEPL
            )
            print(f"[Translator] Usando {config.translation_engine}")
        
        # Directorios de trabajo
        self.temp_dir = os.path.join(config.output_dir, "temp")
        self.audio_dir = os.path.join(self.temp_dir, "audio")
        
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Configurar voz
        if config.voice_id:
            self.tts.set_voice(config.voice_id)
        self.tts.set_rate(config.speech_rate)
    
    def _get_parser(self, file_path: str):
        """Retorna el parser apropiado según la extensión y configuración"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Use MarkItDown parser if enabled (default)
        if self.config.use_markitdown and ext in ['.pdf', '.epub']:
            print(f"[Parser] Usando MarkItDown para mejor estructura")
            return MarkdownParser(
                file_path,
                start_page=self.config.start_page,
                exclude_pages=self.config.exclude_pages
            )
        
        # Fallback to legacy parsers
        if ext == '.epub':
            return EpubParser(file_path)
        elif ext == '.pdf':
            return PdfParser(
                file_path, 
                start_page=self.config.start_page,
                exclude_pages=self.config.exclude_pages
            )
        else:
            raise ValueError(f"Formato no soportado: {ext}")
    
    def run(self, progress_callback: Optional[Callable[[str, float], None]] = None) -> PipelineResult:
        """
        Ejecuta el pipeline completo
        
        Args:
            progress_callback: Callback (stage_name, progress 0-1)
        """
        start_time = time.time()
        
        try:
            # === FASE 1: PARSING ===
            if progress_callback:
                progress_callback("Parseando documento", 0.0)
            
            parser = self._get_parser(self.config.input_file)
            metadata = parser.extract_metadata()
            chapters = parser.extract_chapters()
            
            # Extraer portada
            cover_path = parser.extract_cover(self.temp_dir)
            
            stats = parser.get_stats()
            print(f"\n[Book] {metadata.title} - {metadata.author}")
            print(f"   Capitulos: {len(chapters)}")
            print(f"   Palabras: {stats['total_words']:,}")
            
            if len(chapters) == 0:
                error_msg = "No se encontraron capitulos en el rango de paginas seleccionado"
                if self.config.start_page > 1 or self.config.exclude_pages:
                    error_msg += f" (inicio: {self.config.start_page}, excluidas: {self.config.exclude_pages or 'ninguna'})"
                return PipelineResult(
                    success=False,
                    output_path=None,
                    title=metadata.title,
                    author=metadata.author,
                    chapters_count=0,
                    total_words=0,
                    duration_seconds=0,
                    error_message=error_msg
                )
            
            if progress_callback:
                progress_callback("Documento parseado", 0.1)
            
            # === FASE 1.5: TRANSLATION (if enabled) ===
            if self.config.translate and self.translator:
                if progress_callback:
                    progress_callback("Traduciendo texto", 0.15)
                
                source_lang = self.config.source_lang
                target_lang = self.config.target_lang
                
                # Auto-detect source language if not specified
                if not source_lang:
                    from translator import detect_language
                    sample_text = " ".join(c.text[:500] for c in chapters[:3])
                    source_lang = detect_language(sample_text)
                    print(f"   Idioma detectado: {source_lang}")
                
                print(f"   Traduciendo {source_lang} -> {target_lang}...")
                
                translated_chapters = []
                total_chapters = len(chapters)
                
                for i, chapter in enumerate(chapters):
                    if progress_callback:
                        trans_progress = 0.15 + (0.15 * (i / total_chapters))
                        progress_callback(f"Traduciendo: {chapter.title}", trans_progress)
                    
                    result = self.translator.translate(
                        chapter.text,
                        source_lang,
                        target_lang,
                        self.translation_engine
                    )
                    
                    if result.success:
                        # Create new chapter with translated text
                        from parser.epub_parser import Chapter
                        translated_chapters.append(Chapter(
                            title=chapter.title,
                            text=result.translated_text,
                            order=chapter.order
                        ))
                        print(f"   [{i+1}/{total_chapters}] {chapter.title} - OK")
                    else:
                        print(f"   [{i+1}/{total_chapters}] {chapter.title} - Error: {result.error_message}")
                        # Keep original if translation fails
                        translated_chapters.append(chapter)
                
                chapters = translated_chapters
                print(f"   Traduccion completada")
            
            # === FASE 2: SINTESIS TTS ===
            chapter_audio_files = []
            total_chapters = len(chapters)
            
            voice = self.tts.get_current_voice()
            narrator = voice.name if voice else "Voz Windows"
            
            for i, chapter in enumerate(chapters):
                if progress_callback:
                    chapter_progress = 0.1 + (0.7 * (i / total_chapters))
                    progress_callback(f"Sintetizando: {chapter.title}", chapter_progress)
                
                print(f"\n[Audio] [{i+1}/{total_chapters}] {chapter.title}")
                
                # Archivo de audio del capítulo (Edge genera MP3, Windows genera WAV)
                ext = "mp3" if self.config.use_edge_tts else "wav"
                audio_path = os.path.join(self.audio_dir, f"chapter_{i:03d}.{ext}")
                
                # Sintetizar
                success = self.tts.synthesize_chapter(
                    chapter.text,
                    audio_path,
                    progress_callback=lambda p: progress_callback(
                        f"Sintetizando: {chapter.title}", 
                        0.1 + (0.7 * ((i + p) / total_chapters))
                    ) if progress_callback else None
                )
                
                if success and os.path.exists(audio_path):
                    chapter_audio_files.append((audio_path, chapter.title, 0))
                    
                    # Obtener duración real
                    duration_ms = self.muxer.get_audio_duration_ms(audio_path)
                    chapter_audio_files[-1] = (audio_path, chapter.title, duration_ms)
                    
                    print(f"   [OK] {duration_ms/1000:.1f}s")
                else:
                    print(f"   [!] Error sintetizando capitulo")
            
            if not chapter_audio_files:
                return PipelineResult(
                    success=False,
                    output_path=None,
                    title=metadata.title,
                    author=metadata.author,
                    chapters_count=0,
                    total_words=stats['total_words'],
                    duration_seconds=0,
                    error_message="No se pudo sintetizar ningún capítulo"
                )
            
            # === FASE 3: MUXING ===
            if progress_callback:
                progress_callback("Creando archivo M4B", 0.85)
            
            print(f"\n[Mux] Empaquetando audiolibro...")
            
            # Nombre de archivo de salida
            safe_title = "".join(c for c in metadata.title if c.isalnum() or c in ' -_').strip()
            output_filename = f"{safe_title}.m4b"
            output_path = os.path.join(self.config.output_dir, output_filename)
            
            # Si el archivo ya existe, agregar timestamp para evitar conflicto
            if os.path.exists(output_path):
                from datetime import datetime
                timestamp = datetime.now().strftime("%H%M%S")
                output_filename = f"{safe_title}_{timestamp}.m4b"
                output_path = os.path.join(self.config.output_dir, output_filename)
            
            success = self.muxer.create_from_chapter_audio(
                chapter_audio_files=chapter_audio_files,
                output_path=output_path,
                title=metadata.title,
                author=metadata.author,
                cover_path=cover_path,
                narrator=narrator
            )
            
            if not success:
                return PipelineResult(
                    success=False,
                    output_path=None,
                    title=metadata.title,
                    author=metadata.author,
                    chapters_count=len(chapter_audio_files),
                    total_words=stats['total_words'],
                    duration_seconds=0,
                    error_message="Error creando archivo M4B"
                )
            
            # === FASE 4: GUARDAR MARKDOWN Y LIMPIEZA ===
            if progress_callback:
                progress_callback("Finalizando", 0.95)
            
            # Save Markdown if enabled and parser supports it
            markdown_path = None
            if self.config.save_markdown:
                if hasattr(parser, 'save_markdown'):
                    md_filename = f"{safe_title}.md"
                    markdown_path = os.path.join(self.config.output_dir, md_filename)
                    parser.save_markdown(markdown_path)
                    print(f"   Markdown: {markdown_path}")
                elif hasattr(parser, 'raw_markdown'):
                    # Fallback: save raw_markdown directly
                    md_filename = f"{safe_title}.md"
                    markdown_path = os.path.join(self.config.output_dir, md_filename)
                    with open(markdown_path, 'w', encoding='utf-8') as f:
                        f.write(parser.raw_markdown)
                    print(f"   Markdown (fallback): {markdown_path}")
                else:
                    print(f"   [!] Parser no soporta guardar Markdown")
            
            if not self.config.keep_temp_files:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            # Calcular duración total
            total_duration_ms = sum(c[2] for c in chapter_audio_files)
            total_duration_seconds = total_duration_ms / 1000
            
            if progress_callback:
                progress_callback("Completado", 1.0)
            
            elapsed = time.time() - start_time
            print(f"\n[OK] Audiolibro creado exitosamente!")
            print(f"   Archivo: {output_path}")
            if markdown_path:
                print(f"   Markdown: {markdown_path}")
            print(f"   Duracion: {total_duration_seconds/60:.1f} minutos")
            print(f"   Tiempo de procesamiento: {elapsed/60:.1f} minutos")
            
            # Cerrar parser si es necesario
            if hasattr(parser, 'close'):
                parser.close()
            
            return PipelineResult(
                success=True,
                output_path=output_path,
                title=metadata.title,
                author=metadata.author,
                chapters_count=len(chapter_audio_files),
                total_words=stats['total_words'],
                duration_seconds=total_duration_seconds,
                markdown_path=markdown_path
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return PipelineResult(
                success=False,
                output_path=None,
                title="Error",
                author="",
                chapters_count=0,
                total_words=0,
                duration_seconds=0,
                error_message=str(e)
            )


def list_all_voices():
    """Lista todas las voces disponibles"""
    print("\n" + "=" * 60)
    print("VOCES DISPONIBLES EN NEVEN AUDIOLIBRO")
    print("=" * 60)
    
    # Edge TTS (Neural - requiere internet)
    print("\n[EDGE TTS] Neural, requiere internet - RECOMENDADO")
    print("-" * 50)
    from tts.edge_tts_engine import EdgeTTS, SPANISH_VOICES
    for voice_id, (name, lang, gender) in SPANISH_VOICES.items():
        print(f"  {voice_id:<25} {name:<10} [{lang}] ({gender})")
    
    # Piper TTS (Offline)
    print("\n[PIPER TTS] Neural offline")
    print("-" * 50)
    from tts.piper_tts import PiperTTS, PIPER_VOICES
    piper = PiperTTS()
    for voice_id, info in PIPER_VOICES.items():
        downloaded = "[x]" if piper.is_model_downloaded(voice_id) else "[ ]"
        print(f"  {downloaded} {voice_id:<25} {info['name']:<15} [{info['language']}] ({info['gender']})")
    
    # Windows SAPI
    print("\n[WINDOWS SAPI] Legacy")
    print("-" * 50)
    from tts.windows_tts import WindowsTTS
    win_tts = WindowsTTS()
    for v in win_tts.get_voices():
        print(f"  {v.name:<40} [{v.language}] ({v.gender})")
    
    print("\n" + "=" * 60)
    print("Uso: run.bat libro.pdf --voice es-MX-DaliaNeural")
    print("     run.bat libro.epub --offline --voice es_MX-claude-high")
    print("=" * 60 + "\n")


def main():
    """CLI con argparse"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NEVEN AudioLibro - Generador de Audiolibros",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s libro.epub                           # Genera M4B con voz Dalia
  %(prog)s libro.pdf --voice es-ES-AlvaroNeural # Usa voz espanola
  %(prog)s libro.epub --offline                 # Usa Piper (sin internet)
  %(prog)s libro.pdf --serve                    # Genera y sirve por HTTP
  %(prog)s --list-voices                        # Lista todas las voces
  %(prog)s book.pdf --translate --from en --to es   # Traduce ingles a espanol
  %(prog)s libro.pdf --start-page 5             # Comienza desde pagina 5
  %(prog)s libro.pdf --exclude-pages 1,2,10-12  # Excluye paginas especificas
        """
    )
    
    parser.add_argument("input_file", nargs="?", help="Archivo EPUB o PDF a convertir")
    parser.add_argument("output_dir", nargs="?", default=None, help="Directorio de salida (default: mismo que input)")
    
    parser.add_argument("--voice", "-v", default="es-MX-DaliaNeural",
                       help="ID de la voz a usar (default: es-MX-DaliaNeural)")
    parser.add_argument("--offline", action="store_true",
                       help="Usar Piper TTS (offline, sin internet)")
    parser.add_argument("--rate", "-r", type=int, default=0,
                       help="Velocidad de habla: -50 a +50 (default: 0)")
    parser.add_argument("--serve", "-s", action="store_true",
                       help="Iniciar servidor HTTP después de generar")
    parser.add_argument("--port", "-p", type=int, default=8080,
                       help="Puerto del servidor HTTP (default: 8080)")
    parser.add_argument("--list-voices", "-l", action="store_true",
                       help="Listar todas las voces disponibles")
    parser.add_argument("--keep-temp", action="store_true",
                       help="Mantener archivos temporales")
    
    # Translation options
    parser.add_argument("--translate", "-t", action="store_true",
                       help="Traducir el texto antes de sintetizar")
    parser.add_argument("--from", dest="source_lang", default=None,
                       help="Idioma origen (auto-detectado si no se especifica)")
    parser.add_argument("--to", dest="target_lang", default="es",
                       help="Idioma destino (default: es)")
    parser.add_argument("--translator", default="deepl",
                       choices=["deepl", "argos"],
                       help="Motor de traduccion (default: deepl)")
    
    # Page filtering options (PDF only)
    parser.add_argument("--start-page", type=int, default=1,
                       help="Primera pagina a incluir (default: 1, solo PDF)")
    parser.add_argument("--exclude-pages", default=None,
                       help="Paginas a excluir, ej: '1,2,5-10,45' (solo PDF)")
    
    args = parser.parse_args()
    
    # Listar voces
    if args.list_voices:
        list_all_voices()
        return
    
    # Validar input
    if not args.input_file:
        parser.print_help()
        print("\n[Error] Debes especificar un archivo de entrada")
        sys.exit(1)
    
    if not os.path.exists(args.input_file):
        print(f"[Error] Archivo no encontrado: {args.input_file}")
        sys.exit(1)
    
    output_dir = args.output_dir or os.path.dirname(args.input_file) or "."
    
    # Configurar pipeline
    config = PipelineConfig(
        input_file=args.input_file,
        output_dir=output_dir,
        voice_id=args.voice if not args.offline else None,
        speech_rate=args.rate,
        keep_temp_files=args.keep_temp,
        use_edge_tts=not args.offline,
        translate=args.translate,
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        translation_engine=args.translator,
        start_page=args.start_page,
        exclude_pages=args.exclude_pages
    )
    
    # Si es offline con Piper, establecer voz Piper
    if args.offline:
        # Mapear voz Edge a Piper si es necesario
        piper_voice = args.voice
        if args.voice.startswith("es-MX"):
            piper_voice = "es_MX-claude-high"
        elif args.voice.startswith("es-ES"):
            piper_voice = "es_ES-davefx-medium"
        config.voice_id = piper_voice
    
    # Crear y ejecutar pipeline
    pipeline = NevemPipeline(config)
    
    # Si es offline, usar Piper TTS
    if args.offline:
        from tts.piper_tts import PiperTTS
        pipeline.tts = PiperTTS()
        if config.voice_id:
            pipeline.tts.set_voice(config.voice_id)
        print("[TTS] Usando Piper TTS (modo offline)")
    
    def show_progress(stage: str, progress: float):
        bar_length = 30
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r[{bar}] {progress*100:5.1f}% - {stage}", end="", flush=True)
    
    result = pipeline.run(progress_callback=show_progress)
    print()  # Nueva línea después de la barra de progreso
    
    if not result.success:
        print(f"\n[Error] {result.error_message}")
        sys.exit(1)
    
    # Iniciar servidor si se solicitó
    if args.serve and result.output_path:
        from server.http_server import NevemServer
        
        server = NevemServer(port=args.port)
        book_id = "audiobook"
        
        # Formatear duración
        mins = int(result.duration_seconds // 60)
        secs = int(result.duration_seconds % 60)
        duration_str = f"{mins}:{secs:02d}"
        
        server.add_book(
            book_id=book_id,
            path=result.output_path,
            title=result.title,
            author=result.author,
            duration=duration_str
        )
        
        server.print_qr_ascii(book_id)
        
        try:
            server.start(blocking=True)
        except KeyboardInterrupt:
            print("\n\nServidor detenido")


if __name__ == "__main__":
    main()
