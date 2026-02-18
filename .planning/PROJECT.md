# Business Analyst Assistant

## What This Is

A hybrid mobile and web application that augments business analysts during feature discovery meetings. The system provides AI-powered conversational assistance to explore requirements, proactively identify edge cases, and generate structured business documentation (user stories, acceptance criteria, requirements documents) on demand. Users upload project context documents in multiple formats (Excel, CSV, PDF, Word, text), conduct multiple conversation threads per project, and export professional artifacts in multiple formats. Rich document data can be exported back to Excel or CSV for round-trip workflows.

## Core Value

Business analysts reduce time spent on requirement documentation while improving completeness through AI-assisted discovery conversations that systematically explore edge cases and generate production-ready artifacts.

## Current State

**Shipped:** v3.0 Assistant Foundation (2026-02-18)

**Delivered:**
- Dedicated "Assistant" sidebar section with own routes and deep linking
- Thread management: create, list, delete with 10-second undo
- Streaming conversation UI with markdown rendering and syntax highlighting
- Skills discovery API and skill selector in chat input
- Thread-scoped document upload (file picker, drag-and-drop)
- AssistantConversationProvider: auto-retry, thinking timer, skill prepending
- BA Assistant flow completely unchanged

**Previous:** v0.1-claude-code Claude Code as AI Backend (2026-02-17)

**Next:** Planning next milestone

Previous milestone (v1.9.2):
- Network error resilience with partial content preservation and retry
- Budget transparency with threshold warnings (80%/95%/100%)
- Conversation mode persistence with AppBar badge
- Artifact generation UI with type picker and inline export
- Source attribution with document chips and navigation
- 1,098 total tests (471 backend + 627 frontend)

Previous milestone (v1.9.1):
- Backend: service tests, LLM adapter tests, API contract tests
- Frontend: provider tests, service tests, widget tests, model tests
- CI pipeline with Codecov integration and README coverage badge

Previous milestone (v1.9):
- Enter to send messages, Shift+Enter for newline (industry standard)
- Threads-first project layout with collapsible documents column
- Project-less chats with global Chats navigation section
- One-way chat-to-project association via "Add to Project"
- Real-time search and sort in thread lists (Newest/Oldest/A-Z)

Previous features (v1.8):
- Settings page LLM provider selector (Claude / Gemini / DeepSeek)
- Per-conversation model binding (conversations remember their model)
- Model indicator below chat window with provider-specific colors
- Backend adapter pattern normalizing all providers to StreamChunk format
- SSE heartbeat mechanism for extended thinking (5+ min)

Previous features (v1.7):
- Unique conversation URLs (`/projects/:projectId/threads/:threadId`)
- URL preserved on page refresh (authenticated users stay on same page)
- OAuth redirect preserves intended destination via sessionStorage
- Custom 404 error page with navigation options

Previous features (v1.6):
- One-tap copy for AI responses with cross-platform clipboard support
- Retry failed AI requests without retyping messages
- Thread rename via AppBar edit icon or popup menu
- Auth provider indicator showing "Signed in with Google/Microsoft"

Previous features (v1.5):
- Persistent responsive sidebar navigation (desktop rail, mobile drawer)
- Theme management with instant persistence (no white flash)
- Settings page with profile, token usage, logout
- Deletion with 10-second undo for all resources
- Professional empty states across all list screens

**Codebase:** ~105,000 lines of Python/Dart across FastAPI backend and Flutter frontend.

## Future Vision

**Assistant expansion** (after v3.0)
- Custom tools and capabilities for the Assistant
- Multi-purpose assistant flows (not just BA)
- Provider selection in Assistant mode

**v2.2 — Search, Previews & Integrations** (after deployment)

- Global search across projects and threads
- Thread preview text in list view
- Thread mode indicator badges
- JIRA integration for artifact export
- Voice input for mobile meetings

## Requirements

### Validated

