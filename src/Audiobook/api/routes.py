"""
NEVEM Studio - REST API Routes
Endpoints para la GUI web
"""

import os
import uuid
import threading
from dataclasses import asdict
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

# Importar módulos del proyecto
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline import NevemPipeline, PipelineConfig, PipelineResult
from tts.edge_tts_engine import EdgeTTS, SPANISH_VOICES
from tts.piper_tts import PiperTTS, PIPER_VOICES
from tts.windows_tts import WindowsTTS
from translator import UnifiedTranslator, TranslationEngine, SUPPORTED_LANGUAGES, detect_language


# Estado global de jobs
jobs = {}  # job_id -> {status, progress, stage, result, error}


def create_api_blueprint(upload_folder: str, output_folder: str) -> Blueprint:
    """Crea el blueprint de la API"""
    
    api = Blueprint('api', __name__, url_prefix='/api')
    
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Translation engine (lazy initialization)
    _translator = None
    
    def get_translator():
        nonlocal _translator
        if _translator is None:
            _translator = UnifiedTranslator()
        return _translator
    
    # ═══════════════════════════════════════════════════════════════
    # VOICES
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/voices', methods=['GET'])
    def list_voices():
        """Lista todas las voces disponibles"""
        voices = []
        
        # Edge TTS (Neural)
        for voice_id, (name, lang, gender) in SPANISH_VOICES.items():
            voices.append({
                'id': voice_id,
                'name': name,
                'language': lang,
                'gender': gender,
                'engine': 'edge',
                'neural': True,
                'offline': False
            })
        
        # Piper TTS
        piper = PiperTTS()
        for voice_id, info in PIPER_VOICES.items():
            voices.append({
                'id': voice_id,
                'name': info['name'],
                'language': info['language'],
                'gender': info['gender'],
                'engine': 'piper',
                'neural': True,
                'offline': True,
                'downloaded': piper.is_model_downloaded(voice_id)
            })
        
        # Windows SAPI
        try:
            win_tts = WindowsTTS()
            for v in win_tts.get_voices():
                voices.append({
                    'id': v.id,
                    'name': v.name,
                    'language': v.language,
                    'gender': v.gender,
                    'engine': 'sapi',
                    'neural': False,
                    'offline': True
                })
        except Exception:
            pass
        
        return jsonify(voices)
    
    # ═══════════════════════════════════════════════════════════════
    # VOICE PREVIEW
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/voices/preview/<voice_id>', methods=['GET'])
    def preview_voice(voice_id):
        """Genera una muestra de audio para una voz"""
        import tempfile
        import asyncio
        from flask import send_file
        
        # Texto de muestra en español
        sample_text = "Hola, soy tu asistente de lectura. Así es como sonaré al narrar tu libro."
        
        try:
            # Determinar el motor según el voice_id
            if voice_id.endswith('Neural'):
                # Edge TTS
                import edge_tts
                
                async def generate_preview():
                    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    communicate = edge_tts.Communicate(sample_text, voice_id)
                    await communicate.save(temp_file.name)
                    return temp_file.name
                
                # Ejecutar async
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_path = loop.run_until_complete(generate_preview())
                loop.close()
                
                return send_file(audio_path, mimetype='audio/mpeg', as_attachment=False)
            
            elif voice_id.startswith('HKEY'):
                # Windows SAPI
                win_tts = WindowsTTS()
                win_tts.set_voice(voice_id)
                
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                win_tts.synthesize_to_file(sample_text, temp_file.name)
                
                return send_file(temp_file.name, mimetype='audio/wav', as_attachment=False)
            
            else:
                # Piper TTS
                piper = PiperTTS()
                if not piper.is_model_downloaded(voice_id):
                    return jsonify({'error': 'Modelo no descargado'}), 404
                
                piper.set_voice(voice_id)
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                piper.synthesize_to_file(sample_text, temp_file.name)
                
                return send_file(temp_file.name, mimetype='audio/wav', as_attachment=False)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @api.route('/preview-voice', methods=['POST'])
    def preview_voice_custom():
        """Genera una muestra de audio con texto y velocidad personalizados.
        
        POST body:
        {
            "voice": "es-MX-DaliaNeural",
            "text": "Texto a sintetizar",
            "speed": 0  # -50 a +50
        }
        
        Returns: audio/mpeg
        """
        import tempfile
        import asyncio
        from flask import send_file
        
        data = request.get_json() or {}
        voice_id = data.get('voice', 'es-MX-DaliaNeural')
        text = data.get('text', 'Hola, esta es una muestra de mi voz.')
        speed = int(data.get('speed', 0))
        
        # Limitar texto a ~200 caracteres para preview rápido
        if len(text) > 200:
            text = text[:200] + '...'
        
        try:
            # Solo Edge TTS y Windows SAPI soportados en preview
            if voice_id.endswith('Neural'):
                # Edge TTS con velocidad
                import edge_tts
                
                # Convertir speed a formato Edge TTS (+0%, -20%, etc)
                rate_str = f"+{speed}%" if speed >= 0 else f"{speed}%"
                
                async def generate_preview():
                    temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    communicate = edge_tts.Communicate(text, voice_id, rate=rate_str)
                    await communicate.save(temp_file.name)
                    return temp_file.name
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_path = loop.run_until_complete(generate_preview())
                loop.close()
                
                return send_file(audio_path, mimetype='audio/mpeg', as_attachment=False)
            
            elif voice_id.startswith('Microsoft'):
                # Windows SAPI (nombre simple como "Microsoft Sabina")
                win_tts = WindowsTTS()
                # Buscar la voz por nombre
                voices = win_tts.list_voices()
                found_voice = None
                for v in voices:
                    if voice_id in v.get('name', ''):
                        found_voice = v.get('id')
                        break
                
                if not found_voice:
                    return jsonify({'error': f'Voz no encontrada: {voice_id}'}), 404
                
                win_tts.set_voice(found_voice)
                # Ajustar velocidad (-10 a +10 en SAPI, normalizar desde -50/+50)
                sapi_rate = int(speed / 5)
                win_tts.set_rate(sapi_rate)
                
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                win_tts.synthesize_to_file(text, temp_file.name)
                
                return send_file(temp_file.name, mimetype='audio/wav', as_attachment=False)
            
            else:
                return jsonify({'error': 'Motor de voz no soportado para preview'}), 400
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    # ═══════════════════════════════════════════════════════════════
    # FILE UPLOAD
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/upload', methods=['POST'])
    def upload_file():
        """Sube un archivo EPUB o PDF"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validar extensión
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.epub', '.pdf']:
                return jsonify({'error': 'Only EPUB and PDF files are supported'}), 400
            
            # Guardar archivo
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())[:8]
            save_path = os.path.join(upload_folder, f"{file_id}_{filename}")
            file.save(save_path)
            
            # Extraer metadatos básicos
            title = os.path.splitext(filename)[0]
            author = "Autor desconocido"
            
            # TODO: Parsear archivo para obtener metadatos reales
            
            return jsonify({
                'file_id': file_id,
                'filename': filename,
                'path': save_path,
                'size': os.path.getsize(save_path),
                'title': title,
                'author': author
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    # ═══════════════════════════════════════════════════════════════
    # JOB MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/generate', methods=['POST'])
    def start_generation():
        """Inicia la generación de un audiolibro"""
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path is required'}), 400
        
        file_path = data['file_path']
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Crear job
        job_id = str(uuid.uuid4())[:8]
        jobs[job_id] = {
            'status': 'pending',
            'progress': 0,
            'stage': 'Iniciando...',
            'result': None,
            'error': None
        }
        
        # Configuración
        voice_id = data.get('voice_id', 'es-MX-DaliaNeural')
        speech_rate = data.get('speech_rate', 0)
        use_offline = data.get('offline', False)
        
        # Translation config
        translate = data.get('translate', False)
        source_lang = data.get('source_lang', None)
        target_lang = data.get('target_lang', 'es')
        translation_engine = data.get('translation_engine', 'argos')
        
        # Page filtering config (PDF only)
        start_page = data.get('start_page', 1)
        exclude_pages = data.get('exclude_pages', None)
        
        # Validate start_page
        if not isinstance(start_page, int) or start_page < 1:
            start_page = 1
        
        # Validate exclude_pages (should be string or None)
        if exclude_pages is not None and not isinstance(exclude_pages, str):
            exclude_pages = str(exclude_pages) if exclude_pages else None
        
        # Determinar motor TTS
        use_edge = not use_offline and voice_id.endswith('Neural')
        
        config = PipelineConfig(
            input_file=file_path,
            output_dir=output_folder,
            voice_id=voice_id,
            speech_rate=speech_rate,
            use_edge_tts=use_edge,
            translate=translate,
            source_lang=source_lang,
            target_lang=target_lang,
            translation_engine=translation_engine,
            start_page=start_page,
            exclude_pages=exclude_pages
        )
        
        # Ejecutar en thread separado
        def run_pipeline():
            try:
                jobs[job_id]['status'] = 'running'
                
                pipeline = NevemPipeline(config)
                
                # Si es offline con Piper
                if use_offline and not voice_id.endswith('Neural'):
                    from tts.piper_tts import PiperTTS
                    pipeline.tts = PiperTTS()
                    if voice_id:
                        pipeline.tts.set_voice(voice_id)
                
                def progress_callback(stage: str, progress: float):
                    jobs[job_id]['stage'] = stage
                    jobs[job_id]['progress'] = int(progress * 100)
                
                result = pipeline.run(progress_callback=progress_callback)
                
                if result.success:
                    jobs[job_id]['status'] = 'completed'
                    jobs[job_id]['progress'] = 100
                    jobs[job_id]['result'] = {
                        'output_path': result.output_path,
                        'markdown_path': result.markdown_path,
                        'title': result.title,
                        'author': result.author,
                        'chapters': result.chapters_count,
                        'duration_seconds': result.duration_seconds,
                        'words': result.total_words
                    }
                else:
                    jobs[job_id]['status'] = 'failed'
                    jobs[job_id]['error'] = result.error_message
                    
            except Exception as e:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['error'] = str(e)
        
        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()
        
        return jsonify({'job_id': job_id, 'status': 'pending'})
    
    @api.route('/job/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        """Obtiene el estado de un job"""
        if job_id not in jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(jobs[job_id])
    
    @api.route('/jobs', methods=['GET'])
    def list_jobs():
        """Lista todos los jobs"""
        return jsonify(jobs)
    
    # ═══════════════════════════════════════════════════════════════
    # TWO-STEP WORKFLOW: Extract → Edit → Generate
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/extract', methods=['POST'])
    def extract_to_markdown():
        """
        PASO 1: Extrae PDF/EPUB a Markdown para revisión.
        El usuario puede descargar, editar y luego subir el MD corregido.
        """
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({'error': 'file_path is required'}), 400
        
        file_path = data['file_path']
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Page filtering (PDF only)
        start_page = data.get('start_page', 1)
        exclude_pages = data.get('exclude_pages', None)
        
        if not isinstance(start_page, int) or start_page < 1:
            start_page = 1
        if exclude_pages is not None and not isinstance(exclude_pages, str):
            exclude_pages = str(exclude_pages) if exclude_pages else None
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.pdf':
                from parsers.pdf_parser import PdfParser
                parser = PdfParser(file_path, start_page=start_page, exclude_pages=exclude_pages)
            elif ext == '.epub':
                from parsers.epub_parser import EpubParser
                parser = EpubParser(file_path)
            else:
                return jsonify({'error': f'Formato no soportado: {ext}'}), 400
            
            # Extraer contenido
            metadata = parser.extract_metadata()
            chapters = parser.extract_chapters()
            
            if not chapters:
                return jsonify({'error': 'No se encontraron capítulos'}), 400
            
            # Generar nombre del archivo MD
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            safe_name = "".join(c for c in base_name if c.isalnum() or c in ' -_').strip()
            md_filename = f"{safe_name}_draft.md"
            md_path = os.path.join(output_folder, md_filename)
            
            # Guardar Markdown
            parser.save_markdown(md_path)
            
            # Estadísticas
            stats = parser.get_stats()
            
            if hasattr(parser, 'close'):
                parser.close()
            
            return jsonify({
                'success': True,
                'markdown_path': md_path,
                'markdown_filename': md_filename,
                'title': metadata.title,
                'author': metadata.author,
                'chapters': len(chapters),
                'words': stats['total_words'],
                'estimated_hours': round(stats['estimated_audio_hours'], 1)
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @api.route('/markdown/<filename>', methods=['GET'])
    def get_markdown_content(filename):
        """Obtiene el contenido de un archivo Markdown para edición"""
        safe_filename = secure_filename(filename)
        md_path = os.path.join(output_folder, safe_filename)
        
        if not os.path.exists(md_path):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'filename': safe_filename,
            'content': content,
            'size': len(content)
        })
    
    @api.route('/markdown/<filename>', methods=['PUT'])
    def save_markdown_content(filename):
        """Guarda el contenido editado de un archivo Markdown"""
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'content is required'}), 400
        
        safe_filename = secure_filename(filename)
        md_path = os.path.join(output_folder, safe_filename)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(data['content'])
        
        return jsonify({
            'success': True,
            'filename': safe_filename,
            'size': len(data['content'])
        })
    
    @api.route('/markdown/upload', methods=['POST'])
    def upload_markdown():
        """Sube un archivo Markdown editado externamente (soporta FormData y JSON)"""
        # Check if it's a JSON request (from text content)
        if request.is_json:
            data = request.get_json()
            if not data or 'content' not in data:
                return jsonify({'error': 'content is required'}), 400
            
            filename = data.get('filename', 'uploaded.md')
            content = data['content']
            
            # Ensure .md extension
            if not filename.endswith('.md'):
                filename = filename.rsplit('.', 1)[0] + '.md'
            
            safe_filename = secure_filename(filename)
            save_path = os.path.join(output_folder, safe_filename)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            word_count = len(content.split())
            
            return jsonify({
                'success': True,
                'filename': safe_filename,
                'path': save_path,
                'size': len(content),
                'words': word_count,
                'estimated_hours': round(word_count / 150 / 60, 1)
            })
        
        # Otherwise expect FormData with file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.md', '.txt']:
            return jsonify({'error': 'Solo se aceptan archivos .md o .txt'}), 400
        
        filename = secure_filename(file.filename)
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename = filename.rsplit('.', 1)[0] + '.md'
        
        save_path = os.path.join(output_folder, filename)
        file.save(save_path)
        
        # Leer contenido para estadísticas
        with open(save_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        word_count = len(content.split())
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': save_path,
            'size': len(content),
            'words': word_count,
            'estimated_hours': round(word_count / 150 / 60, 1)
        })
    
    @api.route('/generate-from-markdown', methods=['POST'])
    def generate_from_markdown():
        """
        PASO 2: Genera audio M4B desde un archivo Markdown (editado o no).
        Acepta markdown_path (path completo) o markdown_filename (solo nombre de archivo)
        """
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Accept either markdown_path or markdown_filename
        md_path = data.get('markdown_path')
        md_filename = data.get('markdown_filename')
        
        if not md_path and not md_filename:
            return jsonify({'error': 'markdown_path or markdown_filename is required'}), 400
        
        # If only filename provided, construct full path
        if not md_path and md_filename:
            safe_filename = secure_filename(md_filename)
            md_path = os.path.join(output_folder, safe_filename)
        
        if not os.path.exists(md_path):
            return jsonify({'error': f'Markdown file not found: {md_path}'}), 404
        
        # Crear job
        job_id = str(uuid.uuid4())[:8]
        jobs[job_id] = {
            'status': 'pending',
            'progress': 0,
            'stage': 'Iniciando...',
            'result': None,
            'error': None
        }
        
        # Configuración de voz
        voice_id = data.get('voice_id', 'es-MX-DaliaNeural')
        speech_rate = data.get('speech_rate', 0)
        use_offline = data.get('offline', False)
        
        use_edge = not use_offline and voice_id.endswith('Neural')
        
        def clean_markdown_for_tts(text: str) -> str:
            """
            Limpia el texto Markdown para TTS.
            - # (H1) -> pausa larga (título principal)
            - ## (H2) -> pausa media (subtítulo)
            - ### (H3) -> pausa corta (subtítulo menor)
            - <en>texto</en> -> marca para leer en inglés
            - Elimina otros marcadores de formato
            """
            import re
            
            # Pausas usando puntos suspensivos (el TTS los interpreta como pausas)
            PAUSE_LONG = '\n\n...\n\n'    # H1 - pausa larga
            PAUSE_MEDIUM = '\n\n..\n\n'   # H2 - pausa media  
            PAUSE_SHORT = '\n\n.\n\n'     # H3 - pausa corta
            
            # Procesar headers - convertir # en pausas
            # H1: # Title -> pausa larga + título + pausa larga
            text = re.sub(
                r'^#\s+(.+)$',
                lambda m: f'{PAUSE_LONG}{m.group(1)}{PAUSE_LONG}',
                text,
                flags=re.MULTILINE
            )
            
            # H2: ## Subtitle -> pausa media + título + pausa media
            text = re.sub(
                r'^##\s+(.+)$',
                lambda m: f'{PAUSE_MEDIUM}{m.group(1)}{PAUSE_MEDIUM}',
                text,
                flags=re.MULTILINE
            )
            
            # H3: ### Section -> pausa corta + título + pausa corta
            text = re.sub(
                r'^###\s+(.+)$',
                lambda m: f'{PAUSE_SHORT}{m.group(1)}{PAUSE_SHORT}',
                text,
                flags=re.MULTILINE
            )
            
            # H4-H6: tratar como secciones menores
            text = re.sub(
                r'^#{4,6}\s+(.+)$',
                lambda m: f'\n\n{m.group(1)}.\n\n',
                text,
                flags=re.MULTILINE
            )
            
            # Remover marcadores de negrita/cursiva pero mantener el texto
            text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # ***bold italic***
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # **bold**
            text = re.sub(r'\*(.+?)\*', r'\1', text)          # *italic*
            text = re.sub(r'___(.+?)___', r'\1', text)        # ___bold italic___
            text = re.sub(r'__(.+?)__', r'\1', text)          # __bold__
            text = re.sub(r'_(.+?)_', r'\1', text)            # _italic_
            
            # Convertir bullets a formato legible
            text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
            
            # Remover links pero mantener el texto: [text](url) -> text
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            
            # Remover imágenes
            text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
            
            # Remover backticks de código inline
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            # Remover bloques de código
            text = re.sub(r'```[\s\S]*?```', '\n\n', text)
            
            # Remover líneas horizontales
            text = re.sub(r'^[-*_]{3,}\s*$', '\n\n', text, flags=re.MULTILINE)
            
            # Limpiar blockquotes
            text = re.sub(r'^>\s*(.+)$', r'\1', text, flags=re.MULTILINE)
            
            # Normalizar espacios en blanco
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r'[ \t]+', ' ', text)
            
            return text.strip()
        
        def convert_language_tags_to_ssml(text: str, base_voice: str) -> str:
            """
            Convierte etiquetas <en>texto</en> a SSML para cambio de idioma.
            
            Marcadores soportados:
            - <en>word</en> -> lee en inglés (US)
            - <fr>mot</fr> -> lee en francés
            - <de>wort</de> -> lee en alemán
            - <pt>palavra</pt> -> lee en portugués
            - <it>parola</it> -> lee en italiano
            """
            import re
            
            # Mapeo de idiomas a voces de Edge TTS
            LANGUAGE_VOICES = {
                'en': 'en-US-JennyNeural',      # Inglés US
                'en-us': 'en-US-JennyNeural',   # Inglés US
                'en-gb': 'en-GB-SoniaNeural',   # Inglés UK
                'fr': 'fr-FR-DeniseNeural',     # Francés
                'de': 'de-DE-KatjaNeural',      # Alemán
                'pt': 'pt-BR-FranciscaNeural',  # Portugués Brasil
                'it': 'it-IT-ElsaNeural',       # Italiano
            }
            
            # Buscar todas las etiquetas de idioma
            pattern = r'<(en|en-us|en-gb|fr|de|pt|it)>(.*?)</\1>'
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
            
            if not matches:
                # Sin etiquetas de idioma, retornar texto sin SSML
                return text
            
            # Construir SSML
            ssml_parts = ['<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-MX">']
            last_end = 0
            
            for match in matches:
                lang = match.group(1).lower()
                foreign_text = match.group(2)
                
                # Agregar texto antes de la etiqueta (en idioma base)
                if match.start() > last_end:
                    before_text = text[last_end:match.start()]
                    if before_text.strip():
                        ssml_parts.append(f'<voice name="{base_voice}">{before_text}</voice>')
                
                # Agregar texto en idioma extranjero
                foreign_voice = LANGUAGE_VOICES.get(lang, LANGUAGE_VOICES['en'])
                ssml_parts.append(f'<voice name="{foreign_voice}">{foreign_text}</voice>')
                
                last_end = match.end()
            
            # Agregar texto restante
            if last_end < len(text):
                remaining = text[last_end:]
                if remaining.strip():
                    ssml_parts.append(f'<voice name="{base_voice}">{remaining}</voice>')
            
            ssml_parts.append('</speak>')
            
            return ''.join(ssml_parts)
        
        def synthesize_with_language_tags(text: str, output_path: str, tts, base_voice: str, use_edge: bool) -> bool:
            """
            Sintetiza texto con soporte para etiquetas de idioma.
            Divide el texto en segmentos, sintetiza cada uno con la voz apropiada,
            y concatena los audios resultantes.
            
            Etiquetas soportadas: <en>, <en-us>, <en-gb>, <fr>, <de>, <pt>, <it>
            """
            import re
            import tempfile
            import shutil
            
            # Mapeo de idiomas a voces de Edge TTS
            LANGUAGE_VOICES = {
                'en': 'en-US-JennyNeural',
                'en-us': 'en-US-JennyNeural',
                'en-gb': 'en-GB-SoniaNeural',
                'fr': 'fr-FR-DeniseNeural',
                'de': 'de-DE-KatjaNeural',
                'pt': 'pt-BR-FranciscaNeural',
                'it': 'it-IT-ElsaNeural',
            }
            
            # Buscar etiquetas de idioma
            pattern = r'<(en|en-us|en-gb|fr|de|pt|it)>(.*?)</\1>'
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
            
            # Si no hay etiquetas de idioma, sintetizar normalmente
            if not matches or not use_edge:
                clean_text = re.sub(r'</?(?:en|en-us|en-gb|fr|de|pt|it)>', '', text, flags=re.IGNORECASE)
                return tts.synthesize_chapter(clean_text, output_path)
            
            # Crear directorio temporal para segmentos
            temp_dir = tempfile.mkdtemp(prefix='nevem_lang_')
            segment_files = []
            
            try:
                # Construir lista de segmentos con su idioma
                segments = []
                last_end = 0
                
                for match in matches:
                    # Texto antes de la etiqueta (idioma base)
                    if match.start() > last_end:
                        before_text = text[last_end:match.start()].strip()
                        if before_text:
                            segments.append(('base', before_text))
                    
                    # Texto en idioma extranjero
                    lang = match.group(1).lower()
                    foreign_text = match.group(2).strip()
                    if foreign_text:
                        segments.append((lang, foreign_text))
                    
                    last_end = match.end()
                
                # Texto restante después de la última etiqueta
                if last_end < len(text):
                    remaining = text[last_end:].strip()
                    if remaining:
                        segments.append(('base', remaining))
                
                if not segments:
                    return False
                
                # Sintetizar cada segmento
                from tts.edge_tts_engine import EdgeTTS
                
                for i, (lang, segment_text) in enumerate(segments):
                    segment_path = os.path.join(temp_dir, f"segment_{i:04d}.mp3")
                    
                    if lang == 'base':
                        # Usar voz base
                        tts.set_voice(base_voice)
                        success = tts.synthesize_chapter(segment_text, segment_path)
                    else:
                        # Usar voz del idioma extranjero
                        foreign_voice = LANGUAGE_VOICES.get(lang, LANGUAGE_VOICES['en'])
                        
                        # Crear TTS temporal con voz extranjera
                        foreign_tts = EdgeTTS(default_voice=foreign_voice)
                        success = foreign_tts.synthesize_chapter(segment_text, segment_path)
                    
                    if success and os.path.exists(segment_path):
                        segment_files.append(segment_path)
                
                if not segment_files:
                    return False
                
                # Concatenar todos los segmentos con FFmpeg
                if len(segment_files) == 1:
                    # Solo un segmento, copiar directamente
                    shutil.copy2(segment_files[0], output_path)
                    return True
                
                # Crear archivo de lista para FFmpeg
                list_file = os.path.join(temp_dir, "segments.txt")
                with open(list_file, 'w', encoding='utf-8') as f:
                    for seg_path in segment_files:
                        # Escapar comillas simples en la ruta
                        escaped_path = seg_path.replace("'", "'\\''")
                        f.write(f"file '{escaped_path}'\n")
                
                # Concatenar con FFmpeg
                import subprocess
                cmd = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', list_file,
                    '-c', 'copy',
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"Error FFmpeg concat: {result.stderr}")
                    # Fallback: sintetizar sin etiquetas de idioma
                    clean_text = re.sub(r'</?(?:en|en-us|en-gb|fr|de|pt|it)>', '', text, flags=re.IGNORECASE)
                    tts.set_voice(base_voice)
                    return tts.synthesize_chapter(clean_text, output_path)
                
                return os.path.exists(output_path)
                
            except Exception as e:
                print(f"Error en síntesis multi-idioma: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: sintetizar sin etiquetas
                clean_text = re.sub(r'</?(?:en|en-us|en-gb|fr|de|pt|it)>', '', text, flags=re.IGNORECASE)
                tts.set_voice(base_voice)
                return tts.synthesize_chapter(clean_text, output_path)
                
            finally:
                # Limpiar archivos temporales
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        def run_markdown_to_audio():
            try:
                jobs[job_id]['status'] = 'running'
                jobs[job_id]['stage'] = 'Leyendo Markdown...'
                
                # Leer y parsear el Markdown
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # Parsear capítulos del Markdown
                import re
                chapters = []
                
                # Buscar secciones H2 (## Título)
                sections = re.split(r'^## ', md_content, flags=re.MULTILINE)
                
                if len(sections) > 1:
                    # Primera sección es el header (antes del primer ##)
                    for i, section in enumerate(sections[1:], 1):
                        lines = section.strip().split('\n')
                        title = lines[0].strip()
                        # Remover número de capítulo si existe (ej: "1. Prólogo" -> "Prólogo")
                        title = re.sub(r'^\d+\.\s*', '', title)
                        text = '\n'.join(lines[1:]).strip()
                        if text:
                            chapters.append({'title': title, 'text': text})
                else:
                    # Sin H2, tratar todo como un capítulo
                    chapters.append({'title': 'Contenido', 'text': md_content})
                
                if not chapters:
                    jobs[job_id]['status'] = 'failed'
                    jobs[job_id]['error'] = 'No se encontraron capítulos en el Markdown'
                    return
                
                jobs[job_id]['stage'] = f'Encontrados {len(chapters)} capítulos'
                
                # Configurar TTS
                if use_edge:
                    from tts.edge_tts_engine import EdgeTTS
                    tts = EdgeTTS()
                else:
                    from tts.windows_tts import WindowsTTS
                    tts = WindowsTTS()
                
                if voice_id:
                    tts.set_voice(voice_id)
                tts.set_rate(speech_rate)
                
                # Crear directorios temporales
                import tempfile
                import shutil
                temp_dir = tempfile.mkdtemp(prefix='nevem_')
                audio_dir = os.path.join(temp_dir, 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                
                # Sintetizar cada capítulo
                chapter_audio_files = []
                total_chapters = len(chapters)
                
                for i, chapter in enumerate(chapters):
                    progress = 0.1 + (0.7 * (i / total_chapters))
                    jobs[job_id]['progress'] = int(progress * 100)
                    jobs[job_id]['stage'] = f'Sintetizando: {chapter["title"][:40]}...'
                    
                    ext = "mp3" if use_edge else "wav"
                    audio_path = os.path.join(audio_dir, f"chapter_{i:03d}.{ext}")
                    
                    # Limpiar markdown del texto antes de sintetizar
                    clean_text = clean_markdown_for_tts(chapter['text'])
                    
                    # Procesar etiquetas de idioma y sintetizar
                    success = synthesize_with_language_tags(clean_text, audio_path, tts, voice_id, use_edge)
                    
                    if success and os.path.exists(audio_path):
                        from muxer.ffmpeg_muxer import FFmpegMuxer
                        muxer = FFmpegMuxer()
                        duration_ms = muxer.get_audio_duration_ms(audio_path)
                        chapter_audio_files.append((audio_path, chapter['title'], duration_ms))
                
                if not chapter_audio_files:
                    jobs[job_id]['status'] = 'failed'
                    jobs[job_id]['error'] = 'No se pudo sintetizar ningún capítulo'
                    return
                
                # Crear M4B
                jobs[job_id]['progress'] = 85
                jobs[job_id]['stage'] = 'Creando archivo M4B...'
                
                # Extraer título del MD
                title_match = re.search(r'^# (.+)$', md_content, re.MULTILINE)
                title = title_match.group(1) if title_match else os.path.splitext(os.path.basename(md_path))[0]
                
                author_match = re.search(r'\*\*Autor:\*\*\s*(.+)', md_content)
                author = author_match.group(1).strip() if author_match else 'Autor desconocido'
                
                safe_title = "".join(c for c in title if c.isalnum() or c in ' -_').strip()
                output_filename = f"{safe_title}.m4b"
                output_path = os.path.join(output_folder, output_filename)
                
                # Si el archivo ya existe, agregar timestamp para evitar conflicto
                if os.path.exists(output_path):
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H%M%S")
                    output_filename = f"{safe_title}_{timestamp}.m4b"
                    output_path = os.path.join(output_folder, output_filename)
                
                from muxer.ffmpeg_muxer import FFmpegMuxer
                muxer = FFmpegMuxer()
                
                voice = tts.get_current_voice()
                narrator = voice.name if voice else "Narrador"
                
                success = muxer.create_from_chapter_audio(
                    chapter_audio_files=chapter_audio_files,
                    output_path=output_path,
                    title=title,
                    author=author,
                    narrator=narrator
                )
                
                # Limpiar temporales
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                if success:
                    total_duration_ms = sum(c[2] for c in chapter_audio_files)
                    total_words = sum(len(c['text'].split()) for c in chapters)
                    
                    jobs[job_id]['status'] = 'completed'
                    jobs[job_id]['progress'] = 100
                    jobs[job_id]['stage'] = 'Completado'
                    jobs[job_id]['result'] = {
                        'output_path': output_path,
                        'markdown_path': md_path,
                        'title': title,
                        'author': author,
                        'chapters': len(chapter_audio_files),
                        'duration_seconds': total_duration_ms / 1000,
                        'words': total_words
                    }
                else:
                    jobs[job_id]['status'] = 'failed'
                    jobs[job_id]['error'] = 'Error creando archivo M4B'
                    
            except Exception as e:
                import traceback
                traceback.print_exc()
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['error'] = str(e)
        
        thread = threading.Thread(target=run_markdown_to_audio, daemon=True)
        thread.start()
        
        return jsonify({'job_id': job_id, 'status': 'pending'})
    
    @api.route('/drafts', methods=['GET'])
    def list_drafts():
        """Lista los archivos Markdown disponibles para edición"""
        drafts = []
        
        for filename in os.listdir(output_folder):
            if filename.endswith('.md'):
                path = os.path.join(output_folder, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extraer título
                import re
                title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else filename.replace('.md', '')
                
                drafts.append({
                    'filename': filename,
                    'path': path,
                    'title': title,
                    'size': len(content),
                    'words': len(content.split()),
                    'modified': os.path.getmtime(path)
                })
        
        # Ordenar por fecha de modificación (más reciente primero)
        drafts.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify(drafts)
    
    # ═══════════════════════════════════════════════════════════════
    # OUTPUT FILES
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/books', methods=['GET'])
    def list_books():
        """Lista los audiolibros generados"""
        books = []
        
        for filename in os.listdir(output_folder):
            if filename.endswith('.m4b'):
                path = os.path.join(output_folder, filename)
                books.append({
                    'filename': filename,
                    'path': path,
                    'size': os.path.getsize(path),
                    'title': filename.replace('.m4b', '')
                })
        
        return jsonify(books)
    
    @api.route('/books/<filename>/download', methods=['GET'])
    def download_book(filename):
        """Descarga un audiolibro"""
        from flask import send_file
        
        path = os.path.join(output_folder, secure_filename(filename))
        if not os.path.exists(path):
            return jsonify({'error': 'Book not found'}), 404
        
        return send_file(path, as_attachment=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TRANSLATION
    # ═══════════════════════════════════════════════════════════════
    
    @api.route('/translate/status', methods=['GET'])
    def translation_status():
        """Get status of translation engines"""
        return jsonify(get_translator().get_status())
    
    @api.route('/translate/languages', methods=['GET'])
    def translation_languages():
        """List supported languages"""
        return jsonify(SUPPORTED_LANGUAGES)
    
    @api.route('/translate/detect', methods=['POST'])
    def detect_text_language():
        """Detect language of text"""
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
        
        detected = detect_language(data['text'])
        return jsonify({
            'detected_language': detected,
            'language_name': SUPPORTED_LANGUAGES.get(detected, 'Unknown')
        })
    
    @api.route('/translate', methods=['POST'])
    def translate_text():
        """Translate text"""
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'text is required'}), 400
        
        text = data['text']
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'es')
        engine = data.get('engine', 'deepl')
        
        # Select engine
        try:
            trans_engine = TranslationEngine(engine)
        except ValueError:
            trans_engine = TranslationEngine.DEEPL
        
        result = get_translator().translate(text, source_lang, target_lang, trans_engine)
        
        return jsonify({
            'success': result.success,
            'translated_text': result.translated_text,
            'source_lang': result.source_lang,
            'target_lang': result.target_lang,
            'engine': result.engine,
            'error': result.error_message
        })
    
    @api.route('/translate/argos/models', methods=['GET'])
    def list_argos_models():
        """List available Argos models for download"""
        available = get_translator().argos.get_available_packages()
        installed = get_translator().argos.get_supported_pairs()
        
        return jsonify({
            'available': available,
            'installed': [{'from': p[0], 'to': p[1]} for p in installed]
        })
    
    @api.route('/translate/argos/download', methods=['POST'])
    def download_argos_model():
        """Download an Argos translation model"""
        data = request.get_json()
        
        if not data or 'from_code' not in data or 'to_code' not in data:
            return jsonify({'error': 'from_code and to_code are required'}), 400
        
        success = get_translator().download_argos_model(
            data['from_code'],
            data['to_code']
        )
        
        return jsonify({
            'success': success,
            'from_code': data['from_code'],
            'to_code': data['to_code']
        })
    
    @api.route('/translate/deepl/configure', methods=['POST'])
    def configure_deepl():
        """Configure DeepL API key"""
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify({'error': 'api_key is required'}), 400
        
        # Reinitialize DeepL with new key
        from translator import DeepLTranslator
        get_translator().deepl = DeepLTranslator(api_key=data['api_key'])
        
        return jsonify({
            'success': get_translator().deepl.is_available(),
            'message': 'DeepL configured' if get_translator().deepl.is_available() else 'Invalid API key'
        })
    
    # ═══════════════════════════════════════════════════════════════
    # SYSTEM
    # ═══════════════════════════════════════════════════════════════
    
    # Variable para guardar el último archivo generado
    _last_generated_file = {'path': None}
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check del servidor"""
        return jsonify({
            'status': 'ok',
            'version': '0.1.0'
        })
    
    @api.route('/system', methods=['GET'])
    def system_info():
        """Información del sistema"""
        import socket
        
        # Obtener IP local
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "127.0.0.1"
        
        return jsonify({
            'local_ip': local_ip,
            'upload_folder': upload_folder,
            'output_folder': output_folder
        })
    
    @api.route('/serve', methods=['POST'])
    def start_serve():
        """Prepara el último archivo generado para descarga"""
        # Buscar el archivo más reciente en output
        m4b_files = [f for f in os.listdir(output_folder) if f.endswith('.m4b')]
        
        if not m4b_files:
            return jsonify({'error': 'No hay archivos para servir'}), 404
        
        # Ordenar por fecha de modificación y tomar el más reciente
        m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_folder, f)), reverse=True)
        latest_file = m4b_files[0]
        _last_generated_file['path'] = os.path.join(output_folder, latest_file)
        
        return jsonify({
            'success': True,
            'filename': latest_file,
            'path': _last_generated_file['path']
        })
    
    return api


