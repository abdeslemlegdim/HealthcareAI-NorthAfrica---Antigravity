# Alembic Database Migrations

This directory contains Alembic database migrations for the Healthcare AI application.

## Overview

Alembic is a database migration tool for SQLAlchemy. It allows you to:
- Track database schema changes over time
- Apply schema changes to databases
- Rollback changes if needed
- Generate migrations automatically from model changes

## Configuration

The Alembic configuration is set up to:
- Use the `DATABASE_URL` from `src/utils/config.py`
- Auto-detect models from `src/auth/models.py`
- Store migration scripts in `alembic/versions/`

## Common Commands

### Check current migration status
```bash
alembic current
```

### View migration history
```bash
alembic history
```

### Apply all pending migrations
```bash
alembic upgrade head
```

### Rollback one migration
```bash
alembic downgrade -1
```

### Rollback to a specific revision
```bash
alembic downgrade <revision_id>
```

### Generate a new migration (auto-detect changes)
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create an empty migration (manual)
```bash
alembic revision -m "Description of changes"
```

## Existing Migrations

### f22a27a1a5b4 - Create authentication schema
Creates the initial authentication database schema including:
- `users` table: User accounts with authentication credentials
- `refresh_tokens` table: JWT refresh tokens for session management
- `user_activities` table: User activity tracking for usage statistics
- `audit_logs` table: Comprehensive audit logging for HIPAA compliance

All tables include appropriate indexes for performance and foreign key constraints with CASCADE delete for referential integrity.

**Requirements**: 9.4, 9.5, 9.6, 9.7, 9.8, 9.9

## Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Test migrations** on a development database first
3. **Backup production databases** before applying migrations
4. **Never edit applied migrations** - create a new migration instead
5. **Keep migrations small and focused** on a single change
6. **Add descriptive comments** to complex migrations

## Troubleshooting

### Migration fails to apply
- Check the database connection in `.env`
- Verify the database user has sufficient permissions
- Review the migration script for errors

### Auto-generate doesn't detect changes
- Ensure models are imported in `alembic/env.py`
- Check that `target_metadata` is set correctly
- Verify SQLAlchemy models are properly defined

### Database out of sync
```bash
# Check current state
alembic current

# Stamp database with current revision (use with caution)
alembic stamp head
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
