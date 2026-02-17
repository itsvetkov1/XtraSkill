# Technology Stack

**Project:** XtraSkill - Assistant Section Separation
**Researched:** 2026-02-17

## Recommended Stack

### Core Framework (No Changes)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Flutter | ^3.9.2 | Web/mobile frontend | Already validated; no changes needed |
| FastAPI | >=0.129.0 | Python async backend | Current: 0.115.0+; update recommended for Python 3.14 support and Pydantic v2 improvements |
| GoRouter | ^17.0.1 | Declarative routing | Already integrated; StatefulShellRoute pattern perfect for section separation |
| Provider | ^6.1.5 | State management | Already integrated; sufficient for assistant section state |

### Database (No Changes Required)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLAlchemy | >=2.0.46 | Async ORM | Current: 2.0.35+; update recommended for async session improvements and Python 3.14 support |
| SQLite | (bundled) | Local development database | Thread categorization via enum field (no schema redesign needed) |

### New/Updated Dependencies

#### Backend
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| alembic | >=1.13.0 | Database migrations | Create migration for thread_type enum field addition |

#### Frontend
**NO NEW DEPENDENCIES REQUIRED**

All necessary libraries already present:
- `go_router: ^17.0.1` — Branch navigation via StatefulShellRoute
- `provider: ^6.1.5` — State management for section-specific providers
- `dio: ^5.9.0` — HTTP client for backend API calls
- `flutter_client_sse: ^2.0.0` — SSE streaming for Claude Code CLI responses

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Thread Categorization | Single `thread_type` enum field | Separate tables (ba_threads, assistant_threads) | Over-engineering; adds join complexity without benefit |
| Routing Strategy | Add 5th StatefulShellBranch | Nested routes under existing branch | Doesn't provide UX separation (Assistant needs its own sidebar entry) |
| State Management | Existing Provider pattern | Riverpod 3.0 | Provider sufficient for scope; migration unjustified for single feature |
| System Prompt Routing | Conditional in ai_service.py based on thread_type | Separate service classes | KISS principle; conditional is 5 lines vs 200+ lines of duplication |

## Integration Points

### 1. Thread Model Enhancement

**Change:** Add `thread_type` enum field to existing Thread model

**SQLAlchemy 2.0 Pattern:**
```python
class ThreadType(str, PyEnum):
    """Thread categorization for feature separation."""
    BA_ASSISTANT = "ba_assistant"  # Uses BA system prompt + tools
    ASSISTANT = "assistant"         # Bypasses BA prompt, direct Claude conversation

class Thread(Base):
    # ... existing fields ...

    # NEW: Thread type for section categorization
    thread_type: Mapped[ThreadType] = mapped_column(
        Enum(ThreadType, native_enum=False, length=20),
        nullable=False,
        default=ThreadType.BA_ASSISTANT,
        index=True  # For filtering by type
    )
```

**Migration Required:** Yes (Alembic)
```bash
alembic revision -m "add_thread_type_to_threads"
# Migration will add column with default=ba_assistant for backward compatibility
```

**Rationale:**
- Enum ensures type safety at database and Python levels
- `native_enum=False` uses VARCHAR with CHECK constraint for SQLite compatibility
- Indexed for efficient filtering (`/api/threads?thread_type=assistant`)
- Default preserves existing behavior (all current threads remain BA mode)

### 2. Backend API Changes

#### New Endpoints (MINIMAL)
```python
# routes/threads.py — MODIFY existing endpoint
@router.get("/threads", response_model=PaginatedThreadsResponse)
async def list_all_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    thread_type: Optional[ThreadType] = Query(None),  # NEW filter
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Filter query by thread_type if provided
    if thread_type:
        base_query = base_query.where(Thread.thread_type == thread_type)
```

#### System Prompt Routing (ai_service.py)
```python
async def stream_chat(thread: Thread, user_message: str, ...):
    # NEW: Skip BA system prompt for assistant threads
    if thread.thread_type == ThreadType.ASSISTANT:
        messages = conversation_history  # No system prompt injection
    else:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
```

