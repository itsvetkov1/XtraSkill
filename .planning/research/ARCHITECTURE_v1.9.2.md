# Architecture Research: v1.9.2 Resilience & AI Transparency

**Research Date:** 2026-02-02
**Milestone:** v1.9.2 - Resilience & AI Transparency
**Confidence:** HIGH (verified against existing codebase)

## Executive Summary

This document analyzes how the six target features for v1.9.2 should integrate with the existing BA Assistant architecture. The current architecture follows a clean separation pattern with:
- **Flutter frontend** using Provider pattern for state management
- **FastAPI backend** with SSE streaming for AI responses
- Clear service boundaries and established data flow patterns

All target features can be implemented within existing architecture patterns with minimal structural changes.

---

## Current Architecture Overview

### High-Level Component Diagram

```
+------------------+          +-----------------+          +-------------+
|                  |   SSE    |                 |          |             |
|  Flutter Web     |<---------|  FastAPI        |<-------->|  SQLite DB  |
|  (Provider)      |   REST   |  (Routes/       |          |             |
|                  |--------->|   Services)     |          +-------------+
+------------------+          +-----------------+
        |                            |
        |                            v
        |                     +--------------+
        |                     |   LLM APIs   |
        |                     | (Anthropic/  |
        |                     |  Google/etc) |
        |                     +--------------+
        v
+------------------+
|  Local Storage   |
| (SharedPrefs/    |
|  SecureStorage)  |
+------------------+
```

### Frontend Architecture (Flutter)

**State Management: Provider Pattern**

| Provider | Responsibility | Key State |
|----------|---------------|-----------|
| `AuthProvider` | Authentication state | `isAuthenticated`, `email`, `displayName` |
| `ConversationProvider` | Chat state & streaming | `messages`, `isStreaming`, `streamingText`, `error` |
| `ProjectProvider` | Project CRUD | `projects`, `loading`, `error` |
| `DocumentProvider` | Document management | `documents`, `uploading`, `uploadProgress` |
| `ThemeProvider` | Theme persistence | `themeMode`, `isDarkMode` |
| `ProviderProvider` | Default AI provider | `selectedProvider` |
| `ChatsProvider` | Global threads list | `threads`, `loading` |

**Service Layer**

| Service | Purpose | Communication |
|---------|---------|---------------|
| `AIService` | SSE streaming chat | POST to `/threads/{id}/chat`, SSE response |
| `AuthService` | OAuth + token usage | REST to `/auth/*` |
| `ThreadService` | Thread CRUD | REST to `/threads/*` |
| `DocumentService` | Document upload/search | REST + multipart to `/documents/*` |

**Key Screens**

| Screen | Route | Providers Used |
|--------|-------|----------------|
| `ConversationScreen` | `/chats/:threadId`, `/projects/:id/threads/:threadId` | `ConversationProvider` |
| `SettingsScreen` | `/settings` | `ThemeProvider`, `ProviderProvider`, `AuthProvider` |
| `DocumentUploadScreen` | Dialog/Modal | `DocumentProvider` |
| `ProjectDetailScreen` | `/projects/:id` | `ProjectProvider`, `ThreadProvider`, `DocumentProvider` |

### Backend Architecture (FastAPI)

**Route Organization**

```
/api
  /auth        - OAuth, token refresh, usage stats
  /projects    - Project CRUD
  /threads     - Thread CRUD, global list
  /documents   - Document upload, search, content
  /artifacts   - Artifact retrieval, export

/api/threads/{thread_id}/chat - SSE streaming endpoint
```

**Service Layer**

| Service | Purpose |
|---------|---------|
| `AIService` | LLM adapter pattern, tool execution, streaming |
| `TokenTrackingService` | Usage recording, budget checking |
| `DocumentSearchService` | FTS5 search, document indexing |
| `ConversationService` | Message persistence, context building |

**SSE Streaming Flow**

