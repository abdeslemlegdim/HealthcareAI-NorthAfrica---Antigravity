"""
Unit tests for UserService.

Tests all user management operations including creation, retrieval, updates,
and admin operations.

Requirements: 1.5, 2.1, 2.2, 6.1, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 21.6, 21.7, 21.8
"""

import pytest
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.models import Base, User, RefreshToken
from src.auth.services.user_service import UserService
from src.auth.utils.password import hash_password


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def user_service(db_session):
    """Create a UserService instance with test database."""
    return UserService(db_session)


class TestCreateUser:
    """Tests for create_user method."""
    
    def test_create_user_success(self, user_service):
        """Test successful user creation with valid email and password."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password_hash is not None
        assert user.password_hash != "SecurePass123!"
        assert user.is_admin is False
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.deleted_at is None
    
    def test_create_admin_user(self, user_service):
        """Test creating a user with admin privileges."""
        user = user_service.create_user("admin@example.com", "AdminPass123!", is_admin=True)
        
        assert user.is_admin is True
        assert user.email == "admin@example.com"
    
    def test_create_user_invalid_email(self, user_service):
        """Test user creation fails with invalid email format."""
        with pytest.raises(ValueError, match="Invalid email format"):
            user_service.create_user("invalid-email", "SecurePass123!")
    
    def test_create_user_weak_password(self, user_service):
        """Test user creation fails with weak password."""
        with pytest.raises(ValueError, match="Invalid password"):
            user_service.create_user("test@example.com", "weak")
    
    def test_create_user_no_uppercase(self, user_service):
        """Test user creation fails when password lacks uppercase letter."""
        with pytest.raises(ValueError, match="uppercase"):
            user_service.create_user("test@example.com", "securepass123!")
    
    def test_create_user_no_lowercase(self, user_service):
        """Test user creation fails when password lacks lowercase letter."""
        with pytest.raises(ValueError, match="lowercase"):
            user_service.create_user("test@example.com", "SECUREPASS123!")
    
    def test_create_user_no_number(self, user_service):
        """Test user creation fails when password lacks number."""
        with pytest.raises(ValueError, match="number"):
            user_service.create_user("test@example.com", "SecurePass!")
    
    def test_create_user_no_special_char(self, user_service):
        """Test user creation fails when password lacks special character."""
        with pytest.raises(ValueError, match="special character"):
            user_service.create_user("test@example.com", "SecurePass123")
    
    def test_create_user_duplicate_email(self, user_service):
        """Test user creation fails when email already exists."""
        user_service.create_user("test@example.com", "SecurePass123!")
        
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user("test@example.com", "AnotherPass123!")
    
    def test_create_user_email_normalization(self, user_service):
        """Test email is normalized during user creation."""
        user = user_service.create_user("Test@Example.COM", "SecurePass123!")
        
        # Email domain should be normalized to lowercase
        # Note: email-validator preserves case in local part per RFC 5321
        assert user.email == "Test@example.com"


class TestGetUserByEmail:
    """Tests for get_user_by_email method."""
    
    def test_get_existing_user(self, user_service):
        """Test retrieving an existing user by email."""
        created_user = user_service.create_user("test@example.com", "SecurePass123!")
        
        retrieved_user = user_service.get_user_by_email("test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "test@example.com"
    
    def test_get_nonexistent_user(self, user_service):
        """Test retrieving a non-existent user returns None."""
        user = user_service.get_user_by_email("nonexistent@example.com")
        
        assert user is None
    
    def test_get_soft_deleted_user(self, user_service, db_session):
        """Test soft-deleted users are not returned."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        user_service.soft_delete_user(user.id)
        
        retrieved_user = user_service.get_user_by_email("test@example.com")
        
        assert retrieved_user is None


