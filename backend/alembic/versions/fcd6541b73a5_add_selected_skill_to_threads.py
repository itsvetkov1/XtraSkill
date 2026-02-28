"""add selected_skill to threads

Revision ID: fcd6541b73a5
Revises: 55e1dfa98f3a
Create Date: 2026-02-28 23:55:44.462284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcd6541b73a5'
down_revision: Union[str, Sequence[str], None] = '55e1dfa98f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add selected_skill column to threads table (SKILL-001)."""
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('selected_skill', sa.String(length=100), nullable=True)
        )
        batch_op.create_index(
            batch_op.f('ix_threads_selected_skill'), 
            ['selected_skill'], 
            unique=False
        )


def downgrade() -> None:
    """Remove selected_skill column from threads table."""
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_threads_selected_skill'))
        batch_op.drop_column('selected_skill')
