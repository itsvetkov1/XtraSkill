# Architecture Research: Assistant Integration

**Domain:** Chat application with dual modes (BA-specific vs generic Assistant)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Current Architecture Overview

The existing BA Assistant uses a clean layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Flutter)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Projects │  │ Threads │  │Settings │  │  Chats  │        │
│  │ Screen  │  │ Screen  │  │ Screen  │  │ Screen  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
│       └────────────┴────────────┴────────────┘              │
│                    │                                         │
│            ┌───────┴──────┐                                 │
│            │  API Client   │                                 │
│            └───────┬───────┘                                 │
├────────────────────┼─────────────────────────────────────────┤
│                    │        BACKEND (FastAPI)                │
├────────────────────┼─────────────────────────────────────────┤
│            ┌───────┴───────┐                                 │
│            │    Routes     │ (threads, conversations, etc)   │
│            └───────┬───────┘                                 │
│                    │                                         │
│         ┌──────────┼──────────┐                              │
│         │          │          │                              │
│    ┌────▼────┐ ┌──▼──────┐ ┌▼─────────┐                     │
│    │  AI     │ │  Conv   │ │Document  │                     │
│    │ Service │ │ Service │ │  Search  │                     │
│    └────┬────┘ └─────────┘ └──────────┘                     │
│         │                                                    │
│    ┌────▼───────────────────────────────┐                   │
│    │  LLM Adapter Factory               │                   │
│    ├────────────────────────────────────┤                   │
│    │ Anthropic │ Gemini │ DeepSeek │ CLI│                   │
│    └────┬───────────────────────────────┘                   │
│         │                                                    │
├─────────┼───────────────────────────────────────────────────┤
│         │              DATA LAYER                            │
├─────────┼───────────────────────────────────────────────────┤
│  ┌──────▼─────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Threads   │  │ Messages │  │Artifacts │                 │
│  └────────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Problem: BA System Prompt is Always Applied

**Current flow:**
```
User message
    ↓
POST /api/threads/{thread_id}/chat
    ↓
ai_service.stream_chat()
    ↓
adapter.stream_chat(messages, system_prompt=SYSTEM_PROMPT, ...)
    ↓
BA-specific prompt ALWAYS prepended
```

**Issue:**
- `SYSTEM_PROMPT` constant in `ai_service.py` contains ~600 lines of BA-specific instructions
- Applied to EVERY conversation regardless of intent
- No mechanism to skip BA context for non-BA chats
- MCP tools (`search_documents`, `save_artifact`) are BA-oriented

## Recommended Architecture: Thread Type Discrimination

### Pattern: Thread Type Field

**Approach:** Add a `thread_type` field to the Thread model to discriminate between BA and Assistant modes.

**Why this pattern:**
- Clean data model - thread type is intrinsic to the conversation
- Simple conditional logic in AI service
- No code duplication - same service, different paths
- Matches existing `model_provider` pattern already in Thread model
- Aligns with MEDIUM confidence finding: "Shared Database, Shared Schema" multi-tenancy pattern

**Implementation:**

#### 1. Database Schema Change

```python
# backend/app/models.py
class ThreadType(str, PyEnum):
    """Types of conversation threads."""
    BA_ASSISTANT = "ba_assistant"      # BA discovery mode
    GENERAL_ASSISTANT = "assistant"     # Generic Claude Code chat

class Thread(Base):
    # ... existing fields ...

    thread_type: Mapped[ThreadType] = mapped_column(
        Enum(ThreadType, native_enum=False, length=20),
        nullable=False,
        default=ThreadType.BA_ASSISTANT  # Backward compatibility
    )
```

**Migration:**
- Default existing threads to `ba_assistant`
- New threads specify type at creation

#### 2. AI Service Conditional Logic

```python
# backend/app/services/ai_service.py

async def stream_chat(
    self,
    messages: List[Dict[str, Any]],
    project_id: str,
    thread_id: str,
    thread_type: ThreadType,  # NEW PARAM
    db
) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream chat with thread-type-specific behavior."""

    # Determine system prompt and tools based on thread type
    if thread_type == ThreadType.BA_ASSISTANT:
        system_prompt = BA_SYSTEM_PROMPT
        tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
    else:  # GENERAL_ASSISTANT
        system_prompt = ASSISTANT_SYSTEM_PROMPT  # Minimal or none
        tools = None  # No BA tools

    # Route to appropriate streaming path
    if getattr(self, 'is_agent_provider', False):
        async for event in self._stream_agent_chat(
            messages, project_id, thread_id, db,
            system_prompt, tools
        ):
            yield event
    else:
        # Direct API path...
```

