"""
Token Service for JWT token management.

This module provides JWT token generation, validation, and refresh token management
for the authentication system. It handles:
- Access token generation (30 minute expiry)
- Refresh token generation (7 days or 30 days with remember_me)
- Token validation and verification
- Token refresh and rotation
- Token revocation for logout and security

Requirements: 2.4, 2.5, 2.6, 2.8, 3.1, 3.2, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2, 5.4
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from sqlalchemy.orm import Session

from src.auth.models import RefreshToken
from src.utils.config import Settings


class TokenService:
    """
    Service for managing JWT tokens and refresh token lifecycle.
    
    Handles creation, validation, refresh, and revocation of authentication tokens.
    """
    
    def __init__(self, db: Session, settings: Settings):
        """
        Initialize TokenService.
        
        Args:
            db: Database session for refresh token storage
            settings: Application settings with JWT configuration
        """
        self.db = db
        self.settings = settings
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(
        self,
        user_id: int,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Generate JWT access token.
        
        Creates a short-lived access token (default 30 minutes) for API authentication.
        
        Args:
            user_id: User ID to encode in token
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT access token string
        
        Requirements: 2.4, 3.4
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        payload = {
            "sub": str(user_id),  # JWT spec requires sub to be a string
            "type": "access",
            "exp": expire,
            "iat": now
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    async def create_refresh_token(
        self,
        user_id: int,
        remember_me: bool = False,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Generate JWT refresh token and store in database.
        
        Creates a long-lived refresh token (7 days default, 30 days with remember_me)
        and stores its hash in the database for validation.
        
        Args:
            user_id: User ID to encode in token
            remember_me: If True, extend expiration to 30 days
            device_info: Optional device information for session tracking
            ip_address: Optional IP address for security tracking
        
        Returns:
            Encoded JWT refresh token string
        
        Requirements: 2.5, 2.6, 2.8, 3.5, 3.7
        """
        # Determine expiration time
        if remember_me:
            expires_delta = timedelta(days=30)
        else:
            expires_delta = timedelta(days=7)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        # Generate unique token ID
        jti = secrets.token_urlsafe(32)
        
        payload = {
            "sub": str(user_id),  # JWT spec requires sub to be a string
            "type": "refresh",
            "jti": jti,
            "exp": expire,
            "iat": now
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        # Store token hash in database
        token_hash = self._hash_token(token)
        refresh_token_record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expire,
            device_info=device_info,
            ip_address=ip_address
        )
        
        self.db.add(refresh_token_record)
        self.db.commit()
        
        return token
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode access token.
        
        Validates token signature and expiration, then returns decoded payload.
        
        Args:
            token: JWT access token to verify
        
        Returns:
            Decoded token payload with user_id in 'sub' field (as integer)
        
        Raises:
            InvalidTokenError: If token is invalid or malformed
            ExpiredSignatureError: If token has expired
        
        Requirements: 4.3, 4.4, 4.5
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != "access":
                raise InvalidTokenError("Invalid token type")
            
            # Convert sub back to integer for consistency
            payload["sub"] = int(payload["sub"])
            
            return payload
            
        except ExpiredSignatureError:
            raise ExpiredSignatureError("Access token has expired")
        except InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid access token: {str(e)}")
    
    async def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify refresh token and check not revoked.
        
        Validates token signature, expiration, and checks database to ensure
        token has not been revoked.
        
        Args:
            token: JWT refresh token to verify
        
        Returns:
            Decoded token payload with user_id in 'sub' field (as integer)
        
        Raises:
            InvalidTokenError: If token is invalid, malformed, or revoked
            ExpiredSignatureError: If token has expired
        
        Requirements: 3.1, 3.2, 3.3, 5.4
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != "refresh":
                raise InvalidTokenError("Invalid token type")
            
            # Check if token is revoked in database
            token_hash = self._hash_token(token)
            refresh_token_record = self.db.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash
            ).first()
            
            if not refresh_token_record:
                raise InvalidTokenError("Refresh token not found")
            
            if refresh_token_record.revoked_at is not None:
                raise InvalidTokenError("Refresh token has been revoked")
            
            # Check if token has expired in database
            if refresh_token_record.expires_at < datetime.utcnow():
                raise ExpiredSignatureError("Refresh token has expired")
            
            # Convert sub back to integer for consistency
            payload["sub"] = int(payload["sub"])
            
            return payload
            
        except ExpiredSignatureError:
            raise ExpiredSignatureError("Refresh token has expired")
        except InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {str(e)}")
    
    async def refresh_tokens(
        self,
        refresh_token: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate new access and refresh tokens, invalidate old refresh token.
        
        Validates the provided refresh token, generates new tokens, and revokes
        the old refresh token to prevent reuse (token rotation).
        
        Args:
            refresh_token: Current refresh token
            device_info: Optional device information for new session
            ip_address: Optional IP address for security tracking
        
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        
        Raises:
            InvalidTokenError: If refresh token is invalid or revoked
            ExpiredSignatureError: If refresh token has expired
        
        Requirements: 3.4, 3.5, 3.6, 3.7
        """
        # Verify the refresh token
        payload = await self.verify_refresh_token(refresh_token)
        user_id = payload["sub"]
        
        # Revoke the old refresh token
        await self.revoke_refresh_token(refresh_token)
        
        # Generate new tokens
        new_access_token = self.create_access_token(user_id)
        new_refresh_token = await self.create_refresh_token(
            user_id,
            remember_me=False,  # Default to 7 days for refreshed tokens
            device_info=device_info,
            ip_address=ip_address
        )
        
        return new_access_token, new_refresh_token
    
    async def revoke_refresh_token(self, token: str) -> None:
        """
        Mark refresh token as revoked.
        
        Sets the revoked_at timestamp for the token, preventing future use.
        
        Args:
            token: Refresh token to revoke
        
        Requirements: 5.1, 5.2
        """
        token_hash = self._hash_token(token)
        refresh_token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        
        if refresh_token_record and refresh_token_record.revoked_at is None:
            refresh_token_record.revoked_at = datetime.utcnow()
            self.db.commit()
    
    async def revoke_all_user_tokens(
        self,
        user_id: int,
        except_token: Optional[str] = None
    ) -> None:
        """
        Revoke all refresh tokens for a user.
        
        Used for logout all sessions, password changes, or security events.
        Optionally preserves the current token.
        
        Args:
            user_id: User ID whose tokens should be revoked
            except_token: Optional token to preserve (current session)
        
        Requirements: 5.1, 5.2, 6.9, 17.7
        """
        query = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        )
        
        # If preserving current token, exclude it
        if except_token:
            except_token_hash = self._hash_token(except_token)
            query = query.filter(RefreshToken.token_hash != except_token_hash)
        
        # Revoke all matching tokens
        now = datetime.utcnow()
        for token_record in query.all():
            token_record.revoked_at = now
        
        self.db.commit()
    
    async def get_active_sessions(self, user_id: int) -> list:
        """
        Get all active (non-revoked, non-expired) sessions for a user.
        
        Args:
            user_id: User ID to query sessions for
        
        Returns:
            List of active RefreshToken records
        
        Requirements: 19.3
        """
        now = datetime.utcnow()
        active_sessions = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now
        ).order_by(RefreshToken.created_at.desc()).all()
        
        return active_sessions
    
    async def revoke_session_by_id(self, session_id: int, user_id: int) -> bool:
        """
        Revoke a specific session by its ID.
        
        Args:
            session_id: RefreshToken ID to revoke
            user_id: User ID for authorization check
        
        Returns:
            True if session was revoked, False if not found or unauthorized
        
        Requirements: 19.4
        """
        session = self.db.query(RefreshToken).filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).first()
        
        if session:
            session.revoked_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def _hash_token(self, token: str) -> str:
        """
        Hash token for secure storage.
        
        Uses SHA-256 to hash tokens before storing in database.
        
        Args:
            token: JWT token to hash
        
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(token.encode()).hexdigest()
