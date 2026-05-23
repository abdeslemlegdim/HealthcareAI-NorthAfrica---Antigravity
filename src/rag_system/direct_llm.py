"""Direct LLM generation path with strict JSON contract."""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List
import requests

from src.models.model_loader import get_model_loader
from src.utils.config import settings


def _normalize_language(language: str) -> str:
    value = str(language or "en").strip().lower()
    if value.startswith("ar"):
        return "ar"
    if value.startswith("fr"):
        return "fr"
    return "en"


def build_direct_prompt(query: str, language: str) -> str:
    code = _normalize_language(language)
    lang_map = {
        "en": "English",
        "fr": "French",
        "ar": "Arabic",
    }

    return f"""
You are a professional medical assistant.

Respond ONLY in {lang_map[code]}.

Return your answer STRICTLY in this JSON format:

{{
  "title": "...",
  "summary": "...",
  "symptoms": ["...", "..."],
  "causes": ["...", "..."],
  "treatment": ["...", "..."],
  "warning": "...",
  "disclaimer": "..."
}}

Rules:
- Do NOT mix languages
- Do NOT return text outside JSON
- Keep answers medically accurate but simple
- If unsure, still provide general medical knowledge
- Always fill all fields (no empty lists)

Question: {query}
""".strip()


def _call_llm(prompt: str) -> str:
    response = get_model_loader().llm_chat(
        prompt=prompt,
        system_prompt="You are a strict JSON-only medical assistant.",
        max_tokens=320,
        temperature=0.2,
        top_p=0.9,
    )
    return str(response or "").strip()


def _should_use_runtime_llm() -> bool:
    # Try runtime LLM when explicitly enabled or when an endpoint is configured.
    return bool(
        getattr(settings, "USE_LLM_API", False)
        or str(getattr(settings, "LLM_API_ENDPOINT", "") or "").strip()
    )


def _get_hf_token() -> str:
    placeholder_values = {
        "your-hf-token",
        "hf-token",
        "token",
        "",
    }

    def _clean(value: str) -> str:
        token = str(value or "").strip()
        if not token or token.lower() in placeholder_values:
            return ""
        return token

    token = str(getattr(settings, "HUGGINGFACE_TOKEN", "") or "").strip()
    cleaned = _clean(token)
    if cleaned:
        return cleaned

    env_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or ""
    return _clean(env_token)


def _hf_model_candidates() -> List[str]:
    candidates: List[str] = []

    api_models = str(getattr(settings, "LLM_API_MODELS", "") or "").strip()
    if api_models:
        for item in api_models.split(","):
            model = item.strip()
            if model:
                candidates.append(model)

    configured = [
        str(getattr(settings, "LLM_MODEL", "") or "").strip(),
        str(getattr(settings, "LLM_MODEL_NAME", "") or "").strip(),
        "Qwen/Qwen2.5-1.5B-Instruct",
        "microsoft/Phi-3-mini-4k-instruct",
    ]
    candidates.extend(model for model in configured if model)

    # Keep order but remove duplicates and obvious placeholders.
    seen = set()
    unique: List[str] = []
    for model in candidates:
        key = model.lower().strip()
        if not key or key in seen or key in {"your-model", "model-name"}:
            continue
        seen.add(key)
        unique.append(model)
    return unique


def _call_huggingface_inference(prompt: str) -> str:
    token = _get_hf_token()
    if not token:
        return ""

    model_candidates = _hf_model_candidates()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for model_name in model_candidates:
        url = f"https://api-inference.huggingface.co/models/{model_name}"
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 320,
                "temperature": 0.2,
                "return_full_text": False,
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False,
            },
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            if response.status_code >= 400:
                continue
            data = response.json()

            if isinstance(data, list) and data:
                first = data[0]
                if isinstance(first, dict):
                    generated = str(first.get("generated_text") or "").strip()
                    if generated:
                        return generated

            if isinstance(data, dict):
                generated = str(data.get("generated_text") or data.get("text") or "").strip()
                if generated:
                    return generated
        except Exception:
            continue

    return ""


