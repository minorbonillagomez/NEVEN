"""
NEVEM Studio - Piper TTS Engine
Motor TTS neural offline usando modelos ONNX
"""

import os
import json
import wave
import urllib.request
from typing import Optional, Callable
from pathlib import Path

from .base import TTSEngine, TTSVoice

# Configuración de modelos disponibles
PIPER_VOICES = {
    "es_MX-claude-high": {
        "name": "Claude (México)",
        "language": "es-MX",
        "gender": "male",
        "quality": "high",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high",
        "files": ["es_MX-claude-high.onnx", "es_MX-claude-high.onnx.json"]
    },
    "es_MX-ald-medium": {
        "name": "Ald (México)",
        "language": "es-MX", 
        "gender": "male",
        "quality": "medium",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium",
        "files": ["es_MX-ald-medium.onnx", "es_MX-ald-medium.onnx.json"]
    },
    "es_ES-davefx-medium": {
        "name": "Dave (España)",
        "language": "es-ES",
        "gender": "male", 
        "quality": "medium",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium",
        "files": ["es_ES-davefx-medium.onnx", "es_ES-davefx-medium.onnx.json"]
    },
}


class PiperTTS(TTSEngine):
    """Motor TTS usando Piper (ONNX, 100% offline)"""
    
    def __init__(self, models_dir: Optional[str] = None, default_voice: str = "es_MX-claude-high"):
        self.models_dir = models_dir or os.path.join(os.path.dirname(__file__), "..", "..", "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        self._voices: list[TTSVoice] = []
        self._current_voice_id: str = default_voice
        self._voice_model = None
        self._synthesizer = None
        self._rate = 1.0  # Multiplicador de velocidad
        
        self._load_voices()
    
    def _load_voices(self):
        """Carga las voces disponibles"""
        self._voices = []
        for voice_id, info in PIPER_VOICES.items():
            self._voices.append(TTSVoice(
                id=voice_id,
                name=info["name"],
                language=info["language"],
                gender=info["gender"]
            ))
    
    def _download_model(self, voice_id: str, progress_callback: Optional[Callable[[str, float], None]] = None) -> bool:
        """Descarga el modelo de voz si no existe"""
        if voice_id not in PIPER_VOICES:
            print(f"Voz no encontrada: {voice_id}")
            return False
        
        voice_info = PIPER_VOICES[voice_id]
        model_path = os.path.join(self.models_dir, voice_info["files"][0])
        
        # Si ya existe, no descargar
        if os.path.exists(model_path) and os.path.getsize(model_path) > 1000000:  # >1MB
            return True
        
        print(f"\n📥 Descargando modelo Piper: {voice_info['name']}...")
        
        for i, filename in enumerate(voice_info["files"]):
            url = f"{voice_info['url_base']}/{filename}"
            local_path = os.path.join(self.models_dir, filename)
            
            try:
                print(f"   [{i+1}/{len(voice_info['files'])}] {filename}...")
                
                # Descargar con progreso
                def show_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = min(100, block_num * block_size * 100 / total_size)
                        if progress_callback:
                            progress_callback(filename, percent / 100)
                
                urllib.request.urlretrieve(url, local_path, show_progress)
                print(f"       ✅ OK")
                
            except Exception as e:
                print(f"       ❌ Error: {e}")
                return False
        
        return True
    
    def _load_model(self, voice_id: str) -> bool:
        """Carga el modelo en memoria"""
        try:
            from piper import PiperVoice
            
            if voice_id not in PIPER_VOICES:
                return False
            
            voice_info = PIPER_VOICES[voice_id]
            model_path = os.path.join(self.models_dir, voice_info["files"][0])
            config_path = os.path.join(self.models_dir, voice_info["files"][1])
            
            if not os.path.exists(model_path):
                if not self._download_model(voice_id):
                    return False
            
            print(f"🔊 Cargando modelo Piper: {voice_info['name']}...")
            self._voice_model = PiperVoice.load(model_path, config_path)
            print(f"   ✅ Modelo cargado")
            return True
            
        except ImportError:
            print("❌ piper-tts no instalado. Ejecuta: pip install piper-tts")
            return False
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            return False
    
    def get_voices(self) -> list[TTSVoice]:
        """Retorna las voces disponibles"""
        return self._voices
    
    def set_voice(self, voice_id: str) -> bool:
        """Establece la voz activa"""
        if voice_id in PIPER_VOICES:
            self._current_voice_id = voice_id
            self._voice_model = None  # Forzar recarga
            return True
        return False
    
    def set_rate(self, rate: int) -> None:
        """
        Establece la velocidad de habla
        rate: -50 a +50 (se convierte a multiplicador 0.5x a 2.0x)
        """
        # Convertir de -50/+50 a multiplicador
        self._rate = 1.0 + (rate / 100.0)
        self._rate = max(0.5, min(2.0, self._rate))
    
    def synthesize(self, text: str, output_path: str,
                   progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """Sintetiza texto a archivo WAV"""
        try:
            # Asegurar modelo cargado
            if self._voice_model is None:
                if not self._load_model(self._current_voice_id):
                    return False
            
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            
            # Sintetizar con Piper
            with wave.open(output_path, "wb") as wav_file:
                self._voice_model.synthesize(text, wav_file)
            
            if progress_callback:
                progress_callback(1.0)
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"Error sintetizando con Piper: {e}")
            return False
    
    def synthesize_sentences(self, sentences: list[str], output_dir: str,
                             progress_callback: Optional[Callable[[int, int], None]] = None) -> list[str]:
        """Sintetiza oraciones individuales"""
        os.makedirs(output_dir, exist_ok=True)
        output_files = []
        total = len(sentences)
        
        # Asegurar modelo cargado
        if self._voice_model is None:
            if not self._load_model(self._current_voice_id):
                return []
        
        for i, sentence in enumerate(sentences):
            output_path = os.path.join(output_dir, f"sentence_{i:05d}.wav")
            
            try:
                with wave.open(output_path, "wb") as wav_file:
                    self._voice_model.synthesize(sentence, wav_file)
                output_files.append(output_path)
            except Exception as e:
                print(f"Error sintetizando oración {i}: {e}")
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return output_files
    
    def synthesize_chapter(self, chapter_text: str, output_path: str,
                           progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """Sintetiza un capítulo completo"""
        return self.synthesize(chapter_text, output_path, progress_callback)
    
    def get_current_voice(self) -> Optional[TTSVoice]:
        """Retorna la voz actual"""
        for v in self._voices:
            if v.id == self._current_voice_id:
                return v
        return None
    
    def is_model_downloaded(self, voice_id: Optional[str] = None) -> bool:
        """Verifica si el modelo está descargado"""
        vid = voice_id or self._current_voice_id
        if vid not in PIPER_VOICES:
            return False
        
        voice_info = PIPER_VOICES[vid]
        model_path = os.path.join(self.models_dir, voice_info["files"][0])
        return os.path.exists(model_path) and os.path.getsize(model_path) > 1000000


if __name__ == "__main__":
    print("=" * 50)
    print("NEVEM Studio - Test Piper TTS (Offline)")
    print("=" * 50)
    
    tts = PiperTTS()
    
    print("\n🎤 Voces Piper disponibles:")
    for v in tts.get_voices():
        downloaded = "✓" if tts.is_model_downloaded(v.id) else "↓"
        current = " <- actual" if v.id == tts._current_voice_id else ""
        print(f"  [{downloaded}] [{v.language}] {v.name} ({v.gender}){current}")
    
    # Test de síntesis
    print("\n🔊 Probando síntesis offline...")
    test_text = "Hola, soy Piper. Una voz neural que funciona sin conexión a internet."
    
    os.makedirs('temp', exist_ok=True)
    output_file = 'temp/test_piper.wav'
    
    if tts.synthesize(test_text, output_file):
        size = os.path.getsize(output_file)
        print(f"✅ Éxito! Archivo: {output_file} ({size/1024:.1f} KB)")
    else:
        print("❌ Error en síntesis")
    
    print("\n" + "=" * 50)
