# Domain Pitfalls: Unit Testing FastAPI + Flutter

**Domain:** Comprehensive unit testing for FastAPI backend + Flutter frontend
**Project:** BA Assistant (Multi-LLM adapters, SSE streaming, OAuth, SQLite FTS5, Provider state)
**Researched:** 2026-02-02
**Confidence:** HIGH (verified with official docs and established patterns)

---

## Critical Pitfalls

Mistakes that cause rewrites, CI failures, or major refactoring.

---

### Pitfall 1: Using TestClient for Async Tests

**What goes wrong:** Using FastAPI's synchronous `TestClient` inside async test functions causes event loop conflicts and cryptic errors like `RuntimeError: Task attached to a different loop`.

**Why it happens:** `TestClient` (based on httpx) does internal event loop magic that conflicts with pytest-asyncio's event loop management. When you mark a test as `@pytest.mark.asyncio` but use `TestClient`, you get loop attachment errors.

**Consequences:**
- Tests hang or fail with event loop errors
- Inconsistent behavior between local and CI environments
- Async database clients fail to connect

**Prevention:**
Use `httpx.AsyncClient` with `ASGITransport` for all async tests (already correct in current conftest.py):

```python
from httpx import ASGITransport, AsyncClient

@pytest_asyncio.fixture
async def client(db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
```

**Warning signs:**
- `RuntimeError: Task attached to a different loop`
- Tests pass locally but fail in CI
- Async fixtures not being awaited properly

**Phase to address:** Phase 1 (Test Infrastructure) - Already handled correctly in existing conftest.py

