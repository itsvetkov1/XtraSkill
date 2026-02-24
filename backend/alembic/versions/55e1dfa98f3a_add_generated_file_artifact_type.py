"""add_generated_file_artifact_type

Revision ID: 55e1dfa98f3a
Revises: e330b6621b90
Create Date: 2026-02-24 17:17:31.865383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55e1dfa98f3a'
down_revision: Union[str, Sequence[str], None] = 'e330b6621b90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add generated_file to ArtifactType enum.

    ArtifactType uses native_enum=False (VARCHAR storage in SQLite).
    Adding a new enum value only requires updating the Python enum class.
    This migration is a version checkpoint; no SQL DDL is needed for SQLite.
    PostgreSQL would require: ALTER TYPE artifacttype ADD VALUE 'generated_file'
    """
    pass  # No SQL change needed for SQLite (native_enum=False stores enum as VARCHAR)


def downgrade() -> None:
    """Remove generated_file from ArtifactType enum.

    ArtifactType uses native_enum=False (VARCHAR storage in SQLite).
    Removing enum values requires a data migration; skipped for SQLite.
    """
    pass  # Removing enum values requires data migration; skipped for SQLite
