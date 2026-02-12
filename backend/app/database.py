"""
Database connection and session management.

Supports both SQLite (MVP) and PostgreSQL (production) via connection string.
Uses async SQLAlchemy for non-blocking database operations with FastAPI.
"""

import os
import re
import time
from contextvars import ContextVar
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base
from app.services.logging_service import get_logging_service
from app.middleware.logging_middleware import get_correlation_id


# Context variable for query timing (async-safe, query-scoped)
_query_start_time: ContextVar[float] = ContextVar('query_start_time', default=0.0)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Enable foreign key constraints for SQLite.

    CRITICAL: SQLite disables foreign keys by default for backwards compatibility.
    Without this, cascade deletes won't work and orphaned records will accumulate.

    This listener executes on every new database connection.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Get database URL from environment variable
# Default to SQLite for local development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./ba_assistant.db"
)

# Create async engine
# echo=True enables SQL logging for development (disable in production)
engine = create_async_engine(
    DATABASE_URL,
    echo=(settings.environment != "production"),
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Database operation logging event listeners
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time before execution."""
    _query_start_time.set(time.perf_counter())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Log database operation after execution with timing.

    Logs at DEBUG level to avoid excessive volume in production.
    Skips PRAGMA statements (SQLite metadata queries) to reduce noise.
    """
    # Calculate query duration
    start_time = _query_start_time.get()
    duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0

    # Skip PRAGMA statements (SQLite metadata)
    if statement.strip().upper().startswith('PRAGMA'):
        return

    # Extract table name and operation type from SQL
    statement_upper = statement.strip().upper()
    operation = 'UNKNOWN'
    table = 'unknown'

    # Parse operation type
    if statement_upper.startswith('SELECT'):
        operation = 'SELECT'
    elif statement_upper.startswith('INSERT'):
        operation = 'INSERT'
    elif statement_upper.startswith('UPDATE'):
        operation = 'UPDATE'
    elif statement_upper.startswith('DELETE'):
        operation = 'DELETE'

    # Extract table name using regex (basic pattern)
    # Matches: FROM/INTO/UPDATE <table_name>
    table_match = re.search(
        r'(?:FROM|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        statement_upper
    )
    if table_match:
        table = table_match.group(1).lower()

    # Log database operation
    logging_service = get_logging_service()
    correlation_id = get_correlation_id()

    logging_service.log(
        'DEBUG',
        f'DB {operation} {table}',
        'db',
        correlation_id=correlation_id,
        operation=operation,
        table=table,
        duration_ms=round(duration_ms, 2),
        db_event='query'
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database session.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables.

    This should be called on application startup.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run SQLite migrations for existing databases
    await _run_migrations()


async def _run_migrations():
    """
    Run SQLite migrations for existing databases.

    SQLAlchemy's create_all() is idempotent for new tables but doesn't
    modify existing tables. This function handles schema migrations
    for SQLite databases.

    For production PostgreSQL, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Check if display_name column exists in users table
        result = await conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]

        if "display_name" not in columns:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN display_name VARCHAR(255)")
            )

        # Check and add user_id and last_activity_at columns to threads
        result = await conn.execute(text("PRAGMA table_info(threads)"))
        thread_columns = [row[1] for row in result]

        if "user_id" not in thread_columns:
            await conn.execute(
                text("ALTER TABLE threads ADD COLUMN user_id VARCHAR(36) REFERENCES users(id)")
            )

        if "last_activity_at" not in thread_columns:
            # SQLite doesn't allow non-constant defaults in ALTER TABLE
            # Add column without default, then backfill from updated_at
            await conn.execute(
                text("ALTER TABLE threads ADD COLUMN last_activity_at DATETIME")
            )

        # Always backfill last_activity_at for any threads missing it
        # (handles case where column existed but backfill didn't run)
        await conn.execute(
            text("UPDATE threads SET last_activity_at = updated_at WHERE last_activity_at IS NULL")
        )

        # Check if project_id column is NOT NULL (needs to be nullable for project-less threads)
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        result = await conn.execute(text("PRAGMA table_info(threads)"))
        columns_info = {row[1]: row[3] for row in result}  # name -> notnull

        if columns_info.get("project_id") == 1:  # 1 = NOT NULL, 0 = nullable
            # SQLite doesn't support ALTER COLUMN, must recreate table
            # Disable foreign keys temporarily for table recreation
            await conn.execute(text("PRAGMA foreign_keys=OFF"))

            # Create new table with nullable project_id
            await conn.execute(text("""
                CREATE TABLE threads_new (
                    id VARCHAR(36) PRIMARY KEY,
                    project_id VARCHAR(36) REFERENCES projects(id) ON DELETE SET NULL,
                    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    model_provider VARCHAR(20) DEFAULT 'anthropic',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    last_activity_at DATETIME
                )
            """))

            # Copy data
            await conn.execute(text("""
                INSERT INTO threads_new (id, project_id, user_id, title, model_provider, created_at, updated_at, last_activity_at)
                SELECT id, project_id, user_id, title, model_provider, created_at, updated_at, last_activity_at
                FROM threads
            """))

            # Drop old table and rename new one
            await conn.execute(text("DROP TABLE threads"))
            await conn.execute(text("ALTER TABLE threads_new RENAME TO threads"))

            # Recreate indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_threads_project_id ON threads(project_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_threads_user_id ON threads(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_threads_created_at ON threads(created_at)"))

            # Re-enable foreign keys
            await conn.execute(text("PRAGMA foreign_keys=ON"))

        # --- Document schema migration for rich document support ---
        result = await conn.execute(text("PRAGMA table_info(documents)"))
        doc_columns = [row[1] for row in result]

        if "content_type" not in doc_columns:
            await conn.execute(text(
                "ALTER TABLE documents ADD COLUMN content_type VARCHAR(100) DEFAULT 'text/plain'"
            ))

        if "content_text" not in doc_columns:
            await conn.execute(text(
                "ALTER TABLE documents ADD COLUMN content_text TEXT"
            ))

        if "metadata_json" not in doc_columns:
            await conn.execute(text(
                "ALTER TABLE documents ADD COLUMN metadata_json TEXT"
            ))

        # Ensure FTS5 virtual table exists with unicode61 tokenizer for international text
        result = await conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='document_fts'")
        )
        fts_sql = result.scalar()

        if fts_sql is None:
            # FTS5 doesn't exist — create with unicode61 tokenizer
            await conn.execute(text("""
                CREATE VIRTUAL TABLE document_fts USING fts5(
                    document_id UNINDEXED,
                    filename,
                    content,
                    tokenize = 'porter unicode61'
                )
            """))
        elif 'unicode61' not in (fts_sql or ''):
            # FTS5 exists but uses old ascii tokenizer — upgrade to unicode61
            # Must drop and recreate (SQLite FTS5 doesn't support ALTER)
            await conn.execute(text("DROP TABLE document_fts"))
            await conn.execute(text("""
                CREATE VIRTUAL TABLE document_fts USING fts5(
                    document_id UNINDEXED,
                    filename,
                    content,
                    tokenize = 'porter unicode61'
                )
            """))
            # Re-index existing documents
            # For existing text documents, content_text may be NULL (not yet backfilled)
            # Re-index from content_text where available, otherwise we can't re-index
            # (legacy encrypted content can't be decrypted in migration context)
            # This means old documents lose FTS until accessed and backfilled
            await conn.execute(text("""
                INSERT INTO document_fts(document_id, filename, content)
                SELECT d.id, d.filename, d.content_text
                FROM documents d
                WHERE d.content_text IS NOT NULL
            """))


async def close_db():
    """
    Dispose database engine on application shutdown.
    """
    await engine.dispose()
