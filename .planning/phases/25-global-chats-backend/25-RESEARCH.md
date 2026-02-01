# Phase 25: Global Chats Backend - Research

**Researched:** 2026-02-01
**Domain:** FastAPI backend, SQLAlchemy ORM, REST API design
**Confidence:** HIGH

## Summary

This phase extends the existing thread management system to support project-less threads and a global "Chats" listing. The codebase already has a solid foundation with SQLAlchemy models, FastAPI routes, and patterns that this phase extends rather than replaces.

The key technical challenge is making `project_id` nullable on the Thread model while maintaining backward compatibility with existing project-based thread operations. The existing summarization service provides the foundation for auto-generating thread titles.

**Primary recommendation:** Extend existing `/threads` routes with a new `GET /threads` endpoint for global listing, and modify `POST /threads` to accept optional `project_id` in request body. Minimal model changes required - add nullable `user_id` to Thread and make `project_id` nullable.

## Standard Stack

This phase uses the existing stack already in the codebase:

### Core (Already Present)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| FastAPI | 0.100+ | REST API framework | In use |
| SQLAlchemy | 2.0+ | Async ORM with mapped_column | In use |
| Pydantic | 2.0+ | Request/response validation | In use |
| aiosqlite | - | Async SQLite driver | In use |

### No New Dependencies Required

The phase uses existing patterns and libraries. No additions to `requirements.txt`.

## Architecture Patterns

### Current Model Structure (Thread)
```python
# Current: project_id is required, threads belong to project
class Thread(Base):
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,  # CHANGE: Make nullable=True
        index=True
    )
```

### Required Model Changes

**1. Make project_id nullable:**
```python
# Thread model changes
project_id: Mapped[Optional[str]] = mapped_column(
    String(36),
    ForeignKey("projects.id", ondelete="SET NULL"),  # Changed from CASCADE
    nullable=True,
    index=True
)
```

**2. Add user_id to Thread (for project-less threads):**
```python
# New column - direct user ownership for project-less threads
user_id: Mapped[Optional[str]] = mapped_column(
    String(36),
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=True,  # Only set when project_id is None
    index=True
)
```

**Ownership logic:**
- If `project_id` is set: Thread belongs to project's user (current behavior)
- If `project_id` is None: Thread belongs to `user_id` directly

**3. Add last_activity column for sorting:**
```python
# Track when user last interacted
last_activity_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=datetime.utcnow,
    onupdate=datetime.utcnow,
    nullable=False,
    index=True  # For efficient sorting
)
```

### API Response Shape

**Global threads listing response:**
```python
class GlobalThreadListResponse(BaseModel):
    """Thread in global list with project info."""
    id: str
    title: Optional[str]
    updated_at: str
    last_activity_at: str
    project_id: Optional[str]  # null for project-less
    project_name: Optional[str]  # null for project-less
    message_count: int
    model_provider: str
```

**Paginated response wrapper:**
```python
class PaginatedThreadsResponse(BaseModel):
    """Paginated threads with total count."""
    threads: List[GlobalThreadListResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
```

### New Endpoint: GET /threads

```python
@router.get("/threads", response_model=PaginatedThreadsResponse)
async def list_all_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all threads for current user, across all projects.

    Includes project-less threads.
    Sorted by last_activity_at DESC (most recent first).
    """
```

### Modified Endpoint: POST /threads

Create a new non-project-scoped create endpoint:

```python
@router.post("/threads", response_model=ThreadResponse)
async def create_global_thread(
    thread_data: GlobalThreadCreate,  # project_id optional
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create thread, optionally within a project."""
```

**Request model:**
```python
class GlobalThreadCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    project_id: Optional[str] = None  # Null = project-less thread
    model_provider: Optional[str] = Field(None, max_length=20)
```

### Ownership Validation Pattern

```python
async def validate_thread_ownership(
    db: AsyncSession,
    thread_id: str,
    user_id: str
) -> Thread:
    """
    Validate thread access for both project-based and project-less threads.
    """
    stmt = (
        select(Thread)
        .where(Thread.id == thread_id)
        .options(selectinload(Thread.project))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(404, "Thread not found")

    # Project-less thread: check direct ownership
    if thread.project_id is None:
        if thread.user_id != user_id:
            raise HTTPException(404, "Thread not found")
    # Project thread: check project ownership
    else:
        if thread.project.user_id != user_id:
            raise HTTPException(404, "Thread not found")

    return thread
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pagination | Custom offset tracking | SQLAlchemy offset/limit | Already handles edge cases |
| Activity tracking | Manual timestamp updates | SQLAlchemy onupdate | Automatic on any change |
| Title generation | New summarization logic | Existing `summarization_service.py` | Already implemented, works well |
| Auth validation | Per-endpoint checks | Existing `validate_thread_access` | Extend, don't replace |

## Common Pitfalls

### Pitfall 1: Nullable Foreign Key with CASCADE Delete
**What goes wrong:** When project is deleted, all project-less threads are also deleted
**Why it happens:** `ondelete="CASCADE"` propagates nulls incorrectly
**How to avoid:** Use `ondelete="SET NULL"` for project_id foreign key
**Warning signs:** Thread count suddenly drops when deleting a project

### Pitfall 2: Missing Index on user_id
**What goes wrong:** Global thread listing becomes slow as data grows
**Why it happens:** Query scans full table without index
**How to avoid:** Add `index=True` to user_id column
**Warning signs:** API latency increases over time

### Pitfall 3: Offset Pagination Data Drift
**What goes wrong:** Users see duplicate or missing threads when paginating
**Why it happens:** New activity changes sort order between page requests
**How to avoid:** Accept this limitation for offset pagination OR:
  - Document that refreshing on each load is expected behavior
  - Frontend should treat each page load as fresh data
**Note:** Per CONTEXT.md decision, offset pagination is acceptable with refresh-on-load

### Pitfall 4: Dual Ownership Validation Complexity
**What goes wrong:** Forgetting to check both ownership paths
**Why it happens:** Project-less and project threads have different ownership models
**How to avoid:** Single `validate_thread_ownership` function handles both cases
**Warning signs:** 403/404 errors only for certain thread types

### Pitfall 5: SQLite Migration Complexity
**What goes wrong:** Adding nullable column fails or requires batch migration
**Why it happens:** SQLite has limited ALTER TABLE support
**How to avoid:** Adding nullable columns works fine; only constraint changes need batch mode
**Reference:** Current codebase already handles this in `database.py` migrations

## Code Examples

### Database Query: Get All User Threads with Project Names

```python
# Source: Extended from existing codebase patterns
from sqlalchemy import select, func, outerjoin
from sqlalchemy.orm import selectinload

