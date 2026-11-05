"""
NEVEM Studio - HTTP Server with QR Code
Servidor local para transferir audiolibros al celular
Incluye GUI web completa
"""

import os
import socket
import threading
import io
from typing import Optional
from flask import Flask, send_file, render_template_string, send_from_directory, jsonify, request
import qrcode


# Directorio de archivos estáticos (GUI)
GUI_DIR = os.path.join(os.path.dirname(__file__), "..", "gui")


# Template HTML para la página de descarga
DOWNLOAD_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEVEM Studio - {{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
            background: #4CAF50;
            color: white;
            padding: 15px 40px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .download-btn:hover { transform: scale(1.05); }
        .info { margin-top: 30px; font-size: 0.9rem; color: #888; }
        .size { margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📚 {{ title }}</h1>
        <p class="author">{{ author }}</p>
        <a href="/file/{{ book_id }}" class="download-btn">⬇️ Descargar M4B</a>
        <p class="info">Duración: {{ duration }}</p>
        <p class="size">Tamaño: {{ size }}</p>
    </div>
</body>
</html>
"""


class NevemServer:
    """Servidor HTTP para distribuir audiolibros y servir la GUI"""
    
    def __init__(self, port: int = 8080, upload_folder: str = None, output_folder: str = None):
        self.port = port
        self.app = Flask(__name__)
        self.books: dict[str, dict] = {}  # book_id -> {path, title, author, ...}
        self._server_thread: Optional[threading.Thread] = None
        
        # Carpetas por defecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.upload_folder = upload_folder or os.path.join(base_dir, "uploads")
        self.output_folder = output_folder or os.path.join(base_dir, "output")
        
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        self._setup_routes()
        self._setup_api()
    
    def _setup_routes(self):
        """Configura las rutas del servidor"""
        
        @self.app.route('/')
        def index():
            # Si hay libros, mostrar página de descarga; si no, mostrar GUI
            if self.books:
                book_id = list(self.books.keys())[0]
                return self._render_download_page(book_id)
            else:
                # Servir la GUI
                return send_from_directory(GUI_DIR, 'index.html')
        
        @self.app.route('/app')
        def app_gui():
            """Sirve la GUI de la aplicación"""
            return send_from_directory(GUI_DIR, 'index.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Sirve archivos estáticos (CSS, JS)"""
            return send_from_directory(GUI_DIR, filename)
        
        @self.app.route('/neven_theme.css')
        def theme_css():
            """Sirve el CSS del tema"""
            return send_from_directory(GUI_DIR, 'neven_theme.css')
        
        @self.app.route('/download/<book_id>')
        def download_page(book_id):
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
        
        @self.app.route('/api/books')
        def api_books():
            """API para listar libros disponibles"""
            result = []
            for book_id, book in self.books.items():
                result.append({
                    'id': book_id,
                    'title': book.get('title'),
                    'author': book.get('author'),
                    'duration': book.get('duration'),
                    'size': os.path.getsize(book['path']) if os.path.exists(book['path']) else 0
                })
            return jsonify(result)
        
        @self.app.route('/api/info')
        def api_info():
            """Información del servidor"""
            return jsonify({
                'ip': self.get_local_ip(),
                'port': self.port,
                'books_count': len(self.books)
            })
    
    def _render_download_page(self, book_id: str) -> str:
        """Renderiza la página de descarga"""
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
    
    def _setup_api(self):
        """Configura la API REST"""
        try:
            import sys
            # Asegurar que el directorio src esté en el path
            server_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(server_dir)
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            
            from api.routes import create_api_blueprint
            api_bp = create_api_blueprint(self.upload_folder, self.output_folder)
            self.app.register_blueprint(api_bp)
            print(f"✅ API REST habilitada en /api")
        except ImportError as e:
            import traceback
            print(f"⚠️ API no disponible: {e}")
            traceback.print_exc()
    
    def add_book(self, book_id: str, path: str, title: str, author: str, duration: str):
        """Registra un libro para servir"""
        self.books[book_id] = {
            'path': path,
            'title': title,
            'author': author,
            'duration': duration
        }
    
    def get_local_ip(self) -> str:
        """Obtiene la IP local de la máquina"""
        try:
            # Conectar a un servidor externo para determinar la IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def generate_qr(self, book_id: Optional[str] = None, save_path: Optional[str] = None) -> str:
        """Genera código QR con la URL de descarga"""
        ip = self.get_local_ip()
        
        if book_id:
            url = f"http://{ip}:{self.port}/download/{book_id}"
        else:
            url = f"http://{ip}:{self.port}/"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Guardar como imagen si se especifica ruta
        if save_path:
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(save_path)
        
        return url
    
    def print_qr_ascii(self, book_id: Optional[str] = None):
        """Imprime el código QR en ASCII en la terminal"""
        ip = self.get_local_ip()
        
        if book_id:
            url = f"http://{ip}:{self.port}/download/{book_id}"
        else:
            url = f"http://{ip}:{self.port}/"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Imprimir en ASCII
        print("\n" + "=" * 50)
        print("📱 Escanea este código QR desde tu celular:")
        print("=" * 50)
        
        # Usar caracteres Unicode para mejor visualización
        matrix = qr.get_matrix()
        for row in matrix:
            line = ""
            for cell in row:
                line += "██" if cell else "  "
            print(line)
        
        print("=" * 50)
        print(f"🔗 URL: {url}")
        print(f"📡 Puerto: {self.port}")
        print("=" * 50)
        print("\n💡 Asegúrate de que el celular esté en la misma red WiFi")
        print("   Presiona Ctrl+C para detener el servidor\n")
    
    def start(self, blocking: bool = True):
        """Inicia el servidor"""
        if blocking:
            print(f"\n🚀 Servidor iniciado en puerto {self.port}")
            self.app.run(host='0.0.0.0', port=self.port, debug=True, threaded=True, use_reloader=False)
        else:
            self._server_thread = threading.Thread(
                target=lambda: self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True),
                daemon=True
            )
            self._server_thread.start()
            print(f"\n🚀 Servidor iniciado en segundo plano (puerto {self.port})")
    
    def stop(self):
        """Detiene el servidor (solo funciona si se inició en modo no-blocking)"""
        # Flask no tiene un método limpio para detener, pero el thread daemon morirá con el proceso
        pass


if __name__ == "__main__":
    import sys
    
    # Test del servidor
    server = NevemServer(port=8080)
    
    # Si se pasa un archivo M4B como argumento, servirlo
    if len(sys.argv) > 1:
        m4b_path = sys.argv[1]
        if os.path.exists(m4b_path):
            book_id = "test"
            server.add_book(
                book_id=book_id,
                path=m4b_path,
                title=os.path.basename(m4b_path).replace('.m4b', ''),
                author="Test Author",
                duration="N/A"
            )
            server.print_qr_ascii(book_id)
            server.start()
        else:
            print(f"Archivo no encontrado: {m4b_path}")
    else:
        print("Uso: python http_server.py <archivo.m4b>")