**Files Modified:**
- `backend/app/models.py` — Add ThreadType enum
- `backend/app/routes/threads.py` — Add thread_type to create/update/list
- `backend/app/services/ai_service.py` — Conditional system prompt
- `backend/alembic/versions/XXXX_add_thread_type.py` — Migration

### 3. Frontend Routing Changes

**Current Structure (4 branches):**
```dart
StatefulShellRoute.indexedStack(
  branches: [
    StatefulShellBranch(routes: [GoRoute(path: '/home', ...)]),      // 0
    StatefulShellBranch(routes: [GoRoute(path: '/chats', ...)]),     // 1
    StatefulShellBranch(routes: [GoRoute(path: '/projects', ...)]),  // 2
    StatefulShellBranch(routes: [GoRoute(path: '/settings', ...)]),  // 3
  ],
)
```

**New Structure (5 branches):**
```dart
StatefulShellRoute.indexedStack(
  branches: [
    StatefulShellBranch(routes: [GoRoute(path: '/home', ...)]),        // 0
    StatefulShellBranch(routes: [GoRoute(path: '/assistant', ...)]),   // 1 NEW
    StatefulShellBranch(routes: [GoRoute(path: '/chats', ...)]),       // 2 (was 1)
    StatefulShellBranch(routes: [GoRoute(path: '/projects', ...)]),    // 3 (was 2)
    StatefulShellBranch(routes: [GoRoute(path: '/settings', ...)]),    // 4 (was 3)
  ],
)
```

**Sidebar Destinations (responsive_scaffold.dart):**
```dart
static const List<_NavigationDestination> _destinations = [
  _NavigationDestination(icon: Icons.home_outlined, label: 'Home'),
  _NavigationDestination(icon: Icons.auto_awesome_outlined, label: 'Assistant'),  // NEW
  _NavigationDestination(icon: Icons.chat_bubble_outline, label: 'Chats'),
  _NavigationDestination(icon: Icons.folder_outlined, label: 'Projects'),
  _NavigationDestination(icon: Icons.settings_outlined, label: 'Settings'),
];
```

**Files Modified:**
- `frontend/lib/main.dart` — Add /assistant branch
- `frontend/lib/widgets/responsive_scaffold.dart` — Add Assistant destination
- `frontend/lib/screens/assistant_screen.dart` — NEW (clone ChatsScreen, filter by thread_type=assistant)
- `frontend/lib/screens/conversation/conversation_screen.dart` — OPTIONAL: Pass thread_type to new thread creation

### 4. State Management (NO NEW PATTERNS)

**Existing Providers Reused:**
- `ThreadProvider` — Already handles thread CRUD; add thread_type filter method
- `ConversationProvider` — No changes needed (works with any thread)
- `ChatsProvider` — Add filtering by thread_type

**New Methods (ThreadProvider):**
```dart
class ThreadProvider extends ChangeNotifier {
  // Existing: loadThreads() — loads all threads

  // NEW: Filter by type
  Future<void> loadThreadsByType(ThreadType type) async {
    final response = await dio.get('/api/threads', queryParameters: {'thread_type': type});
    // ... existing parsing logic
  }
}
```

**Rationale:** Provider pattern sufficient; thread filtering is data-layer concern, not architecture change.

## What NOT to Add

### ❌ Avoid Over-Engineering

| Temptation | Why Avoid |
|-----------|-----------|
| Separate AssistantService class | Duplication of ai_service.py for 5-line conditional |
| Riverpod migration | Unjustified complexity; Provider works fine |
| Redux/BLoC for section state | State is simple (thread list with filter); Provider sufficient |
| GraphQL API layer | REST endpoints handle thread_type filter efficiently |
| Separate AssistantThread model | Single Thread table with enum is cleaner |
| Feature flag system | This is a permanent UX change, not an experiment |
| Dedicated AssistantProvider | ThreadProvider already handles thread operations |

### ❌ Avoid Premature Optimization

| Defer Until Needed | Why Wait |
|-------------------|----------|
| Thread type indexing optimization | SQLite handles enum WHERE clauses efficiently; optimize if >10K threads |
| Caching layer for thread lists | Current pagination works; cache if latency becomes issue |
| Web Workers for large thread lists | Flutter web handles lists fine; optimize if scroll performance degrades |

