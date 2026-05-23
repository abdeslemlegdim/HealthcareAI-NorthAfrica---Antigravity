"""
Tests for Alembic database migrations.

This module tests that the authentication schema migration works correctly.

Requirements: 9.4, 9.5, 9.6, 9.7, 9.8, 9.9
"""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import tempfile
import os


@pytest.fixture
def temp_db():
    """Create a temporary database for testing migrations."""
    # Create a temporary file for the database
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_url = f"sqlite:///{path}"
    yield db_url
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def alembic_config(temp_db):
    """Create Alembic configuration for testing."""
    config = Config("alembic.ini")
    # We need to override the database URL in the env.py context
    # by setting it in the config attributes
    config.attributes['connection_string'] = temp_db
    return config


def test_migration_upgrade(alembic_config, temp_db):
    """Test that the migration upgrade creates all required tables."""
    # Apply migrations
    command.upgrade(alembic_config, "head")
    
    # Connect to the database
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    
    # Check that all tables were created
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "refresh_tokens" in tables
    assert "user_activities" in tables
    assert "audit_logs" in tables
    assert "alembic_version" in tables


def test_users_table_schema(alembic_config, temp_db):
    """Test that the users table has the correct schema."""
    command.upgrade(alembic_config, "head")
    
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    
    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('users')}
    assert 'id' in columns
    assert 'email' in columns
    assert 'password_hash' in columns
    assert 'is_admin' in columns
    assert 'is_active' in columns
    assert 'created_at' in columns
    assert 'updated_at' in columns
    assert 'last_activity_at' in columns
    assert 'deleted_at' in columns
    
    # Check indexes
    indexes = {idx['name']: idx for idx in inspector.get_indexes('users')}
    assert 'ix_users_email' in indexes
    assert 'ix_users_is_admin' in indexes
    assert 'ix_users_is_active' in indexes
    # SQLite returns 1 for unique, not True
    assert indexes['ix_users_email']['unique'] == 1 or indexes['ix_users_email']['unique'] is True


def test_refresh_tokens_table_schema(alembic_config, temp_db):
    """Test that the refresh_tokens table has the correct schema."""
    command.upgrade(alembic_config, "head")
    
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    
    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('refresh_tokens')}
    assert 'id' in columns
    assert 'user_id' in columns
    assert 'token_hash' in columns
    assert 'created_at' in columns
    assert 'expires_at' in columns
    assert 'revoked_at' in columns
    assert 'device_info' in columns
    assert 'ip_address' in columns
    
    # Check indexes
    indexes = {idx['name']: idx for idx in inspector.get_indexes('refresh_tokens')}
    assert 'ix_refresh_tokens_token_hash' in indexes
    assert 'ix_refresh_tokens_user_id' in indexes
    
    # Check foreign keys
    foreign_keys = inspector.get_foreign_keys('refresh_tokens')
    assert len(foreign_keys) == 1
    assert foreign_keys[0]['referred_table'] == 'users'
    assert foreign_keys[0]['constrained_columns'] == ['user_id']
    assert foreign_keys[0]['options']['ondelete'] == 'CASCADE'


def test_user_activities_table_schema(alembic_config, temp_db):
    """Test that the user_activities table has the correct schema."""
    command.upgrade(alembic_config, "head")
    
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    
    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('user_activities')}
    assert 'id' in columns
    assert 'user_id' in columns
    assert 'activity_type' in columns
    assert 'timestamp' in columns
    assert 'metadata' in columns
    
    # Check indexes
    indexes = {idx['name']: idx for idx in inspector.get_indexes('user_activities')}
    assert 'ix_user_activities_activity_type' in indexes
    assert 'ix_user_activities_timestamp' in indexes
    assert 'ix_user_activities_user_id' in indexes
    assert 'idx_user_activities_user_timestamp' in indexes
    
    # Check foreign keys
    foreign_keys = inspector.get_foreign_keys('user_activities')
    assert len(foreign_keys) == 1
    assert foreign_keys[0]['referred_table'] == 'users'
    assert foreign_keys[0]['constrained_columns'] == ['user_id']
    assert foreign_keys[0]['options']['ondelete'] == 'CASCADE'


