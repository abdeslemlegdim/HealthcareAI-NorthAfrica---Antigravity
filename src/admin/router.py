"""
Admin Router for FastAPI.

This module provides HTTP endpoints for admin user management and system monitoring.
Includes user management, analytics, and system-wide statistics.

Requirements: 21.1-21.12, 22.1-22.10
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from src.auth.models import User, UserActivity, AuditLog, RefreshToken
from src.auth.services.user_service import UserService
from src.auth.services.token_service import TokenService
from src.auth.services.activity_service import ActivityService
from src.auth.services.audit_service import AuditService
from src.auth.middleware import get_current_admin


# Pydantic models for responses
class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    created_at: datetime
    updated_at: datetime
    last_activity_at: Optional[datetime]
    is_admin: bool
    is_active: bool
    deleted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ActivitySummary(BaseModel):
    """Activity summary response."""
    activity_type: str
    timestamp: datetime
    description: str
    metadata: Optional[dict]


class SessionInfo(BaseModel):
    """Session information response."""
    id: int
    device_info: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class AuditLogEntry(BaseModel):
    """Audit log entry response."""
    event_type: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[dict]
    
    class Config:
        from_attributes = True


class AdminUserDetailResponse(BaseModel):
    """Detailed user information for admin."""
    user: UserResponse
    statistics: dict
    activities: List[ActivitySummary]
    sessions: List[SessionInfo]
    audit_logs: List[AuditLogEntry]


class TopUser(BaseModel):
    """Top user by activity."""
    user_id: int
    email: str
    total_activities: int
    last_activity: Optional[datetime]


class SystemHealth(BaseModel):
    """System health metrics."""
    total_users: int
    active_users: int
    active_sessions: int
    total_activities_today: int


class AuthFailureStats(BaseModel):
    """Authentication failure statistics."""
    total_failures: int
    failures_last_24h: int
    top_failure_reasons: List[dict]


class AdminDashboardResponse(BaseModel):
    """Admin dashboard response."""
    total_users: int
    active_users: int
    total_chat_queries: int
    total_images_analyzed: int
    total_vital_measurements: int
    usage_trends: dict
    top_users: List[TopUser]
    recent_registrations: List[UserResponse]
    system_health: SystemHealth
    auth_failures: AuthFailureStats


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# Router instance
router = APIRouter(tags=["admin"])


from src.database import get_db


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering.
    
    Supports pagination, search by email, and filtering by active status.
    
    Requirements: 21.3
    """
    query = db.query(User)
    
    # Apply search filter
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    
    # Apply active status filter
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Exclude soft-deleted users by default
    query = query.filter(User.deleted_at.is_(None))
    
    # Apply pagination
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return users


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def get_user_details(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific user.
    
    Returns comprehensive user information including profile, statistics,
    activities, sessions, and audit logs.
    
    Requirements: 21.4
    """
    # Initialize services
    user_service = UserService(db)
    activity_service = ActivityService(db)
    audit_service = AuditService(db)
    token_service = TokenService(db, None)  # settings not needed for session queries
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get statistics
    statistics = await activity_service.get_user_statistics(user_id)
    
    # Get recent activities
    activities_raw = await activity_service.get_recent_activities(user_id, limit=20)
    activities = [ActivitySummary(**activity) for activity in activities_raw]
    
    # Get active sessions
    sessions_raw = await token_service.get_active_sessions(user_id)
    sessions = [
        SessionInfo(
            id=s.id,
            device_info=s.device_info,
            ip_address=s.ip_address,
            created_at=s.created_at,
            is_active=s.revoked_at is None
        )
        for s in sessions_raw
    ]
    
    # Get audit logs
    audit_logs_raw = await audit_service.get_user_audit_logs(user_id, limit=50)
    audit_logs = [
        AuditLogEntry(
            event_type=log.event_type,
            timestamp=log.timestamp,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            metadata=log.metadata_
        )
        for log in audit_logs_raw
    ]
    
    return AdminUserDetailResponse(
        user=UserResponse.from_orm(user),
        statistics=statistics,
        activities=activities,
        sessions=sessions,
        audit_logs=audit_logs
    )


@router.get("/users/{user_id}/activities", response_model=List[ActivitySummary])
async def get_user_activities(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get activity history for a specific user.
    
    Returns detailed activity history with timestamps and descriptions.
    
    Requirements: 21.5
    """
    # Initialize services
    activity_service = ActivityService(db)
    
    # Get activities
    activities_raw = await activity_service.get_recent_activities(user_id, limit=limit)
    activities = [ActivitySummary(**activity) for activity in activities_raw]
    
    return activities


@router.put("/users/{user_id}/disable", response_model=MessageResponse)
async def disable_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Disable a user account.
    
    Sets is_active=False and revokes all active sessions.
    
    Requirements: 21.6
    """
    # Initialize services
    user_service = UserService(db)
    token_service = TokenService(db, None)
    audit_service = AuditService(db)
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent disabling self
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account"
        )
    
    # Disable user
    user_service.disable_user(user_id)
    
    # Revoke all sessions
    await token_service.revoke_all_user_tokens(user_id)
    
    # Log admin action
    await audit_service.log_admin_action(
        admin_user_id=current_admin.id,
        admin_email=current_admin.email,
        action="disable_user",
        target_user_id=user_id,
        target_email=user.email
    )
    
    return MessageResponse(message=f"User {user.email} has been disabled")


@router.put("/users/{user_id}/enable", response_model=MessageResponse)
async def enable_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Enable a user account.
    
    Sets is_active=True allowing the user to log in.
    
    Requirements: 21.7
    """
    # Initialize services
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Enable user
    user_service.enable_user(user_id)
    
    # Log admin action
    await audit_service.log_admin_action(
        admin_user_id=current_admin.id,
        admin_email=current_admin.email,
        action="enable_user",
        target_user_id=user_id,
        target_email=user.email
    )
    
    return MessageResponse(message=f"User {user.email} has been enabled")


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Soft delete a user account.
    
    Sets deleted_at timestamp and revokes all active sessions.
    
    Requirements: 21.8
    """
    # Initialize services
    user_service = UserService(db)
    token_service = TokenService(db, None)
    audit_service = AuditService(db)
    
    # Get user
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting self
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete user
    user_service.soft_delete_user(user_id)
    
    # Revoke all sessions
    await token_service.revoke_all_user_tokens(user_id)
    
    # Log admin action
    await audit_service.log_admin_action(
        admin_user_id=current_admin.id,
        admin_email=current_admin.email,
        action="delete_user",
        target_user_id=user_id,
        target_email=user.email
    )
    
    return MessageResponse(message=f"User {user.email} has been deleted")


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard with system-wide statistics.
    
    Returns comprehensive system metrics including user counts, activity
    statistics, top users, recent registrations, and system health.
    
    Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8, 22.9, 22.10
    """
    # Total users
    total_users = db.query(func.count(User.id)).filter(
        User.deleted_at.is_(None)
    ).scalar() or 0
    
    # Active users (logged in within last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(func.count(User.id)).filter(
        User.last_activity_at >= thirty_days_ago,
        User.deleted_at.is_(None)
    ).scalar() or 0
    
    # Total activities by type
    total_chat = db.query(func.count(UserActivity.id)).filter(
        UserActivity.activity_type == 'chat'
    ).scalar() or 0
    
    total_imaging = db.query(func.count(UserActivity.id)).filter(
        UserActivity.activity_type == 'imaging'
    ).scalar() or 0
    
    total_vitals = db.query(func.count(UserActivity.id)).filter(
        UserActivity.activity_type == 'vitals'
    ).scalar() or 0
    
    # Usage trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    activities = db.query(UserActivity).filter(
        UserActivity.timestamp >= thirty_days_ago
    ).all()
    
    # Group by date
    daily_usage = {}
    for activity in activities:
        date_key = activity.timestamp.strftime('%Y-%m-%d')
        if date_key not in daily_usage:
            daily_usage[date_key] = {"date": date_key, "count": 0}
        daily_usage[date_key]["count"] += 1
    
    usage_trends = {
        "daily_trends": sorted(daily_usage.values(), key=lambda x: x["date"])
    }
    
    # Top users by activity
    top_users_raw = db.query(
        User.id,
        User.email,
        func.count(UserActivity.id).label('activity_count'),
        func.max(UserActivity.timestamp).label('last_activity')
    ).join(UserActivity).filter(
        User.deleted_at.is_(None)
    ).group_by(User.id, User.email).order_by(
        func.count(UserActivity.id).desc()
    ).limit(10).all()
    
    top_users = [
        TopUser(
            user_id=row.id,
            email=row.email,
            total_activities=row.activity_count,
            last_activity=row.last_activity
        )
        for row in top_users_raw
    ]
    
    # Recent registrations
    recent_registrations = db.query(User).filter(
        User.deleted_at.is_(None)
    ).order_by(User.created_at.desc()).limit(10).all()
    
    # System health
    active_sessions = db.query(func.count(RefreshToken.id)).filter(
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.utcnow()
    ).scalar() or 0
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    activities_today = db.query(func.count(UserActivity.id)).filter(
        UserActivity.timestamp >= today
    ).scalar() or 0
    
    system_health = SystemHealth(
        total_users=total_users,
        active_users=active_users,
        active_sessions=active_sessions,
        total_activities_today=activities_today
    )
    
    # Auth failures
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    total_failures = db.query(func.count(AuditLog.id)).filter(
        AuditLog.event_type == 'login_failed'
    ).scalar() or 0
    
    failures_24h = db.query(func.count(AuditLog.id)).filter(
        AuditLog.event_type == 'login_failed',
        AuditLog.timestamp >= twenty_four_hours_ago
    ).scalar() or 0
    
    auth_failures = AuthFailureStats(
        total_failures=total_failures,
        failures_last_24h=failures_24h,
        top_failure_reasons=[]  # TODO: Aggregate failure reasons from metadata
    )
    
    return AdminDashboardResponse(
        total_users=total_users,
        active_users=active_users,
        total_chat_queries=total_chat,
        total_images_analyzed=total_imaging,
        total_vital_measurements=total_vitals,
        usage_trends=usage_trends,
        top_users=top_users,
        recent_registrations=recent_registrations,
        system_health=system_health,
        auth_failures=auth_failures
    )


@router.get("/analytics", response_model=dict)
async def get_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics and trends.
    
    Returns detailed system analytics for the specified time period.
    
    Requirements: 22.10
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all activities in time range
    activities = db.query(UserActivity).filter(
        UserActivity.timestamp >= start_date
    ).all()
    
    # Aggregate by type and date
    analytics = {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "total_activities": len(activities),
        "by_type": {
            "chat": sum(1 for a in activities if a.activity_type == 'chat'),
            "imaging": sum(1 for a in activities if a.activity_type == 'imaging'),
            "vitals": sum(1 for a in activities if a.activity_type == 'vitals')
        },
        "daily_breakdown": {}
    }
    
    # Daily breakdown
    for activity in activities:
        date_key = activity.timestamp.strftime('%Y-%m-%d')
        if date_key not in analytics["daily_breakdown"]:
            analytics["daily_breakdown"][date_key] = {
                "date": date_key,
                "chat": 0,
                "imaging": 0,
                "vitals": 0,
                "total": 0
            }
        
        analytics["daily_breakdown"][date_key][activity.activity_type] += 1
        analytics["daily_breakdown"][date_key]["total"] += 1
    
    return analytics
