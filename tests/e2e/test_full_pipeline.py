"""Full pipeline API tests.

Covers key product endpoints:
- /health
- /api/v1/rag/query
- /api/v1/image/analyze
- /api/v1/vitals/measure

Each test asserts HTTP 200 and a valid JSON response shape.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import main

def _assert_200_and_json(response) -> dict[str, Any]:
    """Common assertion helper for status and JSON validity."""
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    return payload


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Shared test client for full pipeline checks."""
    return TestClient(main.app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    payload = _assert_200_and_json(response)

    assert "status" in payload


def test_rag_query_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep this test lightweight by stubbing RAG backend behavior.
    from src.rag_system import api as rag_api

    class _FakeResult:
        answer = "Pneumonia symptoms include cough and fever."
        sources = [
            {
                "title": "Pneumonia",
                "content": {"focus": "Symptoms", "data": ["Cough", "Fever"]},
                "relevance_score": 0.88,
                "score": 0.88,
            }
        ]
        confidence = 0.88
        language = "en"
        metrics = {
            "retrieval_ms": 1.0,
            "rerank_ms": 1.0,
            "generation_ms": 1.0,
            "total_ms": 3.0,
        }

    class _FakeRAG:
        def query(self, question: str, language=None, top_k: int = 5, use_reranking: bool = False):
            return _FakeResult()

    monkeypatch.setattr(rag_api, "rag_system", _FakeRAG())

    response = client.post(
        "/api/v1/rag/query",
        json={"query": "What are pneumonia symptoms?", "top_k": 3},
    )
    payload = _assert_200_and_json(response)

    assert isinstance(payload.get("answer"), str)
    assert isinstance(payload.get("sources"), list)
    assert isinstance(payload.get("confidence"), (float, int))
    assert isinstance(payload.get("language"), str)


def test_image_analyze_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Force lightweight mock classifier path to avoid model loading in tests.
    from src.medical_imaging import simple_analyze_api

    monkeypatch.setattr(simple_analyze_api, "_get_classifier", lambda: None)

    sample_path = Path(__file__).resolve().parents[1] / "sample_xray.png"
    if sample_path.exists():
        image_bytes = sample_path.read_bytes()
    else:
        # Fallback: generate a small valid PNG on the fly.
        from PIL import Image

        img = Image.new("RGB", (32, 32), (120, 120, 120))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

    response = client.post(
        "/api/v1/image/analyze",
        files={"file": ("tiny.png", image_bytes, "image/png")},
    )
    payload = _assert_200_and_json(response)

    assert isinstance(payload.get("disease"), str)
    assert isinstance(payload.get("confidence"), (float, int))


def test_vitals_measure_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock camera-dependent measurement for deterministic test behavior.
    from src.vital_signs import api as vitals_api

    class _FakeVitals:
        heart_rate = 72
        confidence = 0.95

    class _FakeMonitor:
        def measure_vitals(self, duration: int = 30, display: bool = False):
            return _FakeVitals()

    monkeypatch.setattr(vitals_api, "get_monitor", lambda: _FakeMonitor())

    response = client.get("/api/v1/vitals/measure")
    payload = _assert_200_and_json(response)

    assert isinstance(payload.get("heart_rate"), int)
