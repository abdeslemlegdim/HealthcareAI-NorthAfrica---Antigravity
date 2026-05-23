"""
Password hashing and validation utilities.

This module provides secure password hashing using bcrypt and validation
functions for password strength and email format.

Requirements: 1.1, 1.2, 1.4, 6.7, 6.8, 17.5, 17.6
"""

import re
from typing import Tuple
import bcrypt
from email_validator import validate_email, EmailNotValidError


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The bcrypt hashed password as a string
        
    Raises:
        ValueError: If password is empty or None
        
    Requirements: 1.4, 6.8, 17.6
    
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> isinstance(hashed, str)
        True
        >>> len(hashed) > 0
        True
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Generate salt with cost factor 12 and hash the password
    salt = bcrypt.gensalt(rounds=12)
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
        
    Requirements: 2.2
    
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> verify_password("MySecurePass123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, AttributeError):
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    
    Args:
        password: The password to validate
        
    Returns:
        A tuple of (is_valid, error_message)
        - is_valid: True if password meets all requirements, False otherwise
        - error_message: Empty string if valid, otherwise describes the issue
        
    Requirements: 1.2, 6.7, 17.5
    
    Example:
        >>> validate_password_strength("MySecurePass123!")
        (True, '')
        >>> validate_password_strength("weak")
        (False, 'Password must be at least 8 characters long')
    """
    if not password:
        return False, "Password cannot be empty"
    
    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one number
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check for at least one special character
    # Special characters include: !@#$%^&*()_+-=[]{}|;:,.<>?/~`
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]', password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def validate_email_format(email: str) -> Tuple[bool, str]:
    """
    Validate email format using RFC 5322 standards.
    
    Uses the email-validator library to perform comprehensive email validation
    including syntax checking, domain validation, and deliverability checks.
    
    Args:
        email: The email address to validate
        
    Returns:
        A tuple of (is_valid, normalized_email_or_error)
        - is_valid: True if email is valid, False otherwise
        - normalized_email_or_error: Normalized email if valid, error message if invalid
        
    Requirements: 1.1
    
    Example:
        >>> validate_email_format("user@example.com")
        (True, 'user@example.com')
        >>> validate_email_format("invalid-email")
        (False, 'The email address is not valid...')
    """
    if not email:
        return False, "Email cannot be empty"
    
    try:
        # Validate and normalize the email address
        validated = validate_email(email, check_deliverability=False)
        # Return the normalized email address
        return True, validated.normalized
    except EmailNotValidError as e:
        # Return the validation error message
        return False, str(e)
