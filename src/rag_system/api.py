"""
API endpoints for RAG system
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Tuple
import re
import requests
from sqlalchemy.orm import Session

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - optional dependency
    GoogleTranslator = None

from src.utils.config import settings
from src.utils.logger import setup_logger
from src.rag_system.guards import validate_input, correct_query, guess_query_language
from src.rag_system.direct_llm import generate_direct_answer
from src.auth.middleware import get_current_user
from src.auth.models import User
from src.database import get_db
from src.auth.services.activity_service import ActivityService

logger = setup_logger(__name__)

router = APIRouter()
chat_router = APIRouter()

# ===== VALIDATION LAYER CONSTANTS =====
# LAYER 2: Similarity threshold to filter out weak retrievals
SIMILARITY_THRESHOLD = 0.65  # Require 65%+ relevance after normalization

# LAYER 4: Confidence gating - reject low-confidence answers
CONFIDENCE_THRESHOLD = 0.55  # Require 55%+ confidence in answer

# Global RAG instance
rag_system = None


def _is_rag_enabled() -> bool:
    value = getattr(settings, "USE_RAG", True)
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def init_rag():
    """Initialize RAG system"""
    global rag_system
    try:
        from src.rag_system.rag import MedicalRAG
        
        rag_system = MedicalRAG(languages=["ar", "fr", "en"])
        logger.info("RAG system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")


class QueryRequest(BaseModel):
    """Query request model"""
    question: Optional[str] = None
    query: Optional[str] = None
    language: Optional[str] = None
    top_k: int = 5
    use_rag: Optional[bool] = None
    use_reranking: bool = False
    enrich_external_sources: bool = True
    external_source_limit: int = 2
    debug: bool = False


class SourceItem(BaseModel):
    """Standardized source item"""
    title: str
    content: str
    score: float
    url: str = ""
    category: Optional[str] = None
    source_type: Optional[str] = None
    source: Optional[str] = None
    text: Optional[str] = None


class DebugMetrics(BaseModel):
    """Optional debug metrics"""
    retrieval_ms: float
    rerank_ms: float
    generation_ms: float
    total_ms: float


class QueryResponse(BaseModel):
    """Query response model"""
    answer: str
    sources: List[SourceItem]
    confidence: float
    language: str
    mode: str = "rag"
    title: str = ""
    summary: str = ""
    symptoms: List[str] = Field(default_factory=list)
    causes: List[str] = Field(default_factory=list)
    treatment: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    warning: str = ""
    labels: Dict[str, str] = Field(default_factory=dict)
    metrics: Optional[DebugMetrics] = None


def _filter_sources_by_similarity(sources: List[Dict], threshold: float = SIMILARITY_THRESHOLD) -> Tuple[List[Dict], int]:
    """
    LAYER 2: Filter sources by similarity score
    
    Removes sources with scores below threshold to prevent weak/irrelevant document matches.
    Example: "hand" should not match "hand hygiene" → covid
    
    Args:
        sources: Raw sources from retriever
        threshold: Minimum similarity score (0.0-1.0)
    
    Returns:
        Tuple of (filtered_sources, num_filtered_out)
    """
    if not sources:
        return [], 0
    
    filtered = []
    filtered_count = 0
    
    for source in sources:
        score = source.get("score", source.get("relevance_score", 0.0))
        try:
            score_float = float(score)
        except (ValueError, TypeError):
            score_float = 0.0
        
        if score_float >= threshold:
            filtered.append(source)
        else:
            filtered_count += 1
            logger.debug(f"Filtered source (score {score_float:.2f} < {threshold}): {source.get('title', 'unknown')}")
    
    return filtered, filtered_count


def _safe_text(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(_safe_text(v, "") for v in value if _safe_text(v, "").strip()) or fallback
    if isinstance(value, dict):
        for key in ("text", "answer", "content", "data", "focus", "title"):
            if key in value and value[key] is not None:
                return _safe_text(value[key], fallback)
        try:
            return str(value)
        except Exception:
            return fallback
    return fallback


def _normalize_sources(raw_sources: List[Dict]) -> List[SourceItem]:
    def _extract_content_snippet(src: Dict) -> str:
        direct = _safe_text(src.get("content") or src.get("text") or src.get("snippet") or src.get("excerpt") or src.get("summary"), "")
        if direct and direct != "{}":
            return direct[:300]

        content_obj = src.get("content")
        if isinstance(content_obj, dict):
            data = content_obj.get("data")
            if isinstance(data, list):
                joined = "; ".join(_safe_text(item, "") for item in data if _safe_text(item, "").strip())
                if joined:
                    return joined[:300]
            if isinstance(data, dict):
                joined = "; ".join(f"{k}: {_safe_text(v, '')}" for k, v in list(data.items())[:5])
                if joined:
                    return joined[:300]

        return "No source excerpt provided by backend."

    normalized: List[SourceItem] = []
    for idx, src in enumerate(raw_sources or []):
        title_value = _safe_text(src.get("title") or src.get("source"), f"Source {idx + 1}")
        content_value = _extract_content_snippet(src)
        score_value = src.get("score", src.get("relevance_score", 0.0))
        try:
            score = max(0.0, min(1.0, float(score_value)))
        except Exception:
            score = 0.0
        url_value = _safe_text(src.get("url") or src.get("source_url") or src.get("link"), "")
        normalized.append(
            SourceItem(
                title=title_value,
                content=content_value,
                score=score,
                url=url_value,
                category=_safe_text(src.get("category"), "") or None,
                source_type=_safe_text(src.get("source_type"), "") or None,
                # Backward compatibility fields for older clients.
                source=title_value,
                text=content_value,
            )
        )
    return normalized


def _language_name_to_code(language_name: str) -> str:
    """Map a human-readable language name to a supported code."""
    normalized = (language_name or "English").strip().lower()
    if normalized.startswith("ar"):
        return "ar"
    if normalized.startswith("fr"):
        return "fr"
    return "en"


def _translate_text(text: str, target_language: str) -> str:
    """Translate text to the requested language when a translator is available."""
    if not text:
        return text

    code = _language_name_to_code(target_language)
    if code == "en" or GoogleTranslator is None:
        return text

    try:
        translated = GoogleTranslator(source="auto", target=code).translate(text)
        return translated.strip() if translated else text
    except Exception:
        return text


def _extract_items_from_blob(blob: str) -> List[str]:
    """Split a noisy source blob into human-readable list items."""
    text = str(blob or "").strip()
    if not text:
        return []

    parts = re.split(r"[;\n•]+", text)
    items: List[str] = []
    for part in parts:
        item = part.strip().strip("-* ")
        if not item:
            continue
        if item not in items:
            items.append(item)
    return items


def _fetch_pubmed_sources(query: str, limit: int = 2) -> List[Dict]:
    """Fetch top PubMed references for a query using NCBI E-utilities."""
    safe_limit = max(0, min(int(limit or 0), 5))
    if safe_limit == 0:
        return []

    try:
        search_response = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "db": "pubmed",
                "retmode": "json",
                "sort": "relevance",
                "retmax": safe_limit,
                "term": query,
            },
            timeout=2.5,
        )
        search_response.raise_for_status()
        search_data = search_response.json()
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        summary_response = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={
                "db": "pubmed",
                "retmode": "json",
                "id": ",".join(id_list),
            },
            timeout=2.5,
        )
        summary_response.raise_for_status()
        summary_data = summary_response.json() or {}
        result_map = summary_data.get("result", {}) if isinstance(summary_data, dict) else {}

        external_sources: List[Dict] = []
        for rank, pmid in enumerate(id_list, start=1):
            item = result_map.get(str(pmid), {}) if isinstance(result_map, dict) else {}
            title = _safe_text(item.get("title"), "").strip()
            if not title:
                continue

            journal = _safe_text(item.get("fulljournalname") or item.get("source"), "").strip()
            pubdate = _safe_text(item.get("pubdate"), "").strip()
            first_author = _safe_text(item.get("sortfirstauthor"), "").strip()
            snippet_parts = [part for part in [journal, pubdate, first_author] if part]
            snippet = "; ".join(snippet_parts) if snippet_parts else "Peer-reviewed PubMed reference."

            external_sources.append(
                {
                    "title": title,
                    "content": snippet[:300],
                    "score": max(0.5, 0.8 - ((rank - 1) * 0.05)),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "source_type": "pubmed",
                    "category": "PubMed",
                }
            )

        return external_sources
    except Exception as exc:
        logger.warning(f"PubMed enrichment skipped: {exc}")
        return []


def _merge_sources(primary_sources: List[Dict], external_sources: List[Dict], max_total: int) -> List[Dict]:
    """Merge local RAG sources and external references without duplicate titles."""
    merged: List[Dict] = []
    seen_keys = set()

    def _add_source(source: Dict) -> None:
        key = _safe_text(source.get("title") or source.get("source"), "").lower().strip()
        if not key:
            key = _safe_text(source.get("content") or source.get("text"), "")[:80].lower().strip()
        if not key or key in seen_keys:
            return
        seen_keys.add(key)
        merged.append(source)

    for source in primary_sources or []:
        _add_source(source)
    for source in external_sources or []:
        _add_source(source)

    safe_max = max(1, int(max_total or len(merged) or 1))
    return merged[:safe_max]


def _localized_labels(language: str) -> Dict[str, str]:
    lang = (language or "en").strip().lower()
    if lang.startswith("ar"):
        return {
            "clinical_response": "الاستجابة السريرية",
            "clinical_summary": "ملخص سريري",
            "additional_symptoms": "الأعراض الإضافية",
            "symptoms": "الأعراض",
            "causes": "الأسباب",
            "treatment": "العلاج",
            "disclaimer_label": "إخلاء مسؤولية",
            "disclaimer": "هذه المعلومات لأغراض تعليمية فقط ولا تحل محل المشورة الطبية المتخصصة.",
            "warning": "تحذير",
            "sources": "المصادر",
        }
    if lang.startswith("fr"):
        return {
            "clinical_response": "Réponse clinique",
            "clinical_summary": "Résumé clinique",
            "additional_symptoms": "Symptômes supplémentaires",
            "symptoms": "Symptômes",
            "causes": "Causes",
            "treatment": "Traitement",
            "disclaimer_label": "Avertissement",
            "disclaimer": "Ces informations sont fournies à des fins éducatives uniquement et ne remplacent pas l'avis d'un professionnel de santé.",
            "warning": "Avertissement",
            "sources": "Sources",
        }
    return {
        "clinical_response": "Clinical Response",
        "clinical_summary": "Clinical Summary",
        "additional_symptoms": "Additional Symptoms",
        "symptoms": "Symptoms",
        "causes": "Causes",
        "treatment": "Treatment",
        "disclaimer_label": "Disclaimer",
        "disclaimer": "This information is for educational purposes only and does not replace professional medical advice.",
        "warning": "Warning",
        "sources": "Sources",
    }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _strip_noise_from_answer(answer: str) -> str:
    text = str(answer or "").strip()
    if not text:
        return ""

    text = re.split(r"\n\s*(?:sources?|references?|disclaimer|warning|note)\s*:.*$", text, flags=re.IGNORECASE | re.MULTILINE)[0].strip()
    return text


def _heading_to_section(heading: str, language: str) -> Optional[str]:
    normalized = _normalize_text(heading).rstrip(":")
    labels = _localized_labels(language)
    lookup = {
        _normalize_text(labels["symptoms"]): "symptoms",
        _normalize_text(labels["causes"]): "causes",
        _normalize_text(labels["treatment"]): "treatment",
        _normalize_text(labels["clinical_summary"]): "summary",
        _normalize_text(labels["clinical_response"]): "summary",
        "symptoms": "symptoms",
        "symptomes": "symptoms",
        "symptômes": "symptoms",
        "الأعراض": "symptoms",
        "causes": "causes",
        "سبب": "causes",
        "الأسباب": "causes",
        "treatment": "treatment",
        "traitement": "treatment",
        "العلاج": "treatment",
        "summary": "summary",
        "resume clinique": "summary",
        "résumé clinique": "summary",
        "clinical summary": "summary",
        "clinical response": "summary",
    }
    return lookup.get(normalized)


def _prepare_answer_for_parsing(answer: str, language: str) -> str:
    """Expand compact markdown into line-based sections for robust parsing."""
    text = str(answer or "").replace("\r\n", "\n").replace("\r", "\n")
    labels = _localized_labels(language)

    heading_terms = [
        labels.get("clinical_response", "Clinical Response"),
        labels.get("clinical_summary", "Clinical Summary"),
        labels.get("additional_symptoms", "Additional Symptoms"),
        labels.get("symptoms", "Symptoms"),
        labels.get("causes", "Causes"),
        labels.get("treatment", "Treatment"),
        "Summary",
        "Clinical Summary",
        "Clinical Response",
        "Symptoms",
        "Causes",
        "Treatment",
        "Symptomes",
        "Symptômes",
        "Traitement",
        "الأعراض",
        "الأسباب",
        "العلاج",
    ]

    heading_pattern = r"(?i)(?<!\n)(\*{0,3}\s*(?:" + "|".join(re.escape(term) for term in heading_terms) + r")\s*\*{0,3}\s*:)"
    text = re.sub(heading_pattern, r"\n\1\n", text)
    text = re.sub(r"(?<!\n)([-*•]\s+)", r"\n\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_structured_sections(answer: str, language: str) -> Dict[str, List[str]]:
    sections = {"summary": [], "symptoms": [], "causes": [], "treatment": []}
    current = "summary"

    prepared_answer = _prepare_answer_for_parsing(answer, language)

    for raw_line in prepared_answer.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[*_]+\s*(.+?)\s*[*_]+$", r"\1", line).strip()
        heading = _heading_to_section(line, language)
        if heading:
            current = heading
            continue

        if re.match(r"^[-*•]\s+", line):
            line = re.sub(r"^[-*•]\s+", "", line).strip()

        if current in sections:
            sections[current].append(line)

    sections["summary"] = [item for item in sections["summary"] if item]
    sections["symptoms"] = [item for item in sections["symptoms"] if item]
    sections["causes"] = [item for item in sections["causes"] if item]
    sections["treatment"] = [item for item in sections["treatment"] if item]
    return sections


def _fallback_sections_from_sources(sources: List[Dict], language: str) -> Dict[str, List[str]]:
    """Derive sections from retrieved source blobs when answer parsing is noisy."""
    sections = {"summary": [], "symptoms": [], "causes": [], "treatment": []}
    if not sources:
        return sections

    target_code = _language_name_to_code(language)
    candidate_blobs = []
    for source in sources[:3]:
        blob = source.get("text") or source.get("content") or source.get("summary") or ""
        if isinstance(blob, dict):
            blob = blob.get("text") or blob.get("content") or blob.get("summary") or blob.get("data") or ""
        if isinstance(blob, list):
            blob = "; ".join(str(item) for item in blob if str(item).strip())
        if blob:
            candidate_blobs.append(str(blob))

    if candidate_blobs:
        merged_blob = "; ".join(candidate_blobs)
        extracted = _extract_items_from_blob(merged_blob)
        if extracted:
            translated = [_translate_text(item, target_code) for item in extracted if item.strip()]
            sections["symptoms"] = [item for item in translated if item]

    # Also look for causes and treatment patterns in sources
    full_text = " ".join(candidate_blobs)
    
    # Extract potential causes (look for disease-related terms)
    cause_keywords = ["infection", "bacterial", "viral", "fungal", "allergen", "inhalation", "exposure"]
    cause_patterns = [
        r"(?i)(caused by|due to|result of|following|secondary to).*?(?:\.|;|$)",
        r"(?i)(risk factor|etiology|pathogen|organism).*?(?:\.|;|$)",
    ]
    for pattern in cause_patterns:
        for match in re.finditer(pattern, full_text):
            item = str(match.group(0)).strip().strip(".;")
            if item and len(item) > 5:
                translated = _translate_text(item, target_code)
                if translated and translated not in sections["causes"]:
                    sections["causes"].append(translated)
            if len(sections["causes"]) >= 4:
                break
    
    # Extract potential treatments (look for management/therapy terms)
    treatment_keywords = ["antibiotic", "therapy", "treatment", "management", "oxygen", "supportive"]
    treatment_patterns = [
        r"(?i)(treatment|therapy|management|antibiotic|medication|oxygen).*?(?:\.|;|$)",
        r"(?i)(patient.*?receive|administer|prescribe).*?(?:\.|;|$)",
    ]
    for pattern in treatment_patterns:
        for match in re.finditer(pattern, full_text):
            item = str(match.group(0)).strip().strip(".;")
            if item and len(item) > 5:
                translated = _translate_text(item, target_code)
                if translated and translated not in sections["treatment"]:
                    sections["treatment"].append(translated)
            if len(sections["treatment"]) >= 4:
                break

    return sections


def _extract_title_and_summary(question: str, sources: List[Dict], answer: str, language: str) -> Tuple[str, str]:
    top_source = sources[0] if sources else {}
    top_title = _safe_text(top_source.get("title") or top_source.get("source"), "")
    top_category = _safe_text(top_source.get("category"), "")

    cleaned_answer = _strip_noise_from_answer(answer)
    first_paragraph = cleaned_answer.split("\n\n", 1)[0].strip()
    candidate_lines = []
    for line in first_paragraph.splitlines():
        stripped = re.sub(r"^\*\*(.+)\*\*$", r"\1", line).strip()
        stripped = re.sub(r"^\*\((.+)\)\*$", r"\1", stripped).strip()
        if stripped:
            candidate_lines.append(stripped)

    if not top_title:
        q = _safe_text(question, "Medical information").strip()
        top_title = q[:1].upper() + q[1:] if q else "Medical information"

    meaningful_lines = [
        line for line in candidate_lines
        if _normalize_text(line) not in {_normalize_text(top_title), _normalize_text(top_category)}
    ]

    if meaningful_lines:
        summary = " ".join(meaningful_lines)
    else:
        summary = ""

    if _normalize_text(summary) in {_normalize_text(top_title), _normalize_text(f"{top_title} ({top_category})")}:
        summary = ""

    if not summary:
        for source in sources[:3]:
            blob = source.get("content") or source.get("text") or source.get("summary") or ""
            if isinstance(blob, dict):
                blob = blob.get("summary") or blob.get("text") or blob.get("data") or ""
            if isinstance(blob, list):
                blob = "; ".join(str(item) for item in blob if str(item).strip())
            snippet = _safe_text(blob, "").strip()
            if snippet:
                summary = re.split(r"[\n\.]", snippet, maxsplit=1)[0].strip()
                if summary:
                    break

    # Translate title to target language if not English
    if language != "en":
        top_title = _translate_text(top_title, language)
        if summary:
            summary = _translate_text(summary, language)
    return top_title, summary


def _select_display_sources(sources: List[Dict], max_sources: int = 3, min_score: float = 0.30) -> List[Dict]:
    ranked = []
    for source in sources or []:
        try:
            score = float(source.get("score", source.get("relevance_score", 0.0)))
        except Exception:
            score = 0.0
        ranked.append((score, source))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected: List[Dict] = []
    seen_titles = set()
    for score, source in ranked:
        title = _safe_text(source.get("title") or source.get("source"), "").lower().strip()
        if title and title in seen_titles:
            continue
        if len(selected) >= max_sources:
            break
        if score < min_score:
            continue
        if title:
            seen_titles.add(title)
        selected.append(source)

    return selected[:max_sources]


def _sanitize_language_contamination(text: str, language: str) -> str:
    """
    Remove common language contamination artifacts from multilingual responses.
    Prevents French/English text from appearing in Arabic responses and vice versa.
    """
    if not text or language in {"en", "EN", "En"}:
        return text
    
    lang_code = (language or "en").lower().strip()
    output = str(text)
    
    # Define contamination patterns for each language
    contamination_patterns = {
        "ar": [
            # French phrases that often leak into Arabic
            r"(?u)Note\s+de\s+faible\s+confiance.*?(?=\n|$)",
            r"(?u)les\s+données.*?incomplètes.*?(?=\n|$)",
            r"(?u)Veuillez\s+consulter.*?(?=\n|$)",
            r"(?u)Ces\s+informations\s+sont.*?(?=\n|$)",
            # English phrases
            r"(?i)\bLow\s+confidence\s+note.*?(?=\n|$)",
            r"(?i)\bAvailable\s+evidence.*?(?=\n|$)",
            r"(?i)\bVerify\s+with.*?(?=\n|$)",
        ],
        "fr": [
            # English phrases that leak into French
            r"(?i)\blow\s+confidence.*?(?=\n|$)",
            r"(?i)\bavailable\s+evidence.*?(?=\n|$)",
            r"(?i)\bverify\s+with.*?(?=\n|$)",
            r"(?i)\bthis\s+information.*?(?=\n|$)",
            # Arabic phrases (detect Arabic script)
            r"[\u0600-\u06FF].*?(?=\n|$)",  # Only if it's supposed to be pure French
        ],
    }
    
    # Apply contamination removal for the target language
    if lang_code.startswith("ar") or lang_code.startswith("fr"):
        patterns = contamination_patterns.get(lang_code[:2], [])
        for pattern in patterns:
            output = re.sub(pattern, "", output, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean excessive whitespace
    output = re.sub(r"\n\s*\n\s*\n+", "\n\n", output)
    output = re.sub(r"^\s+|\s+$", "", output, flags=re.MULTILINE)
    
    return output.strip()


def _format_structured_response(
    *,
    question: str,
    answer: str,
    sources: List[Dict],
    confidence: float,
    language: str,
    mode: str,
    warning: Optional[str],
) -> Dict:
    labels = _localized_labels(language)
    
    # Sanitize answer to remove language contamination before extraction
    sanitized_answer = _sanitize_language_contamination(answer, language)
    
    # Treat error/fallback messages as empty for fallback section extraction
    error_indicators = ["temporary processing issue", "could not find relevant", "could not process"]
    is_error_answer = any(indicator.lower() in sanitized_answer.lower() for indicator in error_indicators)
    
    structured_sections = _extract_structured_sections(sanitized_answer, language) if not is_error_answer else {}
    if not any(structured_sections.values()):
        structured_sections = _fallback_sections_from_sources(sources, language)

    title, summary = _extract_title_and_summary(question, sources, sanitized_answer, language)
    selected_sources = _select_display_sources(sources, max_sources=3, min_score=0.30)
    
    # Sanitize all section content as well
    cleaned_sections = {
        section: [_sanitize_language_contamination(item, language) for item in items]
        for section, items in structured_sections.items()
    }

    noisy_summary_markers = ["**", "•", "Symptoms:", "Causes:", "Treatment:", "Symptomes:", "الأعراض:", "الأسباب:", "العلاج:"]
    if summary and any(marker.lower() in summary.lower() for marker in noisy_summary_markers):
        summary = ""

    if language != "en" and summary:
        summary = _translate_text(summary, language)

    if language != "en":
        for section_name in ("symptoms", "causes", "treatment"):
            cleaned_sections[section_name] = [
                _translate_text(item, language) for item in cleaned_sections[section_name]
            ]

    return {
        "answer": summary,
        "title": title,
        "summary": summary,
        "symptoms": cleaned_sections["symptoms"],
        "causes": cleaned_sections["causes"],
        "treatment": cleaned_sections["treatment"],
        "sources": _normalize_sources(selected_sources),
        "confidence": confidence,
        "language": language,
        "mode": mode,
        "disclaimer": labels["disclaimer"],
        "warning": warning or "",
        "labels": labels,
    }


@router.post("/query", response_model=QueryResponse, response_model_exclude_none=True)
async def query_knowledge_base(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    """
    Query the medical knowledge base with fallback-aware pipeline
    
    - **question**: Medical question in Arabic, French, or English
    - **language**: Optional language code (ar, fr, en) - auto-detected if not provided
    - **top_k**: Number of sources to retrieve
    - **use_reranking**: Use cross-encoder reranking (not implemented yet)
    - **enrich_external_sources**: Enable PubMed enrichment (default: True)
    
    ACTIVE SAFETY LAYERS:
    - Layer 1: Medical intent detection (reject non-medical queries)
    - Layer 3: LLM guardrail prompt (force refusal for unclear questions)
    - Layer 5: Optional spell correction

    Layer 2 and Layer 4 are intentionally skipped at API level.
    """
    if rag_system is None:
        init_rag()
        if rag_system is None:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    try:
        normalized_question = (request.question or request.query or "").strip()
        if not normalized_question:
            raise HTTPException(status_code=422, detail="Field 'question' is required")

        request_language = _language_name_to_code(request.language or settings.DEFAULT_LANGUAGE)

        if not _is_rag_enabled():
            labels = _localized_labels(request_language)
            direct = generate_direct_answer(normalized_question, request_language)
            
            # Record activity for direct LLM mode
            activity_service = ActivityService(db)
            await activity_service.record_activity(
                user_id=current_user.id,
                activity_type='chat',
                metadata={
                    'query': normalized_question[:100],
                    'language': request_language,
                    'mode': 'direct_llm'
                }
            )
            
            return QueryResponse(
                answer=_safe_text(direct.get("summary"), ""),
                sources=[],
                confidence=0.8,
                language=request_language,
                mode="direct_llm",
                title=_safe_text(direct.get("title"), ""),
                summary=_safe_text(direct.get("summary"), ""),
                symptoms=list(direct.get("symptoms") or []),
                causes=list(direct.get("causes") or []),
                treatment=list(direct.get("treatment") or []),
                disclaimer=_safe_text(direct.get("disclaimer"), labels["disclaimer"]),
                warning=_safe_text(direct.get("warning"), ""),
                labels=labels,
            )

        # ===== LAYER 5: OPTIONAL SPELL CORRECTION =====
        corrected_question = correct_query(normalized_question)
        if corrected_question != normalized_question:
            logger.info(f"Spell-corrected query: '{normalized_question}' -> '{corrected_question}'")
        normalized_question = corrected_question

        # ===== LAYER 1: INPUT VALIDATION & MEDICAL INTENT =====
        is_valid, error_msg = validate_input(normalized_question)
        if not is_valid:
            logger.warning(f"Input validation failed: {error_msg} | Query: {normalized_question}")
            warning_text = error_msg or 'Please ask a clear medical question (e.g., "What are symptoms of pneumonia?")'
            labels = _localized_labels(request_language)
            return QueryResponse(
                answer=f"Warning: {warning_text}",
                sources=[],
                confidence=0.0,
                language=request_language,
                mode="blocked",
                title="",
                summary="",
                symptoms=[],
                causes=[],
                treatment=[],
                disclaimer=labels["disclaimer"],
                warning=warning_text,
                labels=labels,
            )

        # Query the RAG system
        result = rag_system.query(
            question=normalized_question,
            language=request_language,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
        )

        raw_sources = list(result.sources or [])

        # Layer 2 intentionally skipped per objective.
        
        # Enrich with external sources if enabled
        if request.enrich_external_sources:
            external_sources = _fetch_pubmed_sources(normalized_question, request.external_source_limit)
            raw_sources = _merge_sources(
                raw_sources,
                external_sources,
                max_total=max(1, request.top_k + max(0, request.external_source_limit)),
            )

        confidence = max(0.0, min(1.0, float(result.confidence or 0.0)))
        language = _safe_text(result.language, request_language or "en")
        answer = _safe_text(result.answer, "No answer available.")
        mode = _safe_text(getattr(result, "mode", None), "rag")
        structured = _format_structured_response(
            question=normalized_question,
            answer=answer,
            sources=raw_sources,
            confidence=confidence,
            language=language,
            mode=mode,
            warning=None,
        )

        # ===== LAYER 3: LLM GUARDRAIL (implicit via RAG system prompt) =====
        # The RAG system uses a prompt that includes guardrail instructions
        # to refuse when unclear, not medical, etc. (Implemented in rag.py)

        # Layer 4 intentionally skipped per objective.

        metrics = None
        if request.debug:
            raw_metrics = result.metrics or {}
            metrics = DebugMetrics(
                retrieval_ms=float(raw_metrics.get("retrieval_ms", 0.0)),
                rerank_ms=float(raw_metrics.get("rerank_ms", 0.0)),
                generation_ms=float(raw_metrics.get("generation_ms", 0.0)),
                total_ms=float(raw_metrics.get("total_ms", 0.0)),
            )
        
        logger.info(f"Query successful: confidence={confidence:.2f}, sources={len(structured['sources'])}")
        
        # Record activity after successful query
        activity_service = ActivityService(db)
        await activity_service.record_activity(
            user_id=current_user.id,
            activity_type='chat',
            metadata={
                'query': normalized_question[:100],  # Truncate for storage
                'language': language,
                'confidence': confidence,
                'mode': mode,
                'sources_count': len(structured['sources'])
            }
        )
        
        return QueryResponse(
            answer=structured["answer"],
            sources=structured["sources"],
            confidence=confidence,
            language=language,
            mode=mode,
            title=structured["title"],
            summary=structured["summary"],
            symptoms=structured["symptoms"],
            causes=structured["causes"],
            treatment=structured["treatment"],
            disclaimer=structured["disclaimer"],
            warning=structured["warning"],
            labels=structured["labels"],
            metrics=metrics,
        )
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/chat", response_model=QueryResponse, response_model_exclude_none=True)
async def chat(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    """Unified chat endpoint supporting both RAG and direct LLM modes."""
    return await query_knowledge_base(request, current_user, db)


@router.get("/languages")
async def get_supported_languages() -> Dict:
    """Get list of supported languages"""
    return {
        "languages": [
            {"code": "ar", "name": "Arabic", "native": "العربية"},
            {"code": "fr", "name": "French", "native": "Français"},
            {"code": "en", "name": "English", "native": "English"},
        ],
        "default": "ar"
    }


@router.get("/examples")
async def get_example_queries() -> Dict:
    """Get example queries in different languages"""
    return {
        "examples": [
            {
                "language": "ar",
                "question": "ما هي أعراض الالتهاب الرئوي؟",
                "translation": "What are the symptoms of pneumonia?"
            },
            {
                "language": "fr",
                "question": "Comment traiter le COVID-19?",
                "translation": "How to treat COVID-19?"
            },
            {
                "language": "en",
                "question": "What are tuberculosis symptoms?",
                "translation": "What are tuberculosis symptoms?"
            }
        ]
    }


@router.get("/health")
async def health_check() -> Dict:
    """Check RAG service health"""
    if rag_system is None:
        init_rag()
    
    return {
        "status": "healthy" if rag_system is not None else "not_initialized",
        "system_loaded": rag_system is not None,
        "languages": ["ar", "fr", "en"] if rag_system else [],
    }
