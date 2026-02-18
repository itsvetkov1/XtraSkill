# Phase 62: Backend Foundation - Research

**Researched:** 2026-02-17
**Domain:** SQLAlchemy 2.0 data models, FastAPI endpoints, conditional service logic
**Confidence:** HIGH

## Summary

Phase 62 adds `thread_type` discrimination to the existing Thread model using SQLAlchemy Enum, following the established pattern from `model_provider`. The implementation spans three layers: (1) data model migration with backward compatibility, (2) conditional AI service logic that routes Assistant threads to claude-code-cli without BA system prompt, and (3) API endpoints that accept thread_type on creation and support filtering on list.

Current codebase already has patterns we can follow: `model_provider` enum field on Thread, Alembic migrations with batch_alter_table for SQLite compatibility, and adapter routing via LLMFactory. Document scoping for Assistant threads requires making `project_id` nullable on Document model (already nullable on Thread).

**Primary recommendation:** Use SQLAlchemy Enum with `native_enum=False` for SQLite compatibility, add NOT NULL constraint with server default `'ba_assistant'` for backward compatibility, backfill existing threads in migration, and route thread_type to AIService via conditional logic (no duplicate services).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Assistant behavior:**
- No system prompt for Assistant threads — user messages go directly to the LLM with no instructions
- Hardcoded to claude-code-cli adapter — no override or provider selection possible for Assistant threads
- Full conversation history — all prior messages in the thread sent as context (same as BA threads)
- Include thinking/reasoning indicators during streaming — consistent with BA mode experience

**API defaults:**
- thread_type is **required** on thread creation — no default, all callers must be explicit
- Fix existing frontend BA thread creation to send `thread_type=ba_assistant` in this phase (prevents breakage)
- Listing threads without filter returns **all threads** regardless of type (backward compatible)
- thread_type field **always included** in all thread API responses (list, get, create)

