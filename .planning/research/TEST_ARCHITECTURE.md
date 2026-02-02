# Test Architecture Patterns

**Domain:** FastAPI + Flutter test organization for BA Assistant
**Researched:** 2026-02-02
**Milestone:** v1.9.1 Test Coverage
**Overall Confidence:** HIGH (based on existing codebase patterns and official documentation)

---

## Executive Summary

BA Assistant already has a solid test foundation with pytest-asyncio for backend and mockito/flutter_test for frontend. This document captures existing patterns and recommends infrastructure improvements for the v1.9.1 milestone focused on test coverage expansion.

The current architecture follows established patterns:
- **Backend:** Pytest with async fixtures, in-memory SQLite, dependency injection via FastAPI overrides
- **Frontend:** Widget tests with mockito-generated mocks, provider injection

Key recommendations focus on consolidating patterns, improving fixture reusability, and adding LLM mocking infrastructure.

---

## Current Test Structure

### Backend (`backend/tests/`)

```
backend/tests/
+-- conftest.py              # Shared fixtures: db_engine, db_session, client
+-- test_auth_integration.py
+-- test_backend_integration.py  # Comprehensive integration suite
+-- test_documents.py
+-- test_document_search.py
+-- test_global_threads.py
+-- test_projects.py
+-- test_skill_integration.py    # Business analyst skill behavior
+-- test_threads.py
+-- test_thread_integration.py
+-- test_thread_simple.py
```

**Existing Pattern:** Tests are organized by domain area with integration-style tests that use HTTP client and database fixtures.

### Frontend (`frontend/test/`)

```
frontend/test/
+-- widget_test.dart           # Default Flutter generated test
+-- integration/
|   +-- auth_flow_test.dart    # Placeholder integration tests
|   +-- project_flow_test.dart
+-- unit/
|   +-- chats_provider_test.dart   # Provider unit tests
+-- widget/
    +-- chat_input_test.dart
    +-- chats_screen_test.dart
    +-- conversation_screen_test.dart
    +-- document_list_screen_test.dart
    +-- login_screen_test.dart
    +-- project_list_screen_test.dart
    +-- thread_list_screen_test.dart
    +-- *.mocks.dart           # Mockito generated files
```

**Existing Pattern:** Separation of unit, widget, and integration tests. Mockito with `@GenerateNiceMocks` annotations.

---

## Recommended Architecture

### Backend Test Organization

```
backend/tests/
+-- conftest.py                    # Global fixtures only
+-- fixtures/
|   +-- __init__.py
|   +-- auth_fixtures.py           # test_user, auth_headers
|   +-- project_fixtures.py        # test_project, test_project_with_docs
|   +-- thread_fixtures.py         # test_thread, test_thread_with_messages
|   +-- llm_fixtures.py            # mock_llm_adapter, mock_streaming_response
+-- unit/
|   +-- services/
|   |   +-- test_encryption.py
|   |   +-- test_brd_generator.py
|   |   +-- test_skill_loader.py
|   |   +-- test_token_tracking.py
|   +-- llm/
|       +-- test_anthropic_adapter.py
|       +-- test_gemini_adapter.py
|       +-- test_deepseek_adapter.py
+-- integration/
|   +-- test_auth_flow.py
|   +-- test_project_crud.py
|   +-- test_document_flow.py
|   +-- test_thread_flow.py
|   +-- test_chat_flow.py
|   +-- test_artifact_flow.py
+-- api/
    +-- test_auth_router.py
    +-- test_projects_router.py
    +-- test_documents_router.py
    +-- test_threads_router.py
    +-- test_chat_router.py
```

**Rationale:**
- `fixtures/` - Separate fixture modules prevent conftest.py bloat
- `unit/` - Pure function tests without database
- `integration/` - Full request cycle tests with database
- `api/` - Router-level tests focusing on HTTP contracts

### Frontend Test Organization