def create_download_route(app, output_folder: str):
    """Crea la ruta de descarga en la raíz (fuera de /api)"""
    from flask import send_file, render_template_string
    
    # Variable compartida para el archivo a servir
    _serve_file = {'path': None}
    
    @app.route('/download')
    def download_latest():
        """Descarga el último archivo generado - accesible desde QR"""
        # Buscar el archivo más reciente
        m4b_files = [f for f in os.listdir(output_folder) if f.endswith('.m4b')]
        
        if not m4b_files:
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>NEVEM Studio</title>
                    <style>
                        body { 
                            font-family: Georgia, serif; 
                            background: #1a1a1a; 
                            color: #fff; 
                            display: flex; 
                            justify-content: center; 
                            align-items: center; 
                            min-height: 100vh;
                            margin: 0;
                            text-align: center;
                        }
                        .container { padding: 40px; }
                        h1 { color: #DC2626; margin-bottom: 16px; }
                        p { color: #999; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>NEVEM Studio</h1>
                        <p>No hay archivos disponibles para descargar.</p>
                        <p>Genera un audiolibro primero.</p>
                    </div>
                </body>
                </html>
            '''), 404
        
        # Ordenar por fecha y tomar el más reciente
        m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_folder, f)), reverse=True)
        latest_file = m4b_files[0]
        file_path = os.path.join(output_folder, latest_file)
        
        # Página de descarga amigable para móvil
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Descargar Audiolibro - NEVEM</title>
                <style>
                    * { box-sizing: border-box; }
                    body { 
                        font-family: Georgia, serif; 
                        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); 
                        color: #fff; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        min-height: 100vh;
                        margin: 0;
                        padding: 20px;
                    }
                    .card {
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 16px;
                        padding: 40px;
                        text-align: center;
                        max-width: 400px;
                        width: 100%;
                    }
                    .logo { 
                        font-size: 48px; 
                        font-weight: bold; 
                        color: #DC2626;
                        margin-bottom: 8px;
                    }
                    .subtitle {
                        font-size: 12px;
                        color: #666;
                        text-transform: uppercase;
                        letter-spacing: 2px;
                        margin-bottom: 32px;
                    }
                    .filename {
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 8px;
                        word-break: break-word;
                    }
                    .filesize {
                        color: #999;
                        font-style: italic;
                        margin-bottom: 32px;
                    }
                    .download-btn {
                        display: block;
                        width: 100%;
                        padding: 16px 32px;
                        background: #DC2626;
                        color: white;
                        text-decoration: none;
                        border-radius: 8px;
                        font-size: 18px;
                        font-weight: bold;
                        transition: background 0.2s;
                    }
                    .download-btn:hover {
                        background: #B91C1C;
                    }
                    .note {
                        margin-top: 24px;
                        font-size: 12px;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="logo">N</div>
                    <div class="subtitle">NEVEM AudioLibro</div>
                    
                    <div class="filename">{{ filename }}</div>
                    <div class="filesize">{{ "%.1f"|format(size_mb) }} MB</div>
                    
                    <a href="/download/file" class="download-btn">
                        Descargar Audiolibro
                    </a>
                    
                    <p class="note">
                        Despues de descargar, importa el archivo<br>
                        en NEVEN Launcher > Audiolibros > [+]
                    </p>
                </div>
            </body>
            </html>
        ''', filename=latest_file, size_mb=file_size_mb)
    
    @app.route('/download/file')
    def download_file():
        """Descarga directa del archivo M4B"""
        m4b_files = [f for f in os.listdir(output_folder) if f.endswith('.m4b')]
        
        if not m4b_files:
            return "No hay archivos", 404
        
        m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_folder, f)), reverse=True)
        latest_file = m4b_files[0]
        file_path = os.path.join(output_folder, latest_file)
        
        return send_file(
            file_path, 
            as_attachment=True,
            download_name=latest_file,
            mimetype='audio/mp4'
        )
