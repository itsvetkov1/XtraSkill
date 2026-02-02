---
phase: 28-test-infrastructure
plan: 03
type: execute
wave: 2
depends_on: ["28-01"]
files_modified:
  - backend/tests/fixtures/__init__.py
  - backend/tests/fixtures/auth_fixtures.py
  - backend/tests/fixtures/db_fixtures.py
  - backend/tests/fixtures/llm_fixtures.py
  - backend/tests/fixtures/factories.py
  - backend/tests/conftest.py
autonomous: true

must_haves:
  truths:
    - "Test files can import fixtures from tests.fixtures module"
    - "MockLLMAdapter yields configurable StreamChunk responses"
    - "MockLLMAdapter can simulate tool_calls and errors"
    - "Factory-boy factories create valid database objects"
    - "Factories are registered as pytest fixtures via pytest-factoryboy"
  artifacts:
    - path: "backend/tests/fixtures/__init__.py"
      provides: "Fixtures module package"
      exports: ["UserFactory", "ProjectFactory", "MockLLMAdapter"]
    - path: "backend/tests/fixtures/auth_fixtures.py"
      provides: "Auth-related fixtures"
      contains: "def test_user"
    - path: "backend/tests/fixtures/db_fixtures.py"
      provides: "Database session fixtures"
      contains: "db_session"
    - path: "backend/tests/fixtures/llm_fixtures.py"
      provides: "MockLLMAdapter implementation"
      contains: "class MockLLMAdapter"
    - path: "backend/tests/fixtures/factories.py"
      provides: "Factory-boy model factories"
      contains: "class UserFactory"
  key_links:
    - from: "backend/tests/conftest.py"
      to: "backend/tests/fixtures/"
      via: "pytest_plugins import"
      pattern: "pytest_plugins.*fixtures"
    - from: "MockLLMAdapter"
      to: "LLMAdapter"
      via: "class inheritance"
      pattern: "class MockLLMAdapter.*LLMAdapter"
    - from: "UserFactory"
      to: "User model"
      via: "SQLAlchemy factory"
      pattern: "model = User"
---

<objective>
Create shared fixtures module with MockLLMAdapter and Factory-boy factories.

Purpose: Centralize test fixtures for reuse across all test files. MockLLMAdapter enables testing AI service without real API calls. Factory-boy enables clean test data creation.

Output: `tests/fixtures/` module with importable fixtures, MockLLMAdapter, and model factories.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@backend/tests/conftest.py
@backend/app/services/llm/base.py
@backend/app/models.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create fixtures module structure</name>
  <files>
    backend/tests/fixtures/__init__.py
    backend/tests/fixtures/db_fixtures.py
    backend/tests/fixtures/auth_fixtures.py
  </files>
  <action>
Create the fixtures module directory and files.

1. Create `backend/tests/fixtures/__init__.py`:
```python
"""
Shared test fixtures module.

Import fixtures from submodules for pytest auto-discovery.
Factories are auto-registered via pytest-factoryboy.
"""

from .db_fixtures import *
from .auth_fixtures import *
from .llm_fixtures import *
from .factories import *
```

2. Create `backend/tests/fixtures/db_fixtures.py` - extract db fixtures from conftest.py:
```python
"""Database fixtures for testing."""

import os
import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Set up test environment variables
if not os.getenv("FERNET_KEY"):
    os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-jwt"


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine with FTS5 support."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
                document_id UNINDEXED,
                filename,
                content,
                tokenize = 'porter ascii'
            )
        """))

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session_maker = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
```

3. Create `backend/tests/fixtures/auth_fixtures.py`:
```python
"""Authentication fixtures for testing."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from main import app


@pytest_asyncio.fixture
async def client(db_session):
    """Create test HTTP client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Factory for creating auth headers with a given user ID."""
    def _create_headers(user_id: str) -> dict:
        # In tests, we typically override auth dependency
        # This fixture provides consistent header format
        return {"Authorization": f"Bearer test-token-{user_id}"}
    return _create_headers
```
  </action>
  <verify>Directory backend/tests/fixtures/ exists with __init__.py, db_fixtures.py, auth_fixtures.py</verify>
  <done>Fixtures module structure created with db and auth fixtures extracted from conftest.py</done>