```
frontend/test/
+-- test_helpers/
|   +-- mock_providers.dart        # Reusable mock provider setup
|   +-- test_widgets.dart          # Common test widget wrappers
|   +-- fake_services.dart         # In-memory service implementations
+-- unit/
|   +-- providers/
|   |   +-- chats_provider_test.dart
|   |   +-- conversation_provider_test.dart
|   |   +-- auth_provider_test.dart
|   |   +-- project_provider_test.dart
|   +-- models/
|   |   +-- thread_test.dart
|   |   +-- message_test.dart
|   +-- services/
|       +-- thread_service_test.dart
|       +-- auth_service_test.dart
+-- widget/
|   +-- screens/
|   |   +-- chats_screen_test.dart
|   |   +-- conversation_screen_test.dart
|   |   +-- project_list_screen_test.dart
|   +-- components/
|       +-- chat_input_test.dart
|       +-- message_bubble_test.dart
|       +-- thread_list_tile_test.dart
+-- integration/
    +-- auth_flow_test.dart
    +-- project_flow_test.dart
```

**Rationale:**
- `test_helpers/` - Shared utilities reduce boilerplate
- `unit/providers/` - Provider logic tests with mocked services
- `unit/services/` - Service tests with mocked Dio
- `widget/screens/` vs `widget/components/` - Full screens vs reusable widgets

---

## Mocking Strategies

### Backend: Database Mocking

**Current Pattern (Recommended to Keep):**

```python
# conftest.py
@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite for test isolation."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Enable FK constraints
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client(db_session):
    """Test HTTP client with database override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

**Key Points:**
- In-memory SQLite provides isolation and speed
- `StaticPool` prevents connection issues with async
- Foreign key constraints enabled explicitly
- Dependency injection via FastAPI `dependency_overrides`

### Backend: LLM Mocking

**Recommended Pattern (New Infrastructure):**

```python
# fixtures/llm_fixtures.py
from typing import AsyncGenerator, List, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from app.services.llm.base import LLMAdapter, StreamChunk, LLMProvider

class MockLLMAdapter(LLMAdapter):
    """Configurable mock LLM adapter for testing."""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        responses: List[str] = None,
        tool_calls: List[Dict[str, Any]] = None,
        raise_error: Exception = None,
    ):
        self._provider = provider
        self._responses = responses or ["Mock response"]
        self._tool_calls = tool_calls or []
        self._raise_error = raise_error

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: List[Dict[str, Any]] = None,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[StreamChunk, None]:
        if self._raise_error:
            yield StreamChunk(chunk_type="error", error=str(self._raise_error))
            return

        # Yield tool calls first if any
        for tc in self._tool_calls:
            yield StreamChunk(chunk_type="tool_use", tool_call=tc)

        # Yield text responses
        for response in self._responses:
            for word in response.split():
                yield StreamChunk(chunk_type="text", content=word + " ")

        # Final completion
        yield StreamChunk(
            chunk_type="complete",
            usage={"input_tokens": 100, "output_tokens": 50}
        )

@pytest.fixture
def mock_llm_adapter():
    """Factory fixture for creating mock LLM adapters."""
    def _create(**kwargs):
        return MockLLMAdapter(**kwargs)
    return _create

@pytest.fixture
def mock_llm_factory(mock_llm_adapter, monkeypatch):
    """Patch LLMFactory to return mock adapter."""
    adapter = mock_llm_adapter()
    monkeypatch.setattr(
        "app.services.llm.factory.LLMFactory.create",
        lambda provider: adapter
    )
    return adapter
