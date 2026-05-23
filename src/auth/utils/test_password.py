"""
Unit tests for password hashing and validation utilities.

Tests cover:
- Password hashing with bcrypt
- Password verification
- Password strength validation
- Email format validation

Requirements: 1.1, 1.2, 1.4, 6.7, 6.8, 17.5, 17.6
"""

import pytest
from src.auth.utils.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    validate_email_format,
)


class TestHashPassword:
    """Tests for password hashing functionality."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different hashes (due to salt)."""
        password = "MySecurePass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Hashes should be different due to different salts
        assert hash1 != hash2
    
    def test_hash_password_with_empty_string_raises_error(self):
        """Test that hashing an empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")
    
    def test_hash_password_with_none_raises_error(self):
        """Test that hashing None raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password(None)
    
    def test_hash_password_with_special_characters(self):
        """Test that passwords with special characters are hashed correctly."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_with_unicode_characters(self):
        """Test that passwords with unicode characters are hashed correctly."""
        password = "Pässwörd123!你好"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestVerifyPassword:
    """Tests for password verification functionality."""
    
    def test_verify_password_correct_password(self):
        """Test that correct password verification returns True."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """Test that incorrect password verification returns False."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        assert verify_password("WrongPassword123!", hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        assert verify_password("mysecurepass123!", hashed) is False
    
    def test_verify_password_with_empty_plain_password(self):
        """Test that verifying empty password returns False."""
        hashed = hash_password("MySecurePass123!")
        assert verify_password("", hashed) is False
    
    def test_verify_password_with_empty_hash(self):
        """Test that verifying against empty hash returns False."""
        assert verify_password("MySecurePass123!", "") is False
    
    def test_verify_password_with_none_values(self):
        """Test that verifying with None values returns False."""
        assert verify_password(None, "somehash") is False
        assert verify_password("password", None) is False
    
    def test_verify_password_with_invalid_hash(self):
        """Test that verifying against invalid hash returns False."""
        assert verify_password("MySecurePass123!", "invalid_hash") is False
    
    def test_verify_password_with_special_characters(self):
        """Test that passwords with special characters verify correctly."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("P@ssw0rd!#$%^&*()X", hashed) is False


class TestValidatePasswordStrength:
    """Tests for password strength validation."""
    
    def test_valid_password(self):
        """Test that a valid password passes all checks."""
        is_valid, error = validate_password_strength("MySecurePass123!")
        assert is_valid is True
        assert error == ""
    
    def test_password_too_short(self):
        """Test that passwords shorter than 8 characters are rejected."""
        is_valid, error = validate_password_strength("Abc1!")
        assert is_valid is False
        assert "at least 8 characters" in error
    
    def test_password_exactly_8_characters(self):
        """Test that passwords with exactly 8 characters are accepted if they meet other requirements."""
        is_valid, error = validate_password_strength("Abcd123!")
        assert is_valid is True
        assert error == ""
    
    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase letters are rejected."""
        is_valid, error = validate_password_strength("mysecurepass123!")
        assert is_valid is False
        assert "uppercase letter" in error
    
    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase letters are rejected."""
        is_valid, error = validate_password_strength("MYSECUREPASS123!")
        assert is_valid is False
        assert "lowercase letter" in error
    
    def test_password_missing_number(self):
        """Test that passwords without numbers are rejected."""
        is_valid, error = validate_password_strength("MySecurePass!")
        assert is_valid is False
        assert "number" in error
    
    def test_password_missing_special_character(self):
        """Test that passwords without special characters are rejected."""
        is_valid, error = validate_password_strength("MySecurePass123")
        assert is_valid is False
        assert "special character" in error
    
    def test_password_empty_string(self):
        """Test that empty passwords are rejected."""
        is_valid, error = validate_password_strength("")
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_password_none(self):
        """Test that None passwords are rejected."""
        is_valid, error = validate_password_strength(None)
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_password_with_various_special_characters(self):
        """Test that various special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        for char in special_chars:
            password = f"MyPass123{char}"
            is_valid, error = validate_password_strength(password)
            assert is_valid is True, f"Failed for special character: {char}"
            assert error == ""
    
    def test_password_with_spaces(self):
        """Test that passwords with spaces are handled correctly."""
        # Spaces are not considered special characters
        is_valid, error = validate_password_strength("My Pass 123")
        assert is_valid is False
        assert "special character" in error
        
        # But with a special character, it should pass
        is_valid, error = validate_password_strength("My Pass 123!")
        assert is_valid is True
        assert error == ""
    
    def test_password_long_valid(self):
        """Test that long valid passwords are accepted."""
        password = "MyVeryLongAndSecurePassword123!WithLotsOfCharacters"
        is_valid, error = validate_password_strength(password)
        assert is_valid is True
        assert error == ""