**System Prompt Strategy:**
```python
# BA mode: Full 600-line BA skill prompt
BA_SYSTEM_PROMPT = """<system_prompt>...</system_prompt>"""

# Assistant mode: Generic or minimal prompt
ASSISTANT_SYSTEM_PROMPT = """You are Claude Code, a helpful AI assistant.
Provide clear, concise answers to user questions."""
```

#### 3. MCP Tools Separation

**Current issue:** CLI adapter injects BA tools via MCP configuration.

**Solution:** Conditional MCP tool loading:

```python
# backend/app/services/llm/claude_cli_adapter.py

def _get_mcp_config(self, thread_type: ThreadType) -> Dict[str, Any]:
    """Generate MCP config based on thread type."""

    if thread_type == ThreadType.BA_ASSISTANT:
        return {
            "mcpServers": {
                "ba": {
                    "command": "python",
                    "args": ["-m", "app.services.mcp_tools"],
                    "env": {...}
                }
            }
        }
    else:
        # No MCP tools for Assistant mode
        return {"mcpServers": {}}
```

#### 4. Document Access Control

**Decision:** Should Assistant threads access project documents?

**Options:**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Option A: Assistant threads are project-less** | Clean separation, no document access issues | Less useful for project-specific questions | ✅ **RECOMMENDED** |
| **Option B: Assistant threads can join projects** | More flexible, can help with project work | Needs document search without BA context | Defer to Phase 2 |

**Selected: Option A**
- Assistant threads: `project_id = NULL`, `user_id = current_user`
- BA threads: `project_id = <uuid>`, `user_id = NULL` (owned via project)
- Document search tool only available in BA threads (has project context)

### Component Responsibilities (Updated)

| Component | Responsibility | Thread Type Awareness |
|-----------|----------------|----------------------|
| **Thread Model** | Stores `thread_type` field | Intrinsic property |
| **Thread Routes** | Accept `thread_type` in creation requests | Validates type |
| **AI Service** | Routes to BA or Assistant flow based on type | Core discriminator |
| **LLM Adapters** | Execute with provided system prompt + tools | Agnostic to type |
| **Conversation Routes** | Pass `thread_type` from thread to AI service | Pass-through |
| **Frontend UI** | Different creation flows for BA vs Assistant | Type selection |

## Data Flow: Thread Creation

### BA Thread (Existing Flow)

```
User → "New Chat" in Project → ThreadCreateDialog
    ↓
POST /api/projects/{id}/threads
    {
        title: "Discovery Session",
        model_provider: "claude-code-cli",
        thread_type: "ba_assistant"  // NEW
    }
    ↓
Thread created with project_id, type=ba_assistant
    ↓
POST /api/threads/{id}/chat
    ↓
ai_service.stream_chat(..., thread_type=ba_assistant)
    ↓
BA_SYSTEM_PROMPT + BA tools → LLM
```

### Assistant Thread (New Flow)

```
User → "New Assistant Chat" (new nav item)
    ↓
POST /api/threads
    {
        title: "General Chat",
        project_id: null,           // Project-less
        model_provider: "claude-code-cli",
        thread_type: "assistant"    // NEW
    }
    ↓
Thread created with user_id, type=assistant
    ↓
POST /api/threads/{id}/chat
    ↓
ai_service.stream_chat(..., thread_type=assistant)
    ↓
ASSISTANT_SYSTEM_PROMPT (minimal) + no tools → LLM
```

## Data Flow: Message Streaming

### Current BA Flow (Unchanged)

```
[User Message]
    ↓
save_message(db, thread_id, "user", content)
    ↓
build_conversation_context(db, thread_id)
    ↓
AIService.stream_chat(messages, ..., thread_type=ba_assistant)
    ↓
    ┌─ Agent provider (CLI/SDK)?
    │   ↓ YES
    │   ├─ _stream_agent_chat()
    │   │   ↓
    │   │   adapter.set_context(db, project_id, thread_id)
    │   │   ↓
    │   │   adapter.stream_chat(messages, BA_SYSTEM_PROMPT, max_tokens)
    │   │       ↓ (MCP tools injected via CLI)
    │   │       search_documents (via MCP) → SQLite FTS5
    │   │       save_artifact (via MCP) → artifacts table
    │   │   ↓
    │   └─ StreamChunk events → SSE
    │
    └─ NO (Direct API)
        ↓
        adapter.stream_chat(messages, BA_SYSTEM_PROMPT, tools=[...])
            ↓
            execute_tool("search_documents", ...) → Python function
            execute_tool("save_artifact", ...) → Python function
        ↓
        StreamChunk events → SSE
```

### New Assistant Flow

