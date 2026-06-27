# Environment Configuration Guide

This guide explains how to configure environment variables for the User Authentication and Management System.

## Quick Start

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Generate a secure JWT secret key:
   ```bash
   # Using Python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Or using OpenSSL
   openssl rand -base64 32
   ```

3. Update `.env` with your generated keys and configuration

## Required Authentication Variables

### JWT_SECRET_KEY

**Purpose:** Secret key used to sign and verify JWT tokens

**Security Level:** CRITICAL - Never commit this to version control

**How to Generate:**

```bash
# Method 1: Using Python (recommended)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using OpenSSL
openssl rand -base64 32

# Method 3: Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

**Example:**
```env
JWT_SECRET_KEY="xK9mP2vN8qR5tY7wZ3aB6cD1eF4gH0jL"
```

**Best Practices:**
- Use a minimum of 32 characters
- Use cryptographically secure random generation
- Use different keys for development, staging, and production
- Rotate keys periodically (every 90 days recommended)
- Store production keys in a secure secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)

### JWT_ALGORITHM

**Purpose:** Algorithm used for JWT token signing

**Default:** `HS256` (HMAC with SHA-256)

**Options:**
- `HS256` - HMAC with SHA-256 (symmetric, recommended for most use cases)
- `HS384` - HMAC with SHA-384 (symmetric, more secure but slower)
- `HS512` - HMAC with SHA-512 (symmetric, most secure but slowest)
- `RS256` - RSA with SHA-256 (asymmetric, use if you need public key verification)

**Example:**
```env
JWT_ALGORITHM="HS256"
```

**When to Change:**
- Use `RS256` if you need to verify tokens without access to the secret key
- Use `HS384` or `HS512` for higher security requirements (with performance tradeoff)

### ACCESS_TOKEN_EXPIRE_MINUTES

**Purpose:** Expiration time for access tokens in minutes

**Default:** `30` minutes

**Recommended Range:** 15-60 minutes

**Example:**
```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Considerations:**
- Shorter expiration = more secure but more frequent token refreshes
- Longer expiration = better UX but higher risk if token is compromised
- 30 minutes is a good balance for most applications
- For high-security applications, consider 15 minutes
- For internal tools with lower risk, consider 60 minutes

### REFRESH_TOKEN_EXPIRE_DAYS

**Purpose:** Expiration time for refresh tokens in days

**Default:** `7` days

**Recommended Range:** 7-30 days

**Example:**
```env
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Considerations:**
- Refresh tokens are automatically extended to 30 days when "Remember Me" is selected
- Shorter expiration = more secure but users need to log in more frequently
- Longer expiration = better UX but higher risk if token is compromised
- 7 days is recommended for healthcare applications (HIPAA compliance)
- For consumer applications, 30 days is common

### CORS_ORIGINS

**Purpose:** Comma-separated list of allowed origins for Cross-Origin Resource Sharing

**Security Level:** HIGH - Restricts which domains can access your API

**Example:**
```env
# Development
CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

# Production
CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Mixed (not recommended)
CORS_ORIGINS="https://yourdomain.com,http://localhost:3000"
```

**Best Practices:**
- **Development:** Include all local development ports (3000, 5173, 8501, etc.)
- **Production:** ONLY include your actual production domains
- **Never use `*` (wildcard)** - this disables CORS protection
- Use HTTPS in production
- Include both `www` and non-`www` versions if needed
- Include subdomains explicitly (e.g., `app.yourdomain.com`, `api.yourdomain.com`)

**Common Ports:**
- `3000` - Create React App, Next.js
- `5173` - Vite (default)
- `8501` - Streamlit
- `8080` - Alternative development server

## Complete Authentication Configuration Example

### Development Environment (.env.development)

```env
# =================================
# Security & Authentication
# =================================
SECRET_KEY="dev-secret-key-not-for-production"
JWT_SECRET_KEY="dev-jwt-secret-key-not-for-production"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# =================================
# API Configuration
# =================================
CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8501,http://127.0.0.1:5173"
```

### Production Environment (.env.production)

```env
# =================================
# Security & Authentication
# =================================
SECRET_KEY="<generated-with-secrets.token_urlsafe(32)>"
JWT_SECRET_KEY="<generated-with-secrets.token_urlsafe(32)>"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# =================================
# API Configuration
# =================================
CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

## Security Checklist

Before deploying to production, verify:

- [ ] JWT_SECRET_KEY is generated using cryptographically secure random generation
- [ ] JWT_SECRET_KEY is at least 32 characters long
- [ ] JWT_SECRET_KEY is different from development environment
- [ ] JWT_SECRET_KEY is stored in a secure secrets manager (not in .env file in production)
- [ ] CORS_ORIGINS only includes your actual production domains
- [ ] CORS_ORIGINS uses HTTPS (not HTTP) in production
- [ ] ACCESS_TOKEN_EXPIRE_MINUTES is set appropriately for your security requirements
- [ ] REFRESH_TOKEN_EXPIRE_DAYS is set appropriately for your security requirements
- [ ] .env file is in .gitignore and never committed to version control

## Troubleshooting

### "Invalid token" errors

**Possible causes:**
1. JWT_SECRET_KEY changed after tokens were issued
2. Token expired
3. Token was manually modified
4. Clock skew between servers

**Solutions:**
- Ensure JWT_SECRET_KEY is consistent across all servers
- Check token expiration times
- Verify system clocks are synchronized (use NTP)
- Clear browser storage and log in again

### CORS errors in browser console

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/v1/auth/login' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Solutions:**
1. Add your frontend origin to CORS_ORIGINS:
   ```env
   CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
   ```
2. Restart the backend server after changing CORS_ORIGINS
3. Clear browser cache
4. Verify the origin in the error message matches exactly (including protocol and port)

### Tokens expiring too quickly

**Solutions:**
- Increase ACCESS_TOKEN_EXPIRE_MINUTES (e.g., from 30 to 60)
- Ensure automatic token refresh is working in the frontend
- Check for clock skew between client and server

### Users being logged out unexpectedly

**Possible causes:**
1. Refresh token expired
2. Refresh token was revoked (password change, logout from another device)
3. Database connection issues
4. JWT_SECRET_KEY changed

**Solutions:**
- Increase REFRESH_TOKEN_EXPIRE_DAYS
- Check audit logs for token revocation events
- Verify database connectivity
- Ensure JWT_SECRET_KEY hasn't changed

## Environment Variable Validation

The application validates environment variables on startup. If required variables are missing or invalid, you'll see errors like:

```
ValidationError: 1 validation error for Settings
JWT_SECRET_KEY
  field required (type=value_error.missing)
```

**Solution:** Ensure all required variables are set in your .env file.

## Additional Resources

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
