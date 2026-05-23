"""
Medical RAG (Retrieval-Augmented Generation) System

Hybrid retrieval combining:
- Dense retrieval (FAISS vector search)
- Sparse retrieval (BM25 keyword matching)
- Cross-encoder reranking
- Multi-lingual support (Arabic, French, English) - Phase 6
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import re
import unicodedata

try:
    from langdetect import detect as _langdetect_detect
    LANGDETECT_AVAILABLE = True
except Exception:
    LANGDETECT_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator as _DeepTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except Exception:
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except Exception:
    BM25_AVAILABLE = False

from src.utils.logger import setup_logger
from .knowledge_base import MEDICAL_KNOWLEDGE, get_disease_info, search_symptoms

logger = setup_logger(__name__)

ARABIC_QUERY_HINTS = {
    "اعراض": "symptoms",
    "عرض": "symptoms",
    "علامات": "symptoms signs",
    "سبب": "cause",
    "اسباب": "causes",
    "علاج": "treatment",
    "معالجة": "treatment",
    "تشخيص": "diagnosis",
    "وقاية": "prevention",
    "حمى": "fever",
    "سعال": "cough",
    "التهاب": "infection inflammation",
    "ضيق": "shortness breath",
    "تنفس": "breathing",
    "ألم": "pain",
    "صدر": "chest",
    "سكري": "diabetes",
    "سل": "tuberculosis",
    "رئة": "lung",
    "قلب": "heart",
}

FRENCH_QUERY_HINTS = {
    "symptomes": "symptoms",
    "signe": "sign",
    "causes": "causes",
    "cause": "cause",
    "traitement": "treatment",
    "diagnostic": "diagnosis",
    "prevention": "prevention",
    "prevenir": "prevention",
    "fievre": "fever",
    "toux": "cough",
    "douleur": "pain",
    "respiration": "breathing",
    "essoufflement": "shortness breath",
    "diabete": "diabetes",
    "tuberculose": "tuberculosis",
    "poumon": "lung",
    "coeur": "heart",
    "infection": "infection",
}

ARABIC_STOPWORDS = {
    "ما", "هي", "هل", "في", "من", "على", "و", "او", "عن", "الى", "ل", "هذا", "هذه", "ذلك", "تلك",
}

FRENCH_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou", "pour", "dans", "avec", "sur",
    "que", "qui", "quoi", "est", "sont", "ce", "cette", "ces", "au", "aux",
}

QUERY_NORMALIZATION_MAP = {
    "hand break": "hand injury",
    "head ake": "headache",
    "stomack": "stomach",
}

# Lazy import for vector search (optional dependency)
_vector_retriever = None

def get_vector_retriever():
    """Lazy load vector retriever"""
    global _vector_retriever
    if _vector_retriever is None:
        try:
            from .vector_retriever import get_retriever
            _vector_retriever = get_retriever()
            logger.info("[OK] Vector retriever enabled")
        except Exception as e:
            logger.warning(f"Vector retriever not available: {e}")
            _vector_retriever = False
    return _vector_retriever if _vector_retriever is not False else None

# Lazy import for multilingual retriever (Phase 6)
_multilingual_retriever = None

def get_multilingual_retriever():
    """Lazy load multilingual retriever"""
    global _multilingual_retriever
    if _multilingual_retriever is None:
        try:
            from src.retrieval.multilingual_retrieval import get_multilingual_retriever as _get_ml
            _multilingual_retriever = _get_ml()
            logger.info("[OK] Multilingual retriever enabled")
        except Exception as e:
            logger.warning(f"Multilingual retriever not available: {e}")
            _multilingual_retriever = False
    return _multilingual_retriever if _multilingual_retriever is not False else None

# Lazy import for language detector (Phase 6)
_language_detector = None

def get_language_detector():
    """Lazy load language detector"""
    global _language_detector
    if _language_detector is None:
        try:
            from src.multilingual import LanguageDetector
            _language_detector = LanguageDetector()
            logger.info("[OK] Language detector enabled")
        except Exception as e:
            logger.warning(f"Language detector not available: {e}")
            _language_detector = False
    return _language_detector if _language_detector is not False else None

# Lazy import for reranker (optional dependency)
_reranker = None

def get_reranker():
    """Lazy load reranker"""
    global _reranker
    if _reranker is None:
        try:
            from .reranker import get_reranker as _get_reranker
            _reranker = _get_reranker(enabled=True)
            logger.info("[OK] Reranker enabled")
        except Exception as e:
            logger.warning(f"Reranker not available: {e}")
            _reranker = False
    return _reranker if _reranker is not False else None

# Lazy import for LLM generator (optional dependency)
_llm_generator = None
_translator = None

def get_llm_generator():
    """Lazy load LLM generator"""
    global _llm_generator
    if _llm_generator is None:
        try:
            from .llm_generator import get_llm_generator as _get_llm
            _llm_generator = _get_llm()
            if _llm_generator.is_enabled():
                logger.info("[OK] LLM generator enabled")
            else:
                logger.info("LLM generator disabled (using template fallback)")
        except Exception as e:
            logger.warning(f"LLM generator not available: {e}")
            _llm_generator = False
    return _llm_generator if _llm_generator is not False else None


def get_translator():
    """Lazy load translation backend (optional)."""
    global _translator
    if _translator is None:
        try:
            if DEEP_TRANSLATOR_AVAILABLE:
                _translator = ("deep_translator", _DeepTranslator)
                logger.info("[OK] Translation backend enabled: deep_translator")
            else:
                _translator = False
                logger.info("Translation backend not available; using no-op fallback")
        except Exception as e:
            logger.warning(f"Translator initialization failed: {e}")
            _translator = False
    return _translator if _translator is not False else None


# Lazy import for knowledge graph related-disease lookup (optional dependency)
_related_disease_lookup = None

def get_related_disease_lookup():
    """Lazy load knowledge graph related-disease function."""
    global _related_disease_lookup
    if _related_disease_lookup is None:
        try:
            from .knowledge_graph import get_related_diseases as _get_related
            _related_disease_lookup = _get_related
            logger.info("[OK] Knowledge graph related-disease lookup enabled")
        except Exception as e:
            logger.warning(f"Knowledge graph lookup not available: {e}")
            _related_disease_lookup = False
    return _related_disease_lookup if _related_disease_lookup is not False else None


@dataclass
class RetrievalResult:
    """Result from retrieval system"""
    answer: str
    sources: List[Dict]
    confidence: float
    language: str
    mode: str = "rag"
    metrics: Optional[Dict[str, float]] = None


class MedicalRAG:
    """
    Medical Retrieval-Augmented Generation System
    Orchestrates multiple retrieval and generation components
    """
    
    def __init__(
        self,
        languages: List[str] = ["ar", "fr", "en"],
        embedding_model: str = "sentence-transformers/biomed_roberta_base",
        llm_model: str = "Qwen/Qwen2.5-7B-Instruct",
        use_reranking: bool = True,
        enable_vision: bool = False,
    ):
        """Initialize the RAG system
        
        Args:
            languages: Supported languages
            embedding_model: Model for dense retrieval
            llm_model: Language model for answer generation
            use_reranking: Enable cross-encoder reranking
            enable_vision: Enable medical image analysis
        """
        self.languages = languages
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.use_reranking = use_reranking
        self.enable_vision = enable_vision
        self.multilingual_mode = len(languages) > 1
        self._last_rerank_ms = 0.0
        self._last_embedding_ms = 0.0
        self._last_vector_search_ms = 0.0
        self._last_detected_language = "en"
        self.retrieval_top_k = 10
        self.final_top_k = 5
        
        # TODO: Initialize components
        # self.dense_retriever = DenseRetriever(embedding_model)
        # self.sparse_retriever = BM25Retriever()
        # self.reranker = CrossEncoderReranker()
        # self.llm = LLMGenerator(llm_model)
        
        logger.info(f"Initialized MedicalRAG with languages: {languages}")
        if self.multilingual_mode:
            logger.info("Multilingual mode enabled (Phase 6)")
    
    def query(
        self,
        question: str,
        language: Optional[str] = None,
        top_k: int = 5,
        use_reranking: bool = True,
    ) -> RetrievalResult:
        """
        Query the medical knowledge base
        
        Args:
            question: User medical question
            language: Query language (auto-detected if None)
            top_k: Number of results to return
            use_reranking: Whether to apply cross-encoder reranking
            
        Returns:
            RetrievalResult with answer and sources
        """
        try:
            question = self._normalize_query(question)
            logger.info(f"Processing query: {question[:50]}...")
            total_start = time.perf_counter()
            
            # Detect language
            detected_lang = self._normalize_language(language) if language else self._detect_language(question)
            self._last_detected_language = detected_lang

            retrieval_question = question
            translated_for_retrieval = False
            if detected_lang != "en":
                translated_question = self._translate_text(question, source_lang=detected_lang, target_lang="en")
                if translated_question and translated_question.strip():
                    retrieval_question = translated_question
                    translated_for_retrieval = retrieval_question.strip().lower() != question.strip().lower()
            
            # Simple keyword-based retrieval from knowledge base
            retrieval_start = time.perf_counter()
            retrieval_language = "en" if translated_for_retrieval else detected_lang
            sources = self._retrieve_relevant_info(
                retrieval_question,
                top_k,
                use_reranking=use_reranking,
                language=retrieval_language,
            )

            # Fallback mode: no relevant retrieved context, answer from LLM prior knowledge with strict guardrails.
            if not sources:
                llm = get_llm_generator()
                fallback_language = detected_lang
                if llm and llm.is_enabled():
                    fallback_answer = llm.generate_fallback_answer(retrieval_question, fallback_language)
                else:
                    fallback_answer = (
                        "I could not understand the medical intent of your question. Please rephrase.\n\n"
                        "This information is for educational purposes and does not replace professional medical advice."
                    )

                total_ms = (time.perf_counter() - total_start) * 1000.0
                return RetrievalResult(
                    answer=fallback_answer,
                    sources=[],
                    confidence=0.7,
                    language=detected_lang,
                    mode="fallback",
                    metrics={
                        "detected_language": detected_lang,
                        "query_translated_to_en": 1.0 if translated_for_retrieval else 0.0,
                        "answer_translated_back": 0.0,
                        "embedding_ms": round(float(self._last_embedding_ms), 2),
                        "vector_search_ms": round(float(self._last_vector_search_ms), 2),
                        "retrieval_ms": round((time.perf_counter() - retrieval_start) * 1000.0, 2),
                        "rerank_ms": round(float(self._last_rerank_ms), 2),
                        "generation_ms": 0.0,
                        "total_ms": round(total_ms, 2),
                    },
                )

            for source in sources:
                if isinstance(source, dict):
                    source.setdefault("language", detected_lang)
            retrieval_total_ms = (time.perf_counter() - retrieval_start) * 1000.0
            rerank_ms = max(0.0, float(self._last_rerank_ms))
            embedding_ms = max(0.0, float(self._last_embedding_ms))
            vector_search_ms = max(0.0, float(self._last_vector_search_ms))
            retrieval_ms = max(0.0, retrieval_total_ms - rerank_ms)
            
            # Generate answer from sources
            generation_start = time.perf_counter()
            generation_language = detected_lang
            answer = self._generate_answer(retrieval_question, sources, generation_language)

            generation_ms = (time.perf_counter() - generation_start) * 1000.0
            total_ms = (time.perf_counter() - total_start) * 1000.0

            logger.info(
                "RAG timings | embedding_ms=%.2f vector_search_ms=%.2f retrieval_ms=%.2f rerank_ms=%.2f generation_ms=%.2f total_ms=%.2f",
                embedding_ms,
                vector_search_ms,
                retrieval_ms,
                rerank_ms,
                generation_ms,
                total_ms,
            )

            confidence = self._calibrate_confidence(sources)

            # Guardrail 1: No reliable sources.
            # With final_score = 0.7*dense + 0.3*sparse, sparse-only mode caps at 0.3.
            # Use a dynamic threshold to preserve sparse-only fallback behavior.
            has_dense_signal = any(float(s.get("dense_score", s.get("vector_score", 0.0))) > 0.0 for s in sources)
            reliable_threshold = 0.4 if has_dense_signal else 0.25
            reliable_sources = [
                s for s in sources
                if float(s.get("relevance_score", 0.0)) >= reliable_threshold
            ]
            if not reliable_sources:
                llm = get_llm_generator()
                fallback_answer = (
                    llm.generate_fallback_answer(retrieval_question, generation_language)
                    if llm and llm.is_enabled()
                    else "I could not understand the medical intent of your question. Please rephrase.\n\nThis information is for educational purposes and does not replace professional medical advice."
                )
                return RetrievalResult(
                    answer=fallback_answer,
                    sources=[],
                    confidence=0.7,
                    language=detected_lang,
                    mode="fallback",
                    metrics={
                        "detected_language": detected_lang,
                        "query_translated_to_en": 1.0 if translated_for_retrieval else 0.0,
                        "answer_translated_back": 0.0,
                        "embedding_ms": round(embedding_ms, 2),
                        "vector_search_ms": round(vector_search_ms, 2),
                        "retrieval_ms": round(retrieval_ms, 2),
                        "rerank_ms": round(rerank_ms, 2),
                        "generation_ms": round(generation_ms, 2),
                        "total_ms": round(total_ms, 2),
                    },
                )

            # Language consistency: enforce response language
            if answer and detected_lang != "en" and self._detect_language(answer) != detected_lang:
                answer = self._render_language_consistent_answer(detected_lang, sources)
            
            return RetrievalResult(
                answer=answer,
                sources=sources,
                confidence=confidence,
                language=detected_lang,
                mode="rag",
                metrics={
                    "detected_language": detected_lang,
                    "query_translated_to_en": 1.0 if translated_for_retrieval else 0.0,
                    "answer_translated_back": 0.0,
                    "embedding_ms": round(embedding_ms, 2),
                    "vector_search_ms": round(vector_search_ms, 2),
                    "retrieval_ms": round(retrieval_ms, 2),
                    "rerank_ms": round(rerank_ms, 2),
                    "generation_ms": round(generation_ms, 2),
                    "total_ms": round(total_ms, 2),
                },
            )
        except Exception as e:
            logger.error(f"Query error: {e}")
            return RetrievalResult(
                answer="The system encountered a temporary processing issue. Please try again or consult a healthcare professional.",
                sources=[],
                confidence=0.0,
                language=language or "en",
                mode="error",
                metrics={
                    "detected_language": self._normalize_language(language) if language else "en",
                    "query_translated_to_en": 0.0,
                    "answer_translated_back": 0.0,
                    "embedding_ms": 0.0,
                    "vector_search_ms": 0.0,
                    "retrieval_ms": 0.0,
                    "rerank_ms": 0.0,
                    "generation_ms": 0.0,
                    "total_ms": 0.0,
                },
            )

    def _calibrate_confidence(self, sources: List[Dict]) -> float:
        """Calibrate confidence into a stable [0, 1] range."""
        if not sources:
            return 0.0

        top_scores = []
        for source in sources[:3]:
            try:
                top_scores.append(float(source.get("relevance_score", 0.0)))
            except Exception:
                top_scores.append(0.0)

        if not top_scores:
            return 0.0

        avg = sum(top_scores) / len(top_scores)
        calibrated = max(0.0, min(1.0, 0.15 + 0.85 * avg))
        return round(calibrated, 4)

    def _render_language_consistent_answer(self, language: str, sources: List[Dict]) -> str:
        """Render a structured fallback answer in the detected query language."""
        llm = get_llm_generator()
        if llm:
            return llm._generate_template_answer("", sources, language)

        labels = {
            "ar": "هذه المعلومات لأغراض تعليمية فقط. يرجى استشارة مختص صحي للحصول على نصيحة طبية دقيقة.",
            "fr": "Ces informations sont fournies a des fins educatives uniquement. Veuillez consulter un professionnel de sante.",
            "en": "This information is for educational purposes only. Please consult a healthcare professional.",
        }.get(self._normalize_language(language), "This information is for educational purposes only. Please consult a healthcare professional.")
        return labels
    
    def _detect_language(self, text: str) -> str:
        """
        Detect query language using Phase 6 language detector
        
        Args:
            text: Input text to detect language
            
        Returns:
            Language code (ar, fr, en)
        """
        normalized_text = (text or "").strip()
        if not normalized_text:
            return "en"

        probe_text = self._strip_diacritics(normalized_text.lower())

        detector = get_language_detector()
        if detector:
            result = detector.detect(text)
            logger.info(f"Detected language: {result.language_name} (confidence: {result.confidence:.2f})")
            return self._normalize_language(result.language)

        if LANGDETECT_AVAILABLE:
            try:
                detected = _langdetect_detect(normalized_text)
                normalized = self._normalize_language(detected)
                logger.info("Detected language via langdetect: %s", normalized)
                return normalized
            except Exception:
                pass
        
        # Fallback: Simple detection
        # Arabic detection
        if any('\u0600' <= c <= '\u06FF' for c in normalized_text):
            return "ar"
        # French common words
        french_words = [" est ", " sont ", " avec ", " pour ", " dans ", " les ", " des ", " une ", " le ", " la ", " symptomes ", " traitement "]
        text_probe = f" {probe_text} "
        if any(word in text_probe for word in french_words):
            return "fr"
        # Default to English
        return "en"

    def _normalize_language(self, language: Optional[str]) -> str:
        """Normalize incoming language to supported ISO subset: ar, fr, en."""
        if not language:
            return "en"
        code = str(language).strip().lower()
        if code.startswith("ar"):
            return "ar"
        if code.startswith("fr"):
            return "fr"
        return "en"

    @staticmethod
    def _strip_diacritics(text: str) -> str:
        """Remove accents and combining marks for stable retrieval matching."""
        normalized = unicodedata.normalize("NFKD", text or "")
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _normalize_arabic_text(self, text: str) -> str:
        """Normalize Arabic spelling variants and remove diacritics."""
        normalized = self._strip_diacritics(text)
        translations = str.maketrans({
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ٱ": "ا",
            "ى": "ي",
            "ؤ": "و",
            "ئ": "ي",
            "ة": "ه",
            "ـ": "",
        })
        normalized = normalized.translate(translations)
        normalized = re.sub(r"[\u064B-\u065F\u0670]", "", normalized)
        return normalized

    def _normalize_text_for_retrieval(self, text: str, language: Optional[str] = None) -> str:
        """Normalize text and expand key medical terms for retrieval."""
        if not text:
            return ""

        language_code = self._normalize_language(language)
        normalized = unicodedata.normalize("NFKC", str(text)).strip().lower()

        if language_code == "ar":
            normalized = self._normalize_arabic_text(normalized)
            normalized = re.sub(r"[^\w\s\u0600-\u06FF]+", " ", normalized, flags=re.UNICODE)
        elif language_code == "fr":
            normalized = self._strip_diacritics(normalized)
            normalized = re.sub(r"[^\w\s]+", " ", normalized, flags=re.UNICODE)
        else:
            normalized = re.sub(r"[^\w\s]+", " ", normalized, flags=re.UNICODE)

        normalized = re.sub(r"\s+", " ", normalized).strip()
        tokens = re.findall(r"\w+", normalized, flags=re.UNICODE)

        expanded_tokens = list(tokens)
        for token in tokens:
            if language_code == "ar":
                mapped = ARABIC_QUERY_HINTS.get(token)
                if mapped:
                    expanded_tokens.extend(mapped.split())
            elif language_code == "fr":
                mapped = FRENCH_QUERY_HINTS.get(token)
                if mapped:
                    expanded_tokens.extend(mapped.split())

        return " ".join(expanded_tokens)

    def _normalize_query(self, query: str) -> str:
        """Apply deterministic typo/phrase normalization before retrieval."""
        raw = str(query or "").strip()
        if not raw:
            return raw
        replacement = QUERY_NORMALIZATION_MAP.get(raw.lower())
        if replacement:
            logger.info("Normalized query phrase: '%s' -> '%s'", raw, replacement)
            return replacement
        return raw

    def _domain_filter(self, query: str, docs: List[Dict]) -> List[Dict]:
        """Remove off-domain COVID-heavy matches when user did not ask about COVID."""
        query_lower = str(query or "").lower()
        if "covid" in query_lower or "sars" in query_lower:
            return docs

        filtered = []
        for doc in docs or []:
            title = str(doc.get("title", "")).lower()
            category = str(doc.get("category", "")).lower()
            content_text = str(doc.get("content", "")).lower()
            joined = " ".join([title, category, content_text])
            if "covid" in joined:
                continue
            filtered.append(doc)
        return filtered

    def _tokenize_for_bm25(self, text: str, language: Optional[str] = None) -> List[str]:
        """Create BM25 tokens from normalized retrieval text."""
        normalized = self._normalize_text_for_retrieval(text, language)
        if not normalized:
            return []

        language_code = self._normalize_language(language)
        stopwords = {
            "and", "or", "the", "a", "an", "of", "to", "in", "for", "with", "about", "is", "are",
            "what", "which", "when", "where", "why", "how", "this", "that", "can", "you", "from",
        }
        if language_code == "ar":
            stopwords = stopwords | ARABIC_STOPWORDS
        elif language_code == "fr":
            stopwords = stopwords | FRENCH_STOPWORDS

        tokens = [token for token in re.findall(r"\w+", normalized, flags=re.UNICODE) if len(token) > 2]
        return [token for token in tokens if token not in stopwords]

    def _localized_labels(self, language: str) -> Dict[str, str]:
        """Return section labels for the requested language."""
        language_code = self._normalize_language(language)
        if language_code == "ar":
            return {
                "title": "المعلومة الطبية",
                "overview": "نظرة عامة",
                "symptoms": "الأعراض",
                "causes": "الأسباب",
                "treatment": "العلاج",
                "diagnosis": "التشخيص",
                "prevention": "الوقاية",
                "sources": "المصادر",
                "note": "ملاحظة منخفضة الثقة: قد تكون الأدلة المتاحة غير مكتملة؛ يرجى التحقق مع طبيب مختص.",
                "disclaimer": "هذه المعلومات لأغراض تعليمية فقط. يرجى استشارة مختص صحي للحصول على نصيحة طبية دقيقة.",
            }
        if language_code == "fr":
            return {
                "title": "Information medicale",
                "overview": "Apercu",
                "symptoms": "Symptomes",
                "causes": "Causes",
                "treatment": "Traitement",
                "diagnosis": "Diagnostic",
                "prevention": "Prevention",
                "sources": "Sources",
                "note": "Note de faible confiance: les donnees disponibles peuvent etre incomplètes; verifiez aupres d'un clinicien.",
                "disclaimer": "Ces informations sont fournies a des fins educatives uniquement. Veuillez consulter un professionnel de sante.",
            }
        return {
            "title": "Medical Information",
            "overview": "Overview",
            "symptoms": "Symptoms",
            "causes": "Causes",
            "treatment": "Treatment",
            "diagnosis": "Diagnosis",
            "prevention": "Prevention",
            "sources": "Sources",
            "note": "Low confidence note: available evidence may be incomplete; verify with a licensed clinician.",
            "disclaimer": "This information is for educational purposes only. Please consult a healthcare professional.",
        }

    def _extract_section_items(self, source: Dict, section: str) -> List[str]:
        """Collect section items from a retrieved source."""
        items: List[str] = []
        content = source.get("content", {}) if isinstance(source, dict) else {}
        data = content.get("data") if isinstance(content, dict) else None

        if isinstance(data, dict):
            section_values = data.get(section, [])
            if isinstance(section_values, list):
                items.extend(str(item) for item in section_values if str(item).strip())
            elif section_values:
                items.append(str(section_values))

        if not items and isinstance(content, dict):
            direct_values = content.get(section, [])
            if isinstance(direct_values, list):
                items.extend(str(item) for item in direct_values if str(item).strip())
            elif direct_values:
                items.append(str(direct_values))

        if not items and isinstance(data, list):
            focus = str(content.get("focus", section)).lower() if isinstance(content, dict) else section
            for item in data:
                item_text = str(item).strip()
                if not item_text:
                    continue
                item_lower = item_text.lower()
                if section == "symptoms" and any(word in item_lower for word in ["symptom", "fever", "cough", "pain", "fatigue", "breath"]):
                    items.append(item_text)
                elif section == "causes" and any(word in item_lower for word in ["cause", "risk", "infection", "virus", "bacteria", "smoking"]):
                    items.append(item_text)
                elif section == "treatment" and any(word in item_lower for word in ["treat", "therapy", "antibiotic", "rest", "hydration", "monitor"]):
                    items.append(item_text)
                elif section in focus:
                    items.append(item_text)

        deduped: List[str] = []
        for item in items:
            if item not in deduped:
                deduped.append(item)
        return deduped

    def _build_structured_medical_answer(self, sources: List[Dict], language: str) -> str:
        """Build a structured medical answer from retrieved sources."""
        if not sources:
            labels = self._localized_labels(language)
            return labels["disclaimer"]

        labels = self._localized_labels(language)
        top_source = sources[0]
        title = top_source.get("title", labels["title"])
        category = top_source.get("category", "")
        content = top_source.get("content", {}) if isinstance(top_source, dict) else {}
        data = content.get("data", {}) if isinstance(content, dict) else {}

        answer_parts: List[str] = []
        answer_parts.append(f"**{title}**")
        if category:
            answer_parts.append(f"*({category})*")

        description = ""
        if isinstance(data, dict):
            description = str(data.get("description", "")).strip()
        if not description and isinstance(content, dict):
            description = str(content.get("focus", "")).strip()
        if description:
            normalized_description = description.lower()
            if language.lower().startswith("fr"):
                if normalized_description in {"symptoms", "symptom"}:
                    description = labels["symptoms"]
                elif normalized_description in {"causes", "cause"}:
                    description = labels["causes"]
                elif normalized_description == "treatment":
                    description = labels["treatment"]
                elif normalized_description == "overview":
                    description = labels["overview"]
            elif language.lower().startswith("ar"):
                if normalized_description in {"symptoms", "symptom"}:
                    description = labels["symptoms"]
                elif normalized_description in {"causes", "cause"}:
                    description = labels["causes"]
                elif normalized_description == "treatment":
                    description = labels["treatment"]
                elif normalized_description == "overview":
                    description = labels["overview"]
            if description.lower() not in {
                labels["symptoms"].lower(),
                labels["causes"].lower(),
                labels["treatment"].lower(),
                labels["overview"].lower(),
            }:
                answer_parts.append(description)

        section_order = ["symptoms", "causes", "treatment", "diagnosis", "prevention"]
        for section in section_order:
            section_items = self._extract_section_items(top_source, section)
            if not section_items:
                continue
            answer_parts.append(f"\n**{labels[section]}:**")
            for item in section_items[:4]:
                answer_parts.append(f"• {item}")

        if not any(self._extract_section_items(top_source, section) for section in section_order):
            answer_parts.append(f"\n**{labels['overview']}:**")
            answer_parts.append("• Clinical details are limited in the retrieved sources.")

        answer_parts.append(f"\n{labels['disclaimer']}")
        if len(sources) > 1:
            related = [str(source.get("title", "")).strip() for source in sources[1:5] if str(source.get("title", "")).strip()]
            if related:
                answer_parts.append(f"\nRelated conditions: {', '.join(related)}")

        answer_parts.append(f"\n{labels['sources']}:")
        source_lines = []
        for i, source in enumerate(sources[:5], 1):
            title = source.get("title") or source.get("source") or f"Source {i}"
            source_lines.append(f"[S{i}] {str(title)}")
        answer_parts.append("\n".join(source_lines) if source_lines else "[S1] No source available")

        confidence = self._estimate_confidence(sources)
        if confidence < 0.5:
            answer_parts.append(labels["note"])

        return "\n".join(answer_parts).strip()

    def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text with optional backends.

        Fail-safe behavior: returns original text if translation backend is unavailable
        or if translation fails for any reason.
        """
        if not text or source_lang == target_lang:
            return text

        backend = get_translator()
        if not backend:
            return text

        backend_name, backend_client = backend
        try:
            if backend_name == "deep_translator":
                src = source_lang if source_lang in {"ar", "fr", "en"} else "auto"
                translated = backend_client(source=src, target=target_lang).translate(text)
                return translated or text
        except Exception as e:
            logger.warning(f"Translation failed ({source_lang}->{target_lang}): {e}")

        return text

    def _minmax_normalize_score_map(self, score_map: Dict[str, float]) -> Dict[str, float]:
        """Min-max normalize a score map into [0, 1] with stable fallback behavior."""
        if not score_map:
            return {}

        cleaned = {}
        for key, value in score_map.items():
            try:
                cleaned[key] = float(value)
            except Exception:
                cleaned[key] = 0.0

        values = list(cleaned.values())
        min_score = min(values)
        max_score = max(values)

        if max_score - min_score < 1e-9:
            # Flat distribution: keep clipped raw values for deterministic behavior.
            return {k: max(0.0, min(1.0, v)) for k, v in cleaned.items()}

        denom = max_score - min_score
        normalized = {}
        for key, value in cleaned.items():
            score = (value - min_score) / denom
            normalized[key] = max(0.0, min(1.0, score))
        return normalized
    
    def _retrieve_relevant_info(
        self,
        question: str,
        top_k: int = 5,
        use_reranking: bool = True,
        language: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant information with hybrid search (vector + keyword)
        Phase 6: Uses multilingual retriever for cross-lingual search
        No breaking API changes - seamlessly uses vector search if available
        
        Args:
            question: User query
            top_k: Number of results to return
            
        Returns:
            List of relevant source documents
        """
        self._last_rerank_ms = 0.0
        self._last_embedding_ms = 0.0
        self._last_vector_search_ms = 0.0
        sources = []
        retrieval_candidates_k = max(self.retrieval_top_k, int(top_k or 5))
        final_k = min(self.final_top_k, max(1, int(top_k or self.final_top_k)))
        normalized_question = self._normalize_text_for_retrieval(question, language)
        question_lower = normalized_question.lower()
        
        # Try multilingual retriever first (Phase 6)
        if self.multilingual_mode:
            ml_retriever = get_multilingual_retriever()
            if ml_retriever and ml_retriever.index is not None:
                try:
                    ml_results = ml_retriever.search(
                        question,
                        top_k=retrieval_candidates_k,
                        language=self._normalize_language(language),
                    )
                    logger.info(f"Multilingual search returned {len(ml_results)} results")
                    if ml_results:
                        ml_results = self._domain_filter(question, ml_results)
                        return self._append_related_disease_context(ml_results[:final_k])
                except Exception as e:
                    logger.warning(f"Multilingual search error: {e}")
        
        # Fallback to monolingual vector retriever
        retriever = get_vector_retriever()
        vector_results = []
        if retriever and retriever.index is not None:
            try:
                vector_results = retriever.semantic_search(
                    normalized_question or question,
                    top_k=retrieval_candidates_k,
                    language=self._normalize_language(language),
                )
                self._last_embedding_ms = float(getattr(retriever, "last_embedding_ms", 0.0) or 0.0)
                self._last_vector_search_ms = float(getattr(retriever, "last_search_ms", 0.0) or 0.0)
                logger.info(f"Vector search returned {len(vector_results)} results")
            except Exception as e:
                logger.warning(f"Vector search error: {e}")

        # BM25 sparse retrieval over medical knowledge base documents.
        # Extract key medical terms from question.
        medical_terms = {
            "symptoms": ["symptom", "sign", "indication", "أعراض", "symptôme"],
            "causes": ["cause", "reason", "why", "etiology", "أسباب", "cause"],
            "treatment": ["treat", "therapy", "cure", "medication", "علاج", "traiter"],
            "diagnosis": ["diagnose", "test", "detect", "exam", "تشخيص", "diagnostic"],
            "prevention": ["prevent", "avoid", "protection", "وقاية", "prévention"],
            "risk_factors": ["risk", "factor", "susceptible", "عوامل الخطر", "facteur de risque"],
        }

        # Find query intent for focused response composition.
        query_intent = "general"
        for intent, keywords in medical_terms.items():
            normalized_keywords = [self._normalize_text_for_retrieval(keyword, language) for keyword in keywords]
            if any(keyword and keyword in question_lower for keyword in normalized_keywords):
                query_intent = intent
                break

        bm25_score_by_disease = {}
        if BM25_AVAILABLE and MEDICAL_KNOWLEDGE:
            try:
                disease_keys = list(MEDICAL_KNOWLEDGE.keys())
                corpus_docs = []
                for key in disease_keys:
                    info = MEDICAL_KNOWLEDGE[key]
                    parts = [
                        str(info.get("name", key)),
                        " ".join(info.get("symptoms", []) if isinstance(info.get("symptoms"), list) else []),
                        " ".join(info.get("causes", []) if isinstance(info.get("causes"), list) else []),
                        " ".join(info.get("treatment", []) if isinstance(info.get("treatment"), list) else []),
                        " ".join(info.get("diagnosis", []) if isinstance(info.get("diagnosis"), list) else []),
                        " ".join(info.get("prevention", []) if isinstance(info.get("prevention"), list) else []),
                    ]
                    normalized_doc = self._normalize_text_for_retrieval(" ".join(p for p in parts if p), "en")
                    corpus_docs.append(normalized_doc)

                tokenized_corpus = [self._tokenize_for_bm25(doc, "en") for doc in corpus_docs]
                query_tokens = self._tokenize_for_bm25(question, language)
                bm25 = BM25Okapi(tokenized_corpus)
                raw_scores = bm25.get_scores(query_tokens)
                bm25_raw_score_by_disease = {}
                for idx, key in enumerate(disease_keys):
                    bm25_raw_score_by_disease[key] = float(raw_scores[idx]) if len(raw_scores) else 0.0

                bm25_score_by_disease = self._minmax_normalize_score_map(bm25_raw_score_by_disease)

                logger.info("BM25 retrieval computed for %d diseases", len(bm25_score_by_disease))
            except Exception as e:
                logger.warning(f"BM25 retrieval error: {e}")
                bm25_score_by_disease = {}
        else:
            logger.info("BM25 not available; install rank-bm25 for sparse retrieval")

        # Dependency-free lexical fallback.
        # This keeps retrieval query-sensitive even when embeddings/BM25 backends are unavailable.
        if not bm25_score_by_disease and MEDICAL_KNOWLEDGE:
            query_tokens = set(self._tokenize_for_bm25(question, language))

            lexical_raw_scores = {}
            for disease_key, disease_info in MEDICAL_KNOWLEDGE.items():
                disease_name = self._normalize_text_for_retrieval(str(disease_info.get("name", disease_key)), "en").lower()
                fields = [
                    disease_name,
                    str(disease_info.get("category", "")),
                    str(disease_info.get("description", "")),
                    " ".join(disease_info.get("symptoms", []) if isinstance(disease_info.get("symptoms"), list) else []),
                    " ".join(disease_info.get("causes", []) if isinstance(disease_info.get("causes"), list) else []),
                    " ".join(disease_info.get("treatment", []) if isinstance(disease_info.get("treatment"), list) else []),
                    " ".join(disease_info.get("diagnosis", []) if isinstance(disease_info.get("diagnosis"), list) else []),
                    " ".join(disease_info.get("prevention", []) if isinstance(disease_info.get("prevention"), list) else []),
                    " ".join(disease_info.get("risk_factors", []) if isinstance(disease_info.get("risk_factors"), list) else []),
                ]
                doc_text = self._normalize_text_for_retrieval(" ".join(part for part in fields if part), "en").lower()
                doc_tokens = set(self._tokenize_for_bm25(doc_text, "en"))

                overlap = len(query_tokens & doc_tokens)
                base_score = (overlap / max(1, len(query_tokens))) if query_tokens else 0.0

                # Strong bonus when the disease name appears explicitly in the user query.
                name_bonus = 0.65 if disease_name and disease_name in question_lower else 0.0

                # Intent bonus for field-specific matches.
                intent_bonus = 0.0
                if query_intent == "symptoms" and disease_info.get("symptoms"):
                    if any(tok in " ".join(disease_info.get("symptoms", [])).lower() for tok in query_tokens):
                        intent_bonus = 0.12
                elif query_intent == "causes" and disease_info.get("causes"):
                    if any(tok in " ".join(disease_info.get("causes", [])).lower() for tok in query_tokens):
                        intent_bonus = 0.12
                elif query_intent == "treatment" and disease_info.get("treatment"):
                    if any(tok in " ".join(disease_info.get("treatment", [])).lower() for tok in query_tokens):
                        intent_bonus = 0.12

                lexical_raw_scores[disease_key] = base_score + name_bonus + intent_bonus

            bm25_score_by_disease = self._minmax_normalize_score_map(lexical_raw_scores)
            logger.info("Fallback lexical retrieval computed for %d diseases", len(bm25_score_by_disease))

        # Build vector score map by disease key.
        dense_raw_score_by_disease = {}
        for vr in vector_results:
            metadata = vr.get("metadata", {}) if isinstance(vr, dict) else {}
            try:
                raw_dense_score = float(vr.get("score", 0.0))
            except Exception:
                raw_dense_score = 0.0

            disease_key = metadata.get("disease_key")
            if not disease_key:
                disease_name = str(metadata.get("disease", "")).lower().strip()
                if disease_name:
                    for key, info in MEDICAL_KNOWLEDGE.items():
                        if disease_name == str(info.get("name", key)).lower().strip():
                            disease_key = key
                            break

            if disease_key:
                dense_raw_score_by_disease[disease_key] = max(
                    dense_raw_score_by_disease.get(disease_key, 0.0),
                    raw_dense_score,
                )

        dense_score_by_disease = self._minmax_normalize_score_map(dense_raw_score_by_disease)
        
        # Search through comprehensive knowledge base
        for disease_key, disease_info in MEDICAL_KNOWLEDGE.items():
            dense_score = dense_score_by_disease.get(disease_key, 0.0)
            sparse_score = bm25_score_by_disease.get(disease_key, 0.0)

            # Exact hybrid retrieval fusion formula.
            final_score = (0.7 * dense_score) + (0.3 * sparse_score)
            relevance_score = max(0.0, min(1.0, final_score))
            
            # If relevant, add to sources.
            # Keep sparse-only fallback recall when dense retriever is unavailable.
            threshold = 0.15 if not dense_score_by_disease else 0.3
            if relevance_score > threshold:
                # Build focused response based on query intent
                content = {}
                if query_intent == "symptoms":
                    content = {
                        "focus": "Symptoms",
                        "data": disease_info.get("symptoms", [])
                    }
                elif query_intent == "causes":
                    content = {
                        "focus": "Causes",
                        "data": disease_info.get("causes", [])
                    }
                elif query_intent == "treatment":
                    content = {
                        "focus": "Treatment",
                        "data": disease_info.get("treatment", [])
                    }
                elif query_intent == "diagnosis":
                    content = {
                        "focus": "Diagnosis",
                        "data": disease_info.get("diagnosis", [])
                    }
                elif query_intent == "prevention":
                    content = {
                        "focus": "Prevention",
                        "data": disease_info.get("prevention", [])
                    }
                else:
                    # General information
                    content = {
                        "focus": "Overview",
                        "data": disease_info
                    }
                
                sources.append({
                    "title": disease_info.get("name", disease_key.title()),
                    "category": disease_info.get("category", "Medical Condition"),
                    "content": content,
                    "relevance_score": relevance_score,
                    "score": relevance_score,
                    "dense_score": dense_score,
                    "sparse_score": sparse_score,
                    "vector_score": dense_score,
                    "bm25_score": sparse_score,
                    "disease_key": disease_key
                })
        
        # Stable ranking: deterministic tie-breakers after hybrid score.
        sources.sort(
            key=lambda x: (
                -float(x.get("relevance_score", 0.0)),
                -float(x.get("dense_score", x.get("vector_score", 0.0))),
                -float(x.get("sparse_score", x.get("bm25_score", 0.0))),
                str(x.get("disease_key", "")),
                str(x.get("title", "")),
            )
        )
        
        # Always apply cross-encoder reranking when a model is available.
        # This is intentionally independent from request flags for stable quality.
        if sources:
            reranker = get_reranker()
            if reranker and reranker.is_enabled():
                rerank_start = time.perf_counter()
                # Prepare candidates for reranking
                candidates = []
                for source in sources[:retrieval_candidates_k]:
                    # Format document for reranking
                    doc_text = f"{source['title']}: {source['content'].get('focus', '')} - "
                    if isinstance(source['content'].get('data'), list):
                        doc_text += '; '.join(str(x) for x in source['content']['data'][:3])
                    else:
                        doc_text += str(source['content'].get('data', ''))[:200]
                    
                    candidates.append({
                        'document': doc_text,
                        'metadata': source,
                        'score': source['relevance_score']
                    })
                
                # Rerank
                reranked = reranker.rerank(question, candidates, top_k=final_k)
                
                # Update sources with reranked results
                if reranked:
                    sources = [r['metadata'] for r in reranked][:final_k]
                    logger.info(f"Applied cross-encoder reranking: {len(sources)} results")
                self._last_rerank_ms = (time.perf_counter() - rerank_start) * 1000.0
        
        sources = self._domain_filter(question, sources)
        final_sources = sources[:final_k]
        return self._append_related_disease_context(final_sources)

    def _append_related_disease_context(self, sources: List[Dict]) -> List[Dict]:
        """
        Enrich retrieved context with related diseases from the knowledge graph.

        This is a non-breaking augmentation: it only adds an optional
        "related_diseases" field when a disease can be detected.
        """
        if not sources:
            return sources

        lookup_fn = get_related_disease_lookup()
        if not lookup_fn:
            return sources

        detected_disease_name = None
        target_source = None

        # Prefer explicit disease_key, then fallback to source title.
        for source in sources:
            disease_key = source.get("disease_key")
            if disease_key and disease_key in MEDICAL_KNOWLEDGE:
                detected_disease_name = MEDICAL_KNOWLEDGE[disease_key].get("name", disease_key)
                target_source = source
                break

            title = str(source.get("title", "")).strip()
            if not title or title.lower() == "general medical information":
                continue

            for key, info in MEDICAL_KNOWLEDGE.items():
                candidate_name = str(info.get("name", key)).strip().lower()
                if title.lower() == candidate_name:
                    detected_disease_name = info.get("name", key)
                    target_source = source
                    break
            if detected_disease_name:
                break

        if not detected_disease_name or target_source is None:
            return sources

        try:
            related = lookup_fn(detected_disease_name, limit=5)
        except Exception as e:
            logger.warning(f"Related disease lookup failed for '{detected_disease_name}': {e}")
            return sources

        if not related:
            return sources

        # Keep related list clean and avoid self-reference.
        related_clean = [
            name for name in related
            if isinstance(name, str)
            and name.strip()
            and name.strip().lower() != str(detected_disease_name).strip().lower()
        ]
        if not related_clean:
            return sources

        target_source["related_diseases"] = related_clean
        content = target_source.get("content")
        if isinstance(content, dict):
            content["related_diseases"] = related_clean

        logger.debug(
            "Added %d related diseases to context for '%s'",
            len(related_clean),
            detected_disease_name,
        )
        return sources
    
    def _generate_answer(self, question: str, sources: List[Dict], language: str) -> str:
        """Generate comprehensive answer from sources using LLM or template fallback"""
        if not sources:
            return "I don't have enough information to answer this question. Please consult a healthcare professional."
        
        # Try LLM generation first
        llm = get_llm_generator()
        if llm and llm.is_enabled():
            try:
                answer = llm.generate_answer(question, sources, language)
                logger.info("Generated answer using LLM")
                return answer
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to template: {e}")
        
        # Fallback to template-based generation
        return self._generate_template_answer(question, sources, language)
    
    def _generate_template_answer(self, question: str, sources: List[Dict], language: str) -> str:
        """Generate answer using template (fallback when LLM unavailable)"""
        return self._build_structured_medical_answer(sources, language)
    
    def analyze_medical_image(
        self,
        image_path: str,
        question: Optional[str] = None,
        language: str = "en"
    ) -> RetrievalResult:
        """
        Analyze medical image (X-ray, CT scan) and provide diagnosis
        
        Args:
            image_path: Path to medical image
            question: Optional contextual question about the image
            language: Response language
            
        Returns:
            RetrievalResult with image analysis and contextual information
        """
        try:
            # Lazy load image analyzer
            from src.medical_imaging import get_image_analyzer
            
            analyzer = get_image_analyzer()
            
            if not analyzer.is_enabled():
                return RetrievalResult(
                    answer="⚠️ Medical image analysis is currently disabled. Set VISION_ENABLED=true to enable.",
                    sources=[],
                    confidence=0.0,
                    language=language
                )
            
            # Analyze image
            result = analyzer.analyze_image(image_path, return_recommendations=True)
            
            if result.error:
                return RetrievalResult(
                    answer=f"❌ Image analysis failed: {result.error}",
                    sources=[],
                    confidence=0.0,
                    language=language
                )
            
            # Build response
            answer_parts = []
            
            # Header
            if result.is_normal:
                answer_parts.append("**Medical Image Analysis: NORMAL**\n")
                answer_parts.append("No significant abnormalities detected in the image.\n")
            else:
                answer_parts.append("**Medical Image Analysis Results**\n")
            
            # Findings
            if result.findings:
                answer_parts.append("**Detected Findings:**")
                for finding in result.findings[:5]:  # Top 5
                    disease = finding["disease"]
                    conf = finding["confidence"]
                    conf_pct = f"{conf*100:.1f}%"
                    answer_parts.append(f"• {disease}: {conf_pct} confidence")
                answer_parts.append("")
            
            # Recommendations
            if result.recommendations:
                answer_parts.append("**Recommendations:**")
                for rec in result.recommendations:
                    answer_parts.append(f"• {rec}")
                answer_parts.append("")
            
            # If user asked a question, provide contextual information
            if question and result.top_finding:
                answer_parts.append(f"\n**Regarding your question:** {question}\n")
                
                # Retrieve relevant medical knowledge about the finding
                sources = self._retrieve_relevant_info(result.top_finding, top_k=3, language="en")
                
                if sources:
                    answer_parts.append(f"**About {result.top_finding}:**")
                    top_source = sources[0]
                    content = top_source.get("content", {})
                    
                    if isinstance(content.get("data"), dict):
                        data = content["data"]
                        if "description" in data:
                            answer_parts.append(f"{data['description']}\n")
                        
                        # Add relevant sections
                        for key in ["symptoms", "treatment", "diagnosis"]:
                            if key in data and data[key]:
                                title = key.capitalize()
                                answer_parts.append(f"**{title}:**")
                                items = data[key] if isinstance(data[key], list) else [data[key]]
                                for item in items[:3]:
                                    answer_parts.append(f"• {item}")
                                answer_parts.append("")
            
            # Disclaimer
            answer_parts.append("\n*⚠️ IMPORTANT DISCLAIMER:*")
            answer_parts.append("*This automated analysis is for informational purposes only.*")
            answer_parts.append("*It is NOT a substitute for professional medical diagnosis.*")
            answer_parts.append("*Always consult a qualified radiologist or physician for proper diagnosis and treatment.*")
            
            answer = "\n".join(answer_parts)
            
            # Create sources from findings
            sources = [{
                "title": "Image Analysis Result",
                "category": "Medical Imaging",
                "content": {
                    "focus": "Automated Diagnosis",
                    "data": result.to_dict()
                },
                "relevance_score": result.confidence
            }]
            
            return RetrievalResult(
                answer=answer,
                sources=sources,
                confidence=result.confidence,
                language=language
            )
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return RetrievalResult(
                answer=f"❌ Error analyzing image: {str(e)}",
                sources=[],
                confidence=0.0,
                language=language
            )
    
    def build_knowledge_base(self, documents: List[Dict]):
        """Build the medical knowledge base from documents"""
        # TODO: Implement knowledge base construction
        # - Document preprocessing
        # - Chunking strategies
        # - Embedding generation
        # - Index building (FAISS + BM25)
        pass


# TODO: Implement HybridRetriever
# TODO: Implement MedicalKnowledgeGraph integration
# TODO: Implement multi-lingual preprocessing