```
[User Message]
    ↓
save_message(db, thread_id, "user", content)
    ↓
build_conversation_context(db, thread_id)
    ↓
AIService.stream_chat(messages, ..., thread_type=assistant)
    ↓
    ┌─ Agent provider (CLI/SDK)?
    │   ↓ YES
    │   ├─ _stream_agent_chat()
    │   │   ↓
    │   │   adapter.set_context(db, NULL, thread_id)  # No project_id
    │   │   ↓
    │   │   adapter.stream_chat(messages, ASSISTANT_SYSTEM_PROMPT, max_tokens)
    │   │       ↓ (NO MCP tools - empty config)
    │   │       Pure Claude Code conversation
    │   │   ↓
    │   └─ StreamChunk events → SSE
    │
    └─ NO (Direct API)
        ↓
        adapter.stream_chat(messages, ASSISTANT_SYSTEM_PROMPT, tools=None)
            ↓
            No tool calls
        ↓
        StreamChunk events → SSE
```

## Architectural Patterns

### Pattern 1: Discriminated Thread Types

**What:** Single Thread model with a `thread_type` enum field that determines behavior at the service layer.

**When to use:** When you have multiple conversation modes sharing the same data structure and most of the same logic, differing only in AI prompts and tools.

**Trade-offs:**
- ✅ **Pros:** No code duplication, simple to extend with new types, clean data model
- ❌ **Cons:** Service layer must be aware of all types, conditional logic in stream_chat

**Example:**
```python
# Clean separation at service layer
if thread_type == ThreadType.BA_ASSISTANT:
    return await self._stream_ba_chat(...)
elif thread_type == ThreadType.GENERAL_ASSISTANT:
    return await self._stream_assistant_chat(...)
```

### Pattern 2: Project Association as Context Boundary

**What:** Use `project_id` presence to determine document access permissions. BA threads always have projects, Assistant threads are always project-less.

**When to use:** When document context is tightly coupled to a specific use case (BA discovery requires documents, general chat does not).

**Trade-offs:**
- ✅ **Pros:** Natural security boundary, simple access control, aligns with existing ownership model
- ❌ **Cons:** Assistant can't help with project-specific tasks (acceptable trade-off for MVP)

**Example:**
```python
# In conversation service
if thread.project_id:
    # BA thread - documents available
    tools = [DOCUMENT_SEARCH_TOOL, SAVE_ARTIFACT_TOOL]
else:
    # Assistant thread - no document access
    tools = None
```

### Pattern 3: System Prompt Injection Point

**What:** System prompt selection happens at the AI service layer, not the adapter layer.

**When to use:** When different conversation types need different prompts but use the same underlying LLM infrastructure.

**Trade-offs:**
- ✅ **Pros:** Adapters remain pure LLM clients, service layer owns business logic
- ❌ **Cons:** Service layer grows in responsibility

**Example:**
```python
# AI Service decides prompt
system_prompt = self._get_system_prompt(thread_type)

# Adapter just executes
async for chunk in self.adapter.stream_chat(
    messages=messages,
    system_prompt=system_prompt,
    ...
):
    yield chunk
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-100 threads** | Current architecture is perfect - single Thread table with type field |
| **100-10k threads** | Add index on `thread_type` for filtering queries. Consider separate tables for BA-specific metadata (conversation_mode, etc) |
| **10k+ threads** | If BA and Assistant have very different access patterns, consider table partitioning by thread_type |

### Scaling Priorities

1. **First bottleneck:** Thread list queries will slow down
   - **Fix:** Add composite index on `(user_id, thread_type, last_activity_at)`
   - **Reasoning:** Most queries filter by user + type, sort by activity

2. **Second bottleneck:** Message history retrieval for long threads
   - **Fix:** Implement message pagination (already handled by conversation_service truncation)
   - **Reasoning:** Claude has 200k token context but doesn't mean we should load it all

## Anti-Patterns

### Anti-Pattern 1: Global System Prompt Constant

**What people do:** Define one `SYSTEM_PROMPT` constant and use it everywhere.

**Why it's wrong:** Impossible to support multiple conversation modes without complex string manipulation or global state.

**Do this instead:** Make system prompt selection a function of thread type:
```python
def get_system_prompt(thread_type: ThreadType) -> str:
    if thread_type == ThreadType.BA_ASSISTANT:
        return BA_SYSTEM_PROMPT
    elif thread_type == ThreadType.GENERAL_ASSISTANT:
        return ASSISTANT_SYSTEM_PROMPT
    else:
        raise ValueError(f"Unknown thread type: {thread_type}")
