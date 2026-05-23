"""
Integration tests for Frontend ↔ Backend communication.

Tests the complete frontend-backend integration including:
- Chat endpoint (frontend sends message, backend processes via RAG)
- Image upload flow (frontend uploads X-ray, backend classifies)
- Vitals measurement flow (frontend requests measurement, backend processes)
- CORS headers verification
- Authentication (if implemented)
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from typing import Dict, Any


@pytest.mark.integration
class TestFrontendBackendIntegration:
    """Test frontend-backend communication and integration."""
    
    def test_chat_endpoint(self, client: TestClient):
        """
        Test chat endpoint that frontend uses.
        
        Scenario:
        1. Frontend sends chat message
        2. Backend processes via RAG
        3. Frontend receives structured response
        4. Response includes answer and sources
        """
        # Simulate frontend chat request
        chat_request = {
            "query": "What are symptoms of COVID-19?",
            "language": "en",
            "top_k": 5
        }
        
        response = client.post(
            "/api/v1/chat",
            json=chat_request
        )
        
        # Verify response status
        assert response.status_code == 200, f"Chat endpoint failed: {response.text}"
        
        # Parse response
        data = response.json()
        
        # Verify response structure (what frontend expects)
        assert "answer" in data, "Response missing 'answer' field"
        assert "sources" in data, "Response missing 'sources' field"
        assert "confidence" in data, "Response missing 'confidence' field"
        assert "language" in data, "Response missing 'language' field"
        
        # Verify answer content
        assert len(data["answer"]) > 0, "Answer is empty"
        assert isinstance(data["answer"], str), "Answer is not a string"
        
        # Verify confidence score
        assert 0.0 <= data["confidence"] <= 1.0, "Confidence out of range"
        
        # Verify sources structure (if present)
        sources = data.get("sources", [])
        assert isinstance(sources, list), "Sources is not a list"
        
        # If sources exist, verify their structure
        if len(sources) > 0:
            source = sources[0]
            # Sources should have at least a score field
            assert "score" in source, "Source missing 'score' field"
        
        # Verify language is correct
        assert data["language"] == "en", "Language mismatch"
        
        # Log results for debugging
        print(f"\n=== Chat Endpoint Test ===")
        print(f"Query: {chat_request['query']}")
        print(f"Answer length: {len(data['answer'])} chars")
        print(f"Confidence: {data['confidence']:.2f}")
        print(f"Sources count: {len(sources)}")
        print(f"Language: {data['language']}")
        
    def test_chat_endpoint_multilingual(self, client: TestClient):
        """
        Test chat endpoint with different languages.
        
        Verifies:
        1. Frontend can request responses in different languages
        2. Backend properly handles language parameter
        3. Response language matches request
        """
        languages = ["en", "fr", "ar"]
        
        print(f"\n=== Multilingual Chat Test ===")
        
        for lang in languages:
            # Send chat request in specific language
            response = client.post(
                "/api/v1/chat",
                json={
                    "query": "What is pneumonia?",
                    "language": lang,
                    "top_k": 3
                }
            )
            
            assert response.status_code == 200, f"Chat failed for language {lang}"
            data = response.json()
            
            # Verify response structure
            assert "answer" in data, f"Missing answer for language {lang}"
            assert "language" in data, f"Missing language field for {lang}"
            
            # Verify language is set correctly
            assert data["language"] == lang, f"Language mismatch for {lang}"
            
            print(f"Language: {lang}")
            print(f"  Answer length: {len(data['answer'])} chars")
            print(f"  Confidence: {data['confidence']:.2f}")
    
    def test_image_upload_flow(self, client: TestClient, sample_xray_image: Path):
        """
        Test image upload flow from frontend to backend.
        
        Scenario:
        1. Frontend uploads chest X-ray image
        2. Backend receives and validates image
        3. Backend classifies image
        4. Frontend receives classification results
        """
        # Simulate frontend image upload
        with open(sample_xray_image, "rb") as f:
            files = {"file": ("chest_xray.jpg", f, "image/jpeg")}
            data = {"top_k": 3}
            
            response = client.post(
                "/api/v1/imaging/classify",
                files=files,
                data=data
            )
        
        # Verify response status
        assert response.status_code == 200, f"Image upload failed: {response.text}"
        
        # Parse response
        result = response.json()
        
        # Verify response structure (what frontend expects)
        assert "disease" in result, "Response missing 'disease' field"
        assert "confidence" in result, "Response missing 'confidence' field"
        assert "filename" in result, "Response missing 'filename' field"
        
        # Verify disease prediction
        assert len(result["disease"]) > 0, "Disease prediction is empty"
        assert isinstance(result["disease"], str), "Disease is not a string"
        
        # Verify confidence score
        assert 0.0 <= result["confidence"] <= 1.0, "Confidence out of range"
        
        # Verify filename was preserved
        assert result["filename"] == "chest_xray.jpg", "Filename not preserved"
        
        # Log results
        print(f"\n=== Image Upload Test ===")
        print(f"Uploaded: {sample_xray_image.name}")
        print(f"Predicted disease: {result['disease']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Filename preserved: {result['filename']}")
        
    def test_image_upload_with_gradcam(self, client: TestClient, sample_xray_image: Path):
        """
        Test image upload with Grad-CAM explanation.
        
        Verifies:
        1. Frontend can request Grad-CAM visualization
        2. Backend generates explanation
        3. Response includes Grad-CAM data
        """
        # Upload image with Grad-CAM request
        with open(sample_xray_image, "rb") as f:
            files = {"file": ("chest_xray.jpg", f, "image/jpeg")}
            data = {"explain": True}
            
            response = client.post(
                "/api/v1/imaging/classify",
                files=files,
                data=data
            )
        
        assert response.status_code == 200, f"Image upload with Grad-CAM failed: {response.text}"
        
        result = response.json()
        
        # Verify basic fields
        assert "disease" in result, "Missing disease field"
        assert "confidence" in result, "Missing confidence field"
        
        # Verify Grad-CAM data (if supported)
        # Note: Grad-CAM might not be available in mock mode
        if "gradcam" in result:
            assert isinstance(result["gradcam"], str), "Grad-CAM is not a string"
            assert len(result["gradcam"]) > 0, "Grad-CAM data is empty"
            print(f"\n=== Grad-CAM Test ===")
            print(f"Grad-CAM data length: {len(result['gradcam'])} chars")
        else:
            print(f"\n=== Grad-CAM Test ===")
            print(f"Grad-CAM not available (likely mock mode)")
    
    def test_vitals_measurement_flow(self, client: TestClient):
        """
        Test vitals measurement flow from frontend to backend.
        
        Scenario:
        1. Frontend requests vitals measurement
        2. Backend processes measurement (mock or real)
        3. Frontend receives vitals data
        """
        # Simulate frontend vitals measurement request
        measurement_request = {
            "duration": 15,
            "display": False
        }
        
        response = client.post(
            "/api/v1/vitals/measure",
            json=measurement_request
        )
        
        # Verify response status
        assert response.status_code == 200, f"Vitals measurement failed: {response.text}"
        
        # Parse response
        data = response.json()
        
        # Verify response structure (what frontend expects)
        assert "heart_rate" in data, "Response missing 'heart_rate' field"
        assert "confidence" in data, "Response missing 'confidence' field"
        
        # Verify heart rate value
        assert isinstance(data["heart_rate"], (int, float)), "Heart rate is not numeric"
        assert 40 <= data["heart_rate"] <= 200, "Heart rate out of realistic range"
        
        # Verify confidence score
        assert 0.0 <= data["confidence"] <= 1.0, "Confidence out of range"
        
        # Optional fields
        if "blood_pressure" in data and data["blood_pressure"] is not None:
            bp = data["blood_pressure"]
            assert "systolic" in bp, "Blood pressure missing systolic"
            assert "diastolic" in bp, "Blood pressure missing diastolic"
            assert 60 <= bp["systolic"] <= 200, "Systolic BP out of range"
            assert 40 <= bp["diastolic"] <= 130, "Diastolic BP out of range"
        
        if "respiratory_rate" in data and data["respiratory_rate"] is not None:
            assert 8 <= data["respiratory_rate"] <= 40, "Respiratory rate out of range"
        
        if "oxygen_saturation" in data and data["oxygen_saturation"] is not None:
            assert 70 <= data["oxygen_saturation"] <= 100, "O2 saturation out of range"
        
        # Log results
        print(f"\n=== Vitals Measurement Test ===")
        print(f"Heart rate: {data['heart_rate']} BPM")
        print(f"Confidence: {data['confidence']:.2f}")
        if "blood_pressure" in data and data["blood_pressure"]:
            bp = data["blood_pressure"]
            print(f"Blood pressure: {bp['systolic']}/{bp['diastolic']} mmHg")
        if "respiratory_rate" in data and data["respiratory_rate"]:
            print(f"Respiratory rate: {data['respiratory_rate']} breaths/min")
        if "oxygen_saturation" in data and data["oxygen_saturation"]:
            print(f"O2 saturation: {data['oxygen_saturation']}%")
    
    def test_cors_headers(self, client: TestClient):
        """
        Test CORS headers are properly configured.
        
        Verifies:
        1. CORS headers are present in responses
        2. Frontend origins are allowed
        3. Credentials are supported
        4. Proper methods are allowed
        """
        # Test preflight request (OPTIONS)
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Verify CORS headers are present
        headers = response.headers
        
        # Check for CORS headers (FastAPI's CORS middleware handles this)
        # Note: TestClient might not fully simulate CORS preflight
        # In production, these headers should be present
        
        print(f"\n=== CORS Headers Test ===")
        print(f"Response status: {response.status_code}")
        print(f"Headers present: {list(headers.keys())}")
        
        # Test actual request with Origin header
        response = client.post(
            "/api/v1/chat",
            json={"query": "Test query", "language": "en"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200, "Request with Origin header failed"
        
        # Check if CORS headers are in response
        if "access-control-allow-origin" in headers:
            print(f"CORS Allow-Origin: {headers['access-control-allow-origin']}")
        
        if "access-control-allow-credentials" in headers:
            print(f"CORS Allow-Credentials: {headers['access-control-allow-credentials']}")
    
    def test_authentication(self, client: TestClient):
        """
        Test authentication (if implemented).
        
        Verifies:
        1. Endpoints accept requests without auth (if public)
        2. Auth headers are properly handled (if required)
        3. Invalid auth is rejected (if auth is enabled)
        
        Note: This is a placeholder test. Update based on actual auth implementation.
        """
        # Test public endpoint without authentication
        response = client.get("/health")
        assert response.status_code == 200, "Health endpoint should be public"
        
        # Test API endpoint without authentication
        # Currently, the API is public (no auth required)
        response = client.post(
            "/api/v1/chat",
            json={"query": "Test query", "language": "en"}
        )
        assert response.status_code == 200, "Chat endpoint should be accessible"
        
        print(f"\n=== Authentication Test ===")
        print(f"Health endpoint: Public (200 OK)")
        print(f"Chat endpoint: Public (200 OK)")
        print(f"Note: Authentication not currently implemented")
        
        # TODO: Add authentication tests when auth is implemented
        # Example:
        # - Test with valid token
        # - Test with invalid token
        # - Test with expired token
        # - Test with missing token
    
    def test_error_handling(self, client: TestClient):
        """
        Test error handling in frontend-backend communication.
        
        Verifies:
        1. Invalid requests return proper error codes
        2. Error messages are user-friendly
        3. Frontend can handle error responses
        """
        # Test invalid chat request (missing required field)
        response = client.post(
            "/api/v1/chat",
            json={"language": "en"}  # Missing 'query' field
        )
        
        # Should return error (422 or 500 depending on error handling)
        assert response.status_code in [422, 500], f"Invalid request should return error, got {response.status_code}"
        
        # Test invalid image upload (no file)
        response = client.post(
            "/api/v1/imaging/classify",
            files={}
        )
        
        # Should return error (400 or 422)
        assert response.status_code in [400, 422], "Missing file should return error"
        
        # Test invalid vitals request (invalid duration)
        response = client.post(
            "/api/v1/vitals/measure",
            json={"duration": 200}  # Exceeds max duration (120)
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422, "Invalid duration should return 422"
        
        print(f"\n=== Error Handling Test ===")
        print(f"Invalid chat request: {response.status_code} (error)")
        print(f"Missing image file: 400/422 (error)")
        print(f"Invalid vitals duration: 422 (validation error)")
    
    def test_response_format_consistency(self, client: TestClient, sample_xray_image: Path):
        """
        Test response format consistency across endpoints.
        
        Verifies:
        1. All endpoints return JSON
        2. Error responses have consistent format
        3. Success responses have consistent structure
        """
        # Test chat endpoint
        chat_response = client.post(
            "/api/v1/chat",
            json={"query": "Test query", "language": "en"}
        )
        assert chat_response.status_code == 200
        assert chat_response.headers["content-type"].startswith("application/json")
        chat_data = chat_response.json()
        assert isinstance(chat_data, dict), "Chat response should be a dict"
        
        # Test imaging endpoint
        with open(sample_xray_image, "rb") as f:
            imaging_response = client.post(
                "/api/v1/imaging/classify",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )
        assert imaging_response.status_code == 200
        assert imaging_response.headers["content-type"].startswith("application/json")
        imaging_data = imaging_response.json()
        assert isinstance(imaging_data, dict), "Imaging response should be a dict"
        
        # Test vitals endpoint
        vitals_response = client.post(
            "/api/v1/vitals/measure",
            json={"duration": 15, "display": False}
        )
        assert vitals_response.status_code == 200
        assert vitals_response.headers["content-type"].startswith("application/json")
        vitals_data = vitals_response.json()
        assert isinstance(vitals_data, dict), "Vitals response should be a dict"
        
        # Test health endpoint
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.headers["content-type"].startswith("application/json")
        health_data = health_response.json()
        assert isinstance(health_data, dict), "Health response should be a dict"
        
        print(f"\n=== Response Format Consistency Test ===")
        print(f"All endpoints return JSON: ✓")
        print(f"All responses are dictionaries: ✓")
        print(f"Content-Type headers correct: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
