"""
NEVEN AudioLibro - Server Entry Point
Entry point for PyInstaller sidecar - all imports bundled together
"""

import os
import sys
import socket
import threading
import io
from typing import Optional
from flask import Flask, send_file, render_template_string, send_from_directory, jsonify, request
from werkzeug.utils import secure_filename
import qrcode
import uuid


# ═══════════════════════════════════════════════════════════════
# Determine base paths
# ═══════════════════════════════════════════════════════════════

def get_base_path():
    """Get the base path for resources"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys._MEIPASS
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()
GUI_DIR = os.path.join(BASE_PATH, "gui")

# Fallback to src/gui if not in frozen mode
if not os.path.exists(GUI_DIR):
    GUI_DIR = os.path.join(os.path.dirname(BASE_PATH), "src", "gui")
if not os.path.exists(GUI_DIR):
    GUI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "gui")

print(f"[NEVEN] Base path: {BASE_PATH}")
print(f"[NEVEN] GUI directory: {GUI_DIR}")


# ═══════════════════════════════════════════════════════════════
# Simplified HTTP Server (standalone version for sidecar)
# ═══════════════════════════════════════════════════════════════

DOWNLOAD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEVEN AudioLibro - {{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Computer Modern Serif', Georgia, serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        h1 { font-size: 1.5rem; margin-bottom: 10px; }
        .author { color: #888; margin-bottom: 30px; }
        .download-btn {
            display: inline-block;
            background: #DC2626;
            color: white;
            padding: 15px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .download-btn:hover { transform: scale(1.05); }
        .info { margin-top: 30px; font-size: 0.9rem; color: #888; }
    </style>
</head>
<body>
    <div class="card">
        <h1>{{ title }}</h1>
        <p class="author">{{ author }}</p>
        <a href="/file/{{ book_id }}" class="download-btn">Descargar M4B</a>
        <p class="info">Duracion: {{ duration }} | Tamano: {{ size }}</p>
    </div>
</body>
</html>
"""


