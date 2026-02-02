# Phase 29: Backend Service Tests - Research

**Researched:** 2026-02-02
**Domain:** Python service unit testing (FastAPI/SQLAlchemy/async)
**Confidence:** HIGH

## Summary

Phase 29 requires unit test coverage for all backend service modules in `app/services/`. The codebase has 12 service modules with varying complexity and dependency patterns. The Phase 28 infrastructure provides excellent testing foundations including:

- Factory-boy factories with `@register` decorator for all models
- MockLLMAdapter with call_history for LLM interaction assertions
- pytest-asyncio configured with in-memory SQLite
- Fixture discovery via pytest_plugins

Key insight: The services fall into three categories by dependency complexity:
1. **Pure functions** (no dependencies): `brd_generator.validate_brd_content()`, `conversation_service.estimate_tokens()`
2. **Database-only services**: `auth_service`, `token_tracking`, `document_search`
3. **LLM-dependent services**: `ai_service`, `summarization_service`, `agent_service`

**Primary recommendation:** Start with pure functions and database-only services for quick wins, then tackle LLM services using MockLLMAdapter.

---

## Service Inventory

### Services Requiring Test Coverage

| Service | Module | Public Functions/Methods | Lines | Complexity |
|---------|--------|-------------------------|-------|------------|
| auth_service | `auth_service.py` | OAuth2Service class (5 public methods) | 268 | MEDIUM |
| ai_service | `ai_service.py` | AIService class, stream_with_heartbeat() | 882 | HIGH |
| conversation_service | `conversation_service.py` | save_message(), build_conversation_context(), estimate_tokens(), truncate_conversation() | 167 | LOW |
| document_search | `document_search.py` | index_document(), search_documents() | 72 | LOW |
| token_tracking | `token_tracking.py` | calculate_cost(), track_token_usage(), get_monthly_usage(), check_user_budget() | 157 | LOW |
| export_service | `export_service.py` | export_markdown(), export_pdf(), export_docx() | 196 | MEDIUM |
| skill_loader | `skill_loader.py` | load_skill_prompt(), get_skill_references(), clear_skill_cache() | 139 | LOW |
| brd_generator | `brd_generator.py` | validate_brd_content(), get_brd_template_structure(), format_preflight_checklist(), generate_brd_tool() | 430 | MEDIUM |
| agent_service | `agent_service.py` | AgentService class (stream_chat), search_documents_tool(), save_artifact_tool() | 384 | HIGH |
| encryption | `encryption.py` | EncryptionService class (encrypt/decrypt) | 56 | LOW |
| summarization_service | `summarization_service.py` | generate_thread_summary(), maybe_update_summary() | 169 | MEDIUM |

### Services NOT Listed in Requirements (Lower Priority)

| Service | Module | Reason |
|---------|--------|--------|
| llm/anthropic_adapter | `llm/anthropic_adapter.py` | LLM adapter - covered by MockLLMAdapter |
| llm/gemini_adapter | `llm/gemini_adapter.py` | LLM adapter - covered by MockLLMAdapter |
| llm/deepseek_adapter | `llm/deepseek_adapter.py` | LLM adapter - covered by MockLLMAdapter |
| llm/factory | `llm/factory.py` | Factory - simple routing logic |

---

## Dependency Analysis

### Service Dependency Matrix

| Service | DB Session | LLM/API | Settings | Other Services | External Files |
|---------|------------|---------|----------|----------------|----------------|
| auth_service | YES | OAuth HTTP (authlib) | YES | None | None |
| ai_service | YES | LLM Adapter | NO | document_search, LLMFactory | None |
| conversation_service | YES | NO | NO | None | None |
| document_search | YES (raw SQL) | NO | NO | None | None |
| token_tracking | YES | NO | NO | None | None |
| export_service | NO | NO | NO | None | Templates |
| skill_loader | NO | NO | YES | None | Skill files |
| brd_generator | YES (via context) | NO | NO | None | None |
| agent_service | YES (via context) | Claude SDK | YES | document_search, skill_loader, brd_generator | None |
| encryption | NO | NO | YES | None | None |
| summarization_service | YES | Anthropic API | YES | token_tracking, conversation_service | None |

