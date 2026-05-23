"""
SQLAlchemy models for authentication and user management.

This module defines the database models for the authentication system including:
- User: User accounts with authentication credentials
- RefreshToken: JWT refresh tokens for session management
- UserActivity: User activity tracking for usage statistics
- AuditLog: Comprehensive audit logging for HIPAA compliance

Requirements: 9.1, 9.2, 9.3, 21.1
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    JSON,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """
    User model for authentication and account management.
    
    Stores user credentials, account status, and timestamps.
    Supports admin privileges and soft deletes.
    
    Requirements: 9.1, 21.1
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Admin and status fields
    is_admin = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    last_activity_at = Column(DateTime, nullable=True)
    
    # Soft delete support
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    activities = relationship(
        "UserActivity",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_admin={self.is_admin})>"


class RefreshToken(Base):
    """
    Refresh token model for session management.
    
    Stores JWT refresh tokens with expiration and revocation support.
    Tracks device information and IP addresses for security.
    
    Requirements: 9.2
    """
    __tablename__ = "refresh_tokens"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Token data
    token_hash = Column(String(255), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Session metadata
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class UserActivity(Base):
    """
    User activity model for tracking usage statistics.
    
    Records user interactions with the system including chat queries,
    image analyses, and vital sign measurements.
    
    Requirements: 9.3
    """
    __tablename__ = "user_activities"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Activity data
    activity_type = Column(String(50), nullable=False, index=True)  # 'chat', 'imaging', 'vitals'
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type='{self.activity_type}')>"


class AuditLog(Base):
    """
    Audit log model for HIPAA compliance and security monitoring.
    
    Records all authentication events, user actions, and admin operations
    for compliance and security auditing purposes.
    
    Requirements: 18.7, 21.10
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Event data
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    email = Column(String(255), nullable=True)
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', timestamp={self.timestamp})>"


# Create composite indexes for common query patterns
Index('idx_user_activities_user_timestamp', UserActivity.user_id, UserActivity.timestamp)
Index('idx_audit_logs_user_timestamp', AuditLog.user_id, AuditLog.timestamp)
Index('idx_audit_logs_event_timestamp', AuditLog.event_type, AuditLog.timestamp)
