"""
NEVEM Studio - Edge TTS Engine
Usa las voces neurales de Microsoft Azure (gratis, requiere internet)
"""

import os
import asyncio
from typing import Optional, Callable
import edge_tts

from .base import TTSEngine, TTSVoice


# Voces recomendadas en español
SPANISH_VOICES = {
    # México
    "es-MX-DaliaNeural": ("Dalia", "es-MX", "female"),      # Muy natural
    "es-MX-JorgeNeural": ("Jorge", "es-MX", "male"),        # Natural
    
    # España  
    "es-ES-ElviraNeural": ("Elvira", "es-ES", "female"),    # Muy natural
    "es-ES-AlvaroNeural": ("Álvaro", "es-ES", "male"),      # Natural
    
    # Argentina
    "es-AR-ElenaNeural": ("Elena", "es-AR", "female"),
    "es-AR-TomasNeural": ("Tomás", "es-AR", "male"),
    
    # Colombia
    "es-CO-SalomeNeural": ("Salomé", "es-CO", "female"),
    "es-CO-GonzaloNeural": ("Gonzalo", "es-CO", "male"),
}


class EdgeTTS(TTSEngine):
    """Motor TTS usando Microsoft Edge/Azure Neural Voices"""
    
    def __init__(self, default_voice: str = "es-MX-DaliaNeural"):
        self._voices: list[TTSVoice] = []
        self._current_voice_id: str = default_voice
        self._rate = "+0%"  # Modificador de velocidad
        self._pitch = "+0Hz"  # Modificador de tono
        
        # Cargar voces predefinidas
        self._load_voices()
    
    def _load_voices(self):
        """Carga las voces disponibles"""
        self._voices = []
        
        for voice_id, (name, lang, gender) in SPANISH_VOICES.items():
            self._voices.append(TTSVoice(
                id=voice_id,
                name=name,
                language=lang,
                gender=gender
            ))
    
    async def _fetch_all_voices(self) -> list[TTSVoice]:
        """Obtiene todas las voces disponibles de Edge TTS"""
        voices = await edge_tts.list_voices()
        result = []
        
        for v in voices:
            if v["Locale"].startswith("es-"):
                result.append(TTSVoice(
                    id=v["ShortName"],
                    name=v["FriendlyName"],
                    language=v["Locale"],
                    gender=v["Gender"].lower()
                ))
        
        return result
    
    def get_voices(self) -> list[TTSVoice]:
        """Retorna las voces disponibles"""
        return self._voices
    
    def set_voice(self, voice_id: str) -> bool:
        """Establece la voz activa"""
        self._current_voice_id = voice_id
        return True
    
    def set_rate(self, rate: int) -> None:
        """
        Establece la velocidad de habla
        rate: -100 a +100 (porcentaje de cambio)
        """
        if rate >= 0:
            self._rate = f"+{rate}%"
        else:
            self._rate = f"{rate}%"
    
    def set_pitch(self, pitch: int) -> None:
        """
        Establece el tono de voz
        pitch: -50 a +50 Hz
        """
        if pitch >= 0:
            self._pitch = f"+{pitch}Hz"
        else:
            self._pitch = f"{pitch}Hz"
    
    async def _synthesize_async(self, text: str, output_path: str) -> bool:
        """Síntesis asíncrona"""
        try:
            communicate = edge_tts.Communicate(
                text,
                self._current_voice_id,
                rate=self._rate,
                pitch=self._pitch
            )
            await communicate.save(output_path)
            return os.path.exists(output_path)
        except Exception as e:
            print(f"Error en Edge TTS: {e}")
            return False
    
    async def _synthesize_ssml_async(self, ssml: str, output_path: str) -> bool:
        """Síntesis asíncrona con SSML para múltiples idiomas"""
        try:
            # Edge TTS con SSML completo
            communicate = edge_tts.Communicate(ssml)
            await communicate.save(output_path)
            return os.path.exists(output_path)
        except Exception as e:
            print(f"Error en Edge TTS SSML: {e}")
            return False
    
    def synthesize_ssml(self, ssml: str, output_path: str,
                        progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """Sintetiza SSML a un archivo MP3 (soporta múltiples idiomas/voces)"""
        try:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            # Ejecutar síntesis asíncrona
            result = asyncio.run(self._synthesize_ssml_async(ssml, output_path))
            
            if progress_callback:
                progress_callback(1.0)
            
            return result
            
        except Exception as e:
            print(f"Error sintetizando SSML: {e}")
            return False
    
    def synthesize(self, text: str, output_path: str,
                   progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """Sintetiza texto completo a un archivo MP3"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Ejecutar síntesis asíncrona
            result = asyncio.run(self._synthesize_async(text, output_path))
            
            if progress_callback:
                progress_callback(1.0)
            
            return result
            
        except Exception as e:
            print(f"Error sintetizando audio: {e}")
            return False
    
    def synthesize_sentences(self, sentences: list[str], output_dir: str,
                             progress_callback: Optional[Callable[[int, int], None]] = None) -> list[str]:
        """Sintetiza oraciones individuales"""
        os.makedirs(output_dir, exist_ok=True)
        output_files = []
        total = len(sentences)
        
        for i, sentence in enumerate(sentences):
            output_path = os.path.join(output_dir, f"sentence_{i:05d}.mp3")
            
            try:
                if asyncio.run(self._synthesize_async(sentence, output_path)):
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


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("NEVEM Studio - Test Edge TTS")
    print("=" * 50)
    
    tts = EdgeTTS()
    
    print("\n🎤 Voces disponibles:")
    for v in tts.get_voices():
        current = " <- actual" if v.id == tts._current_voice_id else ""
        print(f"  [{v.language}] {v.name} ({v.gender}){current}")
    
    # Test de síntesis
    print("\n🔊 Probando síntesis con voz neural...")
    test_text = """
    Bienvenido a Nevem Studio. Este es un ejemplo de síntesis de voz neural 
    usando Microsoft Edge. La voz que estás escuchando es Dalia, una voz 
    mexicana que suena muy natural y fluida.
    """
    
    os.makedirs('temp', exist_ok=True)
    output_file = 'temp/test_edge_tts.mp3'
    
    if tts.synthesize(test_text.strip(), output_file):
        size = os.path.getsize(output_file)
        print(f"✅ Éxito! Archivo: {output_file} ({size/1024:.1f} KB)")
    else:
        print("❌ Error en síntesis")
    
    print("\n" + "=" * 50)
