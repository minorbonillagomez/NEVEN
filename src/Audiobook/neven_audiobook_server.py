#!/usr/bin/env python
"""
NEVEN Audiobook Server
Servidor HTTP dedicado para el módulo de Audiolibros de NEVEN Studio

Puerto: 5557 por defecto (configurable en neven-config.json, Audiobook.port);
escucha solo en 127.0.0.1 salvo Audiobook.lan=true
Versión: 1.0.0

Este servidor maneja:
- Conversión de PDF/EPUB a audiolibros M4B
- Generación de códigos QR para transferencia móvil
- API REST para el TaskPane de NEVEN Studio
"""

import os
import sys
import json
import socket
import argparse
import logging

# Asegurar que el directorio actual está en el path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from flask import Flask, jsonify
from werkzeug.serving import ThreadedWSGIServer
import neven_local_auth as _auth
from urllib.parse import quote
from muxer.ffmpeg_muxer import AUDIOBOOK_EXTENSIONS

# Configuración por defecto
DEFAULT_PORT = 5557
VERSION = "1.0.0"
LOOPBACK_HOST = "127.0.0.1"
LAN_HOST = "0.0.0.0"
# Puertos que usan otros servicios de NEVEN (Studio, su fallback y el AgentService).
RESERVED_PORTS = frozenset({5555, 5556})
EXIT_CONFIG = 2
EXIT_PORT_BUSY = 3
_log = logging.getLogger("NEVEN.Audiobook")


class ConfigError(Exception):
    """Configuracion invalida; el mensaje nombra la clave y el valor."""


def default_config_path():
    """neven-config.json junto a la carpeta Audiobook (p. ej. NEVEN/neven-config.json)."""
    return os.path.join(os.path.dirname(SCRIPT_DIR), "neven-config.json")


def load_config(config_path=None):
    path = config_path or default_config_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise ConfigError(f"no se pudo leer {path}: {e}")
    if not isinstance(data, dict):
        raise ConfigError(f"{path} no contiene un objeto JSON")
    return data


def _studio_config_ports(config):
    tp = config.get("TaskPane") or {}
    ports = set()
    for key, default in (("port", 5555), ("fallbackPort", 5556)):
        v = tp.get(key, default)
        if isinstance(v, int) and not isinstance(v, bool):
            ports.add(v)
    return ports


def resolve_port(args_port, config_path=None):
    """Precedencia: --port > Audiobook.port > DEFAULT_PORT. Valida rango y reservados."""
    config = load_config(config_path)
    audiobook = config.get("Audiobook") or {}
    if args_port is not None:
        value, source = args_port, "--port"
    elif "port" in audiobook:
        value, source = audiobook["port"], "Audiobook.port"
    else:
        value, source = DEFAULT_PORT, "DEFAULT_PORT"
    if isinstance(value, bool) or not isinstance(value, int) or not 1024 <= value <= 65535:
        raise ConfigError(f"{source}={value!r} no es un puerto entero entre 1024 y 65535")
    reserved = RESERVED_PORTS | _studio_config_ports(config)
    if value in reserved:
        raise ConfigError(
            f"{source}={value} esta reservado por otro servicio de NEVEN "
            f"(Studio, su fallbackPort o el AgentService: {sorted(reserved)}). "
            "Elija otro valor en Audiobook.port de neven-config.json")
    return value


def resolve_lan(config_path=None):
    """Audiobook.lan: ausente = False; si existe debe ser booleano."""
    audiobook = load_config(config_path).get("Audiobook") or {}
    if "lan" not in audiobook:
        return False
    lan = audiobook["lan"]
    if not isinstance(lan, bool):
        raise ConfigError(f"Audiobook.lan={lan!r} debe ser true o false")
    return lan


def resolve_studio_ports(config_path=None):
    """Puerto real del servidor principal (NEVEN_STUDIO_PORT) o, si no, los de la config."""
    env = os.environ.get("NEVEN_STUDIO_PORT")
    if env:
        if env.isascii() and env.isdigit():
            return {int(env)}
        raise ConfigError(f"NEVEN_STUDIO_PORT={env!r} no es un puerto")
    return _studio_config_ports(load_config(config_path)) or {5555, 5556}


