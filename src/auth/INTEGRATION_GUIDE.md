# Authentication System Integration Guide

## Overview

This guide provides step-by-step instructions for integrating the authentication system into the Healthcare AI Assistant main application.

## Prerequisites

- Python 3.8+
- FastAPI application
- SQLAlchemy database setup
- Redis (optional, for distributed rate limiting)

## Integration Steps

### Step 1: Database Setup

#### 1.1 Run Migrations

```bash
# Run Alembic migrations to create authentication tables
alembic upgrade head
```

This will create the following tables:
- `users` - User accounts
- `refresh_tokens` - JWT refresh tokens
- `user_activities` - Activity tracking
- `audit_logs` - Audit trail

#### 1.2 Create Initial Admin User

Use the provided script to create the first admin user:

```bash
# Interactive mode (recommended for security)
python scripts/create_admin_user.py

# Or with command-line arguments
python scripts/create_admin_user.py --email admin@example.com --password SecurePass123!
```

The script will:
- Validate email format
- Verify password strength (min 8 chars, uppercase, lowercase, number, special char)
- Create user with `is_admin=True`
- Provide clear error messages if validation fails

**Example output:**
```
============================================================
Create Initial Admin User
============================================================

Enter admin email: admin@healthcare.com
Enter admin password: 
Confirm admin password: 

Creating admin user...

============================================================
✅ Success!
============================================================

Admin user created successfully:
  Email: admin@healthcare.com
  User ID: 1
  Admin: True
  Created: 2024-01-15 10:30:00
```

**Programmatic usage (if needed):**
```python
from sqlalchemy.orm import Session
from src.auth.services.user_service import UserService

def create_admin_user(db: Session, email: str, password: str):
    """Create initial admin user."""
    user_service = UserService(db)
    admin = user_service.create_user(
        email=email,
        password=password,
        is_admin=True
    )
    print(f"Admin user created: {admin.email}")
    return admin
```

### Step 2: Configure Environment Variables

Add the following to your `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Authentication
ENABLE_AUTHENTICATION=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Redis (optional, for rate limiting)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Security
HTTPS_ONLY=false  # Set to true in production
```

**Generate a secure JWT secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Update main.py

#### 3.1 Import Authentication Components

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Import authentication components
from src.auth import auth_router, get_current_user
from src.admin import admin_router
from src.auth.rate_limiter import RateLimiter
```

#### 3.2 Initialize Rate Limiter

```python
# Initialize rate limiter (with Redis if available)
try:
    import redis
    redis_client = redis.from_url(settings.REDIS_URL, password=settings.REDIS_PASSWORD)
    rate_limiter = RateLimiter(redis_client)
except Exception as e:
    print(f"Redis not available, using in-memory rate limiting: {e}")
    rate_limiter = RateLimiter()

# Make rate limiter available to router
from src.auth import router as auth_router_module
auth_router_module.rate_limiter = rate_limiter
```

#### 3.3 Register Routers

```python
app = FastAPI(title="Healthcare AI Assistant")

# Register authentication router
app.include_router(auth_router, prefix="/api/v1")

# Register admin router
app.include_router(admin_router, prefix="/api/v1")
```

#### 3.4 Configure Database Session Dependency

Replace the placeholder `get_db()` function in auth/router.py and admin/router.py:

```python
# In your database.py or similar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Then update the imports in router files:

```python
# In src/auth/router.py and src/admin/router.py
from your_database_module import get_db  # Replace placeholder
```

### Step 4: Protect Existing Endpoints

#### 4.1 Add Authentication to Existing Routes

Update your existing API endpoints to require authentication:

```python
from src.auth.middleware import get_current_user
from src.auth.models import User

@app.post("/api/v1/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),  # Add this
    db: Session = Depends(get_db)
):
    # Your existing code
    # Now you have access to current_user.id, current_user.email, etc.
    pass
```

#### 4.2 Add Activity Tracking

