"""
Security Middleware for FastAPI.

This module provides middleware for adding security headers and enforcing HTTPS.
Implements security best practices including HSTS, CSP, and other security headers.

Requirements: 10.1, 10.6, 10.7
"""

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Adds the following security headers:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains (if HTTPS)
    - Content-Security-Policy: default-src 'self'
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(), microphone=(), camera=()
    
    Requirements: 10.6, 10.7
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
        
        Returns:
            Response with security headers
        """
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add HSTS header if HTTPS is enabled
        if settings.HTTPS_ONLY:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Add CSP header (adjust based on your needs)
        # This is a basic CSP - you may need to customize it for your frontend
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust based on your needs
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS.
    
    Only active when HTTPS_ONLY is enabled in settings.
    
    Requirements: 10.1
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Redirect HTTP requests to HTTPS if HTTPS_ONLY is enabled.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
        
        Returns:
            Redirect response or normal response
        """
        # Skip HTTPS redirect if not enabled
        if not settings.HTTPS_ONLY:
            return await call_next(request)
        
        # Check if request is already HTTPS
        if request.url.scheme == "https":
            return await call_next(request)
        
        # Check for X-Forwarded-Proto header (common in reverse proxy setups)
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto == "https":
            return await call_next(request)
        
        # Redirect to HTTPS
        https_url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(https_url), status_code=301)


def get_cookie_settings() -> dict:
    """
    Get cookie settings based on configuration.
    
    Returns dictionary with cookie settings for secure, httponly, and samesite.
    
    Returns:
        dict: Cookie settings
    
    Requirements: 10.7
    """
    return {
        "secure": settings.SECURE_COOKIES,
        "httponly": settings.HTTPONLY_COOKIES,
        "samesite": settings.SAMESITE_COOKIES
    }
