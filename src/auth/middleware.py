"""
Authentication Middleware for FastAPI.

This module provides FastAPI dependencies for token validation and user authentication.
Implements get_current_user, get_current_user_optional, and get_current_admin dependencies.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 21.11
"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.auth.services.token_service import TokenService
from src.auth.services.user_service import UserService
from src.auth.models import User
from src.utils.config import settings
from src.database import get_db


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT access token and returns current user.
    
    Extracts token from Authorization header, validates it, and retrieves
    the user from the database.
    
    When ENABLE_AUTHENTICATION is False, this function returns None to allow
    backward compatibility with systems that don't require authentication.
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
    
    Returns:
        User object for authenticated user
    
    Raises:
        HTTPException(401): If token is missing, invalid, or expired
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 16.8, 20.5, 20.6
    """
    # Backward compatibility: if authentication is disabled, return None
    if not settings.ENABLE_AUTHENTICATION:
        return None
    
    # Check if authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    
    # Initialize services
    token_service = TokenService(db, settings)
    user_service = UserService(db)
    
    try:
        # Verify and decode token
        payload = token_service.verify_access_token(token)
        user_id = payload["sub"]
        
        # Get user from database
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Check if user is soft-deleted
        if user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deleted"
            )
        
        return user
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer", "X-Token-Error": "token_expired"}
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        # Log unexpected errors
        print(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns user if token valid, None otherwise.
    
    Used for backward compatibility mode where endpoints can work with or
    without authentication.
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
    
    Returns:
        User object if authenticated, None otherwise
    
    Requirements: 16.8, 20.6
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        # If authentication fails, return None instead of raising error
        return None


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Validates that current user has admin role.
    
    Checks if the authenticated user has admin privileges.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User object if user is admin
    
    Raises:
        HTTPException(403): If user is not an admin
    
    Requirements: 21.11
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. You do not have permission to access this resource."
        )
    
    return current_user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Validates that current user is active.
    
    Additional check to ensure user account is active and not deleted.
    This is already checked in get_current_user, but provided as a
    separate dependency for clarity.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User object if user is active
    
    Raises:
        HTTPException(403): If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted"
        )
    
    return current_user


def require_auth(enabled: bool = True):
    """
    Conditional authentication dependency factory.
    
    Returns appropriate authentication dependency based on configuration.
    Used for backward compatibility mode.
    
    Args:
        enabled: Whether authentication is required
    
    Returns:
        Authentication dependency function
    
    Requirements: 16.8, 20.5, 20.6
    """
    if enabled:
        return get_current_user
    else:
        return get_current_user_optional
