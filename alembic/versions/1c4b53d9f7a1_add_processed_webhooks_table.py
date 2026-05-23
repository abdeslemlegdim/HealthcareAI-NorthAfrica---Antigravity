"""add_processed_webhooks_table

Create a dedicated idempotency table for processed Stripe webhooks.

Revision ID: 1c4b53d9f7a1
Revises: e5eec629d6a3
Create Date: 2026-05-22 23:29:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "1c4b53d9f7a1"
down_revision: Union[str, Sequence[str], None] = "e5eec629d6a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the current database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create processed_webhooks if it does not already exist."""
    if not table_exists("processed_webhooks"):
        op.create_table(
            "processed_webhooks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column(
                "processed_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stripe_event_id", name="uq_processed_webhooks_event_id"),
        )
        op.create_index(
            "ix_processed_webhooks_stripe_event_id",
            "processed_webhooks",
            ["stripe_event_id"],
            unique=True,
        )


def downgrade() -> None:
    """Drop processed_webhooks if it exists."""
    if table_exists("processed_webhooks"):
        op.drop_index("ix_processed_webhooks_stripe_event_id", table_name="processed_webhooks")
        op.drop_table("processed_webhooks")