```
[Frontend]                    [Backend]                      [LLM]
    |                             |                            |
    |--- POST /chat ------------>|                            |
    |                             |--- stream_chat() -------->|
    |                             |                            |
    |<-- SSE: text_delta --------|<-- text chunk -------------|
    |<-- SSE: text_delta --------|<-- text chunk -------------|
    |<-- SSE: tool_executing ----|    (tool use detected)    |
    |                             |--- execute_tool() ------->|
    |<-- SSE: artifact_created --|    (tool result)          |
    |<-- SSE: text_delta --------|<-- continuation ----------|
    |<-- SSE: message_complete --|<-- stop_reason: end ------|
    |                             |                            |
```

---

## Feature-by-Feature Architecture Integration

### Feature 1: Network Interruption Handling During SSE Streaming

**Current State:**
- `AIService.streamChat()` uses `flutter_client_sse` for SSE
- Errors yield `ErrorEvent` which sets `ConversationProvider._error`
- No automatic retry or reconnection logic
- Heartbeat mechanism exists on backend (`stream_with_heartbeat()`)

**Integration Points:**

```
+-------------------+     +------------------------+     +------------------+
| ConversationScreen|     | ConversationProvider   |     | AIService        |
+-------------------+     +------------------------+     +------------------+
        |                          |                           |
        |-- sendMessage() ------->|                           |
        |                          |-- streamChat() --------->|
        |                          |                           |
        |                          |   [CONNECTION LOST]       |
        |                          |                           |
        |                          |<-- ErrorEvent ------------|
        |                          |                           |
        |<-- error + canRetry ----|                           |
        |                          |                           |
        |-- retryLastMessage() -->|                           |
        |                          |-- streamChat() --------->|
        |                          |                           |
```

**Component Boundaries:**

| Layer | Component | Changes Needed |
|-------|-----------|----------------|
| **Frontend Service** | `AIService` | Add connection state tracking, retry with exponential backoff |
| **Frontend Provider** | `ConversationProvider` | Already has `canRetry`, `retryLastMessage()` - extend for auto-retry option |
| **Frontend Widget** | `StreamingMessage` | Add connection status indicator during retry attempts |
| **Backend** | `conversations.py` | Already has heartbeat; add client disconnect detection logging |

**Data Flow:**

```
AIService
  ├── _connectionState: enum (connected, connecting, disconnected, retrying)
  ├── _retryAttempt: int
  ├── _maxRetries: int (3)
  ├── _retryDelays: List<Duration> ([1s, 2s, 4s])
  │
  └── streamChat()
       ├── yield ConnectionStateEvent(connecting)
       ├── try SSEClient.subscribeToSSE()
       │     └── on error: yield ConnectionStateEvent(disconnected)
       │                   if retryAttempt < maxRetries:
       │                     yield ConnectionStateEvent(retrying, attempt)
       │                     delay(retryDelays[retryAttempt])
       │                     retryAttempt++
       │                     continue
       │                   else:
       │                     yield ErrorEvent(message, canRetry: true)
       └── yield ConnectionStateEvent(connected)
```

**Suggested Build Order:**
1. Add `ConnectionStateEvent` to `ai_service.dart`
2. Implement retry logic in `AIService.streamChat()`
3. Update `ConversationProvider` to handle connection state events
4. Update `StreamingMessage` widget to show connection status
5. Add auto-retry preference to Settings (optional)

---

### Feature 2: Token Budget Tracking with Warning Thresholds

**Current State:**
- `TokenUsage` model exists in frontend (`models/token_usage.dart`)
- `SettingsScreen` displays usage with progress bar (orange at >80%)
- Backend has `token_tracking.py` with `check_user_budget()` returning boolean
- `/auth/usage` endpoint returns monthly stats
- Hard block at 100% budget via 429 response

**Integration Points:**

```
+----------------+     +---------------+     +------------------+
| SettingsScreen |     | AuthService   |     | /auth/usage      |
+----------------+     +---------------+     +------------------+
        |                    |                       |
        |-- getUsage() ---->|-- GET ---------------->|
        |                    |                       |
        |<-- TokenUsage ----|<-- {total_cost, budget, ...}
        |                    |                       |
+--------------------+
| ConversationScreen |  (NEW: check before send)
+--------------------+
        |                    |                       |
        |-- checkBudget() ->|-- HEAD/GET ---------->|
        |                    |                       |
        |<-- {nearLimit, remaining}                 |
        |                    |                       |
```

