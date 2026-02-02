# Phase 30: Backend LLM & API Tests - Research

**Researched:** 2026-02-02
**Domain:** Backend testing (pytest, FastAPI, LLM adapters, API routes)
**Confidence:** HIGH

## Summary

Phase 30 involves creating comprehensive tests for LLM adapters (Anthropic, Gemini, DeepSeek) and API routes (auth, projects, documents, threads, conversations, artifacts). This phase builds on Phase 28's test infrastructure (MockLLMAdapter, factories, fixtures) and Phase 29's service test patterns.

The codebase already has excellent test infrastructure established:
- MockLLMAdapter with call_history tracking for LLM testing
- Factory-boy factories with pytest_plugins discovery
- AsyncClient fixture for HTTP testing
- db_session fixture with FTS5 support
- Class-based test organization pattern

**Primary recommendation:** Follow the established patterns from Phase 28/29. Use MockLLMAdapter for adapter tests, httpx AsyncClient for API contract tests, and focus on mocking external HTTP calls rather than testing actual provider APIs.

## Standard Stack

The established testing libraries for this codebase:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 7.x | Test runner | Established in Phase 28 |
| pytest-asyncio | 0.21+ | Async test support | Required for async/await |
| httpx | 0.24+ | Async HTTP client | FastAPI recommended |
| factory-boy | 3.x | Test data factories | Established in Phase 28 |
| pytest-factoryboy | 2.x | Factory fixtures | Auto-registers factories |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock | stdlib | Mocking/patching | Mock external HTTP calls |
| aiosqlite | 0.19+ | Async SQLite | Test database |
| sse-starlette | 1.x | SSE support | Testing SSE endpoints |

### Already Installed (No New Dependencies)
All required dependencies are already in the project from Phase 28.

## Architecture Patterns

### Recommended Project Structure
```
backend/tests/
├── conftest.py                    # pytest_plugins, skill fixtures
├── fixtures/
│   ├── __init__.py
│   ├── db_fixtures.py             # db_engine, db_session
│   ├── auth_fixtures.py           # client, auth_headers
│   ├── llm_fixtures.py            # MockLLMAdapter, mock_llm_*
│   └── factories.py               # UserFactory, ProjectFactory, etc.
├── unit/
│   ├── services/                  # Phase 29 service tests
│   │   ├── test_ai_service.py
│   │   ├── test_auth_service.py
│   │   └── ...
│   └── llm/                       # Phase 30 LLM adapter tests (NEW)
│       ├── __init__.py
│       ├── conftest.py            # LLM-specific fixtures
│       ├── test_anthropic_adapter.py
│       ├── test_gemini_adapter.py
│       ├── test_deepseek_adapter.py
│       └── test_sse_helpers.py
└── api/                           # Phase 30 API contract tests (NEW)
    ├── __init__.py
    ├── conftest.py                # API-specific fixtures
    ├── test_auth_routes.py
    ├── test_project_routes.py
    ├── test_document_routes.py
    ├── test_thread_routes.py
    ├── test_conversation_routes.py
    └── test_artifact_routes.py
```

### Pattern 1: Class-Based Test Organization
**What:** Group related tests in classes with descriptive names
**When to use:** Always for Phase 30 tests
**Example:**
```python
# Source: tests/unit/services/test_ai_service.py (existing pattern)
class TestAIServiceExecuteTool:
    """Tests for AIService.execute_tool method."""

    @pytest.mark.asyncio
    async def test_save_artifact_creates_artifact(self, db_session, user):
        """save_artifact tool creates artifact in database."""
        ...

class TestAIServiceStreamChat:
    """Tests for AIService.stream_chat method."""
    ...
```

