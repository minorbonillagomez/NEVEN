"""
NEVEM Studio - Windows SAPI TTS Engine
Usa las voces nativas de Windows (Sabina, Raul, etc.)

MEJORAS v2:
- Chunking de texto largo para evitar bloqueos
- Timeout por chunk
- Logging detallado
- Concatenación de chunks con ffmpeg
"""

import os
import re
import time
import subprocess
import threading
from typing import Optional, Callable
import pyttsx3

from .base import TTSEngine, TTSVoice


# Tamaño máximo de chunk (caracteres) para evitar bloqueos
MAX_CHUNK_SIZE = 3000  # ~500-600 palabras
CHUNK_TIMEOUT_SECONDS = 120  # 2 minutos máximo por chunk


class WindowsTTS(TTSEngine):
    """Motor TTS usando Windows SAPI (pyttsx3)"""
    
    def __init__(self):
        self.engine = pyttsx3.init('sapi5')
        self._voices: list[TTSVoice] = []
        self._current_voice_id: Optional[str] = None
        self._rate = 200  # Palabras por minuto - AUMENTADO de 150 a 200
        
        # Cargar voces disponibles
        self._load_voices()
        
        # Aplicar rate por defecto
        self.engine.setProperty('rate', self._rate)
    
    def _load_voices(self):
        """Carga las voces disponibles del sistema"""
        self._voices = []
        
        for voice in self.engine.getProperty('voices'):
            # Detectar idioma
            lang = "es" if "spanish" in voice.name.lower() or "sabina" in voice.name.lower() or "raul" in voice.name.lower() else "en"
            
            # Detectar género
            gender = "female" if any(n in voice.name.lower() for n in ['sabina', 'zira', 'helena', 'laura']) else "male"
            
            self._voices.append(TTSVoice(
                id=voice.id,
                name=voice.name,
                language=lang,
                gender=gender
            ))
        
        # Establecer voz por defecto (preferir español)
        spanish_voices = [v for v in self._voices if v.language == "es"]
        if spanish_voices:
            self.set_voice(spanish_voices[0].id)
        elif self._voices:
            self.set_voice(self._voices[0].id)
    
    def get_voices(self) -> list[TTSVoice]:
        """Retorna las voces disponibles"""
        return self._voices
    
    def set_voice(self, voice_id: str) -> bool:
        """Establece la voz activa"""
        try:
            self.engine.setProperty('voice', voice_id)
            self._current_voice_id = voice_id
            return True
        except Exception as e:
            print(f"Error estableciendo voz: {e}")
            return False
    
    def set_rate(self, rate: int) -> None:
        """Establece la velocidad de habla (palabras por minuto, 50-300)"""
        self._rate = max(50, min(300, rate))
        self.engine.setProperty('rate', self._rate)
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Divide texto en oraciones"""
        # Patrón para detectar fin de oración
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)
        
        # Filtrar oraciones vacías y muy cortas
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        return sentences
    
    def _split_into_chunks(self, text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
        """
        Divide texto en chunks manejables, respetando límites de oraciones
        
        Args:
            text: Texto a dividir
            max_size: Tamaño máximo de cada chunk en caracteres
        
        Returns:
            Lista de chunks de texto
        """
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # Si la oración sola es muy larga, dividirla por comas o punto y coma
            if sentence_size > max_size:
                # Guardar chunk actual
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Dividir oración larga
                sub_parts = re.split(r'(?<=[,;:])\s+', sentence)
                for part in sub_parts:
                    if len(part) > max_size:
                        # Dividir por palabras si aún es muy largo
                        words = part.split()
                        temp_chunk = []
                        temp_size = 0
                        for word in words:
                            if temp_size + len(word) + 1 > max_size:
                                if temp_chunk:
                                    chunks.append(" ".join(temp_chunk))
                                temp_chunk = [word]
                                temp_size = len(word)
                            else:
                                temp_chunk.append(word)
                                temp_size += len(word) + 1
                        if temp_chunk:
                            chunks.append(" ".join(temp_chunk))
                    else:
                        chunks.append(part)
            elif current_size + sentence_size + 1 > max_size:
                # Guardar chunk actual y empezar nuevo
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1
        
        # Agregar último chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _synthesize_with_timeout(self, text: str, output_path: str, 
                                  timeout: int = CHUNK_TIMEOUT_SECONDS) -> bool:
        """
        Sintetiza con timeout para evitar bloqueos infinitos
        
        Args:
            text: Texto a sintetizar
            output_path: Ruta del archivo de salida
            timeout: Timeout en segundos
        
        Returns:
            True si tuvo éxito, False si falló o expiró timeout
        """
        result = {"success": False, "error": None}
        
        def synthesize_thread():
            try:
                # Reiniciar engine para evitar estado corrupto
                self.engine = pyttsx3.init('sapi5')
                if self._current_voice_id:
                    self.engine.setProperty('voice', self._current_voice_id)
                self.engine.setProperty('rate', self._rate)
                
                self.engine.save_to_file(text, output_path)
                self.engine.runAndWait()
                result["success"] = os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception as e:
                result["error"] = str(e)
                result["success"] = False
        
        thread = threading.Thread(target=synthesize_thread)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            print(f"   [!] Timeout después de {timeout}s - chunk muy largo")
            # No podemos matar el thread de pyttsx3, pero al menos continuamos
            return False
        
        if result["error"]:
            print(f"   [!] Error: {result['error']}")
        
        return result["success"]
    
    def _concatenate_audio_files(self, audio_files: list[str], output_path: str) -> bool:
        """
        Concatena múltiples archivos WAV en uno solo usando ffmpeg
        
        Args:
            audio_files: Lista de rutas a archivos WAV
            output_path: Ruta del archivo de salida
        
        Returns:
            True si tuvo éxito
        """
        if not audio_files:
            return False
        
        if len(audio_files) == 1:
            # Solo un archivo, copiar directamente
            import shutil
            shutil.copy(audio_files[0], output_path)
            return True
        
        try:
            # Crear archivo de lista para ffmpeg
            list_file = output_path + ".txt"
            with open(list_file, "w", encoding="utf-8") as f:
                for audio in audio_files:
                    # Escapar comillas simples en la ruta
                    safe_path = audio.replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")
            
            # Concatenar con ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Limpiar archivo de lista
            if os.path.exists(list_file):
                os.remove(list_file)
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            print(f"   [!] Error concatenando audio: {e}")
            return False
    
    def synthesize(self, text: str, output_path: str,
                   progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """Sintetiza texto completo a un archivo WAV"""
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Si el texto es corto, sintetizar directamente
            if len(text) <= MAX_CHUNK_SIZE:
                return self._synthesize_with_timeout(text, output_path)
            
            # Dividir en chunks
            chunks = self._split_into_chunks(text)
            print(f"   [Chunking] Texto dividido en {len(chunks)} partes")
            
            # Sintetizar cada chunk
            chunk_files = []
            temp_dir = os.path.dirname(output_path)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            
            for i, chunk in enumerate(chunks):
                chunk_path = os.path.join(temp_dir, f"{base_name}_chunk_{i:03d}.wav")
                
                start_time = time.time()
                print(f"   [Chunk {i+1}/{len(chunks)}] {len(chunk)} chars...", end=" ", flush=True)
                
                if self._synthesize_with_timeout(chunk, chunk_path):
                    elapsed = time.time() - start_time
                    chunk_files.append(chunk_path)
                    print(f"OK ({elapsed:.1f}s)")
                else:
                    print("FALLÓ - saltando")
                
                if progress_callback:
                    progress_callback((i + 1) / len(chunks))
            
            if not chunk_files:
                print("   [!] No se pudo sintetizar ningún chunk")
                return False
            
            # Concatenar todos los chunks
            print(f"   [Concat] Uniendo {len(chunk_files)} archivos...")
            success = self._concatenate_audio_files(chunk_files, output_path)
            
            # Limpiar archivos temporales de chunks
            for chunk_file in chunk_files:
                try:
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                except:
                    pass
            
            return success
            
        except Exception as e:
            print(f"Error sintetizando audio: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def synthesize_sentences(self, sentences: list[str], output_dir: str,
                             progress_callback: Optional[Callable[[int, int], None]] = None) -> list[str]:
        """Sintetiza oraciones individuales"""
        os.makedirs(output_dir, exist_ok=True)
        output_files = []
        total = len(sentences)
        
        for i, sentence in enumerate(sentences):
            output_path = os.path.join(output_dir, f"sentence_{i:05d}.wav")
            
            try:
                if self._synthesize_with_timeout(sentence, output_path, timeout=30):
                    output_files.append(output_path)
                    
            except Exception as e:
                print(f"Error sintetizando oración {i}: {e}")
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return output_files
    
    def synthesize_chapter(self, chapter_text: str, output_path: str,
                           progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Sintetiza un capítulo completo con chunking inteligente
        """
        word_count = len(chapter_text.split())
        print(f"   [{word_count} palabras, {len(chapter_text)} caracteres]")
        
        return self.synthesize(chapter_text, output_path, progress_callback)
    
    def get_current_voice(self) -> Optional[TTSVoice]:
        """Retorna la voz actual"""
        if self._current_voice_id:
            for v in self._voices:
                if v.id == self._current_voice_id:
                    return v
        return None


if __name__ == "__main__":
    # Test del motor TTS
    tts = WindowsTTS()
    
    print("🎤 Voces disponibles:")
    for voice in tts.get_voices():
        current = "← actual" if voice.id == tts._current_voice_id else ""
        print(f"  [{voice.language}] {voice.name} ({voice.gender}) {current}")
    
    # Test de síntesis
    test_text = "Hola, soy Nevem Studio. Estoy listo para convertir tus libros en audiolibros."
    output_file = "test_output.wav"
    
    print(f"\n🔊 Sintetizando prueba...")
    if tts.synthesize(test_text, output_file):
        print(f"✅ Audio guardado en: {output_file}")
        
        # Obtener tamaño
        size = os.path.getsize(output_file)
        print(f"   Tamaño: {size / 1024:.1f} KB")
    else:
        print("❌ Error en síntesis")