**Component Boundaries:**

| Layer | Component | Changes Needed |
|-------|-----------|----------------|
| **Frontend Model** | `TokenUsage` | Add warning threshold properties, `isNearLimit`, `isAtLimit` |
| **Frontend Service** | `AuthService` | Add lightweight `checkBudgetStatus()` method |
| **Frontend Provider** | New `BudgetProvider` or extend `AuthProvider` | Periodic budget check, expose `budgetStatus` |
| **Frontend Widget** | New `BudgetWarningBanner` | Warning UI at 80%, 90%, 100% |
| **Frontend Screen** | `ConversationScreen` | Show banner above chat input when near limit |
| **Backend** | `auth.py` | Add `/auth/budget-status` lightweight endpoint |
| **Backend** | `token_tracking.py` | Add `get_budget_status()` with thresholds |

**Data Flow:**

```
BudgetProvider (or extension of AuthProvider)
  ├── budgetStatus: BudgetStatus? (ok, warning, critical, exceeded)
  ├── usagePercentage: double
  ├── remainingBudget: double
  │
  ├── checkBudget() async
  │     └── GET /auth/budget-status
  │           └── returns { status, percentage, remaining, warningThreshold }
  │
  └── _schedulePeriodicCheck()  // every 5 min while app active

TokenUsage model extension:
  ├── isNearLimit: bool (>80%)
  ├── isCritical: bool (>90%)
  ├── isExceeded: bool (>=100%)
  └── statusColor: Color (based on percentage)
```

**Warning Thresholds:**

| Threshold | Color | Message |
|-----------|-------|---------|
| >80% | Orange | "You've used 85% of your monthly budget" |
| >90% | Red | "Budget nearly exhausted (95% used)" |
| 100% | Red | "Monthly budget exceeded - chat disabled until next month" |

**Suggested Build Order:**
1. Extend `TokenUsage` model with threshold properties
2. Add `/auth/budget-status` backend endpoint (lightweight)
3. Create `BudgetProvider` or extend `AuthProvider`
4. Create `BudgetWarningBanner` widget
5. Integrate banner into `ConversationScreen`
6. Add periodic checking logic

---

### Feature 3: Persistent Conversation Mode Indicator

**Current State:**
- `ModeSelector` widget shows Meeting/Document Refinement modes
- Mode is sent as first message, not stored
- No visual indicator after mode selected
- `ProviderIndicator` shows AI provider (Anthropic/Google)

**Integration Points:**

```
+-------------------+     +----------------------+     +-----------------+
| ConversationScreen|     | ConversationProvider |     | Thread model    |
+-------------------+     +----------------------+     +-----------------+
        |                          |                          |
        |                          |<-- loadThread() ---------|
        |                          |    (thread.mode?)        |
        |                          |                          |
+----------------+                 |
| ModeIndicator  |<-- displayMode -|
+----------------+                 |
```

**Options Analysis:**

**Option A: Backend Storage (Recommended)**
- Add `conversation_mode` column to Thread model
- Set when first message detected ("Meeting Mode" or "Document Refinement Mode")
- Return with thread data

**Option B: Frontend Inference**
- Parse first message in thread
- Derive mode from message content
- No backend changes

**Recommendation:** Option A - Backend storage is cleaner and more reliable.

**Component Boundaries:**

| Layer | Component | Changes Needed |
|-------|-----------|----------------|
| **Backend Model** | `Thread` | Add `conversation_mode: Optional[str]` column |
| **Backend Route** | `threads.py` | Return `conversation_mode` in responses |
| **Backend Service** | `conversation_service.py` | Detect and set mode on first user message |
| **Frontend Model** | `Thread` | Add `conversationMode` property |
| **Frontend Widget** | New `ModeIndicator` | Display mode chip/badge |
| **Frontend Screen** | `ConversationScreen` | Show indicator in toolbar row (next to `ProviderIndicator`) |

**Data Flow:**

```
Thread model (backend):
  ├── conversation_mode: Optional[str]  # "meeting" | "document_refinement" | null
  │
  └── On first message save:
        if content contains "Meeting Mode" → set "meeting"
        if content contains "Document Refinement" → set "document_refinement"

Thread model (frontend):
  ├── conversationMode: String?
  ├── displayMode: String  # "Meeting Mode" | "Document Refinement" | "Chat"
  └── modeIcon: IconData
```