class NevemServer:
    """HTTP Server for NEVEN AudioLibro"""
    
    def __init__(self, port: int = 8080, upload_folder: str = None, output_folder: str = None):
        self.port = port
        self.app = Flask(__name__)
        self.books = {}
        self.selected_file_for_transfer = None  # Nombre del archivo seleccionado
        self.transfer_file_path = None  # Ruta completa del archivo a transferir
        
        # Set folders
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.upload_folder = upload_folder or os.path.join(base_dir, "uploads")
        self.output_folder = output_folder or os.path.join(base_dir, "output")
        
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            if self.books:
                book_id = list(self.books.keys())[0]
                return self._render_download_page(book_id)
            else:
                return send_from_directory(GUI_DIR, 'index.html')
        
        @self.app.route('/app')
        def app_gui():
            return send_from_directory(GUI_DIR, 'index.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory(GUI_DIR, filename)
        
        @self.app.route('/neven_theme.css')
        def theme_css():
            return send_from_directory(GUI_DIR, 'neven_theme.css')
        
        # Ruta legacy para compatibilidad con sistema antiguo de books
        @self.app.route('/book/<book_id>')
        def legacy_book_page(book_id):
            return self._render_download_page(book_id)
        
        @self.app.route('/file/<book_id>')
        def download_file(book_id):
            if book_id not in self.books:
                return "Libro no encontrado", 404
            book = self.books[book_id]
            return send_file(
                book['path'],
                as_attachment=True,
                download_name=os.path.basename(book['path']),
                mimetype='audio/x-m4b'
            )
        
        # API endpoints
        @self.app.route('/api/health')
        def api_health():
            return jsonify({'status': 'ok', 'version': '0.1.0'})
        
        @self.app.route('/api/books')
        def api_books():
            books = []
            for filename in os.listdir(self.output_folder):
                if filename.endswith('.m4b'):
                    path = os.path.join(self.output_folder, filename)
                    books.append({
                        'filename': filename,
                        'path': path,
                        'size': os.path.getsize(path),
                        'title': filename.replace('.m4b', '')
                    })
            return jsonify(books)
        
        @self.app.route('/api/system')
        def api_system():
            return jsonify({
                'local_ip': self.get_local_ip(),
                'upload_folder': self.upload_folder,
                'output_folder': self.output_folder
            })
        
        @self.app.route('/api/qr')
        def api_generate_qr():
            """Genera un QR code como imagen PNG"""
            url = request.args.get('url', f'http://{self.get_local_ip()}:8080/download')
            
            # Generar QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return send_file(img_buffer, mimetype='image/png')
        
        @self.app.route('/api/voices')
        def api_voices():
            # Return basic voice list for sidecar mode
            voices = [
                {'id': 'es-MX-DaliaNeural', 'name': 'Dalia', 'language': 'es-MX', 'gender': 'female', 'engine': 'edge', 'neural': True},
                {'id': 'es-MX-JorgeNeural', 'name': 'Jorge', 'language': 'es-MX', 'gender': 'male', 'engine': 'edge', 'neural': True},
                {'id': 'es-ES-ElviraNeural', 'name': 'Elvira', 'language': 'es-ES', 'gender': 'female', 'engine': 'edge', 'neural': True},
                {'id': 'es-ES-AlvaroNeural', 'name': 'Alvaro', 'language': 'es-ES', 'gender': 'male', 'engine': 'edge', 'neural': True},
            ]
            return jsonify(voices)
        
        @self.app.route('/api/upload', methods=['POST'])
        def api_upload():
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.epub', '.pdf']:
                return jsonify({'error': 'Only EPUB and PDF files are supported'}), 400
            
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())[:8]
            save_path = os.path.join(self.upload_folder, f"{file_id}_{filename}")
            file.save(save_path)
            
            return jsonify({
                'file_id': file_id,
                'filename': filename,
                'path': save_path,
                'size': os.path.getsize(save_path),
                'title': os.path.splitext(filename)[0],
                'author': 'Autor desconocido'
            })
        
        @self.app.route('/api/translate/status')
        def api_translate_status():
            return jsonify({
                'argos': {'available': False, 'installed_pairs': []},
                'deepl': {'available': False}
            })
        
        @self.app.route('/api/transfer/upload', methods=['POST'])
        def api_transfer_upload():
            """Recibe un archivo M4B para transferencia y lo prepara para descarga"""
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.m4b', '.m4a']:
                return jsonify({'error': 'Only M4B and M4A files are supported'}), 400
            
            # Guardar en carpeta temporal de transferencias
            transfer_folder = os.path.join(self.output_folder, '_transfer')
            os.makedirs(transfer_folder, exist_ok=True)
            
            # Limpiar archivos anteriores de transferencia
            for old_file in os.listdir(transfer_folder):
                try:
                    os.remove(os.path.join(transfer_folder, old_file))
                except:
                    pass
            
            filename = secure_filename(file.filename)
            save_path = os.path.join(transfer_folder, filename)
            file.save(save_path)
            
            # Marcar este archivo como el seleccionado para transferencia
            self.selected_file_for_transfer = filename
            self.transfer_file_path = save_path
            
            return jsonify({
                'success': True,
                'filename': filename,
                'path': save_path,
                'size': os.path.getsize(save_path)
            })
        
        @self.app.route('/api/serve', methods=['POST'])
        def api_serve():
            """Prepara un archivo específico o el más reciente para descarga"""
            data = request.get_json() or {}
            requested_filename = data.get('filename')
            
            m4b_files = [f for f in os.listdir(self.output_folder) if f.endswith('.m4b')]
            
            if not m4b_files:
                return jsonify({'error': 'No hay archivos para servir'}), 404
            
            # Si se especificó un archivo, usarlo; si no, usar el más reciente
            if requested_filename and requested_filename in m4b_files:
                selected_file = requested_filename
            else:
                m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_folder, f)), reverse=True)
                selected_file = m4b_files[0]
            
            # Guardar el archivo seleccionado para las rutas de descarga
            self.selected_file_for_transfer = selected_file
            
            return jsonify({
                'success': True,
                'filename': selected_file,
                'path': os.path.join(self.output_folder, selected_file)
            })
        
        @self.app.route('/download')
        def download_page():
            """Página de descarga amigable para móvil - accesible desde QR"""
            # Primero verificar si hay un archivo de transferencia
            transfer_folder = os.path.join(self.output_folder, '_transfer')
            if hasattr(self, 'transfer_file_path') and self.transfer_file_path and os.path.exists(self.transfer_file_path):
                target_file = os.path.basename(self.transfer_file_path)
                file_path = self.transfer_file_path
            else:
                # Fallback: buscar en output folder
                m4b_files = [f for f in os.listdir(self.output_folder) if f.endswith('.m4b') and not f.startswith('_')]
                
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
                                <p>Selecciona un archivo en la aplicacion primero.</p>
                            </div>
                        </body>
                        </html>
                    '''), 404
                
                # Usar el archivo seleccionado o el más reciente
                if self.selected_file_for_transfer and self.selected_file_for_transfer in m4b_files:
                    target_file = self.selected_file_for_transfer
                else:
                    m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_folder, f)), reverse=True)
                    target_file = m4b_files[0]
                
                file_path = os.path.join(self.output_folder, target_file)
            
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
            ''', filename=target_file, size_mb=file_size_mb)
        
        @self.app.route('/download/file')
        def download_file_direct():
            """Descarga directa del archivo M4B"""
            # Primero verificar si hay un archivo de transferencia
            if hasattr(self, 'transfer_file_path') and self.transfer_file_path and os.path.exists(self.transfer_file_path):
                target_file = os.path.basename(self.transfer_file_path)
                file_path = self.transfer_file_path
            else:
                # Fallback: buscar en output folder
                m4b_files = [f for f in os.listdir(self.output_folder) if f.endswith('.m4b') and not f.startswith('_')]
                
                if not m4b_files:
                    return "No hay archivos", 404
                
                # Usar el archivo seleccionado o el más reciente
                if self.selected_file_for_transfer and self.selected_file_for_transfer in m4b_files:
                    target_file = self.selected_file_for_transfer
                else:
                    m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.output_folder, f)), reverse=True)
                    target_file = m4b_files[0]
                
                file_path = os.path.join(self.output_folder, target_file)
            
            return send_file(
                file_path, 
                as_attachment=True,
                download_name=target_file,
                mimetype='audio/mp4'
            )
    
    def _render_download_page(self, book_id):
        if book_id not in self.books:
            return "Libro no encontrado", 404
        
        book = self.books[book_id]
        size_mb = os.path.getsize(book['path']) / (1024 * 1024)
        
        return render_template_string(
            DOWNLOAD_PAGE,
            title=book.get('title', 'Audiolibro'),
            author=book.get('author', 'Autor desconocido'),
            book_id=book_id,
            duration=book.get('duration', 'N/A'),
            size=f"{size_mb:.1f} MB"
        )
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def add_book(self, book_id, path, title, author, duration):
        self.books[book_id] = {
            'path': path,
            'title': title,
            'author': author,
            'duration': duration
        }
    
    def start(self, blocking=True):
        print(f"[NEVEN] Server starting on port {self.port}")
        print(f"[NEVEN] GUI: {GUI_DIR}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)


if __name__ == "__main__":
    print("[NEVEN] Starting NEVEN AudioLibro Server...")
    
    # Import and register the full API blueprint
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from api.routes import create_api_blueprint
        
        server = NevemServer(port=8080)
        
        # Register the full API blueprint (adds /api/generate, etc.)
        api_blueprint = create_api_blueprint(server.upload_folder, server.output_folder)
        server.app.register_blueprint(api_blueprint)
        
        print("[NEVEN] Full API loaded")
    except ImportError as e:
        print(f"[NEVEN] Running in simplified mode: {e}")
        server = NevemServer(port=8080)
    
    server.start()
