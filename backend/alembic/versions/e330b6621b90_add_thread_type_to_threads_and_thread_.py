"""add thread_type to threads and thread_id to documents

Revision ID: e330b6621b90
Revises: b4ef9fb543d5
Create Date: 2026-02-17 11:50:33.584773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e330b6621b90'
down_revision: Union[str, Sequence[str], None] = 'b4ef9fb543d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add thread_type discriminator and thread-scoped documents support.

    Thread_type uses 3-step pattern:
    1. Add as nullable with server_default
    2. Backfill existing threads
    3. Make NOT NULL after backfill

    This ensures backward compatibility with existing data.
    """
    # Step 1: Add thread_type as nullable with server_default
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('thread_type', sa.String(length=20),
                      nullable=True,
                      server_default='ba_assistant')
        )

    # Step 2: Backfill existing threads
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE threads SET thread_type = 'ba_assistant' WHERE thread_type IS NULL")
    )

    # Step 3: Make NOT NULL after backfill
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.alter_column('thread_type', nullable=False)

    # Document model changes: make project_id nullable and add thread_id
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.alter_column('project_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=True)
        batch_op.add_column(sa.Column('thread_id', sa.String(length=36), nullable=True))
        batch_op.create_index(batch_op.f('ix_documents_thread_id'), ['thread_id'], unique=False)
        batch_op.create_foreign_key('fk_documents_thread_id', 'threads', ['thread_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Reverse thread_type and thread-scoped documents changes."""
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_documents_thread_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_documents_thread_id'))
        batch_op.drop_column('thread_id')
        batch_op.alter_column('project_id',
               existing_type=sa.VARCHAR(length=36),
               nullable=False)

    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.drop_column('thread_type')