**Sources:**
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [httpx AsyncClient Documentation](https://www.python-httpx.org/async/)

---

### Pitfall 2: Mocking LLM APIs at Wrong Layer

**What goes wrong:** Using `unittest.mock.patch` on httpx/aiohttp directly creates brittle tests that break when internal implementations change. Tests become tightly coupled to HTTP client internals.

**Why it happens:** Natural instinct is to mock at the lowest level (HTTP calls), but this:
- Requires understanding internal request formats
- Breaks when library versions change
- Makes tests unreadable with complex mock setup

**Consequences:**
- Tests break on library updates
- Complex mock setup obscures test intent
- Missing coverage of adapter logic

**Prevention:**
Mock at the adapter layer, not the HTTP layer. BA Assistant already has an adapter pattern (`LLMFactory.create(provider)`):

```python
# GOOD: Mock the adapter
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_llm_adapter():
    adapter = AsyncMock()
    adapter.stream_chat.return_value = mock_stream_generator()
    return adapter

async def test_ai_service_uses_adapter(mock_llm_adapter):
    with patch('app.services.ai_service.LLMFactory.create', return_value=mock_llm_adapter):
        service = AIService(provider="anthropic")
        # Test behavior, not HTTP internals

# BAD: Don't mock httpx directly
# with patch('httpx.AsyncClient.post'):  # Fragile!
```

For actual LLM adapter tests, use recorded responses or mock at transport level:

```python
# For adapter unit tests, use httpx MockTransport
import httpx

def mock_transport(request):
    return httpx.Response(200, json={"content": "mocked response"})

async def test_anthropic_adapter():
    client = httpx.AsyncClient(transport=httpx.MockTransport(mock_transport))
```

**Warning signs:**
- Test setup is longer than test assertions
- Tests fail after `pip install --upgrade`
- Mocking private methods (`_make_request`)

**Phase to address:** Phase 2 (Backend Service Tests) - LLM adapter mocking strategy

**Sources:**
- [Don't Mock Python's HTTPX](https://www.b-list.org/weblog/2023/dec/08/mock-python-httpx/)
- [RESPX - Mock HTTPX](https://lundberg.github.io/respx/)
- [pytest-httpx](https://colin-b.github.io/pytest_httpx/)

---

### Pitfall 3: SSE Streaming Tests Not Consuming Full Stream

**What goes wrong:** Tests that don't fully consume SSE streams leave connections hanging, cause resource leaks, and produce non-deterministic failures.

**Why it happens:** SSE responses are async generators. If you only check the first few events and don't consume the rest, the connection stays open and can interfere with subsequent tests.

**Consequences:**
- Tests hang waiting for connections to close
- Resource exhaustion in CI
- Flaky tests that fail intermittently

**Prevention:**
Always fully consume streams in tests, or use proper async context managers:

```python
# GOOD: Fully consume the stream
@pytest.mark.asyncio
async def test_sse_stream():
    async with client.stream("GET", "/chat/stream") as response:
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))
            if "message_complete" in line:
                break  # Explicit termination

        assert len(events) > 0
        assert events[-1]["event"] == "message_complete"

# Alternative: Use httpx-sse for cleaner SSE parsing
from httpx_sse import aconnect_sse

async def test_sse_with_library():
    async with aconnect_sse(client, "GET", "/chat/stream") as event_source:
        async for sse in event_source.aiter_sse():
            # Process each SSE event
            if sse.event == "message_complete":
                break
```

**Warning signs:**
- Tests time out instead of failing fast
- "Connection not closed" warnings in logs
- Tests pass individually but fail when run together

**Phase to address:** Phase 2 (Backend Service Tests) - SSE endpoint testing

**Sources:**
- [sse-starlette](https://github.com/sysid/sse-starlette)
- [Testing Streaming with httpx](https://github.com/fastapi/fastapi/issues/2006)

---

### Pitfall 4: Database Test Isolation with Shared State

**What goes wrong:** Tests modify database state and affect other tests. Using module/session-scoped fixtures for mutable data causes test order dependencies.

**Why it happens:** For performance, developers use broader fixture scopes (module, session) for database setup. But if one test modifies data, subsequent tests see dirty state.

**Consequences:**
- Tests pass in isolation but fail when run together
- Different results based on test execution order
- CI failures that can't be reproduced locally

**Prevention:**
Use function-scoped fixtures for database sessions (current conftest.py is correct):

```python
@pytest_asyncio.fixture  # Default scope is "function"
async def db_session(db_engine):
    """Each test gets a fresh session."""
    async_session_maker = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        # Session is closed and changes are not committed
```

For tests that need pre-populated data, use explicit setup:

```python
@pytest.fixture
async def project_with_documents(db_session):
    """Explicitly create test data, don't rely on other tests."""
    project = Project(name="Test Project")
    db_session.add(project)
    await db_session.commit()

    doc = Document(project_id=project.id, filename="test.pdf")
    db_session.add(doc)
    await db_session.commit()

    return project, doc
```

**Warning signs:**
- Tests fail with "NOT NULL constraint failed" unexpectedly
- Test output shows data from other tests
- `pytest -x` passes but full suite fails

**Phase to address:** Phase 1 (Test Infrastructure) - Already correct, but document pattern

**Sources:**
- [pytest fixture scopes](https://pytest-with-eric.com/fixtures/pytest-fixture-scope/)
- [pytest-django database access](https://pytest-django.readthedocs.io/en/latest/database.html)

---

### Pitfall 5: FTS5 Virtual Table Not Created in Tests

**What goes wrong:** Tests fail with `no such table: document_fts` because the FTS5 virtual table isn't created during test database setup.

**Why it happens:** SQLAlchemy's `Base.metadata.create_all()` only creates regular tables defined in models. FTS5 virtual tables require separate DDL execution.

**Consequences:**
- Document search tests fail
- False confidence from tests that skip search functionality

**Prevention:**
Current conftest.py handles this correctly. Ensure FTS5 table creation is part of test setup:

```python
@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, ...)

    # Create regular tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # CRITICAL: Create FTS5 virtual table separately
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
```

**Warning signs:**
- "no such table: document_fts" errors
- Search tests skipped or marked xfail
- Tests pass with SQLite but fail with in-memory database

**Phase to address:** Phase 1 (Test Infrastructure) - Already correct

**Sources:**
- [SQLite FTS5 Extension](https://sqlite.org/fts5.html)
- [SQLite FTS with Python](https://charlesleifer.com/blog/using-the-sqlite-json1-and-fts5-extensions-with-python/)

---

### Pitfall 6: Flutter pumpAndSettle Timeout with Infinite Animations

**What goes wrong:** Widget tests using `pumpAndSettle()` hang and eventually timeout when the widget under test contains infinite animations (loading spinners, progress indicators).

**Why it happens:** `pumpAndSettle()` waits until no more frames are scheduled. Infinite animations never stop scheduling frames, causing the 10-minute default timeout.

**Consequences:**
- Tests take 10+ minutes to fail
- CI pipelines timeout
- Flaky tests that sometimes pass (if animation doesn't start)

**Prevention:**
1. Mock or disable animations in tests
2. Use `pump()` with specific durations instead of `pumpAndSettle()`
3. Replace infinite animations with finite ones in test mode

```dart
// BAD: Will timeout if CircularProgressIndicator is showing
await tester.pumpAndSettle();

// GOOD: Pump specific frames
await tester.pump(); // Initial frame
await tester.pump(const Duration(milliseconds: 100)); // Animation frame

// GOOD: Mock the loading state to skip animation
when(mockProvider.isLoading).thenReturn(false);
await tester.pumpAndSettle();

// GOOD: Use pumpAndSettle with short timeout for quick failure
await tester.pumpAndSettle(const Duration(seconds: 5));
```

**Warning signs:**
- Tests hang on screens with loading indicators
- "pumpAndSettle timed out" errors
- Tests pass when run individually but fail in suite

**Phase to address:** Phase 3 (Frontend Widget Tests) - Loading state handling

**Sources:**
- [pumpAndSettle documentation](https://api.flutter.dev/flutter/flutter_test/WidgetTester/pumpAndSettle.html)
- [Flutter pumpAndSettle timeout handling](https://www.dhiwise.com/post/overcoming-flutter-pumpandsettle-timed-out-your-guide)

---

### Pitfall 7: Mockito Mock Classes with Implementation

**What goes wrong:** Mock classes that extend `Mock` but also contain real implementations cause confusing test behavior where some methods are stubbed and others are real.

**Why it happens:** Developers add "helper" methods to mock classes or forget to use `@GenerateNiceMocks` and manually implement methods.

**Consequences:**
- Tests pass for wrong reasons (real code runs)
- Verification fails unexpectedly
- Inconsistent stubbing behavior

**Prevention:**
Mock classes should ONLY extend Mock, with NO implementation:

```dart
// GOOD: Use code generation
@GenerateNiceMocks([MockSpec<ThreadService>()])
void main() {
  late MockThreadService mockService;

  setUp(() {
    mockService = MockThreadService();
  });
}

// BAD: Don't add implementations to mocks
class BadMockService extends Mock implements ThreadService {
  // DON'T DO THIS - real implementation defeats mocking purpose
  @override
  Future<List<Thread>> getThreads() async {
    return []; // This bypasses stubbing!
  }
}
```

Current project correctly uses `@GenerateNiceMocks` - maintain this pattern.

**Warning signs:**
- `when()` setup has no effect
- `verify()` says method wasn't called but it was
- Tests pass without any stubbing

**Phase to address:** Phase 3 (Frontend Widget Tests) - Mock generation patterns

**Sources:**
- [Mockito Dart package](https://pub.dev/packages/mockito)
- [Flutter testing with Mockito](https://docs.flutter.dev/cookbook/testing/unit/mocking)

---

## Moderate Pitfalls

Mistakes that cause delays, confusion, or technical debt.

---

### Pitfall 8: Testing Provider State Without Listeners

**What goes wrong:** Testing ChangeNotifier state changes without listening for notifications misses the actual update mechanism and can pass even when `notifyListeners()` is never called.

**Why it happens:** Unit tests directly check provider properties after calling methods, but don't verify that notifications are sent to rebuild widgets.

**Consequences:**
- Tests pass but UI doesn't update in real app
- Missing coverage of notification timing
- Subtle bugs where state changes but widgets don't rebuild

**Prevention:**
Test both state AND notification behavior:

```dart
test('loadThreads notifies listeners on completion', () async {
  var notificationCount = 0;
  provider.addListener(() => notificationCount++);

  when(mockService.getThreads()).thenAnswer((_) async => [mockThread]);

  await provider.loadThreads();

  expect(provider.threads, isNotEmpty);
  expect(notificationCount, greaterThan(0)); // Verify notification sent
});
```

**Warning signs:**
- Provider tests pass but widget tests fail
- UI shows stale data after operations complete
- Tests never fail even with broken notification logic

**Phase to address:** Phase 3 (Frontend Unit Tests) - Provider testing patterns

**Sources:**
- [Testing ChangeNotifier](https://medium.com/@shreebhagwat94/unit-test-the-change-notifier-in-flutter-74fb75e8fe58)
- [Flutter Provider testing](https://docs.flutter.dev/data-and-backend/state-mgmt/simple)

---

### Pitfall 9: JWT Token Testing Without Time Control

**What goes wrong:** Tests involving JWT tokens fail intermittently because token expiration is time-dependent. Tests pass locally but fail in slow CI environments.

**Why it happens:** JWT tokens have `exp` claims based on real time. If test execution is slow, tokens expire mid-test.

**Consequences:**
- Flaky tests in CI
- Tests fail on slow machines
- Race conditions in authentication tests

**Prevention:**
1. Use dependency injection to override token generation in tests
2. Use FastAPI's `dependency_overrides` to bypass JWT validation entirely
3. Generate tokens with very long expiration for tests

```python
# Option 1: Override the auth dependency entirely
async def mock_get_current_user():
    return User(id="test-user-id", email="test@example.com")

app.dependency_overrides[get_current_user] = mock_get_current_user

# Option 2: Generate long-lived test tokens
def create_test_token(user_id: str, expires_in_hours: int = 24):
    """Generate test token with extended expiration."""
    expire = datetime.utcnow() + timedelta(hours=expires_in_hours)
    return jwt.encode({"sub": user_id, "exp": expire}, SECRET_KEY)

@pytest.fixture
def auth_headers():
    token = create_test_token("test-user")
    return {"Authorization": f"Bearer {token}"}
```

**Warning signs:**
- `401 Unauthorized` errors that appear randomly
- Tests pass quickly but fail when run with coverage
- Time-based test failures around midnight or hour boundaries

**Phase to address:** Phase 2 (Backend Tests) - Auth testing strategy

**Sources:**
- [FastAPI JWT Testing](https://fastapitutorial.com/blog/fastapi-unit-test-jwt-header/)
- [FastAPI dependency overrides](https://plainenglish.io/blog/how-to-mock-fastapi-dependencies-in-pytest)

---

### Pitfall 10: Async Test Setup/Teardown Race Conditions

**What goes wrong:** Async fixtures don't complete setup before tests run, or teardown interferes with the next test.

**Why it happens:** pytest-asyncio fixture lifecycle can be subtle. Using `yield` in async fixtures without proper cleanup leads to resource leaks.

**Consequences:**
- Tests interfere with each other
- Database connections left open
- Unpredictable test failures

**Prevention:**
Ensure fixtures properly await cleanup:

```python
@pytest_asyncio.fixture
async def db_session(db_engine):
    session = AsyncSession(db_engine)
    try:
        yield session
    finally:
        await session.close()  # Explicit cleanup

@pytest_asyncio.fixture
async def client(db_session):
    async def override():
        yield db_session

    app.dependency_overrides[get_db] = override

    async with AsyncClient(...) as ac:
        yield ac

    app.dependency_overrides.clear()  # Cleanup after yield
```

**Warning signs:**
- "Session is closed" errors
- Tests pass individually but fail together
- Resource warnings about unclosed connections

**Phase to address:** Phase 1 (Test Infrastructure)

**Sources:**
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI async fixtures](https://github.com/fastapi/fastapi/discussions/8415)

---

### Pitfall 11: Cross-Platform Flutter Test Differences

**What goes wrong:** Widget tests pass on one platform but fail on another due to platform-specific rendering or plugin behavior.

**Why it happens:** Flutter plugins use platform channels that don't exist in unit/widget tests. Platform-specific code paths execute differently.

**Consequences:**
- CI failures on different platforms
- Tests pass locally (macOS) but fail in CI (Linux)
- Plugins throw `MissingPluginException`

**Prevention:**
1. Wrap plugins in injectable services
2. Use conditional test setup for platform differences
3. Mock platform channels explicitly

```dart
// Wrap plugins for testability
class StorageService {
  Future<String?> read(String key) async {
    return FlutterSecureStorage().read(key: key);
  }
}

// In tests, inject mock
class MockStorageService extends Mock implements StorageService {}

// For platform channels, set up mock handlers
TestWidgetsFlutterBinding.ensureInitialized();
TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
    .setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/path_provider'),
      (call) async => '/tmp',
    );
```

**Warning signs:**
- `MissingPluginException` in tests
- Platform-specific test skips (`skip: Platform.isLinux`)
- Different test results on different developer machines

**Phase to address:** Phase 3 (Frontend Tests) - Platform abstraction

**Sources:**
- [Flutter testing plugins](https://docs.flutter.dev/testing/testing-plugins)
- [Flutter platform testing](https://flutter.dev/docs/testing/overview)

---

## Minor Pitfalls

Mistakes that cause annoyance but are easily fixable.

---

### Pitfall 12: Overly Specific Assertions on LLM Output

**What goes wrong:** Tests that assert exact LLM response content break when prompts are updated or models change their output format.

**Why it happens:** Natural to write `expect(response.text).toBe("exact response")`, but LLM outputs are inherently variable.

**Consequences:**
- Tests fail on every prompt update
- Maintenance burden increases
- Tests become obstacles to prompt improvement

**Prevention:**
Test structure and behavior, not exact content:

```python
# BAD: Brittle exact match
assert response["text"] == "Welcome! Let me help you gather requirements..."

# GOOD: Test structure and presence of key elements
assert "event" in response
assert response["event"] == "text_delta"
assert len(response["data"]["text"]) > 0

# GOOD: Test tool calls structure
assert any(tc["name"] == "search_documents" for tc in tool_calls)

# GOOD: Test that streaming yields expected event types
events = [e["event"] for e in all_events]
assert "text_delta" in events
assert "message_complete" in events
```

**Warning signs:**
- Tests fail after "improving" prompts
- Large strings in test assertions
- Tests that only pass with specific model versions

**Phase to address:** Phase 2 (Backend Tests) - LLM response testing

---

### Pitfall 13: Missing await in Flutter Async Tests

**What goes wrong:** Forgetting `await` before async operations in tests causes tests to pass before operations complete.

**Why it happens:** Dart doesn't always warn about unawaited futures, and tests may appear to pass because they complete before assertions run.

**Consequences:**
- False positives (tests pass when they shouldn't)
- Race conditions in test assertions
- Verification happens before mock is called

**Prevention:**
Use strict linting rules and careful review:

```dart
// BAD: Missing await - test passes immediately
test('loads data', () async {
  provider.loadData();  // Missing await!
  expect(provider.data, isNotEmpty);  // Runs before loadData completes
});

// GOOD: Properly awaited
test('loads data', () async {
  await provider.loadData();
  expect(provider.data, isNotEmpty);
});

// Enable linting in analysis_options.yaml
analyzer:
  errors:
    unawaited_futures: error
```

**Warning signs:**
- Tests pass but integration fails
- Verification says method not called
- Sporadic test failures

**Phase to address:** Phase 3 (Frontend Tests) - Lint configuration

---

### Pitfall 14: Verbose Test Output Obscuring Failures

**What goes wrong:** Tests produce excessive logging output that makes it hard to find actual failures.

**Why it happens:** Application code has debug logging that runs during tests. Each test prints pages of logs.

**Consequences:**
- CI logs are unreadable
- Actual errors buried in noise
- Developers ignore test output

**Prevention:**
Configure logging levels for tests:

```python
# conftest.py
import logging

@pytest.fixture(autouse=True)
def suppress_logging():
    """Reduce log noise in tests."""
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

```dart
// In Flutter tests
setUp(() {
  // Suppress debug output
  debugPrint = (String? message, {int? wrapWidth}) {};
});
```

**Warning signs:**
- Test output is thousands of lines
- Actual failures scroll off screen
- Developers run tests with `-q` (quiet) always

**Phase to address:** Phase 1 (Test Infrastructure)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Test infrastructure setup | FTS5 table not created | Include DDL in db_engine fixture (already done) |
| LLM adapter tests | Mocking at wrong layer | Mock adapter interface, not HTTP client |
| SSE streaming tests | Stream not fully consumed | Use async context managers, explicit termination |
| JWT auth tests | Time-dependent failures | Use dependency overrides or long-lived test tokens |
| Provider unit tests | Missing notification testing | Verify notifyListeners() called |
| Widget tests with loading states | pumpAndSettle timeout | Mock loading states or use pump() with duration |
| Cross-platform tests | Plugin failures | Wrap plugins in injectable services |
| Document search tests | FTS5 not available | Verify SQLite compiled with FTS5 support |

---

## BA Assistant-Specific Testing Considerations

### Multi-LLM Adapter Testing

The project uses an adapter pattern with `LLMFactory.create(provider)`. When testing:

1. **Unit tests for AIService:** Mock `LLMFactory.create()` to return a mock adapter
2. **Unit tests for adapters:** Use httpx MockTransport for HTTP-level testing
3. **Integration tests:** Consider using recorded API responses (not live calls)

```python
# Example: Testing AIService with mocked adapter
@pytest.fixture
def mock_anthropic_adapter():
    adapter = AsyncMock()
    async def stream_chunks():
        yield StreamChunk(chunk_type="text", content="Hello")
        yield StreamChunk(chunk_type="complete", usage={"input": 10, "output": 5})
    adapter.stream_chat.return_value = stream_chunks()
    return adapter

async def test_ai_service_streams(mock_anthropic_adapter):
    with patch('app.services.ai_service.LLMFactory.create', return_value=mock_anthropic_adapter):
        service = AIService(provider="anthropic")
        events = [e async for e in service.stream_chat(messages, project_id, thread_id, db)]
        assert any(e["event"] == "text_delta" for e in events)
```

### SSE Heartbeat Testing

The project's `stream_with_heartbeat` wrapper needs specific testing:

```python
async def test_heartbeat_during_long_thinking():
    """Ensure heartbeats sent during extended thinking delays."""
    slow_generator = create_slow_generator(delay_seconds=10)

    events = []
    async for event in stream_with_heartbeat(slow_generator, initial_delay=1, heartbeat_interval=2):
        events.append(event)
        if len(events) > 5:  # Collect enough events
            break

    heartbeats = [e for e in events if e.get("comment") == "heartbeat"]
    assert len(heartbeats) >= 1, "Should send heartbeats during silence"
```

### Document Search FTS5 Testing

FTS5 testing requires proper index population:

```python
async def test_document_search_returns_results(db_session, project_with_documents):
    """FTS5 search returns matching documents."""
    project, doc = project_with_documents

    # Populate FTS5 index (mimics what upload does)
    await db_session.execute(text("""
        INSERT INTO document_fts (document_id, filename, content)
        VALUES (:doc_id, :filename, :content)
    """), {"doc_id": doc.id, "filename": doc.filename, "content": "test content with searchable keywords"})
    await db_session.commit()

    results = await search_documents(db_session, project.id, "searchable keywords")
    assert len(results) > 0
    assert results[0][1] == doc.filename
```

---

## Quick Reference Checklist

Before submitting tests for review:

- [ ] All async tests properly `await` operations
- [ ] Fixtures use function scope for mutable state
- [ ] LLM responses mocked at adapter layer, not HTTP layer
- [ ] SSE streams fully consumed or properly terminated
- [ ] No pumpAndSettle() with infinite animations
- [ ] Mock classes have no real implementations
- [ ] JWT/auth tests use dependency overrides
- [ ] Provider tests verify notification behavior
- [ ] Logging noise suppressed in test config
- [ ] Platform-specific code wrapped for testability

---

## Sources

**FastAPI Testing:**
- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [pytest-with-eric FastAPI Testing](https://pytest-with-eric.com/pytest-advanced/pytest-fastapi-testing/)

**Flutter Testing:**
- [Flutter Testing Overview](https://docs.flutter.dev/testing/overview)
- [Mock dependencies using Mockito](https://docs.flutter.dev/cookbook/testing/unit/mocking)
- [DCM - Navigating Hard Parts of Testing](https://dcm.dev/blog/2025/07/30/navigating-hard-parts-testing-flutter-developers)
- [15 Common Flutter Mistakes](https://dcm.dev/blog/2025/03/24/fifteen-common-mistakes-flutter-dart-development)

**Mocking External APIs:**
- [Testing APIs with PyTest Mocks](https://codilime.com/blog/testing-apis-with-pytest-mocks-in-python/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Don't Mock HTTPX](https://www.b-list.org/weblog/2023/dec/08/mock-python-httpx/)
- [MockGPT for LLM Testing](https://www.wiremock.io/post/mockgpt-mock-openai-api)

**Database Testing:**
- [pytest fixture scopes](https://pytest-with-eric.com/fixtures/pytest-fixture-scope/)
- [pytest setup and teardown](https://pytest-with-eric.com/pytest-best-practices/pytest-setup-teardown/)
- [SQLite FTS5](https://sqlite.org/fts5.html)

**Streaming/SSE Testing:**
- [sse-starlette](https://github.com/sysid/sse-starlette)
- [httpx-sse](https://pypi.org/project/httpx-sse/)
- [Testing streaming responses](https://github.com/fastapi/fastapi/issues/2006)
