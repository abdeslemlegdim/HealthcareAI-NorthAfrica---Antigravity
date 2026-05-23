# Authentication Models

This module contains SQLAlchemy models for the user authentication and management system.

## Models

### User
The main user account model with authentication credentials and account status.

**Fields:**
- `id`: Primary key
- `email`: Unique email address (indexed)
- `password_hash`: Bcrypt hashed password
- `is_admin`: Admin privilege flag (indexed)
- `is_active`: Account active status (indexed)
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp (auto-updated)
- `last_activity_at`: Last activity timestamp
- `deleted_at`: Soft delete timestamp

**Relationships:**
- `refresh_tokens`: One-to-many relationship with RefreshToken (cascade delete)
- `activities`: One-to-many relationship with UserActivity (cascade delete)

### RefreshToken
JWT refresh token storage for session management.

**Fields:**
- `id`: Primary key
- `user_id`: Foreign key to User (indexed, cascade delete)
- `token_hash`: Hashed token value (indexed)
- `created_at`: Token creation timestamp
- `expires_at`: Token expiration timestamp
- `revoked_at`: Token revocation timestamp (nullable)
- `device_info`: Device information string
- `ip_address`: IP address of the client

**Relationships:**
- `user`: Many-to-one relationship with User

### UserActivity
User activity tracking for usage statistics and analytics.

**Fields:**
- `id`: Primary key
- `user_id`: Foreign key to User (indexed, cascade delete)
- `activity_type`: Type of activity - 'chat', 'imaging', 'vitals' (indexed)
- `timestamp`: Activity timestamp (indexed)
- `metadata_`: JSON metadata for additional activity details

**Relationships:**
- `user`: Many-to-one relationship with User

**Note:** The field is named `metadata_` in Python but maps to `metadata` in the database to avoid conflicts with SQLAlchemy's reserved `metadata` attribute.

### AuditLog
Comprehensive audit logging for HIPAA compliance and security monitoring.

**Fields:**
- `id`: Primary key
- `event_type`: Type of event (indexed)
- `user_id`: User ID (indexed, nullable)
- `email`: User email
- `ip_address`: Client IP address
- `user_agent`: Client user agent string
- `timestamp`: Event timestamp (indexed)
- `metadata_`: JSON metadata for additional event details

**Note:** The field is named `metadata_` in Python but maps to `metadata` in the database.

## Indexes

The models include several indexes for query optimization:

### Single Column Indexes
- `users.id`, `users.email`, `users.is_admin`, `users.is_active`
- `refresh_tokens.id`, `refresh_tokens.user_id`, `refresh_tokens.token_hash`
- `user_activities.id`, `user_activities.user_id`, `user_activities.activity_type`, `user_activities.timestamp`
- `audit_logs.id`, `audit_logs.event_type`, `audit_logs.user_id`, `audit_logs.timestamp`

### Composite Indexes
- `idx_user_activities_user_timestamp`: (user_id, timestamp) for efficient user activity queries
- `idx_audit_logs_user_timestamp`: (user_id, timestamp) for efficient user audit queries
- `idx_audit_logs_event_timestamp`: (event_type, timestamp) for efficient event type queries

## Foreign Key Constraints

All foreign keys use `CASCADE` delete to ensure referential integrity:
- When a User is deleted, all associated RefreshTokens and UserActivities are automatically deleted
- AuditLog entries are not deleted when users are deleted (user_id is nullable)

## Usage Example

### Creating an Admin User

Use the provided script to create an admin user:

```bash
# Interactive mode (recommended)
python scripts/create_admin_user.py

# Or with command-line arguments
python scripts/create_admin_user.py --email admin@example.com --password SecurePass123!
```

### Programmatic Usage

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.models import Base, User, RefreshToken, UserActivity, AuditLog
from src.auth.services.user_service import UserService

# Create engine and tables
engine = create_engine("sqlite:///auth.db")
Base.metadata.create_all(engine)

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Create an admin user using UserService
user_service = UserService(session)
admin = user_service.create_user(
    email="admin@example.com",
    password="SecurePass123!",
    is_admin=True
)
print(f"Admin user created: {admin.email}")

# Create a regular user
user = user_service.create_user(
    email="user@example.com",
    password="UserPass123!",
    is_admin=False
)

# Create a refresh token
token = RefreshToken(
    user_id=user.id,
    token_hash="token_hash",
    expires_at=datetime.utcnow() + timedelta(days=7)
)
session.add(token)
session.commit()

# Record user activity
activity = UserActivity(
    user_id=user.id,
    activity_type="chat",
    metadata_={"query": "example query"}
)
session.add(activity)
session.commit()

# Create audit log
audit = AuditLog(
    event_type="login",
    user_id=user.id,
    email=user.email,
    ip_address="127.0.0.1"
)
session.add(audit)
session.commit()
```

## Requirements Satisfied

This implementation satisfies the following requirements:
- **9.1**: Users table with all required fields and indexes
- **9.2**: Refresh tokens table with all required fields and indexes
- **9.3**: User activities table with all required fields and indexes
- **21.1**: Admin role support with is_admin field and soft delete support

## Dependencies

- SQLAlchemy >= 2.0.0
- Alembic >= 1.13.0 (for migrations)

## Testing

Run the test script to verify the models:

```bash
python src/auth/test_models.py
```

This will create an in-memory database and test all models, relationships, and cascade deletes.
