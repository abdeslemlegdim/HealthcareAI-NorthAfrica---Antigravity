# Authentication System Setup Guide

Quick start guide for setting up the Healthcare AI Assistant authentication system.

---

## Overview

The Healthcare AI Assistant includes a comprehensive authentication system with:
- User registration and login
- JWT-based token authentication
- Protected API endpoints
- User dashboard with statistics
- Admin dashboard for user management
- Session management across devices
- HIPAA-compliant audit logging
- Rate limiting and security features

---

## Quick Start

### 1. Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend-react
npm install
cd ..
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate secure keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Add generated keys to .env file
```

**Minimum Required Variables:**
```bash
SECRET_KEY=your-generated-secret-key
JWT_SECRET_KEY=your-generated-jwt-key
DATABASE_URL=sqlite:///./healthcare_ai.db
ENABLE_AUTHENTICATION=true
```

### 3. Run Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Run migrations
alembic upgrade head
```

### 4. Create Admin User

```bash
# Run admin creation script
python scripts/create_admin_user.py

# Follow prompts to enter:
# - Admin email
# - Admin password (min 8 chars, 1 upper, 1 lower, 1 number, 1 special)
```

### 5. Start the Application

```bash
# Start backend
uvicorn main:app --reload

# In another terminal, start frontend
cd frontend-react
npm start
```

### 6. Test Authentication

1. **Visit** `http://localhost:3000`
2. **Click** "Sign Up" to create a user account
3. **Login** with your credentials
4. **Access** the dashboard to see your statistics
5. **Login as admin** to access admin dashboard at `/admin`

---

## Detailed Setup

### Database Setup

#### PostgreSQL (Recommended for Production)

```bash
# Install PostgreSQL
sudo apt-get install postgresql

# Create database
sudo -u postgres createdb healthcare_ai

# Create user
sudo -u postgres createuser -P healthcare_user

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE healthcare_ai TO healthcare_user;"

# Update .env
DATABASE_URL=postgresql://healthcare_user:password@localhost/healthcare_ai
```

#### SQLite (Development)

```bash
# SQLite is included with Python
# Just set the database URL
DATABASE_URL=sqlite:///./healthcare_ai.db
```

### Redis Setup (for Rate Limiting)

#### Install Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server

# Or as service
sudo systemctl start redis
```

#### Configure Redis

```bash
# Update .env
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=  # Leave empty for local development
```

#### Test Redis

```bash
redis-cli ping
# Should return: PONG
```

### Frontend Configuration

#### Environment Variables

Create `frontend-react/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENABLE_AUTH=true
```

#### Install Dependencies

```bash
cd frontend-react
npm install
```

#### Build for Production

```bash
npm run build
```

---

## Configuration Options

### Authentication Settings

```bash
# Enable/disable authentication system
ENABLE_AUTHENTICATION=true

# JWT configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_REMEMBER_ME_DAYS=30
```

### Rate Limiting

```bash
# Login rate limiting
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW_MINUTES=15

# Registration rate limiting
RATE_LIMIT_REGISTER_ATTEMPTS=10
RATE_LIMIT_REGISTER_WINDOW_MINUTES=60

# Token refresh rate limiting
RATE_LIMIT_REFRESH_ATTEMPTS=20
RATE_LIMIT_REFRESH_WINDOW_MINUTES=60
```

### Security Settings

```bash
# HTTPS (production only)
HTTPS_ONLY=false  # Set to true in production
SECURE_COOKIES=false  # Set to true in production
HTTPONLY_COOKIES=true
SAMESITE_COOKIES=lax  # Use "strict" in production

# Audit logging
ENABLE_AUDIT_LOGGING=true
```

### CORS Configuration

```bash
# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Production
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## Features

### User Features

**Registration & Login:**
- Email and password authentication
- Password strength validation
- "Remember Me" option for extended sessions

**Dashboard:**
- Usage statistics (chat, imaging, vitals)
- Recent activity timeline
- Usage trends charts
- Health insights and recommendations
- Quick links to features

**Profile Management:**
- Update email address
- Change password
- View account information

**Session Management:**
- View active sessions across devices
- Revoke specific sessions
- Revoke all other sessions

### Admin Features

**User Management:**
- Search and filter users
- View detailed user information
- Enable/disable user accounts
- Delete users (soft delete)
- View user activity history

