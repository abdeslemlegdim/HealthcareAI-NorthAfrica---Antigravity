"""
User service for user management operations.

This module provides business logic for user account management including
user creation, retrieval, updates, and admin operations.

Requirements: 1.5, 2.1, 2.2, 6.1, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 21.6, 21.7, 21.8
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.auth.models import User, RefreshToken
from src.auth.utils.password import (
    hash_password,
    verify_password as verify_password_util,
    validate_email_format,
    validate_password_strength
)


class UserService:
    """
    Service class for user management operations.
    
    Provides methods for creating, retrieving, and updating user accounts,
    as well as admin operations for user management.
    """
    
    def __init__(self, db: Session):
        """
        Initialize UserService with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_user(self, email: str, password: str, is_admin: bool = False) -> User:
        """
        Create a new user with hashed password.
        
        Validates email format and password strength before creating the user.
        Hashes the password using bcrypt with cost factor 12.
        
        Args:
            email: User's email address
            password: Plain text password
            is_admin: Whether the user should have admin privileges (default: False)
            
        Returns:
            The created User object
            
        Raises:
            ValueError: If email format is invalid, password is weak, or email already exists
            
        Requirements: 1.1, 1.2, 1.4, 1.5
        
        Example:
            >>> service = UserService(db)
            >>> user = service.create_user("user@example.com", "SecurePass123!")
            >>> user.email
            'user@example.com'
        """
        # Validate email format
        is_valid_email, normalized_email_or_error = validate_email_format(email)
        if not is_valid_email:
            raise ValueError(f"Invalid email format: {normalized_email_or_error}")
        
        # Validate password strength
        is_valid_password, password_error = validate_password_strength(password)
        if not is_valid_password:
            raise ValueError(f"Invalid password: {password_error}")
        
        # Check if email already exists
        existing_user = self.get_user_by_email(normalized_email_or_error)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Create user record
        user = User(
            email=normalized_email_or_error,
            password_hash=password_hash,
            is_admin=is_admin,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Email already registered")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
            
        Requirements: 2.1
        
        Example:
            >>> service = UserService(db)
            >>> user = service.get_user_by_email("user@example.com")
            >>> user.email if user else None
            'user@example.com'
        """
        return self.db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User object if found, None otherwise
            
        Requirements: 6.1
        
        Example:
            >>> service = UserService(db)
            >>> user = service.get_user_by_id(1)
            >>> user.id if user else None
            1
        """
        return self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a bcrypt hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
            
        Requirements: 2.2
        
        Example:
            >>> service = UserService(db)
            >>> hashed = hash_password("SecurePass123!")
            >>> service.verify_password("SecurePass123!", hashed)
            True
            >>> service.verify_password("WrongPassword", hashed)
            False
        """
        return verify_password_util(plain_password, hashed_password)
    
    def update_user_email(self, user_id: int, new_email: str) -> User:
        """
        Update a user's email address.
        
        Validates the new email format and ensures it's not already registered.
        
        Args:
            user_id: User's ID
            new_email: New email address
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found, email format invalid, or email already exists
            
        Requirements: 6.4, 6.5, 6.6
        
        Example:
            >>> service = UserService(db)
            >>> user = service.update_user_email(1, "newemail@example.com")
            >>> user.email
            'newemail@example.com'
        """
        # Get user
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Validate email format
        is_valid_email, normalized_email_or_error = validate_email_format(new_email)
        if not is_valid_email:
            raise ValueError(f"Invalid email format: {normalized_email_or_error}")
        
        # Check if new email already exists (and it's not the same user)
        existing_user = self.get_user_by_email(normalized_email_or_error)
        if existing_user and existing_user.id != user_id:
            raise ValueError("Email already registered")
        
        # Update email
        user.email = normalized_email_or_error
        user.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Email already registered")
    
    def update_user_password(self, user_id: int, new_password: str) -> None:
        """
        Update a user's password and invalidate all existing refresh tokens.
        
        Validates password strength, hashes the new password, and revokes all
        active sessions for security.
        
        Args:
            user_id: User's ID
            new_password: New plain text password
            
        Raises:
            ValueError: If user not found or password is weak
            
        Requirements: 6.7, 6.8, 6.9
        
        Example:
            >>> service = UserService(db)
            >>> service.update_user_password(1, "NewSecurePass123!")
        """
        # Get user
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Validate password strength
        is_valid_password, password_error = validate_password_strength(new_password)
        if not is_valid_password:
            raise ValueError(f"Invalid password: {password_error}")
        
        # Hash the new password
        password_hash = hash_password(new_password)
        
        # Update password
        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()
        
        # Invalidate all existing refresh tokens for security
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).update({
            "revoked_at": datetime.utcnow()
        })
        
        self.db.commit()
    
    def update_last_activity(self, user_id: int) -> None:
        """
        Update a user's last activity timestamp.
        
        Args:
            user_id: User's ID
            
        Requirements: 8.4
        
        Example:
            >>> service = UserService(db)
            >>> service.update_last_activity(1)
        """
        user = self.get_user_by_id(user_id)
        if user:
            user.last_activity_at = datetime.utcnow()
            self.db.commit()
    
    def disable_user(self, user_id: int) -> User:
        """
        Disable a user account and revoke all active sessions.
        
        Admin operation to disable a user account. Sets is_active to False
        and revokes all refresh tokens.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found
            
        Requirements: 21.6
        
        Example:
            >>> service = UserService(db)
            >>> user = service.disable_user(1)
            >>> user.is_active
            False
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Disable user account
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Revoke all active sessions
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).update({
            "revoked_at": datetime.utcnow()
        })
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def enable_user(self, user_id: int) -> User:
        """
        Enable a previously disabled user account.
        
        Admin operation to re-enable a user account. Sets is_active to True.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found
            
        Requirements: 21.7
        
        Example:
            >>> service = UserService(db)
            >>> user = service.enable_user(1)
            >>> user.is_active
            True
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Enable user account
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def soft_delete_user(self, user_id: int) -> User:
        """
        Soft delete a user account and revoke all active sessions.
        
        Admin operation to soft delete a user account. Sets deleted_at timestamp
        and revokes all refresh tokens. The user record is retained for audit purposes.
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found
            
        Requirements: 21.8
        
        Example:
            >>> service = UserService(db)
            >>> user = service.soft_delete_user(1)
            >>> user.deleted_at is not None
            True
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Soft delete user account
        user.deleted_at = datetime.utcnow()
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Revoke all active sessions
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        ).update({
            "revoked_at": datetime.utcnow()
        })
        
        self.db.commit()
        self.db.refresh(user)
        return user