</task>

<task type="auto">
  <name>Task 2: Create MockLLMAdapter</name>
  <files>backend/tests/fixtures/llm_fixtures.py</files>
  <action>
Create `backend/tests/fixtures/llm_fixtures.py` with MockLLMAdapter:

```python
"""LLM testing fixtures including MockLLMAdapter."""

from typing import Any, AsyncGenerator, Dict, List, Optional
import pytest

from app.services.llm.base import LLMAdapter, LLMProvider, StreamChunk


class MockLLMAdapter(LLMAdapter):
    """
    Mock LLM adapter for testing without real API calls.

    Configurable to return:
    - Text responses (default)
    - Tool calls
    - Errors
    - Custom chunk sequences

    Usage:
        # Simple text response
        adapter = MockLLMAdapter(responses=["Hello", " world"])

        # Tool call response
        adapter = MockLLMAdapter(tool_calls=[{
            "id": "call_1",
            "name": "save_artifact",
            "input": {"title": "Test"}
        }])

        # Error simulation
        adapter = MockLLMAdapter(raise_error="API rate limit")

        # Custom chunks
        adapter = MockLLMAdapter(chunks=[
            StreamChunk(chunk_type="text", content="Hello"),
            StreamChunk(chunk_type="complete", usage={"input_tokens": 10, "output_tokens": 5})
        ])
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        responses: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        raise_error: Optional[str] = None,
        chunks: Optional[List[StreamChunk]] = None,
        usage: Optional[Dict[str, int]] = None,
    ):
        """
        Initialize MockLLMAdapter with configurable behavior.

        Args:
            provider: Provider to report (default: ANTHROPIC)
            responses: List of text strings to yield as text chunks
            tool_calls: List of tool call dicts to yield as tool_use chunks
            raise_error: If set, yields an error chunk with this message
            chunks: If set, yields these exact chunks (overrides responses/tool_calls)
            usage: Token usage to report in complete chunk (default: 10/5)
        """
        self._provider = provider
        self._responses = responses or []
        self._tool_calls = tool_calls or []
        self._raise_error = raise_error
        self._chunks = chunks
        self._usage = usage or {"input_tokens": 10, "output_tokens": 5}

        # Track calls for assertions
        self.call_history: List[Dict[str, Any]] = []

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream mock response chunks."""
        # Record the call
        self.call_history.append({
            "messages": messages,
            "system_prompt": system_prompt,
            "tools": tools,
            "max_tokens": max_tokens,
        })

        # If error configured, yield error chunk
        if self._raise_error:
            yield StreamChunk(chunk_type="error", error=self._raise_error)
            return

        # If custom chunks provided, yield those
        if self._chunks:
            for chunk in self._chunks:
                yield chunk
            return

        # Yield text responses
        for text in self._responses:
            yield StreamChunk(chunk_type="text", content=text)

        # Yield tool calls
        for tool_call in self._tool_calls:
            yield StreamChunk(chunk_type="tool_use", tool_call=tool_call)

        # Yield completion
        yield StreamChunk(chunk_type="complete", usage=self._usage)


@pytest.fixture
def mock_llm_adapter():
    """Factory fixture for creating MockLLMAdapter instances."""
    def _create(
        responses: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        raise_error: Optional[str] = None,
        **kwargs
    ) -> MockLLMAdapter:
        return MockLLMAdapter(
            responses=responses,
            tool_calls=tool_calls,
            raise_error=raise_error,
            **kwargs
        )
    return _create


@pytest.fixture
def mock_llm_text_response():
    """Pre-configured MockLLMAdapter that returns simple text."""
    return MockLLMAdapter(responses=["This is a test response from the mock LLM."])


@pytest.fixture
def mock_llm_tool_response():
    """Pre-configured MockLLMAdapter that returns a tool call."""
    return MockLLMAdapter(tool_calls=[{
        "id": "toolu_01",
        "name": "save_artifact",
        "input": {
            "artifact_type": "brd",
            "title": "Test BRD",
            "content_markdown": "# Test BRD\n\nTest content."
        }
    }])


@pytest.fixture
def mock_llm_error():
    """Pre-configured MockLLMAdapter that returns an error."""
    return MockLLMAdapter(raise_error="API rate limit exceeded")
```
  </action>
  <verify>Run `cd backend && python -c "from tests.fixtures.llm_fixtures import MockLLMAdapter; print('OK')"` succeeds</verify>
  <done>MockLLMAdapter created with configurable responses, tool_calls, errors, and call tracking</done>