- ✓ User can authenticate with Google or Microsoft work account via OAuth 2.0 — MVP v1.0
- ✓ User can create and manage multiple projects with isolated contexts — MVP v1.0
- ✓ User can upload text documents to projects for AI context — MVP v1.0
- ✓ User can create multiple conversation threads per project — MVP v1.0
- ✓ AI provides real-time streaming guidance during feature discovery with proactive edge case identification — MVP v1.0
- ✓ AI autonomously searches project documents when conversation requires context — MVP v1.0
- ✓ User can request structured artifacts (user stories, acceptance criteria, requirements docs) from conversations — MVP v1.0
- ✓ User can export artifacts in Markdown, PDF, and Word formats — MVP v1.0
- ✓ Threads display AI-generated summaries for quick identification — MVP v1.0
- ✓ All data persists and syncs across devices (web, Android, iOS) — MVP v1.0
- ✓ Professional loading states with skeleton loaders — MVP v1.0
- ✓ Global error handling with user-friendly recovery — MVP v1.0
- ✓ Persistent sidebar navigation visible on all screens (responsive: desktop always-visible, mobile hamburger) — Beta v1.5
- ✓ Home screen features primary action buttons ("Start Conversation", "Browse Projects") — Beta v1.5
- ✓ Empty states provide clear guidance when projects/threads/documents lists are empty — Beta v1.5
- ✓ User can delete projects with confirmation dialog — Beta v1.5
- ✓ User can delete threads with confirmation dialog — Beta v1.5
- ✓ User can delete documents with confirmation dialog — Beta v1.5
- ✓ User can delete individual messages with confirmation dialog — Beta v1.5
- ✓ Settings page displays user profile information — Beta v1.5
- ✓ Settings page provides logout functionality — Beta v1.5
- ✓ Settings page includes light/dark theme toggle — Beta v1.5
- ✓ Settings page shows current token budget usage — Beta v1.5
- ✓ AI mode selection presents as clickable buttons instead of typed responses — Beta v1.5
- ✓ Date/time formatting is consistent (relative <7 days, absolute >7 days) — Beta v1.5
- ✓ Project headers are consolidated to reduce wasted vertical space — Beta v1.5
- ✓ Breadcrumb navigation or contextual back arrows show navigation context — Beta v1.5
- ✓ Message pills have improved readability (padding, font size) — Beta v1.5
- ✓ Project cards display metadata badges (thread count, document count) — Beta v1.5
- ✓ User can retry a failed AI request without retyping message — v1.6
- ✓ User can copy AI-generated content with one tap — v1.6
- ✓ User can rename conversation thread after creation — v1.6
- ✓ User can see which OAuth provider they're signed in with — v1.6
- ✓ Conversations have unique URLs (`/projects/:projectId/threads/:threadId`) — v1.7
- ✓ URL preserved on page refresh (authenticated user stays on same page) — v1.7
- ✓ Auth redirect stores return URL and completes to intended destination — v1.7
- ✓ Invalid routes handled gracefully (404 error states with navigation options) — v1.7
- ✓ Deleted project/thread URLs show "not found" state instead of crash — v1.7
- ✓ User can select default LLM provider in Settings (Claude, Gemini, DeepSeek) — v1.8
- ✓ New conversations use the currently selected default provider — v1.8
- ✓ Existing conversations continue with their original model regardless of default — v1.8
- ✓ Model indicator displays below chat window showing current provider name — v1.8
- ✓ Backend supports multiple LLM provider APIs via adapter pattern — v1.8
- ✓ Enter key sends message, Shift+Enter for newline — v1.9
- ✓ Threads are primary view when opening project — v1.9
- ✓ Documents appear in collapsible side column — v1.9
- ✓ Global Chats menu shows all conversations across projects — v1.9
- ✓ User can create chat without selecting project first — v1.9
- ✓ User can add project-less chat to a project (one-way association) — v1.9
- ✓ User can search/filter threads by title — v1.9
- ✓ Chat input supports more visible lines (up to 10) — v1.9

- ✓ Backend services have unit test coverage — v1.9.1
- ✓ Backend API endpoints have unit test coverage — v1.9.1
- ✓ LLM adapters (Claude/Gemini/DeepSeek) have unit test coverage — v1.9.1
- ✓ Frontend providers have unit test coverage — v1.9.1
- ✓ Frontend widgets have unit test coverage — v1.9.1
- ✓ All tests pass without failures — v1.9.1
- ✓ Test suite is CI-ready (can run in automated pipeline) — v1.9.1