**Document scope:**
- Documents in Assistant mode are **thread-scoped** — belong to a specific thread, only visible within that thread's conversation
- **Expanded file types** beyond BA mode: images (PNG, JPG, GIF) and spreadsheets (CSV, XLSX) in addition to existing types
- **Higher file size limit** for Assistant threads compared to BA mode (exact limit at Claude's discretion based on CLI adapter constraints)

**Error responses:**
- Invalid thread_type: HTTP 400 with message listing valid options ("Invalid thread_type. Must be 'ba_assistant' or 'assistant'")
- Assistant thread with project_id: **silently ignore** the project_id — create thread without project, no error
- Invalid thread_type enum: HTTP 400 with clear valid options
- AI generation errors: same error handling as BA mode — reuse existing patterns
- **Separate usage tracking** per thread_type for future analytics

### Claude's Discretion

- Exact file size limit for Assistant uploads (based on CLI adapter constraints)
- Migration implementation approach (Alembic vs manual SQL)
- Usage tracking implementation details (counters, storage)
- How to structure the thread_type enum in the codebase

### Deferred Ideas (OUT OF SCOPE)

- Expanded file type support for BA mode — keep BA types unchanged, only Assistant gets new types
- Per-thread adapter override for Assistant mode — currently hardcoded to CLI, future flexibility deferred (CUST-02)
- Custom system prompts for Assistant mode — deferred to CUST-01

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Thread model has thread_type field distinguishing BA Assistant vs Assistant threads | SQLAlchemy Enum pattern from `model_provider`, Alembic migration with server_default |
| DATA-02 | Existing threads default to ba_assistant type via backward-compatible migration | Alembic batch_alter_table with server_default, backfill in upgrade() function |
| DATA-03 | Documents can be associated with Assistant threads (project_id nullable for Assistant scope) | Document.project_id already nullable, add thread_id foreign key for thread-scoped docs |
| LOGIC-01 | AI service skips BA system prompt for Assistant threads | Conditional logic in ai_service.py based on thread.thread_type |
| LOGIC-02 | MCP tools (search_documents, save_artifact) conditionally loaded only for BA threads | Agent provider check in AIService.stream_chat, pass tools=None for Assistant |
| LOGIC-03 | Assistant threads always use claude-code-cli adapter regardless of settings | Override in AIService.__init__ when thread_type=assistant, force LLMFactory.create("claude-code-cli") |
| API-01 | Thread creation accepts thread_type parameter | Add thread_type to ThreadCreate/GlobalThreadCreate Pydantic models, validate against enum |
| API-02 | Thread listing supports thread_type filter query parameter | Add optional thread_type query param, filter in SQL WHERE clause |
| API-03 | Assistant threads cannot have project association (validation) | Validation in create_global_thread: if thread_type=assistant and project_id provided, set project_id=None (silent ignore per locked decision) |

</phase_requirements>

## Standard Stack

### Core Dependencies (Already Installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.x | ORM and data model | Already in use, supports async operations and modern type hints |
| Alembic | 1.x | Database migrations | Already in use for schema versioning |
| Pydantic | 2.x | Request/response validation | Already in use, validates thread_type in request models |
| FastAPI | 0.x | API endpoints | Already in use, dependency injection for db sessions |

### Supporting (No New Dependencies Needed)

All phase requirements met with existing dependencies. No new packages required.

**Version Check:**
```bash
# Current versions from backend/requirements.txt
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.0.0
fastapi>=0.104.0
```

## Architecture Patterns

### Pattern 1: SQLAlchemy Enum with SQLite Compatibility

**What:** Use Python Enum + SQLAlchemy Enum type with `native_enum=False`
**When to use:** Discriminator fields that need validation and backward compatibility

**Example from existing codebase:**
```python
# backend/app/models.py (existing pattern)
class OAuthProvider(str, PyEnum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class User(Base):
    oauth_provider: Mapped[OAuthProvider] = mapped_column(
        Enum(OAuthProvider, native_enum=False, length=20),
        nullable=False
    )
```

**For thread_type:**
```python
class ThreadType(str, PyEnum):
    """Thread type discriminator."""
    BA_ASSISTANT = "ba_assistant"
    ASSISTANT = "assistant"

class Thread(Base):
    thread_type: Mapped[ThreadType] = mapped_column(
        Enum(ThreadType, native_enum=False, length=20),
        nullable=False,
        server_default="ba_assistant"  # Backward compatibility
    )
```

**Why native_enum=False:** SQLite doesn't support native ENUM type, stores as VARCHAR with application-level validation.

### Pattern 2: Alembic Migration with Backward Compatibility

**What:** Add NOT NULL column with server_default, then backfill existing rows
**When to use:** Adding required fields to tables with existing data

**Example from existing codebase:**
```python
# backend/alembic/versions/c07d77df9b74_add_model_provider_to_threads.py
def upgrade() -> None:
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(sa.Column('model_provider', sa.String(length=20), nullable=True))
```

**For thread_type (improved with backfill):**
```python
def upgrade() -> None:
    # Step 1: Add column as nullable with default
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('thread_type', sa.String(length=20),
                     nullable=True,
                     server_default='ba_assistant')
        )

    # Step 2: Backfill existing rows (already have default from server_default)
    # Connection-level operation for safety
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE threads SET thread_type = 'ba_assistant' WHERE thread_type IS NULL")
    )

    # Step 3: Make NOT NULL after backfill
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.alter_column('thread_type', nullable=False)

def downgrade() -> None:
    with op.batch_alter_table('threads', schema=None) as batch_op:
        batch_op.drop_column('thread_type')
```

**Why batch_alter_table:** SQLite doesn't support ALTER COLUMN, batch mode recreates table.

### Pattern 3: Conditional Service Logic (No Duplication)

**What:** Single AIService with conditional routing based on thread_type
**When to use:** Discriminated behavior that shares 80% of logic

**Current architecture:**
```python
# backend/app/services/ai_service.py (existing)
class AIService:
    def __init__(self, provider: str = "anthropic"):
        self.adapter = LLMFactory.create(provider)
        self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
        self.is_agent_provider = getattr(self.adapter, 'is_agent_provider', False)
```

**For thread_type routing:**
```python
class AIService:
    def __init__(self, provider: str = "anthropic", thread_type: str = "ba_assistant"):
        # Override provider for Assistant threads
        if thread_type == "assistant":
            provider = "claude-code-cli"

        self.adapter = LLMFactory.create(provider)
        self.thread_type = thread_type

        # Conditional tool loading
        if thread_type == "ba_assistant":
            self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
        else:
            self.tools = []  # No BA tools for Assistant

        self.is_agent_provider = getattr(self.adapter, 'is_agent_provider', False)

    async def stream_chat(self, messages, project_id, thread_id, db):
        # Conditional system prompt
        if self.thread_type == "ba_assistant":
            system_prompt = SYSTEM_PROMPT
        else:
            system_prompt = ""  # No system prompt for Assistant

        # Rest of stream_chat logic unchanged...
```

**Alternative (NOT recommended):** Separate AIServiceBA and AIServiceAssistant classes would duplicate 80% of code for minimal benefit.

### Pattern 4: Pydantic Enum Validation

**What:** Use Pydantic Field with enum values for request validation
**When to use:** API request models that accept discriminator fields

**Example:**
```python
# backend/app/routes/threads.py
from pydantic import BaseModel, Field, validator

VALID_THREAD_TYPES = ["ba_assistant", "assistant"]

class GlobalThreadCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    project_id: Optional[str] = None
    model_provider: Optional[str] = Field(None, max_length=20)
    conversation_mode: Optional[str] = Field(None, max_length=50)
    thread_type: str = Field(..., description="Thread type: ba_assistant or assistant")

    @validator('thread_type')
    def validate_thread_type(cls, v):
        if v not in VALID_THREAD_TYPES:
            raise ValueError(f"Invalid thread_type. Must be one of: {', '.join(VALID_THREAD_TYPES)}")
        return v
```

### Pattern 5: Document Scoping (Thread-Scoped vs Project-Scoped)

**What:** Documents can belong to either a project (BA mode) or a thread (Assistant mode)
**When to use:** Multi-context document storage

**Current model:**
```python
# backend/app/models.py (existing)
class Document(Base):
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,  # Currently required
        index=True
    )
```

**Updated model (thread-scoped support):**
```python
class Document(Base):
    # Project-scoped (BA mode) — nullable for Assistant threads
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,  # Now optional
        index=True
    )

    # Thread-scoped (Assistant mode) — nullable for BA threads
    thread_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=True,  # Optional
        index=True
    )

    # Constraint: exactly one of project_id or thread_id must be set
    # (enforced at application level, not DB constraint)
```

**Migration approach:**
```python
def upgrade() -> None:
    # Step 1: Make project_id nullable
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.alter_column('project_id', nullable=True)

    # Step 2: Add thread_id column
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('thread_id', sa.String(36),
                     sa.ForeignKey('threads.id', ondelete='CASCADE'),
                     nullable=True)
        )
        batch_op.create_index('ix_documents_thread_id', ['thread_id'])
```

**Validation in document upload:**
```python
# Pseudo-code for document upload endpoint
if thread_type == "ba_assistant":
    # Require project_id
    if not project_id:
        raise HTTPException(400, "BA threads require project_id")
    doc.project_id = project_id
    doc.thread_id = None
else:
    # Require thread_id
    if not thread_id:
        raise HTTPException(400, "Assistant threads require thread_id")
    doc.project_id = None
    doc.thread_id = thread_id
```

### Anti-Patterns to Avoid

- **Creating AIServiceAssistant as separate class:** Duplicates 80% of code, creates maintenance burden
- **Using nullable thread_type with NULL for existing threads:** Breaks NOT NULL safety, requires null checks everywhere
- **Hard-coded "ba_assistant" checks scattered everywhere:** Use constants or enum values from ThreadType
- **Skipping backfill in migration:** Leaves existing threads with NULL thread_type, breaks NOT NULL constraint
- **Using native_enum=True:** Breaks SQLite compatibility (PostgreSQL-only feature)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Enum validation in API | Manual string checks | Pydantic validators | Type safety, automatic error messages |
| Database migrations | Manual SQL scripts | Alembic batch_alter_table | SQLite compatibility, rollback support |
| Conditional adapter routing | if/elif chains | LLMFactory.create() | Centralized provider logic, extensible |
| Thread-scoped document search | Custom SQL joins | Extend existing search_documents() | Reuse FTS5 index, consistent API |

**Key insight:** Codebase already has robust patterns for enums (OAuthProvider), migrations (conversation_mode), and adapter routing (model_provider). Thread_type follows these patterns exactly — no custom solutions needed.

## Common Pitfalls

### Pitfall 1: Native Enum Breaking SQLite

**What goes wrong:** Using `Enum(ThreadType, native_enum=True)` creates PostgreSQL ENUM type, fails on SQLite
**Why it happens:** SQLAlchemy defaults to database-native enums when available
**How to avoid:** Always use `native_enum=False` in this codebase (SQLite-first design)
**Warning signs:** Migration fails with "no such type" error on SQLite

**Example:**
```python
# BAD (breaks SQLite)
thread_type: Mapped[ThreadType] = mapped_column(
    Enum(ThreadType),  # Defaults to native_enum=True
    nullable=False
)

# GOOD (SQLite compatible)
thread_type: Mapped[ThreadType] = mapped_column(
    Enum(ThreadType, native_enum=False, length=20),
    nullable=False
)
```

### Pitfall 2: Skipping Backfill in Migration

**What goes wrong:** Adding NOT NULL column without backfilling leaves existing threads NULL, violates constraint
**Why it happens:** Developer forgets existing data when adding required field
**How to avoid:** Always add as nullable first, backfill, then make NOT NULL
**Warning signs:** Migration fails with "NOT NULL constraint failed" on existing databases

**Example:**
```python
# BAD (fails on existing data)
def upgrade():
    with op.batch_alter_table('threads') as batch_op:
        batch_op.add_column(
            sa.Column('thread_type', sa.String(20), nullable=False, server_default='ba_assistant')
        )
    # Existing threads have NULL, constraint fails

# GOOD (safe for existing data)
def upgrade():
    # Add as nullable with default
    with op.batch_alter_table('threads') as batch_op:
        batch_op.add_column(
            sa.Column('thread_type', sa.String(20), nullable=True, server_default='ba_assistant')
        )

    # Backfill (server_default handles this, but explicit is safer)
    op.get_bind().execute(
        sa.text("UPDATE threads SET thread_type = 'ba_assistant' WHERE thread_type IS NULL")
    )

    # Make NOT NULL after backfill
    with op.batch_alter_table('threads') as batch_op:
        batch_op.alter_column('thread_type', nullable=False)
```

### Pitfall 3: Forgetting to Update Frontend Thread Creation

**What goes wrong:** Frontend thread creation doesn't send thread_type, API returns 400 "field required"
**Why it happens:** Adding required field breaks existing API contract
**How to avoid:** Update frontend ThreadService.createThread() in same phase to send thread_type=ba_assistant
**Warning signs:** All thread creation calls fail with validation error

**Example:**
```dart
// BAD (missing thread_type)
Future<Thread> createThread(String projectId, String? title, {String? provider}) async {
  final response = await _dio.post(
    '/api/projects/$projectId/threads',
    data: {
      if (title != null) 'title': title,
      if (provider != null) 'model_provider': provider,
      // Missing thread_type!
    },
  );
}

// GOOD (includes thread_type)
Future<Thread> createThread(String projectId, String? title, {String? provider}) async {
  final response = await _dio.post(
    '/api/projects/$projectId/threads',
    data: {
      if (title != null) 'title': title,
      if (provider != null) 'model_provider': provider,
      'thread_type': 'ba_assistant',  // Required for BA threads
    },
  );
}
```

### Pitfall 4: Hardcoding Provider Override in Wrong Layer

**What goes wrong:** Overriding provider in API routes instead of AIService creates scattered logic
**Why it happens:** Seems easier to check thread_type in create_thread endpoint
**How to avoid:** Keep provider routing in AIService constructor, pass thread_type from routes
**Warning signs:** Multiple places checking if thread_type == "assistant" to set provider

**Example:**
```python
# BAD (scattered logic)
# In routes/threads.py
@router.post("/threads/{thread_id}/chat")
async def chat(thread_id: str, message: str, db: AsyncSession):
    thread = await get_thread(thread_id, db)
    if thread.thread_type == "assistant":
        provider = "claude-code-cli"
    else:
        provider = thread.model_provider
    ai_service = AIService(provider=provider)
    # Loses thread_type context, can't skip system prompt

# GOOD (centralized logic)
# In services/ai_service.py
class AIService:
    def __init__(self, provider: str, thread_type: str):
        if thread_type == "assistant":
            provider = "claude-code-cli"  # Override
        self.provider = provider
        self.thread_type = thread_type
        self.adapter = LLMFactory.create(provider)

# In routes/threads.py
@router.post("/threads/{thread_id}/chat")
async def chat(thread_id: str, message: str, db: AsyncSession):
    thread = await get_thread(thread_id, db)
    ai_service = AIService(
        provider=thread.model_provider,
        thread_type=thread.thread_type  # Service handles override
    )
```

### Pitfall 5: Forgetting Thread Type in Response Models

**What goes wrong:** ThreadResponse doesn't include thread_type, frontend can't discriminate
**Why it happens:** Developer adds field to database but forgets response model
**How to avoid:** Add thread_type to all ThreadResponse variants (ThreadResponse, ThreadListResponse, ThreadDetailResponse)
**Warning signs:** Frontend has thread data but no thread_type property

**Example:**
```python
# BAD (missing thread_type)
class ThreadResponse(BaseModel):
    id: str
    project_id: Optional[str]
    title: Optional[str]
    model_provider: Optional[str]
    created_at: str
    updated_at: str
    # Missing thread_type!

# GOOD (includes thread_type)
class ThreadResponse(BaseModel):
    id: str
    project_id: Optional[str]
    title: Optional[str]
    model_provider: Optional[str]
    thread_type: str  # Always include per locked decision
    created_at: str
    updated_at: str
```

## Code Examples

### Example 1: Thread Model with ThreadType Enum

```python
# backend/app/models.py
from enum import Enum as PyEnum

class ThreadType(str, PyEnum):
    """Thread type discriminator for BA vs Assistant modes."""
    BA_ASSISTANT = "ba_assistant"
    ASSISTANT = "assistant"

class Thread(Base):
    __tablename__ = "threads"

    # ... existing fields ...

    # Thread type discriminator
    thread_type: Mapped[ThreadType] = mapped_column(
        Enum(ThreadType, native_enum=False, length=20),
        nullable=False,
        server_default="ba_assistant"
    )
```

### Example 2: Thread Creation with Validation

```python
# backend/app/routes/threads.py
VALID_THREAD_TYPES = ["ba_assistant", "assistant"]

class GlobalThreadCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    project_id: Optional[str] = None
    model_provider: Optional[str] = Field(None, max_length=20)
    conversation_mode: Optional[str] = Field(None, max_length=50)
    thread_type: str = Field(..., description="Required: ba_assistant or assistant")

@router.post("/threads", response_model=ThreadResponse, status_code=201)
async def create_global_thread(
    thread_data: GlobalThreadCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate thread_type
    if thread_data.thread_type not in VALID_THREAD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid thread_type. Must be one of: {', '.join(VALID_THREAD_TYPES)}"
        )

    # API-03: Assistant threads cannot have project (silent ignore per locked decision)
    if thread_data.thread_type == "assistant" and thread_data.project_id:
        thread_data.project_id = None

    # Validate project if provided (BA threads only)
    if thread_data.project_id:
        # ... existing project validation ...

    # Create thread
    thread = Thread(
        project_id=thread_data.project_id,
        user_id=user_id if thread_data.project_id is None else None,
        title=thread_data.title or "New Chat",
        model_provider=thread_data.model_provider or "anthropic",
        conversation_mode=thread_data.conversation_mode,
        thread_type=thread_data.thread_type,  # New field
        last_activity_at=datetime.utcnow()
    )

    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return ThreadResponse(
        id=thread.id,
        project_id=thread.project_id,
        title=thread.title,
        model_provider=thread.model_provider,
        thread_type=thread.thread_type,  # Always include
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
    )
```

### Example 3: Thread Listing with Optional Filter

```python
# backend/app/routes/threads.py
@router.get("/threads", response_model=PaginatedThreadsResponse)
async def list_all_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    thread_type: Optional[str] = Query(None, description="Filter by thread_type"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all threads for current user across all projects.

    Optional thread_type filter. If omitted, returns all threads (backward compatible).
    """
    user_id = current_user["user_id"]

    # Validate thread_type filter if provided
    if thread_type and thread_type not in VALID_THREAD_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid thread_type. Must be one of: {', '.join(VALID_THREAD_TYPES)}"
        )

    # Build query with optional thread_type filter
    base_query = (
        select(Thread)
        .outerjoin(Project, Thread.project_id == Project.id)
        .where(
            (Thread.user_id == user_id) |
            (Project.user_id == user_id)
        )
    )

    # Add thread_type filter if provided (API-02)
    if thread_type:
        base_query = base_query.where(Thread.thread_type == thread_type)

    base_query = base_query.options(
        selectinload(Thread.project),
        selectinload(Thread.messages)
    ).order_by(Thread.last_activity_at.desc())

    # ... pagination logic ...
```

### Example 4: AIService with Conditional Logic

```python
# backend/app/services/ai_service.py
class AIService:
    def __init__(self, provider: str = "anthropic", thread_type: str = "ba_assistant"):
        # LOGIC-03: Override provider for Assistant threads
        if thread_type == "assistant":
            provider = "claude-code-cli"

        self.adapter = LLMFactory.create(provider)
        self.thread_type = thread_type

        # LOGIC-02: Conditional tool loading
        if thread_type == "ba_assistant":
            self.tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
        else:
            self.tools = []  # No BA tools for Assistant

        self.is_agent_provider = getattr(self.adapter, 'is_agent_provider', False)

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        project_id: str,
        thread_id: str,
        db
    ) -> AsyncGenerator[Dict[str, Any], None]:
        # LOGIC-01: Conditional system prompt
        if self.thread_type == "ba_assistant":
            system_prompt = SYSTEM_PROMPT  # Full BA system prompt
        else:
            system_prompt = ""  # No system prompt for Assistant

        # Route to appropriate path (agent vs direct API)
        if self.is_agent_provider:
            async for event in self._stream_agent_chat(messages, project_id, thread_id, db):
                yield event
            return

        # Direct API provider path with conditional tools
        async for chunk in self.adapter.stream_chat(
            messages=messages,
            system_prompt=system_prompt,
            tools=self.tools,  # Empty for Assistant, full for BA
            max_tokens=4096
        ):
            # ... existing streaming logic ...
```

### Example 5: Chat Endpoint Passing Thread Type

```python
# backend/app/routes/chat.py (or wherever chat endpoint lives)
@router.post("/threads/{thread_id}/chat")
async def chat(
    thread_id: str,
    message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get thread with type
    thread = await get_thread_with_ownership_check(thread_id, current_user["user_id"], db)

    # Create AI service with thread type
    ai_service = AIService(
        provider=thread.model_provider,
        thread_type=thread.thread_type  # Pass type for conditional logic
    )

    # Stream response
    return EventSourceResponse(
        ai_service.stream_chat(
            messages=conversation_history,
            project_id=thread.project_id,
            thread_id=thread_id,
            db=db
        )
    )
```

### Example 6: Frontend Thread Creation (Minimal Fix)

```dart
// frontend/lib/services/thread_service.dart
Future<Thread> createThread(
  String projectId,
  String? title,
  {String? provider}
) async {
  final headers = await _getAuthHeaders();
  final response = await _dio.post(
    '/api/projects/$projectId/threads',
    options: Options(headers: headers),
    data: {
      if (title != null && title.isNotEmpty) 'title': title,
      if (provider != null) 'model_provider': provider,
      'thread_type': 'ba_assistant',  // NEW: Required field
    },
  );

  return Thread.fromJson(response.data as Map<String, dynamic>);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global AI mode setting | Thread-level thread_type | Phase 62 (Feb 2026) | Each thread remembers its type, no mode switching mid-conversation |
| Single provider per user | Thread-level model_provider | Phase 21 (Jan 2026) | Already established pattern for thread_type to follow |
| Project-scoped documents only | Project OR thread-scoped | Phase 62 (Feb 2026) | Assistant threads can have thread-specific documents |
| Hard-coded Anthropic | LLM adapter pattern | Phase 21 (Jan 2026) | Factory already supports claude-code-cli for routing |

**Deprecated/outdated:**
- ~~Global conversation mode setting~~ → Replaced by Thread.conversation_mode (Phase 6, Feb 2026)
- ~~Single provider app-wide~~ → Replaced by Thread.model_provider (Phase 21, Jan 2026)

## File Size Limits for Assistant Mode

**Context:** User locked decision: "Higher file size limit for Assistant threads compared to BA mode (exact limit at Claude's discretion based on CLI adapter constraints)"

**Current BA mode limits (from backend/app/services/file_validator.py assumptions):**
- Max file size: 10MB (10,485,760 bytes)
- Content types: .txt, .md, .xlsx, .csv, .pdf, .docx

**Claude Code CLI adapter constraints research:**

Based on Claude Code CLI documentation and Anthropic API limits:
- Vision API (images): 5MB per image (PNG, JPEG, GIF, WebP)
- PDF: 32MB maximum, 100 pages recommended
- Text context window: ~200K tokens (Claude Sonnet 4.5)

**Recommended Assistant mode limits:**
- Images (PNG, JPG, GIF): **5MB** per file (Anthropic Vision API limit)
- PDFs: **32MB** per file (Anthropic PDF limit)
- Spreadsheets (CSV, XLSX): **10MB** per file (same as BA mode, text-based)
- Text files (.txt, .md): **10MB** per file (same as BA mode)

**Implementation approach:**
```python
# backend/app/services/file_validator.py
def get_max_file_size(content_type: str, thread_type: str) -> int:
    """Get max file size based on content type and thread type."""
    if thread_type == "assistant":
        # Assistant mode expanded limits
        if content_type in ["image/png", "image/jpeg", "image/gif"]:
            return 5 * 1024 * 1024  # 5MB (Vision API limit)
        elif content_type == "application/pdf":
            return 32 * 1024 * 1024  # 32MB (PDF API limit)

    # BA mode and Assistant non-image files: 10MB
    return 10 * 1024 * 1024
```

**Confidence:** MEDIUM — based on Anthropic API documentation, not empirically tested with CLI adapter.

## Open Questions

1. **Document search for thread-scoped documents**
   - What we know: search_documents() currently filters by project_id
   - What's unclear: How to extend FTS5 index to support thread_id filtering
   - Recommendation: Add thread_id to document_search_index virtual table, update search_documents() to accept optional thread_id parameter

2. **Usage tracking separation**
   - What we know: User wants separate tracking per thread_type for analytics
   - What's unclear: Where to store aggregate counts (new table? extend token_usage?)
   - Recommendation: Add thread_type column to existing TokenUsage model, aggregate in queries rather than separate table

3. **Document deletion cascade for thread-scoped docs**
   - What we know: Document.thread_id will have ON DELETE CASCADE
   - What's unclear: Should deleting a thread warn user about documents?
   - Recommendation: No warning needed — thread-scoped docs are ephemeral context, not artifacts

## Sources

### Primary (HIGH confidence)

- **Existing codebase:**
  - `/Users/a1testingmac/projects/XtraSkill/backend/app/models.py` - Thread, Document, OAuthProvider enum pattern
  - `/Users/a1testingmac/projects/XtraSkill/backend/app/services/ai_service.py` - AIService architecture, adapter routing
  - `/Users/a1testingmac/projects/XtraSkill/backend/app/routes/threads.py` - Thread CRUD, validation patterns
  - `/Users/a1testingmac/projects/XtraSkill/backend/alembic/versions/` - Migration patterns (model_provider, conversation_mode)
  - `/Users/a1testingmac/projects/XtraSkill/backend/app/services/llm/factory.py` - LLMFactory.create() pattern
  - `/Users/a1testingmac/projects/XtraSkill/backend/app/services/llm/claude_cli_adapter.py` - CLI adapter implementation

- **Phase context:**
  - `.planning/phases/62-backend-foundation/62-CONTEXT.md` - User decisions and constraints
  - `.planning/REQUIREMENTS.md` - v3.0 requirements (DATA-01 through API-03)

### Secondary (MEDIUM confidence)

- **Anthropic API documentation:**
  - Vision API: 5MB image limit (PNG, JPEG, GIF, WebP)
  - PDF API: 32MB limit, 100 pages recommended
  - Context window: ~200K tokens for Claude Sonnet 4.5

### Tertiary (LOW confidence)

- None — all findings based on existing codebase patterns or official API docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All dependencies already installed, verified in requirements.txt
- Architecture patterns: HIGH - Existing codebase has exact patterns needed (enum fields, migrations, conditional service logic)
- Pitfalls: HIGH - Derived from actual code structure and SQLite constraints
- File size limits: MEDIUM - Based on Anthropic docs, not empirically tested with CLI adapter

**Research date:** 2026-02-17
**Valid until:** 30 days (stable stack, no fast-moving dependencies)