### Pattern 2: MockLLMAdapter for LLM Testing
**What:** Use MockLLMAdapter to simulate LLM responses without API calls
**When to use:** Testing any code that uses LLM adapters
**Example:**
```python
# Source: tests/fixtures/llm_fixtures.py (existing)
adapter = MockLLMAdapter(
    responses=["Hello", " world"],     # Text chunks
    tool_calls=[{...}],                 # Tool use simulation
    raise_error="API error",            # Error simulation
    usage={"input_tokens": 10, "output_tokens": 5}
)

# Access call history for assertions
assert len(adapter.call_history) == 1
assert adapter.call_history[0]["messages"] == expected_messages
```

### Pattern 3: Mocking External HTTP for Adapter Tests
**What:** Mock the underlying HTTP client, not the adapter methods
**When to use:** Testing real adapter implementations
**Example:**
```python
# For AnthropicAdapter (uses anthropic.AsyncAnthropic)
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_anthropic_adapter_streams_text():
    """AnthropicAdapter yields text chunks from API response."""

    # Mock the stream context manager
    mock_stream = AsyncMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=None)
    mock_stream.text_stream = mock_async_iter(["Hello", " world"])
    mock_stream.get_final_message = AsyncMock(return_value=MockFinalMessage())

    with patch('anthropic.AsyncAnthropic') as MockClient:
        MockClient.return_value.messages.stream = MagicMock(return_value=mock_stream)
        adapter = AnthropicAdapter(api_key="test-key")

        chunks = []
        async for chunk in adapter.stream_chat(messages, "system"):
            chunks.append(chunk)

        assert len([c for c in chunks if c.chunk_type == "text"]) == 2
```

### Pattern 4: FastAPI AsyncClient for API Tests
**What:** Use httpx AsyncClient with db_session override
**When to use:** All API contract tests
**Example:**
```python
# Source: tests/fixtures/auth_fixtures.py (existing)
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
```

### Pattern 5: JWT Token Creation for Auth Tests
**What:** Use create_access_token to generate valid tokens
**When to use:** Testing authenticated endpoints
**Example:**
```python
# Source: tests/test_projects.py (existing pattern)
from app.utils.jwt import create_access_token

token = create_access_token(user.id, user.email)
response = await client.get(
    "/api/projects",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Anti-Patterns to Avoid
- **Testing real LLM APIs:** Use MockLLMAdapter or mock HTTP clients
- **Testing OAuth providers directly:** Mock httpx calls, don't hit real OAuth servers
- **Flat test files:** Use class-based organization
- **Skipping call_history assertions:** Always verify MockLLMAdapter was called correctly
- **Hardcoded UUIDs:** Use uuid4() or factories

## Don't Hand-Roll

Problems that have existing solutions in the codebase:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mock LLM responses | Custom mock class | `MockLLMAdapter` from llm_fixtures | Has call_history, configurable responses |
| Test user creation | Manual User() | `UserFactory` | Handles all fields, UUIDs, timestamps |
| Test project creation | Manual Project() | `ProjectFactory` | Consistent test data |
| HTTP client setup | Raw httpx | `client` fixture | Handles db override, cleanup |
| JWT tokens | Manual encoding | `create_access_token()` | Consistent with production |
| FTS5 test DB | Manual SQL | `db_engine` fixture | Creates FTS5 table automatically |

**Key insight:** Phase 28 established comprehensive test infrastructure. All fixtures are auto-discovered via pytest_plugins in conftest.py.

## Common Pitfalls

### Pitfall 1: Forgetting Async Generator Consumption
**What goes wrong:** Async generators not fully consumed, missing assertions
**Why it happens:** `async for` loops not completed, exceptions not caught
**How to avoid:** Always collect all chunks, or use break explicitly
**Warning signs:** Tests pass but don't actually verify behavior
```python
# BAD: Generator not consumed
async for chunk in adapter.stream_chat(...):
    if chunk.chunk_type == "complete":
        break  # May miss error chunks

# GOOD: Collect all chunks
chunks = []
async for chunk in adapter.stream_chat(...):
    chunks.append(chunk)