def test_audit_logs_table_schema(alembic_config, temp_db):
    """Test that the audit_logs table has the correct schema."""
    command.upgrade(alembic_config, "head")
    
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    
    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('audit_logs')}
    assert 'id' in columns
    assert 'event_type' in columns
    assert 'user_id' in columns
    assert 'email' in columns
    assert 'ip_address' in columns
    assert 'user_agent' in columns
    assert 'timestamp' in columns
    assert 'metadata' in columns
    
    # Check indexes
    indexes = {idx['name']: idx for idx in inspector.get_indexes('audit_logs')}
    assert 'ix_audit_logs_event_type' in indexes
    assert 'ix_audit_logs_user_id' in indexes
    assert 'ix_audit_logs_timestamp' in indexes
    assert 'idx_audit_logs_event_timestamp' in indexes
    assert 'idx_audit_logs_user_timestamp' in indexes


def test_migration_downgrade(alembic_config, temp_db):
    """Test that the migration downgrade removes all tables."""
    # Apply migrations
    command.upgrade(alembic_config, "head")
    
    # Verify tables exist
    engine = create_engine(temp_db)
    inspector = inspect(engine)
    tables_before = inspector.get_table_names()
    assert "users" in tables_before
    
    # Downgrade
    command.downgrade(alembic_config, "base")
    
    # Verify tables are removed
    inspector = inspect(engine)
    tables_after = inspector.get_table_names()
    assert "users" not in tables_after
    assert "refresh_tokens" not in tables_after
    assert "user_activities" not in tables_after
    assert "audit_logs" not in tables_after


def test_cascade_delete(alembic_config, temp_db):
    """Test that CASCADE delete works correctly."""
    command.upgrade(alembic_config, "head")
    
    engine = create_engine(temp_db)
    
    # Enable foreign key support in SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Enable foreign keys for this session
        session.execute(text("PRAGMA foreign_keys = ON"))
        
        # Insert a user
        session.execute(text("""
            INSERT INTO users (email, password_hash, is_admin, is_active, created_at, updated_at)
            VALUES ('test@example.com', 'hash123', 0, 1, datetime('now'), datetime('now'))
        """))
        session.commit()
        
        # Get user id
        result = session.execute(text("SELECT id FROM users WHERE email = 'test@example.com'"))
        user_id = result.scalar()
        
        # Insert related records
        session.execute(text(f"""
            INSERT INTO refresh_tokens (user_id, token_hash, created_at, expires_at)
            VALUES ({user_id}, 'token123', datetime('now'), datetime('now', '+1 day'))
        """))
        session.execute(text(f"""
            INSERT INTO user_activities (user_id, activity_type, timestamp)
            VALUES ({user_id}, 'login', datetime('now'))
        """))
        session.commit()
        
        # Verify records exist
        result = session.execute(text(f"SELECT COUNT(*) FROM refresh_tokens WHERE user_id = {user_id}"))
        assert result.scalar() == 1
        result = session.execute(text(f"SELECT COUNT(*) FROM user_activities WHERE user_id = {user_id}"))
        assert result.scalar() == 1
        
        # Delete user
        session.execute(text(f"DELETE FROM users WHERE id = {user_id}"))
        session.commit()
        
        # Verify related records were deleted (CASCADE)
        result = session.execute(text(f"SELECT COUNT(*) FROM refresh_tokens WHERE user_id = {user_id}"))
        assert result.scalar() == 0
        result = session.execute(text(f"SELECT COUNT(*) FROM user_activities WHERE user_id = {user_id}"))
        assert result.scalar() == 0
        
    finally:
        session.close()
