# Deployment Checklist - Authentication System

Complete checklist for deploying the Healthcare AI Assistant authentication system to production.

---

## Pre-Deployment Checklist

### 1. Environment Setup

#### Generate Secure Keys
```bash
# Generate JWT secret key (32+ characters recommended)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

#### Environment Variables (.env)
- [ ] `SECRET_KEY` - Application secret key (generated)
- [ ] `JWT_SECRET_KEY` - JWT signing key (generated, different from SECRET_KEY)
- [ ] `JWT_ALGORITHM` - Set to "HS256"
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` - Set to 30
- [ ] `REFRESH_TOKEN_EXPIRE_DAYS` - Set to 7
- [ ] `REFRESH_TOKEN_REMEMBER_ME_DAYS` - Set to 30
- [ ] `DATABASE_URL` - Production database connection string
- [ ] `REDIS_URL` - Redis connection string (for rate limiting)
- [ ] `CORS_ORIGINS` - Production frontend URLs only
- [ ] `ENABLE_AUTHENTICATION` - Set to true
- [ ] `HTTPS_ONLY` - Set to true
- [ ] `SECURE_COOKIES` - Set to true
- [ ] `HTTPONLY_COOKIES` - Set to true
- [ ] `SAMESITE_COOKIES` - Set to "strict"

#### Rate Limiting Configuration
- [ ] `RATE_LIMIT_LOGIN_ATTEMPTS` - Set to 5
- [ ] `RATE_LIMIT_LOGIN_WINDOW_MINUTES` - Set to 15
- [ ] `RATE_LIMIT_REGISTER_ATTEMPTS` - Set to 10
- [ ] `RATE_LIMIT_REGISTER_WINDOW_MINUTES` - Set to 60
- [ ] `RATE_LIMIT_REFRESH_ATTEMPTS` - Set to 20
- [ ] `RATE_LIMIT_REFRESH_WINDOW_MINUTES` - Set to 60

#### Security Settings
- [ ] `ENABLE_AUDIT_LOGGING` - Set to true
- [ ] `ENABLE_DATA_ENCRYPTION` - Set to true
- [ ] `PHI_ANONYMIZATION` - Set to true (HIPAA compliance)

---

### 2. Database Setup

#### Run Migrations
```bash
# Navigate to project directory
cd /path/to/healthcare-ai

# Run Alembic migrations
alembic upgrade head

# Verify migrations
alembic current
```

#### Verify Tables Created
- [ ] `users` table exists
- [ ] `refresh_tokens` table exists
- [ ] `user_activities` table exists
- [ ] `audit_logs` table exists
- [ ] All indexes created
- [ ] Foreign keys configured
- [ ] Existing tables have `user_id` column

#### Test Migration Rollback
```bash
# Test rollback (optional but recommended)
alembic downgrade -1
alembic upgrade head
```

---

### 3. Create Initial Admin User

#### Run Admin Creation Script
```bash
# Using the provided script
python scripts/create_admin_user.py

# Follow prompts:
# - Enter admin email
# - Enter admin password
# - Confirm password
```

#### Verify Admin User
```bash
# Connect to database and verify
# PostgreSQL example:
psql -d healthcare_ai -c "SELECT id, email, is_admin FROM users WHERE is_admin = true;"

# SQLite example:
sqlite3 healthcare_ai.db "SELECT id, email, is_admin FROM users WHERE is_admin = true;"
```

#### Test Admin Login
- [ ] Login with admin credentials
- [ ] Access admin dashboard at `/admin`
- [ ] Verify admin features work

---

### 4. Backend Configuration

#### Update main.py
```python
# Add authentication routers
from src.auth.router import router as auth_router
from src.admin.router import router as admin_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
```

#### Add Security Middleware
```python
# Add security middleware
from src.auth.security_middleware import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)
```

#### Configure CORS
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Apply Authentication to Protected Endpoints
- [ ] Chat endpoints require authentication
- [ ] Imaging endpoints require authentication
- [ ] Vitals endpoints require authentication
- [ ] Health/metrics endpoints excluded
- [ ] Docs endpoints excluded

---

### 5. Frontend Configuration

#### Update Environment Variables
```bash
# .env or .env.production
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENABLE_AUTH=true
```

#### Build Frontend
```bash
cd frontend-react
npm install
npm run build
```

#### Verify Build
- [ ] Build completes without errors
- [ ] Build output in `dist/` or `build/`
- [ ] Static assets generated
- [ ] Index.html created

---

### 6. HTTPS Configuration

