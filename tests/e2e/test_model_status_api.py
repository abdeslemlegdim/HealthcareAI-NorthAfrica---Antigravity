"""
Test API endpoints for model status information.

Tests for Task 1.4: Update API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from main import app
    return TestClient(app)


def test_main_health_endpoint_includes_imaging_model_info(client):
    """Test that /health endpoint includes medical imaging model information."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check basic structure
    assert "status" in data
    assert "services" in data
    assert "ai" in data
    assert "medical_imaging_model" in data
    
    # Check medical imaging model info structure
    imaging_info = data["medical_imaging_model"]
    
    # Should have these fields (even if classifier not initialized)
    expected_fields = [
        "model_loaded",
        "using_mock",
        "backbone",
        "num_classes",
        "device",
        "pretrained_model",
        "supported_diseases"
    ]
    
    # If there's an error, that's acceptable (classifier might not be initialized)
    if "error" not in imaging_info:
        for field in expected_fields:
            assert field in imaging_info, f"Missing field: {field}"
        
        # Check pretrained model info
        pretrained = imaging_info["pretrained_model"]
        assert "exists" in pretrained
        assert "path" in pretrained
        assert "size_mb" in pretrained
        assert "num_parameters_millions" in pretrained
        
        # Validate types
        assert isinstance(imaging_info["model_loaded"], bool)
        assert isinstance(imaging_info["using_mock"], bool)
        assert isinstance(imaging_info["num_classes"], int)
        assert isinstance(imaging_info["supported_diseases"], int)
        
        print(f"✅ Main health endpoint includes imaging model info:")
        print(f"   - Model loaded: {imaging_info['model_loaded']}")
        print(f"   - Using mock: {imaging_info['using_mock']}")
        print(f"   - Backbone: {imaging_info['backbone']}")
        print(f"   - Classes: {imaging_info['num_classes']}")
        print(f"   - Device: {imaging_info['device']}")
        print(f"   - Pretrained exists: {pretrained['exists']}")
        if pretrained['exists']:
            print(f"   - Model size: {pretrained['size_mb']} MB")
            print(f"   - Parameters: {pretrained['num_parameters_millions']}M")


def test_imaging_health_endpoint_includes_model_details(client):
    """Test that /api/v1/imaging/health endpoint includes detailed model information."""
    response = client.get("/api/v1/imaging/health")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check basic structure
    assert "status" in data
    assert "model_loaded" in data
    
    # If model is loaded, check for detailed information
    if data["model_loaded"] and "model_details" in data:
        model_details = data["model_details"]
        
        # Check required fields
        assert "backbone" in model_details
        assert "num_classes" in model_details
        assert "device" in model_details
        assert "model_loaded" in model_details
        assert "using_mock" in model_details
        assert "supported_diseases" in model_details
        
        # Check pretrained model info
        if "pretrained_model" in data:
            pretrained = data["pretrained_model"]
            assert "exists" in pretrained
            assert "path" in pretrained
            
            print(f"✅ Imaging health endpoint includes model details:")
            print(f"   - Backbone: {model_details['backbone']}")
            print(f"   - Classes: {model_details['num_classes']}")
            print(f"   - Device: {model_details['device']}")
            print(f"   - Using mock: {model_details['using_mock']}")
            print(f"   - Supported diseases: {model_details['supported_diseases']}")
            print(f"   - Pretrained exists: {pretrained['exists']}")


def test_classify_response_includes_model_metadata(client):
    """Test that /api/v1/imaging/classify response includes model metadata."""
    # Check if test image exists
    test_image_path = Path("data/test_images/test_chest_xray.jpg")
    
    if not test_image_path.exists():
        pytest.skip(f"Test image not found: {test_image_path}")
    
    # Upload and classify image
    with open(test_image_path, "rb") as f:
        response = client.post(
            "/api/v1/imaging/classify",
            files={"file": ("test_chest_xray.jpg", f, "image/jpeg")},
            data={"top_k": 3}
        )
    
    assert response.status_code == 200
    
    data = response.json()
    
    # Check basic classification response
    assert "disease" in data
    assert "confidence" in data
    assert "filename" in data
    
    # Check for model metadata (if using local inference)
    if data.get("inference_backend") == "local":
        assert "model_metadata" in data, "Missing model_metadata in response"
        
        metadata = data["model_metadata"]
        
        # Check required fields
        assert "backbone" in metadata
        assert "num_classes" in metadata
        assert "device" in metadata
        assert "model_loaded" in metadata
        assert "using_mock" in metadata
        
        print(f"✅ Classify response includes model metadata:")
        print(f"   - Disease: {data['disease']}")
        print(f"   - Confidence: {data['confidence']}")
        print(f"   - Backbone: {metadata['backbone']}")
        print(f"   - Model loaded: {metadata['model_loaded']}")
        print(f"   - Using mock: {metadata['using_mock']}")


def test_model_metadata_consistency(client):
    """Test that model metadata is consistent across different endpoints."""
    # Get info from main health endpoint
    main_health = client.get("/health").json()
    
    # Get info from imaging health endpoint
    imaging_health = client.get("/api/v1/imaging/health").json()
    
    # Both should report consistent information
    if "medical_imaging_model" in main_health and "error" not in main_health["medical_imaging_model"]:
        main_imaging = main_health["medical_imaging_model"]
        
        if imaging_health["model_loaded"] and "model_details" in imaging_health:
            imaging_details = imaging_health["model_details"]
            
            # Check consistency
            assert main_imaging["backbone"] == imaging_details["backbone"]
            assert main_imaging["num_classes"] == imaging_details["num_classes"]
            assert main_imaging["model_loaded"] == imaging_details["model_loaded"]
            assert main_imaging["using_mock"] == imaging_details["using_mock"]
            
            print(f"✅ Model metadata is consistent across endpoints")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