assert any(c.chunk_type == "complete" for c in chunks)
```

### Pitfall 2: Not Cleaning Up Dependency Overrides
**What goes wrong:** Tests leak state between runs
**Why it happens:** FastAPI dependency_overrides not cleared
**How to avoid:** Use the `client` fixture which handles cleanup
**Warning signs:** Tests pass individually but fail in suite

### Pitfall 3: SSE Event Parsing
**What goes wrong:** JSON parsing errors in event data
**Why it happens:** SSE events have specific format, data may be double-encoded
**How to avoid:** Use json.loads() on event["data"], handle comment events
**Warning signs:** KeyError or JSONDecodeError in SSE tests
```python
# Events from stream_chat look like:
# {"event": "text_delta", "data": '{"text": "Hello"}'}
# {"comment": "heartbeat"}  # No "event" key

if "event" in event:
    data = json.loads(event["data"])
```

### Pitfall 4: FTS5 Not Created in Test DB
**What goes wrong:** FTS5 queries fail with "no such table"
**Why it happens:** FTS5 virtual table not created
**How to avoid:** Use `db_engine` fixture from db_fixtures.py (already creates FTS5)
**Warning signs:** "no such table: document_fts" errors

### Pitfall 5: OAuth State Storage in Tests
**What goes wrong:** State validation fails in OAuth callback tests
**Why it happens:** `_oauth_states` dict is module-level, needs manual management
**How to avoid:** Directly manipulate `_oauth_states` in tests or mock it
```python
from app.routes.auth import _oauth_states

# Setup: Add expected state
_oauth_states["test-state"] = "google"

# Test callback
response = await client.get("/auth/google/callback?code=xxx&state=test-state")
```

## Code Examples

### Example 1: Testing Anthropic Adapter with Mocked HTTP
```python
# tests/unit/llm/test_anthropic_adapter.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.base import StreamChunk

class TestAnthropicAdapterStreamChat:
    """Tests for AnthropicAdapter.stream_chat method."""

    @pytest.mark.asyncio
    async def test_yields_text_chunks(self):
        """Text content is yielded as text chunks."""
        # Create mock async iterator for text_stream
        async def mock_text_stream():
            yield "Hello"
            yield " world"

        # Create mock final message
        mock_final = MagicMock()
        mock_final.content = []  # No tool calls
        mock_final.usage.input_tokens = 10
        mock_final.usage.output_tokens = 5

        # Create mock stream context manager
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_stream
        mock_stream.__aexit__.return_value = None
        mock_stream.text_stream = mock_text_stream()
        mock_stream.get_final_message.return_value = mock_final

        with patch('anthropic.AsyncAnthropic') as MockClient:
            mock_client = MockClient.return_value
            mock_client.messages.stream.return_value = mock_stream

            adapter = AnthropicAdapter(api_key="test-key")

            chunks = []
            async for chunk in adapter.stream_chat(
                messages=[{"role": "user", "content": "Hi"}],
                system_prompt="You are helpful."
            ):
                chunks.append(chunk)

            text_chunks = [c for c in chunks if c.chunk_type == "text"]
            assert len(text_chunks) == 2
            assert text_chunks[0].content == "Hello"
            assert text_chunks[1].content == " world"

            # Verify complete chunk
            complete = [c for c in chunks if c.chunk_type == "complete"]
            assert len(complete) == 1
            assert complete[0].usage == {"input_tokens": 10, "output_tokens": 5}
```

### Example 2: API Contract Test Pattern
```python
# tests/api/test_project_routes.py
import pytest
from uuid import uuid4
from app.models import User, Project, OAuthProvider
from app.utils.jwt import create_access_token

