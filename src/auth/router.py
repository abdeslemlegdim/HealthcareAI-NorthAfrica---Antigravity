"""
Authentication Router for FastAPI.

This module provides HTTP endpoints for user authentication including registration,
login, token refresh, logout, profile management, and dashboard access.

Requirements: 1.1-1.6, 2.1-2.8, 3.1-3.7, 5.1-5.4, 6.1-6.9, 7.1-7.10
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.auth.services.user_service import UserService
from src.auth.services.token_service import TokenService
from src.auth.services.activity_service import ActivityService
from src.auth.services.audit_service import AuditService
from src.auth.rate_limiter import RateLimiter
from src.utils.config import settings


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    """Token response for login and refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime]
    is_admin: bool = False
    is_active: bool = True
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# Router instance
router = APIRouter(tags=["authentication"])

# Global rate limiter instance (will be initialized in main.py)
rate_limiter: Optional[RateLimiter] = None


from src.database import get_db


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Client IP address
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """
    Extract user agent from request.
    
    Args:
        request: FastAPI request object
    
    Returns:
        User agent string
    """
    return request.headers.get("User-Agent", "unknown")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates a new user with email and password. Validates email format and
    password strength, applies rate limiting, and logs the event.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 10.4
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check rate limit
    if rate_limiter:
        allowed, retry_after = await rate_limiter.check_register_rate_limit(ip_address)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many registration attempts. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
    
    # Initialize services
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    try:
        # Create user
        user = user_service.create_user(data.email, data.password)
        
        # Log account creation
        await audit_service.log_account_creation(
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user
        
    except ValueError as e:
        # Handle validation errors (email exists, weak password, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log unexpected errors
        print(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and generate tokens.
    
    Verifies credentials, generates access and refresh tokens, applies rate
    limiting, and logs the event.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 10.2
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check rate limit
    if rate_limiter:
        allowed, retry_after = await rate_limiter.check_login_rate_limit(data.email)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
    
    # Initialize services
    user_service = UserService(db)
    token_service = TokenService(db, settings)
    audit_service = AuditService(db)
    
    # Verify credentials
    user = user_service.get_user_by_email(data.email)
    
    if not user:
        # Log failed attempt
        await audit_service.log_login_failed(
            email=data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason="user_not_found"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is active
    if not user.is_active:
        await audit_service.log_login_failed(
            email=data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason="account_disabled"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Verify password
    if not user_service.verify_password(data.password, user.password_hash):
        await audit_service.log_login_failed(
            email=data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason="invalid_password"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate tokens
    access_token = token_service.create_access_token(user.id)
    refresh_token = await token_service.create_refresh_token(
        user.id,
        remember_me=data.remember_me,
        device_info=user_agent,
        ip_address=ip_address
    )
    
    # Update last activity
    user_service.update_last_activity(user.id)
    
    # Log successful login
    await audit_service.log_login_success(
        user_id=user.id,
        email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        remember_me=data.remember_me
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access and refresh tokens.
    
    Validates refresh token, generates new tokens, invalidates old refresh token,
    and applies rate limiting.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 10.5
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Initialize services
    token_service = TokenService(db, settings)
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    try:
        # Verify refresh token and get user_id
        payload = await token_service.verify_refresh_token(refresh_token)
        user_id = payload["sub"]
        
        # Check rate limit
        if rate_limiter:
            allowed, retry_after = await rate_limiter.check_refresh_rate_limit(user_id)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many refresh attempts. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
        
        # Get user for logging
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Generate new tokens
        new_access_token, new_refresh_token = await token_service.refresh_tokens(
            refresh_token,
            device_info=user_agent,
            ip_address=ip_address
        )
        
        # Log token refresh
        await audit_service.log_token_refresh(
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        error_detail = str(e)
        if "expired" in error_detail.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again."
            )
        elif "revoked" in error_detail.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked. Please log in again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Logout user and revoke refresh token.
    
    Invalidates the refresh token to terminate the session.
    
    Requirements: 5.1, 5.2, 5.3, 5.4
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Initialize services
    token_service = TokenService(db, settings)
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    try:
        # Verify token to get user_id before revoking
        payload = await token_service.verify_refresh_token(refresh_token)
        user_id = payload["sub"]
        
        # Get user for logging
        user = user_service.get_user_by_id(user_id)
        
        # Revoke refresh token
        await token_service.revoke_refresh_token(refresh_token)
        
        # Log logout
        if user:
            await audit_service.log_logout(
                user_id=user.id,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                logout_type="user_initiated"
            )
        
        return MessageResponse(message="Successfully logged out")
        
    except Exception as e:
        # Even if token is invalid, return success (idempotent operation)
        return MessageResponse(message="Successfully logged out")



class UpdateEmailRequest(BaseModel):
    """Update email request."""
    new_email: EmailStr


class UpdatePasswordRequest(BaseModel):
    """Update password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


# Import authentication dependencies from middleware
from src.auth.middleware import get_current_user, get_current_admin


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user = Depends(get_current_user)
):
    """
    Get current user profile.
    
    Returns user profile information excluding password hash.
    
    Requirements: 6.1, 6.2, 6.3
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: Request,
    data: UpdateEmailRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user email address.
    
    Validates new email format and ensures it's not already registered.
    
    Requirements: 6.4, 6.5, 6.6
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Initialize services
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    try:
        # Update email
        updated_user = user_service.update_user_email(
            current_user.id,
            data.new_email
        )
        
        # Log email change
        await audit_service.log_email_change(
            user_id=current_user.id,
            old_email=current_user.email,
            new_email=data.new_email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return updated_user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    request: Request,
    data: UpdatePasswordRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    Verifies current password, validates new password strength, and revokes
    all existing sessions for security.
    
    Requirements: 6.7, 6.8, 6.9
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Initialize services
    user_service = UserService(db)
    token_service = TokenService(db, settings)
    audit_service = AuditService(db)
    
    # Verify current password
    if not user_service.verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    try:
        # Update password
        user_service.update_user_password(current_user.id, data.new_password)
        
        # Revoke all refresh tokens (force re-login on all devices)
        await token_service.revoke_all_user_tokens(current_user.id)
        
        # Log password change
        await audit_service.log_password_change(
            user_id=current_user.id,
            email=current_user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            initiated_by="user"
        )
        
        return MessageResponse(
            message="Password changed successfully. Please log in again on all devices."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



class DashboardResponse(BaseModel):
    """Enhanced dashboard response with statistics and insights."""
    user: UserResponse
    statistics: dict
    recent_activities: list
    usage_trends: dict
    health_insights: dict
    quick_links: list


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get enhanced user dashboard with statistics and insights.
    
    Returns comprehensive dashboard data including:
    - User profile
    - Usage statistics (total counts, weekly/monthly activity)
    - Recent activities (last 10)
    - Usage trends (daily/weekly/monthly aggregations)
    - Health insights (engagement score, recommendations)
    - Quick access links (personalized based on usage)
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10
    """
    # Initialize services
    activity_service = ActivityService(db)
    
    # Get all dashboard data
    statistics = await activity_service.get_user_statistics(current_user.id)
    recent_activities = await activity_service.get_recent_activities(current_user.id, limit=10)
    usage_trends = await activity_service.get_usage_trends(current_user.id, days=30)
    health_insights = await activity_service.calculate_health_insights(current_user.id)
    quick_links = await activity_service.generate_quick_links(current_user.id)
    
    return DashboardResponse(
        user=UserResponse.from_orm(current_user),
        statistics=statistics,
        recent_activities=recent_activities,
        usage_trends=usage_trends,
        health_insights=health_insights,
        quick_links=quick_links
    )



class SessionInfo(BaseModel):
    """Session information response."""
    id: int
    device_info: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_used_at: datetime
    is_current: bool = False
    
    class Config:
        from_attributes = True


@router.get("/sessions", response_model=list[SessionInfo])
async def get_sessions(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for current user.
    
    Returns list of active sessions with device info, IP, and timestamps.
    
    Requirements: 19.1, 19.2, 19.3
    """
    # Initialize services
    token_service = TokenService(db, settings)
    
    # Get active sessions
    sessions = await token_service.get_active_sessions(current_user.id)
    
    # Get current request IP for comparison
    current_ip = get_client_ip(request)
    
    # Convert to response format
    session_list = []
    for session in sessions:
        # Mark current session
        is_current = session.ip_address == current_ip
        
        # Calculate last_used_at (use created_at if not available)
        last_used = session.created_at
        
        session_list.append(SessionInfo(
            id=session.id,
            device_info=session.device_info,
            ip_address=session.ip_address,
            created_at=session.created_at,
            last_used_at=last_used,
            is_current=is_current
        ))
    
    return session_list


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session.
    
    Invalidates the refresh token for the specified session.
    
    Requirements: 19.4
    """
    # Initialize services
    token_service = TokenService(db, settings)
    
    # Revoke session
    success = await token_service.revoke_session_by_id(session_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked"
        )
    
    return MessageResponse(message="Session revoked successfully")


@router.delete("/sessions", response_model=MessageResponse)
async def revoke_all_other_sessions(
    request: Request,
    refresh_token: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke all other sessions except current.
    
    Invalidates all refresh tokens for the user except the current one.
    
    Requirements: 19.5
    """
    # Initialize services
    token_service = TokenService(db, settings)
    
    # Revoke all tokens except current
    await token_service.revoke_all_user_tokens(
        current_user.id,
        except_token=refresh_token
    )
    
    return MessageResponse(message="All other sessions revoked successfully")



class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8)


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    
    Generates a password reset token and stores it in the database.
    Returns success regardless of whether email exists (security best practice).
    
    Requirements: 17.1, 17.2, 17.3
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Initialize services
    audit_service = AuditService(db)
    
    # Log password reset request
    await audit_service.log_password_reset_request(
        email=data.email,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # TODO: Implement actual password reset token generation and email sending
    # For now, just return success message
    # This will be implemented when email functionality is available
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent."
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    request: Request,
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset with token.
    
    Verifies reset token, updates password, and revokes all sessions.
    
    Requirements: 17.4, 17.5, 17.6, 17.7, 17.8
    """
    # Get client info
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Initialize services
    user_service = UserService(db)
    token_service = TokenService(db, settings)
    audit_service = AuditService(db)
    
    # TODO: Implement actual password reset token verification
    # For now, raise not implemented error
    # This will be implemented when password reset token storage is added
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset confirmation not yet implemented. Token storage needed."
    )