- ✓ On network loss during streaming, partial AI content is preserved with "Connection lost" banner — v1.9.2
- ✓ Retry option available for interrupted responses — v1.9.2
- ✓ Warning banners at 80%/95% token budget usage — v1.9.2
- ✓ Clear "Budget exhausted" state at 100% (can view history, cannot send) — v1.9.2
- ✓ File size validation with clear error before upload attempt — v1.9.2
- ✓ Current conversation mode shown as persistent badge in AppBar — v1.9.2
- ✓ Mode badge tappable to change mode with context warning — v1.9.2
- ✓ "Generate Artifact" button in ConversationScreen — v1.9.2
- ✓ Artifact type picker (User Stories, Acceptance Criteria, BRD, Custom) — v1.9.2
- ✓ Generated artifacts visually distinct with inline export buttons — v1.9.2
- ✓ AI responses show source document chips when documents were referenced — v1.9.2
- ✓ Source chips clickable to open Document Viewer — v1.9.2

- ✓ User can preview document before upload (filename, size, first lines) — v1.9.3
- ✓ User can cancel upload after preview — v1.9.3
- ✓ User can download document from Document Viewer — v1.9.3
- ✓ User can download document from document list (quick action) — v1.9.3
- ✓ Breadcrumbs show full path including thread name — v1.9.3
- ✓ Project threads: Projects > {Project} > Threads > {Thread} — v1.9.3
- ✓ Project-less chats: Chats > {Thread} — v1.9.3
- ✓ Each breadcrumb segment is clickable — v1.9.3
- ✓ Document Viewer has proper URL route (/projects/:id/documents/:docId) — v1.9.3

- ✓ Each artifact generation request produces exactly one artifact regardless of conversation history — v1.9.4
- ✓ System prompt includes deduplication rule for fulfilled artifact requests — v1.9.4
- ✓ save_artifact tool enforces single-call-per-request behavior — v1.9.4
- ✓ Fulfilled artifact requests structurally removed from conversation context before reaching model — v1.9.4
- ✓ Button-triggered artifact generation bypasses chat history (silent generation) — v1.9.4

- ✓ All log entries use structured JSON format with consistent schema — v1.9.5
- ✓ Log entries include severity level (DEBUG, INFO, WARN, ERROR) — v1.9.5
- ✓ Log entries include ISO 8601 timestamps — v1.9.5
- ✓ Correlation ID links frontend requests to backend operations via X-Correlation-ID header — v1.9.5
- ✓ User can toggle detailed logging on/off from Settings screen — v1.9.5
- ✓ Logs are retained for 7 days with automatic rotation/deletion — v1.9.5
- ✓ Admin can download logs via authenticated API endpoint — v1.9.5
- ✓ Logs are stored in accessible files for direct analysis — v1.9.5
- ✓ User navigation events are logged (screen views, route changes) — v1.9.5
- ✓ User actions are logged (button clicks, form submits) — v1.9.5
- ✓ API requests/responses are logged via Dio interceptor (endpoint, method, status, duration) — v1.9.5
- ✓ Errors are captured with exception type and stack trace — v1.9.5
- ✓ All frontend logs include session ID for grouping — v1.9.5
- ✓ Logs include category tags (auth, api, ai, navigation, error) — v1.9.5
- ✓ Network state changes are logged (connectivity, timeouts) — v1.9.5
- ✓ Frontend logs are sent to backend for centralized storage — v1.9.5
- ✓ HTTP requests are logged via middleware (method, path, correlation ID, user ID) — v1.9.5
- ✓ HTTP responses are logged (status code, duration) — v1.9.5
- ✓ AI service calls are logged (provider, model, input/output tokens, duration) — v1.9.5
- ✓ Database operations are logged (table, operation, duration) — v1.9.5
- ✓ SSE streaming summaries are logged (event count, total duration) — v1.9.5
- ✓ Logging uses async-safe pattern (QueueHandler) to avoid blocking event loop — v1.9.5
- ✓ Sensitive data is sanitized before logging (tokens, API keys, PII fields) — v1.9.5
- ✓ Logging toggle state persists across app restarts — v1.9.5
- ✓ Backend logging level is configurable via environment variable — v1.9.5
- ✓ Log directory path is configurable via environment variable — v1.9.5
- ✓ Frontend buffer size is configurable (default: 1000 entries) — v1.9.5
- ✓ Frontend flush interval is configurable (default: 5 minutes) — v1.9.5