```

### Anti-Pattern 2: Thread Type in Frontend State Only

**What people do:** Store conversation mode in Flutter provider state, not the database.

**Why it's wrong:** Type information is lost on page refresh, can't query threads by type, inconsistent behavior.

**Do this instead:** Make `thread_type` a database field set at creation time and immutable (threads don't change modes).

### Anti-Pattern 3: Duplicating AI Service for Each Type

**What people do:** Create `BAAssistantService` and `GeneralAssistantService` classes.

**Why it's wrong:** Code duplication, harder to maintain, violates DRY principle.

**Do this instead:** Single `AIService` with conditional logic based on thread type parameter.

## Integration Points

### Modified Components

| Component | File Path | Change Required | Risk |
|-----------|-----------|-----------------|------|
| **Thread Model** | `backend/app/models.py` | Add `thread_type` field | LOW - simple enum field |
| **Thread Routes** | `backend/app/routes/threads.py` | Accept `thread_type` in create requests | LOW - additive change |
| **AI Service** | `backend/app/services/ai_service.py` | Conditional prompt/tool selection | MEDIUM - core logic change |
| **Conversation Routes** | `backend/app/routes/conversations.py` | Pass thread type to AI service | LOW - parameter pass-through |
| **CLI Adapter** | `backend/app/services/llm/claude_cli_adapter.py` | Conditional MCP config | MEDIUM - subprocess behavior |
| **Thread Model (Flutter)** | `frontend/lib/models/thread.dart` | Add `threadType` field | LOW - data class change |
| **Thread Create Dialog** | `frontend/lib/screens/threads/thread_create_dialog.dart` | Add type selector | LOW - UI enhancement |

### New Components

| Component | File Path | Purpose | Complexity |
|-----------|-----------|---------|------------|
| **Assistant Screen** | `frontend/lib/screens/assistant_screen.dart` | List Assistant threads | LOW - clone ChatsScreen |
| **Assistant Nav Item** | `frontend/lib/widgets/responsive_scaffold.dart` | Navigation entry | LOW - add to nav items |
| **Assistant Thread List API** | `backend/app/routes/threads.py` | Filter by thread_type=assistant | LOW - query filter |

### Internal Boundaries

| Boundary | Communication | Change Required |
|----------|---------------|-----------------|
| **Frontend ↔ Backend** | REST API (thread creation) | Add `thread_type` field to request/response |
| **Conversation Route ↔ AI Service** | Function call | Add `thread_type` parameter |
| **AI Service ↔ LLM Adapter** | Function call | Pass different `system_prompt` and `tools` |
| **CLI Adapter ↔ Claude CLI** | Subprocess with MCP config | Conditional MCP server injection |

## Build Order Recommendations

### Phase 1: Backend Foundation (Low Risk)
1. Add `thread_type` field to Thread model
2. Create Alembic migration, default existing threads to `ba_assistant`
3. Update thread creation routes to accept `thread_type`
4. Add system prompt selection logic in AI service

### Phase 2: Backend Integration (Medium Risk)
5. Modify `stream_chat()` to accept `thread_type` parameter
6. Update CLI adapter to conditionally load MCP tools
7. Update conversation routes to pass thread type through

### Phase 3: Frontend Updates (Low Risk)
8. Add `threadType` to Flutter Thread model
9. Update thread creation dialog with type selector
10. Create Assistant screen (clone ChatsScreen)
11. Add Assistant nav item

### Phase 4: Testing & Validation (Critical)
12. Test BA thread creation and conversation (regression)
13. Test Assistant thread creation and conversation (new)
14. Verify no BA prompts leak into Assistant threads
15. Verify no document tools available in Assistant threads

## Migration Strategy

### Backward Compatibility

**Challenge:** Existing threads have no `thread_type` field.

**Solution:**
```python
# Migration: Add thread_type with default
op.add_column('threads', sa.Column('thread_type', sa.String(20),
    nullable=False, server_default='ba_assistant'))

# Update frontend to handle null (old data before migration)
String get threadType => json['thread_type'] ?? 'ba_assistant';
```

### Data Integrity

**Constraint:** BA threads must have `project_id`, Assistant threads must NOT have `project_id`.

**Enforcement:**
```python
# In thread creation route
if thread_type == ThreadType.BA_ASSISTANT and not project_id:
    raise HTTPException(400, "BA threads require a project")
if thread_type == ThreadType.GENERAL_ASSISTANT and project_id:
    raise HTTPException(400, "Assistant threads cannot have a project")
```

## Sources

- [Flutter App Architecture Guide (Official)](https://docs.flutter.dev/app-architecture/guide) - MVVM + BLoC pattern recommendations
- [FastAPI Multi-Tenancy Class Based Solution](https://sayanc20002.medium.com/fastapi-multi-tenancy-bf7c387d07b0) - Shared schema pattern with discriminator fields
- [Multi-Tenancy Apps in FastAPI](https://medium.com/@sandesh.thakar18/multi-tenancy-apps-in-fastapi-df80c7e7d52f) - Row-level isolation strategies
- [Multitenancy with FastAPI Practical Guide](https://app-generator.dev/docs/technologies/fastapi/multitenancy.html) - Architecture patterns

---
*Architecture research for: Assistant Integration into BA Assistant App*
*Researched: 2026-02-17*
*Confidence: HIGH (based on existing codebase analysis and established patterns)*