class TestGetUserById:
    """Tests for get_user_by_id method."""
    
    def test_get_existing_user(self, user_service):
        """Test retrieving an existing user by ID."""
        created_user = user_service.create_user("test@example.com", "SecurePass123!")
        
        retrieved_user = user_service.get_user_by_id(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "test@example.com"
    
    def test_get_nonexistent_user(self, user_service):
        """Test retrieving a non-existent user returns None."""
        user = user_service.get_user_by_id(99999)
        
        assert user is None
    
    def test_get_soft_deleted_user(self, user_service):
        """Test soft-deleted users are not returned."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        user_service.soft_delete_user(user.id)
        
        retrieved_user = user_service.get_user_by_id(user.id)
        
        assert retrieved_user is None


class TestVerifyPassword:
    """Tests for verify_password method."""
    
    def test_verify_correct_password(self, user_service):
        """Test password verification succeeds with correct password."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        is_valid = user_service.verify_password("SecurePass123!", user.password_hash)
        
        assert is_valid is True
    
    def test_verify_incorrect_password(self, user_service):
        """Test password verification fails with incorrect password."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        is_valid = user_service.verify_password("WrongPassword123!", user.password_hash)
        
        assert is_valid is False
    
    def test_verify_empty_password(self, user_service):
        """Test password verification fails with empty password."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        is_valid = user_service.verify_password("", user.password_hash)
        
        assert is_valid is False


class TestUpdateUserEmail:
    """Tests for update_user_email method."""
    
    def test_update_email_success(self, user_service):
        """Test successful email update."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        original_updated_at = user.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.01)
        
        updated_user = user_service.update_user_email(user.id, "newemail@example.com")
        
        assert updated_user.email == "newemail@example.com"
        assert updated_user.updated_at >= original_updated_at
    
    def test_update_email_invalid_format(self, user_service):
        """Test email update fails with invalid format."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        with pytest.raises(ValueError, match="Invalid email format"):
            user_service.update_user_email(user.id, "invalid-email")
    
    def test_update_email_already_exists(self, user_service):
        """Test email update fails when new email already exists."""
        user1 = user_service.create_user("user1@example.com", "SecurePass123!")
        user2 = user_service.create_user("user2@example.com", "SecurePass123!")
        
        with pytest.raises(ValueError, match="Email already registered"):
            user_service.update_user_email(user1.id, "user2@example.com")
    
    def test_update_email_same_email(self, user_service):
        """Test updating to the same email succeeds."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        updated_user = user_service.update_user_email(user.id, "test@example.com")
        
        assert updated_user.email == "test@example.com"
    
    def test_update_email_nonexistent_user(self, user_service):
        """Test email update fails for non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_email(99999, "newemail@example.com")
    
    def test_update_email_normalization(self, user_service):
        """Test email is normalized during update."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        updated_user = user_service.update_user_email(user.id, "NewEmail@Example.COM")
        
        # Email domain should be normalized to lowercase
        # Note: email-validator preserves case in local part per RFC 5321
        assert updated_user.email == "NewEmail@example.com"


class TestUpdateUserPassword:
    """Tests for update_user_password method."""
    
    def test_update_password_success(self, user_service):
        """Test successful password update."""
        user = user_service.create_user("test@example.com", "OldPass123!")
        old_hash = user.password_hash
        
        user_service.update_user_password(user.id, "NewPass123!")
        
        # Refresh user from database
        updated_user = user_service.get_user_by_id(user.id)
        
        assert updated_user.password_hash != old_hash
        assert user_service.verify_password("NewPass123!", updated_user.password_hash)
        assert not user_service.verify_password("OldPass123!", updated_user.password_hash)
    
    def test_update_password_weak_password(self, user_service):
        """Test password update fails with weak password."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        with pytest.raises(ValueError, match="Invalid password"):
            user_service.update_user_password(user.id, "weak")
    
    def test_update_password_nonexistent_user(self, user_service):
        """Test password update fails for non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_password(99999, "NewPass123!")
    
    def test_update_password_revokes_tokens(self, user_service, db_session):
        """Test password update revokes all existing refresh tokens."""
        user = user_service.create_user("test@example.com", "OldPass123!")
        
        # Create some refresh tokens
        token1 = RefreshToken(
            user_id=user.id,
            token_hash="token1_hash",
            expires_at=datetime.utcnow(),
            revoked_at=None
        )
        token2 = RefreshToken(
            user_id=user.id,
            token_hash="token2_hash",
            expires_at=datetime.utcnow(),
            revoked_at=None
        )
        db_session.add(token1)
        db_session.add(token2)
        db_session.commit()
        
        # Update password
        user_service.update_user_password(user.id, "NewPass123!")
        
        # Check tokens are revoked
        db_session.refresh(token1)
        db_session.refresh(token2)
        
        assert token1.revoked_at is not None
        assert token2.revoked_at is not None


class TestUpdateLastActivity:
    """Tests for update_last_activity method."""
    
    def test_update_last_activity_success(self, user_service):
        """Test successful last activity update."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        original_activity = user.last_activity_at
        
        user_service.update_last_activity(user.id)
        
        # Refresh user from database
        updated_user = user_service.get_user_by_id(user.id)
        
        assert updated_user.last_activity_at is not None
        assert updated_user.last_activity_at != original_activity
    
    def test_update_last_activity_nonexistent_user(self, user_service):
        """Test updating last activity for non-existent user does not raise error."""
        # Should not raise an error, just silently fail
        user_service.update_last_activity(99999)


class TestDisableUser:
    """Tests for disable_user method."""
    
    def test_disable_user_success(self, user_service):
        """Test successful user account disable."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        original_updated_at = user.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.01)
        
        disabled_user = user_service.disable_user(user.id)
        
        assert disabled_user.is_active is False
        assert disabled_user.updated_at >= original_updated_at
    
    def test_disable_user_revokes_tokens(self, user_service, db_session):
        """Test disabling user revokes all active sessions."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        # Create refresh tokens
        token = RefreshToken(
            user_id=user.id,
            token_hash="token_hash",
            expires_at=datetime.utcnow(),
            revoked_at=None
        )
        db_session.add(token)
        db_session.commit()
        
        # Disable user
        user_service.disable_user(user.id)
        
        # Check token is revoked
        db_session.refresh(token)
        assert token.revoked_at is not None
    
    def test_disable_user_nonexistent(self, user_service):
        """Test disabling non-existent user raises error."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.disable_user(99999)


class TestEnableUser:
    """Tests for enable_user method."""
    
    def test_enable_user_success(self, user_service):
        """Test successful user account enable."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        user_service.disable_user(user.id)
        
        enabled_user = user_service.enable_user(user.id)
        
        assert enabled_user.is_active is True
    
    def test_enable_user_nonexistent(self, user_service):
        """Test enabling non-existent user raises error."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.enable_user(99999)


class TestSoftDeleteUser:
    """Tests for soft_delete_user method."""
    
    def test_soft_delete_user_success(self, user_service):
        """Test successful user soft delete."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        deleted_user = user_service.soft_delete_user(user.id)
        
        assert deleted_user.deleted_at is not None
        assert deleted_user.is_active is False
    
    def test_soft_delete_user_revokes_tokens(self, user_service, db_session):
        """Test soft deleting user revokes all active sessions."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        
        # Create refresh tokens
        token = RefreshToken(
            user_id=user.id,
            token_hash="token_hash",
            expires_at=datetime.utcnow(),
            revoked_at=None
        )
        db_session.add(token)
        db_session.commit()
        
        # Soft delete user
        user_service.soft_delete_user(user.id)
        
        # Check token is revoked
        db_session.refresh(token)
        assert token.revoked_at is not None
    
    def test_soft_delete_user_not_retrievable(self, user_service):
        """Test soft-deleted user cannot be retrieved by normal queries."""
        user = user_service.create_user("test@example.com", "SecurePass123!")
        user_service.soft_delete_user(user.id)
        
        # User should not be retrievable
        retrieved_user = user_service.get_user_by_id(user.id)
        assert retrieved_user is None
        
        retrieved_by_email = user_service.get_user_by_email("test@example.com")
        assert retrieved_by_email is None
    
    def test_soft_delete_user_nonexistent(self, user_service):
        """Test soft deleting non-existent user raises error."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.soft_delete_user(99999)