**UI Design:**

```
+----------------------------------------------------------+
| ProviderIndicator                    ModeIndicator       |
| [Claude icon] Claude                 [meeting icon] Meeting|
+----------------------------------------------------------+
| ChatInput...                                             |
+----------------------------------------------------------+
```

**Suggested Build Order:**
1. Add `conversation_mode` to Thread model (backend)
2. Add migration for new column
3. Update `conversation_service.py` to detect mode on first message
4. Update thread API responses to include mode
5. Update frontend `Thread` model
6. Create `ModeIndicator` widget
7. Integrate into `ConversationScreen` toolbar row

---

### Feature 4: Artifact Generation UI

**Current State:**
- Artifacts created via `save_artifact` tool during AI chat
- `artifact_created` SSE event emitted on creation
- `/artifacts/{id}` endpoint for retrieval
- `/artifacts/{id}/export/{format}` for PDF/DOCX/MD export
- No UI for viewing artifacts (only export)

**Integration Points:**

```
+-------------------+     +----------------------+     +------------------+
| ConversationScreen|     | ConversationProvider |     | ArtifactService  |
+-------------------+     +----------------------+     +------------------+
        |                          |                          |
        |<-- artifact_created ----|<-- SSE event ------------|
        |                          |                          |
        |-- show notification --->|                          |
        |                          |                          |
+----------------+                 |
| ArtifactCard   |<-- artifact ----|
+----------------+                 |
        |                          |
        |-- view/export --------->|-- GET /artifacts/{id} -->|
        |                          |                          |
```

**Component Boundaries:**

| Layer | Component | Changes Needed |
|-------|-----------|----------------|
| **Frontend Model** | New `Artifact` | Map artifact API response |
| **Frontend Service** | New `ArtifactService` | CRUD + export endpoints |
| **Frontend Provider** | Extend `ConversationProvider` or new `ArtifactProvider` | Track artifacts for thread |
| **Frontend Widget** | New `ArtifactCard` | Display artifact metadata, actions |
| **Frontend Widget** | New `ArtifactPreviewDialog` | Full artifact content view |
| **Frontend Screen** | `ConversationScreen` | Show artifact notification, list |
| **Backend** | Already complete | No changes needed |

**Data Flow:**

```
ConversationProvider (extended):
  ├── artifacts: List<Artifact>  # artifacts in current thread
  ├── newArtifactId: String?     # most recent artifact (for highlighting)
  │
  ├── handleArtifactCreated(event)
  │     └── add to artifacts list, set newArtifactId
  │
  └── loadArtifacts(threadId)
        └── GET /threads/{threadId}/artifacts

Artifact model:
  ├── id: String
  ├── threadId: String
  ├── artifactType: ArtifactType (user_stories, acceptance_criteria, requirements_doc)
  ├── title: String
  ├── contentMarkdown: String
  └── createdAt: DateTime
```

**UI Design:**

```
+----------------------------------------------------------+
| Conversation Screen                                       |
+----------------------------------------------------------+
| [messages...]                                            |
|                                                          |
| +------------------------------------------------------+ |
| | Artifact Created                              [VIEW] | |
| | "Login Feature - User Stories"                       | |
| +------------------------------------------------------+ |
|                                                          |
| [StreamingMessage or ChatInput]                          |
+----------------------------------------------------------+

Artifacts Panel (expandable):
+----------------------------------------------------------+
| Artifacts (2)                                    [^/v]   |
+----------------------------------------------------------+
| +------------------------+ +------------------------+    |
| | User Stories           | | BRD - Login Feature    |   |
| | Created: 2 min ago     | | Created: 5 min ago     |   |
| | [View] [Export v]      | | [View] [Export v]      |   |
| +------------------------+ +------------------------+    |
+----------------------------------------------------------+
```