async def get_user_threads_paginated(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 25
) -> tuple[list[Thread], int]:
    """Get paginated threads for user with project info."""

    # Base query: threads owned directly OR via project
    base_query = (
        select(Thread)
        .outerjoin(Project, Thread.project_id == Project.id)
        .where(
            (Thread.user_id == user_id) |  # Direct ownership
            (Project.user_id == user_id)    # Project ownership
        )
        .options(selectinload(Thread.project))  # Eager load for project_name
        .options(selectinload(Thread.messages))  # For message_count
        .order_by(Thread.last_activity_at.desc())
    )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    offset = (page - 1) * page_size
    paginated = base_query.offset(offset).limit(page_size)
    result = await db.execute(paginated)
    threads = result.scalars().all()

    return threads, total
```

### Update Last Activity Timestamp

```python
# Source: Pattern from existing codebase
from datetime import datetime

async def update_thread_activity(db: AsyncSession, thread_id: str):
    """Update thread's last_activity_at timestamp."""
    stmt = select(Thread).where(Thread.id == thread_id)
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()

    if thread:
        thread.last_activity_at = datetime.utcnow()
        await db.commit()
```

**When to call:**
- After saving user message (in conversations.py)
- After loading thread detail (view = activity)

### Create Project-less Thread

```python
# Source: Extended from existing create_thread
async def create_thread(
    project_id: Optional[str],
    user_id: str,
    title: Optional[str],
    model_provider: str,
    db: AsyncSession
) -> Thread:
    """Create thread with or without project."""

    # Validate project if provided
    if project_id:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(404, "Project not found")

    thread = Thread(
        project_id=project_id,
        user_id=user_id if project_id is None else None,  # Only set for project-less
        title=title or "New Chat",
        model_provider=model_provider or "anthropic",
        last_activity_at=datetime.utcnow()
    )

    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return thread
```

### Title Auto-Generation (Existing Service)

The existing `summarization_service.py` already implements title generation. Key parameters from CONTEXT.md:

- Trigger: After 5th AI response (5 messages total)
- Summary scope: First 5 messages
- Max title length: 100 characters

The existing implementation at line 93-168 of `summarization_service.py` handles this. No changes needed for the backend - just ensure frontend calls trigger at the right time.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Threads require project | Threads can be project-less | This phase | More flexible chat UX |
| Sort by created_at | Sort by last_activity_at | This phase | More relevant ordering |
| Project-scoped API only | Global + project-scoped | This phase | New endpoint added |

**No deprecated patterns:** This phase extends existing patterns rather than replacing them.

## Open Questions

### 1. Frontend Thread Model Changes

**What we know:** Current Thread model has required `projectId`
**What's unclear:** Frontend needs model update for nullable projectId and new projectName
**Recommendation:** Frontend phase should update Thread model to match new API response

### 2. Existing Thread Migration

**What we know:** Existing threads all have project_id set
**What's unclear:** Whether to backfill user_id for existing project threads
**Recommendation:** Don't backfill - ownership derives from project.user_id for existing threads

### 3. Cascade Delete Behavior

**What we know:** Project deletion currently cascades to threads
**What's unclear:** Should project-less threads survive if attached project is later deleted?
**Recommendation:** Yes, use `SET NULL` so thread becomes project-less rather than deleted

## Sources

### Primary (HIGH confidence)
- Existing codebase: `backend/app/models.py` - Thread, Project models
- Existing codebase: `backend/app/routes/threads.py` - Current thread endpoints
- Existing codebase: `backend/app/routes/projects.py` - Project ownership patterns
- Existing codebase: `backend/app/services/summarization_service.py` - Title generation

### Secondary (MEDIUM confidence)
- [SQLAlchemy nullable foreign keys discussion](https://github.com/sqlalchemy/sqlalchemy/discussions/10964) - Many to one with optional FK
- [REST API pagination best practices](https://www.speakeasy.com/api-design/pagination) - Offset vs cursor tradeoffs
- [Fixing ALTER TABLE errors with SQLite](https://blog.miguelgrinberg.com/post/fixing-alter-table-errors-with-flask-migrate-and-sqlite) - Migration patterns

### Tertiary (LOW confidence)
- General web search on timestamp tracking patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing codebase patterns
- Architecture: HIGH - Extending proven patterns
- Pitfalls: HIGH - Based on codebase analysis and general SQL knowledge

**Research date:** 2026-02-01
**Valid until:** 2026-03-01 (stable patterns, no external dependencies)
