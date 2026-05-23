"""
Admin module for Healthcare AI Assistant.

This module provides admin-specific functionality including user management,
system monitoring, and analytics.

Components:
- router: FastAPI router with admin endpoints

Requirements: Admin user management and system monitoring
"""

from src.admin.router import router as admin_router

__all__ = ["admin_router"]
