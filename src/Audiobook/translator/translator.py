"""
NEVEN AudioLibro - Translation Module
Supports online (DeepL) and offline (Argos) translation
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from abc import ABC, abstractmethod


class TranslationEngine(Enum):
    """Available translation engines"""
    DEEPL = "deepl"           # Online, high quality
    ARGOS = "argos"           # Offline, local models


# Supported language pairs
SUPPORTED_LANGUAGES = {
    "es": "Spanish",
    "en": "English",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
}


@dataclass
class TranslationResult:
    """Result of a translation operation"""
    success: bool
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    engine: str
    error_message: Optional[str] = None


class BaseTranslator(ABC):
    """Base class for translation engines"""
    
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    def get_supported_pairs(self) -> List[tuple]:
        pass


class DeepLTranslator(BaseTranslator):
    """
    DeepL API translator (online, high quality)
    Free tier: 500,000 characters/month
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPL_API_KEY")
        self._translator = None
        
        if self.api_key:
            try:
                import deepl
                self._translator = deepl.Translator(self.api_key)
            except Exception as e:
                print(f"DeepL init error: {e}")
    
    def is_available(self) -> bool:
        return self._translator is not None
    
    def get_supported_pairs(self) -> List[tuple]:
        """DeepL supports all combinations of these languages"""
        langs = ["ES", "EN", "FR", "DE", "IT", "PT", "RU", "ZH", "JA", "KO"]
        pairs = []
        for src in langs:
            for tgt in langs:
                if src != tgt:
                    pairs.append((src.lower(), tgt.lower()))
        return pairs
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if not self.is_available():
            return TranslationResult(
                success=False,
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine="deepl",
                error_message="DeepL API key not configured"
            )
        
        try:
            # DeepL uses uppercase language codes
            src = source_lang.upper() if source_lang else None
            tgt = target_lang.upper()
            
            # Special handling for English variants
            if tgt == "EN":
                tgt = "EN-US"
            if tgt == "PT":
                tgt = "PT-BR"
            
            result = self._translator.translate_text(
                text,
                source_lang=src,
                target_lang=tgt
            )
            
            return TranslationResult(
                success=True,
                original_text=text,
                translated_text=result.text,
                source_lang=source_lang,
                target_lang=target_lang,
                engine="deepl"
            )
            
        except Exception as e:
            return TranslationResult(
                success=False,
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine="deepl",
                error_message=str(e)
            )