**Suggested Build Order:**
1. Create `Artifact` model (frontend)
2. Create `ArtifactService` with list/get/export methods
3. Extend `ConversationProvider` to track artifacts
4. Handle `artifact_created` SSE event
5. Create `ArtifactCard` widget
6. Create `ArtifactPreviewDialog` (markdown rendering)
7. Add collapsible artifacts panel to `ConversationScreen`
8. Add inline notification for new artifact creation

---

### Feature 5: Document Source Attribution

**Current State:**
- `search_documents` tool returns snippets with filenames
- Results formatted as "**{filename}**:\n{snippet}" in tool result
- No tracking of which documents informed a response
- User cannot see what documents were searched

**Integration Points:**

```
+-------------------+     +------------------+     +-------------------+
| MessageBubble     |     | ConversationProv |     | AIService         |
+-------------------+     +------------------+     +-------------------+
        |                          |                       |
        |                          |<-- SSE events --------|
        |                          |    tool_executing     |
        |                          |    (search_documents) |
        |                          |                       |
        |<-- message with sources -|                       |
        |                          |                       |
+------------------+
| SourceAttribution|
+------------------+
```

**Options Analysis:**

**Option A: New SSE Event (Recommended)**
- Add `document_sources` event after `search_documents` tool
- Include document IDs, filenames, snippets
- Frontend tracks and displays per-message

**Option B: Parse Tool Result**
- Extract sources from `tool_executing` status message
- More fragile, depends on format

**Option C: Append to Message Content**
- Include sources at end of assistant message
- Simplest but pollutes message content

**Recommendation:** Option A - Clean separation, allows rich UI.

**Component Boundaries:**

| Layer | Component | Changes Needed |
|-------|-----------|----------------|
| **Backend Service** | `ai_service.py` | Emit `document_sources` event after search |
| **Frontend Service** | `AIService` | Handle new `DocumentSourcesEvent` |
| **Frontend Provider** | `ConversationProvider` | Track sources per message |
| **Frontend Model** | `Message` | Add `sources: List<DocumentSource>?` |
| **Frontend Widget** | New `SourceAttribution` | Expandable source list under message |
| **Frontend Widget** | `MessageBubble` | Include `SourceAttribution` for assistant messages |

**Data Flow:**

```
Backend ai_service.py (in execute_tool):
  if tool_name == "search_documents":
      results = await search_documents(...)
      # Emit sources event
      yield {
          "event": "document_sources",
          "data": json.dumps({
              "documents": [
                  {"id": doc_id, "filename": filename, "snippet": snippet}
                  for doc_id, filename, snippet, score in results[:5]
              ]
          })
      }
      return formatted_result

Frontend ai_service.dart:
  case 'document_sources':
      yield DocumentSourcesEvent(
          documents: (data['documents'] as List).map(...)
      );

ConversationProvider:
  _pendingSources: List<DocumentSource>?  # sources for current streaming message

  if (event is DocumentSourcesEvent) {
      _pendingSources = event.documents;
  }
  if (event is MessageCompleteEvent) {
      final message = Message(..., sources: _pendingSources);
      _messages.add(message);
      _pendingSources = null;
  }
```

**UI Design:**

```
+----------------------------------------------------------+
| [Assistant message bubble]                                |
|                                                          |
| Based on the project documentation, the login flow...    |
|                                                          |
| +------------------------------------------------------+ |
| | Sources                                        [v/^] | |
| | - requirements.md: "...user authentication..."       | |
| | - security-policy.txt: "...password requirements..." | |
| +------------------------------------------------------+ |
+----------------------------------------------------------+
```

**Suggested Build Order:**
1. Add `document_sources` SSE event to backend `ai_service.py`
2. Add `DocumentSourcesEvent` to frontend `ai_service.dart`
3. Extend `Message` model with `sources` property
4. Update `ConversationProvider` to track pending sources
5. Create `SourceAttribution` widget
6. Integrate into `MessageBubble` for assistant messages
7. Add tap-to-view-document functionality (optional)

---

### Feature 6: File Size Validation UX

**Current State:**
- Backend validates: 1MB max, `.txt`/`.md` only
- Returns 413 error for oversized files
- Frontend shows generic error in SnackBar
- No pre-upload validation

**Integration Points:**

