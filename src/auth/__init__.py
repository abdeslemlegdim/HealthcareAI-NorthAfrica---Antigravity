"""
Authentication and user management module.

This module provides comprehensive authentication and user management functionality
including JWT-based authentication, user registration/login, session management,
activity tracking, and HIPAA-compliant audit logging.

Components:
- models: SQLAlchemy models for users, tokens, activities, and audit logs
- services: Business logic services (UserService, TokenService, ActivityService, AuditService)
- router: FastAPI router with authentication endpoints
- middleware: Authentication dependencies for protected endpoints
- rate_limiter: Rate limiting for authentication endpoints
- utils: Password hashing and validation utilities

Requirements: Complete authentication system with admin features
"""

from src.auth.models import User, RefreshToken, UserActivity, AuditLog, Base
from src.auth.services import UserService, TokenService, ActivityService, AuditService
from src.auth.middleware import get_current_user, get_current_admin, get_current_user_optional
from src.auth.rate_limiter import RateLimiter
from src.auth.router import router as auth_router

__all__ = [
    # Models
    "User",
    "RefreshToken",
    "UserActivity",
    "AuditLog",
    "Base",
    # Services
    "UserService",
    "TokenService",
    "ActivityService",
    "AuditService",
    # Middleware
    "get_current_user",
    "get_current_admin",
    "get_current_user_optional",
    # Rate Limiter
    "RateLimiter",
    # Router
    "auth_router",
]