- ✓ Thread type discrimination separates Assistant from BA flow — v3.0
- ✓ Assistant sidebar navigation with dedicated routes — v3.0
- ✓ Assistant thread create/list/delete with undo — v3.0
- ✓ Assistant conversation screen with streaming, markdown, copy/retry — v3.0
- ✓ Document upload for Assistant threads (file picker, drag-and-drop) — v3.0
- ✓ Assistant always uses claude-code-cli adapter — v3.0

- ✓ User can upload Excel (.xlsx) files with text extracted for AI context and search — v2.1
- ✓ User can upload CSV files with text extracted for AI context and search — v2.1
- ✓ User can upload PDF files with text extracted for AI context and search — v2.1
- ✓ User can upload Word (.docx) files with text extracted for AI context and search — v2.1
- ✓ Excel parsing preserves data types (leading zeros, dates, large numbers stored as strings) — v2.1
- ✓ CSV parsing auto-detects encoding (UTF-8, Windows-1252, UTF-8-BOM) — v2.1
- ✓ Server validates file type via content-type and magic number verification — v2.1
- ✓ Maximum file size 10MB for rich document formats — v2.1
- ✓ XLSX/DOCX uploads protected against XXE attacks (defusedxml) — v2.1
- ✓ XLSX/DOCX uploads protected against zip bombs (uncompressed size validation) — v2.1
- ✓ Malformed files rejected with clear error message — v2.1
- ✓ Original binary files stored encrypted alongside extracted text (dual-column storage) — v2.1
- ✓ Extracted text indexed in FTS5 for full-text search across all document formats — v2.1
- ✓ Document metadata stored (sheet names, row count, column headers, page count) — v2.1
- ✓ Visual table preview shows first rows for Excel/CSV in upload confirmation dialog — v2.1
- ✓ Sheet selector allows choosing which Excel sheets to parse — v2.1
- ✓ Document Viewer renders format-appropriate display (table grid for Excel/CSV, text for PDF/Word) — v2.1
- ✓ Document metadata displayed in Document Viewer (format type, row/page count, sheet names) — v2.1
- ✓ Table renderer supports sorting and handles large datasets with virtualization — v2.1
- ✓ AI document_search tool returns extracted text from all 4 rich document formats — v2.1
- ✓ Token budget management limits document context to prevent context window overflow — v2.1
- ✓ Source attribution chips show format-specific info (sheet name for Excel references) — v2.1
- ✓ User can export parsed document data to Excel (.xlsx) format — v2.1
- ✓ User can export parsed document data to CSV format — v2.1

### Active

**v2.0 — Security Audit & Deployment** (backlogged)

- [ ] OWASP-aligned security audit and hardening
- [ ] Production environment configuration
- [ ] Hosting platform deployment (research-recommended)
- [ ] Custom domain with DNS setup
- [ ] OAuth production redirect URIs (Google + Microsoft)
- [ ] End-to-end deployment guide for first-time deployer

### Deferred

- [ ] Thread list items show preview of last message (deferred from Beta v1.5 - requires backend API)
- [ ] Thread list items display mode indicator (deferred from Beta v1.5 - requires backend tracking)

### Out of Scope

- **Search functionality** — Deferred to v2.2+; users browse manually (acceptable for <20 projects per user)
- **Message editing** — Users can delete but not edit individual messages; editing introduces conversation coherence complexity
- **Multi-user collaboration** — Single-user per account; no project sharing or team workspaces until v2.0+
- **Notifications** — No push or email notifications; not needed for single-user workflow
- **Offline mode** — Requires network connection; offline capability deferred to v2.0+
- **Custom AI personalities** — Single consistent AI behavior; customization deferred unless strong user demand
- **Integration with Jira/Confluence** — External integrations deferred to v2.0+ based on enterprise adoption
- **Advanced thread features** — Thread archiving, starring, categorization deferred to v2.0
- **Bulk operations** — Multi-select delete, bulk export deferred to v2.0

## Context

**User Profile:**
Target users are business analysts working in product development, requirements gathering, and stakeholder management roles. They typically have Google Workspace or Microsoft 365 work accounts, conduct client meetings both in-office (desktop) and on-site (mobile), and need to capture rough feature ideas then convert them into structured documentation.

**Workflow Pattern:**
BAs prepare for meetings by uploading existing requirements or stakeholder notes to project context. During discovery conversations (meetings or solo work), they describe features and ask the AI to explore edge cases, clarify ambiguities, and identify gaps. After exploration, they request artifacts (user stories, acceptance criteria) and export them for stakeholder review or ticketing systems.

