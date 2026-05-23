"""
LLM Answer Generator for Medical RAG
Phase 3: Contextual answer generation with fallback
"""
import os
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.models.model_loader import get_model_loader

try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    GoogleTranslator = None
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    from langdetect import detect as _langdetect_detect
    LANGDETECT_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _langdetect_detect = None
    LANGDETECT_AVAILABLE = False

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _cfg(key: str, default: str) -> str:
    """Read config value from settings first, then environment."""
    try:
        from src.utils.config import settings

        value = getattr(settings, key, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    except Exception:
        pass

    env_value = os.getenv(key)
    if isinstance(env_value, str) and env_value.strip():
        return env_value.strip()
    return default


def _cfg_bool(key: str, default: bool) -> bool:
    """Read boolean config values from settings/env."""
    try:
        from src.utils.config import settings

        value = getattr(settings, key, None)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == "true"
    except Exception:
        pass

    env_value = os.getenv(key)
    if env_value is None:
        return default
    return str(env_value).strip().lower() == "true"


def _normalize_language_code(language: str) -> str:
    """Normalize language labels/codes to the supported code form."""
    normalized = str(language or "en").strip().lower()
    if normalized.startswith("ar") or normalized in {"arabic", "العربية"}:
        return "ar"
    if normalized.startswith("fr") or normalized in {"french", "francais", "français", "française"}:
        return "fr"
    return "en"


def _language_name(language: str) -> str:
    code = _normalize_language_code(language)
    return {"ar": "Arabic", "fr": "French", "en": "English"}.get(code, "English")

# Check for torch availability for no_grad inference
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch not available. Local LLM generation will be disabled.")


@dataclass
class LLMConfig:
    """LLM configuration from environment variables"""
    model_name: str = _cfg("LLM_MODEL", _cfg("LLM_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"))
    use_api: bool = _cfg_bool("USE_LLM_API", False)
    backend: str = _cfg("LLM_BACKEND", "api" if _cfg_bool("USE_LLM_API", False) else "local")
    api_endpoint: Optional[str] = _cfg("LLM_API_ENDPOINT", "") or None
    api_key: Optional[str] = _cfg("LLM_API_KEY", "") or None
    max_tokens: int = int(_cfg("LLM_MAX_TOKENS", "384"))
    temperature: float = float(_cfg("LLM_TEMPERATURE", "0.7"))
    top_p: float = float(_cfg("LLM_TOP_P", "0.9"))
    enabled: bool = _cfg_bool("LLM_ENABLED", True)


class MedicalLLMGenerator:
    """
    LLM-based answer generation for medical Q&A
    Supports local models and API endpoints with fallback
    """
    
    # Medical prompt template
    MEDICAL_PROMPT_TEMPLATE = """You are a clinical safety-first medical information assistant.

======================== LAYER 3: LLM GUARDRAIL RULES ========================
CRITICAL POLICY - MUST FOLLOW:
1. MEDICAL INTENT VALIDATION:
   - This question MUST be clearly medical in nature.
   - Non-medical queries, jokes, or off-topic questions → REFUSE with: 
     "I could not understand the medical intent of your question. Please rephrase."
   
2. INSUFFICIENT CONTEXT RULE:
   - If the provided context is insufficient or irrelevant to answer the question:
     → REFUSE with: "I do not have enough reliable medical information to answer this safely."
   
3. UNCLEAR QUESTION RULE:
   - If the question is ambiguous, vague, or lacks medical specificity:
     → REFUSE with: "Your question is unclear. Please provide more specific details."
   
4. NEVER GUESS:
   - Do NOT fabricate medical information.
   - Do NOT invent sources or facts.
   - Do NOT perform diagnosis or prescribe medications.
   
5. UNCERTAINTY COMMUNICATION:
   - Always acknowledge limitations and encourage professional consultation.
==============================================================================

Safety Policy:
- Never provide diagnosis certainty or medication prescriptions.
- If context is insufficient, state uncertainty clearly.
- Encourage professional medical consultation.
- Do not invent facts outside the provided context.

Context Information:
{context}

Question: {question}

Estimated Confidence: {confidence:.2f}

Required Sources:
{source_list}

Instructions:
- Answer strictly from the provided context.
- Use a structured format with short bullet points.
- Include sections in this exact order:
    1) Symptoms
    2) Causes
    3) Treatment
- Keep the answer concise: target 150-200 words total.
- Do not add any section after Sources.
- End the answer with a Sources section and cite source IDs from Required Sources using [S1], [S2], etc.
- If confidence < 0.50, include this exact sentence once:
    "Low confidence note: available evidence may be incomplete; verify with a licensed clinician."
- Keep response concise and medically safe.

Answer:"""

    SYSTEM_PROMPT = """You are a knowledgeable medical information assistant with strict safety guardrails.

CRITICAL LANGUAGE RULE:
- Respond ONLY in the specified language.
- DO NOT mix languages in your response.
- DO NOT include English words/phrases unless part of medical terminology.
- Translate all section headers and explanations to the target language.
- Ensure 100% language consistency throughout your entire response.

GUARDRAIL RULES:
- Validate that questions are clearly medical. Refuse non-medical queries.
- NEVER guess or fabricate medical information.
- If context is insufficient, clearly state you cannot answer reliably.
- If a question is unclear or ambiguous, ask for clarification.
- Never provide diagnosis certainty or medication prescriptions without proper medical context.
- Always encourage consultation with licensed medical professionals.

RESPONSE FORMAT:
- Use exactly these sections: Symptoms, Causes, Treatment (in target language).
- Keep responses within 150-200 words.
- Always end with Sources citing using [S1], [S2], etc.
- Prioritize safety and evidence-based information.
- Translate all text to match request language, including bullet points and notes."""

    FALLBACK_PROMPT = """You are a medical AI assistant with strong clinical knowledge.

Rules:
- Only answer if the question is clearly medical.
- If unclear, respond exactly: "I could not understand the medical intent of your question. Please rephrase."
- Do NOT hallucinate or invent facts.
- Provide concise, structured answers (Symptoms, Causes, Treatment if relevant).
- Always include this disclaimer exactly:
    "This information is for educational purposes and does not replace professional medical advice."

User Question:
{query}

Answer:
"""

    def build_prompt(
        self,
        query: str,
        context: str,
        target_language: str,
        confidence: float,
        source_list: str,
    ) -> str:
        """Build a language-locked medical prompt."""
        language_name = _language_name(target_language)
        return f"""You are a medical assistant.

STRICT RULE:
- Answer ONLY in {language_name}.
- Do NOT mix languages.
- If the context is in another language, TRANSLATE it.
- Keep all section labels, bullets, and disclaimers in {language_name}.

Return a structured response with exactly these sections:
Title:
Summary:
Symptoms:
Causes:
Treatment:
Sources:

User question: {query}

Target language: {language_name}
Estimated confidence: {confidence:.2f}

Required sources:
{source_list}

Context:
{context}
"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM generator
        
        Args:
            config: LLM configuration (uses env vars if None)
        """
        self.config = config or LLMConfig()
        self.model = None
        self.tokenizer = None
        self.loaded_model_name = None
        mode_label = "API" if self.config.use_api else "LOCAL"

        logger.info(f"LLM Config: backend={self.config.backend}, enabled={self.config.enabled}")
        logger.debug("LLM Mode: %s", mode_label)

        if self.config.enabled and not self.config.use_api and self.config.backend == "local":
            self._load_local_model()
    
    def _load_local_model(self):
        """Load local LLM model"""
        if not TORCH_AVAILABLE:
            logger.warning("Torch not available. LLM generation disabled.")
            self.config.enabled = False
            return
        
        try:
            logger.info("Loading local model via shared loader")
            tokenizer, model, loaded_name = get_model_loader().get_llm()
            self.tokenizer = tokenizer
            self.model = model
            self.loaded_model_name = loaded_name

            if self.model is None or self.tokenizer is None:
                raise RuntimeError("No local LLM model available")

            logger.info("[OK] Local LLM loaded successfully (%s)", self.loaded_model_name)
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self.config.enabled = False
            self.model = None
            self.tokenizer = None
    
    def generate_answer(
        self,
        question: str,
        context: List[Dict],
        language: str = "en",
        target_language: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate answer using LLM or fallback to template
        
        Args:
            question: User question
            context: Retrieved context (list of source dicts)
            language: Response language
            max_tokens: Override default max tokens
            temperature: Override default temperature
            
        Returns:
            Generated answer string
        """
        target_language = target_language or language

        # Use LLM if enabled and available
        if self.config.enabled and (self.model is not None or self.config.backend == "api" or self.config.use_api):
            try:
                llm_answer = self._generate_llm_answer(
                    question,
                    context,
                    target_language,
                    max_tokens or self.config.max_tokens,
                    temperature or self.config.temperature
                )
                if llm_answer:
                    logger.info("Generated answer using LLM")
                    return llm_answer
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
        
        # Fallback to template-based generation
        logger.debug("Using template-based answer generation")
        return self._generate_template_answer(question, context, target_language)

    def generate_fallback_answer(
        self,
        question: str,
        language: str = "en",
        target_language: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate a guardrailed answer when retrieval has no relevant documents."""
        target_language = target_language or language
        prompt = self.FALLBACK_PROMPT.format(query=question)
        language_hint = {
            "ar": "Respond in Arabic.",
            "fr": "Reponds en francais.",
            "en": "Respond in English.",
        }.get(_normalize_language_code(target_language), "Respond in English.")
        prompt = f"{prompt}\n\n{language_hint}"

        if self.config.enabled and (self.model is not None or self.config.backend == "api" or self.config.use_api):
            try:
                answer = get_model_loader().llm_chat(
                    prompt=prompt,
                    system_prompt=self.SYSTEM_PROMPT,
                    max_tokens=max_tokens or self.config.max_tokens,
                    temperature=temperature or self.config.temperature,
                    top_p=self.config.top_p,
                )
                if answer:
                    cleaned = answer.strip()
                    disclaimer = "This information is for educational purposes and does not replace professional medical advice."
                    if disclaimer.lower() not in cleaned.lower():
                        cleaned = f"{cleaned}\n\n{disclaimer}"
                    return self._enforce_language(cleaned, target_language)
            except Exception as exc:
                logger.warning("Fallback LLM generation failed: %s", exc)

        # Deterministic safe fallback if model is unavailable.
        return (
            "I could not find relevant documents, but here is general medical guidance.\n\n"
            "Symptoms:\n- Information not specific without source context.\n"
            "Causes:\n- Clinical causes vary based on condition.\n"
            "Treatment:\n- Consult a licensed clinician for diagnosis and treatment planning.\n\n"
            "This information is for educational purposes and does not replace professional medical advice."
        )
    
    def _generate_llm_answer(
        self,
        question: str,
        context: List[Dict],
        language: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Generate answer using LLM"""
        if self.config.use_api or self.config.backend == "api":
            return self._generate_api(question, context, language, max_tokens, temperature)
        if self.config.backend == "local" and self.model is not None:
            return self._generate_local(question, context, language, max_tokens, temperature)
        return None
    
    def _generate_local(
        self,
        question: str,
        context: List[Dict],
        language: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Generate using local model"""
        try:
            # Format context
            context_text = self._format_context(context)
            estimated_confidence = self._estimate_confidence(context)
            source_list = self._format_source_list(context)

            prompt = self.build_prompt(
                query=question,
                context=context_text,
                target_language=language,
                confidence=estimated_confidence,
                source_list=source_list,
            )
            
            answer = get_model_loader().llm_chat(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=self.config.top_p,
            )
            if not answer:
                return None
            
            # Validate and clean language consistency before postprocessing
            cleaned_answer = self._validate_and_clean_language(answer, language)
            postprocessed_answer = self._postprocess_answer(cleaned_answer, context, language)
            return self._enforce_language(postprocessed_answer, language)
            
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            return None
    
    def _generate_api(
        self,
        question: str,
        context: List[Dict],
        language: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Generate using API endpoint (OpenAI-compatible)"""
        try:
            context_text = self._format_context(context)
            estimated_confidence = self._estimate_confidence(context)
            source_list = self._format_source_list(context)
            prompt = self.build_prompt(
                query=question,
                context=context_text,
                target_language=language,
                confidence=estimated_confidence,
                source_list=source_list,
            )
            
            answer = get_model_loader().llm_chat(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=self.config.top_p,
            )
            if not answer:
                return None
            
            # Validate and clean language consistency
            cleaned_answer = self._validate_and_clean_language(answer, language)
            postprocessed_answer = self._postprocess_answer(cleaned_answer, context, language)
            return self._enforce_language(postprocessed_answer, language)
                
        except Exception as e:
            logger.error(f"API generation failed: {e}")
            return None
    
    def _format_context(self, context: List[Dict]) -> str:
        """Format context sources for LLM prompt"""
        formatted = []
        
        for i, source in enumerate(context[:5], 1):  # Top 5 sources
            title = source.get('title', 'Unknown')
            content = source.get('content', {})
            related = []
            if isinstance(content, dict):
                related = content.get('related_diseases', [])
            if not related:
                related = source.get('related_diseases', [])
            
            if isinstance(content, dict):
                focus = content.get('focus', '')
                data = content.get('data', [])
                
                if isinstance(data, list):
                    info = '\n  - ' + '\n  - '.join(str(x) for x in data[:5])
                else:
                    info = str(data)[:200]

                if isinstance(related, list) and related:
                    related_text = ', '.join(str(x) for x in related[:5])
                    info += f"\n  - Related diseases: {related_text}"
                
                formatted.append(f"[S{i}] {title} ({focus}):{info}")
            else:
                formatted.append(f"[S{i}] {title}: {str(content)[:200]}")
        
        return '\n\n'.join(formatted)

    def _estimate_confidence(self, context: List[Dict]) -> float:
        """Estimate answer confidence from retrieval scores in context."""
        if not context:
            return 0.0

        scores = []
        for source in context[:5]:
            raw = source.get("score", source.get("relevance_score", 0.0))
            try:
                scores.append(max(0.0, min(1.0, float(raw))))
            except Exception:
                scores.append(0.0)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _format_source_list(self, context: List[Dict]) -> str:
        """Format source IDs and names for explicit citation instructions."""
        if not context:
            return "[S1] No source available"

        lines = []
        for i, source in enumerate(context[:5], 1):
            title = source.get("title") or source.get("source") or f"Source {i}"
            lines.append(f"[S{i}] {str(title)}")
        return "\n".join(lines)

    def _validate_and_clean_language(self, answer: str, language: str) -> str:
        """
        Validate and clean language consistency.
        Remove common English phrases that leak into non-English responses.
        """
        if not answer or language in {"en", "EN", "En"}:
            return answer
        
        lang_code = (language or "en").lower().strip()
        text = str(answer)
        
        # Common English medical phrases to strip from non-English responses
        # These often appear as artifacts from LLM generation
        english_artifacts = [
            r"(?i)\bsources?\s*:", # Remove "Sources:" at end (will be added in localized form)
            r"(?i)\bNote\s+of\s+low\s+confidence", # Confidence note in English
            r"(?i)\bThis\s+information\s+is\s+for\s+educational", # English disclaimer
            r"(?i)\bPlease\s+consult\s+a\s+healthcare", # English consultation
            r"(?i)\bClinical\s+Summary", # English section header
        ]
        
        # For Arabic: remove French text artifacts
        if lang_code.startswith("ar"):
            french_artifacts = [
                r"(?u)Note\s+de\s+faible\s+confiance",
                r"(?u)données.*incomplètes",
                r"(?u)Ces\s+informations.*fournies",
                r"(?u)Veuillez\s+consulter",
            ]
            for pattern in french_artifacts:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # For French: remove English text artifacts
        elif lang_code.startswith("fr"):
            english_patterns = [
                r"\b(?i)low\s+confidence\b",
                r"\b(?i)available\s+evidence\s+may\b",
                r"\b(?i)verify\s+with\s+(?:a\s+)?(?:licensed\s+)?clinician\b",
            ]
            for pattern in english_patterns:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Remove English artifact section headers
        for pattern in english_artifacts:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace created by removals
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)
        
        return text.strip()

    def _is_language_compatible(self, text: str, target_language: str) -> bool:
        """Best-effort language match check before translating again."""
        code = _normalize_language_code(target_language)
        if not text:
            return True

        if LANGDETECT_AVAILABLE:
            try:
                detected = _langdetect_detect(text[:1000])
                if detected:
                    return detected.startswith(code)
            except Exception:
                pass

        if code == "ar":
            arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
            return arabic_chars >= max(5, len(text) * 0.08)

        if code == "fr":
            french_marks = sum(1 for c in text if c in "àâäéèêëïîôùûüÿæœç")
            french_tokens = sum(1 for token in [" le ", " la ", " les ", " et ", " des ", " une ", " un "] if token in f" {text.lower()} ")
            return (french_marks + french_tokens) > 0

        return True

    def _enforce_language(self, text: str, target_language: str) -> str:
        """Normalize the final answer language using translation when needed."""
        if not text:
            return text

        target_code = _normalize_language_code(target_language)
        if target_code == "en" or self._is_language_compatible(text, target_code):
            return text

        if not DEEP_TRANSLATOR_AVAILABLE or GoogleTranslator is None:
            return text

        try:
            translated = GoogleTranslator(source="auto", target=target_code).translate(text)
            return translated.strip() if translated else text
        except Exception as exc:
            logger.warning("Language enforcement translation failed for %s: %s", target_code, exc)
            return text

    def _postprocess_answer(self, answer: str, context: List[Dict], language: str) -> str:
        """Enforce output contract: structure, concision, and final sources block."""
        text = answer.strip()
        confidence = self._estimate_confidence(context)
        citations = self._format_source_list(context)
        labels = self._localized_labels(language)

        # Remove any existing trailing Sources/References section so we can append a single canonical one at the end.
        text = re.split(
            rf"\n\s*(?:sources|references|{re.escape(labels['sources'])})\s*:\s*",
            text,
            flags=re.IGNORECASE,
            maxsplit=1,
        )[0].strip()

        if (language or "en").strip().lower()[:2] in {"fr", "ar"}:
            normalized_lines = []
            heading_map = {
                "symptoms": labels["symptoms"],
                "causes": labels["causes"],
                "treatment": labels["treatment"],
                "sources": labels["sources"],
            }
            for line in text.splitlines():
                stripped_line = line.strip()
                heading_key = re.sub(r"^[*\s]+|[*\s]+$", "", stripped_line).rstrip(":").lower()
                if heading_key in heading_map:
                    prefix = line[: len(line) - len(line.lstrip())]
                    normalized_lines.append(f"{prefix}{heading_map[heading_key]}:")
                else:
                    normalized_lines.append(line)
            text = "\n".join(normalized_lines).strip()

        required_headers = [
            f"{labels['symptoms']}:",
            f"{labels['causes']}:",
            f"{labels['treatment']}:",
        ]
        lower_text = text.lower()
        missing_headers = [h for h in required_headers if h.lower() not in lower_text]
        if missing_headers:
            for header in missing_headers:
                text += f"\n\n{header}\n- {self._localized_missing_note(language)}"

        # Keep answer concise before adding mandatory source block.
        text = self._truncate_to_words(text, 170)

        text += f"\n\n{labels['sources']}:\n{citations}"

        if confidence < 0.5:
            disclaimer = labels["note"]
            if disclaimer.lower() not in text.lower():
                text += f"\n{disclaimer}"

        return text.strip()

    def _localized_missing_note(self, language: str) -> str:
        """Return a localized placeholder note for missing sections."""
        language_code = (language or "en").strip().lower()
        if language_code.startswith("ar"):
            return "لم يتم توضيح ذلك بوضوح في السياق المسترجع."
        if language_code.startswith("fr"):
            return "Non precise dans le contexte retrouve."
        return "Not clearly specified in the retrieved context."

    def _localized_labels(self, language: str) -> Dict[str, str]:
        """Return section labels for the requested language."""
        language_code = (language or "en").strip().lower()
        if language_code.startswith("ar"):
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
        if language_code.startswith("fr"):
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

    def _collect_section_items(self, context: List[Dict], section: str) -> List[str]:
        """Collect section items from the first relevant source."""
        for source in context[:5]:
            content = source.get("content", {})
            data = content.get("data") if isinstance(content, dict) else None

            if isinstance(data, dict):
                values = data.get(section, [])
                if isinstance(values, list):
                    return [str(item) for item in values if str(item).strip()]
                if values:
                    return [str(values)]

            if isinstance(content, dict):
                direct_values = content.get(section, [])
                if isinstance(direct_values, list) and direct_values:
                    return [str(item) for item in direct_values if str(item).strip()]
                if direct_values:
                    return [str(direct_values)]

            if isinstance(data, list):
                matches: List[str] = []
                for item in data:
                    item_text = str(item).strip()
                    if not item_text:
                        continue
                    item_lower = item_text.lower()
                    if section == "symptoms" and any(word in item_lower for word in ["symptom", "fever", "cough", "pain", "fatigue", "breath"]):
                        matches.append(item_text)
                    elif section == "causes" and any(word in item_lower for word in ["cause", "risk", "infection", "virus", "bacteria", "smoking"]):
                        matches.append(item_text)
                    elif section == "treatment" and any(word in item_lower for word in ["treat", "therapy", "antibiotic", "rest", "hydration", "monitor"]):
                        matches.append(item_text)
                if matches:
                    return matches

        return []

    def _generate_structured_template_answer(self, context: List[Dict], language: str) -> str:
        """Build a structured answer with explicit medical sections."""
        labels = self._localized_labels(language)
        top_source = context[0]
        title = top_source.get("title", labels["title"])
        category = top_source.get("category", "")
        content = top_source.get("content", {}) if isinstance(top_source, dict) else {}
        data = content.get("data", {}) if isinstance(content, dict) else {}

        parts: List[str] = [f"**{title}**"]
        if category:
            parts.append(f"*({category})*")

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
                parts.append(description)

        for section in ["symptoms", "causes", "treatment", "diagnosis", "prevention"]:
            items = self._collect_section_items(context, section)
            if not items:
                continue
            parts.append(f"\n**{labels[section]}:**")
            for item in items[:4]:
                parts.append(f"• {item}")

        if not any(self._collect_section_items(context, section) for section in ["symptoms", "causes", "treatment"]):
            parts.append(f"\n**{labels['overview']}:**")
            parts.append("• Clinical details are limited in the retrieved sources.")

        confidence = self._estimate_confidence(context)
        if confidence < 0.5:
            parts.append(labels["note"])

        parts.append(f"\n{labels['disclaimer']}")
        parts.append(f"\n{labels['sources']}:")
        parts.append(self._format_source_list(context))

        return "\n".join(parts).strip()

    def _truncate_to_words(self, text: str, max_words: int) -> str:
        """Trim text to a maximum number of words while preserving readability."""
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words]).rstrip(" ,;:")
        if not truncated.endswith("."):
            truncated += "..."
        return truncated
    
    def _generate_template_answer(
        self,
        question: str,
        context: List[Dict],
        language: str
    ) -> str:
        """Fallback template-based generation (used when LLM is disabled/unavailable)."""
        if not context:
            return self._localized_labels(language)["disclaimer"]

        return self._generate_structured_template_answer(context, language)
    
    def is_enabled(self) -> bool:
        """Check if LLM generation is enabled"""
        return self.config.enabled and (self.model is not None or self.config.backend == "api" or self.config.use_api)
    
    def get_status(self) -> Dict:
        """Get LLM status"""
        return {
            'enabled': self.config.enabled,
            'backend': self.config.backend,
            'model': self.loaded_model_name if self.loaded_model_name else (self.config.model_name if self.config.enabled else None),
            'model_loaded': self.model is not None,
            'api_configured': bool(self.config.api_endpoint and self.config.api_key)
        }


# Singleton instance
_llm_generator = None

def get_llm_generator(config: Optional[LLMConfig] = None) -> MedicalLLMGenerator:
    """Get or create LLM generator singleton"""
    global _llm_generator
    if _llm_generator is None:
        _llm_generator = MedicalLLMGenerator(config)
    return _llm_generator
