"""
Shared fixtures for integration tests.

Provides common test fixtures for API testing, database setup, and test data.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from typing import Generator, Dict, Any
import tempfile
import shutil
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from main import app


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path("data/test_images")


@pytest.fixture(scope="session")
def sample_xray_image(test_data_dir: Path) -> Path:
    """
    Path to sample chest X-ray image for testing.
    
    This fixture provides a test image for imaging analysis tests.
    Alias: test_image (for compatibility with task requirements)
    
    Returns:
        Path to test chest X-ray image
    
    Raises:
        pytest.skip: If test image is not found
    """
    image_path = test_data_dir / "test_chest_xray.jpg"
    if not image_path.exists():
        pytest.skip(f"Test image not found: {image_path}")
    return image_path


@pytest.fixture(scope="session")
def test_image(sample_xray_image: Path) -> Path:
    """
    Alias for sample_xray_image fixture.
    
    Provides compatibility with task requirement 2.5.2.
    
    Returns:
        Path to test chest X-ray image
    """
    return sample_xray_image


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    FastAPI test client.
    
    Yields:
        TestClient instance for making API requests
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def temp_upload_dir() -> Generator[Path, None, None]:
    """
    Temporary directory for file uploads.
    
    Yields:
        Path to temporary directory (cleaned up after test)
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def mock_rag_response() -> Dict[str, Any]:
    """
    Mock RAG response for testing.
    
    Returns:
        Dictionary with mock RAG response data
    """
    return {
        "answer": "Pneumonia is an infection that inflames the air sacs in one or both lungs. "
                  "The air sacs may fill with fluid or pus, causing cough with phlegm or pus, "
                  "fever, chills, and difficulty breathing.",
        "sources": [
            {
                "disease": "Pneumonia",
                "category": "Respiratory Infection",
                "relevance_score": 0.95
            },
            {
                "disease": "COVID-19",
                "category": "Viral Respiratory Disease",
                "relevance_score": 0.78
            }
        ],
        "confidence": 0.92,
        "language": "en",
        "language_detected": "en"
    }


@pytest.fixture(scope="function")
def mock_imaging_response() -> Dict[str, Any]:
    """
    Mock imaging response for testing.
    
    Returns:
        Dictionary with mock imaging response data
    """
    return {
        "disease": "Pneumonia",
        "confidence": 0.87,
        "top_k_predictions": [
            {"disease": "Pneumonia", "confidence": 0.87},
            {"disease": "COVID-19", "confidence": 0.12},
            {"disease": "Normal", "confidence": 0.01}
        ]
    }


@pytest.fixture(scope="function")
def mock_vitals_response() -> Dict[str, Any]:
    """
    Mock vitals response for testing.
    
    Returns:
        Dictionary with mock vitals response data
    """
    return {
        "heart_rate": 72.0,
        "blood_pressure": {
            "systolic": 120.0,
            "diastolic": 80.0
        },
        "respiratory_rate": 16.0,
        "oxygen_saturation": 98.0,
        "confidence": 0.85
    }


@pytest.fixture(scope="function")
def sample_rag_queries() -> list:
    """
    Sample RAG queries for testing.
    
    Returns:
        List of sample medical queries
    """
    return [
        "What are the symptoms of pneumonia?",
        "How is tuberculosis diagnosed?",
        "What causes COVID-19?",
        "What is the treatment for heart failure?",
        "How to prevent malaria?",
        "What are the risk factors for diabetes?",
        "Describe the symptoms of asthma",
        "What is cardiomegaly?",
        "How is hypertension treated?",
        "What causes pleural effusion?"
    ]


@pytest.fixture(scope="function")
def sample_diseases() -> list:
    """
    Sample disease names for testing.
    
    Returns:
        List of disease names
    """
    return [
        "Pneumonia",
        "COVID-19",
        "Tuberculosis",
        "Cardiomegaly",
        "Heart Failure",
        "Asthma",
        "COPD",
        "Diabetes",
        "Hypertension",
        "Malaria"
    ]


@pytest.fixture(scope="function")
def test_database() -> Generator[Dict[str, Any], None, None]:
    """
    Test database fixture for integration tests.
    
    Note: Currently returns a mock database since no actual database
    is implemented in the application. When a real database is added,
    this fixture should be updated to create a test database instance.
    
    Yields:
        Dictionary with mock database connection info
    """
    # Mock database for now - replace with real DB when implemented
    mock_db = {
        "type": "mock",
        "connected": True,
        "url": "sqlite:///:memory:",
        "tables": []
    }
    
    yield mock_db
    
    # Cleanup: Close connections, drop test tables, etc.
    # When real DB is implemented, add cleanup logic here
    pass


@pytest.fixture(scope="function")
def cleanup_test_files() -> Generator[list, None, None]:
    """
    Track and cleanup test files created during tests.
    
    Usage:
        def test_something(cleanup_test_files):
            # Create test file
            test_file = Path("test_output.txt")
            test_file.write_text("test")
            
            # Register for cleanup
            cleanup_test_files.append(test_file)
    
    Yields:
        List to track files for cleanup
    """
    files_to_cleanup = []
    
    yield files_to_cleanup
    
    # Cleanup all registered files
    for file_path in files_to_cleanup:
        try:
            if isinstance(file_path, (str, Path)):
                path = Path(file_path)
                if path.exists():
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
        except Exception as e:
            # Log but don't fail test on cleanup errors
            print(f"Warning: Failed to cleanup {file_path}: {e}")


@pytest.fixture(scope="function")
def cleanup_uploaded_images() -> Generator[list, None, None]:
    """
    Track and cleanup uploaded images during tests.
    
    Specifically for cleaning up images uploaded to the API
    during integration tests.
    
    Yields:
        List to track uploaded image paths for cleanup
    """
    uploaded_images = []
    
    yield uploaded_images
    
    # Cleanup all uploaded images
    for image_path in uploaded_images:
        try:
            path = Path(image_path)
            if path.exists() and path.is_file():
                path.unlink()
        except Exception as e:
            print(f"Warning: Failed to cleanup uploaded image {image_path}: {e}")


@pytest.fixture(autouse=True)
def reset_test_state():
    """
    Reset test state before each test.
    
    This fixture runs automatically before each test to ensure clean state.
    Performs cleanup of temporary files and resets any global state.
    """
    # Pre-test setup
    yield
    
    # Post-test cleanup
    # Clean up any temporary directories in the project root
    temp_patterns = ["temp_*", "test_*"]
    for pattern in temp_patterns:
        for temp_path in Path(".").glob(pattern):
            if temp_path.is_dir():
                try:
                    shutil.rmtree(temp_path, ignore_errors=True)
                except Exception:
                    pass


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL for API endpoints."""
    return "http://localhost:8001"


@pytest.fixture(scope="session")
def api_timeout() -> int:
    """Timeout for API requests in seconds."""
    return 30


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "concurrent: marks tests that test concurrent behavior"
    )
    config.addinivalue_line(
        "markers", "requires_model: marks tests that require pretrained model"
    )