```
+----------------------+     +------------------+     +------------------+
| DocumentUploadScreen |     | DocumentProvider |     | Backend          |
+----------------------+     +------------------+     +------------------+
        |                           |                        |
        |-- pickFile() ----------->|                        |
        |<-- PlatformFile ---------|                        |
        |                           |                        |
        |-- validateFile() ------->|                        |
        |<-- ValidationResult -----|                        |
        |                           |                        |
        |   (if valid)              |                        |
        |-- uploadDocument() ----->|-- POST --------------->|
        |                           |                        |
        |   (if invalid)            |                        |
        |-- showValidationError -->|                        |
        |                           |                        |
```

**Component Boundaries:**

| Layer | Component | Changes Needed |
|-------|-----------|----------------|
| **Frontend** | `DocumentUploadScreen` | Pre-validation before upload |
| **Frontend** | `DocumentProvider` | Add validation method |
| **Frontend Widget** | New `FileValidationCard` | Show file details + validation status |
| **Frontend** | Constants | Define `MAX_FILE_SIZE`, `ALLOWED_EXTENSIONS` |
| **Backend** | Already complete | No changes needed |

**Validation Rules:**

| Rule | Limit | Error Message |
|------|-------|---------------|
| File size | 1MB (1,048,576 bytes) | "File exceeds 1MB limit ({actual} MB)" |
| File type | .txt, .md | "Only .txt and .md files are supported" |
| Empty file | >0 bytes | "File is empty" |

**Data Flow:**

```
DocumentProvider:
  static const maxFileSize = 1024 * 1024;  // 1MB
  static const allowedExtensions = ['txt', 'md'];

  ValidationResult validateFile(PlatformFile file) {
      if (file.size > maxFileSize) {
          return ValidationResult.error(
              "File exceeds 1MB limit (${(file.size / 1024 / 1024).toStringAsFixed(2)} MB)"
          );
      }
      if (!allowedExtensions.contains(file.extension?.toLowerCase())) {
          return ValidationResult.error(
              "Only .txt and .md files are supported"
          );
      }
      if (file.size == 0) {
          return ValidationResult.error("File is empty");
      }
      return ValidationResult.valid();
  }

ValidationResult:
  ├── isValid: bool
  ├── errorMessage: String?
  └── warnings: List<String>?  # e.g., "Large file may take longer to upload"
```

**UI Design:**

```
Before Selection:
+----------------------------------------------------------+
| [Upload icon]                                            |
| Upload a text document                                   |
| Only .txt and .md files are supported                    |
| Maximum file size: 1MB                                   |
|                                                          |
| [Select File]                                            |
+----------------------------------------------------------+

After Selection (Valid):
+----------------------------------------------------------+
| +------------------------------------------------------+ |
| | requirements.txt                              [x]    | |
| | 245 KB | .txt                                        | |
| | [checkmark] Ready to upload                          | |
| +------------------------------------------------------+ |
|                                                          |
| [Upload]                                                 |
+----------------------------------------------------------+

After Selection (Invalid - Size):
+----------------------------------------------------------+
| +------------------------------------------------------+ |
| | large-document.txt                            [x]    | |
| | 2.3 MB | .txt                                        | |
| | [warning] File exceeds 1MB limit                     | |
| +------------------------------------------------------+ |
|                                                          |
| [Select Different File]                                  |
+----------------------------------------------------------+

After Selection (Invalid - Type):
+----------------------------------------------------------+
| +------------------------------------------------------+ |
| | document.pdf                                  [x]    | |
| | 500 KB | .pdf                                        | |
| | [error] Only .txt and .md files are supported        | |
| +------------------------------------------------------+ |
|                                                          |
| [Select Different File]                                  |
+----------------------------------------------------------+
```

**Suggested Build Order:**
1. Add validation constants to frontend
2. Add `validateFile()` method to `DocumentProvider`
3. Create `ValidationResult` class
4. Create `FileValidationCard` widget
5. Update `DocumentUploadScreen` to show file preview + validation
6. Add clear file / select different file actions

---

## Cross-Feature Dependencies