```

**Usage:**

```python
async def test_chat_returns_response(client, auth_headers, test_thread, mock_llm_factory):
    mock_llm_factory._responses = ["This is a test response"]

    response = await client.post(
        f"/api/threads/{test_thread.id}/chat",
        json={"content": "Hello"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    # Parse SSE stream and verify response content

async def test_chat_handles_tool_use(client, auth_headers, test_thread, mock_llm_adapter, monkeypatch):
    adapter = mock_llm_adapter(
        tool_calls=[{"id": "call_1", "name": "search_documents", "input": {"query": "test"}}],
        responses=["Found relevant information."]
    )
    monkeypatch.setattr("app.services.llm.factory.LLMFactory.create", lambda p: adapter)

    # Test tool use flow
```

### Backend: API Key Mocking

**Current Pattern (Works Well):**

```python
@pytest.mark.asyncio
async def test_send_message_with_api_key(client, test_thread, auth_headers, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # Test continues...

@pytest.mark.asyncio
async def test_send_message_without_api_key(client, test_thread, auth_headers, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = await client.post(...)
    assert response.status_code == 500
```

### Frontend: Service Mocking with Mockito

**Current Pattern (Standard):**

```dart
// thread_service_test.dart
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

@GenerateNiceMocks([MockSpec<ThreadService>()])
void main() {
  late MockThreadService mockThreadService;

  setUp(() {
    mockThreadService = MockThreadService();
  });

  test('calls getGlobalThreads on loadThreads', () async {
    when(mockThreadService.getGlobalThreads(page: 1)).thenAnswer(
      (_) async => PaginatedThreads(threads: [], total: 0, page: 1, pageSize: 25, hasMore: false),
    );

    final provider = ChatsProvider(threadService: mockThreadService);
    await provider.loadThreads();

    verify(mockThreadService.getGlobalThreads(page: 1)).called(1);
  });
}
```

**Run mock generation:**
```bash
cd frontend && flutter pub run build_runner build --delete-conflicting-outputs
```

### Frontend: Provider Mocking for Widget Tests

**Current Pattern (Recommended to Standardize):**

```dart
// widget/screens/chats_screen_test.dart
@GenerateNiceMocks([
  MockSpec<ChatsProvider>(),
  MockSpec<ProviderProvider>(),
])
void main() {
  late MockChatsProvider mockChatsProvider;
  late MockProviderProvider mockProviderProvider;

  setUp(() {
    mockChatsProvider = MockChatsProvider();
    mockProviderProvider = MockProviderProvider();

    // Default mock behavior
    when(mockChatsProvider.isLoading).thenReturn(false);
    when(mockChatsProvider.threads).thenReturn([]);
    // ... more default stubs
  });

  Widget buildTestWidget() {
    return MaterialApp(
      home: MultiProvider(
        providers: [
          ChangeNotifierProvider<ChatsProvider>.value(value: mockChatsProvider),
          ChangeNotifierProvider<ProviderProvider>.value(value: mockProviderProvider),
        ],
        child: const ChatsScreen(),
      ),
    );
  }

  testWidgets('Shows loading state', (tester) async {
    when(mockChatsProvider.isLoading).thenReturn(true);

    await tester.pumpWidget(buildTestWidget());
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
```

### Frontend: HTTP Mocking for Services

**Recommended Pattern (New Infrastructure):**

```dart
// test_helpers/mock_dio.dart
import 'package:dio/dio.dart';
import 'package:mockito/mockito.dart';

class MockDio extends Mock implements Dio {}

class MockResponseInterceptor extends Interceptor {
  final Map<String, dynamic> responses;

  MockResponseInterceptor(this.responses);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final key = '${options.method}:${options.path}';
    if (responses.containsKey(key)) {
      handler.resolve(Response(
        requestOptions: options,
        data: responses[key],
        statusCode: 200,
      ));
    } else {
      handler.reject(DioException(
        requestOptions: options,
        type: DioExceptionType.unknown,
      ));
    }
  }
}

// Usage in test:
test('getThreads returns threads', () async {
  final mockDio = Dio();
  mockDio.interceptors.add(MockResponseInterceptor({
    'GET:/api/projects/p1/threads': [
      {'id': '1', 'title': 'Thread 1', 'created_at': '2026-01-01T00:00:00Z'},
    ],
  }));

  final service = ThreadService(dio: mockDio);
  final threads = await service.getThreads('p1');

  expect(threads.length, 1);
  expect(threads.first.title, 'Thread 1');
});
```

---

## Fixture Patterns

### Backend: Composable Fixtures

**Recommended Pattern:**

```python
# fixtures/auth_fixtures.py
@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        email="testuser@example.com",
        oauth_provider=OAuthProvider.GOOGLE,
        oauth_id=f"google_{uuid4()}",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Authentication headers for test user."""
    token = create_access_token(user_id=test_user.id, email=test_user.email)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def other_user(db_session):
    """Second user for isolation tests."""
    user = User(
        id=str(uuid4()),
        email="other@example.com",
        oauth_provider=OAuthProvider.GOOGLE,
        oauth_id=f"google_{uuid4()}",
    )
    db_session.add(user)
    await db_session.commit()
    return user

# fixtures/project_fixtures.py
@pytest_asyncio.fixture
async def test_project(db_session, test_user):
    """Create a test project."""
    project = Project(
        id=str(uuid4()),
        user_id=test_user.id,
        name="Test Project",
        description="Test description",
    )
    db_session.add(project)
    await db_session.commit()
    return project

@pytest_asyncio.fixture
async def test_project_with_documents(db_session, test_project):
    """Test project with pre-populated documents."""
    from cryptography.fernet import Fernet
    import os

    fernet = Fernet(os.getenv("FERNET_KEY").encode())

    docs = [
        Document(id=str(uuid4()), project_id=test_project.id, filename="requirements.txt", content=fernet.encrypt(b"Requirements content")),
        Document(id=str(uuid4()), project_id=test_project.id, filename="specs.md", content=fernet.encrypt(b"Specifications")),
    ]
    db_session.add_all(docs)
    await db_session.commit()

    return test_project, docs

# fixtures/thread_fixtures.py
@pytest_asyncio.fixture
async def test_thread(db_session, test_project):
    """Create a test thread."""
    thread = Thread(
        id=str(uuid4()),
        project_id=test_project.id,
        title="Test Thread",
    )
    db_session.add(thread)
    await db_session.commit()
    return thread

@pytest_asyncio.fixture
async def test_thread_with_messages(db_session, test_thread):
    """Thread with pre-populated conversation history."""
    messages = [
        Message(id=str(uuid4()), thread_id=test_thread.id, role="user", content="Hello"),
        Message(id=str(uuid4()), thread_id=test_thread.id, role="assistant", content="Hi there"),
        Message(id=str(uuid4()), thread_id=test_thread.id, role="user", content="How are you?"),
    ]
    db_session.add_all(messages)
    await db_session.commit()

    return test_thread, messages
```

**conftest.py Import Pattern:**

```python
# conftest.py - Keep minimal, import fixtures from modules
pytest_plugins = [
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.project_fixtures",
    "tests.fixtures.thread_fixtures",
    "tests.fixtures.llm_fixtures",
]

# Only engine and session fixtures remain here
@pytest_asyncio.fixture
async def db_engine():
    # ... existing implementation

@pytest_asyncio.fixture
async def db_session(db_engine):
    # ... existing implementation

@pytest_asyncio.fixture
async def client(db_session):
    # ... existing implementation
```

### Frontend: Test Widget Wrappers

**Recommended Pattern:**

```dart
// test_helpers/test_widgets.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class TestWidgetWrapper extends StatelessWidget {
  final Widget child;
  final List<ChangeNotifierProvider> providers;
  final String? initialRoute;

  const TestWidgetWrapper({
    super.key,
    required this.child,
    this.providers = const [],
    this.initialRoute,
  });

  @override
  Widget build(BuildContext context) {
    Widget app = MaterialApp(
      home: child,
    );

    if (providers.isNotEmpty) {
      app = MultiProvider(
        providers: providers,
        child: app,
      );
    }

    return app;
  }
}

// Usage:
await tester.pumpWidget(
  TestWidgetWrapper(
    providers: [
      ChangeNotifierProvider<ChatsProvider>.value(value: mockProvider),
    ],
    child: const ChatsScreen(),
  ),
);
```

---

## Build Order Recommendations

### Phase 1: Test Infrastructure (Build First)

1. **Backend fixtures module structure**
   - Create `tests/fixtures/` directory
   - Extract auth fixtures from conftest.py
   - Extract project fixtures from conftest.py
   - Create LLM mock adapter

2. **Frontend test helpers**
   - Create `test/test_helpers/` directory
   - Create mock providers helper
   - Create test widget wrapper

### Phase 2: Unit Test Coverage

1. **Backend service unit tests**
   - `test_encryption.py` - Fernet encryption/decryption
   - `test_brd_generator.py` - BRD validation logic
   - `test_skill_loader.py` - Skill prompt loading
   - `test_token_tracking.py` - Usage calculation

2. **Backend LLM adapter tests**
   - `test_anthropic_adapter.py`
   - `test_gemini_adapter.py`
   - `test_deepseek_adapter.py`

3. **Frontend provider tests**
   - Expand `chats_provider_test.dart`
   - Add `conversation_provider_test.dart`
   - Add `auth_provider_test.dart`

### Phase 3: Integration Test Coverage

1. **Backend integration tests**
   - Consolidate existing tests into domain-organized structure
   - Add missing edge case coverage
   - Add LLM integration tests with mock adapter

2. **Frontend widget tests**
   - Expand screen-level coverage
   - Add component-level tests
   - Cover error states and edge cases

### Phase 4: API Contract Tests

1. **Backend router tests**
   - Request/response format validation
   - Error response format validation
   - Authentication requirement validation

---

## Anti-Patterns to Avoid

### 1. Shared Mutable State

**Bad:**
```python
# Global mock that tests modify
mock_responses = []

def test_one():
    mock_responses.append("response 1")
    # ...

def test_two():
    # Fails because mock_responses still has "response 1"
```

**Good:**
```python
@pytest.fixture
def mock_responses():
    return []

def test_one(mock_responses):
    mock_responses.append("response 1")

def test_two(mock_responses):
    # Fresh list each test
```

### 2. Over-mocking

**Bad:**
```python
async def test_create_project(mock_db, mock_user_service, mock_project_service):
    # Everything mocked, not testing real behavior
    mock_project_service.create.return_value = Project(...)
```

**Good:**
```python
async def test_create_project(client, db_session, auth_headers):
    # Real database, real service, tests actual behavior
    response = await client.post("/api/projects", ...)

    # Verify in database
    stmt = select(Project).where(Project.name == "Test")
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is not None
```

### 3. Hardcoded Test Data

**Bad:**
```python
async def test_get_thread(client, auth_headers):
    thread_id = "123e4567-e89b-12d3-a456-426614174000"  # May not exist
```

**Good:**
```python
async def test_get_thread(client, auth_headers, test_thread):
    response = await client.get(f"/api/threads/{test_thread.id}", ...)
```

### 4. Test Interdependence

**Bad:**
```dart
testWidgets('test B depends on test A', (tester) async {
  // Assumes some state set by test A
});
```

**Good:**
```dart
testWidgets('test B is independent', (tester) async {
  // Set up all required state in this test
  when(mockProvider.someState).thenReturn(expectedValue);
});
```

---

## Sources

**Backend Testing:**
- FastAPI Testing Documentation: https://fastapi.tiangolo.com/tutorial/testing/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- SQLAlchemy Testing: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncio-scoped-session

**Frontend Testing:**
- Flutter Testing: https://docs.flutter.dev/testing
- Mockito Dart: https://pub.dev/packages/mockito
- Provider Testing: https://pub.dev/packages/provider#testing

**Existing Codebase Patterns:**
- `backend/tests/conftest.py` - Database and client fixtures
- `backend/tests/test_backend_integration.py` - Integration test patterns
- `frontend/test/widget/chats_screen_test.dart` - Widget test patterns
- `frontend/test/unit/chats_provider_test.dart` - Provider unit test patterns

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Backend DB Mocking | HIGH | Pattern already established and working in conftest.py |
| Backend LLM Mocking | MEDIUM | New infrastructure needed, design based on adapter pattern |
| Frontend Service Mocking | HIGH | Mockito pattern well-established in existing tests |
| Frontend Widget Testing | HIGH | Pattern well-established in existing tests |
| Fixture Organization | HIGH | Standard pytest/flutter_test patterns |

---

## Gaps to Address

1. **No LLM mock adapter exists** - Phase should create MockLLMAdapter class
2. **Fixture duplication** - Same fixtures defined in multiple test files
3. **Missing component-level widget tests** - Only screen-level tests exist
4. **No service-level tests in frontend** - Only provider tests exist
5. **SSE stream testing** - Need helper for parsing SSE responses in tests

---

*Generated for v1.9.1 Test Coverage milestone*