### Dependency Patterns

**Pattern 1: Pure Functions (Easiest to Test)**
- `estimate_tokens()`, `estimate_messages_tokens()`, `truncate_conversation()` in conversation_service
- `calculate_cost()` in token_tracking
- `validate_brd_content()`, `get_brd_template_structure()`, `format_preflight_checklist()` in brd_generator
- `export_markdown()` in export_service (no dependencies)

**Pattern 2: Database-Only (Use db_session fixture)**
- `save_message()`, `build_conversation_context()`, `get_message_count()` in conversation_service
- `track_token_usage()`, `get_monthly_usage()`, `check_user_budget()` in token_tracking
- `index_document()`, `search_documents()` in document_search
- `_upsert_user()` in auth_service

**Pattern 3: LLM-Dependent (Use MockLLMAdapter)**
- `AIService.stream_chat()` - Uses LLM adapter
- `AgentService.stream_chat()` - Uses Claude SDK
- `generate_thread_summary()`, `maybe_update_summary()` in summarization_service - Uses Anthropic client directly

**Pattern 4: External Dependencies (Mock Required)**
- `OAuth2Service` methods - Mock authlib AsyncOAuth2Client
- `export_pdf()` - Mock/skip WeasyPrint on systems without GTK
- `load_skill_prompt()` - Mock file system or use test fixtures

---

## Testing Strategy Per Service

### 1. auth_service.py (OAuth2Service)

**Public Methods:**
- `get_google_auth_url(redirect_uri)` -> (url, state)
- `process_google_callback(code, state, expected_state, redirect_uri)` -> User
- `get_microsoft_auth_url(redirect_uri)` -> (url, state)
- `process_microsoft_callback(code, state, expected_state, redirect_uri)` -> User
- `_upsert_user(oauth_provider, oauth_id, email, display_name)` -> User (semi-private but testable)

**Test Strategy:**
- Mock `AsyncOAuth2Client` from authlib
- Test `_generate_state()` produces 32-char hex
- Test CSRF validation (state mismatch raises ValueError)
- Test user creation (new user) and update (existing user)
- Use UserFactory for existing user scenarios

**Fixtures Needed:**
- `mock_oauth_client` - Mocked AsyncOAuth2Client
- `google_user_info` - Sample Google API response
- `microsoft_user_info` - Sample Microsoft Graph API response

### 2. ai_service.py (AIService)

**Public Methods/Functions:**
- `stream_with_heartbeat(data_gen, ...)` - Async generator wrapper
- `AIService.__init__(provider)` - Creates adapter
- `AIService.execute_tool(tool_name, tool_input, ...)` - Executes tools
- `AIService.stream_chat(messages, project_id, thread_id, db)` - Main streaming

**Test Strategy:**
- Use MockLLMAdapter (from Phase 28) for LLM interactions
- Test `stream_with_heartbeat()` with mock async generator
- Test `execute_tool()` for each tool type (save_artifact, search_documents)
- Test `stream_chat()` end-to-end with MockLLMAdapter
- Test error handling paths

**Fixtures Needed:**
- `mock_llm_adapter` (exists)
- `mock_data_generator` - For heartbeat testing
- Use ThreadFactory, ArtifactFactory for tool tests

**Critical Tests:**
- Tool execution creates artifacts in DB
- Tool execution searches documents correctly
- Streaming yields proper SSE event format
- Error chunks yield error events

### 3. conversation_service.py

**Public Functions:**
- `estimate_tokens(text)` -> int
- `estimate_messages_tokens(messages)` -> int
- `save_message(db, thread_id, role, content)` -> Message
- `build_conversation_context(db, thread_id)` -> List[Dict]
- `truncate_conversation(messages, max_tokens)` -> List[Dict]
- `get_message_count(db, thread_id)` -> int