Track user activities in protected endpoints:

```python
from src.auth.services.activity_service import ActivityService

@app.post("/api/v1/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Your existing code
    result = process_chat(request)
    
    # Track activity
    activity_service = ActivityService(db)
    await activity_service.record_activity(
        user_id=current_user.id,
        activity_type="chat",
        metadata={"query": request.query[:100]}  # Store preview
    )
    
    return result
```

#### 4.3 Backward Compatibility Mode

For gradual rollout, use optional authentication:

```python
from src.auth.middleware import get_current_user_optional

@app.post("/api/v1/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # Works with or without authentication
    user_id = current_user.id if current_user else None
    
    # Your existing code
    pass
```

### Step 5: Frontend Integration

#### 5.1 Configure Axios Interceptor

Create `src/services/authInterceptor.js`:

```javascript
import axios from 'axios';

// Add token to requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken
        });
        
        const { access_token, refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

#### 5.2 Create AuthContext

Create `src/context/AuthContext.jsx`:

```javascript
import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Check if user is logged in on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);
  
  const fetchUser = async () => {
    try {
      const response = await axios.get('/api/v1/auth/me');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  };
  
  const login = async (email, password, rememberMe = false) => {
    const response = await axios.post('/api/v1/auth/login', {
      email,
      password,
      remember_me: rememberMe
    });
    
    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    await fetchUser();
  };
  
  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    try {
      await axios.post('/api/v1/auth/logout', {
        refresh_token: refreshToken
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };
  
  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### 5.3 Create Protected Route Component

Create `src/components/Auth/ProtectedRoute.jsx`:

```javascript
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
};
```

#### 5.4 Update App.jsx

```javascript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
// ... other imports

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          } />
          
          <Route path="/chat" element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          } />
          
          {/* Other protected routes */}
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

### Step 6: Testing

#### 6.1 Test Authentication Flow

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Access protected endpoint
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 6.2 Test Admin Endpoints

```bash
# List users (admin only)
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# Get admin dashboard
curl -X GET http://localhost:8000/api/v1/admin/dashboard \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### Step 7: Production Deployment

#### 7.1 Security Checklist

- [ ] Generate strong JWT_SECRET_KEY (min 32 characters)
- [ ] Enable HTTPS (set HTTPS_ONLY=true)
- [ ] Configure CORS with specific origins
- [ ] Set up Redis for distributed rate limiting
- [ ] Configure secure cookie flags
- [ ] Enable audit log retention
- [ ] Set up monitoring and alerting
- [ ] Review and test rate limits
- [ ] Test password reset flow
- [ ] Verify HIPAA compliance requirements

#### 7.2 Performance Optimization

- [ ] Set up database connection pooling
- [ ] Configure Redis for session storage
- [ ] Enable database query caching
- [ ] Set up CDN for frontend assets
- [ ] Configure load balancer
- [ ] Monitor token validation performance

#### 7.3 Monitoring

Set up monitoring for:
- Failed login attempts
- Token refresh rates
- API response times
- Database query performance
- Rate limit hits
- Audit log growth

## Troubleshooting

### Common Issues

**Issue: "Database session dependency not yet configured"**
- Solution: Replace the placeholder `get_db()` function with your actual database session dependency

**Issue: Rate limiting not working**
- Solution: Ensure Redis is running or use in-memory fallback

**Issue: Token refresh fails**
- Solution: Check JWT_SECRET_KEY is consistent across restarts

**Issue: CORS errors**
- Solution: Add frontend origin to CORS_ORIGINS in .env

**Issue: Admin endpoints return 403**
- Solution: Ensure user has is_admin=True in database

## API Documentation

Once integrated, API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues or questions:
1. Check the implementation status: `src/auth/IMPLEMENTATION_STATUS.md`
2. Review the spec files: `.kiro/specs/user-authentication/`
3. Check code documentation in module docstrings
