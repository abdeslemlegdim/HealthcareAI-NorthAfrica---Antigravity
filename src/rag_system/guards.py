"""
Input validation and safety guards for medical queries
Implements 5-layer validation pipeline to prevent hallucination and garbage responses
"""
import re
import unicodedata
from typing import Tuple, Optional
import importlib
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Comprehensive medical keywords across major categories
MEDICAL_KEYWORDS = {
    # Symptoms
    "pain", "fever", "cough", "headache", "nausea", "fatigue", "dizziness", "rash",
    "symptom", "ache", "soreness", "inflammation", "swelling", "bleeding", "discharge",
    "weakness", "shortness", "breath", "difficulty", "trouble", "ache", "cramp",
    # Diseases / Conditions
    "disease", "illness", "condition", "disorder", "disease", "syndrome", "infection",
    "pneumonia", "tuberculosis", "diabetes", "hypertension", "cancer", "covid", "covid-19",
    "asthma", "arthritis", "migraine", "depression", "anxiety", "alzheimer",
    "parkinson", "stroke", "heart", "kidney", "liver", "lung", "cancer", "leukemia",
    # Treatments
    "treatment", "therapy", "medication", "medicine", "drug", "vaccine", "injection",
    "surgery", "procedure", "exercise", "diet", "therapy", "antibiotics", "antibiotic",
    "chemotherapy", "radiation", "rehab", "physiotherapy", "physical",
    # Medical Processes
    "diagnosis", "test", "scan", "xray", "mri", "ultrasound", "blood", "urine",
    "biopsy", "endoscopy", "colonoscopy", "surgery", "vaccination", "quarantine",
    # Health-related
    "health", "medical", "doctor", "physician", "nurse", "hospital", "clinic",
    "emergency", "urgent", "acute", "chronic", "viral", "bacterial", "fungal",
    "allergy", "immune", "vaccine", "side", "effect", "adverse", "reaction",
    # Body parts
    "head", "brain", "heart", "lung", "liver", "kidney", "stomach", "intestine",
    "bone", "muscle", "blood", "nerve", "skin", "eye", "ear", "throat", "chest",
    "back", "joint", "spine", "organ", "cell", "tissue", "gland",
    # French medical terms
    "symptome", "symptomes", "douleur", "maladie", "traitement", "infection", "fievre",
    "pneumonie", "toux", "diagnotic", "sante", "hôpital", "hopital", "medecin", "docteur",
    # Arabic medical terms
    "اعراض", "عرض", "مرض", "امراض", "علاج", "التهاب", "حمى", "سعال", "الم", "الم في", "طبيب", "مستشفى", "رئة", "صدر", "تنفس",
}

# Crisis/Emergency keywords that require special handling
CRISIS_KEYWORDS = {
    # English
    "suicide", "suicidal", "kill myself", "end my life", "want to die", "going to die",
    "i died", "i'm dying", "im dying", "i am dying", "dying", "dead", "i'm dead", "im dead",
    "kill me", "hurt myself", "harm myself", "self harm", "cut myself", "overdose",
    "jump off", "hang myself", "shoot myself", "end it all", "no reason to live",
    # French
    "suicide", "suicidaire", "me tuer", "mettre fin", "veux mourir", "je meurs",
    "je suis mort", "mort", "mourir", "me faire mal", "automutilation",
    # Arabic
    "انتحار", "اقتل نفسي", "اموت", "انا ميت", "اريد ان اموت", "ايذاء النفس",
}

# Non-medical or ambiguous keywords that commonly appear in non-medical queries
NON_MEDICAL_PATTERNS = [
    r"^(hello|hi|hey|how are you|what\s+is\s+your\s+name|who are you)",
    r"^(joke|funny|meme|game|music|movie|sport|football|basketball)",
    r"^(weather|forecast|temperature|climate|rain|snow|wind)",
    r"^(news|political|politics|election|president|minister)",
    r"take\s+a\s+(\w+\s+)?joke",
]

COMMON_QUERY_PUNCTUATION = set("?!.,،؟:;-'\"()[]{}")


def _normalize_for_matching(text: str) -> str:
    """Normalize text for multilingual keyword matching."""
    if not text:
        return ""

    normalized = text.lower().strip()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    translations = str.maketrans({
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ة": "ه",
    })
    normalized = normalized.translate(translations)
    return normalized


