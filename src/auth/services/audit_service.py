"""
Audit Service for HIPAA-compliant audit logging.

This module provides comprehensive audit logging for all authentication events,
user actions, and admin operations to meet HIPAA compliance requirements.

Requirements: 10.9, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 21.10
"""

from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from src.auth.models import AuditLog


class AuditService:
    """
    Service for comprehensive audit logging.
    
    Records all authentication events, user actions, and admin operations
    for security monitoring and HIPAA compliance.
    """
    
    # Event type constants
    EVENT_LOGIN_SUCCESS = "login_success"
    EVENT_LOGIN_FAILED = "login_failed"
    EVENT_PASSWORD_CHANGE = "password_change"
    EVENT_ACCOUNT_CREATION = "account_creation"
    EVENT_TOKEN_REFRESH = "token_refresh"
    EVENT_LOGOUT = "logout"
    EVENT_ADMIN_ACTION = "admin_action"
    EVENT_PASSWORD_RESET_REQUEST = "password_reset_request"
    EVENT_PASSWORD_RESET_CONFIRM = "password_reset_confirm"
    EVENT_EMAIL_CHANGE = "email_change"
    EVENT_ACCOUNT_DISABLE = "account_disable"
    EVENT_ACCOUNT_ENABLE = "account_enable"
    EVENT_ACCOUNT_DELETE = "account_delete"
    
    def __init__(self, db: Session):
        """
        Initialize AuditService.
        
        Args:
            db: Database session for audit log storage
        """
        self.db = db
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an authentication or security event.
        
        Records comprehensive event information for audit trail and compliance.
        
        Args:
            event_type: Type of event (use EVENT_* constants)
            user_id: Optional user ID associated with event
            email: Optional email address associated with event
            ip_address: Optional IP address of request
            user_agent: Optional user agent string
            metadata: Optional additional event metadata
        
        Requirements: 10.9, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 21.10
        """
        audit_log = AuditLog(
            event_type=event_type,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            metadata_=metadata
        )
        
        self.db.add(audit_log)
        self.db.commit()
    
    async def log_login_success(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False
    ) -> None:
        """
        Log successful login attempt.
        
        Args:
            user_id: User ID that logged in
            email: Email address used for login
            ip_address: IP address of request
            user_agent: User agent string
            remember_me: Whether "remember me" was selected
        
        Requirements: 18.1
        """
        await self.log_event(
            event_type=self.EVENT_LOGIN_SUCCESS,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"remember_me": remember_me}
        )
    
    async def log_login_failed(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: str = "invalid_credentials"
    ) -> None:
        """
        Log failed login attempt.
        
        Args:
            email: Email address used for login attempt
            ip_address: IP address of request
            user_agent: User agent string
            failure_reason: Reason for failure (e.g., "invalid_credentials", "account_disabled")
        
        Requirements: 18.2
        """
        await self.log_event(
            event_type=self.EVENT_LOGIN_FAILED,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"failure_reason": failure_reason}
        )
    
    async def log_password_change(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        initiated_by: str = "user"
    ) -> None:
        """
        Log password change event.
        
        Args:
            user_id: User ID whose password was changed
            email: Email address of user
            ip_address: IP address of request
            user_agent: User agent string
            initiated_by: Who initiated the change ("user", "admin", "reset")
        
        Requirements: 18.3
        """
        await self.log_event(
            event_type=self.EVENT_PASSWORD_CHANGE,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"initiated_by": initiated_by}
        )
    
    async def log_account_creation(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log account creation event.
        
        Args:
            user_id: New user ID
            email: Email address of new account
            ip_address: IP address of request
            user_agent: User agent string
        
        Requirements: 18.4
        """
        await self.log_event(
            event_type=self.EVENT_ACCOUNT_CREATION,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_token_refresh(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log token refresh event.
        
        Args:
            user_id: User ID refreshing token
            email: Email address of user
            ip_address: IP address of request
            user_agent: User agent string
        
        Requirements: 18.5
        """
        await self.log_event(
            event_type=self.EVENT_TOKEN_REFRESH,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_logout(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        logout_type: str = "user_initiated"
    ) -> None:
        """
        Log logout event.
        
        Args:
            user_id: User ID logging out
            email: Email address of user
            ip_address: IP address of request
            user_agent: User agent string
            logout_type: Type of logout ("user_initiated", "session_expired", "admin_forced")
        
        Requirements: 18.6
        """
        await self.log_event(
            event_type=self.EVENT_LOGOUT,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"logout_type": logout_type}
        )
    
    async def log_admin_action(
        self,
        admin_user_id: int,
        admin_email: str,
        action: str,
        target_user_id: Optional[int] = None,
        target_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log admin action event.
        
        Args:
            admin_user_id: Admin user ID performing action
            admin_email: Admin email address
            action: Action performed (e.g., "disable_user", "enable_user", "delete_user")
            target_user_id: Optional target user ID
            target_email: Optional target user email
            ip_address: IP address of request
            user_agent: User agent string
            details: Optional additional action details
        
        Requirements: 21.10
        """
        metadata = {
            "action": action,
            "target_user_id": target_user_id,
            "target_email": target_email
        }
        
        if details:
            metadata.update(details)
        
        await self.log_event(
            event_type=self.EVENT_ADMIN_ACTION,
            user_id=admin_user_id,
            email=admin_email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
    
    async def log_password_reset_request(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log password reset request event.
        
        Args:
            email: Email address requesting reset
            ip_address: IP address of request
            user_agent: User agent string
        """
        await self.log_event(
            event_type=self.EVENT_PASSWORD_RESET_REQUEST,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_password_reset_confirm(
        self,
        user_id: int,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log password reset confirmation event.
        
        Args:
            user_id: User ID whose password was reset
            email: Email address of user
            ip_address: IP address of request
            user_agent: User agent string
        """
        await self.log_event(
            event_type=self.EVENT_PASSWORD_RESET_CONFIRM,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_email_change(
        self,
        user_id: int,
        old_email: str,
        new_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log email change event.
        
        Args:
            user_id: User ID whose email was changed
            old_email: Previous email address
            new_email: New email address
            ip_address: IP address of request
            user_agent: User agent string
        """
        await self.log_event(
            event_type=self.EVENT_EMAIL_CHANGE,
            user_id=user_id,
            email=new_email,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"old_email": old_email, "new_email": new_email}
        )
    
    async def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        Get audit logs for a specific user.
        
        Args:
            user_id: User ID to retrieve logs for
            limit: Maximum number of logs to return
            offset: Number of logs to skip
        
        Returns:
            List of AuditLog records
        """
        logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
        
        return logs
    
    async def get_recent_audit_logs(
        self,
        limit: int = 100,
        event_type: Optional[str] = None
    ) -> list:
        """
        Get recent audit logs across all users.
        
        Args:
            limit: Maximum number of logs to return
            event_type: Optional filter by event type
        
        Returns:
            List of AuditLog records
        """
        query = self.db.query(AuditLog)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return logs
    
    async def get_failed_login_attempts(
        self,
        email: Optional[str] = None,
        hours: int = 24
    ) -> list:
        """
        Get failed login attempts.
        
        Args:
            email: Optional filter by email address
            hours: Number of hours to look back
        
        Returns:
            List of failed login AuditLog records
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.event_type == self.EVENT_LOGIN_FAILED,
            AuditLog.timestamp >= since
        )
        
        if email:
            query = query.filter(AuditLog.email == email)
        
        logs = query.order_by(AuditLog.timestamp.desc()).all()
        
        return logs


# Import timedelta for get_failed_login_attempts
from datetime import timedelta
