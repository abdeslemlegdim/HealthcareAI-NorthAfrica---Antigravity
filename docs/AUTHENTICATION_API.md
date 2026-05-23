# Authentication API Documentation

Complete API reference for the User Authentication and Management System.

---

## Table of Contents

1. [Authentication Endpoints](#authentication-endpoints)
2. [Admin Endpoints](#admin-endpoints)
3. [Error Codes](#error-codes)
4. [Rate Limiting](#rate-limiting)
5. [Security](#security)

---

## Authentication Endpoints

Base URL: `/api/v1/auth`

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "is_admin": false
}
```

**Validation Rules:**
- Email must be valid format
- Password minimum 8 characters
- Password must contain: 1 uppercase, 1 lowercase, 1 number, 1 special character
- Passwords must match

**Rate Limit:** 10 requests per IP per hour

**Error Responses:**
- `400 Bad Request`: Invalid email or weak password
- `409 Conflict`: Email already registered
- `429 Too Many Requests`: Rate limit exceeded

---

### POST /auth/login

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "is_admin": false
  }
}
```

**Token Expiry:**
- Access token: 30 minutes
- Refresh token: 7 days (default) or 30 days (with remember_me)

**Rate Limit:** 5 requests per email per 15 minutes

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account disabled or deleted
- `429 Too Many Requests`: Rate limit exceeded

---

### POST /auth/refresh

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Behavior:**
- Old refresh token is invalidated (token rotation)
- New access and refresh tokens are issued
- Maintains same expiry duration as original token

**Rate Limit:** 20 requests per user per hour

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
- `429 Too Many Requests`: Rate limit exceeded

---

### POST /auth/logout

Logout user and revoke refresh token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Behavior:**
- Revokes the provided refresh token
- Access token remains valid until expiry (client should discard)

**Error Responses:**
- `401 Unauthorized`: Invalid or missing access token

---

### GET /auth/me

Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_activity_at": "2024-01-20T14:25:00Z",
  "is_active": true,
  "is_admin": false
}
```

**Note:** Password hash is never included in response

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token

---

### PUT /auth/me

Update user email.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:00:00Z",
  "last_activity_at": "2024-01-20T15:00:00Z",
  "is_active": true,
  "is_admin": false
}
```

**Validation:**
- Email must be valid format
- Email must not be already registered

**Error Responses:**
- `400 Bad Request`: Invalid email format
- `401 Unauthorized`: Invalid or expired access token
- `409 Conflict`: Email already in use

---

### PUT /auth/me/password

Change user password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!",
  "confirm_password": "NewPass456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully. All sessions have been revoked."
}
```

**Behavior:**
- Validates current password
- Validates new password strength
- Revokes all refresh tokens (forces re-login on all devices)

**Error Responses:**
- `400 Bad Request`: Weak password or passwords don't match
- `401 Unauthorized`: Invalid current password or expired token
- `403 Forbidden`: Account disabled

---

### GET /auth/dashboard

Get enhanced user dashboard data.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "account_age_days": 5
  },
  "statistics": {
    "total_chat_queries": 45,
    "total_images_analyzed": 12,
    "total_vital_measurements": 8,
    "this_week": {
      "chat_queries": 15,
      "images_analyzed": 4,
      "vital_measurements": 2
    },
    "this_month": {
      "chat_queries": 45,
      "images_analyzed": 12,
      "vital_measurements": 8
    }
  },
  "recent_activities": [
    {
      "activity_type": "chat",
      "timestamp": "2024-01-20T14:25:00Z",
      "description": "Chat query processed"
    }
  ],
  "usage_trends": {
    "daily": [
      {"date": "2024-01-20", "count": 5},
      {"date": "2024-01-19", "count": 8}
    ],
    "weekly": [
      {"week": "2024-W03", "count": 25}
    ]
  },
  "health_insights": {
    "engagement_score": 85,
    "recommendations": [
      "Great activity this week!",
      "Try the imaging analysis feature"
    ]
  },
  "quick_links": [
    {"name": "Chat", "url": "/chat", "icon": "chat"},
    {"name": "Imaging", "url": "/imaging", "icon": "image"}
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token

---

### GET /auth/sessions

List active sessions for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "id": 1,
      "device_info": "Chrome on Windows",
      "ip_address": "192.168.1.100",
      "created_at": "2024-01-20T10:00:00Z",
      "last_used_at": "2024-01-20T14:25:00Z",
      "is_current": true
    },
    {
      "id": 2,
      "device_info": "Safari on iPhone",
      "ip_address": "192.168.1.101",
      "created_at": "2024-01-19T08:00:00Z",
      "last_used_at": "2024-01-19T22:00:00Z",
      "is_current": false
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token

---

### DELETE /auth/sessions/{session_id}

Revoke a specific session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Session revoked successfully"
}
```

**Behavior:**
- Revokes the refresh token for the specified session
- User on that device will need to re-login

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `404 Not Found`: Session not found or doesn't belong to user

---

### DELETE /auth/sessions

Revoke all other sessions (except current).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "All other sessions revoked successfully",
  "revoked_count": 3
}
```

**Behavior:**
- Keeps current session active
- Revokes all other refresh tokens
- Users on other devices will need to re-login

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token

---

### POST /auth/password-reset/request

Request password reset token.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

**Behavior:**
- Always returns success (prevents email enumeration)
- Generates reset token valid for 1 hour
- Sends email with reset link (if email exists)

**Note:** Email sending not yet implemented (placeholder)

**Error Responses:**
- `429 Too Many Requests`: Rate limit exceeded

---

### POST /auth/password-reset/confirm

Confirm password reset with token.

**Request Body:**
```json
{
  "token": "reset-token-here",
  "new_password": "NewPass456!",
  "confirm_password": "NewPass456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successfully. All sessions have been revoked."
}
```

**Behavior:**
- Validates reset token
- Updates password
- Revokes all refresh tokens
- Marks token as used (single-use)

**Error Responses:**
- `400 Bad Request`: Invalid token or weak password
- `401 Unauthorized`: Token expired or already used

---

## Admin Endpoints

Base URL: `/api/v1/admin`

**Authentication:** All admin endpoints require admin role.

### GET /admin/users

List all users with filtering and pagination.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 100, max: 1000): Number of records to return
- `search` (string, optional): Search by email
- `is_active` (boolean, optional): Filter by active status

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_activity_at": "2024-01-20T14:25:00Z",
    "is_admin": false,
    "is_active": true,
    "deleted_at": null
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin

---

### GET /admin/users/{user_id}

Get detailed user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_activity_at": "2024-01-20T14:25:00Z",
    "is_admin": false,
    "is_active": true,
    "deleted_at": null
  },
  "statistics": {
    "total_chat_queries": 45,
    "total_images_analyzed": 12,
    "total_vital_measurements": 8
  },
  "activities": [
    {
      "activity_type": "chat",
      "timestamp": "2024-01-20T14:25:00Z",
      "description": "Chat query processed",
      "metadata": {}
    }
  ],
  "sessions": [
    {
      "id": 1,
      "device_info": "Chrome on Windows",
      "ip_address": "192.168.1.100",
      "created_at": "2024-01-20T10:00:00Z",
      "is_active": true
    }
  ],
  "audit_logs": [
    {
      "event_type": "login_success",
      "timestamp": "2024-01-20T10:00:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "metadata": {}
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin
- `404 Not Found`: User not found

---

### GET /admin/users/{user_id}/activities

Get user activity history.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (int, default: 50, max: 500): Number of activities to return

**Response (200 OK):**
```json
[
  {
    "activity_type": "chat",
    "timestamp": "2024-01-20T14:25:00Z",
    "description": "Chat query processed",
    "metadata": {}
  }
]
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin
- `404 Not Found`: User not found

---

### PUT /admin/users/{user_id}/disable

Disable user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "User user@example.com has been disabled"
}
```

**Behavior:**
- Sets `is_active = false`
- Revokes all refresh tokens
- Logs admin action to audit log
- Cannot disable own account

**Error Responses:**
- `400 Bad Request`: Cannot disable own account
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin
- `404 Not Found`: User not found

---

### PUT /admin/users/{user_id}/enable

Enable user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "User user@example.com has been enabled"
}
```