**Test Strategy:**
- Pure function tests: estimate_tokens, truncate_conversation
- Database tests: save_message, build_conversation_context, get_message_count
- Test truncation logic (keeps recent, adds summary note)

**Fixtures Needed:**
- Use ThreadFactory, MessageFactory
- No mocking needed for pure functions

**Critical Tests:**
- Token estimation is approximately correct
- Truncation preserves recent messages
- Message saving updates thread.updated_at
- build_conversation_context returns Claude format

### 4. document_search.py

**Public Functions:**
- `index_document(db, doc_id, filename, content)` -> None
- `search_documents(db, project_id, query)` -> List[Tuple]

**Test Strategy:**
- Requires FTS5 table (db_session fixture creates this)
- Test indexing and retrieval
- Test empty query returns empty
- Test project isolation

**Fixtures Needed:**
- Use DocumentFactory, ProjectFactory
- db_session already creates FTS5 table

**Critical Tests:**
- Indexing document makes it searchable
- Search returns relevant results with snippets
- Empty project_id returns empty
- Project isolation (can't search other projects)

### 5. token_tracking.py

**Public Functions:**
- `calculate_cost(model, input_tokens, output_tokens)` -> Decimal
- `track_token_usage(db, user_id, model, input_tokens, output_tokens, endpoint)` -> TokenUsage
- `get_monthly_usage(db, user_id)` -> dict
- `check_user_budget(db, user_id, monthly_limit)` -> bool

**Test Strategy:**
- Pure function: calculate_cost with different models
- Database functions: track, aggregate, check budget
- Test month boundary for monthly aggregation

**Fixtures Needed:**
- Use UserFactory
- Create TokenUsage directly or via factory

**Critical Tests:**
- Cost calculation precision (Decimal)
- Monthly aggregation resets at month start
- Budget check returns False when over limit

### 6. export_service.py

**Public Functions:**
- `export_markdown(artifact)` -> BytesIO
- `export_pdf(artifact)` -> BytesIO (may raise ImportError)
- `export_docx(artifact)` -> BytesIO
- `get_content_type(format)` -> str
- `get_file_extension(format)` -> str

**Test Strategy:**
- Test markdown export (simple)
- Test docx export (verify document structure)
- PDF export: skip if WeasyPrint not available
- Test content type and extension helpers

**Fixtures Needed:**
- Use ArtifactFactory

**Critical Tests:**
- Markdown output contains title and content
- DOCX has correct structure (headers, paragraphs)
- PDF gracefully handles missing GTK

### 7. skill_loader.py

**Public Functions:**
- `get_skill_directory()` -> Path
- `get_skill_references(skill_dir)` -> Dict[str, str]
- `load_skill_prompt()` -> str (cached)
- `clear_skill_cache()` -> None

**Test Strategy:**
- Mock settings.skill_path for testing
- Test with real skill files if available
- Test SkillLoadError on missing files
- Test cache behavior

**Fixtures Needed:**
- `mock_skill_directory` with test files
- Or use real skill files with Path mocking

**Critical Tests:**
- Load prompt includes SKILL.md content
- Load prompt includes all references
- Cache works (second call is same object)
- Missing file raises SkillLoadError

### 8. brd_generator.py

**Public Functions:**
- `validate_brd_content(content)` -> ValidationResult
- `get_brd_template_structure()` -> str
- `format_preflight_checklist(...)` -> Tuple[bool, str]
- `generate_brd_tool(args)` -> Dict (async, requires context)

**Test Strategy:**
- validate_brd_content: test with valid/invalid BRDs
- format_preflight_checklist: test all combinations
- generate_brd_tool: mock context variables

**Fixtures Needed:**
- Sample BRD content (valid and invalid)
- Context variable mocks

**Critical Tests:**
- Validation catches missing required sections
- Validation detects placeholder text
- Validation warns on technical terms
- Preflight checklist formatting

### 9. agent_service.py (AgentService)

**Public Methods:**
- `AgentService.__init__()` - Loads skill, creates tools
- `AgentService.stream_chat(messages, project_id, thread_id, db)` - Main entry

Tool functions (decorated with @tool):
- `search_documents_tool(args)` -> Dict
- `save_artifact_tool(args)` -> Dict

**Test Strategy:**
- Mock Claude SDK `query()` function
- Test tool functions via context variable setup
- Test fallback prompt on skill load failure
- Test SSE event generation

**Fixtures Needed:**
- Mock claude_agent_sdk.query
- Context variable setup helpers
- Use existing factories

**Critical Tests:**
- Tool execution through context vars
- Event yielding (text_delta, artifact_created)
- Error handling

### 10. encryption.py (EncryptionService)

**Public Methods:**
- `EncryptionService.__init__()` - Gets key from settings
- `EncryptionService.encrypt_document(plaintext)` -> bytes
- `EncryptionService.decrypt_document(ciphertext)` -> str
- `get_encryption_service()` -> EncryptionService (singleton)

**Test Strategy:**
- Test encrypt/decrypt roundtrip
- Test different content types (UTF-8, special chars)
- Test singleton behavior

**Fixtures Needed:**
- None (uses FERNET_KEY from env, already set in db_fixtures)

**Critical Tests:**
- Roundtrip encryption preserves content
- Different keys produce different ciphertext
- Invalid ciphertext raises error

### 11. summarization_service.py

**Public Functions:**
- `format_messages_for_summary(messages)` -> str
- `generate_thread_summary(client, messages, current_title)` -> Tuple[str, dict]
- `maybe_update_summary(db, thread_id, user_id)` -> Optional[str]

**Test Strategy:**
- Pure function: format_messages_for_summary
- Mock Anthropic client for generate_thread_summary
- Full flow test with mock for maybe_update_summary

**Fixtures Needed:**
- `mock_anthropic_client` - Mocked AsyncAnthropic
- Use ThreadFactory, MessageFactory

**Critical Tests:**
- Format truncates long messages
- Summary respects max length
- Updates only at interval (5, 10, 15... messages)
- Token usage tracked after summary

---

## Fixture Requirements

### Existing Fixtures (from Phase 28)

| Fixture | Location | Description |
|---------|----------|-------------|
| `db_session` | db_fixtures.py | Async SQLAlchemy session with FTS5 |
| `db_engine` | db_fixtures.py | Test database engine |
| `client` | auth_fixtures.py | Test HTTP client with DB override |
| `auth_headers` | auth_fixtures.py | Auth header factory |
| `mock_llm_adapter` | llm_fixtures.py | MockLLMAdapter factory |
| `mock_llm_text_response` | llm_fixtures.py | Pre-configured text adapter |
| `mock_llm_tool_response` | llm_fixtures.py | Pre-configured tool adapter |
| `mock_llm_error` | llm_fixtures.py | Pre-configured error adapter |
| `user` | factories.py (via @register) | UserFactory instance |
| `project` | factories.py (via @register) | ProjectFactory instance |
| `document` | factories.py (via @register) | DocumentFactory instance |
| `thread` | factories.py (via @register) | ThreadFactory instance |
| `message` | factories.py (via @register) | MessageFactory instance |
| `artifact` | factories.py (via @register) | ArtifactFactory instance |

### New Fixtures Needed

| Fixture | Purpose | Implementation |
|---------|---------|----------------|
| `mock_oauth_client` | Mock authlib OAuth client | pytest-mock/unittest.mock |
| `mock_anthropic_client` | Mock Anthropic API client | pytest-mock/unittest.mock |
| `mock_claude_sdk` | Mock claude_agent_sdk.query | pytest-mock patch |
| `valid_brd_content` | Sample valid BRD markdown | Static string fixture |
| `invalid_brd_content` | Sample BRD missing sections | Static string fixture |
| `user_with_project` | User + Project in DB | Composite fixture |
| `thread_with_messages` | Thread + Messages in DB | Composite fixture |
| `token_usage_samples` | TokenUsage records for aggregation tests | Factory calls |

### Fixture Placement Strategy

```
tests/
  fixtures/
    db_fixtures.py        # Existing - db_session, db_engine
    auth_fixtures.py      # Existing - client, auth_headers
    llm_fixtures.py       # Existing - MockLLMAdapter fixtures
    factories.py          # Existing - Model factories
    service_fixtures.py   # NEW - Service-specific fixtures
  unit/
    services/
      conftest.py         # Service test config (imports fixtures)
      test_auth_service.py
      test_ai_service.py
      test_conversation_service.py
      ...
```

---

## Coverage Targets and Priorities

### Priority Order (Quick Wins First)

1. **Pure functions** (highest ROI, easiest to test)
   - conversation_service: estimate_tokens, truncate_conversation
   - token_tracking: calculate_cost
   - brd_generator: validate_brd_content, format_preflight_checklist
   - export_service: export_markdown, get_content_type

2. **Database-only services** (use existing fixtures)
   - conversation_service: save_message, build_conversation_context
   - token_tracking: track_token_usage, get_monthly_usage
   - document_search: index_document, search_documents
   - encryption: encrypt/decrypt

3. **Services with mocking** (more complex)
   - auth_service: OAuth flow with mocked client
   - skill_loader: File system interaction
   - summarization_service: Mocked Anthropic client

4. **LLM-dependent services** (most complex)
   - ai_service: Full streaming with MockLLMAdapter
   - agent_service: Claude SDK mocking

### Coverage Targets Per Service

| Service | Target Coverage | Critical Paths |
|---------|-----------------|----------------|
| auth_service | 80%+ | CSRF validation, user upsert |
| ai_service | 80%+ | Tool execution, streaming, errors |
| conversation_service | 90%+ | All functions testable |
| document_search | 85%+ | Indexing, search, isolation |
| token_tracking | 90%+ | Cost calculation, budget check |
| export_service | 75%+ | Skip PDF if no GTK |
| skill_loader | 80%+ | Load, cache, errors |
| brd_generator | 85%+ | Validation, preflight |
| agent_service | 75%+ | Tool execution, events |
| encryption | 95%+ | Roundtrip, errors |
| summarization_service | 80%+ | Format, generate, interval |

---

## Known Complexities and Risks

### Complexity 1: Async Generator Testing

**Challenge:** Testing `stream_chat()` methods that yield SSE events.

**Solution:**
```python
async def test_stream_chat():
    events = []
    async for event in service.stream_chat(...):
        events.append(event)

    assert any(e["event"] == "text_delta" for e in events)
    assert events[-1]["event"] == "message_complete"
```

### Complexity 2: Context Variable Setup

**Challenge:** `agent_service.py` and `brd_generator.py` use ContextVar for passing db/thread_id.

**Solution:**
```python
from app.services.agent_service import _db_context, _thread_id_context

def test_tool_with_context(db_session, thread):
    _db_context.set(db_session)
    _thread_id_context.set(thread.id)

    result = await save_artifact_tool({...})
```

### Complexity 3: FTS5 Testing

**Challenge:** document_search requires FTS5 virtual table.

**Solution:** Already handled in db_fixtures.py - creates FTS5 table with engine. Tests should index before searching.

### Complexity 4: External API Mocking (OAuth, Anthropic)

**Challenge:** auth_service and summarization_service make real HTTP calls.

**Solution:**
```python
@pytest.fixture
def mock_anthropic_client(mocker):
    mock_client = mocker.Mock(spec=anthropic.AsyncAnthropic)
    mock_response = mocker.Mock()
    mock_response.content = [mocker.Mock(text="Generated title")]
    mock_response.usage = mocker.Mock(input_tokens=50, output_tokens=10)
    mock_client.messages.create = mocker.AsyncMock(return_value=mock_response)
    return mock_client
```

### Complexity 5: PDF Export (GTK Dependency)

**Challenge:** `export_pdf()` requires WeasyPrint with GTK3.

**Solution:**
```python
@pytest.mark.skipif(
    not has_weasyprint(),
    reason="WeasyPrint/GTK not available"
)
def test_export_pdf():
    ...
```

### Risk 1: LRU Cache in skill_loader

**Risk:** `load_skill_prompt()` uses `@lru_cache` - tests may pollute each other.

**Mitigation:** Call `clear_skill_cache()` in fixture teardown.

### Risk 2: Singleton in encryption

**Risk:** `get_encryption_service()` returns singleton - tests may share state.

**Mitigation:** Reset singleton in fixture or test directly on EncryptionService class.

### Risk 3: Settings Dependencies

**Risk:** Services read from `app.config.settings` which requires env vars.

**Mitigation:** db_fixtures.py already sets FERNET_KEY and SECRET_KEY. Add others as needed.

---

## Code Examples

### Example: Testing Pure Function

```python
# tests/unit/services/test_conversation_service.py

from app.services.conversation_service import estimate_tokens, truncate_conversation

class TestEstimateTokens:
    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_short_text_estimation(self):
        # 4 chars per token
        text = "Hello world"  # 11 chars
        assert estimate_tokens(text) == 2  # 11 // 4 = 2

    def test_long_text_estimation(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100


class TestTruncateConversation:
    def test_no_truncation_when_under_limit(self):
        messages = [{"role": "user", "content": "Hi"}]
        result = truncate_conversation(messages, 10000)
        assert result == messages

    def test_truncation_keeps_recent_messages(self):
        messages = [
            {"role": "user", "content": "a" * 1000},
            {"role": "assistant", "content": "b" * 1000},
            {"role": "user", "content": "recent"}
        ]
        result = truncate_conversation(messages, 100)  # Very low limit

        # Should have summary + recent
        assert "[System note:" in result[0]["content"]
        assert result[-1]["content"] == "recent"
```

### Example: Testing Database Service

```python
# tests/unit/services/test_token_tracking.py

import pytest
from decimal import Decimal
from app.services.token_tracking import (
    calculate_cost, track_token_usage, get_monthly_usage, check_user_budget
)


class TestCalculateCost:
    def test_known_model_pricing(self):
        cost = calculate_cost("claude-sonnet-4-5-20250929", 1000, 500)
        # $3/1M input + $15/1M output
        expected = Decimal("0.003") + Decimal("0.0075")
        assert cost == expected

    def test_default_pricing_for_unknown_model(self):
        cost = calculate_cost("unknown-model", 1000000, 0)
        assert cost == Decimal("3.00")


class TestTrackTokenUsage:
    @pytest.mark.asyncio
    async def test_creates_usage_record(self, db_session, user):
        db_session.add(user)
        await db_session.commit()

        usage = await track_token_usage(
            db_session, user.id, "claude-sonnet", 100, 50, "/api/chat"
        )

        assert usage.user_id == user.id
        assert usage.request_tokens == 100
        assert usage.response_tokens == 50
        assert usage.total_cost > 0


class TestGetMonthlyUsage:
    @pytest.mark.asyncio
    async def test_aggregates_current_month(self, db_session, user):
        db_session.add(user)
        await db_session.commit()

        # Create two usage records
        await track_token_usage(db_session, user.id, "claude", 100, 50, "/api/chat")
        await track_token_usage(db_session, user.id, "claude", 200, 100, "/api/chat")

        usage = await get_monthly_usage(db_session, user.id)

        assert usage["total_requests"] == 2
        assert usage["total_input_tokens"] == 300
        assert usage["total_output_tokens"] == 150
```

### Example: Testing LLM Service with MockLLMAdapter

```python
# tests/unit/services/test_ai_service.py

import pytest
import json
from app.services.ai_service import AIService


class TestAIServiceStreamChat:
    @pytest.mark.asyncio
    async def test_yields_text_events(self, db_session, mock_llm_adapter, thread):
        # Setup
        db_session.add(thread)
        await db_session.commit()

        adapter = mock_llm_adapter(responses=["Hello", " world"])
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        # Execute
        events = []
        async for event in service.stream_chat(
            messages=[{"role": "user", "content": "Hi"}],
            project_id="test",
            thread_id=thread.id,
            db=db_session
        ):
            events.append(event)

        # Assert
        text_events = [e for e in events if e["event"] == "text_delta"]
        assert len(text_events) == 2

        complete_event = [e for e in events if e["event"] == "message_complete"][0]
        data = json.loads(complete_event["data"])
        assert "Hello world" in data["content"]

    @pytest.mark.asyncio
    async def test_records_call_history(self, db_session, mock_llm_adapter, thread):
        db_session.add(thread)
        await db_session.commit()

        adapter = mock_llm_adapter(responses=["Response"])
        service = AIService.__new__(AIService)
        service.adapter = adapter
        service.tools = []

        messages = [{"role": "user", "content": "Test message"}]
        async for _ in service.stream_chat(messages, "proj", thread.id, db_session):
            pass

        # MockLLMAdapter records calls
        assert len(adapter.call_history) == 1
        assert adapter.call_history[0]["messages"] == messages
```

### Example: Testing with Mocked External API

```python
# tests/unit/services/test_summarization_service.py

import pytest
from unittest.mock import AsyncMock, Mock
from app.services.summarization_service import (
    format_messages_for_summary, generate_thread_summary
)


class TestFormatMessagesForSummary:
    def test_formats_role_uppercase(self):
        messages = [{"role": "user", "content": "Hello"}]
        result = format_messages_for_summary(messages)
        assert "USER: Hello" in result

    def test_truncates_long_messages(self):
        messages = [{"role": "user", "content": "x" * 600}]
        result = format_messages_for_summary(messages)
        assert len(result) < 600
        assert "..." in result


class TestGenerateThreadSummary:
    @pytest.mark.asyncio
    async def test_generates_title(self, mocker):
        # Mock Anthropic client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Customer Onboarding Discussion")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=10)
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "We need better onboarding"}]

        title, usage = await generate_thread_summary(mock_client, messages)

        assert title == "Customer Onboarding Discussion"
        assert usage["input_tokens"] == 100
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual object creation | Factory-boy factories | Phase 28 | Cleaner tests |
| Real LLM calls in tests | MockLLMAdapter | Phase 28 | No API costs in tests |
| Scattered fixtures | pytest_plugins | Phase 28 | Centralized discovery |

**Deprecated/outdated:**
- Direct model instantiation in tests (use factories)
- Mocking at wrong level (mock adapters, not internal methods)

---

## Open Questions

1. **agent_service SDK Mocking**
   - What we know: Uses claude_agent_sdk.query() for streaming
   - What's unclear: Best way to mock SDK streaming behavior
   - Recommendation: Mock at query() function level, return mock async generator

2. **PDF Export Testing Coverage**
   - What we know: Requires GTK3 which may not be on all CI systems
   - What's unclear: Should we skip or mock?
   - Recommendation: Use pytest.mark.skipif and test on systems with GTK

---

## Sources

### Primary (HIGH confidence)
- Phase 28 code review: `tests/fixtures/`, `tests/conftest.py`
- Service module inspection: `app/services/` (all files)
- Models inspection: `app/models.py`

### Secondary (MEDIUM confidence)
- pytest-asyncio documentation (async test patterns)
- Factory-boy documentation (fixture patterns)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Service inventory: HIGH - Direct code inspection
- Testing strategy: HIGH - Based on existing test patterns
- Fixture requirements: HIGH - Direct inspection of Phase 28 work

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (30 days - stable domain)