**Technical Environment:**
- Solo developer with 20-30 hours/week capacity (part-time development)
- Developer has Flutter experience (AI Rhythm Coach project) and QA background
- Comprehensive technical specification and roadmap documents
- Cost-conscious approach: monitoring AI API costs, SQLite for simplicity

**Market Validation Goals:**
- Prove AI-assisted discovery genuinely helps BAs capture better requirements faster
- Validate conversation-based interface is preferable to form-based requirement capture
- Test that generated artifacts are high enough quality to use directly
- Confirm cross-device access (desktop planning → mobile meetings) is essential workflow
- Learn which artifact types BAs request most frequently and usage patterns

## Constraints

- **Solo Developer Capacity**: 20-30 hours/week part-time development, must maintain velocity through simplicity choices
- **Technology Stack**: Flutter (web/Android/iOS), FastAPI (Python), SQLite, Multi-LLM APIs (Anthropic/Google/DeepSeek), OAuth 2.0, PaaS hosting (Railway/Render)
- **AI API Costs**: Monitor token usage closely; estimated $50-100/month, must not exceed budget without user validation
- **Cross-Platform**: Single codebase must support web, Android, and iOS simultaneously
- **PaaS Hosting**: Deployment limited to Railway/Render capabilities; no custom infrastructure or Kubernetes
- **Rich Document Parsing**: Supports Excel, CSV, PDF, Word, and text uploads with format-specific parsing and AI context integration (v2.1)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Flutter for frontend | Leverages existing experience from AI Rhythm Coach; single codebase for web/Android/iOS; zero learning curve maximizes velocity | ✓ Implemented |
| Direct Anthropic API (not Agent SDK) | Agent SDK requires Claude Code CLI runtime (not suitable for web backends); Direct API with XML system prompt achieves same behavioral goals with standard PaaS deployment; business-analyst skill transformed to 7,437-token system prompt | ✓ Implemented (Phase 04.1) |
| SQLite for MVP database | Zero-configuration simplicity, file-based deployment, built-in FTS5 for document search; clear migration path to PostgreSQL when scale demands (via SQLAlchemy ORM) | ✓ Implemented |
| OAuth-only authentication | No password management burden (reset flows, strength validation); enterprise-friendly for BA users with work accounts; delegates security to Google/Microsoft | ✓ Implemented |
| Text-only document upload | Defers PDF/Word parsing complexity to validate document usefulness first; users copy-paste content (acceptable friction for MVP) | ✓ Implemented |
| PaaS hosting (Railway/Render) | Git-based deployment, automatic HTTPS, managed infrastructure; operational simplicity critical for solo developer focusing on product | — Ready for deployment |
| SSE for AI streaming | Unidirectional server→client streaming perfect for AI responses; simpler than WebSockets, PaaS-friendly, automatic reconnection | ✓ Implemented |
| Immediate persistence pattern | Theme/sidebar state saved to SharedPreferences BEFORE notifyListeners() to survive crashes | ✓ Implemented (Phase 06) |
| Static load() factory pattern | Async provider initialization before MaterialApp prevents white flash on dark mode | ✓ Implemented (Phase 06) |
| Hard delete with CASCADE | Database handles child record cleanup; simplifies backend code | ✓ Implemented (Phase 09) |
| 10-second undo window | Timer-based deferred deletion with optimistic UI; industry-standard pattern | ✓ Implemented (Phase 09) |
| ActionChip for mode selection | Tap-action semantics (not toggle), immediate response initiation | ✓ Implemented (Phase 10) |
| Synchronous clipboard for Safari | Safari requires clipboard in sync user gesture handler; no async/await | ✓ Implemented (Phase 11) |
| PATCH for thread rename (not PUT) | Semantically correct for single-field updates | ✓ Implemented (Phase 14) |
| Return 404 for non-owner | Security: don't leak thread existence to non-owners | ✓ Implemented (Phase 14) |
| sessionStorage for returnUrl | Auto-clears on tab close; ephemeral by design for security | ✓ Implemented (Phase 16) |
| dart:html for sessionStorage | Simpler API than package:web; migrate to package:web when Wasm becomes default | ✓ Implemented (Phase 16) |
| GoRouter.optionURLReflectsImperativeAPIs | Enables browser back/forward to work correctly with imperative navigation | ✓ Implemented (Phase 17) |
| ResourceNotFoundState widget | Reusable widget for deleted project/thread states; consistent UX | ✓ Implemented (Phase 17) |
| FocusNode.onKeyEvent for keyboard | Modern Flutter API, cleaner TextField integration than RawKeyboardListener | ✓ Implemented (Phase 23) |
| TextInputAction.none | Critical for custom Enter key handling (prevents system interception) | ✓ Implemented (Phase 23) |
| Session-scoped column state | Requirement says "within session" — no SharedPreferences needed | ✓ Implemented (Phase 24) |
| Dual thread ownership model | user_id for project-less, project.user_id for project threads | ✓ Implemented (Phase 25) |
| SET NULL on project FK | Threads become project-less on project delete (not CASCADE) | ✓ Implemented (Phase 25) |
| Permanent association | Thread-project association is one-way and permanent | ✓ Implemented (Phase 26) |
| Client-side thread filtering | Computed filteredThreads getter with in-memory filter/sort | ✓ Implemented (Phase 27) |
| Preserve _streamingText on error | PITFALL-01: Don't clear partial content so users can copy/view incomplete responses | ✓ Implemented (Phase 34) |
| ErrorStateMessage separate from StreamingMessage | Different UI states (error styling, copy-only vs live streaming) | ✓ Implemented (Phase 34) |
| Validate file size BEFORE setState | PITFALL-09: User sees error before any upload UI state change | ✓ Implemented (Phase 34) |
| API costPercentage not local calculation | PITFALL-04: API-provided counts to avoid estimation errors | ✓ Implemented (Phase 35) |
| Mode validation at API level not DB | Allows flexible mode additions without migrations | ✓ Implemented (Phase 35) |
| ActionChip for mode badge (not IconButton) | Chip shows icon + label, distinct from other AppBar icons | ✓ Implemented (Phase 35) |
| Track documents at backend search time | PITFALL-05: Prevents hallucinated citations | ✓ Implemented (Phase 36) |
| ArtifactType enum uses exact backend snake_case | Direct mapping avoids translation errors | ✓ Implemented (Phase 36) |
| Collapsible artifact cards (collapsed by default) | PITFALL-08: Minimize vertical space consumption | ✓ Implemented (Phase 36) |
| Bottom sheet preview for project-less threads | Cannot navigate to document viewer without project context | ✓ Implemented (Phase 36) |
| Nested document route under project | /projects/:id/documents/:docId enables breadcrumbs and deep links | ✓ Implemented (Phase 39) |
| context.push for document navigation | Preserves browser history; back button returns to project | ✓ Implemented (Phase 39) |
| Intermediate breadcrumb segments link to project | "Threads" and "Documents" link to project detail (no separate routes) | ✓ Implemented (Phase 39) |
| Static show() for preview dialog | Consistent with ModeChangeDialog pattern; simplifies caller code | ✓ Implemented (Phase 38) |
| Screen-level download (no service) | Simple 10-line operation; service would be over-engineering | ✓ Implemented (Phase 37) |