class TestCreateProject:
    """Contract tests for POST /api/projects."""

    @pytest.mark.asyncio
    async def test_201_created_with_valid_data(self, client, db_session, user):
        """Returns 201 and project data on success."""
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Project", "description": "Description"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_403_without_auth(self, client):
        """Returns 403 when not authenticated."""
        response = await client.post(
            "/api/projects",
            json={"name": "Test"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_422_with_missing_name(self, client, db_session, user):
        """Returns 422 when required field missing."""
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        response = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "No name"}
        )

        assert response.status_code == 422
```

### Example 3: SSE Streaming Test
```python
# tests/api/test_conversation_routes.py
import json
import pytest
from app.models import User, Thread
from app.utils.jwt import create_access_token
from unittest.mock import patch, AsyncMock

class TestStreamChat:
    """Contract tests for POST /api/threads/{thread_id}/chat."""

    @pytest.mark.asyncio
    async def test_streams_text_events(self, client, db_session, user, mock_llm_adapter):
        """Returns SSE text_delta events."""
        db_session.add(user)
        await db_session.commit()

        thread = Thread(user_id=user.id, title="Test")
        db_session.add(thread)
        await db_session.commit()

        token = create_access_token(user.id, user.email)

        # Mock AIService to use our mock adapter
        adapter = mock_llm_adapter(responses=["Hello", " world"])

        with patch('app.routes.conversations.AIService') as MockAIService:
            mock_service = AsyncMock()

            async def mock_stream(*args, **kwargs):
                for text in ["Hello", " world"]:
                    yield {"event": "text_delta", "data": json.dumps({"text": text})}
                yield {"event": "message_complete", "data": json.dumps({"content": "Hello world", "usage": {}})}

            mock_service.stream_chat = mock_stream
            MockAIService.return_value = mock_service

            async with client.stream(
                "POST",
                f"/api/threads/{thread.id}/chat",
                headers={"Authorization": f"Bearer {token}"},
                json={"content": "Hi"}
            ) as response:
                assert response.status_code == 200

                events = []
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        events.append(line)

                # Verify text_delta events received
                assert any("text_delta" in e for e in events)
```

### Example 4: FTS5 Search Test
```python
# tests/unit/services/test_document_search.py (existing pattern)
class TestSearchDocumentsRanking:
    """Tests for BM25 ranking in search results."""

    @pytest.mark.asyncio
    async def test_higher_relevance_ranked_first(self, db_session, user):
        """Documents with more matches ranked higher."""
        db_session.add(user)
        await db_session.commit()

        project = Project(user_id=user.id, name="Test")
        db_session.add(project)
        await db_session.commit()

        # Document with single match
        doc1 = Document(project_id=project.id, filename="single.md", content_encrypted=b"x")
        # Document with multiple matches
        doc2 = Document(project_id=project.id, filename="multiple.md", content_encrypted=b"x")
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        await index_document(db_session, doc1.id, doc1.filename, "authentication is important")
        await index_document(db_session, doc2.id, doc2.filename,
                            "authentication requires authentication tokens for authentication")
        await db_session.commit()

        results = await search_documents(db_session, project.id, "authentication")

        # Multiple matches should rank higher (BM25)
        assert len(results) == 2
        assert results[0][0] == doc2.id  # Higher relevance first
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mock entire service | Mock HTTP client | Phase 29 | Tests verify actual adapter logic |
| Raw SQL for FTS5 | db_fixtures auto-create | Phase 28 | Consistent test setup |
| Manual user creation | Factory fixtures | Phase 28 | Cleaner, more maintainable |

**Deprecated/outdated:**
- TestClient (sync): Use AsyncClient with ASGITransport instead

## Open Questions

Things that were resolved during research:

1. **How to test SSE streaming?**
   - Answer: Use `client.stream()` context manager with `aiter_lines()`
   - Pattern shown in Example 3 above

2. **How to mock each provider's SDK?**
   - Anthropic: Mock `anthropic.AsyncAnthropic`
   - Gemini: Mock `google.genai.Client`
   - DeepSeek: Mock `openai.AsyncOpenAI`

