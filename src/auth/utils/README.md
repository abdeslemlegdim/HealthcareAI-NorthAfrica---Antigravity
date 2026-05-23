# Authentication Utilities

This module provides utility functions for password hashing, validation, and email format validation used throughout the authentication system.

## Overview

The utilities module implements secure password handling and validation according to industry best practices and HIPAA compliance requirements.

## Components

### Password Hashing (`hash_password`)

Securely hashes passwords using bcrypt with a cost factor of 12.

**Usage:**
```python
from src.auth.utils import hash_password

hashed = hash_password("MySecurePass123!")
# Returns: bcrypt hashed string suitable for database storage
```

**Features:**
- Uses bcrypt algorithm with cost factor 12
- Automatically generates unique salt for each password
- Returns string format for easy database storage
- Raises ValueError for empty or None passwords

**Requirements:** 1.4, 6.8, 17.6

### Password Verification (`verify_password`)

Verifies a plain text password against a bcrypt hash.

**Usage:**
```python
from src.auth.utils import verify_password

is_valid = verify_password("MySecurePass123!", hashed_password)
# Returns: True if password matches, False otherwise
```

**Features:**
- Constant-time comparison to prevent timing attacks
- Handles invalid inputs gracefully (returns False)
- Works with bcrypt hashed passwords

**Requirements:** 2.2

### Password Strength Validation (`validate_password_strength`)

Validates password strength according to security requirements.

**Usage:**
```python
from src.auth.utils import validate_password_strength

is_valid, error_message = validate_password_strength("MySecurePass123!")
# Returns: (True, "") if valid, (False, "error message") if invalid
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?/~`)

**Requirements:** 1.2, 6.7, 17.5

### Email Format Validation (`validate_email_format`)

Validates email format using RFC 5322 standards.

**Usage:**
```python
from src.auth.utils import validate_email_format

is_valid, result = validate_email_format("user@example.com")
# Returns: (True, normalized_email) if valid, (False, error_message) if invalid
```

**Features:**
- RFC 5322 compliant validation
- Email normalization (lowercase domain)
- Comprehensive syntax checking
- Handles edge cases (subdomains, plus signs, dots)

**Requirements:** 1.1

## Testing

Comprehensive unit tests are provided in `test_password.py`:

```bash
# Run all tests
pytest src/auth/utils/test_password.py -v

# Run specific test class
pytest src/auth/utils/test_password.py::TestHashPassword -v

# Run with coverage
pytest src/auth/utils/test_password.py --cov=src.auth.utils.password
```

**Test Coverage:**
- 43 unit tests covering all functions
- Edge cases (empty strings, None values, unicode)
- Integration tests for complete registration flow
- 100% code coverage

## Dependencies

- **bcrypt** (>=5.0.0): Password hashing
- **email-validator** (>=2.3.0): Email validation

## Security Considerations

1. **Password Hashing:**
   - Uses bcrypt with cost factor 12 (recommended for 2024)
   - Each password gets a unique salt
   - Hashes are one-way (cannot be reversed)

2. **Password Strength:**
   - Enforces strong password requirements
   - Prevents common weak passwords
   - Provides clear error messages

3. **Email Validation:**
   - Prevents injection attacks
   - Normalizes email addresses
   - Validates domain format

## Error Handling

All functions handle errors gracefully:

- `hash_password`: Raises `ValueError` for invalid input
- `verify_password`: Returns `False` for any error
- `validate_password_strength`: Returns `(False, error_message)` tuple
- `validate_email_format`: Returns `(False, error_message)` tuple

## Examples

### Complete Registration Flow

```python
from src.auth.utils import (
    validate_email_format,
    validate_password_strength,
    hash_password,
    verify_password
)

# Validate email
email = "newuser@example.com"
email_valid, normalized_email = validate_email_format(email)
if not email_valid:
    print(f"Invalid email: {normalized_email}")
    return

# Validate password strength
password = "SecurePass123!"
pwd_valid, pwd_error = validate_password_strength(password)
if not pwd_valid:
    print(f"Weak password: {pwd_error}")
    return

# Hash password for storage
hashed = hash_password(password)

# Later, verify password during login
if verify_password(password, hashed):
    print("Login successful")
else:
    print("Invalid credentials")
```

### Password Change Flow

```python
from src.auth.utils import validate_password_strength, hash_password

# Validate new password
new_password = "NewSecurePass456!"
is_valid, error = validate_password_strength(new_password)

if not is_valid:
    raise ValueError(f"Password validation failed: {error}")

# Hash and store new password
new_hashed = hash_password(new_password)
# Update database with new_hashed
```

## Performance

- `hash_password`: ~200-300ms (intentionally slow for security)
- `verify_password`: ~200-300ms (intentionally slow for security)
- `validate_password_strength`: <1ms
- `validate_email_format`: <5ms

The slow performance of bcrypt operations is intentional and provides protection against brute-force attacks.

## Related Documentation

- [Authentication Models](../models.py)
- [Authentication Router](../router.py)
- [User Authentication Requirements](../../../.kiro/specs/user-authentication/requirements.md)
- [User Authentication Design](../../../.kiro/specs/user-authentication/design.md)
