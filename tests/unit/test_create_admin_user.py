"""
Unit tests for create_admin_user script.

Tests the admin user creation functionality including validation,
error handling, and database operations.

Requirements: 21.1, 21.2
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.models import Base, User
from src.auth.services.user_service import UserService


@pytest.fixture
def test_db():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_create_admin_user_success(test_db):
    """Test successful admin user creation."""
    user_service = UserService(test_db)
    
    # Create admin user
    admin = user_service.create_user(
        email="admin@test.com",
        password="AdminPass123!",
        is_admin=True
    )
    
    # Verify admin user was created correctly
    assert admin.email == "admin@test.com"
    assert admin.is_admin is True
    assert admin.is_active is True
    assert admin.password_hash is not None
    assert len(admin.password_hash) > 0


def test_create_admin_user_duplicate_email(test_db):
    """Test that duplicate email addresses are rejected."""
    user_service = UserService(test_db)
    
    # Create first admin user
    user_service.create_user(
        email="admin@test.com",
        password="AdminPass123!",
        is_admin=True
    )
    
    # Attempt to create duplicate admin user
    with pytest.raises(ValueError, match="Email already registered"):
        user_service.create_user(
            email="admin@test.com",
            password="DifferentPass123!",
            is_admin=True
        )


def test_create_admin_user_invalid_email(test_db):
    """Test that invalid email formats are rejected."""
    user_service = UserService(test_db)
    
    # Attempt to create admin user with invalid email
    with pytest.raises(ValueError, match="Invalid email format"):
        user_service.create_user(
            email="invalid-email",
            password="AdminPass123!",
            is_admin=True
        )


def test_create_admin_user_weak_password(test_db):
    """Test that weak passwords are rejected."""
    user_service = UserService(test_db)
    
    # Test password too short
    with pytest.raises(ValueError, match="at least 8 characters"):
        user_service.create_user(
            email="admin@test.com",
            password="Weak1!",
            is_admin=True
        )
    
    # Test password without uppercase
    with pytest.raises(ValueError, match="uppercase letter"):
        user_service.create_user(
            email="admin@test.com",
            password="weakpass123!",
            is_admin=True
        )
    
    # Test password without lowercase
    with pytest.raises(ValueError, match="lowercase letter"):
        user_service.create_user(
            email="admin@test.com",
            password="WEAKPASS123!",
            is_admin=True
        )
    
    # Test password without number
    with pytest.raises(ValueError, match="number"):
        user_service.create_user(
            email="admin@test.com",
            password="WeakPass!",
            is_admin=True
        )
    
    # Test password without special character
    with pytest.raises(ValueError, match="special character"):
        user_service.create_user(
            email="admin@test.com",
            password="WeakPass123",
            is_admin=True
        )


def test_admin_user_attributes(test_db):
    """Test that admin user has correct attributes set."""
    user_service = UserService(test_db)
    
    # Create admin user
    admin = user_service.create_user(
        email="admin@test.com",
        password="AdminPass123!",
        is_admin=True
    )
    
    # Verify all attributes
    assert admin.id is not None
    assert admin.email == "admin@test.com"
    assert admin.is_admin is True
    assert admin.is_active is True
    assert admin.deleted_at is None
    assert admin.created_at is not None
    assert admin.updated_at is not None
    assert admin.last_activity_at is None


def test_regular_user_vs_admin_user(test_db):
    """Test that regular users and admin users are distinguished correctly."""
    user_service = UserService(test_db)
    
    # Create regular user
    regular_user = user_service.create_user(
        email="user@test.com",
        password="UserPass123!",
        is_admin=False
    )
    
    # Create admin user
    admin_user = user_service.create_user(
        email="admin@test.com",
        password="AdminPass123!",
        is_admin=True
    )
    
    # Verify distinction
    assert regular_user.is_admin is False
    assert admin_user.is_admin is True
    
    # Verify both are active
    assert regular_user.is_active is True
    assert admin_user.is_active is True
