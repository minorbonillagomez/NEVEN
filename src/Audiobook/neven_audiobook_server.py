#!/usr/bin/env python
"""
NEVEN Audiobook Server
Servidor HTTP dedicado para el módulo de Audiolibros de NEVEN Studio

Puerto: 5556 (separado del servidor principal en 5555)
Versión: 1.0.0

Este servidor maneja:
- Conversión de PDF/EPUB a audiolibros M4B
- Generación de códigos QR para transferencia móvil
- API REST para el TaskPane de NEVEN Studio
"""

import os
import sys
import socket
import argparse

# Asegurar que el directorio actual está en el path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from flask import Flask, jsonify
from flask_cors import CORS

# Configuración por defecto
DEFAULT_PORT = 5556
VERSION = "1.0.0"


def create_app(upload_folder: str = None, output_folder: str = None) -> Flask:
    """Crea y configura la aplicación Flask"""
    
    app = Flask(__name__)
    
    # Habilitar CORS para el TaskPane
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Carpetas por defecto
    base_dir = os.path.dirname(SCRIPT_DIR)
    upload_folder = upload_folder or os.path.join(base_dir, "uploads")
    output_folder = output_folder or os.path.join(base_dir, "output")
    
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Guardar configuración en app
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['OUTPUT_FOLDER'] = output_folder
    
    # ═══════════════════════════════════════════════════════════════
    # RUTAS BÁSICAS
    # ═══════════════════════════════════════════════════════════════
    
    @app.route('/')
    def index():
        return jsonify({
            'service': 'NEVEN Audiobook Server',
            'version': VERSION,
            'status': 'running'
        })
    
    @app.route('/api/health')
    def health():
        """Endpoint de salud para verificar que el servidor está activo"""
        return jsonify({
            'status': 'ok',
            'version': VERSION,
            'service': 'neven-audiobook'
        })
    
    @app.route('/api/system')
    def system_info():
        """Información del sistema"""
        return jsonify({
            'local_ip': get_local_ip(),
            'port': DEFAULT_PORT,
            'upload_folder': upload_folder,
            'output_folder': output_folder,
            'version': VERSION
        })
    
    @app.route('/api/download/<filename>')
    def download_file(filename):
        """Descarga un archivo M4B generado"""
        from flask import send_file
        from werkzeug.utils import secure_filename
        
        safe_filename = secure_filename(filename)
        file_path = os.path.join(output_folder, safe_filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename,
            mimetype='audio/mp4'
        )
    
    @app.route('/api/qr')
    def generate_qr():
        """Genera un código QR para transferencia móvil"""
        import io
        from flask import send_file, request
        
        try:
            import qrcode
        except ImportError:
            return jsonify({'error': 'qrcode no instalado'}), 500
        
        # URL destino (la página de descarga)
        url = request.args.get('url', f'http://{get_local_ip()}:{DEFAULT_PORT}/download')
        
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
    
    @app.route('/download')
    def download_page():
        """Página de descarga amigable para móvil"""
        from flask import render_template_string
        
        # Buscar archivo M4B más reciente
        m4b_files = [f for f in os.listdir(output_folder) if f.endswith('.m4b')]
        
        if not m4b_files:
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>NEVEN Audiobook</title>
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
                        h1 { color: #d7a538; margin-bottom: 16px; }
                        p { color: #999; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>NEVEN Audiobook</h1>
                        <p>No hay archivos disponibles.</p>
                    </div>
                </body>
                </html>
            '''), 404
        
        # Obtener el más reciente
        m4b_files.sort(key=lambda f: os.path.getmtime(os.path.join(output_folder, f)), reverse=True)
        latest_file = m4b_files[0]
        file_path = os.path.join(output_folder, latest_file)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Descargar Audiolibro</title>
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
                    .logo { font-size: 48px; font-weight: bold; color: #d7a538; margin-bottom: 8px; }
                    .subtitle { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 32px; }
                    .filename { font-size: 18px; font-weight: bold; margin-bottom: 8px; word-break: break-word; }
                    .filesize { color: #999; font-style: italic; margin-bottom: 32px; }
                    .download-btn {
                        display: block;
                        width: 100%;
                        padding: 16px 32px;
                        background: #d7a538;
                        color: #1a1a1a;
                        text-decoration: none;
                        border-radius: 8px;
                        font-size: 18px;
                        font-weight: bold;
                        transition: background 0.2s;
                    }
                    .download-btn:hover { background: #c49530; }
                    .note { margin-top: 24px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="logo">N</div>
                    <div class="subtitle">NEVEN Audiobook</div>
                    <div class="filename">{{ filename }}</div>
                    <div class="filesize">{{ "%.1f"|format(size_mb) }} MB</div>
                    <a href="/api/download/{{ filename }}" class="download-btn">
                        Descargar Audiolibro
                    </a>
                    <p class="note">
                        Importa el archivo en NEVEN Launcher<br>
                        Audiolibros &gt; [+]
                    </p>
                </div>
            </body>
            </html>
        ''', filename=latest_file, size_mb=file_size_mb)
    
    # ═══════════════════════════════════════════════════════════════
    # REGISTRAR API BLUEPRINT
    # ═══════════════════════════════════════════════════════════════
    
    try:
        from api.routes import create_api_blueprint
        api_bp = create_api_blueprint(upload_folder, output_folder)
        app.register_blueprint(api_bp)
        print(f"[NEVEN Audiobook] API REST habilitada en /api")
    except ImportError as e:
        print(f"[NEVEN Audiobook] ⚠️ API completa no disponible: {e}")
        print("[NEVEN Audiobook] El servidor funcionará en modo básico")
    
    return app


def get_local_ip() -> str:
    """Obtiene la IP local de la máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_banner(port: int):
    """Imprime el banner de inicio"""
    ip = get_local_ip()
    print()
    print("=" * 60)
    print("  NEVEN Audiobook Server")
    print("=" * 60)
    print(f"  Versión:     {VERSION}")
    print(f"  Puerto:      {port}")
    print(f"  IP local:    {ip}")
    print(f"  URL:         http://localhost:{port}")
    print(f"  Health:      http://localhost:{port}/api/health")
    print("=" * 60)
    print()
    print("  Endpoints disponibles:")
    print("  - GET  /api/health          - Estado del servidor")
    print("  - GET  /api/voices          - Listar voces disponibles")
    print("  - POST /api/upload          - Subir archivo PDF/EPUB")
    print("  - POST /api/generate        - Iniciar conversión")
    print("  - GET  /api/job/<id>        - Estado del job")
    print("  - GET  /api/qr              - Generar código QR")
    print()
    print("  Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    print()


def main():
    """Punto de entrada principal"""
    parser = argparse.ArgumentParser(
        description='NEVEN Audiobook Server - Servidor para generación de audiolibros'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'Puerto del servidor (default: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--upload-folder',
        type=str,
        default=None,
        help='Carpeta para archivos subidos'
    )
    parser.add_argument(
        '--output-folder',
        type=str,
        default=None,
        help='Carpeta para archivos generados'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Habilitar modo debug'
    )
    
    args = parser.parse_args()
    
    # Crear aplicación
    app = create_app(
        upload_folder=args.upload_folder,
        output_folder=args.output_folder
    )
    
    # Imprimir banner
    print_banner(args.port)
    
    # Iniciar servidor
    try:
        app.run(
            host='0.0.0.0',
            port=args.port,
            debug=args.debug,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n[NEVEN Audiobook] Servidor detenido")
    except Exception as e:
        print(f"\n[NEVEN Audiobook] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