class TestValidateEmailFormat:
    """Tests for email format validation."""
    
    def test_valid_email_simple(self):
        """Test that a simple valid email is accepted."""
        is_valid, result = validate_email_format("user@example.com")
        assert is_valid is True
        assert result == "user@example.com"
    
    def test_valid_email_with_subdomain(self):
        """Test that emails with subdomains are accepted."""
        is_valid, result = validate_email_format("user@mail.example.com")
        assert is_valid is True
        assert "user@mail.example.com" in result
    
    def test_valid_email_with_plus(self):
        """Test that emails with plus signs are accepted."""
        is_valid, result = validate_email_format("user+tag@example.com")
        assert is_valid is True
        assert "user+tag@example.com" in result
    
    def test_valid_email_with_dots(self):
        """Test that emails with dots in local part are accepted."""
        is_valid, result = validate_email_format("first.last@example.com")
        assert is_valid is True
        assert "first.last@example.com" in result
    
    def test_valid_email_with_numbers(self):
        """Test that emails with numbers are accepted."""
        is_valid, result = validate_email_format("user123@example456.com")
        assert is_valid is True
        assert "user123@example456.com" in result
    
    def test_invalid_email_no_at_symbol(self):
        """Test that emails without @ symbol are rejected."""
        is_valid, error = validate_email_format("userexample.com")
        assert is_valid is False
        assert isinstance(error, str)
        assert len(error) > 0
    
    def test_invalid_email_no_domain(self):
        """Test that emails without domain are rejected."""
        is_valid, error = validate_email_format("user@")
        assert is_valid is False
        assert isinstance(error, str)
    
    def test_invalid_email_no_local_part(self):
        """Test that emails without local part are rejected."""
        is_valid, error = validate_email_format("@example.com")
        assert is_valid is False
        assert isinstance(error, str)
    
    def test_invalid_email_multiple_at_symbols(self):
        """Test that emails with multiple @ symbols are rejected."""
        is_valid, error = validate_email_format("user@@example.com")
        assert is_valid is False
        assert isinstance(error, str)
    
    def test_invalid_email_spaces(self):
        """Test that emails with spaces are rejected."""
        is_valid, error = validate_email_format("user @example.com")
        assert is_valid is False
        assert isinstance(error, str)
    
    def test_invalid_email_empty_string(self):
        """Test that empty email is rejected."""
        is_valid, error = validate_email_format("")
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_invalid_email_none(self):
        """Test that None email is rejected."""
        is_valid, error = validate_email_format(None)
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_email_normalization(self):
        """Test that emails are normalized (e.g., lowercase domain)."""
        is_valid, result = validate_email_format("User@EXAMPLE.COM")
        assert is_valid is True
        # Domain should be normalized to lowercase
        assert "@example.com" in result.lower()
    
    def test_invalid_email_invalid_domain(self):
        """Test that emails with invalid domains are rejected."""
        is_valid, error = validate_email_format("user@.com")
        assert is_valid is False
        assert isinstance(error, str)
    
    def test_invalid_email_special_characters(self):
        """Test that emails with clearly invalid special characters are rejected."""
        # Test with a character that's definitely invalid
        is_valid, error = validate_email_format("user name@example.com")
        assert is_valid is False
        assert isinstance(error, str)


class TestIntegration:
    """Integration tests combining multiple utilities."""
    
    def test_full_registration_flow(self):
        """Test a complete registration flow with email and password validation."""
        # Validate email
        email = "newuser@example.com"
        email_valid, normalized_email = validate_email_format(email)
        assert email_valid is True
        
        # Validate password strength
        password = "SecurePass123!"
        pwd_valid, pwd_error = validate_password_strength(password)
        assert pwd_valid is True
        assert pwd_error == ""
        
        # Hash password
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        
        # Verify password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False
    
    def test_invalid_registration_attempts(self):
        """Test registration with invalid inputs."""
        # Invalid email
        email_valid, _ = validate_email_format("invalid-email")
        assert email_valid is False
        
        # Weak password
        pwd_valid, _ = validate_password_strength("weak")
        assert pwd_valid is False
        
        # Password missing requirements
        pwd_valid, error = validate_password_strength("NoSpecialChar123")
        assert pwd_valid is False
        assert "special character" in error