**System Monitoring:**
- Total users and active users
- System-wide activity statistics
- Top users by activity
- Recent registrations
- Authentication failure tracking

**Analytics:**
- Usage trends over time
- Activity breakdowns by type
- Custom date range reports

**Export:**
- Export user list to CSV
- Export usage reports to CSV

---

## API Endpoints

### Authentication Endpoints

```
POST   /api/v1/auth/register       - Register new user
POST   /api/v1/auth/login          - Login user
POST   /api/v1/auth/refresh        - Refresh access token
POST   /api/v1/auth/logout         - Logout user
GET    /api/v1/auth/me             - Get current user
PUT    /api/v1/auth/me             - Update user email
PUT    /api/v1/auth/me/password    - Change password
GET    /api/v1/auth/dashboard      - Get dashboard data
GET    /api/v1/auth/sessions       - List active sessions
DELETE /api/v1/auth/sessions/{id}  - Revoke session
DELETE /api/v1/auth/sessions       - Revoke all other sessions
POST   /api/v1/auth/password-reset/request  - Request password reset
POST   /api/v1/auth/password-reset/confirm  - Confirm password reset
```

### Admin Endpoints

```
GET    /api/v1/admin/users                    - List users
GET    /api/v1/admin/users/{id}               - Get user details
GET    /api/v1/admin/users/{id}/activities    - Get user activities
PUT    /api/v1/admin/users/{id}/disable       - Disable user
PUT    /api/v1/admin/users/{id}/enable        - Enable user
DELETE /api/v1/admin/users/{id}               - Delete user
GET    /api/v1/admin/dashboard                - Get admin dashboard
GET    /api/v1/admin/analytics                - Get analytics
```

---

## Testing

### Run Backend Tests

```bash
# All tests
pytest

# Authentication tests only
pytest tests/test_auth.py -v

# With coverage
pytest --cov=src tests/
```

### Run Frontend Tests

```bash
cd frontend-react

# All tests
npm test

# With coverage
npm test -- --coverage
```

### Manual Testing

1. **User Registration:**
   - Visit `/signup`
   - Enter email and password
   - Verify account created

2. **User Login:**
   - Visit `/login`
   - Enter credentials
   - Verify redirect to dashboard

3. **Protected Routes:**
   - Try accessing `/chat` without login
   - Verify redirect to login
   - Login and verify access granted

4. **Admin Features:**
   - Login as admin
   - Visit `/admin`
   - Test user management features

5. **Session Management:**
   - Login on multiple devices
   - View sessions in dashboard
   - Revoke a session
   - Verify logout on that device

---

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
cd frontend-react && npm install
```

**Database connection errors:**
```bash
# Check DATABASE_URL in .env
# Verify database is running
# Run migrations: alembic upgrade head
```

**Redis connection errors:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server
```

**JWT errors:**
```bash
# Verify JWT_SECRET_KEY is set in .env
# Regenerate if needed
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**CORS errors:**
```bash
# Check CORS_ORIGINS in .env
# Add your frontend URL
CORS_ORIGINS=http://localhost:3000
```

**Migration errors:**
```bash
# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

---

## Security Best Practices

### Development

- Use different secrets for development and production
- Don't commit `.env` file to version control
- Use HTTPS even in development (optional)
- Test with realistic data

### Production

- Generate strong random secrets
- Enable HTTPS_ONLY
- Set SECURE_COOKIES=true
- Use strict CORS origins
- Enable all security headers
- Regular security audits
- Monitor authentication failures
- Keep dependencies updated

---

## Backward Compatibility

The authentication system supports backward compatibility mode:

```bash
# Disable authentication (not recommended for production)
ENABLE_AUTHENTICATION=false
```

When disabled:
- All endpoints accessible without authentication
- No token validation
- No rate limiting
- Useful for gradual migration

---

## Documentation

- **API Documentation:** `docs/AUTHENTICATION_API.md`
- **User Guide:** `docs/USER_GUIDE.md`
- **Deployment Checklist:** `docs/DEPLOYMENT_CHECKLIST.md`
- **Architecture:** `.kiro/specs/user-authentication/design.md`
- **Requirements:** `.kiro/specs/user-authentication/requirements.md`

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the API documentation
- Check application logs
- Contact the development team

---

## Next Steps

After setup:
1. Create test users
2. Test all features
3. Configure monitoring
4. Set up backups
5. Review security settings
6. Deploy to staging
7. Perform load testing
8. Deploy to production

---

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

