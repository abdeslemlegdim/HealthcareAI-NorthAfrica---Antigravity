from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(main.app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "healthy"
    assert "services" in payload
    assert payload["services"]["api"] == "active"
    assert payload["services"]["rag_system"] in {"active", "disabled"}
    assert "ai" in payload
    assert "rag_status" in payload["ai"]


def test_rag_query_endpoint_returns_sources(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Pneumonia symptoms include cough and fever."
        sources = [
            {
                "title": "Pneumonia",
                "category": "Respiratory Infection",
                "content": {"focus": "Symptoms", "data": ["Cough", "Fever"]},
                "relevance_score": 0.92,
                "score": 0.92,
            }
        ]
        confidence = 0.92
        language = "en"
        metrics = {"retrieval_ms": 1.0, "rerank_ms": 1.0, "generation_ms": 1.0, "total_ms": 3.0}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What are symptoms of pneumonia?", "debug": True, "enrich_external_sources": False},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["answer"]
    assert isinstance(payload["sources"], list)
    assert payload["sources"][0]["title"] == "Pneumonia"
    assert payload["sources"][0]["content"]
    assert "url" in payload["sources"][0]
    assert payload["sources"][0]["source"] == "Pneumonia"
    assert payload["sources"][0]["score"] >= 0.9
    assert payload["confidence"] >= 0.9
    assert payload["language"] == "en"
    assert payload["title"] == "Pneumonia"
    assert payload["summary"]
    assert payload["disclaimer"]
    assert payload["warning"] == ""
    assert payload["labels"]["clinical_response"] == "Clinical Response"
    assert payload["metrics"]["total_ms"] == 3.0


def test_rag_query_merges_pubmed_sources(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Pneumonia symptoms include cough and fever."
        sources = [
            {
                "title": "Pneumonia",
                "content": {"focus": "Symptoms", "data": ["Cough", "Fever"]},
                "relevance_score": 0.92,
                "score": 0.92,
            }
        ]
        confidence = 0.92
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())
    monkeypatch.setattr(
        rag_api,
        "_fetch_pubmed_sources",
        lambda _query, _limit: [
            {
                "title": "Pneumonia in adults: clinical update",
                "content": "Lancet Respir Med; 2024; Smith",
                "score": 0.78,
                "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                "source_type": "pubmed",
            }
        ],
    )

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What are symptoms of pneumonia?", "enrich_external_sources": True, "external_source_limit": 1},
    )
    assert response.status_code == 200

    payload = response.json()
    assert len(payload["sources"]) >= 2
    assert any(src.get("source_type") == "pubmed" for src in payload["sources"])
    assert any("pubmed.ncbi.nlm.nih.gov" in src.get("url", "") for src in payload["sources"])


def test_rag_query_failure_when_question_missing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.rag_system import api as rag_api

    monkeypatch.setattr(rag_api, "rag_system", object())

    response = client.post("/api/v1/rag/query", json={"query": "", "enrich_external_sources": False})
    assert response.status_code == 500
    assert "question" in response.json()["detail"]


def test_rag_query_failure_when_backend_raises(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.rag_system import api as rag_api

    class _BrokenRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            raise RuntimeError("simulated failure")

    monkeypatch.setattr(rag_api, "rag_system", _BrokenRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What are symptoms of pneumonia?", "enrich_external_sources": False},
    )
    assert response.status_code == 500
    assert "simulated failure" in response.json()["detail"]


# ===== LAYER 1: INPUT VALIDATION & MEDICAL INTENT =====
def test_layer1_rejects_non_medical_query(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """LAYER 1: Should reject non-medical queries"""
    from src.rag_system import api as rag_api

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            raise RuntimeError("Should not be called for non-medical query")

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    # Non-medical query like a joke
    response = client.post(
        "/api/v1/rag/query",
        json={"question": "Tell me a funny joke", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == 0.0
    assert payload["sources"] == []
    assert payload["warning"]
    assert "warning" in payload["answer"].lower()  # Should warn user


def test_layer1_rejects_garbage_input(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """LAYER 1: Should reject single-word queries (too short)"""
    from src.rag_system import api as rag_api

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            raise RuntimeError("Should not be called for garbage input")

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "fever", "enrich_external_sources": False},  # Single word
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == 0.0
    assert payload["warning"]
    assert "warning" in payload["answer"].lower()


def test_layer1_accepts_valid_medical_query(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """LAYER 1: Should accept clear medical queries"""
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Pneumonia causes inflammation of air sacs."
        sources = [{"title": "Pneumonia Causes", "content": "...", "score": 0.85}]
        confidence = 0.85
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What are symptoms of pneumonia?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    # Should proceed with query (pass Layer 1)
    payload = response.json()
    assert payload["answer"] != ""


# ===== LAYER 2: SKIPPED IN API =====
def test_layer2_is_skipped_in_api(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Layer 2 is intentionally skipped, so weak sources are still returned by API."""
    from src.rag_system import api as rag_api

    class _FakeResult:
        # Sources with mixed relevance scores (some too low)
        answer = "Some answer"
        sources = [
            {"title": "Good Source", "content": "...", "score": 0.8},  # Above threshold (0.65)
            {"title": "Weak Source", "content": "...", "score": 0.3},  # Below threshold
        ]
        confidence = 0.7
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What causes diabetes?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    
    # Final formatter keeps the relevant pair while dropping weaker noise.
    assert len(payload["sources"]) == 2
    assert payload["sources"][0]["title"] == "Good Source"
    assert payload["sources"][1]["title"] == "Weak Source"


def test_layer2_skipped_allows_weak_sources(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Layer 2 skipped: API should not auto-reject when weak sources are returned by RAG."""
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Some answer"
        sources = [
            {"title": "Very Weak 1", "content": "...", "score": 0.2},
            {"title": "Very Weak 2", "content": "...", "score": 0.1},
        ]
        confidence = 0.7
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What is X disease?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    
    assert len(payload["sources"]) == 0
    assert payload["answer"] == "Some answer"


# ===== LAYER 4: SKIPPED IN API =====
def test_layer4_is_skipped_in_api(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Layer 4 skipped: low-confidence answers should still be returned."""
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Maybe the answer is X?"
        sources = [{"title": "Questionable Source", "content": "...", "score": 0.8}]
        confidence = 0.4  # Below threshold of 0.55
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What causes rare disease X?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    
    assert "Maybe the answer is X?" in payload["answer"]
    assert payload["confidence"] == 0.4


def test_layer4_accepts_high_confidence_answer(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """LAYER 4: Should accept answers with confidence >= 0.55"""
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Diabetes is an endocrine disorder..."
        sources = [{"title": "Good Source", "content": "...", "score": 0.9}]
        confidence = 0.8  # Above threshold of 0.55
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What is diabetes?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    
    # Should return the answer
    assert "Diabetes is an endocrine disorder" in payload["answer"]
    assert payload["confidence"] == 0.8


def test_fallback_mode_passthrough(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """API should expose fallback mode when RAG returns fallback output."""
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Fallback answer from LLM without retrieved docs."
        sources = []
        confidence = 0.7
        language = "en"
        mode = "fallback"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What are symptoms of pneumonia?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "fallback"
    assert payload["sources"] == []
    assert payload["confidence"] == 0.7


def test_layer5_spell_correction_applies_before_rag_query(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """LAYER 5: corrected question should be sent to rag_system.query."""
    from src.rag_system import api as rag_api

    seen = {"question": None}

    class _FakeResult:
        answer = "Pneumonia symptoms include fever and cough."
        sources = [{"title": "Pneumonia", "content": "...", "score": 0.9}]
        confidence = 0.9
        language = "en"
        metrics = {}

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            seen["question"] = question
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())
    monkeypatch.setattr(rag_api, "correct_query", lambda q: q.replace("simptoms", "symptoms"))

    response = client.post(
        "/api/v1/rag/query",
        json={"question": "What are simptoms of pneumonia?", "enrich_external_sources": False},
    )
    assert response.status_code == 200
    assert seen["question"] == "What are symptoms of pneumonia?"


# ===== GUARDS UNIT TESTS =====
def test_guards_medical_query_detection() -> None:
    """Test is_medical_query() function"""
    from src.rag_system.guards import is_medical_query

    # Should accept medical queries
    assert is_medical_query("What are symptoms of pneumonia?") is True
    assert is_medical_query("How to treat diabetes?") is True
    assert is_medical_query("What causes heart disease?") is True

    # Should reject non-medical queries
    assert is_medical_query("Tell me a joke") is False
    assert is_medical_query("What is the weather?") is False
    assert is_medical_query("hello") is False  # Too short
    
    # Should reject single word (too short)
    assert is_medical_query("fever") is False


def test_guards_input_validation() -> None:
    """Test validate_input() comprehensive check"""
    from src.rag_system.guards import validate_input

    # Valid medical query
    is_valid, error = validate_input("What are the causes of asthma?")
    assert is_valid is True
    assert error is None

    # Too short
    is_valid, error = validate_input("pain")
    assert is_valid is False
    assert error is not None

    # Non-medical
    is_valid, error = validate_input("What time is it?")
    assert is_valid is False
    assert error is not None
    
    # Empty
    is_valid, error = validate_input("")
    assert is_valid is False
    assert "empty" in error.lower()


def test_guards_spam_detection() -> None:
    """Test detect_spam_patterns() function"""
    from src.rag_system.guards import detect_spam_patterns

    # Normal query - not spam
    is_spam, reason = detect_spam_patterns("What are symptoms of asthma?")
    assert is_spam is False

    # Excessive repetition - spam
    is_spam, reason = detect_spam_patterns("aaaaaaa bbbbbbbbb what is this")
    assert is_spam is True
    assert "repetition" in reason.lower()


def test_guards_multilingual_medical_detection() -> None:
    from src.rag_system.guards import is_medical_query, guess_query_language, detect_spam_patterns

    assert guess_query_language("Quels sont les symptômes de la pneumonie ?") == "fr"
    assert guess_query_language("ما هي أعراض الالتهاب الرئوي؟") == "ar"
    assert is_medical_query("Quels sont les symptômes de la pneumonie ?") is True
    assert is_medical_query("ما هي أعراض الالتهاب الرئوي؟") is True

    is_spam_fr, _ = detect_spam_patterns("Quels sont les symptômes de la pneumonie ?")
    is_spam_ar, _ = detect_spam_patterns("ما هي أعراض الالتهاب الرئوي؟")
    assert is_spam_fr is False
    assert is_spam_ar is False


def test_rag_uses_detected_language_for_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.rag_system.rag import MedicalRAG

    rag = MedicalRAG()
    captured: dict[str, str] = {}

    monkeypatch.setattr(rag, "_detect_language", lambda _text: "fr")
    monkeypatch.setattr(
        rag,
        "_translate_text",
        lambda _text, source_lang, target_lang: "What are the symptoms of pneumonia?",
    )
    monkeypatch.setattr(
        rag,
        "_retrieve_relevant_info",
        lambda *args, **kwargs: [
            {
                "title": "Pneumonia",
                "category": "Respiratory Infection",
                "content": {"focus": "Symptoms", "data": ["Cough", "Fever"]},
                "relevance_score": 0.9,
                "score": 0.9,
            }
        ],
    )

    def _fake_generate_answer(question: str, sources, language: str) -> str:
        captured["language"] = language
        return "**Pneumonia**\n\n**Symptomes:**\n- Toux\n\n**Causes:**\n- Infection\n\n**Traitement:**\n- Repos"

    monkeypatch.setattr(rag, "_generate_answer", _fake_generate_answer)

    result = rag.query("Quels sont les symptomes de la pneumonie ?")

    assert captured["language"] == "fr"
    assert result.language == "fr"
    assert result.mode == "rag"


def test_rag_query_normalization_map() -> None:
    """Retrieval query normalization should fix known typo phrases."""
    from src.rag_system.rag import MedicalRAG

    rag = MedicalRAG()
    assert rag._normalize_query("hand break") == "hand injury"
    assert rag._normalize_query("head ake") == "headache"
    assert rag._normalize_query("stomack") == "stomach"
    assert rag._normalize_query("what is pneumonia") == "what is pneumonia"


def test_rag_domain_filter_removes_unrelated_covid_docs() -> None:
    """COVID-heavy documents should be dropped unless user explicitly asks about COVID."""
    from src.rag_system.rag import MedicalRAG

    rag = MedicalRAG()
    docs = [
        {"title": "COVID-19", "category": "Viral", "content": {"focus": "Overview", "data": ["SARS-CoV-2"]}},
        {"title": "Hand Injury", "category": "Trauma", "content": {"focus": "Treatment", "data": ["Immobilization"]}},
    ]

    filtered = rag._domain_filter("hand injury pain", docs)
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Hand Injury"

    covid_query_filtered = rag._domain_filter("covid symptoms", docs)
    assert len(covid_query_filtered) == 2