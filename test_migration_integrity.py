"""
Test script to verify database migration integrity.
Tests that all tables, indexes, and foreign keys work correctly.
"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def test_database_integrity():
    """Test database integrity by inserting and querying data."""
    db_path = Path("healthcare_ai.db")
    conn = sqlite3.connect(str(db_path))
    
    # IMPORTANT: Enable foreign key constraints for SQLite
    conn.execute("PRAGMA foreign_keys = ON")
    
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE INTEGRITY TESTS")
    print("=" * 60)
    
    # Check if foreign keys are enabled
    cursor.execute("PRAGMA foreign_keys")
    fk_status = cursor.fetchone()[0]
    print(f"\nForeign keys enabled: {bool(fk_status)}")
    
    try:
        # Test 1: Insert a user
        print("\n✓ Test 1: Insert user")
        cursor.execute("""
            INSERT INTO users (email, password_hash, is_admin, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "test@example.com",
            "hashed_password_123",
            False,
            True,
            datetime.now(),
            datetime.now()
        ))
        user_id = cursor.lastrowid
        print(f"  Created user with ID: {user_id}")
        
        # Test 2: Insert refresh token with foreign key
        print("\n✓ Test 2: Insert refresh token (tests foreign key)")
        cursor.execute("""
            INSERT INTO refresh_tokens (user_id, token_hash, created_at, expires_at, device_info, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "token_hash_abc123",
            datetime.now(),
            datetime.now() + timedelta(days=7),
            "Mozilla/5.0",
            "192.168.1.1"
        ))
        token_id = cursor.lastrowid
        print(f"  Created refresh token with ID: {token_id}")
        
        # Test 3: Insert user activity
        print("\n✓ Test 3: Insert user activity")
        cursor.execute("""
            INSERT INTO user_activities (user_id, activity_type, timestamp, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            "login",
            datetime.now(),
            '{"ip": "192.168.1.1", "device": "Chrome"}'
        ))
        activity_id = cursor.lastrowid
        print(f"  Created activity with ID: {activity_id}")
        
        # Test 4: Insert audit log
        print("\n✓ Test 4: Insert audit log")
        cursor.execute("""
            INSERT INTO audit_logs (event_type, user_id, email, ip_address, user_agent, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "user_login",
            user_id,
            "test@example.com",
            "192.168.1.1",
            "Mozilla/5.0",
            datetime.now(),
            '{"success": true}'
        ))
        log_id = cursor.lastrowid
        print(f"  Created audit log with ID: {log_id}")
        
        # Test 5: Query with indexes
        print("\n✓ Test 5: Query using indexes")
        
        # Query by email (unique index)
        cursor.execute("SELECT id, email FROM users WHERE email = ?", ("test@example.com",))
        result = cursor.fetchone()
        print(f"  Found user by email: {result}")
        
        # Query by user_id in refresh_tokens (indexed)
        cursor.execute("SELECT COUNT(*) FROM refresh_tokens WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        print(f"  Found {count} refresh token(s) for user")
        
        # Query by activity_type (indexed)
        cursor.execute("SELECT COUNT(*) FROM user_activities WHERE activity_type = ?", ("login",))
        count = cursor.fetchone()[0]
        print(f"  Found {count} login activity(ies)")
        
        # Query by event_type (indexed)
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE event_type = ?", ("user_login",))
        count = cursor.fetchone()[0]
        print(f"  Found {count} user_login audit log(s)")
        
        # Test 6: Test CASCADE delete
        print("\n✓ Test 6: Test CASCADE delete on foreign keys")
        
        # Count related records before delete
        cursor.execute("SELECT COUNT(*) FROM refresh_tokens WHERE user_id = ?", (user_id,))
        tokens_before = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_activities WHERE user_id = ?", (user_id,))
        activities_before = cursor.fetchone()[0]
        
        print(f"  Before delete: {tokens_before} token(s), {activities_before} activity(ies)")
        
        # Delete user (should cascade to refresh_tokens and user_activities)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        # Count related records after delete
        cursor.execute("SELECT COUNT(*) FROM refresh_tokens WHERE user_id = ?", (user_id,))
        tokens_after = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM user_activities WHERE user_id = ?", (user_id,))
        activities_after = cursor.fetchone()[0]
        
        print(f"  After delete: {tokens_after} token(s), {activities_after} activity(ies)")
        
        if tokens_after == 0 and activities_after == 0:
            print("  ✓ CASCADE delete working correctly!")
        else:
            print("  ✗ CASCADE delete failed!")
            return False
        
        # Clean up audit logs (no foreign key constraint)
        cursor.execute("DELETE FROM audit_logs WHERE user_id = ?", (user_id,))
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    test_database_integrity()
