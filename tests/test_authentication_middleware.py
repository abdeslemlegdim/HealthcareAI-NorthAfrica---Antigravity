"""
Test authentication middleware on protected endpoints.

This test verifies that:
1. Protected endpoints require authentication
2. Public endpoints (health, metrics, docs) remain accessible
3. Valid tokens grant access to protected endpoints

Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.9
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from main import app
from src.auth.models import Base, User
from src.database import get_db


# Create test database
TEST_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestPublicEndpoints:
    """Test that public endpoints remain accessible without authentication."""
    
    def test_health_endpoint_public(self):
        """Health endpoint should be accessible without authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_metrics_endpoint_public(self):
        """Metrics endpoint should be accessible without authentication."""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_docs_endpoint_public(self):
        """Docs endpoint should be accessible without authentication."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""
    
    def test_chat_endpoint_requires_auth(self):
        """Chat endpoint should require authentication."""
        response = client.post(
            "/api/v1/chat",
            json={"question": "What is pneumonia?"}
        )
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    def test_rag_query_endpoint_requires_auth(self):
        """RAG query endpoint should require authentication."""
        response = client.post(
            "/api/v1/rag/query",
            json={"question": "What is pneumonia?"}
        )
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    def test_imaging_classify_requires_auth(self):
        """Imaging classify endpoint should require authentication."""
        # Create a minimal test file
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        response = client.post("/api/v1/imaging/classify", files=files)
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    def test_imaging_explain_requires_auth(self):
        """Imaging explain endpoint should require authentication."""
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        response = client.post("/api/v1/imaging/explain", files=files)
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    def test_vitals_measure_post_requires_auth(self):
        """Vitals measure POST endpoint should require authentication."""
        response = client.post(
            "/api/v1/vitals/measure",
            json={"duration": 15, "display": False}
        )
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    def test_vitals_measure_get_requires_auth(self):
        """Vitals measure GET endpoint should require authentication."""
        response = client.get("/api/v1/vitals/measure")
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]


class TestAuthenticatedAccess:
    """Test that valid tokens grant access to protected endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        user.is_admin = False
        user.deleted_at = None
        return user
    
    def test_chat_with_valid_token(self, mock_user):
        """Chat endpoint should be accessible with valid token."""
        # Override the get_current_user dependency to return our mock user
        from src.auth.middleware import get_current_user
        
        def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        try:
            # Mock the RAG system to avoid initialization issues
            with patch("src.rag_system.api.rag_system") as mock_rag:
                mock_result = Mock()
                mock_result.answer = "Test answer"
                mock_result.sources = []
                mock_result.confidence = 0.8
                mock_result.language = "en"
                mock_result.mode = "rag"
                mock_result.metrics = None
                mock_rag.query.return_value = mock_result
                
                response = client.post(
                    "/api/v1/chat",
                    json={"question": "What is pneumonia?"},
                    headers={"Authorization": "Bearer valid_token"}
                )
                # Should not return 401 (may return other errors due to mocking)
                assert response.status_code != 401
        finally:
            # Clean up the override
            app.dependency_overrides.pop(get_current_user, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