def create_app(upload_folder: str = None, output_folder: str = None,
               port: int = None, studio_ports=None, lan: bool = False,
               token_file: str = None) -> Flask:
    """Crea y configura la aplicacion Flask"""
    
    app = Flask(__name__)
    
    # Autenticacion local (SEC-16): secreto de sesion, Host y Origin locales
    own_port = port or DEFAULT_PORT
    if studio_ports is None:
        studio_ports = {5555, 5556}
    token_reader = _auth.TokenReader(token_file or _auth.resolve_token_file())
    _auth.install_guard(app, own_port, studio_ports, token_reader, lan=lan, log=_log)
    app.config['PORT'] = own_port
    app.config['LAN'] = bool(lan)
    app.config['STUDIO_PORT'] = next(iter(studio_ports)) if len(studio_ports) == 1 else None

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
            'service': 'neven-audiobook',
            'port': own_port,
            'studio_port': app.config['STUDIO_PORT'],
            'pid': os.getpid(),
            'lan': bool(lan)
        })
    
    @app.route('/api/system')
    def system_info():
        """Información del sistema"""
        return jsonify({
            'local_ip': get_local_ip(),
            'port': own_port,
            'upload_folder': upload_folder,
            'output_folder': output_folder,
            'version': VERSION
        })
    
    @app.route('/api/download/<path:filename>')
    def download_file(filename):
        """Descarga un audiolibro por nombre EXACTO (M4B, o M4A heredado).

        Flask ya decodifica la URL en <path:filename>: no se decodifica otra vez
        (%2520 debe buscar un archivo llamado '%20', no 'a b'). Si el nombre no es
        un archivo de output_folder, 404; no se sirve otro archivo parecido.
        La contencion se comprueba con commonpath sobre rutas reales (startswith
        aceptaria un directorio hermano 'output_x').
        """
        from flask import send_file
        base = os.path.realpath(output_folder)
        file_path = os.path.realpath(os.path.join(base, filename))
        try:
            inside = os.path.commonpath([base, file_path]) == base
        except ValueError:  # otra unidad
            inside = False
        if not inside:
            _log.warning("Descarga rechazada (fuera de la carpeta de salida): %r", filename)
            return jsonify({'error': 'Acceso no permitido'}), 403
        if not os.path.isfile(file_path):
            _log.info("Descarga: archivo no encontrado: %r", filename)
            return jsonify({'error': 'Archivo no encontrado', 'requested': filename}), 404
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path),
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
        
        if not lan:
            return jsonify({
                'status': 'error',
                'code': 'lan_disabled',
                'message': 'El servidor de audiolibros escucha solo en 127.0.0.1; '
                           'un movil no puede alcanzarlo. Para habilitar la red local '
                           'ponga Audiobook.lan=true en neven-config.json y reinicie el servidor.'
            }), 409
        # URL destino (la página de descarga)
        url = request.args.get('url', f'http://{get_local_ip()}:{own_port}/download')
        
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
        
        # Buscar el audiolibro más reciente (.m4b, o .m4a heredado)
        m4b_files = [f for f in os.listdir(output_folder) if f.lower().endswith(AUDIOBOOK_EXTENSIONS)]
        
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
                    <a href="{{ download_href }}" class="download-btn">
                        Descargar Audiolibro
                    </a>
                    <p class="note">
                        Importa el archivo en NEVEN Launcher<br>
                        Audiolibros &gt; [+]
                    </p>
                </div>
            </body>
            </html>
        ''', filename=latest_file, size_mb=file_size_mb,
            download_href='/api/download/' + quote(latest_file, safe=''))
    
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


def print_banner(port: int, lan: bool = False):
    """Imprime el banner de inicio"""
    ip = get_local_ip()
    print()
    print("=" * 60)
    print("  NEVEN Audiobook Server")
    print("=" * 60)
    print(f"  Version:     {VERSION}")
    print(f"  Puerto:      {port}")
    if lan:
        print(f"  Escucha en:  0.0.0.0 (red local, IP {ip}) - AVISO: expuesto a la red local")
    else:
        print("  Escucha en:  127.0.0.1 (solo este equipo)")
    print(f"  URL:         http://localhost:{port}")
    print(f"  Health:      http://localhost:{port}/api/health")
    print("=" * 60)
    print()
    print("  Endpoints disponibles:")
    print("  - GET  /api/health          - Estado del servidor")
    print("  - GET  /api/voices          - Listar voces disponibles")
    print("  - POST /api/upload          - Subir archivo PDF/EPUB")
    print("  - POST /api/generate        - Iniciar conversion")
    print("  - GET  /api/job/<id>        - Estado del job")
    print("  - GET  /api/qr              - Generar codigo QR")
    print()
    print("  Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    print()
    sys.stdout.flush()


def _fatal(code: int, message: str):
    print(f"[NEVEN Audiobook] ERROR: {message}", file=sys.stderr)
    sys.stderr.flush()
    sys.exit(code)


class _ExclusiveThreadedServer(ThreadedWSGIServer):
    """No comparte puerto: en Windows SO_REUSEADDR permitiria un bind doble silencioso."""
    allow_reuse_address = False


def main():
    """Punto de entrada principal"""
    parser = argparse.ArgumentParser(
        description='NEVEN Audiobook Server - Servidor para generacion de audiolibros'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=None,
        help=f'Puerto del servidor (default: Audiobook.port de neven-config.json, o {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Ruta de neven-config.json (default: junto a la carpeta Audiobook)'
    )
    parser.add_argument('--upload-folder', type=str, default=None, help='Carpeta para archivos subidos')
    parser.add_argument('--output-folder', type=str, default=None, help='Carpeta para archivos generados')
    args = parser.parse_args()

    try:
        port = resolve_port(args.port, args.config)
        lan = resolve_lan(args.config)
        studio_ports = resolve_studio_ports(args.config)
        token_file = _auth.resolve_token_file(load_config(args.config))
    except ConfigError as e:
        _fatal(EXIT_CONFIG, f"configuracion invalida: {e}")

    host = LAN_HOST if lan else LOOPBACK_HOST
    app = create_app(
        upload_folder=args.upload_folder,
        output_folder=args.output_folder,
        port=port, studio_ports=studio_ports, lan=lan, token_file=token_file
    )
    if lan:
        print("[NEVEN Audiobook] WARNING: Audiobook.lan=true: el servidor esta expuesto a la red "
              "local; los endpoints /api exigen secreto, las descargas no.", file=sys.stderr)
        sys.stderr.flush()

    try:
        server = _ExclusiveThreadedServer(host, port, app)
    except (OSError, SystemExit) as e:
        # werkzeug convierte "direccion en uso" en SystemExit(1) tras imprimir su aviso.
        reason = e if isinstance(e, OSError) else "ver el aviso anterior"
        _fatal(EXIT_PORT_BUSY,
               f"el puerto {port} esta ocupado o no se puede abrir en {host} ({reason}). "
               "Cierre el programa que lo usa o cambie Audiobook.port en neven-config.json")

    print_banner(port, lan)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[NEVEN Audiobook] Servidor detenido")
    except Exception as e:
        print(f"\n[NEVEN Audiobook] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
