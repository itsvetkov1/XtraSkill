"""Add FTS5 virtual table for document search

Revision ID: daca512f660c
Revises: 4c40ac075452
Create Date: 2026-01-18 14:10:59.312941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daca512f660c'
down_revision: Union[str, Sequence[str], None] = '4c40ac075452'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create FTS5 virtual table for document full-text search
    op.execute("""
        CREATE VIRTUAL TABLE document_fts USING fts5(
            document_id UNINDEXED,
            filename,
            content,
            tokenize = 'porter ascii'
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop FTS5 virtual table
    op.execute("DROP TABLE document_fts")