```
Feature Dependencies Graph:

[1. Network Resilience]
    └── Independent (no dependencies)

[2. Budget Tracking]
    └── Independent (no dependencies)

[3. Mode Indicator]
    └── Depends on: Backend Thread model change

[4. Artifact UI]
    └── Independent (backend already supports)

[5. Source Attribution]
    └── Depends on: Backend SSE event addition

[6. File Validation]
    └── Independent (frontend only)

Build Order Recommendation:
  Phase 1 (Independent, Frontend-only):
    - Feature 6: File Size Validation UX
    - Feature 1: Network Interruption Handling

  Phase 2 (Independent, Full-stack):
    - Feature 2: Token Budget Tracking
    - Feature 4: Artifact Generation UI

  Phase 3 (Dependent):
    - Feature 3: Persistent Mode Indicator (requires migration)
    - Feature 5: Document Source Attribution (requires backend event)
```

---

## Suggested Roadmap Phases

Based on architectural analysis:

### Phase 1: Client-Side Resilience (No Backend Changes)
**Features:** #1 Network Resilience, #6 File Validation
**Rationale:** Both are frontend-focused, improve UX immediately, no deployment coordination needed.

### Phase 2: Transparency Indicators
**Features:** #2 Budget Tracking, #3 Mode Indicator
**Rationale:** Both surface existing data with better UI. Mode indicator requires simple migration.

### Phase 3: AI Interaction Enhancement
**Features:** #4 Artifact UI, #5 Source Attribution
**Rationale:** Both enhance the AI chat experience. Source attribution requires backend event addition.

---

## File Locations Summary

### New Files to Create

**Frontend:**
```
lib/
  models/
    artifact.dart           # Artifact model (Feature 4)
    validation_result.dart  # File validation result (Feature 6)
  services/
    artifact_service.dart   # Artifact API calls (Feature 4)
  providers/
    budget_provider.dart    # Budget status tracking (Feature 2) [or extend AuthProvider]
  widgets/
    budget_warning_banner.dart    # Budget warning UI (Feature 2)
    mode_indicator.dart           # Conversation mode display (Feature 3)
    artifact_card.dart            # Artifact display card (Feature 4)
    artifact_preview_dialog.dart  # Full artifact view (Feature 4)
    source_attribution.dart       # Document sources list (Feature 5)
    file_validation_card.dart     # Upload validation UI (Feature 6)
```

### Files to Modify

**Frontend:**
```
lib/
  services/
    ai_service.dart         # Add ConnectionStateEvent, retry logic (Feature 1)
                           # Add DocumentSourcesEvent (Feature 5)
  providers/
    conversation_provider.dart  # Connection state, artifact tracking, sources
    auth_provider.dart          # Budget status (if not new provider)
  models/
    thread.dart             # Add conversationMode property (Feature 3)
    message.dart            # Add sources property (Feature 5)
    token_usage.dart        # Add threshold helpers (Feature 2)
  screens/
    conversation/
      conversation_screen.dart       # Integrate all conversation features
      widgets/
        streaming_message.dart       # Connection status indicator (Feature 1)
        message_bubble.dart          # Source attribution (Feature 5)
    documents/
      document_upload_screen.dart    # File validation (Feature 6)
    settings_screen.dart             # Enhanced budget display (Feature 2)
```

**Backend:**
```
app/
  models.py                 # Add conversation_mode to Thread (Feature 3)
  routes/
    auth.py                 # Add /budget-status endpoint (Feature 2)
  services/
    ai_service.py           # Add document_sources event (Feature 5)
    conversation_service.py # Detect mode on first message (Feature 3)
    token_tracking.py       # Add get_budget_status() (Feature 2)
```

---

## Sources

- Analysis based on direct codebase examination:
  - `frontend/lib/main.dart` - Router and provider setup
  - `frontend/lib/providers/conversation_provider.dart` - Chat state management
  - `frontend/lib/services/ai_service.dart` - SSE streaming client
  - `backend/app/services/ai_service.py` - LLM adapter, tool execution
  - `backend/app/routes/conversations.py` - SSE endpoint, heartbeat
  - `backend/app/routes/threads.py` - Thread CRUD
  - `backend/app/routes/documents.py` - Document upload validation
  - `backend/app/models.py` - Database models
  - `backend/app/services/token_tracking.py` - Usage tracking

All integration recommendations verified against existing patterns in the codebase.
