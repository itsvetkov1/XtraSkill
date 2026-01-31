"""add model_provider to threads

Revision ID: c07d77df9b74
Revises: daca512f660c
Create Date: 2026-01-31 17:02:16.067611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c07d77df9b74'
down_revision: Union[str, Sequence[str], None] = 'daca512f660c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add model_provider column to threads table
    # Existing threads will have NULL which defaults to 'anthropic' in application code
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(sa.Column('model_provider', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.drop_column('model_provider')
