"""Smoke tests for core API endpoints.

These tests are intentionally lightweight and validate endpoint stability
and response schema shape for demo readiness.
"""

import os
import pytest
import requests


BASE_URL = os.getenv("MAGHREBCARE_API_URL", "http://localhost:8001")
TIMEOUT = 15


def _is_api_up() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.ok
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def require_api():
    if not _is_api_up():
        pytest.skip(f"API is not reachable at {BASE_URL}")


def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200
    payload = response.json()

    assert "status" in payload
    assert "services" in payload
    assert "ai" in payload
    assert "rag_status" in payload["ai"]
    assert "embedding_model_loaded" in payload["ai"]
    assert "reranker_loaded" in payload["ai"]
    assert "llm_loaded" in payload["ai"]
    assert "imaging_model_loaded" in payload["ai"]


def test_metrics_endpoint():
    response = requests.get(f"{BASE_URL}/metrics", timeout=TIMEOUT)
    assert response.status_code == 200
    text = response.text
    assert "healthcare_api_requests_total" in text or "Prometheus client is not installed" in text


def test_rag_query():
    response = requests.post(
        f"{BASE_URL}/api/v1/rag/query",
        json={"question": "What are symptoms of pneumonia?", "debug": True},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200
    payload = response.json()

    assert isinstance(payload.get("answer"), str)
    assert isinstance(payload.get("sources"), list)
    assert isinstance(payload.get("confidence"), (float, int))
    assert isinstance(payload.get("language"), str)

    for source in payload.get("sources", []):
        assert isinstance(source.get("text"), str)
        assert isinstance(source.get("score"), (float, int))
        assert isinstance(source.get("source"), str)


def test_imaging_classification():
    image_path = os.path.join(os.getcwd(), "test_xray.png")
    if not os.path.exists(image_path):
        pytest.skip("test_xray.png not available in repository root")

    with open(image_path, "rb") as image_file:
        response = requests.post(
            f"{BASE_URL}/api/v1/imaging/classify",
            files={"file": ("test_xray.png", image_file, "image/png")},
            timeout=TIMEOUT,
        )

    assert response.status_code == 200
    payload = response.json()

    assert "predictions" in payload
    assert isinstance(payload.get("predictions"), list)


def test_vitals_health_and_measure():
    health_response = requests.get(f"{BASE_URL}/api/v1/vitals/health", timeout=TIMEOUT)
    assert health_response.status_code == 200
    health_payload = health_response.json()
    assert health_payload.get("status") in {"healthy", "degraded", "not_initialized"}

    measure_response = requests.post(
        f"{BASE_URL}/api/v1/vitals/measure",
        json={"duration": 10, "display": False},
        timeout=TIMEOUT,
    )
    assert measure_response.status_code == 200
    measure_payload = measure_response.json()

    assert isinstance(measure_payload.get("heart_rate"), (float, int))
    assert isinstance(measure_payload.get("confidence"), (float, int))
    assert isinstance(measure_payload.get("mode"), str)
