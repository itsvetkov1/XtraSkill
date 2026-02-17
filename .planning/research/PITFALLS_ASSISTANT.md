# Domain Pitfalls: Assistant Integration

**Domain:** Dual-mode chat application with discriminated thread types
**Researched:** 2026-02-17

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Global System Prompt Constant

**What goes wrong:** Defining one `SYSTEM_PROMPT` constant and using it everywhere makes it impossible to support multiple conversation modes.

**Why it happens:** Copy-paste from simple examples, premature optimization ("we only have one prompt type now").

**Consequences:**
- Assistant threads receive 600-line BA prompt
- Slow responses (unnecessary token overhead)
- Confused AI behavior (BA instructions applied to general questions)
- Impossible to differentiate without refactoring service layer

**Prevention:**
```python
# BAD: Global constant
SYSTEM_PROMPT = """<BA instructions>..."""
adapter.stream_chat(messages, system_prompt=SYSTEM_PROMPT)

# GOOD: Function of thread type
def get_system_prompt(thread_type: ThreadType) -> str:
    if thread_type == ThreadType.BA_ASSISTANT:
        return BA_SYSTEM_PROMPT
    elif thread_type == ThreadType.GENERAL_ASSISTANT:
        return ASSISTANT_SYSTEM_PROMPT
    else:
        raise ValueError(f"Unknown thread type: {thread_type}")

adapter.stream_chat(messages, system_prompt=get_system_prompt(thread.thread_type))
```

**Detection:**
- Code review: Look for `system_prompt=SYSTEM_PROMPT` without conditional
- Runtime test: Create Assistant thread, check if BA instructions appear in response
- Token usage anomaly: Assistant threads consuming unexpectedly high input tokens

### Pitfall 2: Thread Type in Frontend State Only

**What goes wrong:** Storing conversation mode in Flutter provider state instead of the database.

**Why it happens:** Faster to implement, avoids database migration, "we can always add it later."

