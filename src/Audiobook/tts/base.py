"""
NEVEM Studio - Base TTS Engine Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class TTSVoice:
    """Representa una voz TTS disponible"""
    id: str
    name: str
    language: str
    gender: str  # "male" | "female" | "neutral"


class TTSEngine(ABC):
    """Interfaz base para motores TTS"""
    
    @abstractmethod
    def get_voices(self) -> list[TTSVoice]:
        """Retorna las voces disponibles"""
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """Establece la voz activa"""
        pass
    
    @abstractmethod
    def set_rate(self, rate: int) -> None:
        """Establece la velocidad de habla (-10 a 10)"""
        pass
    
    @abstractmethod
    def synthesize(self, text: str, output_path: str, 
                   progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """
        Sintetiza texto a archivo de audio
        
        Args:
            text: Texto a sintetizar
            output_path: Ruta del archivo .wav de salida
            progress_callback: Callback opcional para progreso (0.0 a 1.0)
            
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    def synthesize_sentences(self, sentences: list[str], output_dir: str,
                             progress_callback: Optional[Callable[[int, int], None]] = None) -> list[str]:
        """
        Sintetiza múltiples oraciones a archivos individuales
        
        Args:
            sentences: Lista de oraciones
            output_dir: Directorio de salida
            progress_callback: Callback (current, total)
            
        Returns:
            Lista de rutas de archivos generados
        """
        pass
