"""
Database connection and session management.

Supports both SQLite (MVP) and PostgreSQL (production) via connection string.
Uses async SQLAlchemy for non-blocking database operations with FastAPI.
"""

import os
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base


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
    echo=True,
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


async def close_db():
    """
    Dispose database engine on application shutdown.
    """
    await engine.dispose()