3. **Error response format verification?**
   - All routes use HTTPException which FastAPI converts to {"detail": "message"}
   - Test by asserting response.json()["detail"] == expected_message

## Sources

### Primary (HIGH confidence)
- `backend/tests/fixtures/llm_fixtures.py` - MockLLMAdapter implementation
- `backend/tests/fixtures/factories.py` - Factory-boy factories
- `backend/tests/fixtures/db_fixtures.py` - Database fixtures
- `backend/tests/fixtures/auth_fixtures.py` - HTTP client fixture
- `backend/tests/unit/services/test_ai_service.py` - Service test patterns
- `backend/tests/unit/services/test_auth_service.py` - OAuth mocking patterns
- `backend/tests/test_projects.py` - API test patterns

### Secondary (MEDIUM confidence)
- `backend/app/services/llm/*.py` - Adapter implementations to test
- `backend/app/routes/*.py` - Route implementations to test
- `backend/tests/unit/services/test_document_search.py` - FTS5 test patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All from existing codebase
- Architecture: HIGH - Patterns established in Phase 28/29
- Pitfalls: HIGH - Identified from existing tests

**Research date:** 2026-02-02
**Valid until:** N/A - Codebase-specific patterns

## Existing Codebase Inventory

### LLM Adapters to Test (BLLM-01 to BLLM-03)

| Adapter | Location | Key Methods | HTTP Client |
|---------|----------|-------------|-------------|
| AnthropicAdapter | `app/services/llm/anthropic_adapter.py` | `stream_chat()` | `anthropic.AsyncAnthropic` |
| GeminiAdapter | `app/services/llm/gemini_adapter.py` | `stream_chat()`, `_non_streaming_with_tools()` | `google.genai.Client` |
| DeepSeekAdapter | `app/services/llm/deepseek_adapter.py` | `stream_chat()` | `openai.AsyncOpenAI` |

### API Routes to Test (BAPI-01 to BAPI-06)

| Router | Location | Prefix | Endpoints |
|--------|----------|--------|-----------|
| Auth | `app/routes/auth.py` | `/auth` | POST initiate, GET callback, GET /me, GET /usage, POST /logout |
| Projects | `app/routes/projects.py` | `/api` | CRUD /projects |
| Documents | `app/routes/documents.py` | `/api` | Upload, list, get, search, delete |
| Threads | `app/routes/threads.py` | `/api` | Global /threads, project /projects/{id}/threads |
| Conversations | `app/routes/conversations.py` | `/api` | POST /threads/{id}/chat (SSE), DELETE message |
| Artifacts | `app/routes/artifacts.py` | `/api` | List, get, export |

### Existing Test Coverage

| Area | Existing Tests | Location |
|------|----------------|----------|
| Projects CRUD | Yes (integration) | `tests/test_projects.py` |
| Document search | Yes (unit) | `tests/unit/services/test_document_search.py` |
| Auth service | Yes (unit) | `tests/unit/services/test_auth_service.py` |
| AI service | Yes (unit) | `tests/unit/services/test_ai_service.py` |
| LLM adapters | No | Need tests/unit/llm/*.py |
| API contracts | Partial | Need tests/api/*.py |

### SSE Streaming Helper (BLLM-04)

The `stream_with_heartbeat()` function in `app/services/ai_service.py` already exists and has basic tests in `test_ai_service.py`. Phase 30 needs:
- SSE helper for parsing SSE events in tests
- More comprehensive heartbeat timeout tests

### FTS5 Search (BLLM-05)

Already has tests in `tests/unit/services/test_document_search.py`. Phase 30 needs:
- BM25 ranking verification
- Snippet highlighting verification
- Edge cases (special characters, empty results)

### Error Response Format (BAPI-07)

All routes use FastAPI HTTPException pattern:
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)
```

Response format: `{"detail": "message"}`

Phase 30 needs to verify consistency across all routes.