def is_medical_query(query: str, min_medical_words: int = 1) -> bool:
    """
    LAYER 1: Check if query has genuine medical intent
    
    Rules:
    1. Minimum 2 words
    2. At least 1 medical keyword match
    3. Not matching non-medical patterns
    
    Args:
        query: User's input question
        min_medical_words: Minimum medical keywords needed (default 1)
    
    Returns:
        True if query appears medical, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    normalized = _normalize_for_matching(query)
    
    # Reject very short input
    word_count = len(normalized.split())
    if word_count < 2:
        logger.debug(f"Query too short ({word_count} words): {query}")
        return False
    
    # Check against non-medical patterns (positive rejection)
    for pattern in NON_MEDICAL_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            logger.debug(f"Query matches non-medical pattern '{pattern}': {query}")
            return False
    
    # Count medical keyword matches using language-aware matching.
    medical_count = 0
    for keyword in MEDICAL_KEYWORDS:
        if _matches_keyword(normalized, keyword):
            medical_count += 1
    
    has_medical_intent = medical_count >= min_medical_words
    if not has_medical_intent:
        logger.debug(f"Insufficient medical keywords ({medical_count} < {min_medical_words}): {query}")
    
    return has_medical_intent


def validate_query_length(query: str, min_length: int = 5, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Validate query length to prevent abuse
    
    Args:
        query: User's query
        min_length: Minimum characters
        max_length: Maximum characters
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not query:
        return False, "Query cannot be empty"
    
    if len(query) < min_length:
        return False, f"Query too short (minimum {min_length} characters)"
    
    if len(query) > max_length:
        return False, f"Query too long (maximum {max_length} characters)"
    
    return True, None


def detect_spam_patterns(query: str) -> Tuple[bool, Optional[str]]:
    """
    Detect potential spam or malicious patterns
    
    Returns:
        Tuple (is_spam, reason)
    """
    if not query:
        return False, None
    
    normalized = _normalize_for_matching(query)

    # Only apply repetition heuristics to mostly Latin text to avoid false positives on Arabic/French input.
    if _is_latin_query(normalized):
        # Excessive repetition (more than 3 repeated chars)
        if re.search(r'(.)\1{3,}', normalized):
            return True, "Query contains excessive character repetition"
    
    # Too many special characters
    special_count = sum(
        1
        for c in query
        if not c.isalnum() and not c.isspace() and c not in COMMON_QUERY_PUNCTUATION
    )
    special_ratio_threshold = 0.3 if _is_latin_query(normalized) else 0.45
    if special_count > len(query) * special_ratio_threshold:
        return True, "Query contains too many special characters"
    
    # SQL injection-like patterns
    if any(keyword in normalized for keyword in ["drop", "delete", "insert", "union", "select"]):
        if re.search(r"(from|table|database|query)", normalized):
            return True, "Query contains suspicious technical patterns"
    
    return False, None


def detect_crisis_situation(query: str) -> Tuple[bool, Optional[str]]:
    """
    Detect crisis/emergency situations that require immediate human intervention
    
    Returns:
        Tuple (is_crisis, crisis_message)
    """
    if not query:
        return False, None
    
    normalized = _normalize_for_matching(query)
    
    # Check for crisis keywords
    for keyword in CRISIS_KEYWORDS:
        if _matches_keyword(normalized, keyword):
            logger.warning(f"Crisis keyword detected: '{keyword}' in query: {query}")
            
            # Return appropriate crisis response based on language
            lang = guess_query_language(query)
            
            if lang == "ar":
                return True, (
                    "🆘 **إذا كنت في أزمة أو تفكر في إيذاء نفسك، يرجى طلب المساعدة الفورية:**\n\n"
                    "• **الطوارئ:** اتصل بـ 911 أو رقم الطوارئ المحلي\n"
                    "• **خط الأزمات:** اتصل بخط المساعدة للصحة النفسية في بلدك\n"
                    "• **تحدث إلى شخص ما:** اتصل بصديق أو أحد أفراد الأسرة أو متخصص في الصحة النفسية\n\n"
                    "أنت لست وحدك. المساعدة متاحة."
                )
            elif lang == "fr":
                return True, (
                    "🆘 **Si vous êtes en crise ou pensez à vous faire du mal, veuillez demander de l'aide immédiatement:**\n\n"
                    "• **Urgences:** Appelez le 911 ou votre numéro d'urgence local\n"
                    "• **Ligne de crise:** Contactez une ligne d'assistance en santé mentale\n"
                    "• **Parlez à quelqu'un:** Appelez un ami, un membre de votre famille ou un professionnel de la santé mentale\n\n"
                    "Vous n'êtes pas seul(e). De l'aide est disponible."
                )
            else:  # English
                return True, (
                    "🆘 **If you're in crisis or thinking about harming yourself, please seek immediate help:**\n\n"
                    "• **Emergency:** Call 911 or your local emergency number\n"
                    "• **Crisis Line:** Contact a mental health helpline in your country\n"
                    "• **Talk to someone:** Call a friend, family member, or mental health professional\n\n"
                    "You are not alone. Help is available."
                )
    
    return False, None


def suggest_rephrasing(query: str) -> Optional[str]:
    """
    Provide helpful guidance if query is rejected
    
    Returns:
        Suggested rephrasing or None
    """
    normalized = _normalize_for_matching(query)
    
    if len(normalized.split()) < 2:
        return "Please provide a complete medical question, e.g., 'What are the symptoms of pneumonia?'"
    
    if not any(_matches_keyword(normalized, keyword) for keyword in MEDICAL_KEYWORDS):
        return "Your question doesn't appear to be medical. Try asking about a symptom, disease, or treatment."
    
    return "Please rephrase your question more clearly. Examples: 'What causes headaches?', 'How to treat diabetes?'"


def validate_input(query: str) -> Tuple[bool, Optional[str]]:
    """
    COMPREHENSIVE INPUT VALIDATION
    Combines all guard checks including crisis detection
    
    Returns:
        Tuple (is_valid, rejection_reason)
    """
    # Check 0: Crisis detection (HIGHEST PRIORITY)
    is_crisis, crisis_message = detect_crisis_situation(query)
    if is_crisis:
        return False, crisis_message
    
    # Check 1: Length validation
    length_valid, length_error = validate_query_length(query)
    if not length_valid:
        return False, length_error
    
    # Check 2: Spam detection
    is_spam, spam_reason = detect_spam_patterns(query)
    if is_spam:
        return False, f"Query rejected: {spam_reason}"
    
    # Check 3: Medical intent
    if not is_medical_query(query):
        suggestion = suggest_rephrasing(query)
        return False, suggestion or "Please ask a clear medical question."
    
    return True, None


def _is_latin_query(query: str) -> bool:
    """Only spell-correct mostly Latin queries to avoid harming Arabic/French accents."""
    letters = [ch for ch in query if ch.isalpha()]
    if not letters:
        return False
    latin_letters = [ch for ch in letters if "a" <= ch.lower() <= "z"]
    return (len(latin_letters) / len(letters)) >= 0.8


def _matches_keyword(text: str, keyword: str) -> bool:
    """Language-aware keyword matching for medical intent detection."""
    if not text or not keyword:
        return False
    if _is_latin_query(text) and _is_latin_query(keyword):
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return _normalize_for_matching(keyword) in _normalize_for_matching(text)


def guess_query_language(query: str) -> str:
    """Best-effort query language guess for validation and correction."""
    if not query:
        return "en"
    normalized = query.strip().lower()
    if any("\u0600" <= ch <= "\u06ff" for ch in normalized):
        return "ar"
    french_markers = [" sympt", " douleur", " traitement", " maladie", " quelle", " quels ", " symptomes", " symptômes"]
    if any(marker in normalized for marker in french_markers):
        return "fr"
    return "en"


def correct_query(query: str) -> str:
    """
    LAYER 5: Optional spell correction.

    Applies lightweight TextBlob correction for likely-English medical queries.
    Falls back to original query when unavailable or unsafe.
    """
    if not query or not isinstance(query, str):
        return query

    candidate = query.strip()
    if len(candidate.split()) < 2:
        return candidate

    if guess_query_language(candidate) != "en":
        return candidate

    try:
        textblob_module = importlib.import_module("textblob")
        TextBlob = getattr(textblob_module, "TextBlob", None)
        if TextBlob is None:
            return candidate

        corrected = str(TextBlob(candidate).correct()).strip()
        if not corrected:
            return candidate

        # Keep correction only when change is small and likely typo-fix.
        if corrected.lower() == candidate.lower():
            return candidate
        length_ratio = len(corrected) / max(1, len(candidate))
        if length_ratio < 0.7 or length_ratio > 1.3:
            return candidate
        return corrected
    except Exception:
        return candidate