**Behavior:**
- Sets `is_active = true`
- Logs admin action to audit log

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin
- `404 Not Found`: User not found

---

### DELETE /admin/users/{user_id}

Soft delete user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "User user@example.com has been deleted"
}
```

**Behavior:**
- Sets `deleted_at` timestamp (soft delete)
- Revokes all refresh tokens
- Logs admin action to audit log
- Cannot delete own account

**Error Responses:**
- `400 Bad Request`: Cannot delete own account
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin
- `404 Not Found`: User not found

---

### GET /admin/dashboard

Get admin dashboard with system statistics.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "total_users": 150,
  "active_users": 120,
  "total_chat_queries": 5420,
  "total_images_analyzed": 1230,
  "total_vital_measurements": 890,
  "usage_trends": {
    "daily_trends": [
      {"date": "2024-01-20", "count": 245},
      {"date": "2024-01-19", "count": 198}
    ]
  },
  "top_users": [
    {
      "user_id": 1,
      "email": "user@example.com",
      "total_activities": 156,
      "last_activity": "2024-01-20T14:25:00Z"
    }
  ],
  "recent_registrations": [
    {
      "id": 150,
      "email": "newuser@example.com",
      "created_at": "2024-01-20T12:00:00Z",
      "is_active": true
    }
  ],
  "system_health": {
    "total_users": 150,
    "active_users": 120,
    "active_sessions": 85,
    "total_activities_today": 245
  },
  "auth_failures": {
    "total_failures": 45,
    "failures_last_24h": 12,
    "top_failure_reasons": [
      {"reason": "invalid_credentials", "count": 8},
      {"reason": "account_disabled", "count": 4}
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin

---

### GET /admin/analytics

Get detailed analytics and trends.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `days` (int, default: 30, min: 1, max: 365): Time period for analytics

**Response (200 OK):**
```json
{
  "period_days": 30,
  "start_date": "2023-12-21T00:00:00Z",
  "end_date": "2024-01-20T00:00:00Z",
  "total_activities": 7540,
  "by_type": {
    "chat": 5420,
    "imaging": 1230,
    "vitals": 890
  },
  "daily_breakdown": {
    "2024-01-20": {
      "date": "2024-01-20",
      "chat": 180,
      "imaging": 45,
      "vitals": 20,
      "total": 245
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token
- `403 Forbidden`: User is not admin

---

## Error Codes

### Standard HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., email already exists)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Custom Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "specific_error_code"
}
```

### Authentication Error Codes

- `missing_token`: Authorization header missing
- `invalid_token`: Token format invalid or signature verification failed
- `token_expired`: Token has expired (check X-Token-Error header)
- `user_not_found`: User associated with token not found
- `account_disabled`: User account is disabled
- `account_deleted`: User account has been deleted
- `invalid_credentials`: Email or password incorrect
- `weak_password`: Password doesn't meet strength requirements
- `email_already_exists`: Email is already registered
- `rate_limit_exceeded`: Too many requests

---

## Rate Limiting

### Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/register | 10 per IP | 1 hour |
| POST /auth/login | 5 per email | 15 minutes |
| POST /auth/refresh | 20 per user | 1 hour |
| POST /auth/password-reset/request | 3 per IP | 1 hour |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 1705756800
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Try again in 10 minutes.",
  "retry_after": 600
}
```

---

## Security

### Token Security

**Access Tokens:**
- Short-lived (30 minutes)
- Stateless JWT
- Include user ID and role
- Cannot be revoked (rely on short expiry)

**Refresh Tokens:**
- Long-lived (7-30 days)
- Stored in database
- Can be revoked
- Single-use (token rotation)

### Password Security

**Hashing:**
- Algorithm: bcrypt
- Cost factor: 12
- Salted automatically

**Strength Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

### HTTPS Requirements

**Production:**
- HTTPS required for all endpoints
- Secure cookie flags enabled
- HSTS header enforced

**Development:**
- HTTP allowed
- Secure cookies disabled

### Audit Logging

All authentication events are logged:
- Login attempts (success/failure)
- Password changes
- Account creation
- Token refresh
- Logout
- Admin actions

Logs include:
- User ID and email
- IP address
- User agent
- Timestamp
- Event metadata

---

## Best Practices

### Client Implementation

1. **Store tokens securely:**
   - Use httpOnly cookies or secure storage
   - Never store in localStorage for sensitive apps
   - Clear tokens on logout

2. **Handle token expiry:**
   - Implement automatic token refresh
   - Retry failed requests after refresh
   - Logout on refresh failure

3. **Implement proper error handling:**
   - Show user-friendly error messages
   - Handle rate limiting gracefully
   - Provide retry mechanisms

4. **Security considerations:**
   - Always use HTTPS in production
   - Implement CSRF protection
   - Validate all user input
   - Use secure password storage

### Server Configuration

1. **Environment variables:**
   - Generate strong JWT secret keys
   - Configure appropriate token expiry
   - Set rate limits based on usage
   - Enable HTTPS in production

2. **Database:**
   - Regular backups
   - Index optimization
   - Connection pooling
   - Query optimization

3. **Monitoring:**
   - Track authentication failures
   - Monitor rate limit hits
   - Alert on suspicious activity
   - Log all security events

---

## Support

For issues or questions:
- Check error codes and messages
- Review rate limiting headers
- Consult audit logs for security events
- Contact system administrator for account issues

