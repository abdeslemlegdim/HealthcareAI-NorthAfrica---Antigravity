"""
Unit tests for TokenService.

Tests JWT token generation, validation, refresh, and revocation functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.auth.services.token_service import TokenService
from src.auth.models import RefreshToken, User
from src.utils.config import Settings


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def mock_settings():
    """Create mock settings with JWT configuration."""
    settings = Mock(spec=Settings)
    settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only"
    settings.JWT_ALGORITHM = "HS256"
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    return settings


@pytest.fixture
def token_service(mock_db, mock_settings):
    """Create TokenService instance with mocked dependencies."""
    return TokenService(mock_db, mock_settings)


class TestAccessTokenGeneration:
    """Test access token creation and validation."""
    
    def test_create_access_token_default_expiry(self, token_service):
        """Test access token creation with default 30-minute expiry."""
        user_id = 123
        token = token_service.create_access_token(user_id)
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            token_service.secret_key,
            algorithms=[token_service.algorithm]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        
        # Verify expiration is approximately 30 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        delta = exp_time - iat_time
        
        assert 29 <= delta.total_seconds() / 60 <= 31  # Allow 1 minute tolerance
    
    def test_create_access_token_custom_expiry(self, token_service):
        """Test access token creation with custom expiration time."""
        user_id = 456
        custom_delta = timedelta(minutes=60)
        token = token_service.create_access_token(user_id, expires_delta=custom_delta)
        
        payload = jwt.decode(
            token,
            token_service.secret_key,
            algorithms=[token_service.algorithm]
        )
        
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        delta = exp_time - iat_time
        
        assert 59 <= delta.total_seconds() / 60 <= 61  # Allow 1 minute tolerance
    
    def test_verify_access_token_valid(self, token_service):
        """Test verification of valid access token."""
        user_id = 789
        token = token_service.create_access_token(user_id)
        
        payload = token_service.verify_access_token(token)
        
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
    
    def test_verify_access_token_invalid_signature(self, token_service):
        """Test verification fails with invalid signature."""
        # Create token with different secret
        payload = {"sub": 123, "type": "access", "exp": datetime.utcnow() + timedelta(minutes=30)}
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        with pytest.raises(InvalidTokenError):
            token_service.verify_access_token(token)
    
    def test_verify_access_token_expired(self, token_service):
        """Test verification fails with expired token."""
        user_id = 999
        # Create token that expired 1 minute ago
        expired_delta = timedelta(minutes=-1)
        token = token_service.create_access_token(user_id, expires_delta=expired_delta)
        
        with pytest.raises(ExpiredSignatureError):
            token_service.verify_access_token(token)
    
    def test_verify_access_token_wrong_type(self, token_service):
        """Test verification fails when token type is not 'access'."""
        payload = {
            "sub": 123,
            "type": "refresh",  # Wrong type
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, token_service.secret_key, algorithm=token_service.algorithm)
        
        with pytest.raises(InvalidTokenError, match="Invalid token type"):
            token_service.verify_access_token(token)


class TestRefreshTokenGeneration:
    """Test refresh token creation and storage."""
    
    @pytest.mark.asyncio
    async def test_create_refresh_token_default_expiry(self, token_service, mock_db):
        """Test refresh token creation with default 7-day expiry."""
        user_id = 123
        device_info = "Chrome on Windows"
        ip_address = "192.168.1.1"
        
        token = await token_service.create_refresh_token(
            user_id,
            device_info=device_info,
            ip_address=ip_address
        )
        
        # Verify token structure
        payload = jwt.decode(
            token,
            token_service.secret_key,
            algorithms=[token_service.algorithm]
        )
        
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
        
        # Verify expiration is approximately 7 days
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        delta = exp_time - iat_time
        
        assert 6.9 <= delta.days <= 7.1
        
        # Verify database storage was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_refresh_token_remember_me(self, token_service, mock_db):
        """Test refresh token creation with remember_me (30-day expiry)."""
        user_id = 456
        
        token = await token_service.create_refresh_token(user_id, remember_me=True)
        
        payload = jwt.decode(
            token,
            token_service.secret_key,
            algorithms=[token_service.algorithm]
        )
        
        # Verify expiration is approximately 30 days
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        delta = exp_time - iat_time
        
        assert 29.5 <= delta.days <= 30.5


class TestTokenRefresh:
    """Test token refresh and rotation."""
    
    @pytest.mark.asyncio
    async def test_refresh_tokens_success(self, token_service, mock_db):
        """Test successful token refresh with rotation."""
        user_id = 123
        
        # Create initial refresh token
        old_refresh_token = await token_service.create_refresh_token(user_id)
        
        # Mock database query for token verification
        mock_token_record = Mock(spec=RefreshToken)
        mock_token_record.revoked_at = None
        mock_token_record.expires_at = datetime.utcnow() + timedelta(days=7)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_token_record
        
        # Refresh tokens
        new_access_token, new_refresh_token = await token_service.refresh_tokens(
            old_refresh_token
        )
        
        # Verify new tokens are different
        assert new_access_token != old_refresh_token
        assert new_refresh_token != old_refresh_token
        
        # Verify new access token is valid
        access_payload = token_service.verify_access_token(new_access_token)
        assert access_payload["sub"] == user_id
        assert access_payload["type"] == "access"
        
        # Verify new refresh token is valid
        refresh_payload = jwt.decode(
            new_refresh_token,
            token_service.secret_key,
            algorithms=[token_service.algorithm]
        )
        assert refresh_payload["sub"] == user_id
        assert refresh_payload["type"] == "refresh"


class TestTokenRevocation:
    """Test token revocation functionality."""
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_token(self, token_service, mock_db):
        """Test revoking a single refresh token."""
        token = "test-refresh-token"
        
        # Mock database query
        mock_token_record = Mock(spec=RefreshToken)
        mock_token_record.revoked_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_token_record
        
        await token_service.revoke_refresh_token(token)
        
        # Verify revoked_at was set
        assert mock_token_record.revoked_at is not None
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self, token_service, mock_db):
        """Test revoking all tokens for a user."""
        user_id = 123
        
        # Mock database query returning multiple tokens
        mock_token1 = Mock(spec=RefreshToken)
        mock_token1.revoked_at = None
        mock_token2 = Mock(spec=RefreshToken)
        mock_token2.revoked_at = None
        
        mock_query = Mock()
        mock_query.all.return_value = [mock_token1, mock_token2]
        mock_db.query.return_value.filter.return_value.filter.return_value = mock_query
        
        await token_service.revoke_all_user_tokens(user_id)
        
        # Verify both tokens were revoked
        assert mock_token1.revoked_at is not None
        assert mock_token2.revoked_at is not None
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_except_current(self, token_service, mock_db):
        """Test revoking all tokens except the current one."""
        user_id = 123
        current_token = "current-token"
        
        # Mock database query
        mock_token1 = Mock(spec=RefreshToken)
        mock_token1.revoked_at = None
        
        mock_query = Mock()
        mock_query.all.return_value = [mock_token1]
        mock_filter = Mock()
        mock_filter.filter.return_value = mock_query
        mock_db.query.return_value.filter.return_value.filter.return_value = mock_filter
        
        await token_service.revoke_all_user_tokens(user_id, except_token=current_token)
        
        # Verify filter was called to exclude current token
        assert mock_token1.revoked_at is not None


class TestSessionManagement:
    """Test session management functionality."""
    
    @pytest.mark.asyncio
    async def test_get_active_sessions(self, token_service, mock_db):
        """Test retrieving active sessions for a user."""
        user_id = 123
        
        # Mock database query
        mock_session1 = Mock(spec=RefreshToken)
        mock_session2 = Mock(spec=RefreshToken)
        
        mock_query = Mock()
        mock_query.all.return_value = [mock_session1, mock_session2]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value = mock_query
        
        sessions = await token_service.get_active_sessions(user_id)
        
        assert len(sessions) == 2
        assert sessions[0] == mock_session1
        assert sessions[1] == mock_session2
    
    @pytest.mark.asyncio
    async def test_revoke_session_by_id_success(self, token_service, mock_db):
        """Test revoking a specific session by ID."""
        session_id = 456
        user_id = 123
        
        # Mock database query
        mock_session = Mock(spec=RefreshToken)
        mock_session.revoked_at = None
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_session
        
        result = await token_service.revoke_session_by_id(session_id, user_id)
        
        assert result is True
        assert mock_session.revoked_at is not None
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_revoke_session_by_id_not_found(self, token_service, mock_db):
        """Test revoking a session that doesn't exist."""
        session_id = 999
        user_id = 123
        
        # Mock database query returning None
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        result = await token_service.revoke_session_by_id(session_id, user_id)
        
        assert result is False
        mock_db.commit.assert_not_called()


def test_hash_token(token_service):
    """Test token hashing for secure storage."""
    token1 = "test-token-123"
    token2 = "test-token-456"
    
    hash1 = token_service._hash_token(token1)
    hash2 = token_service._hash_token(token2)
    
    # Verify hashes are different for different tokens
    assert hash1 != hash2
    
    # Verify same token produces same hash
    assert hash1 == token_service._hash_token(token1)
    
    # Verify hash is hexadecimal string
    assert all(c in "0123456789abcdef" for c in hash1)