class ArgosTranslator(BaseTranslator):
    """
    Argos Translate (offline, local models)
    Models are ~100MB per language pair
    """
    
    def __init__(self):
        self._initialized = False
        self._installed_packages = []
        self._init_argos()
    
    def _init_argos(self):
        try:
            import argostranslate.package
            import argostranslate.translate
            
            # Get installed packages
            self._installed_packages = argostranslate.package.get_installed_packages()
            self._initialized = True
            
        except Exception as e:
            print(f"Argos init error: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        return self._initialized
    
    def get_supported_pairs(self) -> List[tuple]:
        """Returns installed language pairs"""
        pairs = []
        for pkg in self._installed_packages:
            pairs.append((pkg.from_code, pkg.to_code))
        return pairs
    
    def get_available_packages(self) -> List[dict]:
        """Returns packages available for download"""
        if not self._initialized:
            return []
        
        try:
            import argostranslate.package
            
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            
            return [
                {
                    "from_code": pkg.from_code,
                    "from_name": pkg.from_name,
                    "to_code": pkg.to_code,
                    "to_name": pkg.to_name,
                    "size_mb": getattr(pkg, 'size', 0) / 1024 / 1024 if hasattr(pkg, 'size') else 100
                }
                for pkg in available
            ]
        except Exception as e:
            print(f"Error getting available packages: {e}")
            return []
    
    def download_package(self, from_code: str, to_code: str, 
                         progress_callback=None) -> bool:
        """Downloads a translation model"""
        if not self._initialized:
            return False
        
        try:
            import argostranslate.package
            
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            
            # Find the package
            pkg = next(
                (p for p in available 
                 if p.from_code == from_code and p.to_code == to_code),
                None
            )
            
            if pkg is None:
                print(f"Package {from_code}->{to_code} not found")
                return False
            
            # Download and install
            download_path = pkg.download()
            argostranslate.package.install_from_path(download_path)
            
            # Refresh installed packages
            self._installed_packages = argostranslate.package.get_installed_packages()
            
            return True
            
        except Exception as e:
            print(f"Error downloading package: {e}")
            return False
    
    def is_pair_installed(self, from_code: str, to_code: str) -> bool:
        """Check if a language pair is installed"""
        return (from_code, to_code) in self.get_supported_pairs()
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if not self.is_available():
            return TranslationResult(
                success=False,
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine="argos",
                error_message="Argos Translate not initialized"
            )
        
        try:
            import argostranslate.translate
            
            translated = argostranslate.translate.translate(
                text, 
                source_lang, 
                target_lang
            )
            
            return TranslationResult(
                success=True,
                original_text=text,
                translated_text=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                engine="argos"
            )
            
        except Exception as e:
            return TranslationResult(
                success=False,
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                engine="argos",
                error_message=str(e)
            )


class UnifiedTranslator:
    """
    Unified translator that can use DeepL or Argos
    Falls back to Argos if DeepL unavailable
    """
    
    def __init__(self, deepl_api_key: Optional[str] = None):
        self.deepl = DeepLTranslator(api_key=deepl_api_key)
        self.argos = ArgosTranslator()
    
    def translate(self, text: str, source_lang: str, target_lang: str,
                  engine: TranslationEngine = TranslationEngine.DEEPL,
                  progress_callback=None) -> TranslationResult:
        """
        Translate text using specified engine
        Falls back to other engine if primary unavailable
        """
        
        # Split text into chunks for progress reporting
        # (important for long texts like books)
        chunk_size = 5000  # characters per chunk
        
        if len(text) <= chunk_size:
            # Short text, translate directly
            return self._translate_chunk(text, source_lang, target_lang, engine)
        
        # Long text, translate in chunks
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        translated_chunks = []
        
        for i, chunk in enumerate(chunks):
            result = self._translate_chunk(chunk, source_lang, target_lang, engine)
            
            if not result.success:
                return result
            
            translated_chunks.append(result.translated_text)
            
            if progress_callback:
                progress_callback((i + 1) / len(chunks))
        
        return TranslationResult(
            success=True,
            original_text=text,
            translated_text="".join(translated_chunks),
            source_lang=source_lang,
            target_lang=target_lang,
            engine=engine.value
        )
    
    def _translate_chunk(self, text: str, source_lang: str, target_lang: str,
                         engine: TranslationEngine) -> TranslationResult:
        """Translate a single chunk of text"""
        
        if engine == TranslationEngine.DEEPL:
            if self.deepl.is_available():
                result = self.deepl.translate(text, source_lang, target_lang)
                if result.success:
                    return result
            
            # Fallback to Argos
            if self.argos.is_available():
                if self.argos.is_pair_installed(source_lang, target_lang):
                    return self.argos.translate(text, source_lang, target_lang)
        
        elif engine == TranslationEngine.ARGOS:
            if self.argos.is_available():
                if self.argos.is_pair_installed(source_lang, target_lang):
                    return self.argos.translate(text, source_lang, target_lang)
            
            # Fallback to DeepL
            if self.deepl.is_available():
                return self.deepl.translate(text, source_lang, target_lang)
        
        return TranslationResult(
            success=False,
            original_text=text,
            translated_text="",
            source_lang=source_lang,
            target_lang=target_lang,
            engine=engine.value,
            error_message="No translation engine available for this language pair"
        )
    
    def get_status(self) -> dict:
        """Get status of translation engines"""
        return {
            "deepl": {
                "available": self.deepl.is_available(),
                "type": "online",
                "quality": "high"
            },
            "argos": {
                "available": self.argos.is_available(),
                "type": "offline",
                "quality": "medium",
                "installed_pairs": self.argos.get_supported_pairs()
            }
        }
    
    def download_argos_model(self, from_code: str, to_code: str,
                             progress_callback=None) -> bool:
        """Download an Argos translation model"""
        return self.argos.download_package(from_code, to_code, progress_callback)


# Convenience functions
def detect_language(text: str) -> str:
    """
    Simple language detection based on common words
    For production, use langdetect or similar library
    """
    text_lower = text.lower()
    
    # Simple heuristics
    spanish_words = ["el", "la", "de", "que", "en", "es", "un", "una", "los", "las"]
    english_words = ["the", "of", "and", "to", "in", "is", "it", "for", "on", "with"]
    french_words = ["le", "la", "de", "et", "en", "un", "une", "les", "des", "est"]
    german_words = ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "ist"]
    
    words = text_lower.split()[:100]  # Check first 100 words
    
    scores = {
        "es": sum(1 for w in words if w in spanish_words),
        "en": sum(1 for w in words if w in english_words),
        "fr": sum(1 for w in words if w in french_words),
        "de": sum(1 for w in words if w in german_words),
    }
    
    return max(scores, key=scores.get)


if __name__ == "__main__":
    # Test
    translator = UnifiedTranslator()
    
    print("Translation Status:")
    print(translator.get_status())
    
    # Test Argos (if models installed)
    test_text = "Hello, how are you today?"
    result = translator.translate(test_text, "en", "es", TranslationEngine.ARGOS)
    print(f"\nArgos: {test_text} -> {result.translated_text}")
    print(f"Success: {result.success}, Error: {result.error_message}")