## Installation

### Backend Updates (Optional but Recommended)

```bash
cd backend

# Update FastAPI for Python 3.14 support and Pydantic v2 improvements
pip install --upgrade 'fastapi[standard]>=0.129.0'

# Update SQLAlchemy for async session improvements
pip install --upgrade 'sqlalchemy>=2.0.46'

# Regenerate requirements.txt
pip freeze > requirements.txt
```

### Frontend (No Changes)

Existing dependencies sufficient. No `flutter pub add` commands needed.

### Database Migration

```bash
cd backend

# Create migration for thread_type field
alembic revision -m "add_thread_type_to_threads"

# Edit migration file:
# - Add thread_type column with default='ba_assistant'
# - Add index on thread_type
# - Backfill existing threads with ba_assistant

# Apply migration
alembic upgrade head
```

**Migration Template:**
```python
def upgrade():
    op.add_column('threads', sa.Column(
        'thread_type',
        sa.String(20),
        nullable=False,
        server_default='ba_assistant'
    ))
    op.create_index('ix_threads_thread_type', 'threads', ['thread_type'])

def downgrade():
    op.drop_index('ix_threads_thread_type', 'threads')
    op.drop_column('threads', 'thread_type')
```

## Version Notes

### FastAPI 0.129.0 (Latest: 2026-02-12)
- **Upgrade from:** 0.115.0
- **Benefits:** Python 3.14 support, Pydantic v1 deprecation warnings, Starlette 0.40.0+ compatibility
- **Breaking changes:** None for this project (Pydantic v2 already in use)
- **Recommendation:** Upgrade to stay current with security patches

### SQLAlchemy 2.0.46 (Latest: 2026-01-21)
- **Upgrade from:** 2.0.35
- **Benefits:** Per-session execution options, free-threaded Python support, async session improvements
- **Breaking changes:** None (2.0.35 → 2.0.46 is patch series)
- **Recommendation:** Upgrade for async performance improvements

### GoRouter 17.0.1 (Current)
- **Already on latest:** ✅
- **Relevant features:** StatefulShellRoute.indexedStack (perfect for section separation)
- **Note:** Requires Flutter 3.32 / Dart 3.8 minimum (project is on 3.9.2, compatible)

### Provider 6.1.5 (Current)
- **Already on latest:** ✅
- **Status:** Considered legacy for complex apps, but perfect for this scope
- **Alternative considered:** Riverpod 3.0 (rejected: overkill for thread filtering)

## Confidence Assessment

| Decision | Confidence | Evidence |
|----------|-----------|----------|
| Thread enum field | **HIGH** | SQLAlchemy 2.0 docs, verified pattern in production apps |
| StatefulShellRoute for section | **HIGH** | GoRouter official docs, already validated in project |
| Provider state management | **HIGH** | Already integrated, sufficient for scope |
| FastAPI/SQLAlchemy versions | **HIGH** | Official release notes, PyPI verified |
| No new frontend deps | **MEDIUM** | Existing stack covers needs, but haven't built AssistantScreen yet |
| Migration backward compatibility | **HIGH** | Default value pattern prevents breaking existing threads |

## Sources

### Official Documentation
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) — v0.129.0 (2026-02-12)
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [GoRouter pub.dev](https://pub.dev/packages/go_router) — v17.0.1
- [Provider pub.dev](https://pub.dev/packages/provider) — v6.1.5

### Community Resources
- [Flutter Bottom Navigation with GoRouter](https://codewithandrea.com/articles/flutter-bottom-navigation-bar-nested-routes-gorouter/)
- [SQLAlchemy Enum Best Practices 2026](https://copyprogramming.com/howto/access-enum-value-from-a-database-record-in-python-sqlalchemy)
- [Flutter State Management in 2026](https://foresightmobile.com/blog/best-flutter-state-management)

### Technical Discussions
- [StatefulShellRoute State Preservation](https://medium.com/@valerii.novykov/how-to-disable-saving-state-of-certain-branches-in-statefulshellroute-gorouter-42c8d6cc4a34)
- [SQLAlchemy Enum Filtering Issues](https://github.com/sqlalchemy/sqlalchemy/issues/7097)