#### SSL/TLS Certificate
- [ ] Obtain SSL certificate (Let's Encrypt, commercial CA, etc.)
- [ ] Install certificate on server
- [ ] Configure web server (Nginx, Apache, etc.)
- [ ] Test HTTPS connection
- [ ] Verify certificate validity

#### Nginx Configuration Example
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers (additional to middleware)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

### 7. Redis Setup (for Rate Limiting)

#### Install Redis
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

#### Configure Redis
- [ ] Set password (if not using Docker)
- [ ] Configure persistence
- [ ] Set memory limits
- [ ] Enable AOF or RDB

#### Test Redis Connection
```bash
redis-cli ping
# Should return: PONG
```

#### Update Redis URL in .env
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password
```

---

### 8. Testing

#### Backend API Tests
```bash
# Run backend tests
pytest tests/

# Run specific authentication tests
pytest tests/test_auth.py -v

# Check test coverage
pytest --cov=src tests/
```

#### Frontend Tests
```bash
cd frontend-react

# Run frontend tests
npm test

# Run with coverage
npm test -- --coverage
```

#### Manual Testing Checklist
- [ ] User registration works
- [ ] User login works
- [ ] Token refresh works automatically
- [ ] Logout works
- [ ] Protected routes require authentication
- [ ] Admin dashboard accessible to admins only
- [ ] User management works
- [ ] Session management works
- [ ] Password change works
- [ ] Rate limiting enforced
- [ ] HTTPS redirect works
- [ ] Security headers present

#### Load Testing (Optional)
```bash
# Using Apache Bench
ab -n 1000 -c 10 https://yourdomain.com/api/v1/auth/login

# Using wrk
wrk -t12 -c400 -d30s https://yourdomain.com/api/v1/auth/login
```

---

### 9. Monitoring Setup

#### Application Monitoring
- [ ] Configure logging (level, format, destination)
- [ ] Set up error tracking (Sentry, Rollbar, etc.)
- [ ] Configure performance monitoring
- [ ] Set up uptime monitoring

#### Database Monitoring
- [ ] Monitor connection pool usage
- [ ] Track slow queries
- [ ] Monitor disk usage
- [ ] Set up backup alerts

#### Security Monitoring
- [ ] Monitor authentication failures
- [ ] Track rate limit hits
- [ ] Alert on suspicious activity
- [ ] Monitor audit logs

#### Metrics to Track
- [ ] Request rate
- [ ] Response time
- [ ] Error rate
- [ ] Active users
- [ ] Active sessions
- [ ] Database connections
- [ ] Redis memory usage

---

### 10. Backup and Recovery

#### Database Backups
```bash
# PostgreSQL backup
pg_dump healthcare_ai > backup_$(date +%Y%m%d).sql

# Automated daily backups
0 2 * * * pg_dump healthcare_ai > /backups/healthcare_ai_$(date +\%Y\%m\%d).sql
```

#### Backup Checklist
- [ ] Daily automated backups configured
- [ ] Backup retention policy set (30 days recommended)
- [ ] Backups stored off-site
- [ ] Backup encryption enabled
- [ ] Restore procedure tested

#### Recovery Testing
- [ ] Test database restore
- [ ] Verify data integrity
- [ ] Test application startup
- [ ] Verify authentication works

---

### 11. Security Hardening

#### Server Security
- [ ] Firewall configured (allow only necessary ports)
- [ ] SSH key-based authentication only
- [ ] Disable root login
- [ ] Keep system updated
- [ ] Install security updates automatically

#### Application Security
- [ ] All secrets in environment variables (not in code)
- [ ] No debug mode in production
- [ ] Error messages don't expose sensitive info
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using ORM)
- [ ] XSS prevention (React handles this)
- [ ] CSRF protection enabled

#### Database Security
- [ ] Strong database password
- [ ] Database not exposed to internet
- [ ] Principle of least privilege for DB user
- [ ] Connection encryption enabled
- [ ] Regular security audits

---

### 12. Documentation

#### Update Documentation
- [ ] API documentation current
- [ ] User guide updated
- [ ] Admin guide updated
- [ ] Deployment guide updated
- [ ] Troubleshooting guide updated

#### Create Runbooks
- [ ] Deployment procedure
- [ ] Rollback procedure
- [ ] Incident response plan
- [ ] Backup and restore procedure
- [ ] Scaling procedure

---

### 13. Performance Optimization

#### Backend Optimization
- [ ] Database indexes optimized
- [ ] Query performance reviewed
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] Async operations where appropriate

#### Frontend Optimization
- [ ] Code splitting enabled
- [ ] Assets minified
- [ ] Images optimized
- [ ] Lazy loading implemented
- [ ] CDN configured (optional)

---

### 14. Compliance

#### HIPAA Compliance
- [ ] Audit logging enabled
- [ ] Data encryption at rest
- [ ] Data encryption in transit (HTTPS)
- [ ] Access controls implemented
- [ ] PHI anonymization enabled
- [ ] Backup encryption enabled

#### GDPR Compliance (if applicable)
- [ ] Privacy policy updated
- [ ] Cookie consent implemented
- [ ] Data export functionality
- [ ] Data deletion functionality
- [ ] User consent tracking

---

## Deployment Steps

### Step 1: Pre-Deployment Verification
```bash
# Verify all environment variables set
python -c "from src.utils.config import settings; print('Config OK')"

# Verify database connection
python -c "from src.database import engine; engine.connect(); print('DB OK')"

# Verify Redis connection
redis-cli ping
```

### Step 2: Database Migration
```bash
# Backup current database
pg_dump healthcare_ai > pre_migration_backup.sql

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

### Step 3: Create Admin User
```bash
python scripts/create_admin_user.py
```

### Step 4: Deploy Backend
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Restart application
systemctl restart healthcare-ai

# Or using Docker
docker-compose up -d --build
```

### Step 5: Deploy Frontend
```bash
# Build frontend
cd frontend-react
npm install
npm run build

# Copy to web server
cp -r build/* /var/www/html/

# Or deploy to CDN/hosting service
```

### Step 6: Verify Deployment
```bash
# Check backend health
curl https://yourdomain.com/health

# Check authentication endpoint
curl https://yourdomain.com/api/v1/auth/login

# Check frontend
curl https://yourdomain.com/
```

### Step 7: Smoke Tests
- [ ] Visit homepage
- [ ] Register new user
- [ ] Login with new user
- [ ] Access dashboard
- [ ] Test protected features
- [ ] Login as admin
- [ ] Access admin dashboard
- [ ] Test user management

### Step 8: Monitor
- [ ] Check application logs
- [ ] Monitor error rates
- [ ] Check database performance
- [ ] Monitor Redis usage
- [ ] Review security logs

---

## Post-Deployment

### Immediate Actions (First Hour)
- [ ] Monitor error logs
- [ ] Check authentication success rate
- [ ] Verify HTTPS working
- [ ] Test critical user flows
- [ ] Monitor server resources

### First Day
- [ ] Review all logs
- [ ] Check performance metrics
- [ ] Monitor user registrations
- [ ] Verify backups running
- [ ] Test admin functions

### First Week
- [ ] Analyze usage patterns
- [ ] Review security logs
- [ ] Check for any issues
- [ ] Gather user feedback
- [ ] Optimize based on metrics

---

## Rollback Procedure

### If Issues Occur

#### Step 1: Assess Severity
- Critical: Immediate rollback
- High: Rollback within 1 hour
- Medium: Fix forward if possible
- Low: Schedule fix

#### Step 2: Rollback Backend
```bash
# Revert to previous version
git checkout <previous-commit>

# Rollback database if needed
alembic downgrade -1

# Restart application
systemctl restart healthcare-ai
```

#### Step 3: Rollback Frontend
```bash
# Deploy previous build
cp -r build-backup/* /var/www/html/
```

#### Step 4: Verify Rollback
- [ ] Application starts successfully
- [ ] Users can login
- [ ] Core features work
- [ ] No errors in logs

#### Step 5: Communicate
- [ ] Notify users of issue
- [ ] Provide status updates
- [ ] Announce resolution

---

## Troubleshooting

### Common Issues

**Database Connection Fails:**
- Check DATABASE_URL
- Verify database is running
- Check firewall rules
- Verify credentials

**Redis Connection Fails:**
- Check REDIS_URL
- Verify Redis is running
- Check password
- Test with redis-cli

**HTTPS Not Working:**
- Check certificate installation
- Verify Nginx/Apache config
- Check firewall (port 443)
- Test with curl

**Authentication Fails:**
- Check JWT_SECRET_KEY set
- Verify database migrations
- Check user exists
- Review audit logs

**Rate Limiting Not Working:**
- Verify Redis connection
- Check rate limit config
- Review Redis logs
- Test with multiple requests

---

## Support Contacts

**Technical Issues:**
- DevOps Team: devops@example.com
- Backend Team: backend@example.com
- Frontend Team: frontend@example.com

**Security Issues:**
- Security Team: security@example.com
- Emergency: +1-XXX-XXX-XXXX

**Business Issues:**
- Product Manager: pm@example.com
- Support Team: support@example.com

---

## Checklist Summary

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Secrets generated
- [ ] Database setup complete
- [ ] Admin user created
- [ ] HTTPS configured
- [ ] Redis configured
- [ ] Tests passing

### Deployment
- [ ] Code deployed
- [ ] Migrations run
- [ ] Services restarted
- [ ] Smoke tests passed
- [ ] Monitoring active

### Post-Deployment
- [ ] Logs reviewed
- [ ] Metrics normal
- [ ] Users can access
- [ ] Backups verified
- [ ] Documentation updated

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Verified By:** _______________  
**Sign-off:** _______________

