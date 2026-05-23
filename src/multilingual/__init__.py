"""
Multilingual Support Module
Phase 6: Arabic and French language support
"""

from .language_detector import LanguageDetector, detect_language
from .multilingual_embeddings import MultilingualEmbeddings, get_multilingual_embeddings

__all__ = [
    'LanguageDetector',
    'detect_language',
    'MultilingualEmbeddings',
    'get_multilingual_embeddings',
]