def _strip_code_fences(text: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json_blob(text: str) -> str:
    cleaned = _strip_code_fences(text)
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    match = re.search(r"\{[\s\S]*\}", cleaned)
    return match.group(0).strip() if match else cleaned


def _language_defaults(language: str) -> Dict[str, List[str] | str]:
    code = _normalize_language(language)
    if code == "ar":
        return {
            "title": "معلومات طبية عامة",
            "summary": "هذه معلومات طبية عامة وقد تختلف حسب الحالة الفردية.",
            "symptoms": ["حمى", "تعب", "ألم", "ضيق تنفس"],
            "causes": ["عدوى فيروسية", "عدوى بكتيرية", "التهاب"],
            "treatment": ["الراحة", "السوائل", "استشارة طبيب"],
            "warning": "اطلب رعاية طبية عاجلة إذا ساءت الأعراض أو ظهرت صعوبة شديدة في التنفس.",
            "disclaimer": "هذه المعلومات لأغراض تعليمية فقط ولا تغني عن استشارة طبيب مختص.",
        }
    if code == "fr":
        return {
            "title": "Informations médicales générales",
            "summary": "Ces informations sont générales et peuvent varier selon chaque patient.",
            "symptoms": ["Fièvre", "Fatigue", "Douleur", "Essoufflement"],
            "causes": ["Infection virale", "Infection bactérienne", "Inflammation"],
            "treatment": ["Repos", "Hydratation", "Avis médical"],
            "warning": "Consultez en urgence si les symptômes s'aggravent ou en cas de difficulté respiratoire.",
            "disclaimer": "Ces informations sont fournies à des fins éducatives et ne remplacent pas un avis médical professionnel.",
        }
    return {
        "title": "General Medical Information",
        "summary": "This is general medical information and may vary by individual condition.",
        "symptoms": ["Fever", "Fatigue", "Pain", "Shortness of breath"],
        "causes": ["Viral infection", "Bacterial infection", "Inflammation"],
        "treatment": ["Rest", "Hydration", "Medical consultation"],
        "warning": "Seek urgent care if symptoms worsen or if breathing becomes difficult.",
        "disclaimer": "This information is for educational purposes only and does not replace professional medical advice.",
    }


def _normalize_items(items: object, fallback: List[str]) -> List[str]:
    if isinstance(items, list):
        normalized = [str(item).strip() for item in items if str(item).strip()]
        if normalized:
            return normalized[:6]
    if isinstance(items, str) and items.strip():
        return [items.strip()]
    return list(fallback)


def _topic_from_query(query: str, language: str) -> str:
    text = str(query or "").strip()
    if not text:
        code = _normalize_language(language)
        if code == "ar":
            return "الحالة الطبية"
        if code == "fr":
            return "la condition médicale"
        return "the medical condition"

    cleaned = re.sub(r"[?؟!.,;:]+", "", text)
    tokens = [t for t in cleaned.split() if t]
    if not tokens:
        return cleaned or text

    stop_en = {"what", "are", "is", "the", "of", "for", "in", "and", "to", "with", "symptoms", "causes", "treatment"}
    stop_fr = {"quels", "quelles", "est", "les", "la", "le", "de", "du", "des", "et", "traitement", "causes", "symptomes", "symptômes"}
    stop_ar = {"ما", "هي", "هو", "عن", "من", "في", "و", "الى", "أعراض", "اعراض", "أسباب", "اسباب", "علاج"}
    stopwords = stop_en | stop_fr | stop_ar

    key_tokens = [t for t in tokens if t.lower() not in stopwords]
    if key_tokens:
        return " ".join(key_tokens[:4])
    return " ".join(tokens[:4])


def _deterministic_answer(query: str, language: str) -> Dict[str, object]:
    defaults = _language_defaults(language)
    q = str(query or "").lower()
    code = _normalize_language(language)

    trauma_keywords = ["broke", "broken", "fracture", "fractured", "leg injury", "arm injury", "sprain", "injury", "fall", "bone"]
    diabetes_keywords = ["diabetes", "diabetic", "blood sugar", "glucose", "hyperglycemia", "hypoglycemia"]
    asthma_keywords = ["asthma", "wheezing", "inhaler", "asthmatic"]

    if any(k in q for k in trauma_keywords):
        if code == "ar":
            return {
                "title": "إصابة أو كسر في العظام",
                "summary": "يبدو أن السؤال يتعلق بإصابة رضحية مثل كسر محتمل، ويحتاج تقييمًا طبيًا سريعًا.",
                "symptoms": [
                    "ألم شديد في الطرف المصاب",
                    "تورم أو كدمات",
                    "صعوبة أو عدم القدرة على تحريك الطرف أو تحميل الوزن",
                    "تشوه واضح في شكل الطرف أحيانًا",
                ],
                "causes": [
                    "سقوط أو صدمة مباشرة",
                    "التواء شديد أو إصابة رياضية",
                    "حوادث الطرق أو الإصابات عالية الطاقة",
                ],
                "treatment": [
                    "تثبيت الطرف المصاب وتجنب الحركة",
                    "وضع كمادات باردة ورفع الطرف إن أمكن",
                    "الذهاب للطوارئ لإجراء أشعة وتحديد الحاجة إلى جبيرة أو تدخل جراحي",
                ],
                "warning": "اطلب رعاية طبية عاجلة فورًا إذا كان هناك تشوه واضح، ألم شديد جدًا، خدر، نزيف، أو عدم القدرة على الوقوف.",
                "disclaimer": str(defaults["disclaimer"]),
            }
        if code == "fr":
            return {
                "title": "Blessure ou fracture osseuse",
                "summary": "Votre question suggère un traumatisme possiblement fracturaire nécessitant une évaluation médicale rapide.",
                "symptoms": [
                    "Douleur intense au membre atteint",
                    "Gonflement ou ecchymoses",
                    "Difficulté à bouger ou à prendre appui",
                    "Déformation visible possible",
                ],
                "causes": [
                    "Chute ou choc direct",
                    "Entorse sévère ou traumatisme sportif",
                    "Accident de la route ou traumatisme à haute énergie",
                ],
                "treatment": [
                    "Immobiliser le membre et éviter tout appui",
                    "Appliquer du froid et surélever si possible",
                    "Consulter rapidement aux urgences pour radiographie et prise en charge",
                ],
                "warning": "Consultez en urgence immédiatement en cas de déformation, douleur très intense, engourdissement, saignement ou impossibilité de marcher.",
                "disclaimer": str(defaults["disclaimer"]),
            }
        return {
            "title": "Possible Leg Fracture or Injury",
            "summary": "Your question suggests a traumatic injury (possible fracture) that needs prompt in-person medical evaluation.",
            "symptoms": [
                "Severe localized pain",
                "Swelling or bruising",
                "Difficulty moving the limb or bearing weight",
                "Possible visible deformity",
            ],
            "causes": [
                "Fall or direct impact",
                "Sports trauma or twisting injury",
                "Road traffic or other high-energy injury",
            ],
            "treatment": [
                "Immobilize the injured limb and avoid weight-bearing",
                "Apply cold packs and elevate if possible",
                "Go to urgent care/emergency for X-ray and definitive treatment",
            ],
            "warning": "Seek urgent care immediately if there is deformity, severe pain, numbness, bleeding, or inability to stand.",
            "disclaimer": str(defaults["disclaimer"]),
        }

    if any(k in q for k in diabetes_keywords):
        if code == "en":
            return {
                "title": "Diabetes",
                "summary": "Diabetes is a condition where blood glucose stays too high due to insulin problems.",
                "symptoms": ["Increased thirst", "Frequent urination", "Fatigue", "Blurred vision"],
                "causes": ["Insulin resistance", "Autoimmune beta-cell damage (Type 1)", "Genetic and lifestyle factors"],
                "treatment": ["Blood sugar monitoring", "Healthy diet and physical activity", "Medication or insulin as prescribed"],
                "warning": "Seek urgent care for confusion, vomiting, rapid breathing, or very high/low blood sugar symptoms.",
                "disclaimer": str(defaults["disclaimer"]),
            }

    if any(k in q for k in asthma_keywords):
        if code == "en":
            return {
                "title": "Asthma",
                "summary": "Asthma is a chronic airway condition causing inflammation and narrowing of breathing passages.",
                "symptoms": ["Wheezing", "Shortness of breath", "Chest tightness", "Cough, often worse at night"],
                "causes": ["Airway inflammation", "Allergen or irritant triggers", "Exercise or respiratory infections"],
                "treatment": ["Reliever inhaler for attacks", "Controller inhaler for prevention", "Trigger avoidance and action plan"],
                "warning": "Seek urgent care if breathing worsens, speaking is difficult, or reliever inhaler is not helping.",
                "disclaimer": str(defaults["disclaimer"]),
            }

    if "pneumonia" in q or "pneumonie" in q or "الالتهاب الرئوي" in q:
        if code == "ar":
            return {
                "title": "الالتهاب الرئوي",
                "summary": "الالتهاب الرئوي هو عدوى تصيب الرئتين وتسبب التهاب الحويصلات الهوائية.",
                "symptoms": [
                    "سعال مع بلغم",
                    "حمى وقشعريرة",
                    "ضيق في التنفس",
                    "ألم في الصدر عند التنفس أو السعال",
                ],
                "causes": [
                    "عدوى بكتيرية",
                    "عدوى فيروسية",
                    "عدوى فطرية",
                ],
                "treatment": [
                    "مضادات حيوية إذا كان السبب بكتيريًا",
                    "الراحة وشرب السوائل",
                    "خافضات حرارة ومتابعة طبية",
                ],
                "warning": "اطلب رعاية طبية عاجلة إذا أصبح التنفس صعبًا أو ساءت الأعراض.",
                "disclaimer": str(defaults["disclaimer"]),
            }
        if code == "fr":
            return {
                "title": "Pneumonie",
                "summary": "La pneumonie est une infection pulmonaire qui enflamme les alvéoles.",
                "symptoms": [
                    "Toux avec expectoration",
                    "Fièvre et frissons",
                    "Essoufflement",
                    "Douleur thoracique à la respiration ou à la toux",
                ],
                "causes": [
                    "Infection bactérienne",
                    "Infection virale",
                    "Infection fongique",
                ],
                "treatment": [
                    "Antibiotiques si cause bactérienne",
                    "Repos et hydratation",
                    "Antipyrétiques et suivi médical",
                ],
                "warning": "Consultez en urgence si la respiration devient difficile ou si les symptômes s'aggravent.",
                "disclaimer": str(defaults["disclaimer"]),
            }
        return {
            "title": "Pneumonia",
            "summary": "Pneumonia is a lung infection that inflames the air sacs.",
            "symptoms": [
                "Cough with phlegm",
                "Fever and chills",
                "Shortness of breath",
                "Chest pain when breathing or coughing",
            ],
            "causes": [
                "Bacterial infection",
                "Viral infection",
                "Fungal infection",
            ],
            "treatment": [
                "Antibiotics if bacterial",
                "Rest and hydration",
                "Fever reducers and clinical follow-up",
            ],
            "warning": "Seek urgent care if breathing becomes difficult or symptoms worsen.",
            "disclaimer": str(defaults["disclaimer"]),
        }

    topic = _topic_from_query(query, language)
    if code == "ar":
        return {
            "title": "غير قادر على المعالجة",
            "summary": "عذراً، لا يمكنني معالجة هذا الاستعلام. يرجى طرح سؤال طبي واضح ومحدد.",
            "symptoms": [],
            "causes": [],
            "treatment": [],
            "warning": "إذا كانت لديك حالة طبية طارئة، اتصل بالطوارئ على الفور.",
            "disclaimer": str(defaults["disclaimer"]),
        }
    if code == "fr":
        return {
            "title": "Impossible de traiter",
            "summary": "Désolé, je ne peux pas traiter cette requête. Veuillez poser une question médicale claire et spécifique.",
            "symptoms": [],
            "causes": [],
            "treatment": [],
            "warning": "Si vous avez une urgence médicale, appelez les urgences immédiatement.",
            "disclaimer": str(defaults["disclaimer"]),
        }

    return {
        "title": "Unable to Process",
        "summary": "Sorry, I cannot process this query. Please ask a clear and specific medical question.",
        "symptoms": [],
        "causes": [],
        "treatment": [],
        "warning": "If you have a medical emergency, call emergency services immediately.",
        "disclaimer": str(defaults["disclaimer"]),
    }


def fallback_parse(raw: str, language: str) -> Dict[str, object]:
    defaults = _language_defaults(language)
    text = _strip_code_fences(raw)

    # Best-effort extraction when JSON parsing fails.
    lines = [line.strip("-• \t") for line in text.splitlines() if line.strip()]
    summary = " ".join(lines[:2]).strip() or str(defaults["summary"])

    return {
        "title": str(defaults["title"]),
        "summary": summary,
        "symptoms": list(defaults["symptoms"]),
        "causes": list(defaults["causes"]),
        "treatment": list(defaults["treatment"]),
        "warning": str(defaults["warning"]),
        "disclaimer": str(defaults["disclaimer"]),
    }


def llm_generate_structured(query: str, language: str) -> Dict[str, object]:
    prompt = build_direct_prompt(query, language)
    raw = ""

    # 1) Prefer Hugging Face hosted inference when token is available.
    raw = _call_huggingface_inference(prompt)

    # 2) Fall back to configured runtime/API LLM path.
    if not raw and _should_use_runtime_llm():
        raw = _call_llm(prompt)

    # 3) Final deterministic fallback to guarantee response continuity.
    if not raw:
        return _deterministic_answer(query, language)

    defaults = _language_defaults(language)

    try:
        blob = _extract_json_blob(raw)
        parsed = json.loads(blob)
    except Exception:
        return fallback_parse(raw, language)

    title = str(parsed.get("title", "")).strip() or str(defaults["title"])
    summary = str(parsed.get("summary", "")).strip() or str(defaults["summary"])
    warning = str(parsed.get("warning", "")).strip() or str(defaults["warning"])
    disclaimer = str(parsed.get("disclaimer", "")).strip() or str(defaults["disclaimer"])

    symptoms = _normalize_items(parsed.get("symptoms"), list(defaults["symptoms"]))
    causes = _normalize_items(parsed.get("causes"), list(defaults["causes"]))
    treatment = _normalize_items(parsed.get("treatment"), list(defaults["treatment"]))

    return {
        "title": title,
        "summary": summary,
        "symptoms": symptoms,
        "causes": causes,
        "treatment": treatment,
        "warning": warning,
        "disclaimer": disclaimer,
    }


def generate_direct_answer(query: str, language: str) -> Dict[str, object]:
    return llm_generate_structured(query, language)
