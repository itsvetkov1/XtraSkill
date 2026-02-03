"""add conversation_mode to threads

Revision ID: b4ef9fb543d5
Revises: c07d77df9b74
Create Date: 2026-02-03 22:02:29.539169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4ef9fb543d5'
down_revision: Union[str, Sequence[str], None] = 'c07d77df9b74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add conversation_mode column to threads table.

    Per PITFALL-07: Mode is a thread property (not global preference).
    Each thread remembers its mode so users see the same mode after app restart.
    Valid modes: 'meeting', 'document_refinement' (enforced at API level, not DB)
    """
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('conversation_mode', sa.String(length=50), nullable=True)
        )


def downgrade() -> None:
    """Remove conversation_mode column from threads table."""
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.drop_column('conversation_mode')