</task>

<task type="auto">
  <name>Task 3: Create Factory-boy factories and update conftest.py</name>
  <files>
    backend/tests/fixtures/factories.py
    backend/tests/conftest.py
  </files>
  <action>
1. Create `backend/tests/fixtures/factories.py` with model factories:

```python
"""Factory-boy factories for test data creation."""

from datetime import datetime
from uuid import uuid4

import factory
from pytest_factoryboy import register

from app.models import (
    User, OAuthProvider, Project, Document, Thread, Message, Artifact, ArtifactType
)


class BaseFactory(factory.Factory):
    """Base factory with common settings."""

    class Meta:
        abstract = True


@register
class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.Faker("email")
    oauth_provider = OAuthProvider.GOOGLE
    oauth_id = factory.LazyFunction(lambda: f"google-{uuid4()}")
    display_name = factory.Faker("name")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


@register
class ProjectFactory(factory.Factory):
    """Factory for Project model."""

    class Meta:
        model = Project

    id = factory.LazyFunction(lambda: str(uuid4()))
    user_id = factory.LazyAttribute(lambda o: str(uuid4()))
    name = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


@register
class DocumentFactory(factory.Factory):
    """Factory for Document model."""

    class Meta:
        model = Document

    id = factory.LazyFunction(lambda: str(uuid4()))
    project_id = factory.LazyAttribute(lambda o: str(uuid4()))
    filename = factory.Faker("file_name", extension="md")
    content_encrypted = factory.LazyFunction(lambda: b"encrypted-content-placeholder")
    created_at = factory.LazyFunction(datetime.utcnow)


@register
class ThreadFactory(factory.Factory):
    """Factory for Thread model."""

    class Meta:
        model = Thread

    id = factory.LazyFunction(lambda: str(uuid4()))
    project_id = None  # Optional - set explicitly when needed
    user_id = factory.LazyAttribute(lambda o: str(uuid4()))
    title = factory.Faker("sentence", nb_words=4)
    model_provider = "anthropic"
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    last_activity_at = factory.LazyFunction(datetime.utcnow)


@register
class MessageFactory(factory.Factory):
    """Factory for Message model."""

    class Meta:
        model = Message

    id = factory.LazyFunction(lambda: str(uuid4()))
    thread_id = factory.LazyAttribute(lambda o: str(uuid4()))
    role = "user"
    content = factory.Faker("paragraph")
    created_at = factory.LazyFunction(datetime.utcnow)


@register
class ArtifactFactory(factory.Factory):
    """Factory for Artifact model."""

    class Meta:
        model = Artifact

    id = factory.LazyFunction(lambda: str(uuid4()))
    thread_id = factory.LazyAttribute(lambda o: str(uuid4()))
    artifact_type = ArtifactType.BRD
    title = factory.Faker("sentence", nb_words=4)
    content_markdown = factory.Faker("text", max_nb_chars=500)
    content_json = None
    created_at = factory.LazyFunction(datetime.utcnow)


# Helper for creating related objects
class UserWithProjectFactory(UserFactory):
    """User with an associated project."""

    @factory.post_generation
    def projects(self, create, extracted, **kwargs):
        if extracted:
            for project in extracted:
                project.user_id = self.id


class ProjectWithThreadFactory(ProjectFactory):
    """Project with an associated thread."""

    @factory.post_generation
    def threads(self, create, extracted, **kwargs):
        if extracted:
            for thread in extracted:
                thread.project_id = self.id
```

