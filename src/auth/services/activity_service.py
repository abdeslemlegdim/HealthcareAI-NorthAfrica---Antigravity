"""
Activity Service for user activity tracking and statistics.

This module provides functionality for recording user activities and generating
usage statistics, trends, health insights, and personalized quick links for the
enhanced user dashboard.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 8.1, 8.2, 8.3, 8.4, 8.5
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import Counter

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from src.auth.models import UserActivity, User


class ActivityService:
    """
    Service for tracking user activities and generating usage statistics.
    
    Handles activity recording, statistics aggregation, usage trends analysis,
    health insights generation, and personalized quick links.
    """
    
    def __init__(self, db: Session):
        """
        Initialize ActivityService.
        
        Args:
            db: Database session for activity storage and queries
        """
        self.db = db
    
    async def record_activity(
        self,
        user_id: int,
        activity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record user activity asynchronously.
        
        Records user interactions with the system for analytics and usage tracking.
        This method is designed to be non-blocking to avoid impacting endpoint
        response times.
        
        Args:
            user_id: User ID performing the activity
            activity_type: Type of activity ('chat', 'imaging', 'vitals')
            metadata: Optional additional activity metadata
        
        Requirements: 8.1, 8.2, 8.3, 8.5
        """
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            timestamp=datetime.utcnow(),
            metadata_=metadata
        )
        
        self.db.add(activity)
        
        # Update user's last_activity_at timestamp
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_activity_at = datetime.utcnow()
        
        self.db.commit()
    
    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve aggregated usage statistics for user.
        
        Returns comprehensive statistics including total counts, weekly/monthly
        counts, account age, and most active day.
        
        Args:
            user_id: User ID to retrieve statistics for
        
        Returns:
            Dictionary with usage statistics
        
        Requirements: 7.2, 7.3, 7.4, 7.5, 7.6
        """
        # Get user info
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Calculate account age
        account_age_days = (datetime.utcnow() - user.created_at).days
        
        # Get total counts by activity type
        total_chat = self.db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'chat'
        ).scalar() or 0
        
        total_imaging = self.db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'imaging'
        ).scalar() or 0
        
        total_vitals = self.db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'vitals'
        ).scalar() or 0
        
        # Get this week's activity count
        week_ago = datetime.utcnow() - timedelta(days=7)
        this_week_queries = self.db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == user_id,
            UserActivity.timestamp >= week_ago
        ).scalar() or 0
        
        # Get this month's activity count
        month_ago = datetime.utcnow() - timedelta(days=30)
        this_month_queries = self.db.query(func.count(UserActivity.id)).filter(
            UserActivity.user_id == user_id,
            UserActivity.timestamp >= month_ago
        ).scalar() or 0
        
        # Find most active day of week
        activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).all()
        
        day_counts = Counter(activity.timestamp.strftime('%A') for activity in activities)
        most_active_day = day_counts.most_common(1)[0][0] if day_counts else "N/A"
        
        return {
            "total_chat_queries": total_chat,
            "total_images_analyzed": total_imaging,
            "total_vital_measurements": total_vitals,
            "account_age_days": account_age_days,
            "last_login": user.last_activity_at or user.created_at,
            "this_week_queries": this_week_queries,
            "this_month_queries": this_month_queries,
            "most_active_day": most_active_day
        }
    
    async def get_recent_activities(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities for user.
        
        Returns the last N activities with timestamps and descriptions.
        
        Args:
            user_id: User ID to retrieve activities for
            limit: Maximum number of activities to return (default 10)
        
        Returns:
            List of activity summaries
        
        Requirements: 7.7
        """
        activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(UserActivity.timestamp.desc()).limit(limit).all()
        
        activity_summaries = []
        for activity in activities:
            # Generate human-readable description
            description = self._generate_activity_description(
                activity.activity_type,
                activity.metadata_
            )
            
            activity_summaries.append({
                "activity_type": activity.activity_type,
                "timestamp": activity.timestamp,
                "description": description,
                "metadata": activity.metadata_
            })
        
        return activity_summaries
    
    async def get_usage_trends(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage trends over time.
        
        Returns daily, weekly, and monthly aggregations of user activity.
        
        Args:
            user_id: User ID to analyze trends for
            days: Number of days to analyze (default 30)
        
        Returns:
            Dictionary with daily, weekly, and monthly usage trends
        
        Requirements: 7.8
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all activities in the time range
        activities = self.db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.timestamp >= start_date
        ).all()
        
        # Group by date
        daily_usage = {}
        for activity in activities:
            date_key = activity.timestamp.strftime('%Y-%m-%d')
            if date_key not in daily_usage:
                daily_usage[date_key] = {
                    "date": date_key,
                    "chat_count": 0,
                    "imaging_count": 0,
                    "vitals_count": 0
                }
            
            if activity.activity_type == 'chat':
                daily_usage[date_key]["chat_count"] += 1
            elif activity.activity_type == 'imaging':
                daily_usage[date_key]["imaging_count"] += 1
            elif activity.activity_type == 'vitals':
                daily_usage[date_key]["vitals_count"] += 1
        
        # Convert to sorted list
        daily_trends = sorted(daily_usage.values(), key=lambda x: x["date"])
        
        # Generate weekly trends (group by week)
        weekly_usage = {}
        for activity in activities:
            week_key = activity.timestamp.strftime('%Y-W%W')
            if week_key not in weekly_usage:
                weekly_usage[week_key] = {
                    "week": week_key,
                    "chat_count": 0,
                    "imaging_count": 0,
                    "vitals_count": 0
                }
            
            if activity.activity_type == 'chat':
                weekly_usage[week_key]["chat_count"] += 1
            elif activity.activity_type == 'imaging':
                weekly_usage[week_key]["imaging_count"] += 1
            elif activity.activity_type == 'vitals':
                weekly_usage[week_key]["vitals_count"] += 1
        
        weekly_trends = sorted(weekly_usage.values(), key=lambda x: x["week"])
        
        # Generate monthly trends (group by month)
        monthly_usage = {}
        for activity in activities:
            month_key = activity.timestamp.strftime('%Y-%m')
            if month_key not in monthly_usage:
                monthly_usage[month_key] = {
                    "month": month_key,
                    "chat_count": 0,
                    "imaging_count": 0,
                    "vitals_count": 0
                }
            
            if activity.activity_type == 'chat':
                monthly_usage[month_key]["chat_count"] += 1
            elif activity.activity_type == 'imaging':
                monthly_usage[month_key]["imaging_count"] += 1
            elif activity.activity_type == 'vitals':
                monthly_usage[month_key]["vitals_count"] += 1
        
        monthly_trends = sorted(monthly_usage.values(), key=lambda x: x["month"])
        
        return {
            "daily_usage": daily_trends,
            "weekly_usage": weekly_trends,
            "monthly_usage": monthly_trends
        }
    
    async def calculate_health_insights(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Calculate health insights and recommendations.
        
        Analyzes user activity patterns to generate engagement scores and
        personalized recommendations.
        
        Args:
            user_id: User ID to generate insights for
        
        Returns:
            Dictionary with health insights and recommendations
        
        Requirements: 7.9
        """
        # Get user statistics
        stats = await self.get_user_statistics(user_id)
        
        total_interactions = (
            stats.get("total_chat_queries", 0) +
            stats.get("total_images_analyzed", 0) +
            stats.get("total_vital_measurements", 0)
        )
        
        # Determine most used feature
        feature_counts = {
            "Chat": stats.get("total_chat_queries", 0),
            "Medical Imaging": stats.get("total_images_analyzed", 0),
            "Vital Signs": stats.get("total_vital_measurements", 0)
        }
        most_used_feature = max(feature_counts, key=feature_counts.get) if total_interactions > 0 else "None"
        
        # Calculate engagement score (0-100)
        # Based on activity frequency and diversity
        account_age_days = max(stats.get("account_age_days", 1), 1)
        activity_rate = total_interactions / account_age_days
        
        # Normalize to 0-100 scale (assuming 5 activities per day is excellent)
        engagement_score = min(100, (activity_rate / 5.0) * 100)
        
        # Calculate feature diversity (0-1)
        features_used = sum(1 for count in feature_counts.values() if count > 0)
        diversity_bonus = (features_used / 3.0) * 20  # Up to 20 points for using all features
        
        engagement_score = min(100, engagement_score + diversity_bonus)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            stats,
            feature_counts,
            engagement_score
        )
        
        return {
            "total_interactions": total_interactions,
            "most_used_feature": most_used_feature,
            "engagement_score": round(engagement_score, 1),
            "recommendations": recommendations
        }
    
    async def generate_quick_links(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized quick links based on usage patterns.
        
        Returns quick access links to frequently used features.
        
        Args:
            user_id: User ID to generate links for
        
        Returns:
            List of quick link objects
        
        Requirements: 7.10
        """
        stats = await self.get_user_statistics(user_id)
        
        quick_links = []
        
        # Add links based on usage
        if stats.get("total_chat_queries", 0) > 0:
            quick_links.append({
                "title": "Chat Assistant",
                "url": "/chat",
                "icon": "chat",
                "description": "Ask health-related questions"
            })
        
        if stats.get("total_images_analyzed", 0) > 0:
            quick_links.append({
                "title": "Medical Imaging",
                "url": "/imaging",
                "icon": "image",
                "description": "Analyze medical images"
            })
        
        if stats.get("total_vital_measurements", 0) > 0:
            quick_links.append({
                "title": "Vital Signs",
                "url": "/vitals",
                "icon": "heart",
                "description": "Record vital measurements"
            })
        
        # Add dashboard link
        quick_links.insert(0, {
            "title": "Dashboard",
            "url": "/dashboard",
            "icon": "dashboard",
            "description": "View your statistics"
        })
        
        # If user hasn't used a feature, suggest it
        if stats.get("total_chat_queries", 0) == 0:
            quick_links.append({
                "title": "Try Chat Assistant",
                "url": "/chat",
                "icon": "chat",
                "description": "Get started with AI health assistant"
            })
        
        if stats.get("total_images_analyzed", 0) == 0:
            quick_links.append({
                "title": "Try Medical Imaging",
                "url": "/imaging",
                "icon": "image",
                "description": "Analyze your first medical image"
            })
        
        return quick_links[:6]  # Limit to 6 quick links
    
    def _generate_activity_description(
        self,
        activity_type: str,
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate human-readable activity description.
        
        Args:
            activity_type: Type of activity
            metadata: Activity metadata
        
        Returns:
            Human-readable description string
        """
        descriptions = {
            "chat": "Asked a health question",
            "imaging": "Analyzed a medical image",
            "vitals": "Recorded vital signs"
        }
        
        base_description = descriptions.get(activity_type, "Performed an action")
        
        # Add metadata details if available
        if metadata:
            if activity_type == "chat" and "query" in metadata:
                query_preview = metadata["query"][:50]
                base_description = f"Asked: {query_preview}..."
            elif activity_type == "imaging" and "image_type" in metadata:
                base_description = f"Analyzed {metadata['image_type']} image"
            elif activity_type == "vitals" and "measurement_type" in metadata:
                base_description = f"Recorded {metadata['measurement_type']}"
        
        return base_description
    
    def _generate_recommendations(
        self,
        stats: Dict[str, Any],
        feature_counts: Dict[str, int],
        engagement_score: float
    ) -> List[str]:
        """
        Generate personalized recommendations.
        
        Args:
            stats: User statistics
            feature_counts: Feature usage counts
            engagement_score: Calculated engagement score
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Engagement-based recommendations
        if engagement_score < 30:
            recommendations.append("Try using the platform more regularly to get better health insights")
        elif engagement_score < 60:
            recommendations.append("You're doing well! Consider exploring more features")
        else:
            recommendations.append("Excellent engagement! Keep up the great work")
        
        # Feature diversity recommendations
        if feature_counts["Chat"] == 0:
            recommendations.append("Try the Chat Assistant to ask health-related questions")
        
        if feature_counts["Medical Imaging"] == 0:
            recommendations.append("Upload a medical image for AI-powered analysis")
        
        if feature_counts["Vital Signs"] == 0:
            recommendations.append("Record your vital signs to track your health over time")
        
        # Activity frequency recommendations
        this_week = stats.get("this_week_queries", 0)
        if this_week == 0:
            recommendations.append("You haven't been active this week. Check in with your health!")
        elif this_week < 3:
            recommendations.append("Consider checking your health metrics more frequently")
        
        return recommendations[:5]  # Limit to 5 recommendations
