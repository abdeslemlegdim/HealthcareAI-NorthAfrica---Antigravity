"""add_user_id_to_existing_tables

This migration adds user_id foreign key columns to existing feature tables
to enable user-specific tracking and association of activities.

The migration checks if each table exists before attempting to add the column,
making it safe to run even if the tables haven't been created yet.

Tables affected (if they exist):
- chat_history: Stores chat conversation history
- image_analyses: Stores medical image analysis results
- vital_measurements: Stores vital sign measurements

Requirements: 20.4

Revision ID: e5eec629d6a3
Revises: f22a27a1a5b4
Create Date: 2026-05-11 17:27:49.237196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e5eec629d6a3'
down_revision: Union[str, Sequence[str], None] = 'f22a27a1a5b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """
    Add user_id columns to existing tables if they exist.
    
    For each table (chat_history, image_analyses, vital_measurements):
    1. Check if the table exists
    2. Check if user_id column doesn't already exist
    3. Add nullable user_id column with foreign key to users.id
    4. Add index on user_id for query performance
    
    Note: Uses batch mode for SQLite compatibility.
    """
    tables_to_update = [
        'chat_history',
        'image_analyses', 
        'vital_measurements'
    ]
    
    for table_name in tables_to_update:
        if table_exists(table_name):
            # Check if user_id column already exists
            if not column_exists(table_name, 'user_id'):
                # Use batch mode for SQLite compatibility
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    # Add user_id column (nullable to support existing data)
                    batch_op.add_column(
                        sa.Column('user_id', sa.Integer(), nullable=True)
                    )
                    
                    # Add foreign key constraint to users table
                    batch_op.create_foreign_key(
                        f'fk_{table_name}_user_id',
                        'users',
                        ['user_id'],
                        ['id'],
                        ondelete='SET NULL'  # Set to NULL if user is deleted
                    )
                    
                    # Add index for query performance
                    batch_op.create_index(
                        f'ix_{table_name}_user_id',
                        ['user_id']
                    )
                
                print(f"Added user_id column to {table_name}")
            else:
                print(f"Column user_id already exists in {table_name}, skipping")
        else:
            print(f"Table {table_name} does not exist, skipping")


def downgrade() -> None:
    """
    Remove user_id columns from tables if they exist.
    
    This reverses the upgrade operation by:
    1. Dropping the index on user_id
    2. Dropping the foreign key constraint
    3. Dropping the user_id column
    
    Note: Uses batch mode for SQLite compatibility.
    """
    tables_to_update = [
        'chat_history',
        'image_analyses',
        'vital_measurements'
    ]
    
    for table_name in tables_to_update:
        if table_exists(table_name):
            if column_exists(table_name, 'user_id'):
                # Use batch mode for SQLite compatibility
                with op.batch_alter_table(table_name, schema=None) as batch_op:
                    # Drop index
                    batch_op.drop_index(f'ix_{table_name}_user_id')
                    
                    # Drop foreign key constraint
                    batch_op.drop_constraint(
                        f'fk_{table_name}_user_id',
                        type_='foreignkey'
                    )
                    
                    # Drop column
                    batch_op.drop_column('user_id')
                
                print(f"Removed user_id column from {table_name}")
            else:
                print(f"Column user_id does not exist in {table_name}, skipping")
        else:
            print(f"Table {table_name} does not exist, skipping")
