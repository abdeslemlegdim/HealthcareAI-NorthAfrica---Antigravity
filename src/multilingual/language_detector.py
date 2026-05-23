"""
Language Detection Module
Phase 6: Detect query language (English, Arabic, French)
"""

import logging
from typing import Optional, Dict
from dataclasses import dataclass

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for langdetect
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available. Install: pip install langdetect")


@dataclass
class LanguageResult:
    """Language detection result"""
    language: str  # 'en', 'ar', 'fr'
    language_name: str  # 'English', 'Arabic', 'French'
    confidence: float  # 0.0 to 1.0
    supported: bool  # Whether language is supported


class LanguageDetector:
    """
    Language Detection for Medical Queries
    
    Supports:
    - English (en)
    - Arabic (ar)
    - French (fr)
    """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'ar': 'Arabic',
        'fr': 'French'
    }
    
    # Common medical keywords for fallback detection
    MEDICAL_KEYWORDS = {
        'en': ['pain', 'fever', 'cough', 'treatment', 'symptoms', 'disease', 'doctor', 'medicine'],
        'ar': ['ألم', 'حمى', 'سعال', 'علاج', 'أعراض', 'مرض', 'طبيب', 'دواء'],
        'fr': ['douleur', 'fièvre', 'toux', 'traitement', 'symptômes', 'maladie', 'médecin', 'médicament']
    }
    
    def __init__(self):
        """Initialize language detector"""
        self.available = LANGDETECT_AVAILABLE
        if not self.available:
            logger.warning("Language detection will use fallback method")
    
    def detect(self, text: str) -> LanguageResult:
        """
        Detect language of text
        
        Args:
            text: Input text to detect
            
        Returns:
            LanguageResult with detected language
        """
        if not text or len(text.strip()) < 3:
            # Default to English for very short text
            return LanguageResult(
                language='en',
                language_name='English',
                confidence=0.5,
                supported=True
            )
        
        # Try langdetect library
        if self.available:
            try:
                lang_code = detect(text)
                
                # Map to our supported languages
                if lang_code not in self.SUPPORTED_LANGUAGES:
                    # Check if it's a variant (e.g., 'en-US' -> 'en')
                    base_lang = lang_code.split('-')[0]
                    if base_lang in self.SUPPORTED_LANGUAGES:
                        lang_code = base_lang
                    else:
                        # Unsupported language, default to English
                        return LanguageResult(
                            language='en',
                            language_name='English',
                            confidence=0.7,
                            supported=True
                        )
                
                return LanguageResult(
                    language=lang_code,
                    language_name=self.SUPPORTED_LANGUAGES[lang_code],
                    confidence=0.9,
                    supported=True
                )
                
            except LangDetectException:
                logger.warning(f"Language detection failed for text: {text[:50]}...")
                return self._fallback_detect(text)
        else:
            # Use fallback method
            return self._fallback_detect(text)
    
    def _fallback_detect(self, text: str) -> LanguageResult:
        """
        Fallback language detection using character patterns and keywords
        
        Args:
            text: Input text
            
        Returns:
            LanguageResult
        """
        text_lower = text.lower()
        
        # Check for Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars > len(text) * 0.3:  # 30% Arabic characters
            return LanguageResult(
                language='ar',
                language_name='Arabic',
                confidence=0.8,
                supported=True
            )
        
        # Check for French keywords and accents
        french_chars = sum(1 for c in text if c in 'àâäéèêëïîôùûüÿæœç')
        french_keywords = sum(1 for kw in self.MEDICAL_KEYWORDS['fr'] if kw in text_lower)
        
        if french_chars > 0 or french_keywords > 0:
            return LanguageResult(
                language='fr',
                language_name='French',
                confidence=0.7,
                supported=True
            )
        
        # Default to English
        return LanguageResult(
            language='en',
            language_name='English',
            confidence=0.6,
            supported=True
        )
    
    def is_supported(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in self.SUPPORTED_LANGUAGES
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get all supported languages"""
        return self.SUPPORTED_LANGUAGES.copy()


# Singleton instance
_detector = None

def detect_language(text: str) -> LanguageResult:
    """
    Detect language of text (convenience function)
    
    Args:
        text: Input text
        
    Returns:
        LanguageResult
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    return _detector.detect(text)
