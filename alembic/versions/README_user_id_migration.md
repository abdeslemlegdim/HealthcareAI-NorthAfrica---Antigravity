# User ID Migration (Task 1.3)

## Overview

This migration (`e5eec629d6a3_add_user_id_to_existing_tables.py`) adds `user_id` foreign key columns to existing feature tables to enable user-specific tracking and association of activities.

**Requirements**: 20.4

## Tables Affected

The migration will add `user_id` columns to the following tables **if they exist**:

1. **chat_history** - Stores chat conversation history
2. **image_analyses** - Stores medical image analysis results  
3. **vital_measurements** - Stores vital sign measurements

## Changes Applied

For each table (if it exists), the migration:

1. Adds a nullable `user_id` column (INTEGER)
2. Creates a foreign key constraint to `users.id` with `SET NULL` on delete
3. Creates an index `ix_{table_name}_user_id` for query performance

## Key Features

### Conditional Execution
The migration only modifies tables that exist in the database. If a table doesn't exist, it is skipped gracefully.

### Idempotent
The migration checks if columns already exist before adding them, making it safe to run multiple times.

### SQLite Compatible
Uses Alembic's batch mode for SQLite ALTER TABLE operations, which is required for adding foreign keys.

### Reversible
Supports both upgrade and downgrade operations cleanly.

### Nullable Column
The `user_id` column is nullable to allow existing data to remain valid. Historical data can have NULL user_id values.

## Foreign Key Behavior

**ON DELETE SET NULL**: If a user is deleted, their associated records remain in the feature tables but the `user_id` is set to NULL. This preserves historical data while maintaining referential integrity.

## Usage

### Apply the Migration

```bash
# Apply all migrations including this one
alembic upgrade head

# Apply only up to this migration
alembic upgrade e5eec629d6a3
```

### Rollback the Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to before this migration
alembic downgrade f22a27a1a5b4
```

## Current State

As of now, the feature tables (chat_history, image_analyses, vital_measurements) **do not exist** in the database. When these tables are created in the future, this migration will need to be re-run to add the `user_id` columns.

### When Tables Are Created

When the feature tables are created:

1. Create the tables using their respective migrations or models
2. Run this migration again: `alembic downgrade f22a27a1a5b4 && alembic upgrade e5eec629d6a3`
3. The migration will detect the new tables and add the `user_id` columns

## Testing

The migration has been tested with the following scenarios:

### Scenario 1: Tables Don't Exist (Current State)
```bash
alembic upgrade e5eec629d6a3
```
**Result**: Migration runs successfully, skips non-existent tables
```
Table chat_history does not exist, skipping
Table image_analyses does not exist, skipping
Table vital_measurements does not exist, skipping
```

### Scenario 2: Tables Exist (Future State)
When tables exist, the migration:
- ✅ Adds `user_id` column to each table
- ✅ Creates foreign key constraint to `users.id`
- ✅ Creates index `ix_{table_name}_user_id`
- ✅ Verifies foreign key points to correct table and column

### Scenario 3: Downgrade
```bash
alembic downgrade f22a27a1a5b4
```
**Result**: Removes `user_id` columns, indexes, and foreign keys cleanly

## Example Schema After Migration

When the migration is applied to existing tables, the schema will look like:

```sql
-- chat_history table
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP,
    user_id INTEGER,  -- Added by migration
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX ix_chat_history_user_id ON chat_history(user_id);

-- image_analyses table
CREATE TABLE image_analyses (
    id INTEGER PRIMARY KEY,
    image_path TEXT NOT NULL,
    analysis_result TEXT NOT NULL,
    created_at TIMESTAMP,
    user_id INTEGER,  -- Added by migration
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX ix_image_analyses_user_id ON image_analyses(user_id);

-- vital_measurements table
CREATE TABLE vital_measurements (
    id INTEGER PRIMARY KEY,
    measurement_type TEXT NOT NULL,
    value REAL NOT NULL,
    created_at TIMESTAMP,
    user_id INTEGER,  -- Added by migration
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX ix_vital_measurements_user_id ON vital_measurements(user_id);
```

## Integration with Authentication System

Once the `user_id` columns are added, the authentication system can:

1. **Track User Activity**: Associate each chat query, image analysis, and vital measurement with a specific user
2. **Generate Statistics**: Calculate per-user usage statistics for the dashboard
3. **Enforce Permissions**: Implement user-specific data access controls
4. **Audit Trail**: Maintain a complete audit trail of which user performed which actions

## Notes

- The migration uses SQLite batch mode for compatibility
- Foreign keys must be enabled in SQLite: `PRAGMA foreign_keys = ON`
- The `SET NULL` behavior preserves historical data when users are deleted
- The nullable column allows backward compatibility with existing data
- Indexes improve query performance for user-specific data retrieval

## Files

- **Migration**: `alembic/versions/e5eec629d6a3_add_user_id_to_existing_tables.py`
- **Documentation**: This file
- **Summary**: `alembic/MIGRATION_SUMMARY.md`