2. Update `backend/tests/conftest.py` to import from fixtures module:

```python
"""Pytest configuration and fixtures for backend tests."""

# Import all fixtures from the fixtures module
# This enables pytest to discover fixtures via pytest_plugins
pytest_plugins = [
    "tests.fixtures.db_fixtures",
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.llm_fixtures",
    "tests.fixtures.factories",
]

# Keep skill integration fixtures in conftest for backward compatibility
# These are specific to skill tests and used infrequently

import pytest


@pytest.fixture
def skill_prompt():
    """Load the business-analyst skill prompt for testing."""
    from app.services.skill_loader import load_skill_prompt
    return load_skill_prompt()


@pytest.fixture
def mock_agent_response():
    """Factory for creating mock agent responses."""
    def _create_response(text: str, tool_calls: list = None):
        return {
            "text": text,
            "tool_calls": tool_calls or [],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }
    return _create_response


@pytest.fixture
def sample_discovery_context():
    """Sample context from a discovery conversation."""
    return {
        "business_objective": "Reduce customer onboarding time from 14 days to 2 days",
        "personas": [
            {
                "name": "Account Manager",
                "role": "Manages customer relationships",
                "pain_points": ["Manual data entry", "Slow approval process"],
                "goals": ["Faster customer activation", "More time for strategic work"]
            }
        ],
        "user_flows": [
            "Customer signs contract -> Account Manager creates account -> Customer activates"
        ],
        "success_metrics": [
            "Onboarding time < 2 days",
            "Customer satisfaction > 90%"
        ]
    }


@pytest.fixture
def sample_brd_content():
    """Sample valid BRD content for testing."""
    return """# Business Requirements Document: Customer Onboarding Portal

## Executive Summary
The Customer Onboarding Portal aims to reduce customer onboarding time from 14 days to 2 days.

## Business Context
Current manual process requires 5 different systems and multiple handoffs.

## Business Objectives

### Primary Objective
Reduce onboarding time from 14 days to 2 days by automating data entry and approvals.
"""
```
  </action>
  <verify>
Run `cd backend && python -c "from tests.fixtures.factories import UserFactory, ProjectFactory; u = UserFactory.build(); print(f'User: {u.email}')"` succeeds
Run `cd backend && pytest tests/test_projects.py -v` still passes (backward compatibility)
  </verify>
  <done>
Factory-boy factories created for all models, conftest.py updated to use fixtures module via pytest_plugins
  </done>
</task>

</tasks>

<verification>
1. Fixtures importable: `from tests.fixtures import MockLLMAdapter, UserFactory` works
2. MockLLMAdapter works:
   ```python
   import asyncio
   from tests.fixtures.llm_fixtures import MockLLMAdapter
   adapter = MockLLMAdapter(responses=["Hello"])
   async def test():
       async for chunk in adapter.stream_chat([], ""):
           print(chunk)
   asyncio.run(test())
   ```
3. Factories work: `UserFactory.build()` returns User instance with valid data
4. Existing tests pass: `pytest tests/test_projects.py -v` succeeds
5. Factories registered as fixtures: `pytest --fixtures | grep -i factory` shows factory fixtures
</verification>

<success_criteria>
- tests/fixtures/ module exists with __init__.py, db_fixtures.py, auth_fixtures.py, llm_fixtures.py, factories.py
- MockLLMAdapter can yield text, tool_calls, or errors based on configuration
- MockLLMAdapter tracks call_history for test assertions
- UserFactory, ProjectFactory, DocumentFactory, ThreadFactory, MessageFactory create valid model instances
- conftest.py uses pytest_plugins to import fixtures
- All existing tests continue to pass
</success_criteria>

<output>
After completion, create `.planning/phases/28-test-infrastructure/28-03-SUMMARY.md`
</output>
