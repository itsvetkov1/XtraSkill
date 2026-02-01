"""
Database models for Business Analyst Assistant.

All models use PostgreSQL-compatible types to enable SQLite->PostgreSQL migration.
Uses SQLAlchemy 2.0 syntax with mapped_column and declarative base.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, LargeBinary, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class OAuthProvider(str, PyEnum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class User(Base):
    """User account authenticated via OAuth 2.0."""

    __tablename__ = "users"

    # Primary key using UUID for PostgreSQL compatibility
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # OAuth authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    oauth_provider: Mapped[OAuthProvider] = mapped_column(
        Enum(OAuthProvider, native_enum=False, length=20),
        nullable=False
    )
    oauth_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # User profile from OAuth provider
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Audit timestamps with timezone awareness
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship for directly-owned threads (project-less)
    threads: Mapped[List["Thread"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="[Thread.user_id]"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, provider={self.oauth_provider})>"


class TokenUsage(Base):
    """
    Token usage tracking for AI API calls.

    CRITICAL: Must exist before AI service ships (Phase 3) to prevent cost explosion.
    Tracks per-request token usage for cost monitoring and budgeting.
    """

    __tablename__ = "token_usage"

    # Primary key using UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Token counts
    request_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    response_tokens: Mapped[int] = mapped_column(Integer, nullable=False)

    # Cost tracking (using Decimal for precision)
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),  # PostgreSQL-compatible DECIMAL
        nullable=False
    )

    # API endpoint that consumed tokens
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Optional: Model used (for tracking different model costs)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True  # Index for time-based queries (daily costs, etc.)
    )

    def __repr__(self) -> str:
        return (
            f"<TokenUsage(id={self.id}, user_id={self.user_id}, "
            f"total={self.request_tokens + self.response_tokens}, "
            f"cost=${self.total_cost})>"
        )


class Project(Base):
    """
    Project container for organizing conversations and documents.

    Projects are user-owned and cascade delete all related documents and threads.
    """

    __tablename__ = "projects"

    # Primary key using UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key to user with cascade delete
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Project metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships with cascade delete
    documents: Mapped[List["Document"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    # Threads relationship - "all" cascade without "delete-orphan" since
    # project-less threads are intentional (orphans when project_id is NULL)
    threads: Mapped[List["Thread"]] = relationship(
        back_populates="project",
        cascade="all",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, user_id={self.user_id})>"


class Document(Base):
    """
    Document attached to a project for AI context.

    Content is encrypted at rest using Fernet symmetric encryption.
    Text-only files (.txt, .md) in MVP; max 1MB.
    """

    __tablename__ = "documents"

    # Primary key using UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key to project with cascade delete
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Document metadata
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # Encrypted content (Fernet encryption)
    content_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship back to project
    project: Mapped["Project"] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, project_id={self.project_id})>"


class Thread(Base):
    """
    Conversation thread, optionally within a project.

    Contains messages exchanged between user and AI assistant.
    Title is optional; will be AI-generated in Phase 3.

    Ownership model:
    - Project-based: project_id set, user_id null -> owned via project
    - Project-less: project_id null, user_id set -> owned directly by user
    """

    __tablename__ = "threads"

    # Primary key using UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key to project with SET NULL on delete (nullable for project-less threads)
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,  # Nullable for project-less threads
        index=True
    )

    # Foreign key to user for direct ownership of project-less threads
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # Only set when project_id is None
        index=True
    )

    # Thread metadata
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # LLM provider binding (anthropic, google, deepseek)
    model_provider: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="anthropic"
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True  # Index for sorting threads by creation
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Last activity timestamp for global thread sorting
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True  # Index for efficient sorting
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(back_populates="threads")
    user: Mapped[Optional["User"]] = relationship(
        back_populates="threads",
        foreign_keys=[user_id]
    )
    messages: Mapped[List["Message"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at"  # Chronological message order
    )
    artifacts: Mapped[List["Artifact"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Artifact.created_at.desc()"  # Newest artifacts first
    )

    def __repr__(self) -> str:
        return f"<Thread(id={self.id}, title={self.title}, project_id={self.project_id})>"


class Message(Base):
    """
    Individual message in a conversation thread.

    Messages alternate between 'user' (BA input) and 'assistant' (AI response).
    Content stored as plaintext (not encrypted like documents).
    """

    __tablename__ = "messages"

    # Primary key using UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key to thread with cascade delete
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message content
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True  # Index for message ordering
    )

    # Relationship back to thread
    thread: Mapped["Thread"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, thread_id={self.thread_id})>"


class ArtifactType(str, PyEnum):
    """Types of generated business analysis artifacts."""
    USER_STORIES = "user_stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    REQUIREMENTS_DOC = "requirements_doc"
    BRD = "brd"  # Business Requirements Document following brd-template.md structure


class Artifact(Base):
    """
    Generated business analysis artifact from conversation.

    Artifacts are created by Claude via the save_artifact tool during conversations.
    Content stored in markdown format with optional JSON for structured access.
    """

    __tablename__ = "artifacts"

    # Primary key using UUID
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Foreign key to thread with cascade delete
    thread_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Artifact metadata
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, native_enum=False, length=30),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Content storage
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )  # Structured data for programmatic access

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship back to thread
    thread: Mapped["Thread"] = relationship(back_populates="artifacts")

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, type={self.artifact_type}, title={self.title})>"