| Deduplication rule at priority 2 | After one-question-at-a-time but before mode detection; artifact deduplication critical for all phases | ✓ Implemented (Phase 40) |
| Tool results as completion evidence | ARTIFACT_CREATED marker from BUG-019 is dead code; tool results are reliable detection signal | ✓ Implemented (Phase 40) |
| Escape hatch for regenerate/revise | Covers user intent to modify artifacts without overly broad catch-all that re-enables duplication | ✓ Implemented (Phase 40) |
| 5-second correlation window | Wide enough to catch typical artifact creation latency, narrow enough to avoid false positives | ✓ Implemented (Phase 41) |
| Filter fulfilled pairs BEFORE truncation | Ensures truncation works on already-filtered conversation for accurate token estimation | ✓ Implemented (Phase 41) |
| generateArtifact() separate from sendMessage() | PITFALL-06: Prevents blank message bubbles, streaming UI conflicts, state machine interference | ✓ Implemented (Phase 42) |
| State clears on ArtifactCreatedEvent | PITFALL-05: Artifact appears before stream ends; user sees result immediately | ✓ Implemented (Phase 42) |
| QueueHandler + QueueListener pattern | Async-safe logging that doesn't block FastAPI event loop during file I/O | ✓ Implemented (Phase 43) |
| structlog for JSON logging | Native JSON output, processor chains, compatible with AI analysis tools | ✓ Implemented (Phase 43) |
| TimedRotatingFileHandler | Daily rotation with configurable retention (default 7 days) | ✓ Implemented (Phase 43) |
| contextvars for correlation ID | Async-safe, request-scoped storage without thread-local issues | ✓ Implemented (Phase 43) |
| Boolean is_admin flag | Simple admin role sufficient for pilot; RBAC library would be overkill | ✓ Implemented (Phase 44) |
| Frontend logs to same file with [FRONTEND] prefix | Simpler than separate log files, enables unified correlation | ✓ Implemented (Phase 44) |
| Path traversal protection via is_relative_to() | Security-critical for log download endpoint | ✓ Implemented (Phase 44) |
| LoggingService singleton with 1000-entry buffer | Memory-bounded with auto-trim on overflow | ✓ Implemented (Phase 45) |
| UUID v4 session ID per app lifecycle | Enables grouping logs by session without auth dependency | ✓ Implemented (Phase 45) |
| ApiClient singleton for shared Dio | All HTTP requests route through same interceptor automatically | ✓ Implemented (Phase 46) |
| Default logging enabled for pilot | Maximizes diagnostic data collection during pilot testing | ✓ Implemented (Phase 47) |
| Clear buffer when logging disabled | Privacy protection - no stale logs remain after user disables | ✓ Implemented (Phase 47) |
| Copy buffer before POST in flush | Prevents mutation during async operation if new logs added | ✓ Implemented (Phase 48) |
| Parser adapter pattern with factory routing | DocumentParser base class + format-specific adapters (Excel, CSV, PDF, Word, Text) | ✓ Implemented (Phase 54) |
| Dual-column storage (binary + text) | content_encrypted for original binary, content_text for extracted text; backward compatible | ✓ Implemented (Phase 54) |
| defusedxml for XXE protection | Prevents XML External Entity attacks in XLSX/DOCX files | ✓ Implemented (Phase 54) |
| PlutoGrid for table rendering | Handles 1000+ rows with virtualization; v8.1.0 used (v8.7.0 unavailable) | ✓ Implemented (Phase 55) |
| Client-side Excel preview | excel package for instant preview in upload dialog; limited to 10 rows | ✓ Implemented (Phase 55) |
| Token budget limiting (3 chunks) | Prevents context window overflow for large documents | ✓ Implemented (Phase 55) |
| openpyxl write_only mode for export | Memory-efficient Excel generation; avoids loading entire workbook in memory | ✓ Implemented (Phase 56) |
| UTF-8 BOM for CSV export | encode('utf-8-sig') ensures Excel opens CSV files correctly | ✓ Implemented (Phase 56) |
| FileSaver for cross-platform download | Works on web and desktop for export file delivery | ✓ Implemented (Phase 56) |
| debugPrint for flush errors | Avoids infinite loop if logError triggers another flush attempt | ✓ Implemented (Phase 48) |

| Separate Assistant from BA flow | BA Assistant stays on direct API with BA prompts; Assistant section uses CLI adapter with no BA context. Two distinct user experiences in one app. | ✓ Implemented (v3.0) |
| String(20) for thread_type (not Enum) | Match existing model_provider pattern; easier to add new types without migrations | ✓ Implemented (Phase 62) |
| 3-step migration for thread_type | Nullable → backfill → NOT NULL for backward compatibility with existing data | ✓ Implemented (Phase 62) |
| AssistantConversationProvider (not reuse ConversationProvider) | BA-specific logic deeply embedded; cleaner to build separate provider stripped of artifacts, budget, mode | ✓ Implemented (Phase 64) |
| MarkdownMessage with flutter_markdown | AI responses render as formatted markdown with syntax highlighting, replacing raw Text() | ✓ Implemented (Phase 64) |
| Skills prepend one-time per message | Skill context prepended transparently, cleared after send; user controls when to apply | ✓ Implemented (Phase 64) |
| flutter_dropzone for web drag-and-drop | Web-only with kIsWeb guard; mobile falls back to file picker | ✓ Implemented (Phase 64) |

---
*Last updated: 2026-02-18 after v3.0 milestone shipped — Assistant Foundation*
