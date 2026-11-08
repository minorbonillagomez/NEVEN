"""
NEVEN Studio - FFmpeg M4A Muxer
Crea archivos .m4a con capítulos y portada (compatible con estéreos de carro)

Nota: M4A y M4B son el mismo formato (AAC en contenedor MP4).
Usamos .m4a porque tiene mejor compatibilidad con reproductores de auto,
mientras que .m4b a veces es ignorado por ser extensión "audiobook" de Apple.
"""

import os
import subprocess
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChapterMarker:
    """Marcador de capítulo para el archivo de audio"""
    title: str
    start_ms: int
    end_ms: int


# Extensión predeterminada para audiolibros
# Usamos .m4a en lugar de .m4b para mejor compatibilidad con reproductores de auto
DEFAULT_AUDIOBOOK_EXTENSION = ".m4a"


class FFmpegMuxer:
    """Empaquetador de audiolibros usando FFmpeg"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self):
        """Verifica que FFmpeg esté disponible"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg no encontrado")
        except FileNotFoundError:
            # Intentar rutas comunes en Windows
            home = os.path.expanduser("~")
            common_paths = [
                # WinGet installation
                os.path.join(home, r"AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"),
                # Buscar en WinGet packages dinámicamente
                *self._find_winget_ffmpeg(),
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                os.path.join(home, r"scoop\apps\ffmpeg\current\bin\ffmpeg.exe"),
            ]
            for path in common_paths:
                if path and os.path.exists(path):
                    self.ffmpeg_path = path
                    return
            raise RuntimeError("FFmpeg no encontrado. Instálalo con: winget install FFmpeg")
    
    def _find_winget_ffmpeg(self) -> list[str]:
        """Busca FFmpeg en los paquetes de WinGet"""
        winget_path = os.path.join(os.path.expanduser("~"), r"AppData\Local\Microsoft\WinGet\Packages")
        if not os.path.exists(winget_path):
            return []
        
        results = []
        for root, dirs, files in os.walk(winget_path):
            if "ffmpeg.exe" in files:
                results.append(os.path.join(root, "ffmpeg.exe"))
        return results
    
    def get_audio_duration_ms(self, audio_path: str) -> int:
        """Obtiene la duración de un archivo de audio en milisegundos"""
        result = subprocess.run(
            [
                self.ffmpeg_path, "-i", audio_path,
                "-hide_banner", "-f", "null", "-"
            ],
            capture_output=True,
            text=True
        )
        
        # Parsear duración del stderr de ffmpeg
        import re
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", result.stderr)
        if match:
            hours, mins, secs, centis = map(int, match.groups())
            return (hours * 3600 + mins * 60 + secs) * 1000 + centis * 10
        return 0
    
    def concatenate_audio(self, audio_files: list[str], output_path: str) -> bool:
        """Concatena múltiples archivos de audio en uno solo"""
        if not audio_files:
            return False
        
        # Si solo hay un archivo, simplemente copiarlo
        if len(audio_files) == 1:
            import shutil
            shutil.copy2(audio_files[0], output_path)
            return os.path.exists(output_path)
        
        # Crear archivo de lista para FFmpeg (usar rutas absolutas con formato Windows)
        list_file = output_path + ".txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for audio in audio_files:
                # Usar rutas absolutas y escapar para FFmpeg en Windows
                abs_path = os.path.abspath(audio).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        try:
            result = subprocess.run(
                [
                    self.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c", "copy",
                    "-y",
                    output_path
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"FFmpeg concat error: {result.stderr}")
            
            return result.returncode == 0
            
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)
    
    def create_chapters_metadata(self, chapters: list[ChapterMarker], output_path: str) -> str:
        """Crea archivo FFMETADATA con información de capítulos"""
        metadata_content = ";FFMETADATA1\n"
        
        for chapter in chapters:
            metadata_content += f"\n[CHAPTER]\n"
            metadata_content += f"TIMEBASE=1/1000\n"
            metadata_content += f"START={chapter.start_ms}\n"
            metadata_content += f"END={chapter.end_ms}\n"
            metadata_content += f"title={chapter.title}\n"
        
        metadata_path = output_path + ".ffmeta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(metadata_content)
        
        return metadata_path
    
    def create_m4a(
        self,
        audio_path: str,
        output_path: str,
        title: str,
        author: str,
        chapters: Optional[list[ChapterMarker]] = None,
        cover_path: Optional[str] = None,
        narrator: Optional[str] = None,
        bitrate: str = "64k"
    ) -> bool:
        """
        Crea un archivo .m4a con metadatos y capítulos
        
        Args:
            audio_path: Ruta al archivo de audio fuente (WAV o M4A)
            output_path: Ruta de salida .m4a
            title: Título del libro
            author: Autor del libro
            chapters: Lista de marcadores de capítulo
            cover_path: Ruta a imagen de portada (opcional)
            narrator: Nombre del narrador/voz TTS (opcional)
            bitrate: Bitrate de audio (default: 64k para voz)
            
        Returns:
            True si fue exitoso
        """
        
        # Construir comando FFmpeg
        cmd = [self.ffmpeg_path, "-y"]
        
        # Input de audio
        cmd.extend(["-i", audio_path])
        
        # Input de portada si existe
        if cover_path and os.path.exists(cover_path):
            cmd.extend(["-i", cover_path])
        
        # Input de metadatos de capítulos si existen
        metadata_path = None
        if chapters:
            metadata_path = self.create_chapters_metadata(chapters, output_path)
            cmd.extend(["-i", metadata_path])
        
        # Codificar a AAC
        cmd.extend([
            "-c:a", "aac",
            "-b:a", bitrate,
            "-ar", "22050",  # 22kHz es suficiente para voz
            "-ac", "1",      # Mono
        ])
        
        # Añadir portada como stream de video
        if cover_path and os.path.exists(cover_path):
            cmd.extend([
                "-c:v", "copy",
                "-disposition:v", "attached_pic",
                "-map", "0:a",
                "-map", "1:v",
            ])
        else:
            cmd.extend(["-map", "0:a"])
        
        # Mapear metadatos de capítulos
        if chapters:
            cmd.extend(["-map_metadata", "2" if cover_path else "1"])
        
        # Metadatos del libro
        cmd.extend([
            "-metadata", f"title={title}",
            "-metadata", f"artist={author}",
            "-metadata", f"album_artist={author}",
            "-metadata", f"album={title}",
            "-metadata", f"genre=Audiobook",
        ])
        
        if narrator:
            cmd.extend(["-metadata", f"composer={narrator}"])
        
        # Output
        cmd.append(output_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error FFmpeg: {result.stderr}")
                return False
            
            return os.path.exists(output_path)
            
        finally:
            # Limpiar archivo de metadatos temporal
            if metadata_path and os.path.exists(metadata_path):
                os.remove(metadata_path)
    
    def create_from_chapter_audio(
        self,
        chapter_audio_files: list[tuple[str, str, str]],  # (audio_path, title, duration_ms)
        output_path: str,
        title: str,
        author: str,
        cover_path: Optional[str] = None,
        narrator: Optional[str] = None
    ) -> bool:
        """
        Crea .m4a a partir de archivos de audio por capítulo
        
        Args:
            chapter_audio_files: Lista de tuplas (ruta_audio, titulo_capitulo)
            output_path: Ruta de salida .m4a
            ... otros metadatos
        """
        
        # Concatenar todos los audios primero
        audio_paths = [c[0] for c in chapter_audio_files]
        concat_path = output_path.replace('.m4a', '_concat.wav').replace('.m4b', '_concat.wav')
        
        if not self.concatenate_audio(audio_paths, concat_path):
            print("Error concatenando audios")
            return False
        
        # Calcular marcadores de capítulo
        chapters = []
        current_position = 0
        
        for audio_path, chapter_title, _ in chapter_audio_files:
            duration = self.get_audio_duration_ms(audio_path)
            
            chapters.append(ChapterMarker(
                title=chapter_title,
                start_ms=current_position,
                end_ms=current_position + duration
            ))
            
            current_position += duration
        
        try:
            # Crear M4A final
            return self.create_m4a(
                audio_path=concat_path,
                output_path=output_path,
                title=title,
                author=author,
                chapters=chapters,
                cover_path=cover_path,
                narrator=narrator
            )
        finally:
            # Limpiar archivo concatenado
            if os.path.exists(concat_path):
                os.remove(concat_path)
    
    # Alias para compatibilidad hacia atrás
    def create_m4b(self, *args, **kwargs) -> bool:
        """Alias de create_m4a para compatibilidad con código existente"""
        return self.create_m4a(*args, **kwargs)


if __name__ == "__main__":
    # Test básico
    muxer = FFmpegMuxer()
    print(f"✅ FFmpeg encontrado en: {muxer.ffmpeg_path}")
    
    # Verificar versión
    result = subprocess.run([muxer.ffmpeg_path, "-version"], capture_output=True, text=True)
    version_line = result.stdout.split('\n')[0]
    print(f"   {version_line}")
