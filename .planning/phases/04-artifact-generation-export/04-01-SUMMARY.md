---
phase: 04-artifact-generation-export
plan: 01
subsystem: artifact-generation
tags: [claude-tools, database-model, api-endpoints, sse-events]

dependency-graph:
  requires:
    - 03: AI streaming infrastructure
    - 02: Thread and database models
  provides:
    - Artifact database model with ArtifactType enum
    - save_artifact Claude tool for autonomous generation
    - artifact_created SSE event for frontend notifications
    - GET endpoints for artifact list and detail
  affects:
    - 04-02: Frontend artifact display and export

tech-stack:
  added: []
  patterns:
    - Claude tool execution with database persistence
    - SSE event types extended for artifact notifications
    - Pydantic response models with from_attributes

key-files:
  created:
    - backend/app/routes/artifacts.py
  modified:
    - backend/app/models.py
    - backend/app/services/ai_service.py
    - backend/app/routes/conversations.py
    - backend/main.py

decisions:
  - id: artifact-model-design
    choice: "Markdown content primary with optional JSON"
    why: "Human-readable output for export; JSON reserved for future structured access"
  - id: no-post-endpoint
    choice: "Artifacts created only via chat tool"
    why: "Generation happens through Claude tool execution, not manual POST"
  - id: sse-artifact-event
    choice: "artifact_created event with id, type, title"
    why: "Frontend can show toast notification and update artifact list"

metrics:
  duration: "3 min 31 sec"
  completed: "2026-01-24"
  tasks: "3/3"
---

# Phase 04 Plan 01: Backend Artifact Generation Summary

**One-liner:** Artifact model with save_artifact Claude tool enabling autonomous generation of user stories, acceptance criteria, and requirements docs during conversations.

## What Was Built

### 1. Artifact Database Model (Task 1)

**File:** `backend/app/models.py`

Added `ArtifactType` enum and `Artifact` model:

```python
class ArtifactType(str, PyEnum):
    USER_STORIES = "user_stories"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    REQUIREMENTS_DOC = "requirements_doc"

class Artifact(Base):
    __tablename__ = "artifacts"
    id: Mapped[str]           # UUID primary key
    thread_id: Mapped[str]    # FK to threads with cascade delete
    artifact_type: Mapped[ArtifactType]
    title: Mapped[str]
    content_markdown: Mapped[str]
    content_json: Mapped[Optional[str]]  # Reserved for structured data
    created_at: Mapped[datetime]
```

Thread model updated with `artifacts` relationship for cascade delete.

### 2. save_artifact Claude Tool (Task 2)

**File:** `backend/app/services/ai_service.py`

Added `SAVE_ARTIFACT_TOOL` definition:
- Input schema: `artifact_type` (enum), `title` (string), `content_markdown` (string)
- Tool description guides Claude when to use (on "create", "generate", "write" requests)
- Suggests using `search_documents` first for context

Updated `execute_tool`:
- Returns `tuple[str, Optional[dict]]` for result + event data
- Persists artifact to database on tool execution
- Returns artifact metadata for SSE event emission

Updated `stream_chat`:
- Accepts `thread_id` parameter (needed for artifact persistence)
- Emits `artifact_created` SSE event with artifact id, type, title
- Shows "Generating artifact..." status during tool execution

Updated `SYSTEM_PROMPT`:
- Added instruction 5: Generate artifacts when users request documentation

### 3. Artifacts API Endpoints (Task 3)

**File:** `backend/app/routes/artifacts.py`

Two GET endpoints (no POST needed - generation via chat):

```
GET /api/threads/{thread_id}/artifacts
- Returns ArtifactListItem (id, thread_id, type, title, created_at)
- Validates user owns thread's project

GET /api/artifacts/{artifact_id}
- Returns ArtifactResponse (full content_markdown included)
- Validates user owns artifact's thread's project
```

Router registered in `backend/main.py`.

## Technical Details

### SSE Event Types (Extended)

```
text_delta         - Incremental text from Claude
tool_executing     - Tool is being executed (status message)
artifact_created   - Artifact was generated and saved  <-- NEW
message_complete   - Response complete with usage stats
error              - Error occurred
```

### Database Schema

```sql
CREATE TABLE artifacts (
    id VARCHAR(36) PRIMARY KEY,
    thread_id VARCHAR(36) NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    artifact_type VARCHAR(30) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content_markdown TEXT NOT NULL,
    content_json TEXT,
    created_at DATETIME NOT NULL
);
CREATE INDEX ix_artifacts_thread_id ON artifacts (thread_id);
```

### Tool Response Format

When Claude uses `save_artifact`, it receives:
```
Artifact saved successfully: 'Login Feature - User Stories' (ID: uuid).
User can now export as PDF, Word, or Markdown from the artifacts list.
```

## Commits

| Hash | Message |
|------|---------|
| e77a60e | feat(04-01): add Artifact model with ArtifactType enum |
| 0e4b34d | feat(04-01): add save_artifact tool for artifact generation |
| df679ff | feat(04-01): add artifacts API endpoints for list and detail |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for 04-02 (Frontend Artifact Display):**

- Artifact model with thread relationship ready for frontend queries
- GET endpoints available for list and detail views
- artifact_created SSE event ready for frontend notification handling
- Markdown content ready for rendering and export

**Integration Points for Frontend:**
- SSE event: `artifact_created` with `{id, artifact_type, title}`
- List endpoint: `GET /api/threads/{threadId}/artifacts`
- Detail endpoint: `GET /api/artifacts/{artifactId}`
- Content format: Markdown (frontend renders with markdown package)