**Consequences:**
- Type information lost on page refresh
- Can't query threads by type (slow thread list loading)
- Inconsistent behavior across sessions
- Impossible to implement deep linking (URL doesn't know thread type)
- Migration path is painful (must infer types from usage patterns)

**Prevention:**
```python
# BAD: Frontend only
class ThreadProvider extends ChangeNotifier {
  ThreadMode _mode = ThreadMode.ba;  // Lost on refresh
}

# GOOD: Database field
class Thread(Base):
    thread_type: Mapped[ThreadType] = mapped_column(
        Enum(ThreadType, native_enum=False, length=20),
        nullable=False
    )
```

**Detection:**
- Database inspection: `SELECT * FROM threads` → no thread_type column
- Refresh test: Create Assistant thread, refresh page, check if type persists
- Query test: Try filtering threads by type in SQL → field doesn't exist

### Pitfall 3: Duplicating AI Service for Each Type

**What goes wrong:** Creating `BAAssistantService` and `GeneralAssistantService` classes instead of conditional logic.

**Why it happens:** Separation of concerns taken too far, "cleaner architecture."

**Consequences:**
- Code duplication (2x the stream_chat logic)
- Bug fixes must be applied twice
- Harder to add third thread type (would need third service)
- Violates DRY principle
- Testing complexity (must test both services independently)

**Prevention:**
```python
# BAD: Separate services
class BAAssistantService:
    async def stream_chat(self, ...):
        # 100 lines of streaming logic

class GeneralAssistantService:
    async def stream_chat(self, ...):
        # 100 lines of DUPLICATED streaming logic

# GOOD: Single service with conditionals
class AIService:
    async def stream_chat(self, ..., thread_type: ThreadType):
        system_prompt = self._get_system_prompt(thread_type)
        tools = self._get_tools(thread_type)
        # Single implementation of streaming logic
```

**Detection:**
- File count: Multiple *_service.py files for AI
- Git blame: Identical code blocks in multiple files
- Test coverage: Duplicate test suites for similar functionality

## Moderate Pitfalls

### Pitfall 4: Forgetting to Conditionally Load MCP Tools

**What goes wrong:** CLI adapter always loads BA MCP tools (search_documents, save_artifact), even for Assistant threads.

**Why it happens:** MCP config is complex, easier to always load everything.

**Prevention:**
```python
# backend/app/services/llm/claude_cli_adapter.py
def _get_mcp_config(self, thread_type: ThreadType) -> Dict[str, Any]:
    if thread_type == ThreadType.BA_ASSISTANT:
        return {"mcpServers": {"ba": {...}}}
    else:
        return {"mcpServers": {}}  # Empty for Assistant
```

**Detection:**
- Tool usage logs: search_documents called in Assistant thread
- Error logs: MCP tool errors in Assistant threads (project_id is null)

### Pitfall 5: Allowing Project Association for Assistant Threads

**What goes wrong:** Accepting project_id in Assistant thread creation requests.

**Why it happens:** Reusing same creation route, forgot to add validation.

**Prevention:**
```python
# backend/app/routes/threads.py
if thread_type == ThreadType.GENERAL_ASSISTANT and project_id:
    raise HTTPException(400, "Assistant threads cannot have a project")
```

**Detection:**
- Database query: `SELECT * FROM threads WHERE thread_type='assistant' AND project_id IS NOT NULL`
- Integration test: POST with type=assistant + project_id → expect 400

### Pitfall 6: Not Defaulting Existing Threads in Migration

**What goes wrong:** Migration adds thread_type column without default value.

**Why it happens:** Forgot nullable=False or server_default.

**Consequences:**
- Existing threads have null thread_type
- Application crashes on thread list (enum parse fails)
- Must manually backfill all threads

**Prevention:**
```python
# Alembic migration
op.add_column('threads', sa.Column('thread_type', sa.String(20),
    nullable=False, server_default='ba_assistant'))  # DEFAULT!
```

**Detection:**
- Migration dry run: Apply to test DB, check existing threads
- Query test: `SELECT * FROM threads WHERE thread_type IS NULL` → should be empty

## Minor Pitfalls

### Pitfall 7: Hardcoding Thread Type in Thread Creation Dialog

**What goes wrong:** Thread creation dialog hardcodes `thread_type: "ba_assistant"` instead of passing a parameter.

**Why it happens:** Copied existing dialog, didn't parameterize.

**Prevention:**
```dart
// BAD: Hardcoded
final response = await api.createThread(projectId, title, threadType: "ba_assistant");

// GOOD: Parameterized
class ThreadCreateDialog extends StatelessWidget {
  final ThreadType threadType;  // Pass from caller
  
  @override
  Widget build(BuildContext context) {
    // Use this.threadType in API call
  }
}
```

**Detection:**
- Code review: Search for "ba_assistant" strings in dialog
- UI test: Attempt to create Assistant thread → creates BA thread instead

### Pitfall 8: Inconsistent Thread Type Naming

**What goes wrong:** Backend uses `thread_type`, frontend uses `threadMode`, database uses `conversation_type`.

**Why it happens:** Different developers, no naming convention.

**Prevention:**
- Establish naming: `thread_type` everywhere
- Backend: `thread_type` (snake_case, Python convention)
- Frontend: `threadType` (camelCase, Dart convention)
- Database: `thread_type` (snake_case, SQL convention)
- JSON: `thread_type` (snake_case, API contract)

**Detection:**
- Grep search: `grep -r "thread.*type\|conversation.*mode\|chat.*type"` → should use same base term

### Pitfall 9: Missing Thread Type in Deep Link Routes

**What goes wrong:** Deep link `/chats/:id` works for BA threads but not Assistant threads, or vice versa.

**Why it happens:** Forgot to register `/assistant/:id` route variant.

**Prevention:**
```dart
// GoRouter configuration
GoRoute(
  path: '/chats/:id',
  builder: (context, state) => ConversationScreen(threadId: state.params['id']!),
),
GoRoute(
  path: '/assistant/:id',  // NEW
  builder: (context, state) => ConversationScreen(threadId: state.params['id']!),
),
```

**Detection:**
- Manual test: Navigate to `/assistant/{uuid}` → 404 or redirects incorrectly
- Integration test: Create Assistant thread, copy URL, refresh → should work

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Phase 1: Data Model** | Forgetting migration default | Review migration SQL, test on copy of production DB |
| **Phase 2: AI Service** | Global system prompt constant | Extract prompt selection to separate method |
| **Phase 3: API Routes** | Forgetting validation (project_id constraints) | Add integration tests for invalid requests |
| **Phase 4: Frontend Model** | Inconsistent naming (threadType vs thread_type) | Establish naming convention document |
| **Phase 5: Frontend UI** | Hardcoding thread type in dialog | Parameterize dialog, pass type from caller |
| **Phase 6: Testing** | Not testing isolation (BA prompt in Assistant) | Add specific test: create Assistant thread, verify response has no BA instructions |

## Testing Checklist

### Thread Type Isolation Tests

```python
# Test: BA threads use BA prompt
def test_ba_thread_uses_ba_prompt():
    thread = create_thread(type="ba_assistant", project_id="...")
    response = send_message(thread.id, "Hello")
    assert "business requirements" in response.lower()  # BA-specific language

# Test: Assistant threads use generic prompt
def test_assistant_thread_uses_generic_prompt():
    thread = create_thread(type="assistant", project_id=None)
    response = send_message(thread.id, "Hello")
    assert "business requirements" not in response.lower()  # No BA language

# Test: Tools not available in Assistant threads
def test_assistant_no_tools():
    thread = create_thread(type="assistant", project_id=None)
    response = send_message(thread.id, "Search project documents")
    assert "tool_use" not in response  # No tool calls
```

### Data Integrity Tests

```python
# Test: BA threads must have project
def test_ba_thread_requires_project():
    with pytest.raises(HTTPException) as exc:
        create_thread(type="ba_assistant", project_id=None)
    assert exc.value.status_code == 400

# Test: Assistant threads cannot have project
def test_assistant_thread_no_project():
    with pytest.raises(HTTPException) as exc:
        create_thread(type="assistant", project_id="abc-123")
    assert exc.value.status_code == 400
```

### Migration Tests

```python
# Test: Existing threads default to ba_assistant
def test_migration_defaults_to_ba():
    # Apply migration to DB with existing threads
    run_migration("add_thread_type")
    
    threads = db.query(Thread).filter(Thread.created_at < migration_timestamp).all()
    assert all(t.thread_type == ThreadType.BA_ASSISTANT for t in threads)
```

## Sources

- Codebase analysis: `backend/app/services/ai_service.py` (global SYSTEM_PROMPT constant)
- Codebase analysis: `backend/app/models.py` (existing thread fields)
- Codebase analysis: `backend/app/services/llm/claude_cli_adapter.py` (MCP tool loading)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/) - Conditional service behavior
- [SQLAlchemy Enum Types](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum) - Type safety
- [Alembic Migrations Best Practices](https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-uptodate-database-from-scratch) - Migration defaults

---
*Pitfalls research for: Assistant Integration*
*Researched: 2026-02-17*
*Critical pitfalls: 3 (all preventable with proper architecture)*
*Moderate pitfalls: 3 (caught by integration tests)*
*Minor pitfalls: 3 (caught by code review)*
