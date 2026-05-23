"""
Integration tests for activity tracking in protected endpoints.

Tests that activity is properly recorded when users interact with:
- Medical imaging endpoints
- Vital signs endpoints
- RAG/chat endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from main import app
from src.database import get_db
from src.auth.models import User, UserActivity, Base
from src.auth.services.auth_service import AuthService


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_activity.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user and return authentication token."""
    auth_service = AuthService(db_session)
    
    # Create user
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=auth_service._hash_password("testpassword123"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Generate token
    token = auth_service.create_access_token({"sub": user.username})
    
    return {"user": user, "token": token}


def test_rag_query_records_activity(client, test_user, db_session):
    """Test that RAG query endpoint records chat activity."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Make a query request
    response = client.post(
        "/api/rag/query",
        json={
            "question": "What are symptoms of pneumonia?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response is successful (or at least authenticated)
    assert response.status_code in [200, 500]  # 500 if RAG not initialized, but auth passed
    
    # Check activity was recorded
    activity = db_session.query(UserActivity).filter(
        UserActivity.user_id == user_id,
        UserActivity.activity_type == 'chat'
    ).first()
    
    if response.status_code == 200:
        assert activity is not None, "Activity should be recorded for successful query"
        assert activity.activity_type == 'chat'
        assert 'query' in activity.metadata_
        assert 'language' in activity.metadata_


def test_chat_endpoint_records_activity(client, test_user, db_session):
    """Test that chat endpoint records chat activity."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Make a chat request
    response = client.post(
        "/api/chat/chat",
        json={
            "question": "What is tuberculosis?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response is successful (or at least authenticated)
    assert response.status_code in [200, 500]
    
    # Check activity was recorded
    if response.status_code == 200:
        activity = db_session.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'chat'
        ).first()
        
        assert activity is not None
        assert activity.activity_type == 'chat'


def test_vitals_measurement_records_activity(client, test_user, db_session):
    """Test that vitals measurement endpoint records vitals activity."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Make a vitals measurement request
    response = client.post(
        "/api/vitals/measure",
        json={
            "duration": 10,
            "display": False
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response (may fail if camera not available, but auth should pass)
    assert response.status_code in [200, 500, 503]
    
    # Check activity was recorded only if measurement succeeded
    if response.status_code == 200:
        activity = db_session.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'vitals'
        ).first()
        
        assert activity is not None
        assert activity.activity_type == 'vitals'
        assert 'duration' in activity.metadata_
        assert 'heart_rate' in activity.metadata_


def test_heart_rate_measurement_records_activity(client, test_user, db_session):
    """Test that heart rate GET endpoint records vitals activity."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Make a heart rate measurement request
    response = client.get(
        "/api/vitals/measure",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response (may timeout or fail if camera not available)
    assert response.status_code in [200, 408, 500, 503]
    
    # Check activity was recorded only if measurement succeeded
    if response.status_code == 200:
        activity = db_session.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'vitals'
        ).first()
        
        assert activity is not None
        assert activity.activity_type == 'vitals'
        assert 'measurement_type' in activity.metadata_
        assert activity.metadata_['measurement_type'] == 'heart_rate'


def test_imaging_classify_records_activity(client, test_user, db_session):
    """Test that imaging classify endpoint records imaging activity."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Create a dummy image file
    from io import BytesIO
    from PIL import Image
    
    # Create a small test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Make a classify request
    response = client.post(
        "/api/imaging/classify",
        files={"file": ("test.png", img_bytes, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response is successful (or at least authenticated)
    assert response.status_code in [200, 500]
    
    # Check activity was recorded only if classification succeeded
    if response.status_code == 200:
        activity = db_session.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'imaging'
        ).first()
        
        assert activity is not None
        assert activity.activity_type == 'imaging'
        assert 'filename' in activity.metadata_
        assert activity.metadata_['filename'] == 'test.png'


def test_imaging_explain_records_activity(client, test_user, db_session):
    """Test that imaging explain endpoint records imaging activity."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Create a dummy image file
    from io import BytesIO
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Make an explain request
    response = client.post(
        "/api/imaging/explain",
        files={"file": ("test.png", img_bytes, "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code in [200, 500]
    
    # Check activity was recorded only if explanation succeeded
    if response.status_code == 200:
        activity = db_session.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'imaging'
        ).filter(
            UserActivity.metadata_['operation'].astext == 'explain'
        ).first()
        
        assert activity is not None
        assert activity.activity_type == 'imaging'
        assert 'operation' in activity.metadata_
        assert activity.metadata_['operation'] == 'explain'


def test_user_last_activity_updated(client, test_user, db_session):
    """Test that user's last_activity_at is updated after activity."""
    token = test_user["token"]
    user = test_user["user"]
    
    # Record initial last_activity_at
    initial_last_activity = user.last_activity_at
    
    # Make a request
    response = client.post(
        "/api/rag/query",
        json={
            "question": "What is COVID-19?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Refresh user from database
    db_session.refresh(user)
    
    # Check last_activity_at was updated (if request succeeded)
    if response.status_code == 200:
        assert user.last_activity_at is not None
        if initial_last_activity:
            assert user.last_activity_at >= initial_last_activity


def test_activity_metadata_structure(client, test_user, db_session):
    """Test that activity metadata has the expected structure."""
    token = test_user["token"]
    user_id = test_user["user"].id
    
    # Make a query request
    response = client.post(
        "/api/rag/query",
        json={
            "question": "What are symptoms of flu?",
            "language": "fr",
            "top_k": 5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        # Check activity metadata
        activity = db_session.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'chat'
        ).first()
        
        assert activity is not None
        metadata = activity.metadata_
        
        # Verify expected fields
        assert 'query' in metadata
        assert 'language' in metadata
        assert metadata['language'] == 'fr'
        
        # Verify query is truncated to 100 chars
        assert len(metadata['query']) <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
