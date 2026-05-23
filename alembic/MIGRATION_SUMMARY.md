# Alembic Migration Summary

## Overview
This document tracks all Alembic migrations for the Healthcare AI Assistant authentication system.

## Migrations

### Migration 1: Create Authentication Schema
**Migration ID**: `f22a27a1a5b4`
**Task**: 1.2
**Description**: Create authentication schema

The migration creates four tables:

#### users
- Columns: id, email, password_hash, is_admin, is_active, created_at, updated_at, last_activity_at, deleted_at
- Indexes: email (unique), id, is_admin, is_active
- Purpose: User accounts with authentication credentials

#### refresh_tokens
- Columns: id, user_id, token_hash, created_at, expires_at, revoked_at, device_info, ip_address
- Indexes: id, token_hash, user_id
- Foreign Key: user_id → users.id (CASCADE delete)
- Purpose: JWT refresh tokens for session management

#### user_activities
- Columns: id, user_id, activity_type, timestamp, metadata
- Indexes: id, user_id, activity_type, timestamp, (user_id, timestamp) composite
- Foreign Key: user_id → users.id (CASCADE delete)
- Purpose: User activity tracking for usage statistics

#### audit_logs
- Columns: id, event_type, user_id, email, ip_address, user_agent, timestamp, metadata
- Indexes: id, event_type, user_id, timestamp, (event_type, timestamp) composite, (user_id, timestamp) composite
- Purpose: Comprehensive audit logging for HIPAA compliance

**Requirements Satisfied**: 9.4, 9.5, 9.6, 9.7, 9.8, 9.9

---

### Migration 2: Add user_id to Existing Tables
**Migration ID**: `e5eec629d6a3`
**Task**: 1.3
**Description**: Add user_id columns to existing tables

This migration adds user_id foreign key columns to existing feature tables to enable user-specific tracking and association of activities.

#### Tables Affected (if they exist)
- **chat_history**: Stores chat conversation history
- **image_analyses**: Stores medical image analysis results
- **vital_measurements**: Stores vital sign measurements

#### Changes Applied
For each table (if it exists):
1. Adds nullable `user_id` column (INTEGER)
2. Creates foreign key constraint to `users.id` with `SET NULL` on delete
3. Creates index `ix_{table_name}_user_id` for query performance

#### Key Features
- **Conditional Execution**: Only modifies tables that exist in the database
- **Idempotent**: Checks if columns already exist before adding them
- **SQLite Compatible**: Uses batch mode for SQLite ALTER TABLE operations
- **Reversible**: Supports both upgrade and downgrade operations
- **Nullable Column**: Allows existing data to remain valid (user_id can be NULL for historical data)

#### Foreign Key Behavior
- **ON DELETE SET NULL**: If a user is deleted, their associated records remain but user_id is set to NULL
- This preserves historical data while maintaining referential integrity

**Requirements Satisfied**: 20.4

**Testing**: 
- Created comprehensive test script (`test_user_id_migration.py`)
- Verified migration works correctly when tables exist
- Verified migration skips gracefully when tables don't exist
- Verified indexes and foreign keys are created correctly
- Verified downgrade removes all changes cleanly

---

## Alembic Setup

### Configuration
- **Config File**: `alembic.ini`
- **Environment**: `alembic/env.py`
- **Database**: SQLite (configured via `src/utils/config.py`)

### Usage

#### Check Current Migration Status
```bash
alembic current
```

#### View Migration History
```bash
alembic history
```

#### Apply All Migrations
```bash
alembic upgrade head
```

#### Apply Specific Migration
```bash
alembic upgrade <revision_id>
```

#### Rollback One Migration
```bash
alembic downgrade -1
```

#### Rollback to Specific Migration
```bash
alembic downgrade <revision_id>
```

#### Create New Migration
```bash
alembic revision -m "description"
```

#### Auto-generate Migration from Models
```bash
alembic revision --autogenerate -m "description"
```

## Database Verification

### Check Tables
```python
from sqlalchemy import create_engine, inspect
from src.utils.config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

# List all tables
print(inspector.get_table_names())

# Check columns for a table
print([col['name'] for col in inspector.get_columns('users')])

# Check indexes for a table
print([idx['name'] for idx in inspector.get_indexes('users')])

# Check foreign keys
print(inspector.get_foreign_keys('refresh_tokens'))
```

## Notes
- SQLite requires `PRAGMA foreign_keys = ON` to enable CASCADE delete
- All migrations are reversible (support both upgrade and downgrade)
- All indexes are properly created for query performance
- Foreign key constraints ensure referential integrity
- Batch mode is used for SQLite compatibility with ALTER TABLE operations
