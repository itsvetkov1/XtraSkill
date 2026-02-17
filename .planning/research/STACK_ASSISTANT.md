# Technology Stack: Assistant Integration

**Project:** BA Assistant - Assistant Mode Addition
**Researched:** 2026-02-17

## Recommended Stack (No Changes Required)

The existing stack fully supports the Assistant integration without additional dependencies.

### Backend (Python/FastAPI)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | 0.115.x | Web framework | Already in use, supports async, SSE, dependency injection |
| SQLAlchemy | 2.0.x | ORM | Already in use, supports enums natively via `Enum()` |
| Alembic | 1.13.x | Migrations | Already in use, handles schema changes |
| Pydantic | 2.x | Validation | Already in use, validates thread_type in request models |

**No new backend dependencies required.**

### Frontend (Flutter)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Flutter | 3.x | UI framework | Already in use, cross-platform support |
| Provider | 6.x | State management | Already in use for thread state |
| GoRouter | 14.x | Navigation | Already in use, supports dynamic routing |

**No new frontend dependencies required.**

### Database Schema Changes

| Change | Implementation | Migration Risk |
|--------|---------------|----------------|
| Add `ThreadType` enum | SQLAlchemy Enum type | LOW - non-breaking |
| Add `thread_type` column | `nullable=False`, `server_default='ba_assistant'` | LOW - backward compatible |
| Index on thread_type | Composite index `(user_id, thread_type, last_activity_at)` | LOW - performance optimization |

**Migration SQL:**
```sql
-- Add thread_type column with default
ALTER TABLE threads ADD COLUMN thread_type VARCHAR(20) NOT NULL DEFAULT 'ba_assistant';

-- Create index for thread filtering queries
CREATE INDEX idx_threads_user_type_activity ON threads(user_id, thread_type, last_activity_at DESC);
```

### AI Service Architecture (Existing)

No changes to LLM adapter infrastructure. Thread type discrimination happens at the service layer:

```
AIService (service/ai_service.py)
    ├── Conditional prompt selection
    ├── Conditional tool selection
    └── Delegates to existing adapters
        ├── AnthropicAdapter (direct API)
        ├── GeminiAdapter (direct API)
        ├── DeepSeekAdapter (direct API)
        ├── ClaudeCLIAdapter (subprocess)
        └── ClaudeAgentAdapter (SDK)
```

### System Prompts (New Constants)

| Constant | Location | Size | Purpose |
|----------|----------|------|---------|
| `BA_SYSTEM_PROMPT` | `ai_service.py` | ~600 lines | Existing BA discovery prompt |
| `ASSISTANT_SYSTEM_PROMPT` | `ai_service.py` | ~5 lines | New generic assistant prompt |

**Example:**
```python
# backend/app/services/ai_service.py

BA_SYSTEM_PROMPT = """<system_prompt>
  <quick_reference>
    <purpose>Systematic business requirements discovery...</purpose>
    ...
  </quick_reference>
</system_prompt>"""

ASSISTANT_SYSTEM_PROMPT = """You are Claude, a helpful AI assistant created by Anthropic.
Provide clear, accurate, and helpful responses to user questions.
Be concise but thorough."""
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Thread type storage | Database enum field | Frontend state only | Lost on refresh, can't filter/query |
| Service architecture | Single AIService with conditionals | Separate BAService + AssistantService | Code duplication, harder to maintain |
| System prompt loading | Python constants | External YAML files | Overkill for 2 prompts, harder to debug |
| Tool availability | Conditional in stream_chat | Separate tool registries | Unnecessary complexity |
| MCP config | Conditional generation | Always load all servers | Performance penalty for Assistant threads |

## Installation

No new installations required. Existing dependencies handle all functionality.

### Migration Application

```bash
# Backend: Apply schema migration
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add thread_type discriminator"
alembic upgrade head

# Frontend: No dependencies to install
cd frontend
flutter pub get  # Existing dependencies sufficient
```

### Configuration Changes

**None required.** No environment variables, no config files, no external services.

## Development Tools (Optional Enhancements)

If developing the Assistant screen from scratch (not cloning ChatsScreen), these tools may be helpful:

| Tool | Purpose | Install | Necessity |
|------|---------|---------|-----------|
| Flutter DevTools | UI debugging | Built-in | Optional |
| DB Browser for SQLite | Inspect thread_type values | `brew install --cask db-browser-for-sqlite` | Optional |
| Postman/Insomnia | Test API endpoints | External app | Optional |

## Performance Considerations

### Database Indexing

Recommended indexes for thread filtering:

```sql
-- Primary index for Assistant screen queries
CREATE INDEX idx_threads_user_type_activity 
ON threads(user_id, thread_type, last_activity_at DESC);

-- Index for project-scoped BA threads (existing use case)
CREATE INDEX idx_threads_project_type 
ON threads(project_id, thread_type) WHERE project_id IS NOT NULL;
```

### Query Patterns

**Assistant screen query (new):**
```python
# Will use idx_threads_user_type_activity
threads = await db.execute(
    select(Thread)
    .where(Thread.user_id == user_id, Thread.thread_type == 'assistant')
    .order_by(Thread.last_activity_at.desc())
)
```

**BA threads in project (existing):**
```python
# Will use idx_threads_project_type
threads = await db.execute(
    select(Thread)
    .where(Thread.project_id == project_id, Thread.thread_type == 'ba_assistant')
    .order_by(Thread.created_at.desc())
)
```

### Memory Impact

**System prompt storage:**
- BA_SYSTEM_PROMPT: ~100KB in memory (loaded once at service initialization)
- ASSISTANT_SYSTEM_PROMPT: ~1KB in memory
- Total overhead: Negligible

**Thread model size:**
- thread_type field: 20 bytes per thread
- Index overhead: ~100 bytes per thread
- Impact: Minimal (< 0.1% database growth)

## Sources

- [SQLAlchemy 2.0 Enum Types](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum) - Native enum support
- [Alembic Schema Migrations](https://alembic.sqlalchemy.org/en/latest/tutorial.html) - Adding columns with defaults
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/) - Existing pattern usage
- [Flutter Provider State Management](https://pub.dev/packages/provider) - Already in use

---
*Stack research for: Assistant Integration*
*Researched: 2026-02-17*
*Conclusion: Existing stack is sufficient, zero new dependencies required*
