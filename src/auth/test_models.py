"""
Test script to verify SQLAlchemy models are correctly defined.

This script creates an in-memory SQLite database and tests the models.
"""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.models import Base, User, RefreshToken, UserActivity, AuditLog


def test_models():
    """Test that all models can be created and used correctly."""
    
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Test User model
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            is_admin=False,
            is_active=True
        )
        session.add(user)
        session.commit()
        
        print(f"✓ Created user: {user}")
        
        # Test RefreshToken model
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash="token_hash_value",
            expires_at=datetime.utcnow() + timedelta(days=7),
            device_info="Test Device",
            ip_address="127.0.0.1"
        )
        session.add(refresh_token)
        session.commit()
        
        print(f"✓ Created refresh token: {refresh_token}")
        
        # Test UserActivity model
        activity = UserActivity(
            user_id=user.id,
            activity_type="chat",
            metadata_={"query": "test query"}
        )
        session.add(activity)
        session.commit()
        
        print(f"✓ Created user activity: {activity}")
        
        # Test AuditLog model
        audit_log = AuditLog(
            event_type="login",
            user_id=user.id,
            email=user.email,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            metadata_={"success": True}
        )
        session.add(audit_log)
        session.commit()
        
        print(f"✓ Created audit log: {audit_log}")
        
        # Test relationships
        user_with_relations = session.query(User).filter_by(email="test@example.com").first()
        print(f"\n✓ User has {len(user_with_relations.refresh_tokens)} refresh token(s)")
        print(f"✓ User has {len(user_with_relations.activities)} activity record(s)")
        
        # Test cascade delete
        session.delete(user)
        session.commit()
        
        # Verify cascade delete worked
        remaining_tokens = session.query(RefreshToken).count()
        remaining_activities = session.query(UserActivity).count()
        
        print(f"\n✓ After deleting user:")
        print(f"  - Remaining refresh tokens: {remaining_tokens} (should be 0)")
        print(f"  - Remaining activities: {remaining_activities} (should be 0)")
        
        if remaining_tokens == 0 and remaining_activities == 0:
            print("\n✓ Cascade delete working correctly!")
        
        print("\n✓ All model tests passed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    test_models()
